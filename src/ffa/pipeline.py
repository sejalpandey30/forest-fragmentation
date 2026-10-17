"""End-to-end analysis: labels -> model -> maps -> metrics -> validation -> figures/tables/report."""
import json
from pathlib import Path
import numpy as np
import pandas as pd
from . import report as R
from .config import to_dict
from .metrics import patch_metrics, change_stats
from .model import clean_labels, train_model, predict_proba
from .postprocess import postprocess, temporal_smooth
from .validation import worldcover_validator, hansen_validator


def sensitivity(probs, valid, cfg, px, years, landscape_ha):
    """Re-run post-processing under alternative settings; do the conclusions survive?"""
    from copy import copy
    rows = []
    for tw in (1, 3):
        smoothed = temporal_smooth(probs, years, tw)
        for sf in (1, 3, 5):
            for mh in (0.5, 1.0, 2.0):
                c = copy(cfg); c.spatial_filter, c.min_patch_ha = sf, mh
                m0 = patch_metrics(postprocess(smoothed[years[0]], valid, c, px), px, mh, cfg.edge_depth_m, landscape_ha)
                m1 = patch_metrics(postprocess(smoothed[years[-1]], valid, c, px), px, mh, cfg.edge_depth_m, landscape_ha)
                rows.append(dict(temporal_window=tw, spatial_filter=sf, min_patch_ha=mh,
                                 d_forest_pct=100 * (m1["forest_ha"] / m0["forest_ha"] - 1) if m0["forest_ha"] else np.nan,
                                 d_edge_density_pct=100 * (m1["edge_density_m_ha"] / m0["edge_density_m_ha"] - 1) if m0["edge_density_m_ha"] else np.nan,
                                 d_n_patches_pct=100 * (m1["n_patches"] / m0["n_patches"] - 1) if m0["n_patches"] else np.nan,
                                 d_eff_mesh_pct=100 * (m1["eff_mesh_ha"] / m0["eff_mesh_ha"] - 1) if m0["eff_mesh_ha"] else np.nan))
    return pd.DataFrame(rows)


def analyze(cfg, feats, names, wc, px, out, extra_labels=None, validators=None, grid=None, title=""):
    years = list(range(cfg.start_year, cfg.end_year + 1))
    out = Path(out)
    for d in ("tables", "figures", "rasters"):
        (out / d).mkdir(parents=True, exist_ok=True)

    lab = clean_labels(wc, feats[cfg.train_year], names, cfg, extra_labels)
    clf, cv, imp = train_model(feats[cfg.train_year], lab, px, cfg, names)
    if len(cv):
        print(f"Spatial-block CV: accuracy {cv.accuracy.mean():.3f} ± {cv.accuracy.std():.3f} | "
              f"F1(forest) {cv.f1_forest.mean():.3f} ± {cv.f1_forest.std():.3f} | kappa {cv.kappa.mean():.3f}")

    probs = {y: predict_proba(clf, feats[y]) for y in years}
    valid = np.all([np.isfinite(probs[y]) for y in years], axis=0)
    landscape_ha = valid.sum() * px * px / 1e4
    sm = temporal_smooth(probs, years, cfg.temporal_window)
    forests = {y: postprocess(sm[y], valid, cfg, px) for y in years}

    rows = []
    for y in years:
        m = patch_metrics(forests[y], px, cfg.min_patch_ha, cfg.edge_depth_m, landscape_ha)
        rows.append({"year": y, "valid_frac": float(np.isfinite(feats[y][0]).mean()), **m})
        print(y, {k: round(v, 3) for k, v in m.items() if k in ("forest_ha", "n_patches", "edge_density_m_ha", "eff_mesh_ha")})
    df = pd.DataFrame(rows)
    tstats = R.trend_stats(df)
    change = change_stats(forests[years[0]], forests[years[-1]], px)
    sens = sensitivity(probs, valid, cfg, px, years, landscape_ha)

    val = {}
    for name, fn in (validators or {}).items():
        try:
            r = fn(forests, valid)
            if r:
                val[name] = r
                print(f"Validation [{name}]: F1 {r['f1']:.3f} (precision {r['precision']:.3f}, recall {r['recall']:.3f})")
        except Exception as e:                                   # network / asset problems must not kill the run
            print(f"Validation [{name}] skipped: {e}")

    # outputs
    df.to_csv(out / "tables/landscape_metrics.csv", index=False)
    tstats.to_csv(out / "tables/trend_statistics.csv", index=False)
    cv.to_csv(out / "tables/cross_validation.csv", index=False)
    imp.to_csv(out / "tables/feature_importance.csv", header=["importance"])
    sens.to_csv(out / "tables/sensitivity.csv", index=False)
    (out / "tables/validation.json").write_text(json.dumps(val, indent=2))
    (out / "tables/change_accounting.json").write_text(json.dumps(change, indent=2))
    (out / "config_used.json").write_text(json.dumps(to_dict(cfg), indent=2))
    h, w = valid.shape
    extent = (0, w * px / 1000, 0, h * px / 1000)
    y0, y1 = years[0], years[-1]
    R.fig_maps(forests, y0, y1, extent, out / "figures/fig1_forest_change.png", title, change)
    R.fig_grid(forests, extent, out / "figures/fig2_forest_timeseries.png", f"{title} - forest extent by year")
    R.fig_trends(df, tstats, out / "figures/fig3_fragmentation_trends.png", f"{title} - fragmentation metrics")
    R.fig_validation(cv, val, out / "figures/fig4_accuracy.png")
    R.fig_importance(imp, out / "figures/fig5_feature_importance.png")
    if grid is not None:
        import rasterio
        for y in years:
            with rasterio.open(out / f"rasters/forest_{y}.tif", "w", driver="GTiff", height=h, width=w, count=1,
                               dtype="uint8", crs=grid["crs"], transform=grid["transform"], compress="lzw") as dst:
                dst.write(forests[y].astype("uint8"), 1)
    _write_results(cfg, out, title, df, tstats, change, cv, val, sens, len(years))
    print(f"\nAll outputs written to {out}/")
    return dict(df=df, trends=tstats, change=change, cv=cv, validation=val, sensitivity=sens, forests=forests)


def _write_results(cfg, out, title, df, tstats, change, cv, val, sens, n):
    s = [f"# Results: {title}\n", f"AOI bbox (lon/lat): {cfg.bbox} | pixel {cfg.res} m | years {cfg.start_year}-{cfg.end_year} "
         f"| training labels year {cfg.train_year}\n"]
    if len(cv):
        s += ["## Classification accuracy (spatial-block cross-validation)\n",
              R.md_table(pd.DataFrame({"metric": ["accuracy", "F1 (forest)", "precision", "recall", "kappa"],
                                       "mean": [cv.accuracy.mean(), cv.f1_forest.mean(), cv.precision.mean(), cv.recall.mean(), cv.kappa.mean()],
                                       "sd": [cv.accuracy.std(), cv.f1_forest.std(), cv.precision.std(), cv.recall.std(), cv.kappa.std()]}))]
    if val:
        s += ["## External validation\n", R.md_table(pd.DataFrame([{"reference": k, **v} for k, v in val.items()]))]
    s += ["## Landscape metrics by year\n", R.md_table(df[["year", "forest_ha", "n_patches", "edge_density_m_ha", "mean_perim_area", "eff_mesh_ha", "core_pct"]], 4),
          "## Trend statistics\n", R.md_table(tstats, 3),
          f"Note: with n = {n} annual observations, Kendall's test has low power; interpret p-values cautiously.\n",
          "## Change accounting\n", R.md_table(pd.DataFrame([change]), 4),
          "## Sensitivity to post-processing choices\n",
          f"Edge density increased from first to last year in {int((sens.d_edge_density_pct > 0).sum())}/{len(sens)} settings; "
          f"effective mesh size decreased in {int((sens.d_eff_mesh_pct < 0).sum())}/{len(sens)}; "
          f"forest area decreased in {int((sens.d_forest_pct < 0).sum())}/{len(sens)}.\n"]
    (out / "results.md").write_text("\n".join(s))


def run(cfg):
    """Real-data run for one site."""
    from . import data as D
    from .validation import prf  # noqa: F401
    years = list(range(cfg.start_year, cfg.end_year + 1))
    all_years = sorted(set(years) | {cfg.train_year})
    names = D.feature_names(cfg)
    das = {}
    for i, y in enumerate(all_years, 1):
        print(f"[{i}/{len(all_years)}] features {y}")
        das[y] = D.get_features(cfg, y)
    template = das[cfg.train_year].isel(band=0, drop=True)
    px = float(abs(template.rio.resolution()[0]))
    feats = {y: da.values for y, da in das.items()}
    print("Loading ESA WorldCover labels...")
    wc = D.worldcover(cfg, template, 2021)
    extra = D.load_extra_labels(cfg.extra_labels, template, cfg.crs) if cfg.extra_labels else None

    validators = {}
    if cfg.validate_worldcover_2020 and 2020 in years:
        try:
            validators["worldcover_2020"] = worldcover_validator(cfg, D.worldcover(cfg, template, 2020))
        except Exception as e:
            print("WorldCover 2020 validator unavailable:", e)
    if cfg.validate_hansen:
        try:
            validators["hansen_loss"] = hansen_validator(cfg, D.hansen_layer(cfg, template, "treecover2000"),
                                                         D.hansen_layer(cfg, template, "lossyear"))
        except Exception as e:
            print("Hansen validator unavailable:", e)
    out = Path(cfg.out_dir) / cfg.name
    grid = dict(crs=cfg.crs, transform=template.rio.transform())
    return analyze(cfg, feats, names, wc, px, out, extra, validators, grid, title=f"{cfg.name}, Western Ghats")
