# Project Tracker - NC Field Soil Mapping

**Date:** 2026-04-07  
**Project:** Assignment 05 - Landsat NDVI Analysis

---

## 1. Project Overview

This project acquires Landsat satellite imagery for the largest agricultural field in North Carolina from the field boundaries dataset (768 acres, Guilford County). The analysis includes extracting 6 spectral bands and calculating NDVI (Normalized Difference Vegetation Index) to assess vegetation health.

---

## 2. Data Sources

| Source | Description |
|--------|-------------|
| `NC_field_boundaries_EPSG4326_2026-04-01.geojson` | Field boundary polygons (23 fields) - identified largest field (osm-260949778) |
| Landsat 7 Collection 2 Level-2 | Scene: LE07_L2SP_016035_20231104_02_T1, Date: 2023-11-04, Cloud cover: 0% |
| Microsoft Planetary Computer STAC API | Alternative to USGS M2M API (endpoint issues) |

---

## 3. Spectral Bands Extracted

| Band | File (EPSG:4326) | File (UTM) | Colormap | Mean Value |
|------|------------------|------------|----------|------------|
| Blue (B2) | `osm-260949778_B2_Blue_EPSG4326.tif` | `osm-260949778_B2_Blue_UTM.tif` | Blues | 227.6 |
| Green (B3) | `osm-260949778_B3_Green_EPSG4326.tif` | `osm-260949778_B3_Green_UTM.tif` | Greens | 205.4 |
| Red (B4) | `osm-260949778_B4_Red_EPSG4326.tif` | `osm-260949778_B4_Red_UTM.tif` | Reds | 182.9 |
| NIR (B5) | `osm-260949778_B5_NIR_EPSG4326.tif` | `osm-260949778_B5_NIR_UTM.tif` | hot_r | 129.7 |
| SWIR1 (B6) | `osm-260949778_B6_SWIR1_EPSG4326.tif` | `osm-260949778_B6_SWIR1_UTM.tif` | inferno | 106.5 |
| SWIR2 (B7) | `osm-260949778_B7_SWIR2_EPSG4326.tif` | `osm-260949778_B7_SWIR2_UTM.tif` | viridis | 120.9 |

---

## 4. NDVI Results

| Output File | Description |
|-------------|-------------|
| `osm-260949778_NDVI_EPSG4326.tif` | GeoTIFF in WGS84 |
| `osm-260949778_NDVI_UTM.tif` | GeoTIFF in UTM (EPSG:32617) |
| `osm-260949778_NDVI_color.png` | Color visualization (RdYlGn colormap) |
| `ndvi_summary.csv` | Statistics summary |

**NDVI Statistics:**
- Mean: 0.2387
- Min: -0.0116
- Max: 0.4382
- Valid pixels: 2074

---

## 5. Color Visualizations

| Image File | Description |
|------------|-------------|
| `osm-260949778_B2_Blue_color.png` | Blue band visualization |
| `osm-260949778_B3_Green_color.png` | Green band visualization |
| `osm-260949778_B4_Red_color.png` | Red band visualization |
| `osm-260949778_B5_NIR_color.png` | NIR band visualization |
| `osm-260949778_B6_SWIR1_color.png` | SWIR1 band visualization |
| `osm-260949778_B7_SWIR2_color.png` | SWIR2 band visualization |
| `osm-260949778_NDVI_color.png` | NDVI visualization |

---

## 6. Scripts

| Script | Description |
|--------|-------------|
| `generate_bands.py` | Downloads Landsat bands from Planetary Computer STAC API and clips to field boundary |
| `generate_final.py` | Scales band values to 0-255 and reprojects to EPSG:4326 |
| `generate_color_images.py` | Creates color visualization PNGs for each spectral band with titles |
| `generate_ndvi.py` | Calculates NDVI from Red and NIR bands, creates NDVI visualization |

All scripts saved in `data/workspace/scripts/`

---

## 7. Challenges & Resolutions

### Challenge 1: USGS M2M API Endpoint Issues
**Issue:** The USGS Machine-to-Machine API endpoint (`https://m2m.cr.usgs.gov/api/api/json/stable/`) returned 404 errors.

**Resolution:** Used Microsoft Planetary Computer STAC API as an alternative - provides the same Landsat Collection 2 Level-2 data.

### Challenge 2: CRS Mismatch
**Issue:** Raw Landsat data in EPSG:32617 (UTM Zone 17N), field boundaries in EPSG:4326 (WGS84).

**Resolution:** Projected field geometry to UTM for clipping, then reprojected output to EPSG:4326 for compatibility.

### Challenge 3: Band Visualization Grayscale
**Issue:** Initial band images appeared as grayscale due to high surface reflectance values (7000-25000).

**Resolution:** Scaled values to 0-255 range using: `scaled = (reflectance / 10000) * 255`

---

## 8. Notebook

- `05_landsat_ndvi.ipynb` - Contains spectral band visualizations, NDVI calculation summary, and interpretation

---

# Project Tracker - NC Field Soil Mapping

**Date:** 2026-04-06  
**Project:** Assignment 04 - Field Soil Mapping

---

## 1. Project Overview

This project creates interactive and static dashboard maps for agricultural fields in North Carolina. The maps visualize soil characteristics and texture components across 23 fields.

---

## 2. Data Sources

| Source File | Description |
|-------------|-------------|
| `NC_field_boundaries_EPSG4326_2026-04-01.geojson` | Field boundary polygons (23 fields) |
| `NC_soil_crop_data_summary_EPSG4326_2026-04-01.csv` | Soil data summary with 8 indicators |

**Soil Indicators (8 total):**
- Soil pH
- Organic Matter (%)
- CEC (meq/100g)
- Available Water Storage (in)
- Clay (%)
- Sand (%)
- Silt (%)
- Bulk Density (g/cm³)

---

## 3. Interactive Maps

| Map File | Location | Description |
|----------|----------|-------------|
| `soil_indicators_dashboard.html` | `dashboard_assets/` | Unified dashboard with all 8 soil indicators, dropdown legend, centered title, North arrow |

**Dashboard Features:**
- Centered title: "NC Field Soil Indicators"
- Dropdown labeled "Soil Indicators:" to switch between layers
- North arrow in top-right corner
- Zoomed on largest field (osm-260949778, 768 acres)
- Tooltip shows all 8 indicators on hover

---

## 4. Static Outputs

| Output File | Location |
|-------------|----------|
| `field_map_dashboard_final.png` | `dashboard_assets/` |

---

## 5. Scripts

| Script | Description |
|--------|-------------|
| `generate_soil_dashboard.py` | Creates the unified HTML dashboard with all 8 soil indicators |
| `generate_soil_dashboard_png.py` | Generates static PNG screenshot of the dashboard |

---

## 6. Challenges & Resolutions

### Challenge 1: CRS Reprojection Warnings
**Issue:** Fields stored in EPSG:4326 (WGS84), calculations require EPSG:3857 (Web Mercator) for proper area calculations.

**Resolution:** Projected geometries to EPSG:3857 for area calculations. Warning appears but does not block execution.

### Challenge 2: Duplicate Legend IDs
**Issue:** Original HTML had duplicate legend blocks with identical IDs, causing `getElementById` to fail inconsistently.

**Resolution:** Removed duplicate HTML blocks, kept single legend container.

### Challenge 3: Layer Switching
**Issue:** Dropdown only changed legend visibility, not the actual map layer displayed.

**Resolution:** Added JavaScript function to toggle both:
- Legend content visibility
- Map layer visibility using Leaflet's `addLayer()` / `removeLayer()`

---

## 7. Notebook

- `04_field_mapping.ipynb` - Contains both interactive maps embedded, summary statistics, geographic trend analysis, and narrative descriptions.

---

# Project Tracker - NC Field Soil Mapping

**Date:** 2026-04-14  
**Project:** Assignment 06 - Weather Analysis

---

## 1. Project Overview

This project retrieves historical weather data from NASA POWER API for 5 NC agricultural fields, calculates Growing Degree Days (GDD), detects anomalies using a 5-year baseline (2020-2024), and creates interactive HTML visualizations with field selectors.

---

## 2. Data Sources

| Source | Description |
|--------|-------------|
| `NC_field_boundaries_EPSG4326_2026-04-01.geojson` | Field boundary polygons - 5 fields selected |
| NASA POWER API | Parameters: T2M (mean temp), T2M_MAX, T2M_MIN, PRECTOTCORR (precipitation), ALLSKY_SFC_SW_DWN (solar radiation), RH2M, WS10M |

**Fields Analyzed:**
- osm-260949778 (Guilford County, 768 acres)
- osm-1153259427 (Forsyth County, 56 acres)
- osm-813157720 (Forsyth County, 52 acres)
- osm-1305439648 (Iredell County, 45 acres)
- osm-1386621285 (Iredell County, 41 acres)

---

## 3. Weather Outputs

### CSV Files

| File | Description |
|------|-------------|
| `weather_top5_2020_2024.csv` | Daily weather data for all 5 fields (9,136 rows) |
| `weather_top5_with_rolling_avg.csv` | Daily data with 30-day rolling averages |
| `anomaly_summary.csv` | Monthly mean, std, and deviation calculations (301 rows) |
| `anomaly_summary_flagged.csv` | Only months exceeding ±2σ threshold (empty - no anomalies) |
| `weather_seasonal_summary.csv` | Growing season (May-Sep) summaries |

### Interactive HTML Visualizations

| File | Description |
|------|-------------|
| `weather_trends.html` | Main dashboard with 5 stacked charts: Temperature (°F), Daily Precip, Cumulative Precip, GDD, Solar Radiation |
| `temperature_rolling_avg.html` | 30-day rolling average temperature per field |
| `precipitation_rolling_avg.html` | 30-day rolling average precipitation per field |
| `temperature_anomalies.html` | Monthly temperature deviations from 5-year baseline |
| `precipitation_anomalies.html` | Monthly precipitation deviations from 5-year baseline |
| `cumulative_precipitation.html` | Monthly running precipitation totals |

### PNG Charts

| File | Description |
|------|-------------|
| `weather_osm-{field_id}_{year}.png` | Per-field, per-year temperature range + GDD cumulative (20 files, 5 fields × 4 years) |

---

## 4. Scripts

| Script | Description |
|--------|-------------|
| `download_weather.py` | Queries NASA POWER API for all 5 fields (2020-2024) |
| `generate_weather_trends.py` | Creates the weather_trends.html dashboard using Plotly |
| `generate_dashboard_maps.py` | Generates field map visualizations |
| `generate_dashboard_png.py` | Creates PNG screenshots of dashboards |
| `generate_summary_tables.py` | Aggregates data into summary CSVs |
| `field_eda_analysis.py` | Exploratory data analysis for fields |
| `field_map_visualization.py` | Creates interactive field maps |
| `collect_nc_piedmont_fields.py` | Collects NC Piedmont field boundaries |
| `collect_nc_soil_crop_data_incremental.py` | Collects soil and crop data incrementally |
| `download_nc_counties.py` | Downloads NC county boundaries |

---

## 5. Key Findings

### Anomaly Detection Results
- **No significant anomalies detected** for either temperature or precipitation using the ±2σ threshold
- Maximum deviation observed: 1.71σ (precipitation, December 2023)
- With only 5 years of baseline data, statistical power is limited for outlier detection

### Year-over-Year Trends (2020-2024)

| Indicator | 2020 | 2021 | 2022 | 2023 | 2024 | Change |
|-----------|------|------|------|------|------|--------|
| Mean Temp (°C) | 15.41 | 15.54 | 15.36 | 15.86 | 15.94 | +0.53 |
| Total Precip (mm) | 1607.8 | 981.2 | 1184.4 | 1182.2 | 1335.6 | -16.9% |
| Total GDD | 2533.8 | 2710.6 | 2711.3 | 2628.9 | 2762.0 | +9.0% |
| Total Solar (MJ/m²) | 5737.4 | 5934.7 | 5961.9 | 5838.0 | 5892.1 | +2.7% |

**Key Observations:**
- Temperature: Slight increasing trend (+0.53°C from 2020 to 2024)
- Precipitation: Large drop in 2021 (-39% YoY), then gradual recovery with 13% increase in 2024
- GDD: 2021 and 2022 were high GDD years; 2023 showed a 3% decrease before recovering in 2024 (+5%)
- Solar radiation: Relatively stable with minor fluctuations

---

## 6. Data Quality Issues

### Duplicate Field Data
**Issue:** osm-1305439648 and osm-1386621285 have identical weather data (temperature, precipitation, GDD, solar radiation).

**Reason:** These two fields are located very close to each other (~8km apart) in Iredell County. NASA POWER returns the same weather grid values for both locations, resulting in duplicate data.

**Impact:**
- Rolling averages and anomaly calculations are affected (effectively weighted 2x for these two fields)
- This is expected behavior for nearby agricultural fields sharing the same weather grid

**Fields:**
- osm-1305439648: lat=35.8364, lon=-80.4793
- osm-1386621285: lat=35.7514, lon=-80.6983

---

## 7. Notebook

- `06_weather_analysis.ipynb` - Contains all code for data retrieval, GDD calculation, rolling averages, anomaly detection, trends analysis, and visualizations
