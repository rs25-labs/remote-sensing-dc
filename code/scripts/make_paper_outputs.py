"""Phase 8: collate every analysis output into the paper's tables, figures and number ledger.

Reads only result CSVs in outputs/ (run the run_*.py scripts first) and writes outputs/paper/:
tables as CSV and Markdown, figures as PNG and SVG, and numbers_ledger.csv, which records where every
number quoted in the paper comes from.
"""

import json
from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd
from scipy import stats as sps

from dcheat import crosssite

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
CENSUS, NIGHT, PAPER = ROOT / "outputs" / "census", ROOT / "outputs" / "night", ROOT / "outputs" / "paper"
SETTING_ORDER = ["dry natural", "dry irrigated", "humid"]
SETTING_COLOURS = {"dry natural": "#c2873a", "dry irrigated": "#6f9a3e", "humid": "#2f6fa3"}
LEDGER: list[dict] = []
YEAR_SOURCE = {"epoch": "epoch_ai", "paper": "pilot_imagery", "manual": "landsat_manual",
               "announced": "announcement_year", "detected": "landsat_detected"}


def record(key: str, value, source: str, how: str) -> None:
    LEDGER.append({"key": key.replace(" ", "_"), "value": value, "source": source, "how": how})


def markdown_table(df: pd.DataFrame, digits: int = 2) -> str:
    shown = df.copy()
    for col in shown.select_dtypes("float"):
        shown[col] = shown[col].map(lambda v: "" if pd.isna(v) else f"{v:.{digits}f}")
    header = "| " + " | ".join(shown.columns) + " |"
    rule = "|" + "|".join("---" for _ in shown.columns) + "|"
    body = ["| " + " | ".join("" if pd.isna(v) else str(v) for v in row) + " |" for row in shown.itertuples(index=False)]
    return "\n".join([header, rule, *body]) + "\n"


def write_table(df: pd.DataFrame, name: str, title: str, digits: int = 2, folder: Path = PAPER) -> None:
    df.to_csv(folder / f"{name}.csv", index=False)
    (folder / f"{name}.md").write_text(f"**{title}**\n\n" + markdown_table(df, digits))


def save_figure(fig, name: str) -> None:
    fig.savefig(PAPER / f"{name}.png", dpi=200, bbox_inches="tight")
    fig.savefig(PAPER / f"{name}.svg", bbox_inches="tight")
    plt.close(fig)


def load_core() -> pd.DataFrame:
    core = pd.read_csv(CENSUS / "crosssite_core.csv")
    windows_used = pd.read_csv(CENSUS / "census_windows.csv")
    cooling = pd.read_csv(ROOT / "data" / "census" / "cooling_labels.csv")[["site_id", "cooling"]]
    energy = pd.read_csv(CENSUS / "energy_ceiling.csv")[["site_id", "power_mw"]]
    return (core.merge(windows_used[["site_id", "construction_source", "base_years", "op_years"]], on="site_id")
                .merge(cooling, on="site_id", how="left").merge(energy, on="site_id", how="left"))


def greenfield_units(core: pd.DataFrame) -> pd.DataFrame:
    values = ["dlst", "ci_lo", "ci_hi", "dndvi", "dalbedo", "aridity"]
    green = core[core.group == "greenfield"]
    return crosssite.collapse_clusters(green[["site_id", "cluster_id", "setting", "name"] + values], values)


# --- tables -------------------------------------------------------------------------------

def table_sites(core: pd.DataFrame) -> None:
    sites = pd.read_csv(ROOT / "data" / "census" / "census_sites.csv")[["site_id", "operator", "construction_year"]]
    t = core[core.group.isin(["greenfield", "conversion"])].merge(sites, on="site_id", suffixes=("", "_reg"))
    t = t.sort_values(["group", "setting", "dlst"])
    t["construction_source"] = t.construction_source.replace(YEAR_SOURCE)
    cols = {"name": "Site", "operator": "Operator", "group": "Type", "setting": "Setting",
            "dominant_cover": "Cover before", "aridity": "Aridity", "construction_source": "Year source",
            "base_years": "Before", "op_years": "After", "cooling": "Cooling", "power_mw": "Power (MW)",
            "dlst": "Core dLST", "ci_lo": "CI low", "ci_hi": "CI high", "dndvi": "dNDVI", "dalbedo": "dAlbedo"}
    write_table(t[list(cols)].rename(columns=cols), "table1_sites",
                "Table 1. Census sites, settings and core (0-0.5 km) daytime change vs the 3.5-5 km ring")
    record("n_sites_census", int(len(t)), "crosssite_core.csv", "greenfield + conversion rows, ring 0")
    record("n_greenfield_sites", int((t.group == "greenfield").sum()), "crosssite_core.csv", "group == greenfield")


def table_settings(units: pd.DataFrame) -> None:
    rows = []
    for setting in SETTING_ORDER:
        d = units[units.setting == setting]
        rows.append({"Setting": setting, "Independent sites": len(d), "Cooled": int((d.dlst < 0).sum()),
                     "Warmed": int((d.dlst >= 0).sum()), "Median dLST": d.dlst.median(),
                     "Min": d.dlst.min(), "Max": d.dlst.max(), "Median dNDVI": d.dndvi.median()})
        record(f"{setting}_cooled_of", f"{int((d.dlst < 0).sum())}/{len(d)}", "crosssite_core.csv",
               "greenfield, clusters collapsed, dlst < 0")
        record(f"{setting}_median_dlst", round(d.dlst.median(), 2), "crosssite_core.csv", "greenfield units, median")
    write_table(pd.DataFrame(rows), "table2_settings", "Table 2. Core daytime change by setting (independent sites)")
    test = crosssite.sign_test(units.assign(flag=units.setting == "dry natural"), "flag")
    rho, p_rho = sps.spearmanr(units.aridity, units.dlst)
    record("n_independent_units", len(units), "crosssite_core.csv", "greenfield clusters collapsed")
    record("fisher_p_dry_natural", f"{test['p']:.2g}", "crosssite_core.csv", "dry natural vs rest, Fisher exact")
    record("spearman_rho_aridity", round(rho, 2), "crosssite_core.csv", "units, dlst vs aridity")
    record("spearman_p_aridity", f"{p_rho:.2g}", "crosssite_core.csv", "units, dlst vs aridity")


def table_models() -> None:
    rows = []
    for name, label in (("crosssite_ols_dndvi_dalbedo", "Land change"),
                        ("crosssite_ols_dndvi_dalbedo_aridity", "Land change + aridity")):
        fit = pd.read_csv(CENSUS / f"{name}.csv", index_col=0)
        for term, r in fit.iterrows():
            rows.append({"Model": label, "Term": term, "Coefficient": r.coef, "CI low": r.ci_lo, "CI high": r.ci_hi})
            record(f"ols_{name.removeprefix('crosssite_ols_')}_{term}", round(r.coef, 2), f"{name}.csv",
                   f"coef [{r.ci_lo:.2f}, {r.ci_hi:.2f}], unit bootstrap")
    warehouse = pd.read_csv(CENSUS / "warehouse_ols.csv")
    labels = {"all": "DC vs warehouse, all", "far": "DC vs warehouse, warehouses >= 5 km",
              "far_strong": "DC vs warehouse, >= 5 km and dNDVI <= -0.05", "no_albedo": "DC vs warehouse, no albedo"}
    for sample, d in warehouse.groupby("sample", sort=False):
        for r in d.itertuples():
            rows.append({"Model": labels[sample], "Term": r.term, "Coefficient": r.coef,
                         "CI low": r.ci_lo, "CI high": r.ci_hi})
        dc = d[d.term == "is_dc"].iloc[0]
        record(f"is_dc_{sample}", round(dc.coef, 2), "warehouse_ols.csv", f"[{dc.ci_lo:.2f}, {dc.ci_hi:.2f}]")
    write_table(pd.DataFrame(rows), "table3_models",
                "Table 3. Cross-site regressions of core dLST (95% CIs from resampling whole sites)")


def table_marinoni() -> None:
    rows = []
    for sensor, file in (("Terra", "marinoni_results.csv"), ("Aqua", "marinoni_results_aqua.csv")):
        r = pd.read_csv(CENSUS / file)
        for band, d in r.groupby("band"):
            row = {"Sensor": sensor, "Band": band, "Sites": int(d.marinoni.notna().sum()),
                   "Marinoni metric, sites": d.marinoni.mean(), "Same metric, placebos": d.placebo_mean.mean(),
                   "Referenced, sites": d.referenced.mean(), "Referenced, placebos": d.placebo_ref_mean.mean(),
                   "r(site, placebo)": d[["marinoni", "placebo_mean"]].corr().iloc[0, 1]}
            rows.append(row)
            for key in ("Marinoni metric, sites", "Same metric, placebos", "Referenced, sites"):
                record(f"marinoni_{sensor}_{band}_{key.split(',')[0].split()[0].lower()}_{key.split(', ')[1]}",
                       round(row[key], 2), file, f"mean over sites, band == {band}")
    write_table(pd.DataFrame(rows), "table4_marinoni",
                "Table 4. Marinoni et al. metric (0-10 km, 12 months after vs 60 before) at sites and placebos")


def table_cooling() -> None:
    t = pd.read_csv(CENSUS / "cooling_tests.csv")
    t = t[t.measure == "residual"].drop(columns="measure").rename(columns={
        "sample": "Sample", "n_dry": "Dry", "n_evaporative": "Evaporative",
        "diff": "Dry minus evaporative (residual, °C)", "p": "Permutation p"})
    write_table(t, "table5_cooling", "Table 5. Cooling type vs residual core warming (exploratory)")
    main = t.iloc[0]
    record("cooling_residual_diff", round(main.iloc[3], 2), "cooling_tests.csv", "All labelled units, residual")
    record("cooling_residual_p", round(main.iloc[4], 2), "cooling_tests.csv", "All labelled units, residual")


def table_night() -> None:
    rings = pd.read_csv(NIGHT / "night_rings_summary.csv")
    rings = rings[(rings.ring == 0) & (rings.season.isin(["all", "cool (Oct-Mar)"]))]
    points = pd.read_csv(NIGHT / "night_point_summary.csv")
    points = points[(points.point == "verified") & (points.window == "paper") & (points.season == "all")]
    t = pd.concat([rings.assign(design="rings, core vs 3.5-5 km"),
                   points.assign(design="point control (paper design)")])
    t = t[["site_id", "design", "window", "season", "change", "ci_lo", "ci_hi", "p", "n_base", "n_op"]]
    t["window"] = t["window"].replace({"paper": "pilot"})
    write_table(t, "table6_night", "Table 6. Night change (ECOSTRESS, 21-05 local; month and hour adjusted)")
    for r in t.itertuples():
        if r.design.startswith("rings") and r.season == "all":
            record(f"night_{r.site_id}_{r.window}", round(r.change, 2), "night_rings_summary.csv",
                   f"ring 0, all seasons, [{r.ci_lo:.2f}, {r.ci_hi:.2f}]")


def table_energy() -> None:
    e = pd.read_csv(CENSUS / "energy_ceiling.csv")
    upper = pd.read_csv(CENSUS / "warehouse_ols.csv").query("term == 'is_dc'").ci_hi.max()
    record("energy_n_sites", len(e), "energy_ceiling.csv", "greenfield sites with Epoch power")
    record("energy_median_power_mw", round(e.power_mw.median()), "energy_ceiling.csv", "after window 2025-01..2026-09")
    record("energy_median_flux_core", round(e.flux_core.median()), "energy_ceiling.csv", "W/m2 over 0.5 km disk")
    record("energy_full_warming_core", round(e.full_warming_core.median(), 1), "energy_ceiling.csv", "lambda = 25")
    record("energy_dc_upper_bound", round(upper, 2), "warehouse_ols.csv", "max ci_hi of is_dc over specifications")
    record("energy_max_share_1km_lambda30", f"{max(0, upper) * 30 / e.flux_1km.median():.1%}",
           "energy_ceiling.csv + warehouse_ols.csv", "upper * 30 / median 1 km flux")


# --- figures ------------------------------------------------------------------------------

def figure_dlst_vs_dndvi(core: pd.DataFrame, units: pd.DataFrame) -> None:
    green = core[core.group == "greenfield"]
    warehouses = core[core.group == "warehouse"]
    fig, ax = plt.subplots(figsize=(6.4, 4.6))
    ax.axhline(0, color="#888", lw=0.7)
    for setting in SETTING_ORDER:
        d = green[green.setting == setting]
        ax.errorbar(d.dndvi, d.dlst, yerr=[d.dlst - d.ci_lo, d.ci_hi - d.dlst], fmt="o", ms=6,
                    color=SETTING_COLOURS[setting], ecolor=SETTING_COLOURS[setting], elinewidth=0.8,
                    alpha=0.9, label=f"data center, {setting}")
        w = warehouses[warehouses.setting == setting]
        ax.scatter(w.dndvi, w.dlst, marker="^", s=36, facecolors="none", edgecolors=SETTING_COLOURS[setting],
                   label=f"warehouse, {setting}")
    ax.set_xlabel("Change in vegetation (dNDVI), core 0-0.5 km")
    ax.set_ylabel("Change in surface temperature (°C)\ncore minus 3.5-5 km ring")
    ax.legend(fontsize=7, frameon=False, ncol=2, loc="upper right")
    save_figure(fig, "fig2_dlst_vs_dndvi")


def figure_rings() -> None:
    rings = pd.read_csv(CENSUS / "rings_summary.csv").merge(
        pd.read_csv(CENSUS / "crosssite_core.csv")[["site_id", "group", "setting"]], on="site_id")
    rings = rings[rings.group == "greenfield"]
    mids = {0: 0.25, 1: 0.75, 2: 1.5, 3: 2.75}
    fig, ax = plt.subplots(figsize=(5.6, 4.0))
    ax.axhline(0, color="#888", lw=0.7)
    for setting in SETTING_ORDER:
        d = rings[rings.setting == setting].groupby("ring").dlst
        med, q1, q3 = d.median(), d.quantile(0.25), d.quantile(0.75)
        x = [mids[r] for r in med.index]
        ax.plot(x, med.values, "o-", color=SETTING_COLOURS[setting], label=f"{setting} (median)")
        ax.fill_between(x, q1.values, q3.values, color=SETTING_COLOURS[setting], alpha=0.15)
    ax.set_xlabel("Distance from site centre (km)")
    ax.set_ylabel("Change in surface temperature (°C)\nvs 3.5-5 km ring")
    ax.legend(frameon=False, fontsize=8)
    save_figure(fig, "fig5_ring_profiles")


def figure_marinoni() -> None:
    fig, axes = plt.subplots(1, 2, figsize=(9, 4), sharex=True, sharey=True)
    for ax, (sensor, file) in zip(axes, (("Terra", "marinoni_results.csv"), ("Aqua", "marinoni_results_aqua.csv"))):
        r = pd.read_csv(CENSUS / file)
        r = r[r.band == "day"]
        ax.axline((0, 0), slope=1, color="#888", lw=0.7)
        ax.scatter(r.placebo_mean, r.marinoni, s=22, color="#555", label="Marinoni metric")
        ax.scatter(r.placebo_ref_mean, r.referenced, s=22, color="#b02318", marker="s",
                   label="referenced to 10-20 km ring")
        ax.set_title(f"MODIS {sensor}, day", loc="left", fontsize=10)
        ax.set_xlabel("Placebo points, same metric (°C)")
    axes[0].set_ylabel("Data-center sites (°C)")
    axes[0].legend(frameon=False, fontsize=8)
    save_figure(fig, "fig3_marinoni_placebos")


def albers(lon, lat, lon0=-96.0, lat0=23.0, lat1=29.5, lat2=45.5):
    """Albers equal-area conic projection on a unit sphere (the usual map of the lower 48 states)."""
    lon, lat = np.radians(np.asarray(lon, dtype=float)), np.radians(np.asarray(lat, dtype=float))
    lon0, lat0, lat1, lat2 = map(np.radians, (lon0, lat0, lat1, lat2))
    n = (np.sin(lat1) + np.sin(lat2)) / 2
    c = np.cos(lat1) ** 2 + 2 * n * np.sin(lat1)
    rho0 = np.sqrt(c - 2 * n * np.sin(lat0)) / n
    rho = np.sqrt(c - 2 * n * np.sin(lat)) / n
    theta = n * (lon - lon0)
    return rho * np.sin(theta), rho0 - rho * np.cos(theta)


def figure_map(core: pd.DataFrame) -> None:
    states = json.loads((ROOT / "data" / "basemap" / "ne_110m_admin_1_states_provinces.geojson").read_text())
    sites = pd.read_csv(ROOT / "data" / "census" / "census_sites.csv")[["site_id", "lat", "lon"]]
    d = core[core.group.isin(["greenfield", "conversion"])].merge(sites, on="site_id")
    fig, ax = plt.subplots(figsize=(8, 5))
    for feature in states["features"]:
        if feature["properties"]["name"] in ("Alaska", "Hawaii"):
            continue
        geometry = feature["geometry"]
        polygons = [geometry["coordinates"]] if geometry["type"] == "Polygon" else geometry["coordinates"]
        for polygon in polygons:
            ring = np.array(polygon[0])
            x, y = albers(ring[:, 0], ring[:, 1])
            ax.fill(x, y, facecolor="#f2f2f2", edgecolor="#9a9a9a", linewidth=0.5)
    lim = np.ceil(np.nanmax(np.abs(d.dlst)))
    for group, marker in (("greenfield", "o"), ("conversion", "s")):
        g = d[d.group == group].sort_values("dlst", key=np.abs)        # strongest changes drawn on top
        x, y = albers(g.lon, g.lat)
        sc = ax.scatter(x, y, c=g.dlst, cmap="RdBu_r", vmin=-lim, vmax=lim, s=70, marker=marker,
                        edgecolors="#222", linewidths=0.6, label=f"{group} ({len(g)})", zorder=3)
    fig.colorbar(sc, ax=ax, shrink=0.75, label="Core change in surface temperature (°C)")
    ax.set_aspect("equal")
    ax.axis("off")
    ax.legend(loc="lower left", frameon=False, fontsize=8)
    save_figure(fig, "fig1_site_map")


if __name__ == "__main__":
    PAPER.mkdir(parents=True, exist_ok=True)
    core = load_core()
    units = greenfield_units(core)
    table_sites(core)
    table_settings(units)
    table_models()
    table_marinoni()
    table_cooling()
    table_night()
    table_energy()
    figure_map(core)
    figure_dlst_vs_dndvi(core, units)
    figure_marinoni()
    figure_rings()
    pd.DataFrame(LEDGER).to_csv(PAPER / "numbers_ledger.csv", index=False)
    print(f"wrote {len(list(PAPER.glob('*.md')))} tables, {len(list(PAPER.glob('*.png')))} figures and "
          f"{len(LEDGER)} ledger rows to {PAPER}")
