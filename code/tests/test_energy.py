import numpy as np
import pandas as pd
import pytest

from dcheat import energy


def test_heat_flux_spreads_facility_power_over_a_disk():
    # 100 MW over a 500 m radius disk (785,398 m^2) is about 127 W/m^2
    assert energy.heat_flux(100, 500) == pytest.approx(127.32, abs=0.01)


def test_surface_warming_if_all_heat_entered_the_surface():
    # 127 W/m^2 against a 25 W m^-2 K^-1 coupling coefficient is about 5.1 K
    assert energy.full_coupling_warming(127.32, coupling=25) == pytest.approx(5.09, abs=0.01)


def test_max_coupled_fraction_from_an_upper_bound_on_observed_warming():
    # if at most 0.2 K of extra warming is allowed and full coupling would give 5 K, at most 4% couples
    assert energy.max_coupled_fraction(0.2, 125.0, coupling=25) == pytest.approx(0.04)


def test_max_coupled_fraction_is_zero_when_the_bound_is_negative():
    assert energy.max_coupled_fraction(-0.3, 125.0, coupling=25) == 0.0


def test_after_window_power_uses_mean_of_records_in_window_else_latest_before():
    timeline = pd.DataFrame({"Date": pd.to_datetime(["2023-01-01", "2025-03-01", "2026-03-01", "2027-01-01"]),
                             "Power (MW)": [50.0, 100.0, 200.0, 400.0]})
    assert energy.after_window_power(timeline, "2025-01-01", "2026-12-31") == pytest.approx(150.0)
    assert energy.after_window_power(timeline.iloc[:1], "2025-01-01", "2026-12-31") == pytest.approx(50.0)
    assert np.isnan(energy.after_window_power(timeline.iloc[3:], "2025-01-01", "2026-12-31"))
