# Data dictionary

Temperatures are in °C. Rings are concentric zones around each site's centre:
ring 0 = 0–0.5 km (the core), 1 = 0.5–1 km, 2 = 1–2 km, 3 = 2–3.5 km, 4 = 3.5–5 km (the reference).
"Change" means the after period minus the before period of (ring minus ring 4, in the same image),
with calendar-month means removed, unless stated otherwise. Dates are UTC.

## data/sites/

**data_centers.csv** (36 rows): the census.
`site_id`, `legacy_id` (ID in the code), `name`, `operator`, `lat`, `lon` (WGS84, main data-hall
buildings), `location_source` (`checked_on_imagery`), `type` (`greenfield` = built on undeveloped
land; `conversion` = existing building or developed land), `construction_year` and
`construction_year_source` as recorded before analysis (`epoch_ai`, `pilot_imagery`, `landsat_manual`,
or blank = dated from Landsat), `announced_year` (public announcement, Meta sites),
`operation_start`, `cluster` (sites with the same number are within 1 km and count as one
independent site in the statistics), `description` (conversions only).

**warehouses.csv** (23 rows): large distribution buildings used as land-change comparisons.
`site_id`, `legacy_id`, `name`, `lat`, `lon`, `location_source`, `paired_data_center`,
`distance_to_data_center_km`. Derived from OpenStreetMap (ODbL).

**pilot_points.csv** (4 rows): the points used in the pilot analysis, kept to check that the census
code reproduces it. `data_center`, `before_years`, `after_years` give the pilot periods.

**cooling.csv** (36 rows): `cooling` (`dry`, `cooling towers`, `evaporative assist` = outside air
with evaporative cooling on hot days, `unknown`), `detail`, `basis` (`site` = statement about this
facility; `operator` = company-wide statement), `operating_from` (date the facility was operating,
used to compute how much of the after period it ran), `source_url`.

**land_cover_aridity.csv**: one row per site and NLCD edition. `nlcd_year`; `nlcd_<class>` =
fraction of the 0–0.5 km core in each NLCD class (11 water, 21–24 developed, 31 barren, 41–43
forest, 52 shrub, 71 grassland, 81 pasture, 82 crops, 90/95 wetland); `aridity` = mean annual
precipitation ÷ potential evapotranspiration, 2013–2022 (TerraClimate).

**epoch_power_timelines.csv**: Epoch AI timeline records for the census sites: `Date`,
`Construction status`, `IT power (MW)`, `Power (MW)` (total facility power). Includes planned future
records; the analysis uses records up to September 2026.

## data/landsat_rings/

One file per site (`<site_id>.csv`): every Landsat 8/9 Collection 2 Level 2 image from 2013 to 2026
with clear pixels in a ring. Columns: `site_id`, `date`, `ring` (0–4), `lst_c` (mean surface
temperature of clear pixels), `ndvi`, `emissivity`, `albedo` (Liang 2001 broadband). Clouds and cloud
shadows removed with QA_PIXEL bits 3 and 4. Images are at about 10:30 local time.

## data/modis/

**terra_monthly.csv**, **aqua_monthly.csv**: monthly mean of daily MODIS surface temperature
(MOD11A1 / MYD11A1 v6.1), January 2004 to August 2026. `site_id` (the data center a point belongs
to), `point_id` (the site itself, or a placebo point `<site_id>-pNN`), `kind` (`site` or `placebo`),
`zone` (`disk` = 0–10 km; `annulus` = 10–20 km), `month`, `lst_day_c`, `lst_night_c`.

**placebo_points.csv** (280 rows): random points 20–60 km from each data center with the same
pre-construction land cover and at least 10 km from every census site. `data_center`, `point_id`,
`lat`, `lon`, `cover`.

## data/ecostress_night/

One file per site group (`mesa-az`, `midlothian-tx`, `gallatin-tn`): every ECOSTRESS ECO_L2T_LSTE
v002 image flagged night, mid-2018 onward. `site_id`, `granule` (NASA granule ID), `utc` (start
time), `local_hour` (local mean solar time), `cloud_mask` (whether the cloud layer was applied),
`zone` (`ring0`–`ring4`, or a 9 × 9 pixel window at `pt_verified` = the site point, `pt_pilot` =
the pilot-analysis point, `pt_control` = the pilot analysis's control point), `lst_c`, `valid_frac`
(share of the ring's pixels that were clear; blank for points). The analysis keeps 21:00–05:00 local
time and one tile per overpass. The Mesa file covers two sites: `meta-edgecore-mesa-az` and
`edgecore-mesa-az`.

## results/

**landsat_periods.csv**: for every data center and warehouse, `construction_year_used`,
`construction_source` (how it was set), `landsat_detected_year`, `before_years`, `after_years`,
`landsat_images`, and `not_analysed_because` where a site was skipped.

**landsat_ring_changes.csv**: one row per site and ring 0–3. `dlst` (change vs ring 4), `ci_lo`,
`ci_hi` (95% interval, resampling images), `ci_lo_block`, `ci_hi_block` (resampling whole years),
`p` (Welch's test), `mde` (smallest detectable change at 80% power), `n_base`, `n_op` (images
before / after), `dlst_raw` (without month adjustment), `dndvi`, `dalbedo` (change within the ring),
`demis_core`, `demis_far` (raw emissivity change in ring 0 and ring 4).

**landsat_core_changes.csv**: ring 0 rows for all analysed data centers and warehouses, with `name`,
`group`, `cluster_id`, land cover fractions before construction (`frac_*`, from `nlcd_year_used`),
`dominant_cover`, `aridity`, `setting` (`humid` if aridity ≥ 0.5; `dry irrigated` if drier and at
least half crop or pasture; otherwise `dry natural`), `significant` (95% interval excludes zero).

**crosssite_models.csv**: regressions of core change across the 29 independent greenfield sites.
`model`, `term`, `coef`, `ci_lo`, `ci_hi` (resampling whole sites).

**warehouse_comparison_models.csv**: the same regression with data centers and warehouses together.
`sample`: `all`; `far` = warehouses ≥ 5 km from any data center; `far_strong` = also ΔNDVI ≤ −0.05;
`no_albedo` = without the albedo term. `is_dc` is the extra change at data centers.

**warehouse_pairs.csv**: each warehouse next to its data center: `dlst_dc`, `dlst`, `dc_minus_wh`,
`dndvi_dc`, `dndvi`, `dalbedo_dc`, `dalbedo`, `nearest_km` (distance to its data center).

**cooling_units.csv**, **cooling_tests.csv**: cooling type per independent site with `residual`
(change not explained by the land-change regression) and `operating_share` (share of the after
period the site was running); permutation tests of dry minus evaporative.

**energy_ceiling.csv**: `power_mw` (mean Epoch power, January 2025 to September 2026), heat flux over
the core and over a 1 km disk (W/m²), and the warming each would cause if all heat entered the
surface (`full_warming_*`, coupling coefficient 25 W m⁻² K⁻¹).

**modis_metric_terra.csv**, **modis_metric_aqua.csv**: the Marinoni et al. metric per site, `band`
day or night: `op_month` and `op_source` (`recorded` or `estimated`), `marinoni` (0–10 km disk, mean
of 12 months after operation minus 60 before, seasonal cycle removed), `referenced` (disk minus
10–20 km ring), `placebo_mean`, `placebo_sd`, `placebo_ref_mean`, `n_placebo`.

**night_ring_changes.csv**, **night_point_changes.csv**: night change by `window` (`pilot` = pilot
periods; `census` = up to 5 years before construction vs 2025–2026), `season` (`all`, Jun–Sep,
Oct–Mar), and `ring` (0–3) or `point` (`verified` or `pilot` site point minus the control point);
adjusted for calendar month and hour of the night.

**purpleair_sensor_counts.csv**: number of outdoor PurpleAir sensors within 2 km of each site, and how
many ran from before construction into 2025 or later. Sensor locations are not released.

## paper/

`tables/` and `figures/` are the paper's tables and figures; `supplement/` is the supplementary
material (Markdown, and one CSV per table). `numbers_ledger.csv` lists every number quoted in the
paper with the result file and calculation it comes from.
