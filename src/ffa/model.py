"""Random Forest training with spatial block cross-validation."""
import numpy as np
import pandas as pd
from scipy import ndimage as ndi
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, cohen_kappa_score, f1_score, precision_score, recall_score
from sklearn.model_selection import GroupKFold

FOUR = ndi.generate_binary_structure(2, 1)


def clean_labels(wc, feats, names, cfg, extra=None):
    """WorldCover classes -> 1 forest / 0 non-forest / -1 ignore.
    Border pixels are eroded away (mixed pixels) and 'forest' labels that look cleared are dropped."""
    forest = wc == 10
    non = (wc > 0) & ~forest
    k = cfg.label_erode_px
    if k > 0:
        forest = ndi.binary_erosion(forest, FOUR, iterations=k, border_value=1)
        non = ndi.binary_erosion(non, FOUR, iterations=k, border_value=1)
    ndvi = np.nan_to_num(feats[names.index("ndvi")], nan=-1.0)
    forest &= ndvi >= cfg.forest_ndvi_floor
    lab = np.full(wc.shape, -1, dtype=np.int8)
    lab[non] = 0
    lab[forest] = 1
    if extra is not None:
        lab[extra >= 0] = extra[extra >= 0]
    return lab


def block_ids(shape, px, block_km):
    b = max(1, int(block_km * 1000 / px))
    rr, cc = np.indices(shape)
    return (rr // b) * int(np.ceil(shape[1] / b)) + cc // b


def _rf(cfg):
    return RandomForestClassifier(n_estimators=cfg.n_trees, min_samples_leaf=2, n_jobs=-1,
                                  random_state=cfg.seed)


def train_model(feats, lab, px, cfg, names):
    """Returns (fitted model, per-fold CV table, feature-importance Series)."""
    nb, h, w = feats.shape
    X = feats.reshape(nb, -1).T
    y = lab.reshape(-1)
    g = block_ids((h, w), px, cfg.cv_block_km).reshape(-1)
    ok = np.isfinite(X).all(axis=1) & (y >= 0)
    X, y, g = X[ok], y[ok], g[ok]
    rng = np.random.default_rng(cfg.seed)
    sel = []
    for c in (0, 1):
        idx = np.where(y == c)[0]
        if idx.size == 0:
            raise ValueError(f"No training pixels for class {c}: check the AOI, labels or NDVI floor")
        sel.append(rng.choice(idx, size=min(cfg.n_per_class, idx.size), replace=False))
    sel = np.concatenate(sel)
    X, y, g = X[sel], y[sel], g[sel]
    print(f"Training pixels: {int((y == 1).sum())} forest / {int((y == 0).sum())} non-forest "
          f"in {len(np.unique(g))} spatial blocks")

    rows = []
    n_splits = min(cfg.cv_folds, len(np.unique(g)))
    if n_splits >= 2:
        for i, (tr, te) in enumerate(GroupKFold(n_splits=n_splits).split(X, y, g)):
            if len(np.unique(y[te])) < 2 or len(np.unique(y[tr])) < 2:
                continue
            p = _rf(cfg).fit(X[tr], y[tr]).predict(X[te])
            rows.append(dict(fold=i + 1, accuracy=accuracy_score(y[te], p), f1_forest=f1_score(y[te], p),
                             precision=precision_score(y[te], p), recall=recall_score(y[te], p),
                             kappa=cohen_kappa_score(y[te], p)))
    cv = pd.DataFrame(rows)
    clf = _rf(cfg).fit(X, y)
    imp = pd.Series(clf.feature_importances_, index=names).sort_values(ascending=False)
    return clf, cv, imp


def predict_proba(clf, feats):
    """Forest probability map; NaN where any feature is missing."""
    nb, h, w = feats.shape
    X = feats.reshape(nb, -1).T
    ok = np.isfinite(X).all(axis=1)
    out = np.full(X.shape[0], np.nan, dtype=np.float32)
    if ok.any():
        out[ok] = clf.predict_proba(X[ok])[:, list(clf.classes_).index(1)]
    return out.reshape(h, w)
