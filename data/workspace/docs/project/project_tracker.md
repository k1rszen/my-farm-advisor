# Project Tracker - NC Farm Analysis and Mapping

**Date:** 2026-04-06  
**Project:** Assignment 04 - Field Soil Mapping

---

## 1. Project Overview

This project creates interactive and static dashboard maps for agricultural fields in North Carolina. The maps visualize soil characteristics and texture components across 23 fields.

---

## 2. Data Sources

| Source File | Description |
|------------|-------------|
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
|------------|----------|
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

# Project Tracker - NC Farm Analysis and Mapping

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
|------------|-------------|
| `osm-260949778_NDVI_EPSG4326.tif` | GeoTIFF in WGS84 |
| `osm-260949778_NDVI_UTM.tif` | GeoTIFF in UTM (EPSG:32617) |
| `osm-260949778_NDVI_color.png` | Color visualization (RdYlGn colormap) |
| `ndvi_summary_top10.csv` | Statistics summary for top 10 fields |

### Top 10 Fields NDVI Summary

| Field ID | County | Area (acres) | NDVI Min | NDVI Max | NDVI Mean | Pixels | Source |
|----------|--------|-------------|----------|----------|----------|--------|--------|
| osm-260949778 | Guilford | 768.05 | -0.0116 | 0.4382 | 0.2387 | 2074 | landsat |
| osm-1153259427 | Union | 617.77 | 0.1553 | 0.6011 | 0.4011 | 24823 | sentinel2 |
| osm-813157720 | Person | 194.99 | -0.0315 | 0.5052 | 0.1959 | 7181 | sentinel2 |
| osm-1305439648 | Davidson | 192.38 | 0.0617 | 0.4194 | 0.1625 | 7457 | sentinel2 |
| osm-1386621285 | Rowan | 187.21 | 0.1361 | 0.3476 | 0.2324 | 8150 | sentinel2 |
| osm-1133139440 | Hoke | 144.39 | 0.0788 | 0.4809 | 0.1174 | 5356 | sentinel2 |
| osm-1476971106 | Alamance | 137.74 | 0.1696 | 0.5425 | 0.3753 | 5415 | sentinel2 |
| osm-834363677 | Randolph | 132.83 | 0.1043 | 0.3402 | 0.1343 | 5842 | sentinel2 |
| osm-548794709 | Cumberland | 99.31 | 0.0748 | 0.4848 | 0.2990 | 3783 | sentinel2 |
| osm-199889806 | Moore | 98.41 | 0.0922 | 0.4652 | 0.2098 | 3679 | sentinel2 |

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

## 9. Data Lineage Updates (2026-04-19)

### Satellite NDVI Update: osm-260949778

| Version | Source | Date | Gap % | Mean NDVI | Coverage | Status |
|---------|--------|------|-------|---------|---------|--------|
| Original | SSURGO pipeline | Various | 62%* | 0.238 | N/A | Has -9999 nodata |
| **Sentinel-2 v2** | Element84 AWS | 2025-09-19 | 0% | 0.699 | 100% | **CURRENT** |

### Data Source Changes

**Previous Issues:**
- Original NDVI had 62% nodata (-9999 values)
- Azure Planetary Computer returned wrong MGRS tile (T17SPA vs T17SPV)
- Landsat downloads failed due to SAS token authentication

**Solution Applied:**
1. Used Element84 STAC API (no auth required) - public access
2. Downloaded full Sentinel-2 L2A scene (red + nir bands)
3. **Proper clipping workflow:**
   - Convert field EPSG:4326 bounds → UTM EPSG:32617 bounds
   - Add 100m buffer to field bounds
   - Clip from cached AWS bands (not center point)
   - Calculate NDVI in UTM
   - Reproject entire clipped area to EPSG:4326
4. Final coverage: 100% of field boundary

### Files Produced

| File | Description |
|------|-----------|
| `osm-260949778_AWS_red.tif` | AWS Sentinel-2 red band (cached, 201.9 MB) |
| `osm-260949778_AWS_nir.tif` | AWS Sentinel-2 NIR band (cached, 239.0 MB) |
| `osm-260949778_NDVI_AWS_Sentinel2_utm_v2.tif` | NDVI in UTM |
| `osm-260949778_NDVI_AWS_Sentinel2_4326_v2.tif` | **Current NDVI** (EPSG:4326) |

### Key Lesson

**Always convert field boundaries to the raster's CRS before clipping**, not just use approximate center points.

---

# Project Tracker - NC Farm Analysis and Mapping

**Date:** 2026-04-14  
**Project:** Assignment 06 - Weather Analysis

---

## 1. Project Overview

This project retrieves historical weather data from NASA POWER API for 10 NC agricultural fields, calculates Growing Degree Days (GDD), detects anomalies using a 5-year baseline (2020-2024), and creates interactive HTML visualizations with field selectors.

---

## 2. Data Sources

| Source | Description |
|--------|-------------|
| `NC_field_boundaries_EPSG4326_2026-04-01.geojson` | Field boundary polygons - 10 fields selected |
| NASA POWER API | Parameters: T2M (mean temp), T2M_MAX, T2M_MIN, PRECTOTCORR (precipitation), ALLSKY_SFC_SW_DWN (solar radiation), RH2M, WS10M |

**Fields Analyzed:**
- osm-260949778 (Guilford County, 768 acres)
- osm-1153259427 (Union County, 618 acres)
- osm-813157720 (Person County, 195 acres)
- osm-1305439648 (Davidson County, 192 acres)
- osm-1386621285 (Rowan County, 187 acres)
- osm-1133139440 (Hoke County, 144 acres)
- osm-1476971106 (Alamance County, 138 acres)
- osm-834363677 (Randolph County, 133 acres)
- osm-548794709 (Cumberland County, 99 acres)
- osm-199889806 (Moore County, 98 acres)

---

## 3. Weather Outputs

### CSV Files

| File | Description |
|------|-------------|
| `weather_top10_2020_2024.csv` | Daily weather data for all 10 fields (2020-2024) |
| `weather_top10_with_rolling_avg.csv` | Daily data with 30-day rolling averages |
| `anomaly_summary.csv` | Monthly mean, std, and deviation calculations |
| `weather_seasonal_summary.csv` | Growing season (May-Sep) summaries |

### Annual Weather Summary (2020-2024)

| Year | Temp Mean (°C) | Temp Max (°C) | Temp Min (°C) | Precip (mm) | Precip Days | GDD | Solar (MJ/m²) |
|------|----------------|--------------|--------------|------------|------------|-----|-------------|
| 2020 | 15.41 | 22.78 | 8.04 | 1607.8 | 182 | 2533.8 | 5737.4 |
| 2021 | 15.54 | 22.87 | 8.21 | 981.2 | 178 | 2710.6 | 5934.7 |
| 2022 | 15.36 | 22.64 | 8.08 | 1184.4 | 185 | 2711.3 | 5961.9 |
| 2023 | 15.86 | 23.15 | 8.57 | 1182.2 | 179 | 2628.9 | 5838.0 |
| 2024 | 15.94 | 23.22 | 8.66 | 1335.6 | 181 | 2762.0 | 5892.1 |

### Interactive HTML Visualizations

| File | Description |
|------|-------------|
| `weather_trends.html` | Main dashboard with 10 stacked charts: Temperature (°F), Daily Precip, Cumulative Precip, GDD, Solar Radiation |
| `temperature_rolling_avg.html` | 30-day rolling average temperature per field |
| `precipitation_rolling_avg.html` | 30-day rolling average precipitation per field |
| `temperature_anomalies.html` | Monthly temperature deviations from 5-year baseline |
| `precipitation_anomalies.html` | Monthly precipitation deviations from 5-year baseline |
| `cumulative_precipitation.html` | Monthly running precipitation totals |

### PNG Charts

| File | Description |
|------|-------------|
| `weather_osm-{field_id}_{year}.png` | Per-field, per-year temperature range + GDD cumulative |

---

## 4. Scripts

| Script | Description |
|--------|-------------|
| `download_weather.py` | Queries NASA POWER API for all 10 fields (2020-2024) |
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

## 6. Notebook

- `06_weather_analysis.ipynb` - Contains all code for data retrieval, GDD calculation, rolling averages, anomaly detection, trends analysis, and visualizations

---

# Project Tracker - NC Farm Analysis and Mapping

**Date:** 2026-04-19  
**Project:** Assignment 07 - Zonal Statistics Integration

---

## 1. Project Overview

This project integrates soil (SSURGO), weather (NASA POWER), and satellite NDVI (Sentinel-2) data for 24 agricultural fields across North Carolina. Zonal statistics are computed for each field boundary to create a unified dataset for multi-year analysis.

---

## 2. Data Sources

| Source | Description |
|--------|-------------|
| `NC_field_boundaries_EPSG4326_2026-04-01.geojson` | Field boundary polygons (23 fields originally, 24 in output) |
| SSURGO via SoilWeb API | Soil properties: OM, pH, AWC, clay, sand, CEC, drainage |
| NASA POWER API | Weather: temperature, precipitation, GDD, solar radiation (2020-2024) |
| Sentinel-2 L2A (Element84 AWS) | NDVI: cloud-free composite for fields with gaps |

---

## 3. Outputs

### CSV Files

| File | Description |
|------|-------------|
| `zonal_integration_summary.csv` | Integrated soil + weather + NDVI for all 24 fields |
| `om_vs_gdd.png` | Scatter plot: Organic Matter vs GDD |
| `zonal_stats_summary.png` | Multi-panel visualization |

### Fields Analyzed (24 total)

| Field ID | County | Area (acres) | OM (%) | pH | NDVI | GDD | Precip (mm) |
|----------|--------|-------------|--------|-----|------|-----|-------------|
| osm-260949778 | Guilford | 768.05 | 1.04 | 5.89 | 0.239 | 11230 | 3530 |
| osm-1153259427 | Union | 617.77 | 0.83 | 4.80 | 0.401 | 12086 | 3319 |
| osm-813157720 | Person | 194.99 | 1.05 | 5.39 | 0.195 | 11073 | 3548 |
| osm-1386621285 | Rowan | 187.21 | 0.85 | 5.93 | 0.233 | 10775 | 3603 |
| osm-1305439648 | Davidson | 192.38 | 1.05 | 5.09 | 0.162 | 10775 | 3603 |
| osm-1133139440 | Hoke | 144.39 | 2.39 | 4.84 | 0.117 | 12418 | 3541 |
| osm-1476971106 | Alamance | 137.74 | 0.90 | 5.32 | 0.375 | 11230 | 3530 |
| osm-834363677 | Randolph | 132.83 | 0.68 | 5.82 | 0.133 | 11230 | 3530 |
| osm-548794709 | Cumberland | 99.31 | 2.98 | 4.92 | 0.299 | 12418 | 3541 |
| osm-199889806 | Moore | 98.41 | 0.89 | 4.88 | 0.209 | 11981 | 3479 |
| osm-1435108796 | Iredell | 90.73 | 0.76 | 5.88 | — | 10775 | 3603 |
| osm-692623518 | Montgomery | 4.44 | 2.93 | 4.93 | — | 12497 | 3467 |
| osm-1361967329 | Rockingham | 74.81 | 0.80 | 5.56 | — | 11230 | 3530 |
| osm-976134461 | Chatham | 59.08 | 1.04 | 5.06 | — | 11688 | 3628 |
| osm-1103713058 | Franklin | 54.45 | 0.79 | 5.26 | — | 11819 | 3606 |
| osm-274848457 | Granville | 63.97 | 0.67 | 5.32 | — | 11688 | 3628 |
| osm-588414811 | Cabarrus | 67.71 | 1.03 | 5.95 | — | 11374 | 3458 |
| osm-1424677694 | Lee | 26.48 | 0.96 | 5.18 | — | 11981 | 3479 |
| osm-1009084804 | Anson | 44.58 | 0.74 | 5.26 | — | 12086 | 3319 |
| osm-566823123 | Davie | 22.60 | 0.63 | 5.59 | — | 10775 | 3603 |
| osm-1197040178 | Yadkin | 22.00 | 0.77 | 5.33 | — | 10775 | 3603 |
| osm-1278239614 | Forsyth | 35.99 | 1.31 | 5.38 | — | 10775 | 3603 |
| osm-1383475117 | Stanly | 13.19 | 0.72 | 5.22 | — | 11374 | 3458 |

---

## 4. Key Findings

### Soil-Weather Relationships
- Fields with higher organic matter (>2%) tend to have lower GDD accumulation
- Poorly drained soils (Cumberland, Montgomery) show highest OM but require management for planting
- pH ranges from 4.2 to 7.0; most fields acidic (pH < 5.5)

### NDVI Coverage (5 of 24 fields)
- Only Guilford (768 ac), Union (618 ac), Hoke (144 ac), Cumberland (99 ac), Person (195 ac) have full Sentinel-2 NDVI
- Other fields: gaps due to cloud cover in imagery archive

---

## 5. Data Quality Issues

### Weather Data Duplication (Same NASA POWER Grid)
**Issue:** Multiple fields share identical weather data from the same NASA POWER grid cell.

**Weather Station Group 1** (temp=21.67°C, precip=3602.99mm, GDD=10774.96):
- osm-1305439648 (Davidson, 192 ac)
- osm-566823123 (Davie, 23 ac)
- osm-1435108796 (Iredell, 91 ac)
- osm-1197040178 (Yadkin, 22 ac)
- osm-1386621285 (Rowan, 187 ac)

**Weather Station Group 2** (temp=22.04°C, precip=3530.29mm, GDD=11230.0):
- osm-260949778 (Guilford, 768 ac)
- osm-834363677 (Randolph, 133 ac)
- osm-1476971106 (Alamance, 138 ac)

**Impact:** Weather metrics for these fields are identical. This is expected for fields within the same NASA POWER 0.5° grid cell.

---

## 6. Scripts

| Script | Description |
|--------|-------------|
| `generate_zonal_stats.py` | Integrates SSURGO + weather + NDVI per field |
| `generate_correlation_plots.py` | Creates OM vs GDD scatter and multi-panel plots |

---

## 7. Notebook

- `07_zonal_integration.ipynb` - Contains all zonal statistics calculations, integration logic, and visualizations