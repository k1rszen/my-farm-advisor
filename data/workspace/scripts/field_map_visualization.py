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
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import folium
from pathlib import Path

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
# SUMMARY
# =============================================================================
print("\n" + "=" * 70)
print("VISUALIZATION COMPLETE")
print("=" * 70)
print(f"\nStatic Map (2x2 combined):")
print(f"  → {PLOTS_DIR / 'field_soil_characteristics.png'}")
print(f"\nInteractive HTML Map:")
print(f"  → {OUTPUT_DIR / 'farm_field_map_interactive.html'}")
print(f"\nFeatures:")
print(f"  - 4 soil characteristic layers: pH, OM%, CEC, AWS")
print(f"  - pH is default visible layer")
print(f"  - Toggle layers using layer control (top-right)")
print(f"  - Hover tooltips show all field properties")
