# Quantifying Forest Habitat Fragmentation in the Western Ghats

A reproducible remote-sensing pipeline using Sentinel-2, Random Forest classification and landscape metrics to quantify changes in forest fragmentation (2020–2025). This repository contains code, configuration and demonstration outputs for research and reproducible analyses.

Authors: YOUR NAME
Contact: your.email@example.com
Status: research prototype (v0.2)

---

## Abstract

Habitat fragmentation—the subdivision of continuous forest into smaller, isolated patches—can drive biodiversity loss by increasing edge effects and reducing core habitat. This project provides a reproducible workflow to map forest/non-forest from Sentinel-2 imagery, compute landscape fragmentation metrics, and analyse trends and sensitivities across multiple sites in the Western Ghats.

The code and data access are designed for transparency and reproducibility: all input datasets used are open (Sentinel-2 L2A, Copernicus DEM, ESA WorldCover, Hansen Global Forest Change). The repository includes a small synthetic demo (for testing) and configuration files to run site-specific analyses.

---

## Key research questions

- RQ1: Do fragmentation metrics (edge density, perimeter-to-area ratio, shape index, effective mesh size, core-area share) show directional change between 2020 and 2025?
- RQ2: Is observed change driven primarily by area loss or by spatial reconfiguration (splitting/perforation)?
- RQ3: How robust are conclusions to pre-processing choices (minimum patch size, smoothing, temporal filtering)?

Working hypothesis: fragmentation indicators increase (more edge, higher P/A) while connectivity measures (core-area share, effective mesh size) decrease, even where total forest area changes modestly.

---

## Study areas

- Valparai / Anamalai Plateau — rainforest fragments inside a tea-estate matrix. Config: `configs/valparai.yaml`.
- Kodagu (Coorg) — coffee agroforestry matrix; replication site. Config: `configs/kodagu.yaml`.

Add a site by copying a YAML config in `configs/` and updating the `bbox` and metadata.

---

## Datasets (open)

- Sentinel-2 L2A (10–20 m) — optical features (via AWS Earth Search STAC / Copernicus)
- Copernicus DEM GLO-30 — elevation and slope (via AWS Earth Search STAC)
- ESA WorldCover v200/v100 — label source for training / label-transfer checks
- Hansen Global Forest Change — independent loss validation

See code in src/ffa/data.py for the exact access routines and caching behaviour.

---

## Methods (pipeline overview)

1. Image compositing: annual dry-season composites (1 Jan–30 Apr), cloud-masked and aggregated to reduce residual cloud and seasonal noise.
2. Feature extraction: spectral bands, vegetation indices (NDVI, NDWI, NBR, NDMI), temporal NDVI std, local NDVI texture, elevation and slope (≈17 features).
3. Labels: WorldCover tree cover as positive class; border/mixed pixels eroded; low NDVI pixels filtered to reduce label noise.
4. Classifier: Random Forest (200 trees), class-balanced sampling. Trained on 2021 labels and applied across years.
5. Post-processing: probability thresholding, 3×3 smoothing, remove patches < 1 ha, fill holes < 0.5 ha. Optional temporal median filter.
6. Landscape metrics: patch count, perimeter/area, shape index, edge density, core-area share (≥100 m buffer), effective mesh size (Jaeger 2000).
7. Trend analysis: percent change, Theil–Sen slope, Kendall's τ; sensitivity analysis across parameter combinations.

---

## Validation design

- Spatial block cross-validation (2 km blocks, 5 folds) to avoid spatial leakage between train/test.
- Label-transfer check: test maps produced for 2020 against WorldCover 2020.
- Change validation: compare detected loss to Hansen annual loss (noting Hansen maps stand-replacing loss only).
- Sensitivity: run combinations of temporal window, smoothing and minimum patch size to report robustness.

---

## Quick start

```bash
git clone https://github.com/sejalpandey30/forest-fragmentation
cd forest-fragmentation
python -m venv .venv && source .venv/bin/activate    # macOS/Linux
# Windows: .venv\Scripts\activate
pip install -r requirements.txt
pytest -q
python run.py demo                     # synthetic demo (~1 min)
python run.py analyze --config configs/valparai.yaml --res 60  # fast test
python run.py analyze --config configs/valparai.yaml          # full run (default resolution)
```

Composites and intermediate data are cached under `data/cache/` for faster re-runs.

---

## Typical outputs (written to outputs/<site>/)

- figures/fig1_forest_change.png — first-year, last-year and loss/gain map (example below)
- figures/fig2_forest_timeseries.png — forest extent per year
- figures/fig3_fragmentation_trends.png — metrics time series, percent change and Sen slope (example below)
- figures/fig4_accuracy.png, fig5_feature_importance.png — validation and variable importance
- tables/*.csv, *.json — metrics, trend statistics, CV folds, sensitivity and validation summaries
- rasters/forest_YYYY.tif — georeferenced binary maps for GIS
- results.md — auto-generated run summary suitable for inclusion in manuscripts

---

## Demonstration outputs (synthetic demo)

The images below illustrate the demo outputs produced by `python run.py demo`. These are synthetic and intended to demonstrate the pipeline; they are not empirical findings about the Western Ghats.

![Demo: forest change map](demo_fig1_forest_change.png)

![Demo: fragmentation trends](demo_fig3_fragmentation_trends.png)

---

## Limitations and threats to validity

- Plantations (tea, coffee shade, rubber) can be misclassified as native forest; WorldCover does not distinguish plantations from natural forest.
- Label transfer across years assumes stable spectral relationships; sensor drift, phenology and residual clouds can induce artefactual change.
- Spatial resolution (30 m) misses narrow features (minor roads, small clearings); run at 10 m on small areas for finer edges.
- Hansen loss detects stand-replacing loss and will undercount subtle edge degradation.
- Metric edge effects at the analysis window boundary must be interpreted cautiously.
- No field validation in repository — adding field plots or high-resolution manual labels would strengthen accuracy assessment.

---

## Reproducibility and extensibility

- All analysis is deterministic given the same inputs and random seed. Results and figures are saved under `outputs/<site>/` and `results.md` provides a concise run summary for papers.
- To extend: add plantation-native separation labels, include driver datasets (roads, protected areas), test deep segmentation (U-Net) at 10 m, or link metrics to species occurrence data.

---

## How to cite

If you use this code in research, cite the repository and relevant datasets (Sentinel-2, WorldCover, Hansen). See `CITATION.cff` for a machine-readable citation.

---

## License

Code: MIT. Input datasets are subject to their respective terms (Copernicus, ESA WorldCover CC BY 4.0, Hansen data terms).
