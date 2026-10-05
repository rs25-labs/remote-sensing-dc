import pandas as pd

from dcheat import windows


def _scenes(core_ndvi_by_year, core_albedo_by_year=None, far_ndvi=0.6, far_albedo=0.15, per_year=6):
    """Synthetic ring-0 and ring-4 scenes; the far ring stays constant."""
    rows = []
    for year, ndvi in core_ndvi_by_year.items():
        albedo = (core_albedo_by_year or {}).get(year, far_albedo)
        for k in range(per_year):
            date = pd.Timestamp(year=year, month=2 + 2 * k, day=10)
            rows.append((date, 0, ndvi, albedo))
            rows.append((date, 4, far_ndvi, far_albedo))
    return pd.DataFrame(rows, columns=["date", "ring", "ndvi", "albedo"])


# --- detect_construction_year ---------------------------------------------------

def test_detects_first_year_of_persistent_vegetation_loss():
    ndvi = {y: 0.6 for y in range(2013, 2019)} | {2019: 0.45, 2020: 0.30, 2021: 0.25, 2022: 0.25}
    assert windows.detect_construction_year(_scenes(ndvi)) == 2019


def test_ignores_a_single_anomalous_year():
    ndvi = {y: 0.6 for y in range(2013, 2023)} | {2017: 0.45}
    assert windows.detect_construction_year(_scenes(ndvi)) is None


def test_detects_brightening_when_vegetation_barely_changes():
    ndvi = {y: 0.15 for y in range(2013, 2024)}  # desert
    albedo = {y: 0.20 for y in range(2013, 2021)} | {2021: 0.25, 2022: 0.27, 2023: 0.27}
    assert windows.detect_construction_year(_scenes(ndvi, albedo)) == 2021


def test_works_without_an_albedo_column():
    ndvi = {y: 0.6 for y in range(2013, 2019)} | {2019: 0.4, 2020: 0.4}
    assert windows.detect_construction_year(_scenes(ndvi).drop(columns="albedo")) == 2019


def test_change_in_the_final_year_counts_without_a_following_year():
    ndvi = {y: 0.6 for y in range(2013, 2026)} | {2026: 0.3}
    assert windows.detect_construction_year(_scenes(ndvi)) == 2026


# --- census_windows ------------------------------------------------------------------

def test_greenfield_uses_five_years_before_construction_and_latest_years_after():
    w = windows.census_windows("greenfield", construction_year=2021)
    assert w["base_years"] == [2016, 2017, 2018, 2019, 2020]
    assert w["op_years"] == [2025, 2026]
    assert w["reason"] == ""


def test_greenfield_baseline_is_clipped_at_2013():
    w = windows.census_windows("greenfield", construction_year=2016)
    assert w["base_years"] == [2013, 2014, 2015]


def test_greenfield_with_too_short_baseline_is_flagged():
    w = windows.census_windows("greenfield", construction_year=2014)
    assert "baseline" in w["reason"]


def test_greenfield_without_construction_year_is_flagged():
    w = windows.census_windows("greenfield", construction_year=None)
    assert "construction year" in w["reason"]


def test_greenfield_built_in_the_after_window_is_flagged():
    w = windows.census_windows("greenfield", construction_year=2025)
    assert "after window" in w["reason"]


def test_conversion_after_window_starts_at_operation():
    w = windows.census_windows("conversion", construction_year=2024,
                               operation_start=pd.Timestamp("2024-08-11"))
    assert w["base_years"] == [2019, 2020, 2021, 2022, 2023]
    assert w["op_years"] == [2025, 2026]


def test_conversion_operating_by_march_counts_that_year():
    w = windows.census_windows("conversion", construction_year=2023,
                               operation_start=pd.Timestamp("2024-01-31"))
    assert w["op_years"] == [2024, 2025, 2026]


def test_conversion_without_operation_date_is_flagged():
    w = windows.census_windows("conversion", construction_year=2023, operation_start=None)
    assert "operation" in w["reason"]


# --- resolve_construction_year ----------------------------------------------------------

def test_registry_year_always_wins():
    assert windows.resolve_construction_year(2021, detected=2017, announced=2016) == (2021, "registry")


def test_earliest_of_detected_and_announced_is_used():
    assert windows.resolve_construction_year(None, detected=2019, announced=2016) == (2016, "announced")
    assert windows.resolve_construction_year(None, detected=2017, announced=2022) == (2017, "detected")


def test_detected_alone_or_announced_alone():
    assert windows.resolve_construction_year(None, detected=2019, announced=None) == (2019, "detected")
    assert windows.resolve_construction_year(float("nan"), detected=None, announced=2018) == (2018, "announced")


def test_nothing_known_returns_none():
    assert windows.resolve_construction_year(None, detected=None, announced=float("nan")) == (None, "none")
