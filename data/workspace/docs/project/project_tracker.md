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
