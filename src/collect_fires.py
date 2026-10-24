"""use the saved fire data or get it from wfigs"""
import json
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def collect_fires():
    path = ROOT / "data/raw/wfigs_fires.csv"
    if path.exists():
        fires = pd.read_csv(path, low_memory=False)
        print(f"Using the supplied table: {len(fires)} fires.")
        return fires

    endpoint = "https://services3.arcgis.com/T4QMspbfLg3qTGWY/arcgis/rest/services/WFIGS_Incident_Locations/FeatureServer/0/query"
    where = ("IncidentTypeCategory = 'WF' AND POOState IN "
             "('US-WA','US-OR','US-CA','US-NV','US-ID','US-MT','US-WY','US-UT','US-CO','US-AZ','US-NM') "
             "AND FireDiscoveryDateTime >= TIMESTAMP '2020-01-01 00:00:00' "
             "AND FireDiscoveryDateTime < TIMESTAMP '2026-01-01 00:00:00' "
             "AND FireOutDateTime IS NOT NULL AND IncidentSize IS NOT NULL "
             "AND InitialLatitude IS NOT NULL AND InitialLongitude IS NOT NULL")
    params = {"f": "json", "where": where, "returnIdsOnly": "true"}
    with urlopen(endpoint + "?" + urlencode(params), timeout=90) as connection:
        object_ids = sorted(json.load(connection)["objectIds"])

    records = []
    coordinates = []
    for start in range(0, len(object_ids), 100):
        batch = object_ids[start:start + 100]
        params = {"f": "json", "objectIds": ",".join(str(value) for value in batch),
                  "outFields": "*", "returnGeometry": "true", "outSR": "4326",
                  "returnZ": "false", "returnM": "false"}
        with urlopen(endpoint + "?" + urlencode(params), timeout=90) as connection:
            response = json.load(connection)
        if "error" in response or response.get("exceededTransferLimit"):
            raise ValueError("WFIGS did not return the full requested batch")
        for feature in response["features"]:
            records.append(feature["attributes"])
            coordinates.append(feature["geometry"])

    fires = pd.DataFrame(records, dtype=object)
    if fires["OBJECTID"].duplicated().any() or set(fires["OBJECTID"]) != set(object_ids):
        raise ValueError("Fire records do not match the queried object IDs")
    geometry = pd.DataFrame(coordinates)
    fires["latitude"] = fires["InitialLatitude"]
    fires["longitude"] = fires["InitialLongitude"]
    fires["latitude_wgs84"] = geometry["y"]
    fires["longitude_wgs84"] = geometry["x"]
    fires["fire_id"] = fires["IrwinID"].str.strip().str.strip("{}").str.lower()
    discovery = pd.to_datetime(fires["FireDiscoveryDateTime"], unit="ms", utc=True)
    fires["discovery_datetime_utc"] = discovery.dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    fires["discovery_date_utc"] = discovery.dt.strftime("%Y-%m-%d")
    fires = fires.sort_values("OBJECTID")
    path.parent.mkdir(parents=True, exist_ok=True)
    fires.to_csv(path, index=False, encoding="utf-8-sig")
    print(f"Saved {len(fires)} fires and {len(fires.columns)} columns.")
    return fires


if __name__ == "__main__":
    collect_fires()
