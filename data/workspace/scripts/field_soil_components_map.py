#!/usr/bin/env python3
"""Field Soil Components Map

Creates an interactive map of NC field boundaries with soil texture components:
- Clay (%)
- Sand (%)
- Silt (%)

Output:
- data/workspace/output/farm_field_soil_components_interactive.html (interactive)
"""

import json
import pandas as pd
import geopandas as gpd
import folium
from pathlib import Path

DATA_DIR = Path("/workspaces/my-farm-advisor/data/workspace")
OUTPUT_DIR = DATA_DIR / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

print("=" * 70)
print("FIELD SOIL COMPONENTS MAP")
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

# Center on bounding box of NC fields
bounds = gdf.total_bounds
center_lat = (bounds[1] + bounds[3]) / 2
center_lon = (bounds[0] + bounds[2]) / 2

m = folium.Map(location=[center_lat, center_lon], zoom_start=8, tiles='cartodbpositron')

# Color functions for each component
def get_color_clay(value):
    if pd.isna(value):
        return '#cccccc'
    norm = (value - 5) / (40 - 5)
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

def get_color_sand(value):
    if pd.isna(value):
        return '#cccccc'
    norm = (value - 20) / (90 - 20)
    if norm < 0.2:
        return '#0c2c84'
    elif norm < 0.4:
        return '#225ea8'
    elif norm < 0.6:
        return '#41b6c4'
    elif norm < 0.8:
        return '#c7e9b4'
    else:
        return '#ffffd9'

def get_color_silt(value):
    if pd.isna(value):
        return '#cccccc'
    norm = (value - 5) / (55 - 5)
    if norm < 0.2:
        return '#ffffd9'
    elif norm < 0.4:
        return '#c7e9b4'
    elif norm < 0.6:
        return '#7bccc4'
    elif norm < 0.8:
        return '#1d91c0'
    else:
        return '#0c2c84'

# Style functions
style_clay = lambda x: {'fillColor': get_color_clay(x['properties'].get('avg_clay_pct')), 'color': 'black', 'weight': 1, 'fillOpacity': 0.7}
style_sand = lambda x: {'fillColor': get_color_sand(x['properties'].get('avg_sand_pct')), 'color': 'black', 'weight': 1, 'fillOpacity': 0.7}
style_silt = lambda x: {'fillColor': get_color_silt(x['properties'].get('avg_silt_pct')), 'color': 'black', 'weight': 1, 'fillOpacity': 0.7}

# Tooltip fields
tooltip_fields = ['field_id', 'crop_name', 'area_acres', 'avg_clay_pct', 'avg_sand_pct', 'avg_silt_pct']
tooltip_aliases = ['Field ID:', 'Crop:', 'Area (acres):', 'Clay (%):', 'Sand (%):', 'Silt (%):']

# Feature groups
fg_clay = folium.FeatureGroup(name='Clay (%)', show=True)
fg_sand = folium.FeatureGroup(name='Sand (%)', show=False)
fg_silt = folium.FeatureGroup(name='Silt (%)', show=False)

# Convert to GeoJSON
gdf_json = json.loads(gdf.to_json())

# Add layers
folium.GeoJson(gdf_json, style_function=style_clay, tooltip=folium.GeoJsonTooltip(fields=tooltip_fields, aliases=tooltip_aliases)).add_to(fg_clay)
folium.GeoJson(gdf_json, style_function=style_sand, tooltip=folium.GeoJsonTooltip(fields=tooltip_fields, aliases=tooltip_aliases)).add_to(fg_sand)
folium.GeoJson(gdf_json, style_function=style_silt, tooltip=folium.GeoJsonTooltip(fields=tooltip_fields, aliases=tooltip_aliases)).add_to(fg_silt)

# Add to map
fg_clay.add_to(m)
fg_sand.add_to(m)
fg_silt.add_to(m)

# Add layer control
folium.LayerControl(collapsed=False).add_to(m)

# Add title
title_html = '''
<div style="position: fixed; top: 10px; left: 50px; z-index: 9999; background-color: white; padding: 10px; border-radius: 5px; box-shadow: 2px 2px 5px rgba(0,0,0,0.3);">
    <h4 style="margin: 0;">NC Field Soil Texture Components</h4>
</div>
'''
m.get_root().html.add_child(folium.Element(title_html))

# Add legend
legend_html = '''
<div style="position: fixed; bottom: 30px; left: 30px; z-index: 9999; 
            background-color: white; padding: 12px; border-radius: 5px; 
            box-shadow: 0 0 15px rgba(0,0,0,0.2); font-family: Arial, sans-serif; font-size: 11px; min-width: 200px;">
    <div style="margin-bottom: 8px;">
        <strong>Layer:</strong>
        <select id="layer-select" onchange="switchLayer(this.value)" style="margin-left: 5px; padding: 2px;">
            <option value="clay">Clay (%)</option>
            <option value="sand">Sand (%)</option>
            <option value="silt">Silt (%)</option>
        </select>
    </div>
    <div id="legend-content">
        <div id="legend-clay-content">
            <strong>Clay (%)</strong><br>
            <span style="background: #0c2c84; color: white; padding: 2px 6px; margin-right: 2px;">40</span>
            <span style="background: #225ea8; color: white; padding: 2px 6px; margin-right: 2px;">32</span>
            <span style="background: #41b6c4; color: white; padding: 2px 6px; margin-right: 2px;">23</span>
            <span style="background: #c7e9b4; padding: 2px 6px; margin-right: 2px;">14</span>
            <span style="background: #ffffd9; padding: 2px 6px;">5</span><br>
            <span style="color: #666; font-size: 10px;">High ← → Low</span>
        </div>
        <div id="legend-sand-content" style="display: none;">
            <strong>Sand (%)</strong><br>
            <span style="background: #ffffd9; padding: 2px 6px; margin-right: 2px;">20</span>
            <span style="background: #c7e9b4; padding: 2px 6px; margin-right: 2px;">38</span>
            <span style="background: #41b6c4; color: white; padding: 2px 6px; margin-right: 2px;">55</span>
            <span style="background: #225ea8; color: white; padding: 2px 6px; margin-right: 2px;">72</span>
            <span style="background: #0c2c84; color: white; padding: 2px 6px;">90</span><br>
            <span style="color: #666; font-size: 10px;">Low ← → High</span>
        </div>
        <div id="legend-silt-content" style="display: none;">
            <strong>Silt (%)</strong><br>
            <span style="background: #0c2c84; color: white; padding: 2px 6px; margin-right: 2px;">55</span>
            <span style="background: #1d91c0; color: white; padding: 2px 6px; margin-right: 2px;">44</span>
            <span style="background: #7bccc4; color: white; padding: 2px 6px; margin-right: 2px;">32</span>
            <span style="background: #c7e9b4; padding: 2px 6px; margin-right: 2px;">21</span>
            <span style="background: #ffffd9; padding: 2px 6px;">5</span><br>
            <span style="color: #666; font-size: 10px;">High ← → Low</span>
        </div>
    </div>
</div>
'''

m.get_root().html.add_child(folium.Element(legend_html))

# Add layer switching script
script_html = '''
<script>
var layerFeatureGroups = {
    'clay': fg_clay,
    'sand': fg_sand,
    'silt': fg_silt
};

function switchLayer(layer) {
    document.getElementById('legend-clay-content').style.display = 'none';
    document.getElementById('legend-sand-content').style.display = 'none';
    document.getElementById('legend-silt-content').style.display = 'none';
    document.getElementById('legend-' + layer + '-content').style.display = 'block';
    
    for (var key in layerFeatureGroups) {
        if (layerFeatureGroups.hasOwnProperty(key)) {
            if (key === layer) {
                if (!map.hasLayer(layerFeatureGroups[key])) {
                    layerFeatureGroups[key].addTo(map);
                }
            } else {
                if (map.hasLayer(layerFeatureGroups[key])) {
                    map.removeLayer(layerFeatureGroups[key]);
                }
            }
        }
    }
}
</script>
'''

# Note: The feature group names in the script need to match the actual JS variables
# This is a simplified approach - the layer control already handles visibility

# Save HTML
output_path = OUTPUT_DIR / 'farm_field_soil_components_interactive.html'
m.save(output_path)
print(f"\n✓ Saved: {output_path}")

print("\n" + "=" * 70)
print("SOIL COMPONENTS MAP COMPLETE")
print("=" * 70)
print(f"\nInteractive HTML Map:")
print(f"  → {output_path}")
print(f"\nFeatures:")
print(f"  - 3 soil texture layers: Clay, Sand, Silt")
print(f"  - Clay is default visible layer")
print(f"  - Toggle layers using layer control (top-right)")
print(f"  - Hover tooltips show all field properties")
