# Western U.S. wildfire size

This project studies reported wildfire size in 11 western U.S. states during 2020–2025. The dataset has 75,272 incident records and 33 columns. The target is an ordered size class derived from IncidentSize.

Python 3.14.6 and pandas 3.0.6 were used. Run from the project folder:

```text
conda env create -f environment.yml
conda activate wildfire-data
python src/collect_fires.py
python src/pull_weather.py
python src/merge_weather.py
```

The scripts reuse saved files and request only missing data. The supplied data can be processed without internet access. Data are in `data/` and code is in `src/`. The completed team report will go in `report/`. `data/DATA_DICTIONARY.md` defines every final column. `data/category_values.csv` lists category meanings, and `data/raw_field_dictionary.csv` describes the original fire table.

Fire records come from the [NIFC WFIGS API](https://services3.arcgis.com/T4QMspbfLg3qTGWY/arcgis/rest/services/WFIGS_Incident_Locations/FeatureServer/0). Weather comes from [Open-Meteo](https://open-meteo.com/en/docs/historical-weather-api) using ERA5 from the Copernicus Climate Change Service/ECMWF. Elevation comes from [Copernicus DEM GLO-90 through Open-Meteo](https://open-meteo.com/en/docs/elevation-api). Open-Meteo data use CC BY 4.0; the MIT license applies to code, not the source data.
