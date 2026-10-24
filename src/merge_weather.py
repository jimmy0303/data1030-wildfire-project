"""prepare the fire data and seven days of weather"""

from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
(DATA / "processed").mkdir(parents=True, exist_ok=True)
VARIABLES = [
    "temperature_2m_max", "precipitation_sum", "wind_speed_10m_max",
    "wind_gusts_10m_max", "et0_fao_evapotranspiration",
    "relative_humidity_2m_min", "vapour_pressure_deficit_max",
]

# keep text labels; only empty cells count as missing
raw = pd.read_csv(DATA / "raw/wfigs_fires.csv", keep_default_na=False,
                  na_values=[""], low_memory=False)
valid_size = (raw["IncidentSize"] >= 0) & (raw["IncidentSize"] < float("inf"))
valid_location = ((raw["InitialLatitude"] >= 31) & (raw["InitialLatitude"] <= 50)
                  & (raw["InitialLongitude"] >= -125) & (raw["InitialLongitude"] <= -102))
selected = valid_size & valid_location
fires = raw.loc[selected].copy()

# use the reported size for the target, not the final area
fires["size_class"] = "D+"
fires.loc[fires["IncidentSize"] < 100, "size_class"] = "C"
fires.loc[fires["IncidentSize"] < 10, "size_class"] = "B"
fires.loc[fires["IncidentSize"] <= 0.25, "size_class"] = "A"

discovery = pd.to_datetime(fires["FireDiscoveryDateTime"], unit="ms", utc=True)
fires["discovery_datetime_utc"] = discovery.dt.strftime("%Y-%m-%dT%H:%M:%SZ")
fires["year"] = discovery.dt.year
fires["month"] = discovery.dt.month
fires["dayofyear"] = discovery.dt.dayofyear
fires["latitude"] = fires["InitialLatitude"]
fires["longitude"] = fires["InitialLongitude"]
fires["cell_latitude"] = (fires["InitialLatitude"] * 2).round() / 2
fires["cell_longitude"] = (fires["InitialLongitude"] * 2).round() / 2
fires["cell_id"] = fires["cell_latitude"].astype(str) + "_" + fires["cell_longitude"].astype(str)
fires["weather_start_date"] = (discovery - pd.Timedelta(days=7)).dt.strftime("%Y-%m-%d")
fires["weather_end_date"] = (discovery - pd.Timedelta(days=1)).dt.strftime("%Y-%m-%d")

daily = pd.read_csv(DATA / "raw/weather_daily.csv", keep_default_na=False, na_values=[""])
if daily.duplicated(["cell_id", "date"]).any():
    raise ValueError("Daily weather contains repeated cell/date rows.")

# add seven rows for each fire, one for each day
days = []
for lag in range(7, 0, -1):
    rows = fires[["fire_id", "cell_id"]].copy()
    rows["date"] = (discovery - pd.Timedelta(days=lag)).dt.strftime("%Y-%m-%d")
    rows["days_before"] = lag
    days.append(rows)
days = pd.concat(days, ignore_index=True)
days = days.merge(daily[["cell_id", "date"] + VARIABLES],
                  on=["cell_id", "date"], how="left", validate="many_to_one")
grouped = days.groupby("fire_id")[VARIABLES]
counts = grouped.count()
means = grouped.mean()
sums = grouped.sum(min_count=7)
maximums = grouped.max()
previous = days.loc[days["days_before"] == 1].set_index("fire_id")
days["dry_day"] = days["precipitation_sum"] < 1

weather = pd.DataFrame(index=counts.index)
weather["temp_max_mean_7d"] = means["temperature_2m_max"]
weather["precipitation_sum_7d"] = sums["precipitation_sum"]
weather["wind_speed_max_7d"] = maximums["wind_speed_10m_max"]
weather["wind_gust_max_7d"] = maximums["wind_gusts_10m_max"]
weather["et0_sum_7d"] = sums["et0_fao_evapotranspiration"]
weather["rh_min_mean_7d"] = means["relative_humidity_2m_min"]
weather["vpd_max_7d"] = maximums["vapour_pressure_deficit_max"]
weather["dry_days_7d"] = days.groupby("fire_id")["dry_day"].sum()
weather["previous_day_temp_max"] = previous["temperature_2m_max"]
weather["previous_day_rh_min"] = previous["relative_humidity_2m_min"]

# leave the result empty if any of the seven values is missing
features = {
    "temperature_2m_max": ["temp_max_mean_7d", "previous_day_temp_max"],
    "precipitation_sum": ["precipitation_sum_7d", "dry_days_7d"],
    "wind_speed_10m_max": ["wind_speed_max_7d"],
    "wind_gusts_10m_max": ["wind_gust_max_7d"],
    "et0_fao_evapotranspiration": ["et0_sum_7d"],
    "relative_humidity_2m_min": ["rh_min_mean_7d", "previous_day_rh_min"],
    "vapour_pressure_deficit_max": ["vpd_max_7d"],
}
for variable in VARIABLES:
    weather.loc[counts[variable] != 7, features[variable]] = float("nan")
weather["weather_complete"] = (counts == 7).all(axis=1)
missing_fields = []
for fire_id, row in counts.iterrows():
    names = []
    for variable in VARIABLES:
        if row[variable] != 7:
            names.append(variable)
    missing_fields.append(";".join(names))
weather["weather_missing_fields"] = missing_fields

elevation = pd.read_csv(DATA / "raw/cell_elevation.csv")
fires = fires.merge(elevation[["cell_id", "elevation_m"]], on="cell_id",
                    how="left", validate="many_to_one")
fires = fires.merge(weather.reset_index(), on="fire_id", how="left", validate="one_to_one")
fires = fires.rename(columns={
    "POOState": "state", "POOCounty": "county", "POOLandownerCategory": "landowner_category",
    "PredominantFuelGroup": "fuel_group", "FireCause": "fire_cause",
    "IncidentSize": "incident_size_acres", "FinalAcres": "final_acres",
    "elevation_m": "cell_elevation_m",
})
columns = [
    "fire_id", "discovery_datetime_utc", "year", "month", "dayofyear",
    "latitude", "longitude", "state", "county", "landowner_category",
    "fuel_group", "fire_cause", "incident_size_acres", "final_acres", "size_class",
    "cell_id", "cell_latitude", "cell_longitude", "cell_elevation_m",
    "weather_start_date", "weather_end_date", "temp_max_mean_7d", "precipitation_sum_7d",
    "wind_speed_max_7d", "wind_gust_max_7d", "et0_sum_7d", "rh_min_mean_7d",
    "vpd_max_7d", "dry_days_7d", "previous_day_temp_max", "previous_day_rh_min",
    "weather_complete", "weather_missing_fields",
]
data = fires[columns]
data.to_csv(DATA / "processed/wildfire_dataset.csv", index=False)

print(f"Saved {len(data):,} fires and {len(columns)} columns.")
