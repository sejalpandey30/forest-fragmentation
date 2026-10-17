# Forest Fragmentation

A Python-based project for analyzing and visualizing forest fragmentation patterns over space and time.

![Forest change demo](demo_fig1_forest_change.png)

## Overview

Forest fragmentation refers to the process by which continuous forest cover becomes divided into smaller, isolated patches. This can happen because of roads, agriculture, urban growth, logging, or other land-use changes. Fragmentation often disrupts habitat connectivity, reduces biodiversity, and affects ecological resilience.

This repository provides a simple, reproducible workflow to:
- process forest-cover data,
- detect fragmented forest patches,
- compute relevant landscape metrics,
- and generate visual outputs for interpretation and reporting.

## Why this project matters

Forest ecosystems are critical for biodiversity, carbon storage, climate regulation, and watershed health. As forests become more fragmented, species have fewer safe habitats and movement corridors, and ecosystem functions can degrade.

This project helps make those landscape changes easier to understand through clear, data-driven analysis.

## Project workflow

The standard workflow is straightforward:

1. Load forest cover data
2. Identify connected forest patches
3. Quantify fragmentation metrics
4. Generate visual summaries and reports
5. Interpret change over time or across locations

## Repository structure

- `src/` — core analysis, metric computation, and plotting logic
- `run.py` — entry point for running the demo workflow
- `configs/` — configuration files for project runs
- `docs/` — documentation, notes, and supporting materials
- `tests/` — automated tests for validation
- `requirements.txt` — Python dependencies
- `pyproject.toml` — project configuration and packaging metadata
- `demo_fig1_forest_change.png` — example forest change visualization
- `demo_fig3_fragmentation_trends.png` — example fragmentation trend visualization
- `CITATION.cff` — citation metadata
- `LICENSE` — project license

## Getting started

### Prerequisites

- Python 3.x
- A virtual environment is recommended

### Installation

```bash
git clone https://github.com/sejalpandey30/forest-fragmentation.git
cd forest-fragmentation
python -m venv .venv
source .venv/bin/activate   # On Windows: .\.venv\Scripts\activate
pip install -r requirements.txt
```

### Run the demo

```bash
python run.py
```

This executes the example workflow and produces the generated analysis outputs in the repository.

## What the demo shows

The example outputs in this repository demonstrate:
- forest cover change patterns,
- patch-level fragmentation,
- and overall trends in landscape structure.

These visualizations are useful for:
- research summaries,
- presentations,
- technical documentation,
- and ecological analysis workflows.

## Simple technical explanation

At a high level, the project treats forest cover as a binary map where cells are classified as forest or non-forest. Neighboring forest cells are grouped into connected patches, and the resulting structure is analyzed using landscape metrics such as:

- number of forest patches,
- average patch size,
- largest patch size,
- edge density,
- and landscape connectivity indicators.

These metrics help describe how fragmented a landscape is and how that structure changes over time.

## Contributing

Contributions are welcome. If you would like to improve the analysis, add new metrics, expand the documentation, or help refine the visual outputs, please open an issue or submit a pull request.

## Citation

Use the metadata in `CITATION.cff` when citing this project in academic or research work.

## License

This project is licensed under the terms specified in the `LICENSE` file.

## Contact

Maintainer: @sejalpandey30
