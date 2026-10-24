# Data dictionary

This dictionary specifies the 33-column fire-level table. Each row represents one selected WFIGS incident record. The selected source snapshot contains 75,272 records after coordinate screening. Category values and their counts refer to all 75,272 selected incident records.

The acquisition selected wildfire (WF) records in 11 western U.S. states with discovery dates in 2020-2025 UTC, a nonempty FireOutDateTime and IncidentSize, and usable original InitialLatitude/InitialLongitude within the saved coordinate bounds. FireOutDateTime indicates that the incident was reported out; this does not prove that IncidentSize equals a finalized burned area. The target is size_class derived from IncidentSize, not FinalAcres. IncidentSize, FinalAcres and variables derived from the target must not be used as prediction features.

Let D be the UTC calendar date of discovery. Every weather feature uses the seven complete UTC dates D-7 through D-1 inclusive, excluding the fire discovery UTC day. The 0.5-degree cells are project request groups, not ERA5 native resolution. ERA5 has a documented 0.25-degree grid; API-returned weather coordinates can differ from the requested cell coordinates. Reanalysis reconstructs historical conditions using assimilated observations and was retrieved retrospectively. Even earlier-dated weather is not guaranteed to have been available for real-time prediction at discovery.

Cell elevation refers to the rounded request coordinate and a 90 m DEM, not actual fire-site altitude. Fire cause can become known after discovery. This snapshot also does not establish discovery-time availability for county, landowner or fuel fields. Their availability must be justified for any discovery-time prediction claim.

Empty CSV cells indicate missing numeric/date/category data unless a field-specific rule below says otherwise. Literal #, Unknown and Undetermined are retained source values rather than silently converted to missing. Each weather aggregation requires all seven daily values for its source variable; otherwise its derived feature is missing. No missing values are imputed.

| Column | Stored type | Kind / role | Unit | Definition and interpretation |
|---|---|---|---|---|
| `fire_id` | string | Identifier, not a measurement | none | Source `IrwinID`. Stable normalized IRWIN record key; not a label for a measured fire extent. |
| `discovery_datetime_utc` | datetime string | Datetime / temporal index | UTC | Source `FireDiscoveryDateTime`. Source FireDiscoveryDateTime converted to ISO 8601 UTC. |
| `year` | integer | Discrete calendar feature | year | UTC discovery year, 2020 through 2025. |
| `month` | integer | Discrete cyclic calendar feature | month | UTC month number, January=1 through December=12. |
| `dayofyear` | integer | Discrete cyclic calendar feature | day | UTC day number within the year, January 1=1; 1-365 or 1-366 in a leap year. |
| `latitude` | number | Continuous location | decimal degrees | Source `InitialLatitude`. Original InitialLatitude retained for half-degree weather-cell assignment. |
| `longitude` | number | Continuous location | decimal degrees | Source `InitialLongitude`. Original InitialLongitude retained for half-degree weather-cell assignment. |
| `state` | category | Nominal category | none | Source `POOState`. All 11 observed code/name pairs are listed in category_values.csv. |
| `county` | category | Nominal category | none | Source `POOCounty`. Every observed literal county name is listed in category_values.csv. Same-name counties can occur in different states. |
| `landowner_category` | category | Nominal category | none | Source `POOLandownerCategory`. Recorded point-of-origin deeded-owner category. NWCG mappings are documented below; OthFed, OthLoc and # remain unresolved. |
| `fuel_group` | category | Nominal category | none | Source `PredominantFuelGroup`. Source predominant fuel grouping; observed labels and missing values are listed in category_values.csv. No exact fuel-model mapping is inferred. |
| `fire_cause` | category | Nominal category; availability-sensitive | none | Source `FireCause`. All four source labels are preserved, including Unknown and Undetermined as distinct literal values. Cause may be determined after discovery. |
| `incident_size_acres` | number | Continuous target-source measurement; not a predictor | acres | Source `IncidentSize`. Reported source incident area used to derive size_class; nonnegative values are required. It can change over the incident and is not certified final area. |
| `final_acres` | number or null | Continuous source measurement; not a predictor | acres | Source `FinalAcres`. Independently retained reported final acreage; never used as a substitute for IncidentSize. Blank remains missing. |
| `size_class` | category | Classification target (ordered categories) | none | Project intervals: A [0,0.25], B (0.25,10), C [10,100), D+ [100,infinity) acres. Target derives only from IncidentSize. |
| `cell_id` | string | Spatial grouping identifier | none | Requested cell coordinate pair formatted latitude_longitude; not an original fire identifier or the returned ERA5 grid-cell identifier. |
| `cell_latitude` | number | Spatial lookup coordinate | decimal degrees | round(latitude * 2) / 2, using Python ties-to-even rounding. Request grouping uses 0.5-degree increments. |
| `cell_longitude` | number | Spatial lookup coordinate | decimal degrees | round(longitude * 2) / 2, using Python ties-to-even rounding. Request grouping uses 0.5-degree increments. |
| `cell_elevation_m` | number | Continuous spatial feature | m | Copernicus GLO-90 DEM elevation at the requested rounded cell coordinate. It is not measured altitude at the original fire coordinates. |
| `weather_start_date` | date string | Date / window metadata | UTC date | Inclusive UTC date D-7, where D is the UTC discovery date. |
| `weather_end_date` | date string | Date / window metadata | UTC date | Inclusive UTC date D-1. The discovery UTC day is excluded. |
| `temp_max_mean_7d` | number | Continuous weather feature | °C | Arithmetic mean of the seven daily maximum 2 m temperatures. |
| `precipitation_sum_7d` | number | Continuous weather feature | mm | Sum of seven daily precipitation totals. |
| `wind_speed_max_7d` | number | Continuous weather feature | m/s | Maximum of seven daily maximum 10 m wind speeds. |
| `wind_gust_max_7d` | number | Continuous weather feature | m/s | Maximum of seven daily maximum 10 m wind gusts. |
| `et0_sum_7d` | number | Continuous weather feature | mm | Sum of seven daily FAO reference evapotranspiration totals. |
| `rh_min_mean_7d` | number | Continuous weather feature | % | Arithmetic mean of seven daily minimum 2 m relative humidities. |
| `vpd_max_7d` | number | Continuous weather feature | kPa | Maximum of seven daily maximum vapour pressure deficits. |
| `dry_days_7d` | integer | Discrete count feature | days | Count of days with precipitation_sum < 1 mm; possible values 0-7 when all seven days are present. |
| `previous_day_temp_max` | number | Continuous weather feature | °C | Daily maximum 2 m temperature on D-1. |
| `previous_day_rh_min` | number | Continuous weather feature | % | Daily minimum 2 m relative humidity on D-1. |
| `weather_complete` | boolean | Boolean data-quality flag | none | True only when all seven requested source weather variables have nonmissing values for all seven expected dates; otherwise False. This does not certify scientific accuracy. |
| `weather_missing_fields` | string | Data-quality metadata, not a physical measurement | none | Semicolon-separated source variable names missing on at least one required day. Empty string means no missing weather variables; it is not an unknown value for this flag. |

## Category values

`category_values.csv` lists every observed value of state, county, landowner_category, fuel_group, fire_cause and size_class, with its meaning and occurrence count among all 75,272 selected incidents. It has 376 rows: 11 state values, 333 county-name literals, 18 landowner values including the empty value, six fuel values including the empty value, four cause values and four size classes. Counts for each column independently sum to 75,272. Counties are named county or equivalent entities; no county name is converted to or guessed to be a FIPS code. A name should be interpreted with its state.

Landowner expansions use the NWCG Landowner Kind & Category standard (2016), not a fabricated coded domain for this layer. The retained OthFed and OthLoc source codes are not defined in that standard or supplied layer metadata, and # has no verified meaning. Their CSV meanings explicitly remain unresolved. Fuel labels are retained as source groups without inventing species, fuel moisture, model membership or numeric codes. Human and Natural are broad cause categories; the supplied definition does not distinguish Unknown from Undetermined.

## Sources and data limitations

Six overlapping daily ET0 observations differed between saved API responses. The retained values follow a fixed selection of the later-retrieved response. The difference has no confirmed explanation, and the selected values are not claimed to be more accurate.

Fire-field meanings follow the [NIFC descriptions archived by WIFIRE](https://wifire-data.sdsc.edu/dataset/wildland-fire-incident-locations), [NWCG Incident Size standard](https://fs-prod-nwcg.s3.us-gov-west-1.amazonaws.com/s3fs-public/2023-08/910-incident-size.pdf), and [NWCG Landowner Kind & Category standard](https://fs-prod-nwcg.s3.us-gov-west-1.amazonaws.com/s3fs-public/2023-08/LandownerKindCategory20160825.pdf).

Weather definitions and units follow the [Open-Meteo Historical Weather API](https://open-meteo.com/en/docs/historical-weather-api); terrain definitions follow the [Open-Meteo Elevation API](https://open-meteo.com/en/docs/elevation-api). Credit belongs to Open-Meteo, the Copernicus Climate Change Service/ERA5 and Copernicus DEM. Source identifiers are [ERA5 DOI](https://doi.org/10.24381/cds.adbb2d47), [Open-Meteo DOI](https://doi.org/10.5281/zenodo.7970649), and [Copernicus DEM DOI](https://doi.org/10.5270/ESA-c5d3d65).
