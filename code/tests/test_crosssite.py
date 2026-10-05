import numpy as np
import pandas as pd
import pytest

from dc_heat import crosssite


def _labels():
    rows = []
    for year in (2013, 2016, 2019, 2021):
        # Site A: forest until 2016, developed from 2019
        a = {"nlcd_41": 0.9, "nlcd_21": 0.1} if year <= 2016 else {"nlcd_41": 0.1, "nlcd_21": 0.9}
        rows.append({"site_id": "A", "nlcd_year": year, **a, "aridity": 1.2})
        # Site B: shrub desert throughout
        rows.append({"site_id": "B", "nlcd_year": year, "nlcd_52": 0.8, "nlcd_31": 0.2, "aridity": 0.2})
        # Site C: irrigated crop in a dry climate
        rows.append({"site_id": "C", "nlcd_year": year, "nlcd_82": 0.7, "nlcd_52": 0.3, "aridity": 0.3})
    return pd.DataFrame(rows).fillna(0.0)


# --- pre-construction cover ------------------------------------------------------------

def test_cover_uses_latest_nlcd_year_before_construction():
    out = crosssite.precon_cover(_labels(), {"A": 2019, "B": 2020, "C": 2018}).set_index("site_id")
    assert out.loc["A", "nlcd_year_used"] == 2016
    assert out.loc["A", "dominant_cover"] == "forest"
    assert out.loc["A", "frac_forest"] == pytest.approx(0.9)


def test_cover_falls_back_to_earliest_year_when_none_precedes_construction():
    out = crosssite.precon_cover(_labels(), {"A": 2010, "B": 2020, "C": 2018}).set_index("site_id")
    assert out.loc["A", "nlcd_year_used"] == 2013


def test_moisture_setting_separates_humid_dry_natural_and_dry_irrigated():
    out = crosssite.precon_cover(_labels(), {"A": 2019, "B": 2020, "C": 2018}).set_index("site_id")
    assert out.loc["A", "setting"] == "humid"
    assert out.loc["B", "setting"] == "dry natural"
    assert out.loc["C", "setting"] == "dry irrigated"


# --- collapsing overlapping campuses ------------------------------------------------------

def test_collapse_averages_sites_sharing_a_cluster():
    df = pd.DataFrame({"site_id": ["X", "Y", "Z"], "cluster_id": [1, 1, 2],
                       "dlst": [2.0, 4.0, -1.0], "aridity": [1.0, 1.0, 0.2]})
    out = crosssite.collapse_clusters(df, ["dlst", "aridity"]).set_index("unit")
    assert len(out) == 2
    assert out.loc["X+Y", "dlst"] == pytest.approx(3.0)
    assert out.loc["X+Y", "n_sites"] == 2


# --- sign test --------------------------------------------------------------------------------

def test_sign_table_and_fisher_p():
    df = pd.DataFrame({"dlst": [-2, -3, -1, 2, 3, 1, 2, 4], "dry": [True] * 3 + [False] * 5})
    result = crosssite.sign_test(df, "dry")
    assert result["table"] == {"dry_cool": 3, "dry_warm": 0, "other_cool": 0, "other_warm": 5}
    assert result["p"] < 0.05


# --- regression with unit bootstrap -------------------------------------------------------------

def test_ols_recovers_known_coefficients():
    rng = np.random.default_rng(0)
    df = pd.DataFrame({"dndvi": rng.uniform(-0.4, 0, 40), "dalbedo": rng.uniform(-0.02, 0.12, 40)})
    df["dlst"] = 0.5 - 10 * df.dndvi - 30 * df.dalbedo + rng.normal(0, 0.05, 40)
    fit = crosssite.ols_bootstrap(df, "dlst", ["dndvi", "dalbedo"], n=500)
    assert fit.loc["dndvi", "coef"] == pytest.approx(-10, abs=0.5)
    assert fit.loc["dalbedo", "coef"] == pytest.approx(-30, abs=2)
    assert fit.loc["dndvi", "ci_lo"] < -10 < fit.loc["dndvi", "ci_hi"]
    assert 0 <= fit.attrs["r2"] <= 1


# --- permutation test ------------------------------------------------------------------

def test_permutation_detects_clear_group_difference():
    values = np.array([0.0, 0.1, -0.1, 0.05, 3.0, 3.1, 2.9, 3.05])
    flags = np.array([False] * 4 + [True] * 4)
    out = crosssite.permutation_test(values, flags, n=2000, seed=1)
    assert out["diff"] == pytest.approx(3.0)
    assert out["p"] < 0.05


def test_permutation_p_is_large_when_groups_match():
    values = np.array([1.0, -1.0, 0.5, -0.5, 1.0, -1.0, 0.5, -0.5])
    flags = np.array([False, False, False, False, True, True, True, True])
    out = crosssite.permutation_test(values, flags, n=2000, seed=1)
    assert out["diff"] == pytest.approx(0.0)
    assert out["p"] > 0.5
