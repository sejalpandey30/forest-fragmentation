import numpy as np
from ffa.config import Config
from ffa.postprocess import remove_small, fill_holes, temporal_smooth, postprocess
from ffa.model import train_model, predict_proba, clean_labels, block_ids


def test_remove_small_and_fill_holes():
    m = np.zeros((30, 30), bool); m[2:4, 2:4] = True; m[10:25, 10:25] = True
    assert remove_small(m, 10)[2, 2] == False and remove_small(m, 10)[15, 15]
    h = m.copy(); h[15, 15] = False
    assert fill_holes(h, 5)[15, 15] and not fill_holes(h, 0 + 1)[15, 15]


def test_temporal_smooth_removes_one_year_flicker():
    years = [1, 2, 3]
    p = {1: np.ones((3, 3)), 2: np.zeros((3, 3)), 3: np.ones((3, 3))}
    assert temporal_smooth(p, years, 3)[2].min() == 1.0


def test_postprocess_respects_valid_mask():
    cfg = Config(spatial_filter=1, min_patch_ha=0.01)
    prob = np.ones((10, 10)); valid = np.ones((10, 10), bool); valid[:, :5] = False
    out = postprocess(prob, valid, cfg, 10)
    assert out[:, :5].sum() == 0 and out[:, 5:].all()


def test_model_learns_with_spatial_cv_and_handles_nan():
    rng = np.random.default_rng(0); h = w = 60
    forest = (np.arange(w)[None, :] < 30).repeat(h, 0)
    ndvi = np.where(forest, 0.8, 0.2) + rng.normal(0, 0.05, (h, w))
    feats = np.stack([ndvi, rng.normal(0, 1, (h, w))]).astype("float32")
    wc = np.where(forest, 10, 40)
    cfg = Config(n_trees=30, n_per_class=2000, cv_block_km=0.3, cv_folds=3, label_erode_px=1)
    names = ["ndvi", "noise"]
    lab = clean_labels(wc, feats, names, cfg)
    assert (lab == -1).any()                                   # border pixels eroded away
    clf, cv, imp = train_model(feats, lab, 10, cfg, names)
    assert cv.accuracy.mean() > 0.95 and imp.index[0] == "ndvi"
    feats[:, :4, :4] = np.nan
    p = predict_proba(clf, feats)
    assert np.isnan(p[:4, :4]).all() and p[:, 35:].mean() < 0.1 and p[10:, :25].mean() > 0.9
    assert block_ids((10, 10), 10, 0.05).max() == 3
