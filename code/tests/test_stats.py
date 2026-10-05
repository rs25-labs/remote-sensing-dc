from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from dcheat import stats


def _scenes(rows):
    df = pd.DataFrame(rows, columns=["date", "ring", "lst_c"])
    df["date"] = pd.to_datetime(df["date"])
    return df


# --- within_scene_contrast -------------------------------------------------

def test_contrast_is_ring_minus_far_ring_in_same_scene():
    scenes = _scenes([
        ("2019-06-01", 0, 30.0), ("2019-06-01", 4, 28.0),
        ("2019-07-01", 0, 35.0), ("2019-07-01", 4, 31.0),
    ])
    out = stats.within_scene_contrast(scenes)
    assert list(out["c"]) == [2.0, 4.0]
    assert set(out["ring"]) == {0}


def test_contrast_drops_scene_without_far_ring_instead_of_filling():
    scenes = _scenes([
        ("2019-06-01", 0, 30.0), ("2019-06-01", 4, 28.0),
        ("2019-07-01", 0, 35.0),  # far ring clouded out
    ])
    out = stats.within_scene_contrast(scenes)
    assert len(out) == 1
    assert out["date"].iloc[0] == pd.Timestamp("2019-06-01")


def test_contrast_keeps_every_inner_ring():
    scenes = _scenes([
        ("2019-06-01", 0, 30.0), ("2019-06-01", 1, 29.0), ("2019-06-01", 4, 28.0),
    ])
    out = stats.within_scene_contrast(scenes).sort_values("ring")
    assert list(out["ring"]) == [0, 1]
    assert list(out["c"]) == [2.0, 1.0]


# --- month_demean / hour_demean ---------------------------------------------

def test_month_demean_removes_a_pure_seasonal_cycle():
    dates = pd.date_range("2015-01-15", periods=48, freq="MS") + pd.Timedelta(days=14)
    seasonal = 3.0 * np.sin(2 * np.pi * dates.month / 12)
    df = pd.DataFrame({"date": dates, "ring": 0, "c": seasonal})
    out = stats.month_demean(df)
    assert np.allclose(out["c_prime"], 0.0)


def test_month_demean_is_computed_separately_per_ring():
    df = pd.DataFrame({
        "date": pd.to_datetime(["2019-06-01", "2020-06-01", "2019-06-01", "2020-06-01"]),
        "ring": [0, 0, 1, 1],
        "c": [1.0, 3.0, 10.0, 30.0],
    })
    out = stats.month_demean(df).sort_values(["ring", "date"])
    assert list(out["c_prime"]) == [-1.0, 1.0, -10.0, 10.0]


def test_hour_demean_removes_hour_bin_means_and_drops_daytime_hours():
    df = pd.DataFrame({
        "local_hour": [22, 23, 1, 1, 3, 4, 14],
        "d": [2.0, 4.0, 5.0, 7.0, 0.0, 2.0, 99.0],
    })
    out = stats.hour_demean(df, col="d")
    assert 14 not in set(out["local_hour"])
    # bins: evening 21-24 -> mean 3; midnight 0-2 -> mean 6; pre-dawn 2-5 -> mean 1
    assert sorted(out["d_prime"]) == [-1.0, -1.0, -1.0, 1.0, 1.0, 1.0]


# --- before_after -------------------------------------------------------------

def test_before_after_is_operational_mean_minus_baseline_mean():
    df = pd.DataFrame({
        "date": pd.to_datetime(["2019-05-01", "2020-05-01", "2025-05-01", "2025-08-01"]),
        "c_prime": [0.0, 0.0, 1.5, 1.5],
    })
    assert stats.before_after(df, [2019, 2020], [2025]) == pytest.approx(1.5)


def test_before_after_ignores_years_outside_both_periods():
    df = pd.DataFrame({
        "date": pd.to_datetime(["2019-05-01", "2022-05-01", "2025-05-01"]),
        "c_prime": [0.0, 50.0, 1.0],
    })
    assert stats.before_after(df, [2019], [2025]) == pytest.approx(1.0)


def test_before_after_raises_when_a_period_has_no_scenes():
    df = pd.DataFrame({"date": pd.to_datetime(["2019-05-01"]), "c_prime": [0.0]})
    with pytest.raises(ValueError, match="operational"):
        stats.before_after(df, [2019], [2025])


# --- bootstrap_ci / year_block_bootstrap_ci ----------------------------------

def test_bootstrap_ci_of_constant_groups_is_exact():
    lo, hi = stats.bootstrap_ci(np.zeros(50), np.ones(50))
    assert (lo, hi) == (1.0, 1.0)


def test_bootstrap_ci_contains_point_estimate_and_is_reproducible():
    rng = np.random.default_rng(1)
    base, op = rng.normal(0, 1, 80), rng.normal(0.7, 1, 60)
    lo, hi = stats.bootstrap_ci(base, op, seed=3)
    assert lo < op.mean() - base.mean() < hi
    assert stats.bootstrap_ci(base, op, seed=3) == (lo, hi)


def _year_clustered(base_year_means, op_year_means, per_year=30, spread=0.01, seed=0):
    rng = np.random.default_rng(seed)
    rows = []
    for year, mean in list(base_year_means.items()) + list(op_year_means.items()):
        for k in range(per_year):
            rows.append((pd.Timestamp(year=year, month=1 + k % 12, day=1), mean + rng.normal(0, spread)))
    return pd.DataFrame(rows, columns=["date", "c_prime"])


def test_year_block_ci_is_wider_than_scene_ci_when_years_differ():
    df = _year_clustered({2019: 0.0, 2020: 0.0, 2021: 3.0}, {2024: 1.0, 2025: 1.0})
    base = df[df.date.dt.year <= 2021]["c_prime"].to_numpy()
    op = df[df.date.dt.year >= 2024]["c_prime"].to_numpy()
    scene_lo, scene_hi = stats.bootstrap_ci(base, op)
    block_lo, block_hi = stats.year_block_bootstrap_ci(df, [2019, 2020, 2021], [2024, 2025])
    assert (block_hi - block_lo) > 3 * (scene_hi - scene_lo)


def test_year_block_ci_falls_back_to_scenes_for_a_single_year_period():
    df = _year_clustered({2019: 0.0, 2020: 0.0}, {2025: 1.0}, spread=0.5)
    lo, hi = stats.year_block_bootstrap_ci(df, [2019, 2020], [2025])
    # operational variability must still contribute: interval is not degenerate
    assert hi - lo > 0.05
    assert lo < 1.0 < hi


# --- welch_p / mde -----------------------------------------------------------------

def test_welch_p_identical_samples_is_not_significant():
    x = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
    assert stats.welch_p(x, x.copy()) > 0.99


def test_welch_p_separated_samples_is_significant():
    rng = np.random.default_rng(0)
    assert stats.welch_p(rng.normal(0, 1, 100), rng.normal(3, 1, 100)) < 0.001


def test_mde_matches_gallatin_value_in_draft():
    assert stats.mde(-0.24, 1.20) == pytest.approx(1.03, abs=0.01)


# --- regression against the published four-site numbers ---------------------------

SOCIAL_CIRCLE_SCENES = Path(__file__).resolve().parents[2] / "outputs" / "census" / "rings_scenes_social_circle.csv"


@pytest.mark.skipif(not SOCIAL_CIRCLE_SCENES.exists(), reason="export from notebook §10 not yet provided")
def test_reproduces_social_circle_core_result():
    scenes = pd.read_csv(SOCIAL_CIRCLE_SCENES, parse_dates=["date"])
    contrast = stats.month_demean(stats.within_scene_contrast(scenes))
    core = contrast[contrast["ring"] == 0]
    base_years, op_years = list(range(2013, 2018)), list(range(2023, 2026))
    assert stats.before_after(core, base_years, op_years) == pytest.approx(4.75, abs=0.01)
    in_base, in_op = core.date.dt.year.isin(base_years), core.date.dt.year.isin(op_years)
    lo, hi = stats.bootstrap_ci(core.loc[in_base, "c_prime"].to_numpy(), core.loc[in_op, "c_prime"].to_numpy())
    assert lo == pytest.approx(4.31, abs=0.02)
    assert hi == pytest.approx(5.19, abs=0.02)
