# Code

- `dc_heat/`: the analysis package (ring contrasts, before/after statistics, construction dating,
  cross-site tests, the MODIS metric, ECOSTRESS sampling, energy ceiling). Tests are in `tests/`.
- `scripts/`: the analysis scripts, run in order by `run_all.sh`, plus `find_warehouses.py`
  (OpenStreetMap search for warehouse candidates) and `find_purpleair.py` (PurpleAir sensor counts;
  needs your own PurpleAir read key in `PURPLEAIR_API_KEY`).
- `notebooks/`: the Google Colab notebooks that produced the satellite data.
  `dc_heat_census.ipynb` needs a Google Earth Engine project (set `EE_PROJECT` in Part 0);
  `dc_night.ipynb` needs a NASA Earthdata login.

## Running the tests

Requires [uv](https://docs.astral.sh/uv/):

```bash
cd code
uv run pytest -q
```

## Paths and IDs

The scripts were run in the project's working layout and read files by their working names
(for example `outputs/census/rings_summary.csv`, which is `results/landsat_ring_changes.csv` here)
and use the working site IDs, given as `legacy_id` in `data/sites/*.csv`. The data in this
repository are the same files, renamed. To rerun a script against the release data, map the
paths at the top of the script and the IDs through `legacy_id`.
