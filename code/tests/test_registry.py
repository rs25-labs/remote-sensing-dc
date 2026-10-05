import numpy as np
import pandas as pd
import pytest

from dcheat import registry


def _candidates(rows):
    cols = ["site_id", "group", "lat", "lon", "construction_start", "operation_start", "note"]
    df = pd.DataFrame(rows, columns=cols)
    for col in ("construction_start", "operation_start"):
        df[col] = pd.to_datetime(df[col])
    return df


def _one(**overrides):
    row = {"site_id": "S", "group": "greenfield", "lat": 33.0, "lon": -111.0,
           "construction_start": "2020-01-01", "operation_start": "2023-01-01", "note": ""}
    row.update(overrides)
    return _candidates([tuple(row.values())])


# --- eligibility --------------------------------------------------------------

def test_clean_greenfield_site_is_eligible():
    out = registry.eligibility(_one())
    assert bool(out["eligible"].iloc[0]) is True
    assert out["exclusion_reason"].iloc[0] == ""


def test_expansion_is_excluded():
    out = registry.eligibility(_one(group="expansion"))
    assert not out["eligible"].iloc[0]
    assert "expansion" in out["exclusion_reason"].iloc[0]


def test_manual_exclude_note_is_honoured():
    out = registry.eligibility(_one(note="EXCLUDE: next to a nuclear plant"))
    assert not out["eligible"].iloc[0]
    assert "nuclear" in out["exclusion_reason"].iloc[0]


def test_greenfield_started_before_2016_is_excluded_for_short_baseline():
    out = registry.eligibility(_one(construction_start="2015-06-01"))
    assert not out["eligible"].iloc[0]
    assert "baseline" in out["exclusion_reason"].iloc[0]


def test_conversion_is_not_held_to_the_land_baseline_rule():
    out = registry.eligibility(_one(group="conversion", construction_start="2015-06-01"))
    assert bool(out["eligible"].iloc[0]) is True


def test_site_operational_after_cutoff_is_excluded():
    out = registry.eligibility(_one(operation_start="2026-03-01"))
    assert not out["eligible"].iloc[0]
    assert "operational" in out["exclusion_reason"].iloc[0]


def test_missing_coordinates_and_dates_are_pending_not_excluded():
    out = registry.eligibility(_one(lat=np.nan, lon=np.nan, construction_start=None, operation_start=None))
    assert bool(out["eligible"].iloc[0]) is True
    assert out["needs"].iloc[0] == "coordinates;dates"


# --- neighbours and clusters ------------------------------------------------------

def _three_sites():
    # B is ~3.2 km east of A; C is ~20 km away; D has no coordinates yet
    return _candidates([
        ("A", "greenfield", 33.0, -111.0, "2020-01-01", "2023-01-01", ""),
        ("B", "expansion", 33.0, -110.9656, "2020-01-01", "2023-01-01", ""),
        ("C", "greenfield", 33.18, -111.0, "2020-01-01", "2023-01-01", ""),
        ("D", "greenfield", np.nan, np.nan, "2020-01-01", "2023-01-01", ""),
    ])


def test_neighbours_include_excluded_sites_within_radius():
    out = registry.flag_neighbours(_three_sites(), radius_m=5000).set_index("site_id")
    assert out.loc["A", "neighbours_5km"] == "B"
    assert out.loc["B", "neighbours_5km"] == "A"
    assert out.loc["C", "neighbours_5km"] == ""
    assert out.loc["A", "nearest_km"] == pytest.approx(3.2, abs=0.1)


def test_neighbours_skip_rows_without_coordinates():
    out = registry.flag_neighbours(_three_sites(), radius_m=5000).set_index("site_id")
    assert out.loc["D", "neighbours_5km"] == ""
    assert np.isnan(out.loc["D", "nearest_km"])


def test_clusters_assigned_only_where_coordinates_exist():
    out = registry.assign_clusters(_three_sites(), radius_m=1000).set_index("site_id")
    assert out.loc[["A", "B", "C"], "cluster_id"].nunique() == 3
    assert pd.isna(out.loc["D", "cluster_id"])

