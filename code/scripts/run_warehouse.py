"""Phase 5: do data centers warm their surroundings more than large warehouses with the same land change?

Uses the census outputs (local copies in outputs/census/). Greenfield data centers are collapsed to
independent units as in run_crosssite.py; each warehouse is its own unit.
"""

from pathlib import Path

import pandas as pd

from dc_heat import crosssite

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs" / "census"
NEAR_KM = 5          # warehouses closer than this share background rings with their data center
WEAK_NDVI = -0.05    # warehouses with less vegetation loss than this may be misdated or pre-existing


def fmt(v: float) -> str:
    return f"{v:.2f}"


def model(units: pd.DataFrame, label: str, xs=("dndvi", "dalbedo", "aridity", "is_dc")) -> pd.DataFrame:
    xs = list(xs)
    fit = crosssite.ols_bootstrap(units, "dlst", xs)
    n_dc, n_wh = int(units.is_dc.sum()), int((~units.is_dc.astype(bool)).sum())
    print(f"\n{label}: dlst ~ {' + '.join(xs)}  "
          f"(n = {fit.attrs['n']}: {n_dc} data-center units, {n_wh} warehouses; R^2 = {fit.attrs['r2']:.2f})")
    print(fit.round(2).to_string())
    return fit


if __name__ == "__main__":
    rings = pd.read_csv(OUT / "rings_summary.csv")
    windows_used = pd.read_csv(OUT / "census_windows.csv")
    labels = pd.read_csv(OUT / "site_labels.csv").fillna(0.0)
    sites = pd.read_csv(ROOT / "data" / "census" / "census_sites.csv")

    years = dict(zip(windows_used.site_id, windows_used.construction_year))
    cover = crosssite.precon_cover(labels[labels.site_id.isin(years)], years)
    core = (rings[rings.ring == 0]
            .merge(sites[["site_id", "name", "group", "cluster_id", "nearest_km", "note"]], on="site_id")
            .merge(cover, on="site_id"))

    values = ["dlst", "ci_lo", "ci_hi", "dndvi", "dalbedo", "aridity"]
    green = core[core.group == "greenfield"]
    dc_units = crosssite.collapse_clusters(green[["site_id", "cluster_id", "setting"] + values], values)
    dc_units["is_dc"] = 1.0
    warehouses = core[core.group == "warehouse"].copy()
    warehouses["paired_dc"] = warehouses.note.str.extract(r"paired with (\S+?);")[0]
    warehouses["is_dc"] = 0.0
    warehouses["unit"] = warehouses.site_id

    # 1. Each warehouse next to its own data center
    pairs = warehouses.merge(core[["site_id", "name", "setting", "dlst", "dndvi", "dalbedo"]],
                             left_on="paired_dc", right_on="site_id", suffixes=("", "_dc"))
    pairs["dc_minus_wh"] = pairs.dlst_dc - pairs.dlst
    cols = ["site_id", "name_dc", "setting", "nearest_km", "dlst_dc", "dlst", "dc_minus_wh",
            "dndvi_dc", "dndvi", "dalbedo_dc", "dalbedo"]
    with pd.option_context("display.width", 250, "display.max_colwidth", 30):
        print("Warehouse vs its own data center (core 0-0.5 km change, °C):")
        print(pairs.sort_values(["setting", "paired_dc"])[cols].to_string(index=False, float_format=fmt))
    pairs[cols].to_csv(OUT / "warehouse_pairs.csv", index=False)

    # 2. Cooling vs warming by setting
    both = pd.concat([dc_units.assign(kind="data center"), warehouses.assign(kind="warehouse")],
                     ignore_index=True)
    both["cools"] = both.dlst < 0
    print("\nCore change by setting:")
    print(both.groupby(["setting", "kind"]).agg(n=("dlst", "size"), cool=("cools", "sum"),
                                                median=("dlst", "median"), mean=("dlst", "mean"),
                                                median_dndvi=("dndvi", "median"))
          .round(2).to_string())

    # 3. Same land change, is there a data-center excess?
    keep = ["unit", "setting", "nearest_km", "is_dc"] + values
    pooled = pd.concat([dc_units[keep[:2] + keep[3:]], warehouses[keep]], ignore_index=True)
    fits = {"all": model(pooled, "All warehouses")}
    far = pooled[(pooled.is_dc == 1) | (pooled.nearest_km >= NEAR_KM)]
    fits["far"] = model(far, f"Warehouses at least {NEAR_KM} km from any data center")
    strong = far[(far.is_dc == 1) | (far.dndvi <= WEAK_NDVI)]
    fits["far_strong"] = model(strong, f"... and with clear vegetation loss (dNDVI <= {WEAK_NDVI})")
    fits["no_albedo"] = model(pooled, "All warehouses, without albedo", xs=("dndvi", "aridity", "is_dc"))
    pd.concat(fits, names=["sample", "term"]).to_csv(OUT / "warehouse_ols.csv")
