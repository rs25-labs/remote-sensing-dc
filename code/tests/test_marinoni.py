import numpy as np
import pandas as pd
import pytest

from dcheat import marinoni

MONTHS = pd.date_range("2004-01-01", "2026-08-01", freq="MS")
OP_START = pd.Timestamp("2020-06-15")


def _series(values):
    return pd.Series(values, index=MONTHS)


def _seasonal():
    return 8 * np.sin(2 * np.pi * (MONTHS.month - 1) / 12)


# --- deseasonalize -------------------------------------------------------------------------

def test_deseasonalize_removes_the_mean_annual_cycle():
    out = marinoni.deseasonalize(_series(20 + _seasonal()))
    assert np.allclose(out, 0.0)


# --- marinoni_metric ---------------------------------------------------------------------------

def test_step_at_operation_start_is_recovered():
    step = np.where(MONTHS >= "2020-06-01", 2.0, 0.0)
    assert marinoni.marinoni_metric(_series(20 + _seasonal() + step), OP_START) == pytest.approx(2.0, abs=0.05)


def test_regional_trend_leaks_into_the_metric():
    years = (MONTHS - MONTHS[0]).days / 365.25
    trend = 0.05 * years                      # 0.05 °C per year, no data center at all
    metric = marinoni.marinoni_metric(_series(20 + _seasonal() + trend), OP_START)
    # before window centre is 30.5 months before start, after window centre 5.5 months after: 36 months apart
    assert metric == pytest.approx(0.05 * 3.0, abs=0.01)


def test_metric_is_nan_when_the_before_window_is_mostly_missing():
    values = _series(20 + _seasonal())
    values[(MONTHS >= "2015-06-01") & (MONTHS < "2019-06-01")] = np.nan
    assert np.isnan(marinoni.marinoni_metric(values, OP_START))


# --- referenced_metric -----------------------------------------------------------------------------

def test_background_reference_cancels_a_shared_trend():
    years = (MONTHS - MONTHS[0]).days / 365.25
    shared = 20 + _seasonal() + 0.05 * years
    assert marinoni.referenced_metric(_series(shared + 1.0), _series(shared), OP_START) == pytest.approx(0.0, abs=1e-9)


def test_background_reference_keeps_a_local_step():
    years = (MONTHS - MONTHS[0]).days / 365.25
    shared = 20 + _seasonal() + 0.05 * years
    step = np.where(MONTHS >= "2020-06-01", 1.5, 0.0)
    assert marinoni.referenced_metric(_series(shared + step), _series(shared), OP_START) == pytest.approx(1.5, abs=0.05)


# --- placebo selection ----------------------------------------------------------------------------

def _candidates():
    return pd.DataFrame({
        "site_id": ["S"] * 6,
        "point_id": [f"S-p{i}" for i in range(6)],
        "lat": [33.0, 33.3, 33.6, 33.0, 33.0, 33.2],
        "lon": [-110.6, -110.6, -110.6, -110.2, -111.0, -111.4],
        "cover": ["grass_shrub", "grass_shrub", "crop", "grass_shrub", "grass_shrub", "grass_shrub"],
    })


def test_placebos_match_cover_and_stay_away_from_every_data_center():
    sites = pd.DataFrame({"site_id": ["S", "T"], "lat": [33.0, 33.05], "lon": [-111.0, -111.0],
                          "cover": ["grass_shrub", "crop"]})
    out = marinoni.select_placebos(_candidates(), sites, n=10, min_km=10)
    chosen = set(out.point_id)
    assert "S-p2" not in chosen                 # wrong cover
    assert "S-p4" not in chosen                 # on top of site S
    assert {"S-p0", "S-p1", "S-p3", "S-p5"} <= chosen


def test_placebos_are_capped_at_n_per_site():
    sites = pd.DataFrame({"site_id": ["S"], "lat": [33.0], "lon": [-111.0], "cover": ["grass_shrub"]})
    assert len(marinoni.select_placebos(_candidates(), sites, n=2, min_km=10)) == 2


# --- operation month for the metric ----------------------------------------------------------

def test_operation_month_uses_the_recorded_date_when_present():
    assert marinoni.operation_month(pd.Timestamp("2024-04-20"), 2021) == (pd.Timestamp("2024-04-01"), "recorded")


def test_operation_month_is_estimated_from_construction_when_missing():
    month, source = marinoni.operation_month(pd.NaT, 2018, gap_years=2.25)
    assert (month, source) == (pd.Timestamp("2020-10-01"), "estimated")


# --- metric_table (the whole 6c calculation) -------------------------------------------------

def _modis_long(step_sites=("A",)):
    years = (MONTHS - MONTHS[0]).days / 365.25
    rows = []
    for point_id, site_id in (("A", "A"), ("A-P00", "A"), ("A-P01", "A")):
        for zone in ("disk", "annulus"):
            step = np.where((MONTHS >= "2022-01-01") & (point_id in step_sites) & (zone == "disk"), 1.5, 0.0)
            values = 20 + _seasonal() + 0.05 * years + step
            rows += [{"point_id": point_id, "site_id": site_id, "zone": zone, "month": m, "day": v, "night": v - 10}
                     for m, v in zip(MONTHS, values)]
    return pd.DataFrame(rows)


def test_metric_table_separates_step_trend_and_placebos():
    sites = pd.DataFrame({"site_id": ["A"], "name": ["Site A"], "group": ["greenfield"],
                          "operation_start": [pd.Timestamp("2022-01-10")]})
    placebos = pd.DataFrame({"site_id": ["A", "A"], "point_id": ["A-P00", "A-P01"]})
    out = marinoni.metric_table(_modis_long(), sites, placebos, {"A": 2020}).set_index("band")
    assert out.loc["day", "marinoni"] == pytest.approx(1.65, abs=0.02)
    assert out.loc["day", "placebo_mean"] == pytest.approx(0.15, abs=0.02)
    assert out.loc["day", "referenced"] == pytest.approx(1.50, abs=0.02)
    assert out.loc["night", "placebo_ref_mean"] == pytest.approx(0.0, abs=1e-9)
    assert out.loc["day", "n_placebo"] == 2
    assert out.loc["day", "op_source"] == "recorded"
