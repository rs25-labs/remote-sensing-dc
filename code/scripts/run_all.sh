#!/bin/sh
# Rebuild every local result and the paper tables/figures from the CSVs in outputs/.
# Run from anywhere on the Mac (not in Colab): sh analysis/scripts/run_all.sh
# Inputs: outputs/census/{rings_summary,census_windows,site_labels,marinoni_results*}.csv and
# outputs/night/night_scenes_*.csv, which come from the Colab notebooks.
set -e
cd "$(dirname "$0")/.."
export PYTHONPATH=.
uv run pytest -q
uv run python scripts/run_crosssite.py
uv run python scripts/run_warehouse.py
uv run python scripts/run_cooling.py
uv run python scripts/run_energy.py
uv run python scripts/run_night.py
uv run python scripts/make_paper_outputs.py
PYTHONPATH=.:scripts uv run python scripts/make_supplement.py
