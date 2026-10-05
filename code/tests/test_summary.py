from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from dc_heat import summary

SOCIAL_CIRCLE = Path(__file__).resolve().parents[2] / "outputs" / "census" / "rings_scenes_social_circle.csv"


def _synthetic(step=2.0, ndvi_drop=0.3, seed=0):
    """Core ring warms by ``step`` and loses ``ndvi_drop`` greenness after 2020; far ring unchanged."""
    rng = np.random.default_rng(seed)
    rows = []
    for year in range(2016, 2026):
        for month in range(1, 13):
            date = pd.Timestamp(year=year, month=month, day=15)
            after = year >= 2023
            for ring in range(5):
                lst = 25 + 5 * np.sin(month / 12 * 2 * np.pi) + rng.normal(0, 0.3)
                ndvi = 0.6
                if ring == 0 and after:
                    lst, ndvi = lst + step, ndvi - ndvi_drop
                rows.append((date, ring, lst, ndvi, 0.97, 0.15))
    return pd.DataFrame(rows, columns=["date", "ring", "lst_c", "ndvi", "emis", "albedo"])


def test_summary_has_one_row_per_inner_ring_with_all_columns():
    out = summary.summarize_site(_synthetic(), [2016, 2017, 2018], [2023, 2024, 2025])
    assert list(out["ring"]) == [0, 1, 2, 3]
    for col in ["dlst", "ci_lo", "ci_hi", "ci_lo_block", "ci_hi_block", "p", "mde", "n_base", "n_op",
                "dlst_raw", "dndvi", "dalbedo", "demis_core", "demis_far"]:
        assert col in out.columns


def test_summary_recovers_core_step_and_leaves_outer_rings_near_zero():
    out = summary.summarize_site(_synthetic(step=2.0), [2016, 2017, 2018], [2023, 2024, 2025]).set_index("ring")
    assert out.loc[0, "dlst"] == pytest.approx(2.0, abs=0.1)
    assert out.loc[0, "ci_lo"] < 2.0 < out.loc[0, "ci_hi"]
    assert abs(out.loc[1, "dlst"]) < 0.15


def test_ndvi_change_is_per_ring_not_far_referenced():
    out = summary.summarize_site(_synthetic(ndvi_drop=0.3), [2016, 2017, 2018], [2023, 2024, 2025]).set_index("ring")
    assert out.loc[0, "dndvi"] == pytest.approx(-0.3, abs=1e-9)
    assert out.loc[1, "dndvi"] == pytest.approx(0.0, abs=1e-9)


def test_missing_albedo_column_gives_nan_not_an_error():
    scenes = _synthetic().drop(columns="albedo")
    out = summary.summarize_site(scenes, [2016, 2017, 2018], [2023, 2024, 2025])
    assert out["dalbedo"].isna().all()


@pytest.mark.skipif(not SOCIAL_CIRCLE.exists(), reason="Social Circle export not present")
def test_summary_reproduces_social_circle_paper_values():
    scenes = pd.read_csv(SOCIAL_CIRCLE, parse_dates=["date"])
    out = summary.summarize_site(scenes, list(range(2013, 2018)), list(range(2023, 2026))).set_index("ring")
    assert out.loc[0, "dlst"] == pytest.approx(4.75, abs=0.01)
    assert out.loc[1, "dlst"] == pytest.approx(2.28, abs=0.01)
    assert out.loc[3, "p"] == pytest.approx(0.59, abs=0.01)
    assert out.loc[0, "dndvi"] == pytest.approx(-0.285, abs=0.002)
    assert out.loc[0, "demis_core"] == pytest.approx(-0.0022, abs=0.0003)
