"""Figures, tables and the auto-generated results.md."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
import numpy as np
import pandas as pd
from scipy import stats

GREEN, BEIGE, RED, BLUE = (0.13, 0.45, 0.22), (0.93, 0.92, 0.88), (0.84, 0.15, 0.15), (0.15, 0.35, 0.85)
TREND_COLS = [("forest_ha", "Forest area (ha)"), ("n_patches", "Number of patches"),
              ("edge_density_m_ha", "Edge density (m/ha)"), ("mean_perim_area", "Mean perimeter/area (1/m)"),
              ("eff_mesh_ha", "Effective mesh size (ha)"), ("core_pct", "Core area (% of forest)")]


def _rgb(forest):
    img = np.ones(forest.shape + (3,)) * BEIGE
    img[forest] = GREEN
    return img


def trend_stats(df, cols=None):
    rows = []
    for c, _ in (cols or TREND_COLS):
        y, x = df[c].values, df["year"].values
        slope = stats.theilslopes(y, x)[0] if len(x) >= 3 else np.nan
        tau, p = stats.kendalltau(x, y) if len(x) >= 3 else (np.nan, np.nan)
        first = y[0]
        rows.append(dict(metric=c, first=y[0], last=y[-1], pct_change=100 * (y[-1] - first) / first if first else np.nan,
                         sen_slope_per_year=slope, kendall_tau=tau, kendall_p=p))
    return pd.DataFrame(rows)


def fig_maps(forests, y0, y1, extent, path, title, change):
    f0, f1 = forests[y0], forests[y1]
    chg = _rgb(f0 & f1)
    chg[f0 & ~f1], chg[f1 & ~f0] = RED, BLUE
    fig, ax = plt.subplots(1, 3, figsize=(17, 5.8))
    for a, img, t in zip(ax, [_rgb(f0), _rgb(f1), chg],
                         [f"Forest {y0}", f"Forest {y1}", f"Change {y0}-{y1}: loss {change['loss_ha']:.0f} ha "
                          f"({change['loss_pct_of_start']:.1f}%), gain {change['gain_ha']:.0f} ha"]):
        a.imshow(img, extent=extent, interpolation="nearest")
        a.set_title(t, fontsize=11); a.set_xlabel("km"); a.set_ylabel("km")
    ax[2].legend(handles=[Patch(color=GREEN, label="Stable forest"), Patch(color=RED, label="Loss"),
                          Patch(color=BLUE, label="Gain"), Patch(color=BEIGE, label="Non-forest")],
                 loc="lower right", fontsize=8, framealpha=0.9)
    fig.suptitle(title, fontsize=13, fontweight="bold")
    plt.tight_layout(); fig.savefig(path, dpi=160); plt.close(fig)


def fig_grid(forests, extent, path, title):
    ys = sorted(forests); cols = 3; rows = int(np.ceil(len(ys) / cols))
    fig, ax = plt.subplots(rows, cols, figsize=(5.2 * cols, 5 * rows), squeeze=False)
    for a in ax.ravel():
        a.axis("off")
    for a, y in zip(ax.ravel(), ys):
        a.axis("on"); a.imshow(_rgb(forests[y]), extent=extent, interpolation="nearest")
        a.set_title(str(y)); a.set_xticks([]); a.set_yticks([])
    fig.suptitle(title, fontsize=13, fontweight="bold")
    plt.tight_layout(); fig.savefig(path, dpi=130); plt.close(fig)


def fig_trends(df, tstats, path, title):
    fig, ax = plt.subplots(2, 3, figsize=(16, 8))
    for a, (c, t) in zip(ax.ravel(), TREND_COLS):
        a.plot(df.year, df[c], marker="o", color="#1b6b3a")
        r = tstats[tstats.metric == c].iloc[0]
        a.set_title(f"{t}\n{r['pct_change']:+.1f}% | Sen slope {r['sen_slope_per_year']:+.3g}/yr", fontsize=10)
        a.set_xticks(df.year); a.grid(alpha=0.3)
    fig.suptitle(title, fontsize=13, fontweight="bold")
    plt.tight_layout(); fig.savefig(path, dpi=150); plt.close(fig)


def fig_validation(cv, val, path):
    labels, vals, errs = [], [], []
    if len(cv):
        labels.append("Spatial-CV F1\n(mean ± sd)"); vals.append(cv.f1_forest.mean()); errs.append(cv.f1_forest.std())
    for k, v in val.items():
        if "f1" in v:
            labels.append(k.replace("_", "\n")); vals.append(v["f1"]); errs.append(0)
    fig, a = plt.subplots(figsize=(1.8 * max(3, len(labels)) + 2, 4.5))
    a.bar(labels, vals, yerr=errs, color="#2e8b57", capsize=4)
    a.set_ylim(0, 1); a.set_ylabel("F1 score"); a.set_title("Accuracy assessment")
    for i, v in enumerate(vals):
        a.text(i, v + 0.02, f"{v:.2f}", ha="center")
    plt.tight_layout(); fig.savefig(path, dpi=150); plt.close(fig)


def fig_importance(imp, path):
    top = imp.head(12)[::-1]
    fig, a = plt.subplots(figsize=(6.5, 4.8))
    a.barh(top.index, top.values, color="#3b7d4f"); a.set_title("Random Forest feature importance")
    plt.tight_layout(); fig.savefig(path, dpi=150); plt.close(fig)


def md_table(df, digits=3):
    d = df.copy()
    for c in d.columns:
        if d[c].dtype.kind == "f":
            d[c] = d[c].map(lambda v: f"{v:.{digits}g}")
    head = "| " + " | ".join(map(str, d.columns)) + " |\n|" + "---|" * len(d.columns) + "\n"
    return head + "\n".join("| " + " | ".join(map(str, r)) + " |" for r in d.values.tolist()) + "\n"
