"""Offline synthetic demo: exercises the full pipeline without any download.
Figures are produced from SIMULATED data and are labelled as such. Never present them as results."""
from copy import copy
import numpy as np
from scipy import ndimage as ndi
from .config import Config
from .pipeline import analyze
from .validation import prf


def synthetic_landscape(size=360, years=range(2020, 2026), seed=1):
    rng = np.random.default_rng(seed)
    base = ndi.gaussian_filter(rng.normal(size=(size, size)), 6)
    cur = base > np.quantile(base, 0.42)
    truth = {}
    for i, y in enumerate(years):
        if i:
            edge = cur & ~ndi.binary_erosion(cur)
            ys, xs = np.nonzero(edge)
            for j in rng.choice(len(ys), 40, replace=False):
                r = rng.integers(2, 7)
                yy, xx = np.ogrid[:size, :size]
                cur &= ((yy - ys[j]) ** 2 + (xx - xs[j]) ** 2) > r * r
            if i in (2, 4):                                    # a new road cuts through
                a, b = rng.integers(0, size, 2)
                for t in range(size):
                    cur[min(size - 1, (a + t // 3) % size), t] = False
        truth[y] = cur.copy()
    return truth


def run_demo(out_dir="outputs/demo"):
    cfg = Config(name="synthetic-demo", start_year=2020, end_year=2025, train_year=2021, res=30,
                 use_terrain=False, n_trees=100, n_per_class=15000, cv_block_km=1.5, forest_ndvi_floor=0.3)
    years = list(range(cfg.start_year, cfg.end_year + 1))
    truth = synthetic_landscape(years=years)
    rng = np.random.default_rng(7)
    names = ["blue", "green", "red", "nir", "swir16", "ndvi", "ndwi", "nbr", "ndvi_tstd", "elev"]
    feats = {}
    for y in years:
        t = truth[y].astype(float)
        ndvi = 0.30 + 0.48 * t + ndi.gaussian_filter(rng.normal(0, 0.9, t.shape), 1.2)
        f = [0.05 + 0.02 * (1 - t) + rng.normal(0, 0.012, t.shape) for _ in range(3)]
        nir = 0.15 + 0.25 * t + rng.normal(0, 0.04, t.shape)
        swir = 0.2 - 0.07 * t + rng.normal(0, 0.03, t.shape)
        ndwi = -0.5 * ndvi + rng.normal(0, 0.05, t.shape)
        nbr = 0.8 * ndvi + rng.normal(0, 0.06, t.shape)
        tstd = 0.15 - 0.08 * t + rng.normal(0, 0.04, t.shape)
        elev = ndi.gaussian_filter(rng.normal(0, 1, t.shape), 20)
        feats[y] = np.stack(f + [nir, swir, ndvi, ndwi, nbr, tstd, elev]).astype("float32")[[0, 1, 2, 3, 4, 5, 6, 7, 8, 9]]
    wc = np.where(truth[cfg.train_year], 10, 40)               # WorldCover-like labels with simulated errors
    g = ndi.gaussian_filter(rng.normal(size=wc.shape), 2)
    wrong = g > np.quantile(g, 0.95)
    wc = np.where(wrong, np.where(wc == 10, 40, 10), wc)

    def truth_validator(forests, valid):
        r = {y: prf(forests[y], truth[y], valid) for y in forests}
        loss = prf(forests[years[0]] & ~forests[years[-1]], truth[years[0]] & ~truth[years[-1]], valid)
        return dict(f1=float(np.mean([v["f1"] for v in r.values()])), precision=loss["precision"], recall=loss["recall"],
                    note="mean per-year forest F1 vs simulated truth; precision/recall refer to loss pixels")

    title = "SYNTHETIC DEMO (simulated data, not real results)"
    return analyze(cfg, feats, names, wc, 30.0, out_dir, None, {"simulated_truth": truth_validator}, None, title=title)
