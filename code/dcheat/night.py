"""Night ECOSTRESS sampling: ring means and the paper's point window, from one raster window."""

import numpy as np
import pandas as pd


def to_celsius(raw: np.ndarray) -> np.ndarray:
    """ECOSTRESS LST to °C; zero, negative and fill values become NaN (scaled Kelvin is unscaled)."""
    values = np.asarray(raw, dtype=float).copy()
    values[~np.isfinite(values) | (values <= 0)] = np.nan
    values = np.where(values > 1000, values * 0.02, values)
    return values - 273.15


def ring_means(values: np.ndarray, xs: np.ndarray, ys: np.ndarray, cx: float, cy: float,
               rings_km) -> list[dict]:
    """Mean of ``values`` (NaN = masked) in each annulus around (cx, cy), with its valid fraction.

    ``xs`` and ``ys`` are pixel-centre coordinates in metres (columns and rows of ``values``).
    """
    dist = np.hypot(*np.meshgrid(xs - cx, ys - cy))
    out = []
    for r0, r1 in rings_km:
        inside = (dist >= r0 * 1000) & (dist < r1 * 1000)
        ring_values = values[inside]
        valid = np.isfinite(ring_values)
        expected = np.pi * ((r1 * 1000) ** 2 - (r0 * 1000) ** 2) / abs((xs[1] - xs[0]) * (ys[1] - ys[0]))
        out.append({"mean": float(ring_values[valid].mean()) if valid.any() else np.nan,
                    "valid_frac": float(valid.sum() / expected)})
    return out


def point_mean(values: np.ndarray, xs: np.ndarray, ys: np.ndarray, x: float, y: float,
               half: int = 4, min_valid: float = 0.5) -> float:
    """Mean in a (2*half+1)-pixel square around the pixel nearest (x, y), as in the paper's ``_samp``."""
    col = int(np.abs(xs - x).argmin())
    row = int(np.abs(ys - y).argmin())
    window = values[max(0, row - half): row + half + 1, max(0, col - half): col + half + 1]
    if np.isfinite(window).sum() < min_valid * window.size:
        return np.nan
    return float(np.nanmean(window))


def local_solar_hour(utc: pd.Timestamp, lon: float) -> float:
    """Local mean solar time in hours (0-24) from a UTC timestamp and longitude."""
    hour = utc.hour + utc.minute / 60 + utc.second / 3600
    return (hour + lon / 15) % 24


def scene_table(raw: pd.DataFrame, night_hours=(21, 5)) -> pd.DataFrame:
    """One row per site and overpass from the long night CSV: ``lst_<zone>`` and ``valid_<zone>`` columns.

    Keeps passes whose local solar hour is within ``night_hours`` (start, end across midnight). When one
    pass appears in two overlapping tiles (start times within 10 minutes), keeps the tile with the most
    clear pixels in the core and far rings.
    """
    wide = raw.pivot_table(index=["site_id", "granule", "utc", "local_hour"], columns="zone",
                           values=["lst_c", "valid_frac"]).reset_index()
    wide.columns = [
        {"lst_c": "lst_", "valid_frac": "valid_"}.get(a, a) + b if b else a for a, b in wide.columns
    ]
    start, end = night_hours
    hour = wide["local_hour"]
    wide = wide[(hour >= start) | (hour < end)].copy()
    wide["coverage"] = wide.get("valid_ring0", 0).fillna(0) + wide.get("valid_ring4", 0).fillna(0)
    wide["pass_time"] = wide["utc"].dt.floor("10min")
    wide = wide.sort_values("coverage", ascending=False).drop_duplicates(["site_id", "pass_time"])
    return wide.drop(columns=["coverage", "pass_time"]).sort_values(["site_id", "utc"]).reset_index(drop=True)
