"""Landscape fragmentation metrics for a binary forest raster (FRAGSTATS-style)."""
import numpy as np
from scipy import ndimage as ndi

FOUR = ndi.generate_binary_structure(2, 1)
KEYS = ["n_patches", "forest_ha", "forest_pct", "mean_patch_ha", "median_patch_ha",
        "largest_patch_index", "mean_perim_area", "mean_shape_index",
        "edge_density_m_ha", "core_pct", "eff_mesh_ha"]


def patch_metrics(forest, px=30.0, min_ha=1.0, edge_depth_m=100.0, landscape_ha=None):
    """forest: 2D bool array; px: pixel size (m).

    mean_perim_area   mean over patches of perimeter(m)/area(m2)
    mean_shape_index  mean of 0.25*perimeter/sqrt(area) (1 = square, higher = more convoluted)
    edge_density      total patch perimeter (m) per hectare of forest
    core_pct          % of forest further than edge_depth_m from any non-forest pixel
    eff_mesh_ha       effective mesh size, sum(a_i^2)/A_landscape (Jaeger 2000); lower = more fragmented
    The AOI border is not counted as edge.
    """
    forest = np.asarray(forest).astype(bool)
    landscape_ha = landscape_ha or forest.size * px * px / 1e4
    empty = {k: 0.0 for k in KEYS}
    lab, n = ndi.label(forest, structure=FOUR)
    if n == 0:
        return empty
    sizes = ndi.sum(forest, lab, index=np.arange(1, n + 1))
    min_px = max(1, int(min_ha * 10_000 / (px * px)))
    keep = np.where(sizes >= min_px)[0] + 1
    if keep.size == 0:
        return empty
    f = np.isin(lab, keep)
    lab_f = lab * f

    padded = np.pad(f, 1, mode="edge")
    h, w = f.shape
    edge = np.zeros(f.shape, dtype=np.int32)
    for dy, dx in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        edge += (f & ~padded[1 + dy:1 + dy + h, 1 + dx:1 + dx + w])

    area_m2 = sizes[keep - 1] * px * px
    perim_m = ndi.sum(edge, lab_f, index=keep) * px
    area_ha = area_m2 / 1e4
    total_ha = float(area_ha.sum())
    iters = max(1, int(round(edge_depth_m / px)))
    core = ndi.binary_erosion(f, structure=FOUR, iterations=iters, border_value=1)
    return dict(
        n_patches=int(keep.size),
        forest_ha=total_ha,
        forest_pct=total_ha / landscape_ha * 100,
        mean_patch_ha=float(area_ha.mean()),
        median_patch_ha=float(np.median(area_ha)),
        largest_patch_index=float(area_ha.max() / total_ha * 100),
        mean_perim_area=float((perim_m / area_m2).mean()),
        mean_shape_index=float((0.25 * perim_m / np.sqrt(area_m2)).mean()),
        edge_density_m_ha=float(perim_m.sum() / total_ha),
        core_pct=float(core.sum() / f.sum() * 100),
        eff_mesh_ha=float((area_ha ** 2).sum() / landscape_ha),
    )


def change_stats(f0, f1, px):
    """Loss/gain accounting between two forest maps."""
    ha = px * px / 1e4
    loss, gain = (f0 & ~f1).sum() * ha, (f1 & ~f0).sum() * ha
    base = f0.sum() * ha
    return dict(forest_start_ha=base, loss_ha=loss, gain_ha=gain, net_ha=gain - loss,
                loss_pct_of_start=100 * loss / base if base else 0.0)
