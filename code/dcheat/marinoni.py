"""Re-test of the Marinoni et al. (2026) "data heat island" estimator.

Their metric: monthly, deseasonalized LST over a 0-10 km disk; mean of the months after operations
start minus the mean of the previous k months (k = 60 in their main analysis), with no spatial
reference. We reproduce it, add a background-referenced version, and run it at placebo points.
"""

import numpy as np
import pandas as pd

from dcheat import geo


def deseasonalize(monthly: pd.Series) -> pd.Series:
    """Subtract each calendar month's mean over the whole record."""
    return monthly - monthly.groupby(monthly.index.month).transform("mean")


def marinoni_metric(monthly: pd.Series, op_start: pd.Timestamp, k: int = 60, after_months: int = 12,
                    min_coverage: float = 0.75) -> float:
    """Mean deseasonalized LST over ``after_months`` from the operation month, minus the mean over
    the ``k`` months before it. NaN when either window has less than ``min_coverage`` of its months."""
    anomalies = deseasonalize(monthly)
    start = pd.Timestamp(op_start).to_period("M").to_timestamp()
    before = anomalies[(anomalies.index >= start - pd.DateOffset(months=k)) & (anomalies.index < start)]
    after = anomalies[(anomalies.index >= start) & (anomalies.index < start + pd.DateOffset(months=after_months))]
    if before.notna().sum() < min_coverage * k or after.notna().sum() < min_coverage * after_months:
        return np.nan
    return float(after.mean() - before.mean())


def referenced_metric(site_monthly: pd.Series, background_monthly: pd.Series, op_start: pd.Timestamp,
                      **kwargs) -> float:
    """The same metric on (site minus background), which removes regional trends and weather."""
    return marinoni_metric(site_monthly - background_monthly, op_start, **kwargs)


def operation_month(operation_start, construction_year, gap_years: float = 2.25) -> tuple[pd.Timestamp, str]:
    """Month operations began: the recorded date when available, otherwise mid-construction-year
    plus the typical clearing-to-operation gap (Epoch AI median, 2.25 years)."""
    if operation_start is not None and not pd.isna(operation_start):
        return pd.Timestamp(operation_start).to_period("M").to_timestamp(), "recorded"
    start = pd.Timestamp(year=int(construction_year), month=7, day=1)
    return start + pd.DateOffset(months=round(gap_years * 12)), "estimated"


def select_placebos(candidates: pd.DataFrame, sites: pd.DataFrame, n: int = 10, min_km: float = 10) -> pd.DataFrame:
    """Up to ``n`` candidates per site whose land cover matches that site's pre-construction cover and
    which lie at least ``min_km`` from every data center. Candidate order is preserved."""
    cover = dict(zip(sites.site_id, sites.cover))
    site_points = list(zip(sites.lat, sites.lon))

    def far_enough(lat, lon):
        return all(geo.haversine_m(lat, lon, s_lat, s_lon) >= min_km * 1000 for s_lat, s_lon in site_points)

    keep = [
        row.Index for row in candidates.itertuples()
        if row.cover == cover.get(row.site_id) and far_enough(row.lat, row.lon)
    ]
    return candidates.loc[keep].groupby("site_id", sort=False).head(n).reset_index(drop=True)


def metric_table(modis: pd.DataFrame, sites: pd.DataFrame, placebos: pd.DataFrame,
                 construction_years: dict) -> pd.DataFrame:
    """Per site and band (day/night): the Marinoni metric, its background-referenced version, and
    the same two metrics averaged over the site's placebo points.

    ``modis`` is long format with point_id, zone (disk/annulus), month and one column per band.
    """
    modis = modis.assign(month=pd.to_datetime(modis["month"]))
    series = {key: g.set_index("month").sort_index() for key, g in modis.groupby(["point_id", "zone"])}

    def lst(point_id, zone, band):
        return series[(point_id, zone)][band] if (point_id, zone) in series else pd.Series(dtype=float)

    def mean_or_nan(values):
        values = np.asarray(values, dtype=float)
        return float(np.nanmean(values)) if np.isfinite(values).any() else np.nan

    rows = []
    for s in sites.itertuples():
        month, source = operation_month(s.operation_start, construction_years[s.site_id])
        placebo_ids = list(placebos.loc[placebos.site_id == s.site_id, "point_id"])
        for band in ("day", "night"):
            placebo = [marinoni_metric(lst(p, "disk", band), month) for p in placebo_ids]
            placebo_ref = [referenced_metric(lst(p, "disk", band), lst(p, "annulus", band), month) for p in placebo_ids]
            rows.append({
                "site_id": s.site_id, "name": s.name, "group": s.group, "band": band,
                "op_month": month.date(), "op_source": source,
                "marinoni": marinoni_metric(lst(s.site_id, "disk", band), month),
                "referenced": referenced_metric(lst(s.site_id, "disk", band), lst(s.site_id, "annulus", band), month),
                "placebo_mean": mean_or_nan(placebo),
                "placebo_sd": float(np.nanstd(placebo)) if np.isfinite(np.asarray(placebo, float)).any() else np.nan,
                "placebo_ref_mean": mean_or_nan(placebo_ref),
                "n_placebo": int(np.isfinite(np.asarray(placebo, float)).sum()),
            })
    return pd.DataFrame(rows)
