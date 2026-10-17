import numpy as np
from ffa.metrics import patch_metrics, change_stats


def square():
    a = np.zeros((50, 50), bool); a[10:30, 10:30] = True   # 20x20 px at 10 m = 4 ha
    return a


def test_single_square_patch():
    m = patch_metrics(square(), px=10, min_ha=0.5)
    assert m["n_patches"] == 1 and abs(m["forest_ha"] - 4.0) < 1e-9
    assert abs(m["mean_perim_area"] - 800 / 40000) < 1e-12
    assert abs(m["mean_shape_index"] - 1.0) < 1e-9            # perfect square
    assert abs(m["eff_mesh_ha"] - 16 / 25) < 1e-9             # 4^2 / 25 ha landscape
    assert abs(m["forest_pct"] - 16.0) < 1e-9


def test_fragmentation_raises_edge_and_lowers_mesh_and_core():
    solid = np.ones((60, 60), bool); split = solid.copy(); split[:, 30] = False
    s, f = patch_metrics(solid, 10, 0.1), patch_metrics(split, 10, 0.1)
    assert s["n_patches"] == 1 and f["n_patches"] == 2
    assert f["mean_perim_area"] > s["mean_perim_area"] and f["edge_density_m_ha"] > s["edge_density_m_ha"]
    assert f["eff_mesh_ha"] < s["eff_mesh_ha"] and f["core_pct"] < s["core_pct"]


def test_small_patches_filtered_and_empty_ok():
    a = np.zeros((20, 20), bool); a[0:2, 0:2] = True
    assert patch_metrics(a, 10, min_ha=1.0)["n_patches"] == 0
    assert patch_metrics(np.zeros((5, 5), bool))["forest_ha"] == 0


def test_change_stats():
    f0 = square(); f1 = f0.copy(); f1[10:20, 10:30] = False
    c = change_stats(f0, f1, 10)
    assert abs(c["loss_ha"] - 2.0) < 1e-9 and c["gain_ha"] == 0 and abs(c["loss_pct_of_start"] - 50) < 1e-9
