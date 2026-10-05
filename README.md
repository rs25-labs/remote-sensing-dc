# Data-center surface temperature census

Data, results and code for the paper *Land Change, Not Server Heat: A Satellite Census of Surface
Temperature Around 36 U.S. Data Centers* (Rhea Sreedhar; working title, under preparation for IEEE
Access).

We measured how ground-surface temperature changed around 36 U.S. data centers from before
construction to 2025–2026, using Landsat 8/9, and compared each site's centre (0–0.5 km) with land
3.5–5 km away in the same satellite image. We also compared data centers with 18 large warehouses,
tested cooling type and an energy-balance ceiling, re-tested a published 10 km MODIS metric with
placebo locations and two satellites, and looked at night changes with ECOSTRESS at four sites.

## What is here

| Folder | Contents |
|---|---|
| `data/sites/` | Site lists (data centers, warehouses, pilot points), cooling type with sources, land cover and aridity, Epoch AI power records |
| `data/landsat_rings/` | One file per site: every clear Landsat 8/9 image, mean surface temperature, NDVI, emissivity and albedo in five rings |
| `data/modis/` | Monthly MODIS Terra and Aqua surface temperature for every site and placebo point (10 km disk and 10–20 km ring), and the placebo points |
| `data/ecostress_night/` | Every ECOSTRESS night image over the four night-analysis sites: ring means and point values |
| `results/` | Per-site changes, periods, regressions, warehouse comparison, cooling test, energy ceiling, MODIS metric, night changes |
| `analysis/` | The paper's tables and figures, the supplementary material, and `numbers_ledger.csv` (every number in the paper and the file it comes from) |
| `code/` | Analysis package with tests, analysis scripts and the two Google Colab notebooks that produced the satellite data |

Start with `data/README.md` for a description of every file and column.

## Site IDs

Sites are named `operator-place-state`, for example `google-mesa-az`. Warehouses are `wh-` plus the
data center they were matched to and a number (`wh-google-red-oak-tx-1`); the four points used in
the pilot analysis are `pilot-` plus the data center. The site tables also give a `legacy_id`, the
ID used inside the code and notebooks (for example `EPOCH-05` for `google-mesa-az`).

## How the data were made

1. `code/notebooks/dc_heat_census.ipynb` (Google Colab with Google Earth Engine) exported the Landsat
   ring files, land cover and aridity, and the MODIS monthly files.
2. `code/notebooks/dc_night.ipynb` (Google Colab with a NASA Earthdata login) read the ECOSTRESS
   night images.
3. The scripts in `code/scripts/` turned those into the files in `results/` and `analysis/`
   (`run_all.sh` runs them in order). They were run in the project's working layout, where files
   have their legacy names; the release copies are renamed but otherwise identical.

Resampling uses fixed random seeds, so the statistics are exactly reproducible.

## Licence

- **Data and results** (except as below): Creative Commons Attribution 4.0 (CC BY 4.0).
  See `DATA-LICENSE.md`.
- **Warehouse locations** (`data/sites/warehouses.csv`) are derived from OpenStreetMap and are
  available under the Open Database License (ODbL). © OpenStreetMap contributors.
- **Epoch AI power records** (`data/sites/epoch_power_timelines.csv`): Epoch AI, "AI data centers",
  CC BY 4.0.
- **Code** (`code/`): MIT License. See [`LICENSE`](LICENSE).

## Citation
