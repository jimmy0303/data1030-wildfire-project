"""use saved weather and get missing data one place at a time"""
import json
from pathlib import Path
import time
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import urlopen

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
VARIABLES = ["temperature_2m_max", "precipitation_sum", "wind_speed_10m_max",
             "wind_gusts_10m_max", "et0_fao_evapotranspiration",
             "relative_humidity_2m_min", "vapour_pressure_deficit_max"]
UNITS = ["°C", "mm", "m/s", "m/s", "mm", "%", "kPa"]
FIELDS = ["cell_id", "date", *VARIABLES, "elevation_m",
          "grid_latitude", "grid_longitude", "model"]


def request_data(endpoint, params):
    """count this request before getting the data"""
    time.sleep(1)
    now = pd.Timestamp.now(tz="UTC")
    path = ROOT / "data/daily_api_usage.json"
    usage = {"date": now.strftime("%Y-%m-%d"), "calls": 0}
    if path.exists():
        with open(path, encoding="utf-8") as file:
            saved = json.load(file)
        if saved["date"] == usage["date"]:
            usage = saved
    if usage["calls"] >= 9800:
        print("The daily API budget is used. Resume on the next UTC day.")
        return None
    usage["calls"] += 1
    with open(path, "w", encoding="utf-8") as file:
        json.dump(usage, file)
    try:
        with urlopen(endpoint + "?" + urlencode(params), timeout=90) as connection:
            return json.load(connection)
    except HTTPError as error:
        if error.code == 429:
            print("The API returned 429. Saved data are kept. Resume later.")
            return None
        raise


def pull_weather():
    """use seven full utc days before the fire was found"""
    raw = ROOT / "data/raw"
    fires = pd.read_csv(raw / "wfigs_fires.csv", low_memory=False)
    latitude = fires["InitialLatitude"]
    longitude = fires["InitialLongitude"]
    size = fires["IncidentSize"]
    valid = ((latitude >= 31) & (latitude <= 50) & (longitude >= -125)
             & (longitude <= -102) & (size >= 0) & (size < float("inf")))
    requests = pd.DataFrame({"cell_latitude": (latitude.loc[valid] * 2).round() / 2,
                             "cell_longitude": (longitude.loc[valid] * 2).round() / 2,
                             "discovery_date": pd.to_datetime(fires.loc[valid, "FireDiscoveryDateTime"], unit="ms", utc=True).dt.normalize()})
    requests["cell_id"] = requests["cell_latitude"].astype(str) + "_" + requests["cell_longitude"].astype(str)
    requests = requests.drop_duplicates(["cell_id", "discovery_date"])
    daily_path = raw / "weather_daily.csv"
    if daily_path.exists():
        daily = pd.read_csv(daily_path)[FIELDS]
    else:
        daily = pd.DataFrame(columns=FIELDS)
    covered = set(zip(daily["cell_id"], daily["date"]))
    downloaded = 0
    stopped = False
    for request in requests.to_dict("records"):
        discovery = request["discovery_date"]
        days = [(discovery - pd.Timedelta(days=offset)).strftime("%Y-%m-%d") for offset in range(7, 0, -1)]
        if all((request["cell_id"], day) in covered for day in days):
            continue
        params = {"latitude": str(request["cell_latitude"]), "longitude": str(request["cell_longitude"]),
                  "start_date": days[0], "end_date": days[-1], "daily": ",".join(VARIABLES),
                  "models": "era5", "timezone": "GMT", "temperature_unit": "celsius",
                  "wind_speed_unit": "ms", "precipitation_unit": "mm", "timeformat": "iso8601"}
        response = request_data("https://archive-api.open-meteo.com/v1/archive", params)
        if response is None:
            stopped = True
            break
        if response["daily"]["time"] != days or response["utc_offset_seconds"] != 0:
            raise ValueError("Weather dates do not match the seven UTC days requested")
        for variable, unit in zip(VARIABLES, UNITS):
            if response["daily_units"][variable] != unit:
                raise ValueError("The weather API returned a different unit")
        new = pd.DataFrame(response["daily"]).rename(columns={"time": "date"})
        new["cell_id"] = request["cell_id"]
        new["elevation_m"] = response["elevation"]
        new["grid_latitude"] = response["latitude"]
        new["grid_longitude"] = response["longitude"]
        new["model"] = "era5"
        # keep the old values if we already have these days
        new = new.loc[[(request["cell_id"], day) not in covered for day in new["date"]], FIELDS]
        daily = pd.concat([daily, new], ignore_index=True)
        covered.update(zip(new["cell_id"], new["date"]))
        downloaded += 1
        if downloaded % 25 == 0:
            daily.to_csv(daily_path, index=False, encoding="utf-8-sig")
    daily = daily.sort_values(["cell_id", "date"])
    daily.to_csv(daily_path, index=False, encoding="utf-8-sig")
    print(f"Saved {len(daily)} weather rows. New weather requests: {downloaded}.")

    cells = requests[["cell_id", "cell_latitude", "cell_longitude"]].drop_duplicates("cell_id")
    elevation_path = raw / "cell_elevation.csv"
    if elevation_path.exists():
        elevations = pd.read_csv(elevation_path)
    else:
        elevations = pd.DataFrame(columns=["cell_id", "cell_latitude", "cell_longitude", "elevation_m"])
    missing = cells.loc[~cells["cell_id"].isin(elevations["cell_id"])]
    if not stopped:
        for cell in missing.to_dict("records"):
            params = {"latitude": str(cell["cell_latitude"]), "longitude": str(cell["cell_longitude"])}
            response = request_data("https://api.open-meteo.com/v1/elevation", params)
            if response is None:
                break
            new = pd.DataFrame([{**cell, "elevation_m": response["elevation"][0]}])
            elevations = pd.concat([elevations, new], ignore_index=True)
            elevations.to_csv(elevation_path, index=False, encoding="utf-8-sig")
    if not elevation_path.exists():
        elevations.to_csv(elevation_path, index=False)
    print(f"Saved elevation for {len(elevations)} cells.")
    return daily


if __name__ == "__main__":
    pull_weather()
