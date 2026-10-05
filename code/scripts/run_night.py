"""Phase 7a: night ECOSTRESS change at the four paper sites, rings (main) and point control (check).

Reads outputs/night/night_scenes_*.csv (from notebooks/dc_night.ipynb). Night = 21:00-05:00 local solar
time; one tile per overpass. Each scene's contrast (ring minus 3.5-5 km ring, or campus point minus
control point) has its calendar-month mean and night-hour-bin mean removed before the before/after
comparison, so differences in season and hour between periods do not masquerade as change.
"""

import glob
from pathlib import Path

import numpy as np
import pandas as pd

from dcheat import night, stats

ROOT = Path(__file__).resolve().parents[2]
NIGHT = ROOT / "outputs" / "night"
MIN_VALID = 0.5
SEASONS = {"all": range(1, 13), "summer (Jun-Sep)": [6, 7, 8, 9], "cool (Oct-Mar)": [10, 11, 12, 1, 2, 3]}
# Paper windows (Table V) and census windows (5 years before construction, after = 2025-2026),
# both limited by ECOSTRESS starting in mid-2018.
WINDOWS = {
    "paper": {"MESA-META": ([2019, 2020, 2021], [2025]),
              "MESA-EDGECORE": ([2019, 2020, 2021], [2024, 2025]),
              "MIDLOTHIAN": ([2018], [2023, 2024, 2025]),
              "GALLATIN": ([2019, 2020, 2021], [2025, 2026])},
    "census": {"MESA-META": ([2018, 2019, 2020, 2021], [2025, 2026]),
               "MESA-EDGECORE": ([2018, 2019, 2020, 2021], [2025, 2026]),
               "MIDLOTHIAN": ([2018], [2025, 2026]),
               "GALLATIN": ([2018, 2019, 2020, 2021], [2025, 2026])},
}
PAPER_TABLE_V = {"MESA-META": 1.09, "MESA-EDGECORE": 0.87, "MIDLOTHIAN": 1.38, "GALLATIN": -0.98}


def demean(df: pd.DataFrame, col: str) -> pd.DataFrame:
    """Remove calendar-month means, then night-hour-bin means, of ``col`` within each series."""
    out = []
    for _, series in df.groupby("series"):
        series = stats.month_demean(series, col=col)
        series = stats.hour_demean(series, col=col + "_prime")
        out.append(series.rename(columns={col + "_prime_prime": "value"}))
    return pd.concat(out, ignore_index=True)


def ring_contrasts(scenes: pd.DataFrame, min_valid: float) -> pd.DataFrame:
    rows = []
    for ring in range(4):
        ok = (scenes[f"valid_ring{ring}"] >= min_valid) & (scenes["valid_ring4"] >= min_valid)
        part = scenes.loc[ok, ["site_id", "utc", "local_hour"]].copy()
        part["c"] = scenes.loc[ok, f"lst_ring{ring}"] - scenes.loc[ok, "lst_ring4"]
        part["ring"] = ring
        rows.append(part)
    out = pd.concat(rows).dropna(subset=["c"]).rename(columns={"utc": "date"})
    out["series"] = out.site_id + "/ring" + out.ring.astype(str)
    return out


def point_contrasts(scenes: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for point in ("verified", "paper"):
        part = scenes[["site_id", "utc", "local_hour"]].copy()
        part["c"] = scenes[f"lst_pt_{point}"] - scenes["lst_pt_control"]
        part["point"] = point
        rows.append(part)
    out = pd.concat(rows).dropna(subset=["c"]).rename(columns={"utc": "date"})
    out["series"] = out.site_id + "/" + out.point
    return out


def trim_outliers(df: pd.DataFrame, k: float = 5.0) -> pd.DataFrame:
    """Drop scenes more than k robust SDs from their series median (cloud edges the mask missed)."""
    med = df.groupby("series").c.transform("median")
    mad = df.groupby("series").c.transform(lambda x: (x - x.median()).abs().median()) * 1.4826
    return df[(df.c - med).abs() <= k * mad]


def summarize(values: pd.DataFrame, keys: list[str]) -> pd.DataFrame:
    rows = []
    for window, per_site in WINDOWS.items():
        for site_id, (base_years, op_years) in per_site.items():
            for season, months in SEASONS.items():
                site = values[(values.site_id == site_id) & values.date.dt.month.isin(months)]
                for key, d in site.groupby(keys):
                    years = d.date.dt.year
                    base = d.loc[years.isin(base_years), "value"].to_numpy()
                    op = d.loc[years.isin(op_years), "value"].to_numpy()
                    if base.size < 2 or op.size < 2:
                        continue
                    lo, hi = stats.bootstrap_ci(base, op)
                    blo, bhi = stats.year_block_bootstrap_ci(d, base_years, op_years, col="value")
                    rows.append({"window": window, "site_id": site_id, "season": season,
                                 **dict(zip(keys, key if isinstance(key, tuple) else (key,))),
                                 "change": op.mean() - base.mean(), "ci_lo": lo, "ci_hi": hi,
                                 "ci_lo_block": blo, "ci_hi_block": bhi, "p": stats.welch_p(base, op),
                                 "n_base": base.size, "n_op": op.size})
    return pd.DataFrame(rows)


def show(table: pd.DataFrame, title: str, cols: list[str]) -> None:
    print(f"\n{title}")
    with pd.option_context("display.width", 220):
        print(table[cols].to_string(index=False, float_format=lambda v: f"{v:+.2f}"))


if __name__ == "__main__":
    raw = pd.concat(pd.read_csv(f, parse_dates=["utc"]) for f in sorted(glob.glob(str(NIGHT / "night_scenes_*.csv"))))
    scenes = night.scene_table(raw)
    print("night overpasses (21-05 local, one tile per pass):", scenes.groupby("site_id").size().to_dict())

    rings = summarize(demean(ring_contrasts(scenes, MIN_VALID), "c"), ["ring"])
    rings.to_csv(NIGHT / "night_rings_summary.csv", index=False)
    points = summarize(demean(point_contrasts(scenes), "c"), ["point"])
    points.to_csv(NIGHT / "night_point_summary.csv", index=False)

    cols = ["site_id", "season", "change", "ci_lo", "ci_hi", "ci_lo_block", "ci_hi_block", "p", "n_base", "n_op"]
    show(rings[(rings.window == "census") & (rings.ring == 0)],
         "RINGS, core (0-0.5 km) vs 3.5-5 km, census windows:", cols)
    show(rings[(rings.window == "paper") & (rings.ring == 0)], "RINGS, core, paper windows:", cols)
    profile = rings[(rings.window == "census") & (rings.season == "all")].pivot(index="site_id", columns="ring",
                                                                                 values="change")
    print("\nRing profile, census windows, all seasons (°C; ring 0 = 0-0.5 km ... ring 3 = 2-3.5 km):")
    print(profile.round(2).to_string())

    paper_pts = points[(points.window == "paper") & (points.season == "all")].copy()
    paper_pts["table_v"] = paper_pts.site_id.map(PAPER_TABLE_V)
    show(paper_pts, "POINT CONTROL, paper windows, all seasons (compare with Table V):",
         ["site_id", "point", "table_v", "change", "ci_lo", "ci_hi", "p", "n_base", "n_op"])
    show(points[(points.window == "paper") & (points.point == "verified") & (points.season != "all")],
         "POINT CONTROL at verified point, paper windows, by season:", cols)

    print("\nRobustness, core ring, census windows, all seasons:")
    variants = {"main (valid >= 0.5)": demean(ring_contrasts(scenes, 0.5), "c"),
                "strict clouds (valid >= 0.8)": demean(ring_contrasts(scenes, 0.8), "c"),
                "outliers trimmed (5 robust SD)": demean(trim_outliers(ring_contrasts(scenes, 0.5)), "c")}
    for name, values in variants.items():
        table = summarize(values, ["ring"])
        table = table[(table.window == "census") & (table.ring == 0) & (table.season == "all")]
        print(f"  {name:32s} " + "  ".join(f"{r.site_id} {r.change:+.2f} [{r.ci_lo:+.2f},{r.ci_hi:+.2f}]"
                                           for r in table.itertuples()))

    # Timing probe: does the after-period core contrast fade from evening to pre-dawn?
    core = ring_contrasts(scenes, MIN_VALID)
    core = core[core.ring == 0]
    core = pd.concat(stats.month_demean(g, col="c") for _, g in core.groupby("series"))
    core["part"] = pd.cut((core.local_hour - 21) % 24, [0, 3, 5, 8], right=False,
                          labels=["evening 21-24", "midnight 0-2", "pre-dawn 2-5"])
    print("\nCore contrast by night hour (month-adjusted), base vs after, census windows:")
    for site_id, (base_years, op_years) in WINDOWS["census"].items():
        d = core[core.site_id == site_id]
        period = np.where(d.date.dt.year.isin(op_years), "after", np.where(d.date.dt.year.isin(base_years), "base", ""))
        table = d.assign(period=period)[period != ""].groupby(["part", "period"], observed=True).c_prime.agg(["mean", "count"])
        print(f"  {site_id}: " + "; ".join(f"{part} {per} {row['mean']:+.2f} (n={int(row['count'])})"
                                          for (part, per), row in table.iterrows()))
