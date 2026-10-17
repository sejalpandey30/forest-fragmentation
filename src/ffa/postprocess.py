"""Turn probability maps into clean binary forest maps."""
import warnings
import numpy as np
from scipy import ndimage as ndi

FOUR = ndi.generate_binary_structure(2, 1)


def temporal_smooth(probs, years, window):
    """Median over neighbouring years (optional; blurs the timing of real loss, off by default)."""
    if window <= 1:
        return dict(probs)
    half, out = window // 2, {}
    for i, y in enumerate(years):
        lo, hi = max(0, i - half), min(len(years), i + half + 1)
        stack = np.stack([probs[years[j]] for j in range(lo, hi)])
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            out[y] = np.nanmedian(stack, axis=0)
    return out


def remove_small(mask, min_px):
    lab, n = ndi.label(mask, structure=FOUR)
    if n == 0:
        return mask
    sizes = ndi.sum(mask, lab, np.arange(1, n + 1))
    return np.concatenate([[False], sizes >= min_px])[lab]


def fill_holes(mask, hole_px):
    """Fill enclosed non-forest holes smaller than hole_px (holes touching the border are kept)."""
    lab, n = ndi.label(~mask, structure=FOUR)
    if n == 0:
        return mask
    sizes = ndi.sum(~mask, lab, np.arange(1, n + 1))
    border = np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))
    fill = np.concatenate([[False], sizes < hole_px])
    fill[border] = False
    return mask | fill[lab]


def postprocess(prob, valid, cfg, px):
    p = np.nan_to_num(prob, nan=0.0)
    if cfg.spatial_filter > 1:
        p = ndi.uniform_filter(p, cfg.spatial_filter, mode="nearest")
    f = (p >= cfg.threshold) & valid
    f = remove_small(f, max(1, int(cfg.min_patch_ha * 1e4 / (px * px))))
    f = fill_holes(f, max(1, int(cfg.hole_ha * 1e4 / (px * px))))
    return f & valid
