"""Eligibility rules, neighbour flags and clustering for the census site registry."""

import numpy as np
import pandas as pd

from dc_heat import geo


def eligibility(cands: pd.DataFrame, min_construction: str = "2016-01-01",
                max_operation: str = "2025-12-31") -> pd.DataFrame:
    """Add ``eligible``, ``exclusion_reason`` (first rule that fails) and ``needs`` (pending checks).

    Missing coordinates or dates do not exclude a site; they are listed in ``needs`` for the
    imagery check.
    """
    min_construction, max_operation = pd.Timestamp(min_construction), pd.Timestamp(max_operation)
    reasons, needs = [], []
    for row in cands.itertuples():
        note = row.note if isinstance(row.note, str) else ""
        if note.startswith("EXCLUDE"):
            reason = note.removeprefix("EXCLUDE:").strip()
        elif row.group == "expansion":
            reason = "expansion of an existing campus: buildings already present in the baseline"
        elif row.group == "greenfield" and pd.notna(row.construction_start) and row.construction_start < min_construction:
            reason = f"construction began before {min_construction.year}: baseline shorter than 3 years"
        elif pd.notna(row.operation_start) and row.operation_start > max_operation:
            reason = f"not operational by {max_operation.date()}"
        else:
            reason = ""
        reasons.append(reason)
        pending = []
        if pd.isna(row.lat) or pd.isna(row.lon):
            pending.append("coordinates")
        if pd.isna(row.construction_start) or pd.isna(row.operation_start):
            pending.append("dates")
        needs.append(";".join(pending))
    return cands.assign(eligible=[r == "" for r in reasons], exclusion_reason=reasons, needs=needs)


def flag_neighbours(df: pd.DataFrame, radius_m: float = 5000) -> pd.DataFrame:
    """List every other candidate (any group) within ``radius_m``, and the nearest distance in km."""
    located = df.dropna(subset=["lat", "lon"])
    names, nearest = [], []
    for row in df.itertuples():
        if pd.isna(row.lat) or pd.isna(row.lon):
            names.append("")
            nearest.append(np.nan)
            continue
        distances = {
            other.site_id: geo.haversine_m(row.lat, row.lon, other.lat, other.lon)
            for other in located.itertuples() if other.site_id != row.site_id
        }
        names.append(";".join(site for site, d in sorted(distances.items(), key=lambda kv: kv[1]) if d < radius_m))
        nearest.append(min(distances.values()) / 1000 if distances else np.nan)
    return df.assign(neighbours_5km=names, nearest_km=nearest)


def assign_clusters(df: pd.DataFrame, radius_m: float = 1000) -> pd.DataFrame:
    """Add ``cluster_id`` for campuses within ``radius_m`` of each other; NaN without coordinates."""
    located = geo.cluster_sites(df.dropna(subset=["lat", "lon"]), radius_m=radius_m)
    return df.assign(cluster_id=located["cluster_id"].reindex(df.index))
