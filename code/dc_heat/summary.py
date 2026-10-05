"""Per-site ring summary: the numbers reported for every site in the census."""

import numpy as np
import pandas as pd

from dc_heat import stats


def _per_ring_change(scenes: pd.DataFrame, column: str, base_years, op_years) -> dict[int, float]:
    """Season-matched before/after change of ``column`` within each ring (not far-referenced)."""
    if column not in scenes.columns:
        return {}
    per_ring = scenes.groupby(["date", "ring"], as_index=False)[column].mean().rename(columns={column: "v"})
    per_ring = stats.month_demean(per_ring.dropna(subset=["v"]), col="v")
    changes = {}
    for ring, values in per_ring.groupby("ring"):
        try:
            changes[int(ring)] = stats.before_after(values, base_years, op_years, col="v_prime")
        except ValueError:
            changes[int(ring)] = np.nan
    return changes


def _raw_mean_change(scenes: pd.DataFrame, column: str, ring: int, base_years, op_years) -> float:
    if column not in scenes.columns:
        return np.nan
    values = scenes[scenes["ring"] == ring]
    years = values["date"].dt.year
    return float(values.loc[years.isin(op_years), column].mean() - values.loc[years.isin(base_years), column].mean())


def summarize_site(scenes: pd.DataFrame, base_years, op_years, far_ring: int = 4) -> pd.DataFrame:
    """One row per inner ring: LST change vs. the far ring with CIs, plus NDVI, albedo, emissivity."""
    contrast = stats.month_demean(stats.within_scene_contrast(scenes, far_ring=far_ring))
    dndvi = _per_ring_change(scenes, "ndvi", base_years, op_years)
    dalbedo = _per_ring_change(scenes, "albedo", base_years, op_years)
    demis_core = _raw_mean_change(scenes, "emis", 0, base_years, op_years)
    demis_far = _raw_mean_change(scenes, "emis", far_ring, base_years, op_years)

    rows = []
    for ring, ring_df in contrast.groupby("ring"):
        years = ring_df["date"].dt.year
        base = ring_df.loc[years.isin(base_years), "c_prime"].to_numpy()
        op = ring_df.loc[years.isin(op_years), "c_prime"].to_numpy()
        if base.size < 2 or op.size < 2:
            continue
        ci_lo, ci_hi = stats.bootstrap_ci(base, op)
        block_lo, block_hi = stats.year_block_bootstrap_ci(ring_df, base_years, op_years)
        rows.append({
            "ring": int(ring),
            "dlst": stats.before_after(ring_df, base_years, op_years),
            "ci_lo": ci_lo, "ci_hi": ci_hi, "ci_lo_block": block_lo, "ci_hi_block": block_hi,
            "p": stats.welch_p(base, op), "mde": stats.mde(ci_lo, ci_hi),
            "n_base": int(base.size), "n_op": int(op.size),
            "dlst_raw": stats.before_after(ring_df, base_years, op_years, col="c"),
            "dndvi": dndvi.get(int(ring), np.nan), "dalbedo": dalbedo.get(int(ring), np.nan),
            "demis_core": demis_core, "demis_far": demis_far,
        })
    return pd.DataFrame(rows)
