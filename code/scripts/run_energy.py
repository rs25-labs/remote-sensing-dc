"""Phase 7b: energy-balance ceiling on how much of the data centers' heat can reach the surface.

For each census site with Epoch power data: facility power in the after window (2025-2026), the heat
flux it implies over the 0-0.5 km core and over a 1 km disk, and the surface warming that flux would
cause if it all entered the surface. The data center vs warehouse comparison bounds the observed extra
warming; the ratio caps the fraction of the heat that can be reaching the surface.
"""

from pathlib import Path

import numpy as np
import pandas as pd

from dcheat import energy

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs" / "census"
COUPLING = (15.0, 25.0, 30.0)     # W m^-2 K^-1: low, central, high


if __name__ == "__main__":
    sites = pd.read_csv(ROOT / "data" / "census" / "census_sites.csv")
    sites = sites[(sites.role == "census") & (sites.group == "greenfield")]
    timelines = pd.read_csv(ROOT / "data" / "census" / "epoch_raw" / "data_center_timelines.csv",
                            parse_dates=["Date"])

    rows = []
    for s in sites.itertuples():
        # Epoch also lists planned future records, so stop at the end of the observed after window
        power = energy.after_window_power(timelines[timelines["Data center"] == s.name], "2025-01-01", "2026-09-30")
        if np.isnan(power):
            continue
        core, wide = energy.heat_flux(power, 500), energy.heat_flux(power, 1000)
        rows.append({"site_id": s.site_id, "name": s.name, "power_mw": power, "flux_core": core, "flux_1km": wide,
                     "full_warming_core": energy.full_coupling_warming(core, COUPLING[1]),
                     "full_warming_1km": energy.full_coupling_warming(wide, COUPLING[1])})
    table = pd.DataFrame(rows)
    table.to_csv(OUT / "energy_ceiling.csv", index=False)
    with pd.option_context("display.width", 200):
        print(table.sort_values("power_mw", ascending=False).to_string(index=False, float_format=lambda v: f"{v:.1f}"))

    ols = pd.read_csv(OUT / "warehouse_ols.csv")
    upper = ols.loc[ols.term == "is_dc", "ci_hi"].max()            # most permissive specification
    print(f"\n{len(table)} sites with Epoch power; median after-window power {table.power_mw.median():.0f} MW")
    print(f"median heat flux: {table.flux_core.median():.0f} W/m2 over the core, {table.flux_1km.median():.0f} W/m2 over 1 km")
    print(f"if all of it entered the surface: core warming {table.full_warming_core.median():.1f} K "
          f"(range over sites {table.full_warming_core.min():.1f}-{table.full_warming_core.max():.1f}) at lambda = {COUPLING[1]:.0f}")
    print(f"upper bound on extra warming at data centers vs warehouses (most permissive model): {upper:+.2f} K")
    for area, col in (("core", "flux_core"), ("1 km disk", "flux_1km")):
        fractions = [energy.max_coupled_fraction(upper, table[col].median(), lam) for lam in COUPLING]
        print(f"max share of heat reaching the surface ({area}): " +
              ", ".join(f"{f:.1%} at lambda {lam:.0f}" for f, lam in zip(fractions, COUPLING)))
