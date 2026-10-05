"""Phase 6 (exploratory): does cooling type change the core temperature response?

Compares dry-cooled data centers (all heat leaves as warm air) with evaporatively cooled ones
(cooling towers or outside air with evaporative assist), on the raw core change and on the residual
after the land-change model (dNDVI + dalbedo + aridity, fitted on greenfield independent units).
"""

from pathlib import Path

import numpy as np
import pandas as pd

from dc_heat import crosssite

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs" / "census"
AFTER_START, AFTER_END = pd.Timestamp("2025-01-01"), pd.Timestamp("2026-09-30")
MIN_OPERATING = 0.5   # share of the after window the site must have been operating


def operating_share(start: pd.Timestamp) -> float:
    """Share of the after window from ``start`` onward; sites with no date were running before 2025."""
    if pd.isna(start) or start <= AFTER_START:
        return 1.0
    return max(0.0, (AFTER_END - start) / (AFTER_END - AFTER_START))


def compare(units: pd.DataFrame, label: str) -> list[dict]:
    known = units[units.cooling != "unknown"]
    dry = (known.cooling == "dry").to_numpy()
    print(f"\n{label}: {dry.sum()} dry vs {(~dry).sum()} evaporative")
    rows = []
    for col in ("dlst", "residual"):
        test = crosssite.permutation_test(known[col].to_numpy(), dry)
        print(f"  {col:8s} dry minus evaporative = {test['diff']:+.2f} °C   permutation p = {test['p']:.2f}")
        rows.append({"sample": label, "measure": col, "n_dry": int(dry.sum()),
                     "n_evaporative": int((~dry).sum()), **test})
    return rows


if __name__ == "__main__":
    rings = pd.read_csv(OUT / "rings_summary.csv")
    windows_used = pd.read_csv(OUT / "census_windows.csv")
    labels = pd.read_csv(OUT / "site_labels.csv").fillna(0.0)
    sites = pd.read_csv(ROOT / "data" / "census" / "census_sites.csv")
    cooling = pd.read_csv(ROOT / "data" / "census" / "cooling_labels.csv", parse_dates=["operating_from"])

    years = dict(zip(windows_used.site_id, windows_used.construction_year))
    cover = crosssite.precon_cover(labels[labels.site_id.isin(years)], years)
    core = (rings[rings.ring == 0]
            .merge(sites[["site_id", "group", "cluster_id"]], on="site_id")
            .merge(cover[["site_id", "setting", "aridity"]], on="site_id")
            .merge(cooling[["site_id", "name", "cooling", "basis", "operating_from"]], on="site_id"))
    core = core[core.group == "greenfield"]
    core["operating_share"] = core.operating_from.map(operating_share)
    # dry vs any evaporative; a cluster mixing the two would be ambiguous, so check
    core["cooling"] = core.cooling.replace({"cooling towers": "evaporative", "evaporative assist": "evaporative"})
    mixed = core[core.cooling != "unknown"].groupby("cluster_id").cooling.nunique()
    assert (mixed <= 1).all(), f"clusters mixing cooling types: {list(mixed[mixed > 1].index)}"

    values = ["dlst", "dndvi", "dalbedo", "aridity", "operating_share"]
    units = crosssite.collapse_clusters(
        core[["site_id", "cluster_id", "name", "setting", "cooling", "basis"] + values], values)
    fit = crosssite.ols_bootstrap(units, "dlst", ["dndvi", "dalbedo", "aridity"])
    design = np.column_stack([np.ones(len(units)), units[["dndvi", "dalbedo", "aridity"]]])
    units["residual"] = units.dlst - design @ fit.coef.to_numpy()

    cols = ["name", "setting", "cooling", "basis", "operating_share", "dlst", "residual", "dndvi"]
    with pd.option_context("display.width", 200, "display.max_colwidth", 40):
        print(units.sort_values(["cooling", "residual"])[cols].to_string(index=False, float_format=lambda v: f"{v:.2f}"))
    units[["unit"] + cols].to_csv(OUT / "cooling_units.csv", index=False)

    rows = compare(units, "All labelled units")
    rows += compare(units[units.operating_share >= MIN_OPERATING],
                    f"Operating at least {MIN_OPERATING:.0%} of the after window")
    rows += compare(units[units.basis == "site"], "Site-specific labels only")
    rows += compare(units[units.setting == "humid"], "Humid sites only")
    pd.DataFrame(rows).to_csv(OUT / "cooling_tests.csv", index=False)
