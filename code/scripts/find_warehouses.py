"""Find large warehouse candidates near each selected census data center from OpenStreetMap.

Keeps building footprints of at least MIN_AREA_M2 that are MIN_KM-MAX_KM from their data center and at
least MIN_KM from every census data center, merges footprints within 500 m (one site, several
buildings), and writes the largest candidates per site to data/census/warehouse_candidates.csv.
Construction years are not needed here: the census notebook dates each one from Landsat.
"""

import json
import math
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from dc_heat import geo  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
CENSUS = ROOT / "data" / "census"
import os
URL = os.environ.get("OVERPASS_URL", "https://overpass-api.de/api/interpreter")
HEADERS = {"User-Agent": "dc_heat-research/0.1"}
MIN_AREA_M2, MIN_KM, PER_SITE = 40_000, 3, 5
MAX_KM = float(os.environ.get("MAX_KM", 30))
SELECTED = ["OWN-MESA", "EPOCH-09", "META-EAGLE-MOUNTAIN", "META-LOS-LUNAS", "EPOCH-13", "META-KUNA",
            "OWN-MIDLOTHIAN", "EPOCH-07", "EPOCH-10", "OWN-SOCIAL-CIRCLE", "OWN-GALLATIN",
            "META-HENRICO", "EPOCH-00", "EPOCH-06", "EPOCH-14", "EPOCH-01"]


def query(lat: float, lon: float) -> list[dict]:
    radius = MAX_KM * 1000
    q = f"""[out:json][timeout:180];
    (way["building"~"^(warehouse|industrial|commercial|retail)$"](around:{radius},{lat},{lon});
     way["building"]["name"~"distribution|fulfillment|fulfilment|warehouse|logistics",i](around:{radius},{lat},{lon}););
    out tags geom;"""
    data = urllib.parse.urlencode({"data": q}).encode()
    request = urllib.request.Request(URL, data=data, headers=HEADERS)
    with urllib.request.urlopen(request, timeout=240) as response:
        return json.load(response)["elements"]


def area_and_centroid(geometry: list[dict]) -> tuple[float, float, float]:
    lat0 = sum(p["lat"] for p in geometry) / len(geometry)
    kx, ky = 111_320 * math.cos(math.radians(lat0)), 110_540
    xs = [p["lon"] * kx for p in geometry]
    ys = [p["lat"] * ky for p in geometry]
    area = 0.5 * abs(sum(xs[i] * ys[i + 1] - xs[i + 1] * ys[i] for i in range(len(xs) - 1)))
    return area, lat0, sum(p["lon"] for p in geometry) / len(geometry)


if __name__ == "__main__":
    retry = sys.argv[1:]                     # optional: only these site ids, appended to the existing file
    if retry:
        SELECTED = retry
    sites = pd.read_csv(CENSUS / "census_sites.csv")
    census = sites[sites.role == "census"]
    all_dcs = list(zip(census.lat, census.lon))
    rows = []
    for site_id in SELECTED:
        s = census.set_index("site_id").loc[site_id]
        try:
            elements = query(s.lat, s.lon)
        except Exception as err:
            print(f"{site_id}: ERROR {err}")
            continue
        found = []
        for e in elements:
            if not e.get("geometry") or len(e["geometry"]) < 4:
                continue
            area, lat, lon = area_and_centroid(e["geometry"])
            if area < MIN_AREA_M2:
                continue
            d_own = geo.haversine_m(s.lat, s.lon, lat, lon) / 1000
            d_any = min(geo.haversine_m(a, b, lat, lon) for a, b in all_dcs) / 1000
            if not (MIN_KM <= d_own <= MAX_KM) or d_any < MIN_KM:
                continue
            tags = e.get("tags", {})
            found.append({"dc_site_id": site_id, "data_center": s["name"], "osm_way": e["id"],
                          "name": tags.get("name", ""), "operator": tags.get("operator", ""),
                          "building": tags.get("building", ""), "roof_m2": round(area),
                          "lat": round(lat, 5), "lon": round(lon, 5),
                          "dist_dc_km": round(d_own, 1), "dist_nearest_dc_km": round(d_any, 1)})
        found.sort(key=lambda r: -r["roof_m2"])
        kept = []
        for r in found:                       # one candidate per site of several buildings
            if all(geo.haversine_m(r["lat"], r["lon"], k["lat"], k["lon"]) > 500 for k in kept):
                kept.append(r)
        rows += kept[:PER_SITE]
        print(f"{site_id:20s} {len(elements):5d} OSM buildings -> {len(found):3d} big enough and well placed -> kept {len(kept[:PER_SITE])}")
        time.sleep(20 if retry else 5)
    out = pd.DataFrame(rows)
    if retry and (CENSUS / "warehouse_candidates.csv").exists():
        previous = pd.read_csv(CENSUS / "warehouse_candidates.csv")
        out = pd.concat([previous[~previous.dc_site_id.isin(retry)], out], ignore_index=True)
    out.to_csv(CENSUS / "warehouse_candidates.csv", index=False)
    print(f"\n{len(out)} candidates written")
