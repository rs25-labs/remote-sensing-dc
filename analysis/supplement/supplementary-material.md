# Supplementary Material

*Land Change, Not Server Heat: A Satellite Census of Surface Temperature Around 36 U.S. Data Centers* [working title]

## S1. Data and processing details

**Landsat.** Google Earth Engine collections `LANDSAT/LC08/C02/T1_L2` and `LANDSAT/LC09/C02/T1_L2`,
2013-01-01 to 2026-12-31. Surface temperature = ST_B10 × 0.00341802 + 149.0 − 273.15 (°C). Pixels with
QA_PIXEL bit 3 (cloud) or bit 4 (cloud shadow) set were removed. Surface reflectance = SR × 0.0000275 − 0.2.
NDVI = (B5 − B4)/(B5 + B4). Albedo = 0.356·B2 + 0.130·B4 + 0.373·B5 + 0.085·B6 + 0.072·B7 − 0.0018 (Liang
2001, adapted to OLI bands). Emissivity = ST_EMIS × 0.0001. Zone means at 30 m with Earth Engine's
reduceRegions; a zone mean was kept only if the zone had clear pixels.

**MODIS.** `MODIS/061/MOD11A1` (Terra) and `MODIS/061/MYD11A1` (Aqua), LST_Day_1km and LST_Night_1km ×
0.02 − 273.15, averaged by calendar month over a 10 km disk and a 10–20 km ring, January 2004 to August
2026. Seasonal cycle removed by subtracting each calendar month's mean over the whole record. The metric
was left blank when fewer than 75% of the months in the 60-month before window or the 12-month after
window had data. Operation month: the recorded date where known, otherwise the middle of the
construction year plus 2.25 years (the median gap from construction to operation in Epoch AI's records).

**ECOSTRESS.** ECO_L2T_LSTE version 002 (70 m tiles), mid-2018 onward, read from NASA LP DAAC over HTTPS
in a 12 km window around each site. Pixels with a non-zero value in the scene's cloud layer were removed.
Only overpasses at 21:00–05:00 local mean solar time were kept; where one overpass appeared in two
overlapping tiles, the tile with more clear pixels in the core and outer ring was kept.

**Land cover.** NLCD 2019 and 2021 releases in Earth Engine (`USGS/NLCD_RELEASES/2019_REL/NLCD`,
`USGS/NLCD_RELEASES/2021_REL/NLCD`), class fractions in the 0–0.5 km core for each edition; the latest
edition before the construction year was used (the earliest if none preceded it). Cover groups: forest
(41–43), crop (82), pasture (81), grass/shrub (52, 71), barren (31), developed (21–24), wetland (90, 95),
water (11).

**Aridity.** TerraClimate (`IDAHO_EPSCOR/TERRACLIMATE`), mean precipitation ÷ mean potential
evapotranspiration (PET × 0.1), 2013–2022, at the site.

**Settings.** Humid: aridity ≥ 0.5. Dry irrigated: aridity < 0.5 and crop + pasture ≥ 50% of the core
before construction. Dry natural: other dry sites.

**Sites.** Candidates from Epoch AI's "AI data centers" dataset and Meta's data-center location list.
Every site was located by hand on satellite imagery and placed on the main data-hall buildings. Sites
within 1 km of each other were merged into one independent unit for statistics (Google Columbus, Google
New Albany and Meta New Albany; Meta Henrico and QTS Richmond 1).

**Construction year detector.** For each site, the within-image contrast of NDVI and of albedo (core
minus 3.5–5 km ring) was summarized by its median in each year and compared with the median for
2013–2015. The detected year is the first year after 2015 in which either contrast departed from that
reference by at least 0.08 (NDVI) or 0.02 (albedo) and was still departed the following year (or was the
last year on record). Using the contrast cancels regional greening and drought. Where Epoch recorded a construction start,
the Epoch year was used; otherwise the earlier of the detected year and the public announcement year.

**Placebos for the 10 km metric.** For each site, 60 random points 20–60 km away; kept those whose NLCD
2019 cover group matched the site's pre-construction cover and that were at least 10 km from every census
site; up to 10 per site (280 in total).

**Warehouses.** OpenStreetMap buildings tagged warehouse, industrial, commercial or retail, or named
distribution/fulfillment/warehouse/logistics, within 30 km of 16 census data centers, with a footprint of
at least 40,000 m², 3–30 km from their data center and at least 3 km from every census data center;
footprints within 500 m merged; candidates reviewed on imagery and up to two kept per data center.

**Statistics.** Percentile bootstrap, 10,000 resamples of images within each period; year-block
bootstrap resampling whole years (images resampled within a period that has only one year). Welch's
two-sample t-test. Smallest detectable effect = 2.8 × (half-width of the 95% interval ÷ 1.96). Across
sites: Fisher's exact test, Spearman correlation, ordinary least squares with 5,000 resamples of whole
units. Cooling comparison: two-sided permutation test, 10,000 permutations.

**Energy ceiling.** Heat flux Q = P/(πr²) for r = 500 m and 1,000 m; warming at full coupling = Q/λ;
largest share of heat reaching the surface = max(0, ΔT_upper)·λ/Q, with λ = 15, 25 and 30 W m⁻² K⁻¹ and
ΔT_upper the largest upper 95% bound on the data-center term across the four warehouse specifications.

## S2. Software and reproducibility

Landsat and MODIS extraction: Colab notebook `dc_heat_census.ipynb` (Earth Engine). ECOSTRESS: Colab
notebook `dc_night.ipynb`. Analysis: Python package `dcheat` with unit tests (numpy, pandas, scipy,
matplotlib). All statistics, tables and figures in the paper and this supplement are rebuilt from the
result CSVs by `analysis/scripts/run_all.sh`; resampling uses fixed random seeds, so results are exactly
reproducible. Every number quoted in the paper is traced to its source file in `numbers_ledger.csv`.

## S3. Supplementary tables

### Table S1. All census sites: location, periods and core daytime change

Core ΔLST = change in (0–0.5 km mean minus 3.5–5 km mean), month-adjusted, °C. Two 95% intervals: resampling images, and resampling whole years. Year source: epoch_ai = Epoch AI record; pilot_imagery = imagery check in the pilot analysis; landsat_manual = reading of the Landsat record; announcement_year / landsat_detected = the earlier of the Landsat-detected year and the public announcement year, labelled by which one it was.

| Site ID | Site | Operator | Type | Lat | Lon | Setting | Cover before | Aridity | Year used | Year source | Landsat-detected year | Before | After | Images before | Images after | Core ΔLST | CI (images) | CI (years) | p | Smallest detectable | ΔNDVI | ΔAlbedo |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| microsoft-sat40-tx | Microsoft SAT40 | Microsoft | conversion | 29.413 | -98.806 | dry natural | developed | 0.439 | 2018 | epoch_ai | 2016 | 2013–2017 | 2025–2026 | 121 | 94 | 2.754 | [+2.17, +3.38] | [+1.62, +4.03] | 4.4e-16 | 0.868 | -0.248 | 0.075 |
| xai-qts-atlanta-ga | xAI QTS Atlanta | SpaceXAI | conversion | 33.778 | -84.421 | humid | developed | 1.251 | 2024 | epoch_ai |  | 2019–2023 | 2025–2026 | 94 | 47 | 0.243 | [-0.47, +0.95] | [-0.03, +0.49] | 0.51 | 1.017 | -0.026 | 0.005 |
| coreweave-chester-va | CoreWeave Chester VA | CoreWeave | conversion | 37.360 | -77.327 | humid | developed | 1.084 | 2023 | epoch_ai | 2022 | 2018–2022 | 2024–2026 | 82 | 78 | 1.080 | [+0.05, +2.08] | [+0.42, +1.58] | 0.04 | 1.451 | -0.080 | 0.007 |
| xai-colossus1-tn | Colossus 1 | SpaceXAI | conversion | 35.060 | -90.156 | humid | crop | 1.148 | 2024 | epoch_ai | 2026 | 2019–2023 | 2025–2026 | 90 | 48 | 1.533 | [+0.58, +2.43] | [+0.97, +2.27] | 0.0022 | 1.324 | -0.078 | 0.018 |
| qts-richmond1-va | QTS Richmond 1 |  | conversion | 37.487 | -77.241 | humid | developed | 1.104 | 2023 | epoch_ai | 2021 | 2018–2022 | 2024–2026 | 81 | 71 | 2.322 | [+1.71, +2.96] | [+1.69, +3.34] | 2.8e-11 | 0.891 | -0.208 | 0.035 |
| google-mesa-az | Google Mesa | Google | greenfield | 33.353 | -111.678 | dry irrigated | crop | 0.125 | 2023 | epoch_ai | 2021 | 2018–2022 | 2025–2026 | 238 | 134 | 0.410 | [-0.23, +1.05] | [-0.75, +1.44] | 0.21 | 0.914 | -0.251 | 0.028 |
| microsoft-goodyear-az | Microsoft Goodyear | Microsoft | greenfield | 33.492 | -112.439 | dry irrigated | crop | 0.082 | 2021 | epoch_ai | 2016 | 2016–2020 | 2025–2026 | 103 | 71 | 0.997 | [+0.02, +2.06] | [+0.28, +1.83] | 0.062 | 1.460 | -0.128 | 0.027 |
| meta-kuna-id | Meta Kuna | Meta | greenfield | 43.464 | -116.272 | dry irrigated | crop | 0.234 | 2017 | landsat_detected | 2017 | 2013–2016 | 2025–2026 | 111 | 101 | 2.917 | [+2.20, +3.63] | [+1.68, +4.09] | 1e-13 | 1.024 | -0.231 | 0.019 |
| meta-los-lunas-nm | Meta Los Lunas | Meta | greenfield | 34.830 | -106.781 | dry natural | grass/shrub | 0.134 | 2016 | announcement_year | 2019 | 2013–2015 | 2025–2026 | 104 | 117 | -3.531 | [-4.18, -2.93] | [-4.26, -2.58] | 1.5e-22 | 0.894 | -0.103 | 0.036 |
| meta-eagle-mountain-ut | Meta Eagle Mountain (original campus) | Meta | greenfield | 40.266 | -112.015 | dry natural | grass/shrub | 0.251 | 2018 | announcement_year | 2019 | 2013–2017 | 2025–2026 | 73 | 60 | -3.018 | [-3.97, -2.05] | [-3.86, -2.37] | 7.5e-09 | 1.366 | -0.122 | -0.020 |
| google-storey-county-nv | Google Storey County | Google | greenfield | 39.494 | -119.423 | dry natural | grass/shrub | 0.146 | 2019 | landsat_manual | 2026 | 2014–2018 | 2025–2026 | 172 | 118 | -2.108 | [-2.57, -1.65] | [-2.82, -1.50] | 3.1e-17 | 0.656 | -0.088 | 0.008 |
| meta-edgecore-mesa-az | Mesa cluster (Meta + Edgecore) | Meta; Edgecore | greenfield | 33.347 | -111.632 | dry natural | grass/shrub | 0.128 | 2022 | pilot_imagery | 2023 | 2017–2021 | 2025–2026 | 199 | 135 | -1.861 | [-2.58, -1.17] | [-2.41, -1.22] | 4.8e-07 | 1.009 | -0.066 | 0.033 |
| openai-stargate-abilene-tx | OpenAI Stargate Abilene | Oracle | greenfield | 32.505 | -99.780 | dry natural | grass/shrub | 0.316 | 2024 | epoch_ai | 2020 | 2019–2023 | 2025–2026 | 213 | 116 | -0.530 | [-1.15, +0.09] | [-1.87, +0.57] | 0.099 | 0.884 | -0.249 | 0.109 |
| microsoft-sat14-tx | Microsoft SAT14 | Microsoft | greenfield | 29.476 | -98.682 | dry natural | developed | 0.462 | 2022 | epoch_ai | 2022 | 2017–2021 | 2025–2026 | 134 | 96 | 0.081 | [-0.44, +0.63] | [-0.49, +0.83] | 0.77 | 0.767 | -0.087 | 0.025 |
| meta-temple-tx | Meta Temple | Meta | greenfield | 31.131 | -97.369 | humid | grass/shrub | 0.572 | 2022 | epoch_ai | 2022 | 2017–2021 | 2025–2026 | 72 | 53 | -1.645 | [-2.23, -1.05] | [-2.34, -0.95] | 2.3e-07 | 0.837 | -0.244 | 0.127 |
| meta-dekalb-il | Meta DeKalb | Meta | greenfield | 41.889 | -88.731 | humid | crop | 1.175 | 2020 | announcement_year | 2020 | 2015–2019 | 2025–2026 | 106 | 88 | -0.056 | [-0.91, +0.71] | [-0.76, +0.82] | 0.89 | 1.158 | -0.136 | 0.013 |
| meta-kansas-city-mo | Meta Kansas City | Meta | greenfield | 39.323 | -94.598 | humid | crop | 0.970 | 2017 | landsat_detected | 2017 | 2013–2016 | 2025–2026 | 87 | 88 | 0.155 | [-0.66, +0.99] | [-0.32, +0.79] | 0.72 | 1.179 | -0.104 | 0.041 |
| google-omaha-ne | Google Omaha | Google | greenfield | 41.339 | -96.085 | humid | crop | 0.845 | 2021 | epoch_ai | 2022 | 2016–2020 | 2025–2026 | 65 | 43 | 0.447 | [-0.27, +1.14] | [+0.03, +0.92] | 0.22 | 1.004 | -0.105 | -0.008 |
| meta-sarpy-ne | Meta Sarpy | Meta | greenfield | 41.123 | -96.144 | humid | developed | 0.850 | 2017 | announcement_year | 2020 | 2013–2016 | 2025–2026 | 48 | 45 | 0.644 | [-0.52, +1.76] | [+0.17, +1.25] | 0.28 | 1.634 | -0.031 | -0.029 |
| meta-gallatin-tn | Meta Gallatin | Meta | greenfield | 36.412 | -86.370 | humid | barren | 1.357 | 2022 | pilot_imagery | 2021 | 2017–2021 | 2025–2026 | 108 | 77 | 0.871 | [+0.31, +1.43] | [+0.24, +1.43] | 0.0029 | 0.800 | -0.117 | 0.022 |
| google-red-oak-tx | Google Red Oak | Google | greenfield | 32.538 | -96.793 | humid | crop | 0.640 | 2023 | epoch_ai | 2022 | 2018–2022 | 2025–2026 | 99 | 49 | 0.884 | [+0.18, +1.61] | [-0.06, +1.47] | 0.017 | 1.024 | -0.203 | 0.068 |
| microsoft-osmium-ia | Microsoft Project Osmium | Microsoft | greenfield | 41.498 | -93.787 | humid | crop | 0.988 | 2018 | epoch_ai | 2016 | 2013–2017 | 2025–2026 | 107 | 90 | 1.256 | [+0.53, +1.99] | [+0.91, +1.60] | 0.0011 | 1.046 | -0.119 | 0.042 |
| google-lancaster-oh | Google Lancaster | Google | greenfield | 39.724 | -82.687 | humid | crop | 1.222 | 2021 | epoch_ai | 2022 | 2016–2020 | 2025–2026 | 56 | 33 | 1.270 | [+0.47, +2.10] | [+0.46, +2.17] | 0.0036 | 1.165 | -0.160 | 0.048 |
| google-bristow-va | Google Bristow | Google | greenfield | 38.776 | -77.583 | humid | grass/shrub | 1.076 | 2021 | epoch_ai | 2016 | 2016–2020 | 2025–2026 | 117 | 83 | 1.630 | [+0.95, +2.28] | [+1.21, +1.96] | 3.3e-06 | 0.954 | -0.255 | 0.063 |
| meta-qts-hillsboro-or | Meta-QTS Hillsboro 2 | Meta | greenfield | 45.559 | -122.930 | humid | crop | 1.160 | 2021 | epoch_ai | 2020 | 2016–2020 | 2025–2026 | 107 | 77 | 1.837 | [+1.22, +2.44] | [+1.32, +2.32] | 1.9e-08 | 0.869 | -0.159 | 0.007 |
| google-midlothian-tx | Google Midlothian | Google | greenfield | 32.443 | -97.062 | humid | grass/shrub | 0.602 | 2019 | pilot_imagery | 2019 | 2014–2018 | 2025–2026 | 61 | 49 | 1.914 | [+1.12, +2.86] | [+1.14, +2.67] | 5.3e-05 | 1.243 | -0.192 | 0.057 |
| google-columbus-oh | Google Columbus | Google | greenfield | 40.064 | -82.758 | humid | crop | 1.259 | 2021 | epoch_ai | 2019 | 2016–2020 | 2025–2026 | 45 | 31 | 2.121 | [+0.87, +3.25] | [+1.35, +2.73] | 0.0013 | 1.700 | -0.166 | 0.066 |
| stack-nva02-va | STACK Infrastructure NVA02 |  | greenfield | 38.747 | -77.537 | humid | pasture | 1.054 | 2019 | epoch_ai | 2020 | 2014–2018 | 2025–2026 | 123 | 80 | 2.264 | [+1.75, +2.78] | [+1.60, +3.08] | 1.1e-14 | 0.734 | -0.223 | 0.030 |
| google-new-albany-oh | Google New Albany | Google | greenfield | 40.060 | -82.764 | humid | crop | 1.259 | 2019 | landsat_detected | 2019 | 2014–2018 | 2025–2026 | 57 | 31 | 2.427 | [+1.18, +3.55] | [+1.42, +3.31] | 0.00027 | 1.691 | -0.164 | 0.065 |
| amazon-new-carlisle-in | Anthropic-Amazon New Carlisle | Amazon | greenfield | 41.691 | -86.462 | humid | crop | 1.306 | 2024 | epoch_ai | 2024 | 2019–2023 | 2025–2026 | 81 | 33 | 2.482 | [+1.36, +3.62] | [+1.92, +3.24] | 8.9e-05 | 1.618 | -0.227 | 0.027 |
| microsoft-fairwater-atlanta-ga | Microsoft Fairwater Atlanta | Microsoft | greenfield | 33.449 | -84.522 | humid | pasture | 1.248 | 2023 | epoch_ai | 2022 | 2018–2022 | 2025–2026 | 75 | 48 | 2.749 | [+1.97, +3.53] | [+1.87, +4.06] | 8.4e-10 | 1.113 | -0.331 | 0.038 |
| amazon-madison-ms | Amazon Madison Mega Site | Amazon | greenfield | 32.596 | -90.095 | humid | grass/shrub | 1.258 | 2023 | epoch_ai | 2021 | 2018–2022 | 2025–2026 | 164 | 111 | 2.777 | [+2.11, +3.48] | [+1.08, +4.84] | 2e-14 | 0.975 | -0.449 | 0.096 |
| meta-huntsville-al | Meta Huntsville | Meta | greenfield | 34.841 | -86.629 | humid | crop | 1.360 | 2018 | announcement_year | 2018 | 2013–2017 | 2025–2026 | 104 | 89 | 2.895 | [+2.25, +3.54] | [+2.54, +3.33] | 1.2e-15 | 0.923 | -0.144 | 0.009 |
| meta-new-albany-oh | Meta New Albany | Meta | greenfield | 40.066 | -82.749 | humid | crop | 1.259 | 2017 | announcement_year | 2017 | 2013–2016 | 2025–2026 | 43 | 33 | 3.541 | [+2.52, +4.58] | [+2.90, +4.13] | 3.1e-09 | 1.470 | -0.186 | 0.031 |
| meta-social-circle-ga | Meta Social Circle (Stanton Springs) | Meta | greenfield | 33.600 | -83.697 | humid | forest | 1.138 | 2018 | pilot_imagery | 2018 | 2013–2017 | 2025–2026 | 134 | 103 | 4.783 | [+4.21, +5.30] | [+4.24, +5.27] | 1.9e-41 | 0.779 | -0.258 | 0.064 |
| meta-henrico-va | Meta Henrico | Meta | greenfield | 37.484 | -77.237 | humid | forest | 1.104 | 2017 | announcement_year | 2018 | 2013–2016 | 2025–2026 | 43 | 48 | 4.891 | [+3.46, +6.04] | [+3.45, +6.82] | 2.1e-09 | 1.849 | -0.326 | 0.055 |

### Table S2. Ring profiles and a nearer reference ring

Change in each ring minus the 3.5–5 km ring (°C). The last columns use the 2–3.5 km ring as the reference instead, to test whether change in the outer ring drives the core result.

| Site ID | Site | Type | Setting | 0–0.5 km | 0.5–1 km | 1–2 km | 2–3.5 km | Core vs 2–3.5 km ring | Same sign |
|---|---|---|---|---|---|---|---|---|---|
| microsoft-sat40-tx | Microsoft SAT40 | conversion | dry natural | 2.75 | 2.80 | 1.20 | 0.86 | 1.89 | True |
| xai-qts-atlanta-ga | xAI QTS Atlanta | conversion | humid | 0.24 | 0.19 | 0.26 | -0.33 | 0.58 | True |
| coreweave-chester-va | CoreWeave Chester VA | conversion | humid | 1.08 | 0.92 | 0.80 | 0.35 | 0.73 | True |
| xai-colossus1-tn | Colossus 1 | conversion | humid | 1.53 | 0.58 | 0.09 | -1.27 | 2.80 | True |
| qts-richmond1-va | QTS Richmond 1 | conversion | humid | 2.32 | 1.29 | 0.90 | 0.10 | 2.22 | True |
| google-mesa-az | Google Mesa | greenfield | dry irrigated | 0.41 | 0.51 | 0.12 | -0.10 | 0.51 | True |
| microsoft-goodyear-az | Microsoft Goodyear | greenfield | dry irrigated | 1.00 | 1.12 | -0.38 | 0.46 | 0.54 | True |
| meta-kuna-id | Meta Kuna | greenfield | dry irrigated | 2.92 | 1.91 | 1.11 | 1.00 | 1.92 | True |
| meta-los-lunas-nm | Meta Los Lunas | greenfield | dry natural | -3.53 | -2.79 | -1.15 | -0.71 | -2.82 | True |
| meta-eagle-mountain-ut | Meta Eagle Mountain (original campus) | greenfield | dry natural | -3.02 | -1.01 | 0.73 | 0.29 | -3.30 | True |
| google-storey-county-nv | Google Storey County | greenfield | dry natural | -2.11 | -1.59 | -0.63 | -0.16 | -1.94 | True |
| meta-edgecore-mesa-az | Mesa cluster (Meta + Edgecore) | greenfield | dry natural | -1.86 | -0.88 | -0.79 | -0.43 | -1.43 | True |
| openai-stargate-abilene-tx | OpenAI Stargate Abilene | greenfield | dry natural | -0.53 | -0.20 | 0.15 | 0.08 | -0.61 | True |
| microsoft-sat14-tx | Microsoft SAT14 | greenfield | dry natural | 0.08 | -0.28 | 0.19 | -0.10 | 0.18 | True |
| meta-temple-tx | Meta Temple | greenfield | humid | -1.65 | -1.10 | -0.33 | 0.24 | -1.88 | True |
| meta-dekalb-il | Meta DeKalb | greenfield | humid | -0.06 | 0.66 | 0.20 | -0.16 | 0.10 | False |
| meta-kansas-city-mo | Meta Kansas City | greenfield | humid | 0.16 | 0.05 | 0.02 | -0.64 | 0.79 | True |
| google-omaha-ne | Google Omaha | greenfield | humid | 0.45 | 0.47 | 0.27 | -0.21 | 0.66 | True |
| meta-sarpy-ne | Meta Sarpy | greenfield | humid | 0.64 | 0.21 | 0.19 | 0.13 | 0.52 | True |
| meta-gallatin-tn | Meta Gallatin | greenfield | humid | 0.87 | 0.27 | 0.04 | -0.36 | 1.23 | True |
| google-red-oak-tx | Google Red Oak | greenfield | humid | 0.88 | 0.86 | 0.34 | 0.19 | 0.69 | True |
| microsoft-osmium-ia | Microsoft Project Osmium | greenfield | humid | 1.26 | 0.39 | 0.27 | 0.11 | 1.15 | True |
| google-lancaster-oh | Google Lancaster | greenfield | humid | 1.27 | -0.16 | 0.00 | -0.14 | 1.41 | True |
| google-bristow-va | Google Bristow | greenfield | humid | 1.63 | 0.49 | -0.02 | 0.06 | 1.57 | True |
| meta-qts-hillsboro-or | Meta-QTS Hillsboro 2 | greenfield | humid | 1.84 | 0.51 | -0.10 | 0.27 | 1.56 | True |
| google-midlothian-tx | Google Midlothian | greenfield | humid | 1.91 | 1.28 | 0.15 | -0.03 | 1.94 | True |
| google-columbus-oh | Google Columbus | greenfield | humid | 2.12 | 1.55 | 0.38 | -0.26 | 2.38 | True |
| stack-nva02-va | STACK Infrastructure NVA02 | greenfield | humid | 2.26 | 1.87 | 0.49 | -0.05 | 2.32 | True |
| google-new-albany-oh | Google New Albany | greenfield | humid | 2.43 | 1.42 | 0.90 | 0.15 | 2.28 | True |
| amazon-new-carlisle-in | Anthropic-Amazon New Carlisle | greenfield | humid | 2.48 | 1.02 | 0.20 | 0.31 | 2.18 | True |
| microsoft-fairwater-atlanta-ga | Microsoft Fairwater Atlanta | greenfield | humid | 2.75 | 0.87 | 0.42 | -0.14 | 2.89 | True |
| amazon-madison-ms | Amazon Madison Mega Site | greenfield | humid | 2.78 | 2.09 | 0.99 | 0.27 | 2.51 | True |
| meta-huntsville-al | Meta Huntsville | greenfield | humid | 2.90 | 0.68 | 0.64 | 0.24 | 2.66 | True |
| meta-new-albany-oh | Meta New Albany | greenfield | humid | 3.54 | 2.36 | 0.85 | 0.38 | 3.16 | True |
| meta-social-circle-ga | Meta Social Circle (Stanton Springs) | greenfield | humid | 4.78 | 2.08 | 0.68 | 0.23 | 4.55 | True |
| meta-henrico-va | Meta Henrico | greenfield | humid | 4.89 | 2.31 | 1.68 | 0.11 | 4.78 | True |

### Table S3. Warehouses used as land-change comparisons

Large distribution buildings (roof ≥ 40,000 m²) from OpenStreetMap, 3–30 km from a census data center and ≥ 3 km from all of them, checked on imagery. Construction year detected from Landsat.

| Warehouse ID | Warehouse | Lat | Lon | Paired data center | Distance (km) | Setting | Year (Landsat) | Core ΔLST | CI | ΔNDVI | ΔAlbedo | Not used because |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| wh-amazon-madison-ms-1 | unnamed warehouse building (OpenStreetMap way 941353573) | 32.59 | -90.06 | Amazon Madison Mega Site | 3.20 | humid | 2021 | 2.17 | [+1.41, +2.92] | 0.00 | -0.02 |  |
| wh-amazon-new-carlisle-in-1 | Tire Rack | 41.73 | -86.35 | Anthropic-Amazon New Carlisle | 10.10 |  |  |  |  |  |  | no construction year |
| wh-amazon-new-carlisle-in-2 | unnamed warehouse building (OpenStreetMap way 167600034) | 41.63 | -86.68 | Anthropic-Amazon New Carlisle | 19.20 |  |  |  |  |  |  | no construction year |
| wh-google-midlothian-tx-1 | unnamed warehouse building (OpenStreetMap way 468820234) | 32.64 | -96.85 | Google Midlothian | 29.40 |  |  |  |  |  |  | no construction year |
| wh-google-midlothian-tx-2 | unnamed warehouse building (OpenStreetMap way 472411739) | 32.63 | -96.87 | Google Midlothian | 27.90 | humid | 2016 | 0.33 | [-0.17, +0.85] | 0.00 | 0.04 |  |
| wh-google-omaha-ne-1 | Oriental Trading Company | 41.17 | -96.09 | Google Omaha | 18.40 | humid | 2022 | -1.36 | [-1.98, -0.70] | 0.01 | 0.02 |  |
| wh-google-omaha-ne-2 | unnamed warehouse building (OpenStreetMap way 1042336077) | 41.15 | -96.13 | Google Omaha | 21.40 | humid | 2021 | 0.79 | [-0.01, +1.66] | -0.07 | -0.02 |  |
| wh-google-red-oak-tx-1 | American Standard distribution center (Hutchins) | 32.64 | -96.70 | Google Red Oak | 14.20 | humid | 2024 | 0.80 | [+0.40, +1.21] | -0.03 | 0.01 |  |
| wh-google-storey-county-nv-1 | Wal-Mart Distribution Center | 39.54 | -119.48 | Google Storey County | 6.70 | dry natural | 2024 | -1.05 | [-1.55, -0.62] | -0.01 | 0.02 |  |
| wh-google-storey-county-nv-2 | unnamed warehouse building (OpenStreetMap way 1176319744) | 39.51 | -119.74 | Google Storey County | 27.70 | dry irrigated | 2020 | 2.49 | [+1.65, +3.29] | -0.16 | 0.03 |  |
| wh-meta-gallatin-tn-1 | Gap Distribution Center | 36.37 | -86.50 | Meta Gallatin | 12.30 | humid | 2020 | -1.58 | [-2.64, -0.69] | -0.09 | 0.10 |  |
| wh-meta-gallatin-tn-2 | unnamed warehouse building (OpenStreetMap way 1408148107) | 36.15 | -86.40 | Meta Gallatin | 28.90 | humid | 2023 | 2.61 | [+2.10, +3.12] | -0.21 | 0.05 |  |
| wh-meta-henrico-va-1 | AutoZone Distribution Center | 37.50 | -77.08 | Meta Henrico | 14.10 | humid | 2023 | 2.38 | [+1.70, +3.05] | -0.23 | 0.06 |  |
| wh-meta-kuna-id-1 | WinCo Foods Distribution Center | 43.52 | -116.16 | Meta Kuna | 11.10 |  | 2025 |  |  |  |  | construction began in the after window |
| wh-meta-kuna-id-2 | BOI2 Amazon Fulfillment Center | 43.60 | -116.50 | Meta Kuna | 24.10 | dry irrigated | 2018 | 1.27 | [+0.53, +2.12] | -0.16 | 0.02 |  |
| wh-meta-los-lunas-nm-1 | Amazon Fulfillment Center | 34.83 | -106.82 | Meta Los Lunas | 3.30 | dry natural | 2022 | -1.84 | [-2.49, -1.14] | -0.05 | 0.04 |  |
| wh-meta-los-lunas-nm-2 | Amazon ABQ1 | 35.08 | -106.80 | Meta Los Lunas | 27.90 | dry natural | 2021 | -2.33 | [-2.91, -1.76] | -0.07 | 0.05 |  |
| wh-meta-social-circle-ga-1 | unnamed warehouse building (OpenStreetMap way 1027002005) | 33.64 | -83.68 | Meta Social Circle (Stanton Springs) | 4.50 | humid | 2024 | -0.50 | [-1.07, +0.02] | -0.01 | -0.00 |  |
| wh-meta-social-circle-ga-2 | unnamed warehouse building (OpenStreetMap way 1484771356) | 33.65 | -83.69 | Meta Social Circle (Stanton Springs) | 5.70 | humid | 2024 | 2.46 | [+2.01, +2.94] | -0.20 | 0.06 |  |
| wh-microsoft-goodyear-az-1 | Walmart Distribution Center | 33.39 | -112.56 | Microsoft Goodyear | 16.40 | dry natural | 2017 | 2.76 | [+2.17, +3.40] | -0.15 | 0.08 |  |
| wh-microsoft-goodyear-az-2 | Ross Distribution Center | 33.39 | -112.55 | Microsoft Goodyear | 15.40 | dry irrigated | 2020 | 2.21 | [+1.18, +3.27] | -0.28 | 0.06 |  |
| wh-microsoft-osmium-ia-1 | GXO Logistics | 41.66 | -93.60 | Microsoft Project Osmium | 24.20 | humid | 2016 | 1.01 | [+0.49, +1.49] | -0.02 | 0.01 |  |
| wh-microsoft-osmium-ia-2 | Interstate Distribution Center | 41.63 | -93.76 | Microsoft Project Osmium | 15.20 |  |  |  |  |  |  | no construction year |

### Table S4. Cooling type and sources

Dry = all heat rejected as warm air (air-cooled chillers, dry coolers, closed-loop to dry coolers). Cooling towers and evaporative assist (outside air with evaporative cooling on hot days) were grouped as evaporative. Basis: site = a statement about this facility; operator = a company-wide statement.

| Site ID | Site | Type | Cooling | Detail | Basis | Source |
|---|---|---|---|---|---|---|
| amazon-new-carlisle-in | Anthropic-Amazon New Carlisle | greenfield | evaporative assist | outside air for ~98% of the year; evaporative cooling only on the hottest days | site | https://measuredai.substack.com/p/aws-new-carlisle-data-center-campus |
| amazon-madison-ms | Amazon Madison Mega Site | greenfield | evaporative assist | outside air ~91% of the year; water-based cooling in the hottest periods | site | https://afrotech.com/amazon-announces-25b-commitment-toward-mississippi-data-center-operations-and-addresses-water-usage |
| google-bristow-va | Google Bristow | greenfield | unknown | no public statement found |  |  |
| google-columbus-oh | Google Columbus | greenfield | cooling towers | Google Lockbourne OH: 23 million gallons consumed in 2023 (Google 2024 Environmental Report) | site | https://www.visualcapitalist.com/mapped-googles-data-centers-water-use/ |
| google-lancaster-oh | Google Lancaster | greenfield | unknown | only 8 million gallons consumed in 2023; cooling type not stated |  | https://www.visualcapitalist.com/mapped-googles-data-centers-water-use/ |
| google-mesa-az | Google Mesa | greenfield | dry | air-cooled; water only for offices | site | https://www.12news.com/article/news/local/valley/google-is-building-a-600-million-data-center-in-mesa-that-wont-use-water-to-cool-storage-units/75-423d5f59-5c3e-4160-b587-0a328eec9a83 |
| google-omaha-ne | Google Omaha | greenfield | cooling towers | Google Nebraska sites consumed ~417 million gallons in 2024; Epoch lists water use | site | https://flatwaterfreepress.org/data-centers-can-guzzle-serious-water-as-some-nebraskans-worry-tech-giants-seek-solutions/ |
| google-red-oak-tx | Google Red Oak | greenfield | dry | closed-loop system | site | https://www.fox7austin.com/news/texas-data-centers-google-water-fund-stewardship-plan |
| google-new-albany-oh | Google New Albany | greenfield | cooling towers | 127 million gallons consumed in 2023 (Google 2024 Environmental Report) | site | https://www.visualcapitalist.com/mapped-googles-data-centers-water-use/ |
| google-storey-county-nv | Google Storey County | greenfield | dry | air-cooled; 0.2 million gallons consumed in 2023 | site | https://www.technologyreview.com/2025/05/20/1116287/ai-data-centers-nevada-water-reno-computing-environmental-impact/ |
| meta-temple-tx | Meta Temple | greenfield | dry | closed-loop liquid cooling with dry coolers; outside air at least half the year | site | https://kdhnews.com/news/region/first-ai-optimized-meta-data-center-in-nation-opens-in-temple-tx/article_fd6cd4ad-d6a5-52cf-bf85-86199550c88d.html |
| meta-qts-hillsboro-or | Meta-QTS Hillsboro 2 | greenfield | dry | QTS Hillsboro: water-free cooling design | site | https://hillsboronewstimes.com/2020/06/22/new-qts-data-center-in-hillsboro-powered-by-renewables/ |
| microsoft-fairwater-atlanta-ga | Microsoft Fairwater Atlanta | greenfield | dry | closed-loop liquid cooling; water filled once | site | https://news.microsoft.com/source/features/ai/from-wisconsin-to-atlanta-microsoft-connects-datacenters-to-build-its-first-ai-superfactory/ |
| microsoft-goodyear-az | Microsoft Goodyear | greenfield | evaporative assist | adiabatic: outside air below 85 °F; evaporative above | site | https://azure.microsoft.com/en-us/blog/expanding-cloud-services-microsoft-launches-its-sustainable-datacenter-region-in-arizona/ |
| microsoft-osmium-ia | Microsoft Project Osmium | greenfield | evaporative assist | West Des Moines: direct evaporative cooling ~10% of the year; otherwise outside air | site | https://www.wpr.org/news/microsoft-data-center-iowa-wisconsin-expect |
| microsoft-sat14-tx | Microsoft SAT14 | greenfield | unknown | no public statement found for this building |  |  |
| openai-stargate-abilene-tx | OpenAI Stargate Abilene | greenfield | dry | closed-loop liquid cooling with non-evaporative dry coolers | site | https://www.tpr.org/environment/2025-08-15/big-techs-big-thirst-ais-demand-for-texas-water |
| stack-nva02-va | STACK Infrastructure NVA02 | greenfield | dry | air-cooled chillers | site | https://www.stackinfra.com/wp-content/uploads/2023/12/NVA02_Campus_120523.pdf |
| xai-colossus1-tn | Colossus 1 | conversion | cooling towers | makeup water for Colossus 1 cooling towers | site | https://measuredai.substack.com/p/xai-colossus-data-center-cluster |
| coreweave-chester-va | CoreWeave Chester VA | conversion | unknown | liquid plus existing air cooling; heat rejection not stated |  | https://www.coreweave.com/blog/coreweave-opens-new-data-center-in-virginia |
| xai-qts-atlanta-ga | xAI QTS Atlanta | conversion | dry | QTS Freedom design (operator-wide) | operator | https://q.com/resources/pioneering-water-efficiency-and-sustainability-in-data-center-operations/ |
| qts-richmond1-va | QTS Richmond 1 | conversion | dry | QTS Freedom design (operator-wide) | operator | https://q.com/resources/pioneering-water-efficiency-and-sustainability-in-data-center-operations/ |
| microsoft-sat40-tx | Microsoft SAT40 | conversion | cooling towers | Microsoft San Antonio campus uses recycled water in cooling towers (Westover Hills) | operator | https://ceowatermandate.org/wp-content/uploads/2018/01/Water_Risk_Monetizer_Microsoft_Case_Study.pdf |
| meta-los-lunas-nm | Meta Los Lunas | greenfield | evaporative assist | Meta standard design: outside air plus direct evaporative misting (operator-wide) | operator | https://datacenters.atmeta.com/water/ |
| meta-sarpy-ne | Meta Sarpy | greenfield | evaporative assist | Meta standard design (operator-wide) | operator | https://datacenters.atmeta.com/water/ |
| meta-new-albany-oh | Meta New Albany | greenfield | evaporative assist | Meta standard design (operator-wide) | operator | https://datacenters.atmeta.com/water/ |
| meta-henrico-va | Meta Henrico | greenfield | evaporative assist | Meta standard design (operator-wide) | operator | https://datacenters.atmeta.com/water/ |
| meta-huntsville-al | Meta Huntsville | greenfield | evaporative assist | Meta standard design (operator-wide) | operator | https://datacenters.atmeta.com/water/ |
| meta-eagle-mountain-ut | Meta Eagle Mountain (original campus) | greenfield | evaporative assist | Meta standard design (operator-wide) | operator | https://datacenters.atmeta.com/water/ |
| meta-dekalb-il | Meta DeKalb | greenfield | evaporative assist | Meta standard design (operator-wide) | operator | https://datacenters.atmeta.com/water/ |
| meta-kansas-city-mo | Meta Kansas City | greenfield | evaporative assist | Meta standard design (operator-wide) | operator | https://datacenters.atmeta.com/water/ |
| meta-kuna-id | Meta Kuna | greenfield | dry | closed-loop with dry coolers; small evaporative structures on campus | site | https://datacenters.atmeta.com/innovation/ |
| meta-edgecore-mesa-az | Mesa cluster (Meta + Edgecore) | greenfield | evaporative assist | Meta Mesa uses outside air most of the year; Edged building in the rings is waterless | site | https://siteselection.com/meta-finds-an-oasis-in-the-sonoran-desert/ |
| google-midlothian-tx | Google Midlothian | greenfield | cooling towers | evaporative cooling towers; 136 million gallons consumed in 2023 | site | https://www.visualcapitalist.com/mapped-googles-data-centers-water-use/ |
| meta-gallatin-tn | Meta Gallatin | greenfield | evaporative assist | Meta standard design (operator-wide) | operator | https://datacenters.atmeta.com/water/ |
| meta-social-circle-ga | Meta Social Circle (Stanton Springs) | greenfield | evaporative assist | hybrid evaporative plus outside air, ~500,000 gal/day reported (secondary sources only) | operator | https://datacenters.atmeta.com/water/ |

### Table S5. Energy-balance ceiling by site

Power = mean Epoch AI facility power, Jan 2025–Sep 2026. Warming assumes a coupling coefficient of 25 W m⁻² K⁻¹. Greenfield sites with Epoch power data only.

| Site ID | Site | Power (MW) | Heat flux over core (W/m²) | Heat flux over 1 km disk (W/m²) | Warming if all reached surface, core (°C) | Same, 1 km disk (°C) |
|---|---|---|---|---|---|---|
| amazon-new-carlisle-in | Anthropic-Amazon New Carlisle | 640.0 | 814.9 | 203.7 | 32.6 | 8.1 |
| microsoft-fairwater-atlanta-ga | Microsoft Fairwater Atlanta | 539.5 | 686.9 | 171.7 | 27.5 | 6.9 |
| google-new-albany-oh | Google New Albany | 373.4 | 475.4 | 118.9 | 19.0 | 4.8 |
| openai-stargate-abilene-tx | OpenAI Stargate Abilene | 316.0 | 402.3 | 100.6 | 16.1 | 4.0 |
| google-columbus-oh | Google Columbus | 280.8 | 357.5 | 89.4 | 14.3 | 3.6 |
| amazon-madison-ms | Amazon Madison Mega Site | 255.8 | 325.6 | 81.4 | 13.0 | 3.3 |
| google-bristow-va | Google Bristow | 247.0 | 314.5 | 78.6 | 12.6 | 3.1 |
| meta-qts-hillsboro-or | Meta-QTS Hillsboro 2 | 243.0 | 309.4 | 77.3 | 12.4 | 3.1 |
| microsoft-osmium-ia | Microsoft Project Osmium | 228.0 | 290.3 | 72.6 | 11.6 | 2.9 |
| microsoft-goodyear-az | Microsoft Goodyear | 223.5 | 284.6 | 71.1 | 11.4 | 2.8 |
| google-omaha-ne | Google Omaha | 208.0 | 264.8 | 66.2 | 10.6 | 2.6 |
| google-storey-county-nv | Google Storey County | 187.2 | 238.4 | 59.6 | 9.5 | 2.4 |
| meta-temple-tx | Meta Temple | 156.8 | 199.6 | 49.9 | 8.0 | 2.0 |
| google-mesa-az | Google Mesa | 153.8 | 195.8 | 48.9 | 7.8 | 2.0 |
| google-lancaster-oh | Google Lancaster | 136.7 | 174.0 | 43.5 | 7.0 | 1.7 |
| stack-nva02-va | STACK Infrastructure NVA02 | 118.0 | 150.2 | 37.6 | 6.0 | 1.5 |
| meta-los-lunas-nm | Meta Los Lunas | 105.0 | 133.7 | 33.4 | 5.3 | 1.3 |
| google-midlothian-tx | Google Midlothian | 102.5 | 130.5 | 32.6 | 5.2 | 1.3 |
| meta-kuna-id | Meta Kuna | 99.0 | 126.1 | 31.5 | 5.0 | 1.3 |
| google-red-oak-tx | Google Red Oak | 93.0 | 118.4 | 29.6 | 4.7 | 1.2 |
| meta-huntsville-al | Meta Huntsville | 60.6 | 77.2 | 19.3 | 3.1 | 0.8 |
| meta-gallatin-tn | Meta Gallatin | 57.0 | 72.6 | 18.1 | 2.9 | 0.7 |
| meta-sarpy-ne | Meta Sarpy | 52.5 | 66.8 | 16.7 | 2.7 | 0.7 |
| microsoft-sat14-tx | Microsoft SAT14 | 39.3 | 50.1 | 12.5 | 2.0 | 0.5 |

### Table S6. The 10 km metric by site, Terra and Aqua

metric = Marinoni et al. metric at the site (0–10 km disk, 12 months after vs 60 before, °C); placebos = mean of the same metric at up to 10 placebo points; referenced = site disk minus its 10–20 km ring. Month source: recorded (Epoch/operator) or estimated (middle of construction year + 2.25 years).

| Site ID | Site | Operation month | Month source | Terra day metric | Terra day placebos | Terra day referenced | Terra night metric | Terra night placebos | Terra night referenced | Aqua day metric | Aqua day placebos | Aqua day referenced | Aqua night metric | Aqua night placebos | Aqua night referenced |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| amazon-new-carlisle-in | Anthropic-Amazon New Carlisle | 2025-06-01 | recorded | -3.17 | -3.15 | -0.33 | 1.63 | 1.03 | 0.19 | -1.60 | -1.89 | -0.35 | -0.44 | -0.06 | -0.28 |
| amazon-madison-ms | Amazon Madison Mega Site | 2025-06-01 | recorded | -1.94 | -1.67 | -0.07 | 1.02 | 1.17 | 0.06 | -0.36 | -0.07 | -0.17 | 0.60 | 0.28 | 0.14 |
| google-bristow-va | Google Bristow | 2024-04-01 | recorded | -0.99 |  | -0.08 | 0.11 |  | -0.02 | 0.26 |  | 0.17 | -0.38 |  | 0.07 |
| google-columbus-oh | Google Columbus | 2024-04-01 | recorded | -0.66 | -0.63 | 0.08 | 0.66 | 0.53 | 0.15 | 1.03 | 0.74 | 0.22 | -0.38 | -0.39 | -0.12 |
| google-lancaster-oh | Google Lancaster | 2024-01-01 | recorded | 0.27 | 0.34 | -0.10 | 1.23 | 0.73 | 0.06 | 1.50 | 1.54 | 0.14 | 0.90 | 0.66 | 0.06 |
| google-mesa-az | Google Mesa | 2025-07-01 | recorded | -3.37 | -2.95 | -0.05 | 2.80 | 2.46 | 0.18 | -0.72 | -0.62 | 0.02 | 0.85 | 0.84 | 0.05 |
| google-omaha-ne | Google Omaha | 2024-04-01 | recorded | -0.69 | -0.70 | -0.10 | 1.07 | 0.76 | 0.08 | 0.14 | 0.35 | -0.32 | 0.24 | 0.11 | 0.05 |
| google-red-oak-tx | Google Red Oak | 2025-08-01 | recorded | -1.92 | -1.89 | -0.04 | 2.01 | 1.60 | 0.01 | -0.53 | -0.50 | -0.05 | 0.99 | 0.83 | 0.01 |
| google-new-albany-oh | Google New Albany | 2024-04-01 | recorded | -0.66 | -0.59 | 0.08 | 0.70 | 0.52 | 0.18 | 1.08 | 0.92 | 0.25 | -0.35 | -0.35 | -0.10 |
| google-storey-county-nv | Google Storey County | 2023-08-01 | recorded | -1.63 | -1.75 | 0.06 | 1.27 | 1.55 | -0.08 | 0.17 | -0.30 | 0.09 | 0.77 | 0.99 | -0.01 |
| meta-temple-tx | Meta Temple | 2025-12-01 | recorded | -2.68 | -2.88 | -0.27 | 2.28 | 2.09 | 0.13 | -0.83 | -0.93 | -0.34 | 0.88 | 0.75 | -0.12 |
| meta-qts-hillsboro-or | Meta-QTS Hillsboro 2 | 2023-08-01 | recorded | -0.71 | -0.61 | -0.08 | 1.02 | 1.05 | 0.01 | 0.52 | 0.36 | -0.18 | -0.11 | 0.16 | -0.26 |
| microsoft-fairwater-atlanta-ga | Microsoft Fairwater Atlanta | 2025-10-01 | recorded | -2.12 | -2.16 | 0.04 | 1.26 | 1.08 | 0.23 | -0.42 | -0.46 | 0.11 | 0.40 | 0.24 | 0.08 |
| microsoft-goodyear-az | Microsoft Goodyear | 2023-04-01 | recorded | -0.59 | -0.89 | 0.06 | 1.01 | 0.82 | 0.12 | 0.98 | 0.42 | 0.25 | 0.31 | 0.06 | 0.11 |
| microsoft-osmium-ia | Microsoft Project Osmium | 2021-01-01 | recorded | 0.94 | 1.06 | 0.24 | -0.32 | -0.50 | 0.08 | 0.71 | 0.87 | 0.17 | -0.57 | -0.53 | 0.00 |
| microsoft-sat14-tx | Microsoft SAT14 | 2024-07-01 | recorded | -2.17 | -1.96 | -0.23 | 1.44 | 1.47 | 0.08 | 0.25 | 0.40 | -0.21 | 0.49 | 0.41 | 0.11 |
| openai-stargate-abilene-tx | OpenAI Stargate Abilene | 2025-09-01 | recorded | -2.10 | -2.31 | 0.06 | 2.86 | 2.43 | 0.17 | 0.17 | -0.42 | 0.26 | 1.13 | 1.01 | 0.04 |
| stack-nva02-va | STACK Infrastructure NVA02 | 2024-10-01 | recorded | -1.93 | -1.91 | -0.30 | -0.27 | -0.09 | -0.01 | -0.78 | -0.96 | -0.15 | -0.56 | -0.62 | 0.04 |
| xai-colossus1-tn | Colossus 1 | 2024-08-01 | recorded | -1.53 | -1.71 | 0.09 | 0.63 | 0.67 | 0.08 | -0.32 | -0.33 | 0.09 | -0.11 | 0.32 | -0.21 |
| coreweave-chester-va | CoreWeave Chester VA | 2024-01-01 | recorded | -1.08 | -0.99 | 0.06 | 0.42 | 0.31 | 0.25 | -0.14 | 0.13 | -0.01 | -0.17 | -0.18 | 0.10 |
| xai-qts-atlanta-ga | xAI QTS Atlanta | 2025-02-01 | recorded | -2.32 | -1.84 | -0.19 | 1.09 | 0.93 | 0.05 | -0.25 | -0.28 | 0.02 | -0.12 | -0.11 | -0.03 |
| qts-richmond1-va | QTS Richmond 1 | 2024-01-01 | recorded | -1.14 | -1.04 | -0.09 | 0.16 | 0.25 | -0.06 | -0.26 | 0.05 | -0.19 | -0.26 | -0.24 | -0.10 |
| microsoft-sat40-tx | Microsoft SAT40 | 2024-05-01 | recorded | -1.21 | -1.28 | -0.24 | 1.75 | 1.68 | -0.03 | 1.44 | 0.95 | -0.10 | 0.59 | 0.57 | 0.02 |
| meta-dekalb-il | Meta DeKalb | 2022-10-01 | estimated | 1.47 | 1.57 | -0.18 | 1.13 | 1.09 | -0.15 | 2.61 | 2.45 | 0.02 | 0.33 | 0.39 | -0.09 |
| meta-eagle-mountain-ut | Meta Eagle Mountain (original campus) | 2020-10-01 | estimated | 3.38 | 2.73 | 0.97 | -0.22 | 0.37 | -0.34 | 3.77 | 3.06 | 1.20 | -0.40 | 0.28 | -0.39 |
| meta-henrico-va | Meta Henrico | 2019-10-01 | estimated | -0.09 | -0.18 | 0.08 | -0.22 | -0.18 | 0.06 | -0.12 | -0.20 | -0.00 | -0.47 | -0.40 | -0.18 |
| meta-huntsville-al | Meta Huntsville | 2020-10-01 | estimated | -0.53 | -0.66 | -0.01 | -0.86 | -0.98 | 0.08 | -0.44 | -0.68 | 0.10 | -0.69 | -0.60 | 0.04 |
| meta-kansas-city-mo | Meta Kansas City | 2019-10-01 | estimated | -0.44 | -0.77 | 0.08 | -0.72 | -0.56 | -0.10 | -0.84 | -0.95 | -0.03 | -0.61 | -0.34 | -0.03 |
| meta-kuna-id | Meta Kuna | 2019-10-01 | estimated | 0.18 | 0.35 | -0.39 | -0.40 | -0.17 | -0.09 | -0.14 | 0.58 | -0.47 | -0.65 | -0.61 | -0.11 |
| meta-los-lunas-nm | Meta Los Lunas | 2018-10-01 | estimated | -0.97 | -0.58 | -0.20 | -0.37 | -0.63 | 0.03 | -1.16 | -1.09 | -0.08 | -0.31 | -0.45 | -0.04 |
| meta-new-albany-oh | Meta New Albany | 2019-10-01 | estimated | 0.82 | 0.54 | 0.14 | -0.04 | -0.16 | 0.04 | 0.82 | 0.52 | 0.26 | -0.34 | -0.63 | 0.19 |
| meta-sarpy-ne | Meta Sarpy | 2019-10-01 | estimated | 0.50 | 0.10 | 0.16 | -0.27 | -0.41 | 0.00 | 0.99 | 0.65 | 0.42 | -0.24 | -0.33 | 0.02 |
| meta-gallatin-tn | Meta Gallatin | 2024-11-01 | recorded | -1.56 |  | -0.12 | 0.90 |  | -0.05 | -0.57 |  | -0.15 | 0.07 |  | -0.08 |
| meta-edgecore-mesa-az | Mesa cluster (Meta + Edgecore) | 2024-07-01 | recorded | -1.81 | -0.83 | -0.40 | 1.55 | 1.42 | 0.13 | 0.73 | 1.57 | -0.41 | 0.24 | 0.19 | 0.15 |
| google-midlothian-tx | Google Midlothian | 2020-07-01 | recorded | -0.62 | -0.18 | -0.09 | -0.76 | -0.79 | -0.04 | -0.57 | -0.22 | -0.13 | -1.13 | -1.04 | 0.00 |
| meta-social-circle-ga | Meta Social Circle (Stanton Springs) | 2021-07-01 | recorded | -0.45 | -0.51 | 0.04 | 0.19 | 0.17 | -0.05 | 0.20 | 0.09 | -0.02 | 0.28 | 0.15 | 0.03 |

### Table S7. Night change, all designs, periods and seasons

ECOSTRESS 21:00–05:00 local solar time, one tile per overpass, core and outer ring ≥ 50% clear, adjusted for calendar month and night-hour bin. Periods: pilot = before 2019–2021 (Midlothian 2018) and after as in the pilot analysis; census = up to 5 years before construction and 2025–2026. Midlothian has fewer than two usable images before construction and is omitted.

| Site | Periods | Season | Design | Change (°C) | CI | CI (years) | p | Images before | Images after |
|---|---|---|---|---|---|---|---|---|---|
| meta-edgecore-mesa-az | pilot | all | ring 0–0.5 km | 0.95 | [+0.67, +1.26] | [+0.60, +1.32] | 3.5e-07 | 47 | 13 |
| meta-edgecore-mesa-az | pilot | all | ring 0.5–1 km | 0.60 | [+0.29, +0.97] | [+0.28, +0.97] | 0.0045 | 48 | 12 |
| meta-edgecore-mesa-az | pilot | all | ring 1–2 km | 0.41 | [+0.22, +0.62] | [+0.18, +0.65] | 0.00073 | 50 | 15 |
| meta-edgecore-mesa-az | pilot | all | ring 2–3.5 km | 0.15 | [+0.06, +0.24] | [+0.04, +0.25] | 0.0016 | 55 | 17 |
| meta-edgecore-mesa-az | pilot | summer (Jun-Sep) | ring 0–0.5 km | 0.63 | [+0.30, +1.01] | [+0.19, +1.18] | 0.0023 | 28 | 5 |
| meta-edgecore-mesa-az | pilot | summer (Jun-Sep) | ring 0.5–1 km | 0.29 | [-0.03, +0.65] | [-0.09, +0.72] | 0.17 | 28 | 5 |
| meta-edgecore-mesa-az | pilot | summer (Jun-Sep) | ring 1–2 km | 0.23 | [+0.05, +0.42] | [-0.03, +0.52] | 0.028 | 28 | 6 |
| meta-edgecore-mesa-az | pilot | summer (Jun-Sep) | ring 2–3.5 km | 0.13 | [+0.00, +0.26] | [-0.03, +0.30] | 0.074 | 30 | 7 |
| meta-edgecore-mesa-az | pilot | cool (Oct-Mar) | ring 0–0.5 km | 1.22 | [+0.85, +1.61] | [+0.93, +1.50] | 3.8e-05 | 12 | 7 |
| meta-edgecore-mesa-az | pilot | cool (Oct-Mar) | ring 0.5–1 km | 0.75 | [+0.32, +1.25] | [+0.38, +1.25] | 0.017 | 13 | 7 |
| meta-edgecore-mesa-az | pilot | cool (Oct-Mar) | ring 1–2 km | 0.45 | [+0.17, +0.78] | [+0.19, +0.75] | 0.021 | 15 | 8 |
| meta-edgecore-mesa-az | pilot | cool (Oct-Mar) | ring 2–3.5 km | 0.14 | [+0.02, +0.25] | [+0.04, +0.22] | 0.034 | 18 | 9 |
| edgecore-mesa-az | pilot | all | ring 0–0.5 km | 0.75 | [+0.44, +1.11] | [+0.42, +1.04] | 4.4e-05 | 47 | 26 |
| edgecore-mesa-az | pilot | all | ring 0.5–1 km | 0.36 | [-0.09, +0.75] | [+0.05, +0.63] | 0.12 | 48 | 24 |
| edgecore-mesa-az | pilot | all | ring 1–2 km | 0.30 | [+0.12, +0.49] | [+0.19, +0.41] | 0.0029 | 51 | 26 |
| edgecore-mesa-az | pilot | all | ring 2–3.5 km | 0.09 | [-0.01, +0.19] | [+0.03, +0.15] | 0.087 | 55 | 29 |
| edgecore-mesa-az | pilot | summer (Jun-Sep) | ring 0–0.5 km | 0.60 | [+0.15, +1.15] | [+0.19, +1.24] | 0.028 | 28 | 11 |
| edgecore-mesa-az | pilot | summer (Jun-Sep) | ring 0.5–1 km | 0.27 | [-0.65, +1.05] | [+0.02, +0.67] | 0.57 | 28 | 11 |
| edgecore-mesa-az | pilot | summer (Jun-Sep) | ring 1–2 km | 0.30 | [+0.03, +0.59] | [-0.05, +0.67] | 0.05 | 28 | 12 |
| edgecore-mesa-az | pilot | summer (Jun-Sep) | ring 2–3.5 km | 0.11 | [-0.06, +0.29] | [-0.01, +0.25] | 0.24 | 30 | 13 |
| edgecore-mesa-az | pilot | cool (Oct-Mar) | ring 0–0.5 km | 0.93 | [+0.55, +1.35] | [+0.61, +1.26] | 0.00019 | 13 | 14 |
| edgecore-mesa-az | pilot | cool (Oct-Mar) | ring 0.5–1 km | 0.42 | [+0.13, +0.73] | [+0.01, +0.78] | 0.015 | 13 | 12 |
| edgecore-mesa-az | pilot | cool (Oct-Mar) | ring 1–2 km | 0.26 | [+0.01, +0.53] | [-0.04, +0.49] | 0.079 | 16 | 13 |
| edgecore-mesa-az | pilot | cool (Oct-Mar) | ring 2–3.5 km | 0.07 | [-0.05, +0.18] | [-0.01, +0.12] | 0.27 | 18 | 15 |
| meta-gallatin-tn | pilot | all | ring 0–0.5 km | -0.08 | [-0.67, +0.48] | [-0.60, +0.56] | 0.79 | 44 | 27 |
| meta-gallatin-tn | pilot | all | ring 0.5–1 km | -0.02 | [-0.44, +0.36] | [-0.44, +0.47] | 0.91 | 42 | 27 |
| meta-gallatin-tn | pilot | all | ring 1–2 km | -0.24 | [-0.60, +0.11] | [-0.40, -0.04] | 0.19 | 44 | 28 |
| meta-gallatin-tn | pilot | all | ring 2–3.5 km | -0.11 | [-0.28, +0.04] | [-0.19, -0.03] | 0.18 | 45 | 28 |
| meta-gallatin-tn | pilot | summer (Jun-Sep) | ring 0–0.5 km | 0.43 | [-0.13, +1.03] | [-0.22, +1.45] | 0.18 | 14 | 11 |
| meta-gallatin-tn | pilot | summer (Jun-Sep) | ring 0.5–1 km | 0.47 | [-0.02, +0.98] | [-0.06, +1.32] | 0.092 | 13 | 11 |
| meta-gallatin-tn | pilot | summer (Jun-Sep) | ring 1–2 km | -0.02 | [-0.33, +0.30] | [-0.23, +0.25] | 0.9 | 14 | 12 |
| meta-gallatin-tn | pilot | summer (Jun-Sep) | ring 2–3.5 km | -0.14 | [-0.27, +0.00] | [-0.22, -0.06] | 0.07 | 15 | 12 |
| meta-gallatin-tn | pilot | cool (Oct-Mar) | ring 0–0.5 km | -0.36 | [-1.39, +0.59] | [-1.13, +0.45] | 0.5 | 27 | 14 |
| meta-gallatin-tn | pilot | cool (Oct-Mar) | ring 0.5–1 km | -0.32 | [-1.00, +0.27] | [-0.86, +0.21] | 0.36 | 26 | 14 |
| meta-gallatin-tn | pilot | cool (Oct-Mar) | ring 1–2 km | -0.37 | [-0.97, +0.23] | [-0.48, -0.25] | 0.25 | 27 | 14 |
| meta-gallatin-tn | pilot | cool (Oct-Mar) | ring 2–3.5 km | -0.08 | [-0.36, +0.19] | [-0.21, +0.01] | 0.6 | 27 | 14 |
| meta-edgecore-mesa-az | census | all | ring 0–0.5 km | 0.50 | [-0.21, +1.02] | [-0.12, +1.13] | 0.13 | 50 | 27 |
| meta-edgecore-mesa-az | census | all | ring 0.5–1 km | -0.02 | [-0.81, +0.57] | [-0.62, +0.69] | 0.95 | 52 | 27 |
| meta-edgecore-mesa-az | census | all | ring 1–2 km | 0.10 | [-0.30, +0.41] | [-0.32, +0.50] | 0.61 | 54 | 30 |
| meta-edgecore-mesa-az | census | all | ring 2–3.5 km | 0.09 | [-0.02, +0.19] | [-0.04, +0.20] | 0.12 | 59 | 32 |
| meta-edgecore-mesa-az | census | summer (Jun-Sep) | ring 0–0.5 km | 0.19 | [-1.29, +1.12] | [-0.41, +0.92] | 0.79 | 31 | 12 |
| meta-edgecore-mesa-az | census | summer (Jun-Sep) | ring 0.5–1 km | -0.28 | [-1.68, +0.59] | [-0.84, +0.45] | 0.68 | 32 | 12 |
| meta-edgecore-mesa-az | census | summer (Jun-Sep) | ring 1–2 km | -0.04 | [-0.83, +0.46] | [-0.41, +0.38] | 0.92 | 32 | 13 |
| meta-edgecore-mesa-az | census | summer (Jun-Sep) | ring 2–3.5 km | 0.08 | [-0.12, +0.23] | [-0.06, +0.22] | 0.42 | 34 | 14 |
| meta-edgecore-mesa-az | census | cool (Oct-Mar) | ring 0–0.5 km | 0.83 | [+0.38, +1.27] | [+0.11, +1.24] | 0.0028 | 12 | 11 |
| meta-edgecore-mesa-az | census | cool (Oct-Mar) | ring 0.5–1 km | 0.12 | [-0.92, +0.86] | [-0.83, +0.89] | 0.8 | 13 | 12 |
| meta-edgecore-mesa-az | census | cool (Oct-Mar) | ring 1–2 km | 0.15 | [-0.24, +0.51] | [-0.36, +0.48] | 0.47 | 15 | 13 |
| meta-edgecore-mesa-az | census | cool (Oct-Mar) | ring 2–3.5 km | 0.09 | [-0.01, +0.19] | [-0.04, +0.15] | 0.12 | 18 | 14 |
| edgecore-mesa-az | census | all | ring 0–0.5 km | 0.39 | [-0.49, +1.08] | [-0.23, +0.99] | 0.35 | 50 | 30 |
| edgecore-mesa-az | census | all | ring 0.5–1 km | 0.05 | [-0.62, +0.49] | [-0.49, +0.61] | 0.87 | 52 | 27 |
| edgecore-mesa-az | census | all | ring 1–2 km | 0.01 | [-0.39, +0.32] | [-0.35, +0.36] | 0.97 | 55 | 30 |
| edgecore-mesa-az | census | all | ring 2–3.5 km | 0.01 | [-0.10, +0.12] | [-0.11, +0.11] | 0.8 | 59 | 32 |
| edgecore-mesa-az | census | summer (Jun-Sep) | ring 0–0.5 km | 0.22 | [-1.44, +1.33] | [-0.41, +0.93] | 0.78 | 31 | 13 |
| edgecore-mesa-az | census | summer (Jun-Sep) | ring 0.5–1 km | -0.31 | [-1.66, +0.52] | [-0.89, +0.45] | 0.64 | 32 | 12 |
| edgecore-mesa-az | census | summer (Jun-Sep) | ring 1–2 km | -0.12 | [-0.92, +0.39] | [-0.45, +0.24] | 0.75 | 32 | 13 |
| edgecore-mesa-az | census | summer (Jun-Sep) | ring 2–3.5 km | -0.02 | [-0.24, +0.16] | [-0.14, +0.09] | 0.88 | 34 | 14 |
| edgecore-mesa-az | census | cool (Oct-Mar) | ring 0–0.5 km | 0.55 | [-0.67, +1.40] | [-0.42, +1.26] | 0.34 | 13 | 13 |
| edgecore-mesa-az | census | cool (Oct-Mar) | ring 0.5–1 km | 0.41 | [+0.08, +0.73] | [-0.13, +0.78] | 0.034 | 13 | 11 |
| edgecore-mesa-az | census | cool (Oct-Mar) | ring 1–2 km | 0.11 | [-0.30, +0.48] | [-0.42, +0.49] | 0.61 | 16 | 13 |
| edgecore-mesa-az | census | cool (Oct-Mar) | ring 2–3.5 km | 0.06 | [-0.06, +0.17] | [-0.04, +0.12] | 0.33 | 18 | 14 |
| meta-gallatin-tn | census | all | ring 0–0.5 km | -0.08 | [-0.67, +0.48] | [-0.60, +0.56] | 0.79 | 44 | 27 |
| meta-gallatin-tn | census | all | ring 0.5–1 km | -0.02 | [-0.44, +0.36] | [-0.44, +0.47] | 0.91 | 42 | 27 |
| meta-gallatin-tn | census | all | ring 1–2 km | -0.24 | [-0.60, +0.11] | [-0.40, -0.04] | 0.19 | 44 | 28 |
| meta-gallatin-tn | census | all | ring 2–3.5 km | -0.11 | [-0.28, +0.04] | [-0.19, -0.03] | 0.18 | 45 | 28 |
| meta-gallatin-tn | census | summer (Jun-Sep) | ring 0–0.5 km | 0.43 | [-0.13, +1.03] | [-0.22, +1.45] | 0.18 | 14 | 11 |
| meta-gallatin-tn | census | summer (Jun-Sep) | ring 0.5–1 km | 0.47 | [-0.02, +0.98] | [-0.06, +1.32] | 0.092 | 13 | 11 |
| meta-gallatin-tn | census | summer (Jun-Sep) | ring 1–2 km | -0.02 | [-0.33, +0.30] | [-0.23, +0.25] | 0.9 | 14 | 12 |
| meta-gallatin-tn | census | summer (Jun-Sep) | ring 2–3.5 km | -0.14 | [-0.27, +0.00] | [-0.22, -0.06] | 0.07 | 15 | 12 |
| meta-gallatin-tn | census | cool (Oct-Mar) | ring 0–0.5 km | -0.36 | [-1.39, +0.59] | [-1.13, +0.45] | 0.5 | 27 | 14 |
| meta-gallatin-tn | census | cool (Oct-Mar) | ring 0.5–1 km | -0.32 | [-1.00, +0.27] | [-0.86, +0.21] | 0.36 | 26 | 14 |
| meta-gallatin-tn | census | cool (Oct-Mar) | ring 1–2 km | -0.37 | [-0.97, +0.23] | [-0.48, -0.25] | 0.25 | 27 | 14 |
| meta-gallatin-tn | census | cool (Oct-Mar) | ring 2–3.5 km | -0.08 | [-0.36, +0.19] | [-0.21, +0.01] | 0.6 | 27 | 14 |
| meta-edgecore-mesa-az | pilot | all | point control, pilot point | 1.30 | [+0.53, +2.15] | [+0.57, +2.13] | 0.014 | 40 | 10 |
| meta-edgecore-mesa-az | pilot | all | point control, verified point | 1.30 | [+0.53, +2.15] | [+0.57, +2.13] | 0.014 | 40 | 10 |
| meta-edgecore-mesa-az | pilot | summer (Jun-Sep) | point control, pilot point | 0.84 | [+0.04, +1.72] | [+0.07, +1.73] | 0.23 | 25 | 3 |
| meta-edgecore-mesa-az | pilot | summer (Jun-Sep) | point control, verified point | 0.84 | [+0.04, +1.72] | [+0.07, +1.73] | 0.23 | 25 | 3 |
| meta-edgecore-mesa-az | pilot | cool (Oct-Mar) | point control, pilot point | 1.72 | [+0.50, +3.00] | [+0.65, +3.13] | 0.029 | 10 | 7 |
| meta-edgecore-mesa-az | pilot | cool (Oct-Mar) | point control, verified point | 1.72 | [+0.50, +3.00] | [+0.65, +3.13] | 0.029 | 10 | 7 |
| edgecore-mesa-az | pilot | all | point control, pilot point | 0.91 | [+0.28, +1.60] | [+0.28, +1.37] | 0.015 | 41 | 17 |
| edgecore-mesa-az | pilot | all | point control, verified point | 0.91 | [+0.28, +1.60] | [+0.28, +1.37] | 0.015 | 41 | 17 |
| edgecore-mesa-az | pilot | summer (Jun-Sep) | point control, pilot point | 0.37 | [-0.54, +1.19] | [-0.04, +0.91] | 0.47 | 25 | 7 |
| edgecore-mesa-az | pilot | summer (Jun-Sep) | point control, verified point | 0.37 | [-0.54, +1.19] | [-0.04, +0.91] | 0.47 | 25 | 7 |
| edgecore-mesa-az | pilot | cool (Oct-Mar) | point control, pilot point | 1.64 | [+0.67, +2.71] | [+0.89, +3.52] | 0.0089 | 10 | 10 |
| edgecore-mesa-az | pilot | cool (Oct-Mar) | point control, verified point | 1.64 | [+0.67, +2.71] | [+0.89, +3.52] | 0.0089 | 10 | 10 |
| meta-gallatin-tn | pilot | all | point control, pilot point | -0.78 | [-1.50, -0.19] | [-1.41, -0.03] | 0.027 | 42 | 26 |
| meta-gallatin-tn | pilot | all | point control, verified point | -0.89 | [-1.62, -0.29] | [-1.48, -0.18] | 0.013 | 42 | 26 |
| meta-gallatin-tn | pilot | summer (Jun-Sep) | point control, pilot point | -0.05 | [-0.60, +0.46] | [-0.57, +0.64] | 0.86 | 14 | 11 |
| meta-gallatin-tn | pilot | summer (Jun-Sep) | point control, verified point | -0.28 | [-0.74, +0.15] | [-0.64, +0.37] | 0.26 | 14 | 11 |
| meta-gallatin-tn | pilot | cool (Oct-Mar) | point control, pilot point | -1.13 | [-2.38, -0.18] | [-2.18, -0.11] | 0.068 | 24 | 13 |
| meta-gallatin-tn | pilot | cool (Oct-Mar) | point control, verified point | -1.16 | [-2.46, -0.19] | [-2.16, -0.19] | 0.07 | 24 | 13 |
| meta-edgecore-mesa-az | census | all | point control, pilot point | 0.57 | [-0.33, +1.35] | [-0.02, +1.34] | 0.2 | 43 | 24 |
| meta-edgecore-mesa-az | census | all | point control, verified point | 0.57 | [-0.33, +1.35] | [-0.02, +1.34] | 0.2 | 43 | 24 |
| meta-edgecore-mesa-az | census | summer (Jun-Sep) | point control, pilot point | 0.43 | [-1.31, +1.62] | [+0.15, +0.94] | 0.62 | 28 | 10 |
| meta-edgecore-mesa-az | census | summer (Jun-Sep) | point control, verified point | 0.43 | [-1.31, +1.62] | [+0.15, +0.94] | 0.62 | 28 | 10 |
| meta-edgecore-mesa-az | census | cool (Oct-Mar) | point control, pilot point | 1.17 | [+0.15, +2.24] | [-0.01, +2.55] | 0.051 | 10 | 11 |
| meta-edgecore-mesa-az | census | cool (Oct-Mar) | point control, verified point | 1.17 | [+0.15, +2.24] | [-0.01, +2.55] | 0.051 | 10 | 11 |
| edgecore-mesa-az | census | all | point control, pilot point | 0.59 | [-0.49, +1.49] | [+0.03, +1.35] | 0.27 | 44 | 25 |
| edgecore-mesa-az | census | all | point control, verified point | 0.59 | [-0.49, +1.49] | [+0.03, +1.35] | 0.27 | 44 | 25 |
| edgecore-mesa-az | census | summer (Jun-Sep) | point control, pilot point | 0.30 | [-2.01, +1.86] | [+0.01, +0.90] | 0.79 | 28 | 10 |
| edgecore-mesa-az | census | summer (Jun-Sep) | point control, verified point | 0.30 | [-2.01, +1.86] | [+0.01, +0.90] | 0.79 | 28 | 10 |
| edgecore-mesa-az | census | cool (Oct-Mar) | point control, pilot point | 1.29 | [+0.18, +2.39] | [+0.23, +3.16] | 0.044 | 10 | 12 |
| edgecore-mesa-az | census | cool (Oct-Mar) | point control, verified point | 1.29 | [+0.18, +2.39] | [+0.23, +3.16] | 0.044 | 10 | 12 |
| meta-gallatin-tn | census | all | point control, pilot point | -0.78 | [-1.50, -0.19] | [-1.41, -0.03] | 0.027 | 42 | 26 |
| meta-gallatin-tn | census | all | point control, verified point | -0.89 | [-1.62, -0.29] | [-1.48, -0.18] | 0.013 | 42 | 26 |
| meta-gallatin-tn | census | summer (Jun-Sep) | point control, pilot point | -0.05 | [-0.60, +0.46] | [-0.57, +0.64] | 0.86 | 14 | 11 |
| meta-gallatin-tn | census | summer (Jun-Sep) | point control, verified point | -0.28 | [-0.74, +0.15] | [-0.64, +0.37] | 0.26 | 14 | 11 |
| meta-gallatin-tn | census | cool (Oct-Mar) | point control, pilot point | -1.13 | [-2.38, -0.18] | [-2.18, -0.11] | 0.068 | 24 | 13 |
| meta-gallatin-tn | census | cool (Oct-Mar) | point control, verified point | -1.16 | [-2.46, -0.19] | [-2.16, -0.19] | 0.07 | 24 | 13 |
