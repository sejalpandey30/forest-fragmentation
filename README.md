# Forest Fragmentation 🌲

A small, friendly toolkit to measure and visualize how forests break into smaller pieces over time.

![Forest change demo](demo_fig1_forest_change.png)

1) Grab the code
- git clone https://github.com/sejalpandey30/forest-fragmentation.git

2) Set up your environment (quick)
- python -m venv .venv
- source .venv/bin/activate  # Windows: .\.venv\Scripts\activate
- pip install -r requirements.txt

3) Run the demo
- python run.py
- What happens: the demo finds forest patches, computes simple numbers about them, and saves example PNGs in the repo.

4) Open the outputs
- demo_fig1_forest_change.png — a sample map showing forest and change.
- demo_fig3_fragmentation_trends.png — a simple chart of fragmentation values over time.

5) Quick, plain explanation of what the code does
- Input: a map where each cell is forest (1) or not (0).
- Group neighboring forest cells into patches.
- Compute basic metrics: number of patches, average patch size, largest patch share, and edge exposure.
- Save maps and charts to help you see where and how fragmentation is changing.

6) Repo layout (where things live)
- src/        — core code: detection, metrics, plotting
- run.py      — demo entry script (fast path)
- configs/    — optional run settings
- docs/       — add notebooks or guides here
- tests/      — simple checks
- requirements.txt, pyproject.toml — installable deps
- demo_fig1_forest_change.png, demo_fig3_fragmentation_trends.png — example outputs
- CITATION.cff / LICENSE — citation and license info

7) Simple tips and next steps
- If patch counts look off, check if input is binary (0/1) and whether 4-neighbor or 8-neighbor rules are used.
- To try your data, replace the example input in the demo with your raster (binary forest map).
- To add a metric: implement the function in src/ and add a small test in tests/.

8) Want to help?
- File an issue with a screenshot and steps if something breaks.
- Fork, add code in src/, add tests, and open a PR.

Maintainer: @sejalpandey30

License: see LICENSE
