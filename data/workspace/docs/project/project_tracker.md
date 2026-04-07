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
