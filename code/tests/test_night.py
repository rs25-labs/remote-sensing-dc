import numpy as np
import pandas as pd
import pytest

from dc_heat import night


def _grid(n=201, step=70.0):
    """A square grid of pixel-centre coordinates (metres) centred on 0, like a UTM window."""
    half = (n - 1) / 2 * step
    xs = np.linspace(-half, half, n)
    ys = np.linspace(half, -half, n)          # rasters run north to south
    return xs, ys


# --- ring means --------------------------------------------------------------------------

def test_ring_means_follow_distance_from_centre():
    xs, ys = _grid()
    dist = np.hypot(*np.meshgrid(xs, ys))
    values = np.where(dist < 500, 30.0, 20.0)          # hot core, uniform background
    out = night.ring_means(values, xs, ys, 0.0, 0.0, [(0, 0.5), (0.5, 1.0), (3.5, 5.0)])
    assert out[0]["mean"] == pytest.approx(30.0)
    assert out[1]["mean"] == pytest.approx(20.0)
    assert out[2]["mean"] == pytest.approx(20.0)
    assert out[0]["valid_frac"] == pytest.approx(1.0, abs=0.02)   # pixel edges vs the ideal circle


def test_ring_means_ignore_masked_pixels_and_report_valid_fraction():
    xs, ys = _grid()
    values = np.full((len(ys), len(xs)), 25.0)
    values[:, : len(xs) // 2] = np.nan                 # west half under cloud
    out = night.ring_means(values, xs, ys, 0.0, 0.0, [(0, 0.5), (3.5, 5.0)])
    assert out[0]["mean"] == pytest.approx(25.0)
    assert out[1]["valid_frac"] == pytest.approx(0.5, abs=0.03)


def test_ring_outside_the_window_has_no_valid_pixels():
    xs, ys = _grid(n=41)                               # window only ~1.4 km across
    values = np.full((len(ys), len(xs)), 25.0)
    out = night.ring_means(values, xs, ys, 0.0, 0.0, [(3.5, 5.0)])
    assert np.isnan(out[0]["mean"])
    assert out[0]["valid_frac"] == 0.0


# --- point window (the paper's point-control sampler) ------------------------------------

def test_point_mean_averages_a_nine_by_nine_window():
    xs, ys = _grid(n=21)
    values = np.zeros((len(ys), len(xs)))
    values[6:15, 6:15] = 10.0                          # the 9x9 block around the centre pixel
    assert night.point_mean(values, xs, ys, 0.0, 0.0) == pytest.approx(10.0)


def test_point_mean_is_nan_when_window_mostly_masked():
    xs, ys = _grid(n=21)
    values = np.full((len(ys), len(xs)), np.nan)
    values[10, 10] = 5.0
    assert np.isnan(night.point_mean(values, xs, ys, 0.0, 0.0))


# --- local solar time -------------------------------------------------------------------

def test_local_solar_hour_shifts_utc_by_longitude():
    utc = pd.Timestamp("2025-01-15 08:30")
    assert night.local_solar_hour(utc, -105.0) == pytest.approx(1.5)
    assert night.local_solar_hour(pd.Timestamp("2025-01-15 02:00"), -90.0) == pytest.approx(20.0)


# --- to Kelvin/Celsius -------------------------------------------------------------------

def test_to_celsius_handles_kelvin_and_fill_values():
    raw = np.array([300.0, 0.0, -9999.0, 273.15])
    out = night.to_celsius(raw)
    assert out[0] == pytest.approx(26.85)
    assert np.isnan(out[1]) and np.isnan(out[2])
    assert out[3] == pytest.approx(0.0)


# --- scene table (long CSV -> one row per site and pass) ---------------------------------

def _long(rows):
    out = []
    for site, granule, utc, hour, values in rows:
        for zone, (lst, frac) in values.items():
            out.append({"site_id": site, "granule": granule, "utc": pd.Timestamp(utc), "local_hour": hour,
                        "zone": zone, "lst_c": lst, "valid_frac": frac})
    return pd.DataFrame(out)


def test_scene_table_keeps_best_covered_tile_of_a_pass_and_true_night_hours():
    good = {"ring0": (20.0, 0.9), "ring4": (18.0, 0.9), "pt_verified": (20.0, np.nan)}
    worse = {"ring0": (25.0, 0.6), "ring4": (18.0, 0.5), "pt_verified": (25.0, np.nan)}
    dusk = {"ring0": (40.0, 1.0), "ring4": (35.0, 1.0), "pt_verified": (40.0, np.nan)}
    raw = _long([("A", "tile1", "2025-07-01 08:00:00", 1.0, worse),
                 ("A", "tile2", "2025-07-01 08:00:30", 1.0, good),      # same pass, another tile
                 ("A", "tile3", "2025-07-02 01:00:00", 18.0, dusk)])    # 6 pm local: not night
    out = night.scene_table(raw)
    assert len(out) == 1
    assert out.iloc[0]["granule"] == "tile2"
    assert out.iloc[0]["lst_ring0"] == pytest.approx(20.0)
    assert out.iloc[0]["valid_ring4"] == pytest.approx(0.9)
