"""Build the supplementary material: outputs/paper/supplement/ (supplement.md plus one CSV per table).

Reads only result CSVs (run run_all.sh first). Warehouse and data-center coordinates are included;
PurpleAir sensor locations are not, since many are at private homes.
"""

import ast
from pathlib import Path

import pandas as pd

from make_paper_outputs import YEAR_SOURCE, markdown_table

ROOT = Path(__file__).resolve().parents[2]
CENSUS, NIGHT = ROOT / "outputs" / "census", ROOT / "outputs" / "night"
OUT = ROOT / "outputs" / "paper" / "supplement"
SECTIONS: list[str] = []


def years(text) -> str:
    values = ast.literal_eval(text) if isinstance(text, str) and text.startswith("[") else []
    return f"{min(values)}–{max(values)}" if len(values) > 1 else (str(values[0]) if values else "")


def add_table(name: str, title: str, note: str, df: pd.DataFrame, digits: int = 2) -> None:
    df.to_csv(OUT / f"{name}.csv", index=False)
    SECTIONS.append(f"### {title}\n\n{note}\n\n{markdown_table(df, digits)}")


def add_text(text: str) -> None:
    SECTIONS.append(text.strip() + "\n")


def load() -> dict[str, pd.DataFrame]:
    sites = pd.read_csv(ROOT / "data" / "census" / "census_sites.csv")
    return {
        "sites": sites,
        "windows": pd.read_csv(CENSUS / "census_windows.csv"),
        "core": pd.read_csv(CENSUS / "crosssite_core.csv"),
        "rings": pd.read_csv(CENSUS / "rings_summary.csv"),
        "cooling": pd.read_csv(ROOT / "data" / "census" / "cooling_labels.csv"),
        "energy": pd.read_csv(CENSUS / "energy_ceiling.csv"),
    }


def table_sites(d: dict) -> None:
    t = (d["core"][d["core"].group.isin(["greenfield", "conversion"])]
         .merge(d["sites"][["site_id", "operator", "lat", "lon", "cluster_id"]], on="site_id", suffixes=("", "_s"))
         .merge(d["windows"][["site_id", "construction_year", "construction_source", "detected_year",
                              "base_years", "op_years"]], on="site_id"))
    t = t.sort_values(["group", "setting", "dlst"])
    out = pd.DataFrame({
        "Site ID": t.site_id, "Site": t.name, "Operator": t.operator.fillna(""), "Type": t.group,
        "Lat": t.lat.round(5), "Lon": t.lon.round(5), "Setting": t.setting,
        "Cover before": t.dominant_cover.str.replace("_", "/"), "Aridity": t.aridity,
        "Year used": t.construction_year.astype(int), "Year source": t.construction_source.replace(YEAR_SOURCE),
        "Landsat-detected year": t.detected_year.map(lambda v: "" if pd.isna(v) else str(int(v))),
        "Before": t.base_years.map(years), "After": t.op_years.map(years),
        "Images before": t.n_base, "Images after": t.n_op,
        "Core ΔLST": t.dlst, "CI (images)": t.apply(lambda r: f"[{r.ci_lo:+.2f}, {r.ci_hi:+.2f}]", axis=1),
        "CI (years)": t.apply(lambda r: f"[{r.ci_lo_block:+.2f}, {r.ci_hi_block:+.2f}]", axis=1),
        "p": t.p.map(lambda v: f"{v:.2g}"), "Smallest detectable": t.mde, "ΔNDVI": t.dndvi, "ΔAlbedo": t.dalbedo,
    })
    add_table("tableS1_sites", "Table S1. All census sites: location, periods and core daytime change",
              "Core ΔLST = change in (0–0.5 km mean minus 3.5–5 km mean), month-adjusted, °C. Two 95% "
              "intervals: resampling images, and resampling whole years. Year source: epoch_ai = Epoch AI "
              "record; pilot_imagery = imagery check in the pilot analysis; landsat_manual = reading of the "
              "Landsat record; announcement_year / landsat_detected = the earlier of the Landsat-detected year "
              "and the public announcement year, labelled by which one it was.",
              out, digits=3)


def table_rings(d: dict) -> None:
    rings = d["rings"].pivot(index="site_id", columns="ring", values="dlst")
    rings.columns = [f"{label}" for label in ("0–0.5 km", "0.5–1 km", "1–2 km", "2–3.5 km")]
    rings["Core vs 2–3.5 km ring"] = rings["0–0.5 km"] - rings["2–3.5 km"]
    names = d["core"][["site_id", "name", "group", "setting"]]
    t = names.merge(rings.reset_index(), on="site_id")
    t = t[t.group.isin(["greenfield", "conversion"])].sort_values(["group", "setting", "0–0.5 km"])
    t["Same sign"] = (t["0–0.5 km"] > 0) == (t["Core vs 2–3.5 km ring"] > 0)
    t = t.rename(columns={"site_id": "Site ID", "name": "Site", "group": "Type", "setting": "Setting"})
    add_table("tableS2_ring_profiles", "Table S2. Ring profiles and a nearer reference ring",
              "Change in each ring minus the 3.5–5 km ring (°C). The last columns use the 2–3.5 km ring as "
              "the reference instead, to test whether change in the outer ring drives the core result.", t)


def table_warehouses(d: dict) -> None:
    w = d["sites"][d["sites"].role == "warehouse"][["site_id", "name", "lat", "lon", "nearest_km", "note"]]
    w["Paired data center"] = w.note.str.extract(r"paired with (\S+?);")[0]
    w = (w.merge(d["windows"][["site_id", "construction_year", "reason"]], on="site_id", how="left")
          .merge(d["core"][["site_id", "setting", "dlst", "ci_lo", "ci_hi", "dndvi", "dalbedo"]], on="site_id", how="left"))
    dc_names = d["sites"].set_index("site_id")["name"]
    t = pd.DataFrame({
        "Warehouse ID": w.site_id, "Warehouse": w.name, "Lat": w.lat.round(5), "Lon": w.lon.round(5),
        "Paired data center": w["Paired data center"].map(dc_names), "Distance (km)": w.nearest_km,
        "Setting": w.setting.fillna(""),
        "Year (Landsat)": w.construction_year.map(lambda v: "" if pd.isna(v) else str(int(v))),
        "Core ΔLST": w.dlst, "CI": w.apply(lambda r: "" if pd.isna(r.dlst) else f"[{r.ci_lo:+.2f}, {r.ci_hi:+.2f}]", axis=1),
        "ΔNDVI": w.dndvi, "ΔAlbedo": w.dalbedo, "Not used because": w.reason.fillna(""),
    }).sort_values(["Paired data center", "Warehouse ID"])
    add_table("tableS3_warehouses", "Table S3. Warehouses used as land-change comparisons",
              "Large distribution buildings (roof ≥ 40,000 m²) from OpenStreetMap, 3–30 km from a census data "
              "center and ≥ 3 km from all of them, checked on imagery. Construction year detected from Landsat.", t)


def table_cooling(d: dict) -> None:
    c = d["cooling"].merge(d["sites"][["site_id", "group"]], on="site_id")
    t = pd.DataFrame({"Site ID": c.site_id, "Site": c.name, "Type": c.group, "Cooling": c.cooling,
                      "Detail": c.detail, "Basis": c.basis.fillna(""), "Source": c.source_url.fillna("")})
    add_table("tableS4_cooling", "Table S4. Cooling type and sources",
              "Dry = all heat rejected as warm air (air-cooled chillers, dry coolers, closed-loop to dry coolers). "
              "Cooling towers and evaporative assist (outside air with evaporative cooling on hot days) were "
              "grouped as evaporative. Basis: site = a statement about this facility; operator = a company-wide "
              "statement.", t)


def table_energy(d: dict) -> None:
    e = d["energy"].sort_values("power_mw", ascending=False)
    t = pd.DataFrame({"Site ID": e.site_id, "Site": e.name, "Power (MW)": e.power_mw,
                      "Heat flux over core (W/m²)": e.flux_core, "Heat flux over 1 km disk (W/m²)": e.flux_1km,
                      "Warming if all reached surface, core (°C)": e.full_warming_core,
                      "Same, 1 km disk (°C)": e.full_warming_1km})
    add_table("tableS5_energy", "Table S5. Energy-balance ceiling by site",
              "Power = mean Epoch AI facility power, Jan 2025–Sep 2026. Warming assumes a coupling coefficient "
              "of 25 W m⁻² K⁻¹. Greenfield sites with Epoch power data only.", t, digits=1)


def table_marinoni() -> None:
    frames = []
    for sensor, file in (("Terra", "marinoni_results.csv"), ("Aqua", "marinoni_results_aqua.csv")):
        r = pd.read_csv(CENSUS / file)
        frames.append(r.assign(sensor=sensor))
    r = pd.concat(frames)
    wide = r.pivot_table(index=["site_id", "name", "op_month", "op_source"], columns=["sensor", "band"],
                         values=["marinoni", "placebo_mean", "referenced"])
    wide.columns = [f"{sensor} {band} {value}" for value, sensor, band in wide.columns]
    order = [f"{s} {b} {v}" for s in ("Terra", "Aqua") for b in ("day", "night")
             for v in ("marinoni", "placebo_mean", "referenced")]
    t = wide[order].reset_index().rename(columns={"site_id": "Site ID", "name": "Site", "op_month": "Operation month",
                                                  "op_source": "Month source"})
    t.columns = [c.replace("marinoni", "metric").replace("placebo_mean", "placebos") for c in t.columns]
    add_table("tableS6_marinoni", "Table S6. The 10 km metric by site, Terra and Aqua",
              "metric = Marinoni et al. metric at the site (0–10 km disk, 12 months after vs 60 before, °C); "
              "placebos = mean of the same metric at up to 10 placebo points; referenced = site disk minus its "
              "10–20 km ring. Month source: recorded (Epoch/operator) or estimated (middle of construction year + 2.25 years).", t)


def table_night() -> None:
    rings = pd.read_csv(NIGHT / "night_rings_summary.csv")
    points = pd.read_csv(NIGHT / "night_point_summary.csv")
    t = pd.concat([rings.assign(design=rings.ring.map(lambda r: f"ring {['0–0.5', '0.5–1', '1–2', '2–3.5'][r]} km")),
                   points.assign(design=points.point.map({"verified": "point control, verified point",
                                                          "paper": "point control, pilot point"}))])
    t["CI"] = t.apply(lambda r: f"[{r.ci_lo:+.2f}, {r.ci_hi:+.2f}]", axis=1)
    t["CI (years)"] = t.apply(lambda r: f"[{r.ci_lo_block:+.2f}, {r.ci_hi_block:+.2f}]", axis=1)
    t["window"] = t["window"].replace({"paper": "pilot"})
    t = t[["site_id", "window", "season", "design", "change", "CI", "CI (years)", "p", "n_base", "n_op"]]
    t = t.rename(columns={"site_id": "Site", "window": "Periods", "season": "Season", "design": "Design",
                          "change": "Change (°C)", "n_base": "Images before", "n_op": "Images after"})
    t["p"] = t["p"].map(lambda v: f"{v:.2g}")
    add_table("tableS7_night", "Table S7. Night change, all designs, periods and seasons",
              "ECOSTRESS 21:00–05:00 local solar time, one tile per overpass, core and outer ring ≥ 50% clear, "
              "adjusted for calendar month and night-hour bin. Periods: pilot = before 2019–2021 (Midlothian "
              "2018) and after as in the pilot analysis; census = up to 5 years before construction and "
              "2025–2026. Midlothian has fewer than two usable images before construction and is omitted.", t)


METHODS = """
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
notebook `dc_night.ipynb`. Analysis: Python package `dc_heat` with unit tests (numpy, pandas, scipy,
matplotlib). All statistics, tables and figures in the paper and this supplement are rebuilt from the
result CSVs by `analysis/scripts/run_all.sh`; resampling uses fixed random seeds, so results are exactly
reproducible. Every number quoted in the paper is traced to its source file in `numbers_ledger.csv`.

## S3. Supplementary tables
"""


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    data = load()
    add_text("# Supplementary Material\n\n*Land Change, Not Server Heat: A Satellite Census of Surface "
             "Temperature Around 36 U.S. Data Centers* [working title]")
    add_text(METHODS)
    table_sites(data)
    table_rings(data)
    table_warehouses(data)
    table_cooling(data)
    table_energy(data)
    table_marinoni()
    table_night()
    text = "\n".join(SECTIONS)
    (OUT / "supplement.md").write_text(text)
    (ROOT / "docs" / "supplementary-material.md").write_text(text)   # repo copy, kept in sync on every run
    print(f"wrote supplement.md and {len(list(OUT.glob('*.csv')))} tables to {OUT}")
