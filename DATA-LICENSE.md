# Data licence and credits

Except where noted below, the data and results in this repository are released under the
**Creative Commons Attribution 4.0 International licence (CC BY 4.0)**:
https://creativecommons.org/licenses/by/4.0/. You may share and adapt them for any purpose, with
credit to the paper and this repository.

## Third-party sources

| Source | Used for | Terms |
|---|---|---|
| U.S. Geological Survey, Landsat 8/9 Collection 2 Level 2 | `data/landsat_rings/` | Public domain (U.S. Government) |
| NASA, MODIS MOD11A1 / MYD11A1 v6.1 | `data/modis/` | Public domain (U.S. Government); credit NASA LP DAAC |
| NASA, ECOSTRESS ECO_L2T_LSTE v002 | `data/ecostress_night/` | Public domain (U.S. Government); credit NASA LP DAAC |
| USGS National Land Cover Database (2019, 2021 releases) | `data/sites/land_cover_aridity.csv` | Public domain (U.S. Government) |
| TerraClimate (Abatzoglou et al., 2018) | aridity in `data/sites/land_cover_aridity.csv` | See the TerraClimate data terms; cite Abatzoglou et al. (2018) |
| Epoch AI, "AI data centers" | `data/sites/epoch_power_timelines.csv`, construction and operation dates | CC BY 4.0; cite Epoch AI |
| OpenStreetMap | `data/sites/warehouses.csv` | Open Database License (ODbL) 1.0, © OpenStreetMap contributors |
| Natural Earth | state outlines in `analysis/figures/fig1_site_map` | Public domain |

The warehouse list is a database derived from OpenStreetMap, so it is shared under the ODbL rather
than CC BY: https://opendatacommons.org/licenses/odbl/.

Cooling-type sources in `data/sites/cooling.csv` are links to public statements and news reports;
only short factual summaries are included here.
