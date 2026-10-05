"""Distance and campus-clustering helpers."""

import math

import pandas as pd

EARTH_RADIUS_M = 6_371_000.0


def haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance in metres."""
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi, dlam = phi2 - phi1, math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    return 2 * EARTH_RADIUS_M * math.asin(math.sqrt(a))


def cluster_sites(df: pd.DataFrame, radius_m: float = 1000) -> pd.DataFrame:
    """Add ``cluster_id``: campuses linked by any chain of pairs closer than ``radius_m``."""
    parent = list(range(len(df)))

    def root(i: int) -> int:
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    lats, lons = df["lat"].to_list(), df["lon"].to_list()
    for i in range(len(df)):
        for j in range(i + 1, len(df)):
            if haversine_m(lats[i], lons[i], lats[j], lons[j]) < radius_m:
                parent[root(j)] = root(i)

    roots = [root(i) for i in range(len(df))]
    ids = {r: k for k, r in enumerate(dict.fromkeys(roots))}
    return df.assign(cluster_id=[ids[r] for r in roots])
