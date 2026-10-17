from ffa.demo import run_demo


def test_demo_runs_end_to_end(tmp_path):
    res = run_demo(str(tmp_path))
    assert res["cv"].f1_forest.mean() > 0.9
    for f in ["figures/fig1_forest_change.png", "figures/fig3_fragmentation_trends.png",
              "tables/landscape_metrics.csv", "results.md"]:
        assert (tmp_path / f).exists()
    assert res["change"]["loss_ha"] > res["change"]["gain_ha"]
