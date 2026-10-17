# Forest Fragmentation 🌲✨

Welcome! This project explores forest fragmentation — what it is, how it changes over time, and why it matters. Whether you’re a curious human, a budding ecologist, or a developer who loves nature and data, this repo gives you approachable tools and visualizations to play with forest-change data.

![Forest change demo](demo_fig1_forest_change.png)

Why this project? Because forests are not just trees — they are habitats, climate buffers, and living communities. When forests break into smaller pieces (fragment), ecosystems suffer. Forest Fragmentation helps you measure, visualize, and understand those changes.

Highlights
- Play with visual demos: demo_fig1_forest_change.png and demo_fig3_fragmentation_trends.png show what fragmentation and trends can look like.
- Ready-to-run code: `run.py` gets you started quickly.
- Modular codebase: core code lives in `src/` so you can reuse or extend analyses.
- Reproducible environment: use `requirements.txt` or `pyproject.toml` to reproduce results.
- Tests: `tests/` contains automated checks so you can tweak confidently.

Getting started (5 minutes)
1. Clone this repo:
   git clone https://github.com/sejalpandey30/forest-fragmentation.git
2. Install dependencies (recommend a venv):
   python -m venv .venv
   source .venv/bin/activate  # or `.\.venv\Scripts\activate` on Windows
   pip install -r requirements.txt
3. Run the demo script:
   python run.py

What this does
- run.py launches a short demo pipeline that walks through key steps: loading data, computing fragmentation metrics, and producing example visuals (see `demo_fig1_forest_change.png`, `demo_fig3_fragmentation_trends.png`).
- `src/` holds the functions and modules that implement the core logic — think of it as the brain of the project. Peek inside to adapt metrics or add new visualizations.

Project structure (quick tour)
- src/ — core code and utilities (analysis, metrics, plotting)
- configs/ — configuration files for experiments and reproducible runs
- docs/ — background, extended explanations, and how-tos
- tests/ — unit and integration tests
- run.py — simple entry point to run the demo
- requirements.txt, pyproject.toml — dependency declarations
- demo_fig1_forest_change.png, demo_fig3_fragmentation_trends.png — example outputs you can inspect or use in reports
- CITATION.cff — how to cite this work in papers or presentations
- LICENSE — licensing information

How you can help (and make an impact)
- Try the demo: run the code and open the images. If something looks off, file an issue with a screenshot and steps to reproduce.
- Add a metric: think of connectivity, edge density, or core patch size? Implement it in `src/` and add tests in `tests/`.
- Improve docs: add a notebook walkthrough to `docs/` or a short explainer for non-technical audiences.
- Share results: if you publish work using these scripts, add your DOI to CITATION.cff and cite the repo.

A friendly challenge
Fork this repo, change one metric, and create a short before/after visualization — then open a PR. Small changes can reveal big ecological stories.

Citing this work
Please use the information in CITATION.cff when referencing this project in academic work.

License
This project is available under the terms in `LICENSE`.

Contact
Created with care by @sejalpandey30. Got ideas, bugs, or collaborators? Open an issue or a PR — I’d love to hear from you.

Thanks for checking out Forest Fragmentation — build, learn, and protect the green!
