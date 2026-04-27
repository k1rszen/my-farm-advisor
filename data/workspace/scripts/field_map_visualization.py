#!/usr/bin/env python3
"""Field Map Visualization

Creates static and interactive maps of NC field boundaries with soil characteristics:
- pH (default for interactive)
- Organic Matter (%)
- CEC (meq/100g)
- Available Water Storage (inches)

Output:
- data/workspace/plots/field_soil_characteristics.png (static 2x2)
- data/workspace/output/farm_field_map_interactive.html (interactive)
"""

import json
import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import folium
from pathlib import Path

try:
    import rasterio
    from rasterio.plot import show
except ImportError:
    print("WARNING: rasterio not found. Install with: pip install rasterio")
    rasterio = None

DATA_DIR = Path("/workspaces/my-farm-advisor/data/workspace")
PLOTS_DIR = DATA_DIR / "plots"
OUTPUT_DIR = DATA_DIR / "output"
PLOTS_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

print("=" * 70)
print("FIELD MAP VISUALIZATION")
print("=" * 70)

# Load data
print("\n1. Loading data...")
soil_df = pd.read_csv(DATA_DIR / "NC_soil_crop_data_summary_EPSG4326_2026-04-01.csv")
geojson_path = DATA_DIR / "NC_field_boundaries_EPSG4326_2026-04-01.geojson"
gdf = gpd.read_file(geojson_path)

print(f"   GeoDataFrame: {len(gdf)} fields")
print(f"   Soil data: {len(soil_df)} rows")

# Merge soil data with GeoDataFrame
print("\n2. Merging datasets...")
gdf = gdf.merge(soil_df, on='field_id', how='left', suffixes=('', '_soil'))
print(f"   Merged: {len(gdf)} fields with soil properties")

# Check coordinate system
print(f"\n   CRS: {gdf.crs}")

# Define soil characteristics
soil_chars = {
    'avg_ph': {'label': 'Soil pH', 'cmap': 'YlOrRd', 'vmin': 4.5, 'vmax': 6.5},
    'avg_om_pct': {'label': 'Organic Matter (%)', 'cmap': 'YlGn', 'vmin': 0.5, 'vmax': 2.2},
    'avg_cec': {'label': 'CEC (meq/100g)', 'cmap': 'YlGnBu', 'vmin': 2.5, 'vmax': 14.0},
    'total_aws_inches': {'label': 'Available Water Storage (inches)', 'cmap': 'OrRd', 'vmin': 0.5, 'vmax': 9.0}
}

# =============================================================================
# STATIC MAP: 2x2 Combined Figure
# =============================================================================
print("\n3. Creating static 2x2 map...")

fig, axes = plt.subplots(2, 2, figsize=(16, 12))
axes = axes.flatten()

for idx, (col, props) in enumerate(soil_chars.items()):
    ax = axes[idx]
    gdf.plot(
        column=col,
        cmap=props['cmap'],
        vmin=props['vmin'],
        vmax=props['vmax'],
        legend=True,
        edgecolor='black',
        linewidth=0.5,
        ax=ax,
        legend_kwds={
            'label': props['label'],
            'orientation': 'horizontal',
            'shrink': 0.6,
            'pad': 0.02
        }
    )
    ax.set_title(props['label'], fontsize=12, fontweight='bold')
    ax.set_xlabel('Longitude')
    ax.set_ylabel('Latitude')
    ax.set_axis_off()

plt.suptitle('NC Field Soil Characteristics', fontsize=16, fontweight='bold', y=0.98)
plt.tight_layout(rect=[0, 0.03, 1, 0.95])
plt.savefig(PLOTS_DIR / 'field_soil_characteristics.png', dpi=300, bbox_inches='tight')
plt.close()

print(f"   ✓ Saved: {PLOTS_DIR / 'field_soil_characteristics.png'}")

# =============================================================================
# INTERACTIVE HTML MAP (FOLIUM)
# =============================================================================
print("\n4. Creating interactive HTML map...")

# Center on bounding box of NC fields
bounds = gdf.total_bounds  # [minx, miny, maxx, maxy]
center_lat = (bounds[1] + bounds[3]) / 2
center_lon = (bounds[0] + bounds[2]) / 2

m = folium.Map(location=[center_lat, center_lon], zoom_start=8, tiles='cartodbpositron')

# Color functions for each characteristic
def get_color_ph(value):
    if pd.isna(value):
        return '#cccccc'
    norm = (value - 4.5) / (6.5 - 4.5)
    if norm < 0.2:
        return '#ffffb2'
    elif norm < 0.4:
        return '#fecc5c'
    elif norm < 0.6:
        return '#fd8d3c'
    elif norm < 0.8:
        return '#f03b20'
    else:
        return '#bd0026'

def get_color_om(value):
    if pd.isna(value):
        return '#cccccc'
    norm = (value - 0.5) / (2.2 - 0.5)
    if norm < 0.2:
        return '#ffffe5'
    elif norm < 0.4:
        return '#c7e9b4'
    elif norm < 0.6:
        return '#7bccc4'
    elif norm < 0.8:
        return '#41b6c4'
    else:
        return '#1d91c0'

def get_color_cec(value):
    if pd.isna(value):
        return '#cccccc'
    norm = (value - 2.5) / (14.0 - 2.5)
    if norm < 0.2:
        return '#ffffd9'
    elif norm < 0.4:
        return '#c7e9b4'
    elif norm < 0.6:
        return '#41b6c4'
    elif norm < 0.8:
        return '#225ea8'
    else:
        return '#0c2c84'

def get_color_aws(value):
    if pd.isna(value):
        return '#cccccc'
    norm = (value - 0.5) / (9.0 - 0.5)
    if norm < 0.2:
        return '#ffffb2'
    elif norm < 0.4:
        return '#fecc5c'
    elif norm < 0.6:
        return '#fd8d3c'
    elif norm < 0.8:
        return '#f03b20'
    else:
        return '#bd0026'

# Style functions
style_ph = lambda x: {'fillColor': get_color_ph(x['properties'].get('avg_ph')), 'color': 'black', 'weight': 1, 'fillOpacity': 0.7}
style_om = lambda x: {'fillColor': get_color_om(x['properties'].get('avg_om_pct')), 'color': 'black', 'weight': 1, 'fillOpacity': 0.7}
style_cec = lambda x: {'fillColor': get_color_cec(x['properties'].get('avg_cec')), 'color': 'black', 'weight': 1, 'fillOpacity': 0.7}
style_aws = lambda x: {'fillColor': get_color_aws(x['properties'].get('total_aws_inches')), 'color': 'black', 'weight': 1, 'fillOpacity': 0.7}

# Tooltip fields
tooltip_fields = ['field_id', 'crop_name', 'area_acres', 'avg_ph', 'avg_om_pct', 'avg_cec', 'total_aws_inches']
tooltip_aliases = ['Field ID:', 'Crop:', 'Area (acres):', 'pH:', 'OM (%):', 'CEC:', 'AWS (in):']

# Feature groups
fg_ph = folium.FeatureGroup(name='Soil pH (default)', show=True)
fg_om = folium.FeatureGroup(name='Organic Matter (%)', show=False)
fg_cec = folium.FeatureGroup(name='CEC (meq/100g)', show=False)
fg_aws = folium.FeatureGroup(name='Available Water Storage', show=False)

# Convert to GeoJSON
gdf_json = json.loads(gdf.to_json())

# Add layers
folium.GeoJson(gdf_json, style_function=style_ph, tooltip=folium.GeoJsonTooltip(fields=tooltip_fields, aliases=tooltip_aliases)).add_to(fg_ph)
folium.GeoJson(gdf_json, style_function=style_om, tooltip=folium.GeoJsonTooltip(fields=tooltip_fields, aliases=tooltip_aliases)).add_to(fg_om)
folium.GeoJson(gdf_json, style_function=style_cec, tooltip=folium.GeoJsonTooltip(fields=tooltip_fields, aliases=tooltip_aliases)).add_to(fg_cec)
folium.GeoJson(gdf_json, style_function=style_aws, tooltip=folium.GeoJsonTooltip(fields=tooltip_fields, aliases=tooltip_aliases)).add_to(fg_aws)

# Add to map
fg_ph.add_to(m)
fg_om.add_to(m)
fg_cec.add_to(m)
fg_aws.add_to(m)

# Add layer control
folium.LayerControl(collapsed=False).add_to(m)

# Add title
title_html = '''
<div style="position: fixed; top: 10px; left: 50px; z-index: 9999; background-color: white; padding: 10px; border-radius: 5px; box-shadow: 2px 2px 5px rgba(0,0,0,0.3);">
    <h4 style="margin: 0;">NC Field Soil Characteristics</h4>
</div>
'''
m.get_root().html.add_child(folium.Element(title_html))

# Save HTML
output_path = OUTPUT_DIR / 'farm_field_map_interactive.html'
m.save(output_path)
print(f"   ✓ Saved: {output_path}")


# =============================================================================
# SPATIAL JOIN: NDVI + Soil Indicators for 5 Largest Fields
# =============================================================================
#
# IMPORTANT - CRS Conversion Best Practice:
# ====================================
# This script uses PRE-PROCESSED NDVI files that were created with proper CRS handling.
#
# WRONG approach (会导致部分覆盖/partial coverage):
# --------------------------------------------
# Using approximate center point + buffer without CRS conversion:
#     center_x, center_y = field_centroid  # Wrong!
#     window = rasterio.windows.from_bounds(center_x - buffer, ...)
# This causes incomplete field coverage because buffer doesn't match actual field boundaries.
#
# CORRECT approach used for NDVI preprocessing:
# --------------------------------------------
# 1. Get field bounds in EPSG:4326 (lat/lon):
#     field_bounds = field.geometry.bounds
#
# 2. Convert field bounds to raster CRS (e.g., EPSG:32617 UTM):
#     transformer = pyproj.Transformer.from_crs('EPSG:4326', 'EPSG:32617', always_xy=True)
#     left_utm, bottom_utm = transformer.transform(field_bounds[0], field_bounds[1])
#
# 3. Add buffer and clip using bounds (NOT center point!):
#     window = rasterio.windows.from_bounds(left_utm-buffer, bottom_utm-buffer, ...)
#
# 4. Reproject entire clipped area to EPSG:4326 after calculating NDVI
#
# Lesson learned (2026-04-19):
# =============================
# The field osm-260949778 (768 acres) initially showed only 41% coverage
# when using center point + buffer approach. After switching to proper
# CRS conversion, coverage became 100%.
#
# See: skills/my-farm-advisor/r2-seed-pipeline/src/scripts/lib/satellite_imagery.py
#      Function: clip_asset_to_field()
# =============================================================================
def create_spatial_join_visualizations():
    """Create spatial join visualizations combining NDVI rasters with soil indicators."""
    if rasterio is None:
        print("   SKIP: rasterio not available")
        return

    print("\n5. Creating spatial join visualizations...")

    print("   Loading field boundaries...")
    fields_gdf = gpd.read_file(DATA_DIR / "NC_field_boundaries_EPSG4326_2026-04-01.geojson")

    print("   Loading soil indicators...")
    soil_df = pd.read_csv(DATA_DIR / "NC_soil_crop_data_summary_EPSG4326_2026-04-01.csv")

    print("   Performing spatial join (merge on field_id)...")
    merged_gdf = fields_gdf.merge(soil_df, on="field_id", how="inner")
    print(f"   Joined {len(merged_gdf)} fields with soil data")

    print("   Identifying 5 largest fields...")
    top5 = merged_gdf.nlargest(5, "area_acres")
    print(f"   Top 5 fields: {top5['field_id'].tolist()}")

    ndvi_dir = DATA_DIR / "output" / "assignment-05"

    ndvi_files = {
        "osm-260949778": "osm-260949778_NDVI_AWS_Sentinel2_4326_v2.tif",
        "osm-1153259427": "osm-1153259427_NDVI.tif",
        "osm-1305439648": "osm-1305439648_NDVI.tif",
        "osm-1386621285": "osm-1386621285_NDVI.tif",
        "osm-813157720": "osm-813157720_NDVI.tif",
        "osm-1476971106": "osm-1476971106_NDVI.tif",
        "osm-1133139440": "osm-1133139440_NDVI.tif",
        "osm-834363677": "osm-834363677_NDVI.tif",
        "osm-548794709": "osm-548794709_NDVI.tif",
        "osm-199889806": "osm-199889806_NDVI.tif",
    }

    fig, axes = plt.subplots(2, 3, figsize=(18, 12))
    axes = axes.flatten()

    om_cmap = mcolors.LinearSegmentedColormap.from_list(
        "om_brown", ["#d4a574", "#8b4513", "#3d1f0d"], N=256
    )

    plotted = 0
    for idx, (_, row) in enumerate(top5.iterrows()):
        field_id = row["field_id"]
        area = row["area_acres"]
        county = row["county_name"]

        print(f"   Processing field {plotted + 1}/5: {field_id} ({area:.1f} ac)")

        if field_id not in ndvi_files:
            print(f"      WARNING: No NDVI file for {field_id}")
            continue

        ndvi_path = ndvi_dir / ndvi_files[field_id]
        if not ndvi_path.exists():
            print(f"      WARNING: NDVI file not found: {ndvi_path}")
            continue

        ax = axes[plotted]

        try:
            with rasterio.open(ndvi_path) as src:
                nodata_val = src.nodata
                ndvi_data = src.read(1)
                ndvi_bounds = src.bounds
                field_bounds = row.geometry.bounds

                if nodata_val is not None and nodata_val == -9999:
                    ndvi_data = np.where(ndvi_data == nodata_val, np.nan, ndvi_data)

                valid_data = ndvi_data[~np.isnan(ndvi_data)]
                if len(valid_data) > 0:
                    vmin = max(-0.2, np.percentile(valid_data, 2))
                    vmax = min(0.8, np.percentile(valid_data, 98))
                    ndvi_mean = np.mean(valid_data)
                else:
                    vmin, vmax = -0.2, 0.8
                    ndvi_mean = np.nan

                show(
                    ndvi_data,
                    cmap="RdYlGn",
                    vmin=vmin,
                    vmax=vmax,
                    ax=ax,
                    alpha=0.5,
                    transform=src.transform,
                )

                field_geom = row.geometry
                x, y = field_geom.exterior.coords.xy
                ax.plot(x, y, color="black", linewidth=2.0, solid_joinstyle="round")

                om_val = row.get("avg_om_pct", 0)
                if pd.notna(om_val):
                    om_norm = (om_val - 0.5) / (2.2 - 0.5)
                    om_norm = max(0, min(1, om_norm))
                    om_color = om_cmap(om_norm)
                    ax.plot(
                        x,
                        y,
                        color=om_color,
                        linewidth=3.5,
                        solid_joinstyle="round",
                        label=f"OM: {om_val:.2f}%",
                    )

                ax.set_xlim(field_bounds[0] - 0.002, field_bounds[2] + 0.002)
                ax.set_ylim(field_bounds[1] - 0.002, field_bounds[3] + 0.002)

                ax.set_title(
                    f"{field_id}\n{area:.1f} ac | {county}\nOM: {om_val:.2f}% | NDVI: {ndvi_mean:.3f}",
                    fontsize=9,
                    fontweight="bold",
                )
                ax.set_xlabel("Longitude", fontsize=8)
                ax.set_ylabel("Latitude", fontsize=8)
                ax.tick_params(labelsize=7)

                plotted += 1

        except Exception as e:
            print(f"      ERROR: {e}")
            continue

    for i in range(plotted, 6):
        axes[i].axis("off")

    fig.suptitle(
        "Spatial Join: NDVI (alpha=0.5) + Soil Indicators\n5 Largest NC Fields",
        fontsize=14,
        fontweight="bold",
    )

    cbar_ax = fig.add_axes([0.92, 0.15, 0.015, 0.7])
    cbar_ax.set_title("NDVI", fontsize=9)
    fig.colorbar(
        plt.cm.ScalarMappable(cmap="RdYlGn", norm=mcolors.Normalize(vmin=-0.2, vmax=0.8)),
        cax=cbar_ax,
        label="NDVI (-1 to 1)",
    )

    om_cbar_ax = fig.add_axes([0.92, 0.82, 0.015, 0.12])
    om_cbar_ax.set_title("OM Border", fontsize=8)
    fig.colorbar(
        plt.cm.ScalarMappable(cmap=om_cmap, norm=mcolors.Normalize(vmin=0.5, vmax=2.2)),
        cax=om_cbar_ax,
        label="Organic Matter (%)",
    )

    plt.tight_layout(rect=[0, 0, 0.9, 0.95])
    plt.savefig(PLOTS_DIR / "spatial_join_5largest.png", dpi=200, bbox_inches="tight")
    plt.close()

    print(f"   ✓ Saved: {PLOTS_DIR / 'spatial_join_5largest.png'}")
    print(f"   Created {plotted} field visualizations with NDVI + OM border")


create_spatial_join_visualizations()

# =============================================================================
# SUMMARY
# =============================================================================
print("\n" + "=" * 70)
print("VISUALIZATION COMPLETE")
print("=" * 70)
print(f"\nStatic Map (2x2 combined):")
print(f"  → {PLOTS_DIR / 'field_soil_characteristics.png'}")
print(f"\nInteractive HTML Map:")
print(f"  → {OUTPUT_DIR / 'farm_field_map_interactive.html'}")
print(f"\nSpatial Join Visualizations:")
print(f"  → {PLOTS_DIR / 'spatial_join_5largest.png'}")
print(f"\nFeatures:")
print(f"  - 4 soil characteristic layers: pH, OM%, CEC, AWS")
print(f"  - pH is default visible layer")
print(f"  - Toggle layers using layer control (top-right)")
print(f"  - Hover tooltips show all field properties")
print(f"  - Spatial join combines NDVI raster with soil indicators")
print(f"  - NDVI transparency: 0.5")
print(f"  - OM border: color-coded by OM value (0.5-2.2%)")
