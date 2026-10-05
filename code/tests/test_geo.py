import pandas as pd
import pytest

from dc_heat import geo


def test_haversine_between_the_two_mesa_campuses():
    assert geo.haversine_m(33.3472, -111.6325, 33.3463, -111.6289) == pytest.approx(349, abs=10)


def test_haversine_is_zero_for_the_same_point():
    assert geo.haversine_m(36.4116, -86.3690, 36.4116, -86.3690) == 0.0


def _sites():
    return pd.DataFrame({
        "site_id": ["META-MESA", "EDGECORE-MESA", "META-GALLATIN"],
        "lat": [33.3472, 33.3463, 36.4116],
        "lon": [-111.6325, -111.6289, -86.3690],
    })


def test_cluster_groups_campuses_within_radius():
    out = geo.cluster_sites(_sites(), radius_m=1000).set_index("site_id")
    assert out.loc["META-MESA", "cluster_id"] == out.loc["EDGECORE-MESA", "cluster_id"]
    assert out.loc["META-GALLATIN", "cluster_id"] != out.loc["META-MESA", "cluster_id"]


def test_cluster_links_chains_of_nearby_campuses():
    # A-B 800 m apart and B-C 800 m apart: all three share a cluster even though A-C is 1.6 km
    sites = pd.DataFrame({
        "site_id": ["A", "B", "C"],
        "lat": [33.0, 33.0, 33.0],
        "lon": [-111.0, -111.0 + 0.00859, -111.0 + 0.01718],
    })
    out = geo.cluster_sites(sites, radius_m=1000)
    assert out["cluster_id"].nunique() == 1


def test_cluster_ids_are_stable_and_start_at_zero():
    out = geo.cluster_sites(_sites(), radius_m=1000)
    assert sorted(out["cluster_id"].unique()) == [0, 1]
