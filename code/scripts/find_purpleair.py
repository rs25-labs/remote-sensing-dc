"""Count outdoor PurpleAir sensors near each census data center that ran before and after construction.

Needs a free PurpleAir read key in the environment: PURPLEAIR_API_KEY. Writes
outputs/census/purpleair_sensors.csv (one row per nearby sensor) and purpleair_summary.csv (per site).
Only counts are reported; sensor names are not kept, since many are at private homes.
"""

import json
import math
import os
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from dc_heat import geo  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
URL = "https://api.purpleair.com/v1/sensors"
NEAR_KM, FAR_KM = 2, 10        # "near" sensors, and the radius searched for comparison sensors
FIELDS = "latitude,longitude,date_created,last_seen,location_type"


def sensors_around(lat: float, lon: float, key: str) -> pd.DataFrame:
    pad_lat = FAR_KM / 111.0
    pad_lon = FAR_KM / (111.0 * math.cos(math.radians(lat)))
    query = urllib.parse.urlencode({
        "fields": FIELDS, "location_type": 0, "max_age": 0,          # outdoor, including retired sensors
        "nwlat": lat + pad_lat, "nwlng": lon - pad_lon, "selat": lat - pad_lat, "selng": lon + pad_lon})
    request = urllib.request.Request(f"{URL}?{query}", headers={"X-API-Key": key})
    with urllib.request.urlopen(request, timeout=60) as response:
        data = json.load(response)
    frame = pd.DataFrame(data["data"], columns=data["fields"])
    if frame.empty:
        return frame
    frame["created"] = pd.to_datetime(frame.date_created, unit="s")
    frame["last_seen"] = pd.to_datetime(frame.last_seen, unit="s")
    frame["dist_km"] = [geo.haversine_m(lat, lon, a, b) / 1000 for a, b in zip(frame.latitude, frame.longitude)]
    return frame[frame.dist_km <= FAR_KM]


if __name__ == "__main__":
    key = os.environ.get("PURPLEAIR_API_KEY")
    if not key:
        sys.exit("Set PURPLEAIR_API_KEY first (a free read key from https://develop.purpleair.com).")
    sites = pd.read_csv(ROOT / "data" / "census" / "census_sites.csv")
    windows_used = pd.read_csv(ROOT / "outputs" / "census" / "census_windows.csv")
    sites = sites[sites.role == "census"].merge(
        windows_used[["site_id", "construction_year"]], on="site_id", suffixes=("_registry", ""))

    rows, summary = [], []
    for s in sites.itertuples():
        found = sensors_around(s.lat, s.lon, key)
        start = pd.Timestamp(int(s.construction_year), 1, 1)
        spans = (found.created < start) & (found.last_seen >= pd.Timestamp("2025-01-01")) if len(found) else []
        near = found.dist_km <= NEAR_KM if len(found) else []
        summary.append({
            "site_id": s.site_id, "name": s.name,
            "construction_year": int(s.construction_year),
            "near_any": int(sum(near)), "near_before_and_after": int(sum(near & spans)) if len(found) else 0,
            "within_10km_before_and_after": int(sum(spans)) if len(found) else 0})
        if len(found):
            rows.append(found.assign(site_id=s.site_id, spans_construction=spans)
                        [["site_id", "latitude", "longitude", "dist_km", "created", "last_seen", "spans_construction"]])
        time.sleep(1)
    if rows:
        pd.concat(rows).to_csv(ROOT / "outputs" / "census" / "purpleair_sensors.csv", index=False)
    table = pd.DataFrame(summary).sort_values("near_before_and_after", ascending=False)
    table.to_csv(ROOT / "outputs" / "census" / "purpleair_summary.csv", index=False)
    print(f"Outdoor PurpleAir sensors: within {NEAR_KM} km, and those running from before construction into 2025+")
    print(table.to_string(index=False))
