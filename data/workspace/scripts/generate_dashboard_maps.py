#!/usr/bin/env python3
"""Dashboard-style Field Soil Maps

Creates dashboard-ready HTML versions of field soil maps with:
- Centered, bold title
- Larger, more readable legend
- Zoomed in on largest field
"""

import json
import pandas as pd
import geopandas as gpd
import folium
from pathlib import Path

DATA_DIR = Path("/workspaces/my-farm-advisor/data/workspace")
DASH_DIR = DATA_DIR / "dashboard_assets"
DASH_DIR.mkdir(parents=True, exist_ok=True)

# Load data
soil_df = pd.read_csv(DATA_DIR / "NC_soil_crop_data_summary_EPSG4326_2026-04-01.csv")
geojson_path = DATA_DIR / "NC_field_boundaries_EPSG4326_2026-04-01.geojson"
gdf = gpd.read_file(geojson_path)
gdf = gdf.merge(soil_df, on='field_id', how='left')

# Get largest field center
gdf['area_calc'] = gdf.geometry.area
largest = gdf.nlargest(1, 'area_calc').iloc[0]
center_lat = largest.geometry.centroid.y
center_lon = largest.geometry.centroid.x

# Color functions
def get_color_ph(value):
    if pd.isna(value):
        return '#cccccc'
    norm = (value - 4.5) / (6.5 - 4.5)
    if norm < 0.2: return '#ffffb2'
    elif norm < 0.4: return '#fecc5c'
    elif norm < 0.6: return '#fd8d3c'
    elif norm < 0.8: return '#f03b20'
    else: return '#bd0026'

def get_color_om(value):
    if pd.isna(value):
        return '#cccccc'
    norm = (value - 0.5) / (2.2 - 0.5)
    if norm < 0.2: return '#ffffe5'
    elif norm < 0.4: return '#c7e9b4'
    elif norm < 0.6: return '#7bccc4'
    elif norm < 0.8: return '#41b6c4'
    else: return '#1d91c0'

def get_color_cec(value):
    if pd.isna(value):
        return '#cccccc'
    norm = (value - 2.5) / (14.0 - 2.5)
    if norm < 0.2: return '#ffffd9'
    elif norm < 0.4: return '#c7e9b4'
    elif norm < 0.6: return '#41b6c4'
    elif norm < 0.8: return '#225ea8'
    else: return '#0c2c84'

def get_color_aws(value):
    if pd.isna(value):
        return '#cccccc'
    norm = (value - 0.5) / (9.0 - 0.5)
    if norm < 0.2: return '#ffffb2'
    elif norm < 0.4: return '#fecc5c'
    elif norm < 0.6: return '#fd8d3c'
    elif norm < 0.8: return '#f03b20'
    else: return '#bd0026'

# Style functions
style_ph = lambda x: {'fillColor': get_color_ph(x['properties'].get('avg_ph')), 'color': 'black', 'weight': 1, 'fillOpacity': 0.7}
style_om = lambda x: {'fillColor': get_color_om(x['properties'].get('avg_om_pct')), 'color': 'black', 'weight': 1, 'fillOpacity': 0.7}
style_cec = lambda x: {'fillColor': get_color_cec(x['properties'].get('avg_cec')), 'color': 'black', 'weight': 1, 'fillOpacity': 0.7}
style_aws = lambda x: {'fillColor': get_color_aws(x['properties'].get('total_aws_inches')), 'color': 'black', 'weight': 1, 'fillOpacity': 0.7}

# Tooltip
tooltip_fields = ['field_id', 'crop_name', 'area_acres', 'avg_ph', 'avg_om_pct', 'avg_cec', 'total_aws_inches']
tooltip_aliases = ['Field ID:', 'Crop:', 'Area (acres):', 'pH:', 'OM (%):', 'CEC:', 'AWS (in):']

# Convert to GeoJSON
gdf_json = json.loads(gdf.to_json())

# ======== MAP 1: Soil Characteristics ========
m = folium.Map(location=[center_lat, center_lon], zoom_start=11, tiles='cartodbpositron')

fg_ph = folium.FeatureGroup(name='Soil pH (default)', show=True)
fg_om = folium.FeatureGroup(name='Organic Matter (%)', show=False)
fg_cec = folium.FeatureGroup(name='CEC (meq/100g)', show=False)
fg_aws = folium.FeatureGroup(name='Available Water Storage', show=False)

folium.GeoJson(gdf_json, style_function=style_ph, tooltip=folium.GeoJsonTooltip(fields=tooltip_fields, aliases=tooltip_aliases)).add_to(fg_ph)
folium.GeoJson(gdf_json, style_function=style_om, tooltip=folium.GeoJsonTooltip(fields=tooltip_fields, aliases=tooltip_aliases)).add_to(fg_om)
folium.GeoJson(gdf_json, style_function=style_cec, tooltip=folium.GeoJsonTooltip(fields=tooltip_fields, aliases=tooltip_aliases)).add_to(fg_cec)
folium.GeoJson(gdf_json, style_function=style_aws, tooltip=folium.GeoJsonTooltip(fields=tooltip_fields, aliases=tooltip_aliases)).add_to(fg_aws)

fg_ph.add_to(m)
fg_om.add_to(m)
fg_cec.add_to(m)
fg_aws.add_to(m)

folium.LayerControl(collapsed=False).add_to(m)

# Title
title_html = '''
<div style="position: fixed; top: 15px; left: 50%; transform: translateX(-50%); z-index: 9999; 
            background-color: white; padding: 12px 25px; border-radius: 5px; 
            box-shadow: 2px 2px 5px rgba(0,0,0,0.3);">
    <h2 style="margin: 0; font-size: 22px; font-weight: 700; font-family: Arial, sans-serif;">
        NC Field Soil Characteristics
    </h2>
</div>
'''
m.get_root().html.add_child(folium.Element(title_html))

# Legend with larger font
legend_html = f'''
<div style="position: fixed; bottom: 30px; left: 30px; z-index: 9999; 
            background-color: white; padding: 15px; border-radius: 5px; 
            box-shadow: 0 0 15px rgba(0,0,0,0.2); font-family: Arial, sans-serif; 
            font-size: 13px; min-width: 220px;">
    <div style="margin-bottom: 8px;">
        <strong>Layer:</strong>
        <select id="layer-select" onchange="switchLayer(this.value)" style="margin-left: 5px; padding: 4px;">
            <option value="ph">Soil pH</option>
            <option value="om">Organic Matter (%)</option>
            <option value="cec">CEC (meq/100g)</option>
            <option value="aws">Water Storage (in)</option>
        </select>
    </div>
    <div id="legend-content">
        <div id="legend-ph-content">
            <strong>Soil pH</strong><br>
            <span style="background: #bd0026; color: white; padding: 3px 8px; margin-right: 3px;">6.5</span>
            <span style="background: #f03b20; color: white; padding: 3px 8px; margin-right: 3px;">5.5</span>
            <span style="background: #fd8d3c; color: white; padding: 3px 8px; margin-right: 3px;">5.0</span>
            <span style="background: #fecc5c; padding: 3px 8px; margin-right: 3px;">5.0</span>
            <span style="background: #ffffb2; padding: 3px 8px;">4.5</span><br>
            <span style="color: #666; font-size: 11px;">Alkaline ← → Acidic</span>
        </div>
        <div id="legend-om-content" style="display: none;">
            <strong>Organic Matter (%)</strong><br>
            <span style="background: #1d91c0; color: white; padding: 3px 8px; margin-right: 3px;">2.2</span>
            <span style="background: #41b6c4; color: white; padding: 3px 8px; margin-right: 3px;">1.7</span>
            <span style="background: #7bccc4; color: white; padding: 3px 8px; margin-right: 3px;">1.3</span>
            <span style="background: #c7e9b4; padding: 3px 8px; margin-right: 3px;">0.9</span>
            <span style="background: #ffffe5; padding: 3px 8px;">0.5</span><br>
            <span style="color: #666; font-size: 11px;">High ← → Low</span>
        </div>
        <div id="legend-cec-content" style="display: none;">
            <strong>CEC (meq/100g)</strong><br>
            <span style="background: #0c2c84; color: white; padding: 3px 8px; margin-right: 3px;">14.0</span>
            <span style="background: #225ea8; color: white; padding: 3px 8px; margin-right: 3px;">11.1</span>
            <span style="background: #41b6c4; color: white; padding: 3px 8px; margin-right: 3px;">8.2</span>
            <span style="background: #c7e9b4; padding: 3px 8px; margin-right: 3px;">5.4</span>
            <span style="background: #ffffd9; padding: 3px 8px;">2.5</span><br>
            <span style="color: #666; font-size: 11px;">High ← → Low</span>
        </div>
        <div id="legend-aws-content" style="display: none;">
            <strong>Water Storage (inches)</strong><br>
            <span style="background: #bd0026; color: white; padding: 3px 8px; margin-right: 3px;">9.0</span>
            <span style="background: #f03b20; color: white; padding: 3px 8px; margin-right: 3px;">7.0</span>
            <span style="background: #fd8d3c; color: white; padding: 3px 8px; margin-right: 3px;">4.8</span>
            <span style="background: #fecc5c; padding: 3px 8px; margin-right: 3px;">2.6</span>
            <span style="background: #ffffb2; padding: 3px 8px;">0.5</span><br>
            <span style="color: #666; font-size: 11px;">High ← → Low</span>
        </div>
    </div>
</div>
'''
m.get_root().html.add_child(folium.Element(legend_html))

# JS for layer switching
script = '''
<script>
var layerFeatureGroups = {
    'ph': feature_group_da504d4c2024ed4f9db78e67f8ff3079,
    'om': feature_group_89c634f0322a21d3c7da9a947a9c53ce,
    'cec': feature_group_8417e4d27bd8194064f9186bbc89b8ad,
    'aws': feature_group_822e8eed082adbd390b0297507a15d25
};

function switchLayer(layer) {
    document.getElementById('legend-ph-content').style.display = 'none';
    document.getElementById('legend-om-content').style.display = 'none';
    document.getElementById('legend-cec-content').style.display = 'none';
    document.getElementById('legend-aws-content').style.display = 'none';
    document.getElementById('legend-' + layer + '-content').style.display = 'block';
}
</script>
'''

m.save(DASH_DIR / 'farm_field_map_dashboard.html')
print(f"Saved: {DASH_DIR / 'farm_field_map_dashboard.html'}")

# ======== MAP 2: Soil Components ========
# Color functions for components
def get_color_clay(value):
    if pd.isna(value):
        return '#cccccc'
    norm = (value - 5) / (40 - 5)
    if norm < 0.2: return '#ffffd9'
    elif norm < 0.4: return '#c7e9b4'
    elif norm < 0.6: return '#41b6c4'
    elif norm < 0.8: return '#225ea8'
    else: return '#0c2c84'

def get_color_sand(value):
    if pd.isna(value):
        return '#cccccc'
    norm = (value - 20) / (90 - 20)
    if norm < 0.2: return '#0c2c84'
    elif norm < 0.4: return '#225ea8'
    elif norm < 0.6: return '#41b6c4'
    elif norm < 0.8: return '#c7e9b4'
    else: return '#ffffd9'

def get_color_silt(value):
    if pd.isna(value):
        return '#cccccc'
    norm = (value - 5) / (55 - 5)
    if norm < 0.2: return '#ffffd9'
    elif norm < 0.4: return '#c7e9b4'
    elif norm < 0.6: return '#7bccc4'
    elif norm < 0.8: return '#1d91c0'
    else: return '#0c2c84'

style_clay = lambda x: {'fillColor': get_color_clay(x['properties'].get('avg_clay_pct')), 'color': 'black', 'weight': 1, 'fillOpacity': 0.7}
style_sand = lambda x: {'fillColor': get_color_sand(x['properties'].get('avg_sand_pct')), 'color': 'black', 'weight': 1, 'fillOpacity': 0.7}
style_silt = lambda x: {'fillColor': get_color_silt(x['properties'].get('avg_silt_pct')), 'color': 'black', 'weight': 1, 'fillOpacity': 0.7}

tooltip_fields2 = ['field_id', 'crop_name', 'area_acres', 'avg_clay_pct', 'avg_sand_pct', 'avg_silt_pct']
tooltip_aliases2 = ['Field ID:', 'Crop:', 'Area (acres):', 'Clay (%):', 'Sand (%):', 'Silt (%):']

m2 = folium.Map(location=[center_lat, center_lon], zoom_start=11, tiles='cartodbpositron')

fg_clay = folium.FeatureGroup(name='Clay (%)', show=True)
fg_sand = folium.FeatureGroup(name='Sand (%)', show=False)
fg_silt = folium.FeatureGroup(name='Silt (%)', show=False)

folium.GeoJson(gdf_json, style_function=style_clay, tooltip=folium.GeoJsonTooltip(fields=tooltip_fields2, aliases=tooltip_aliases2)).add_to(fg_clay)
folium.GeoJson(gdf_json, style_function=style_sand, tooltip=folium.GeoJsonTooltip(fields=tooltip_fields2, aliases=tooltip_aliases2)).add_to(fg_sand)
folium.GeoJson(gdf_json, style_function=style_silt, tooltip=folium.GeoJsonTooltip(fields=tooltip_fields2, aliases=tooltip_aliases2)).add_to(fg_silt)

fg_clay.add_to(m2)
fg_sand.add_to(m2)
fg_silt.add_to(m2)

folium.LayerControl(collapsed=False).add_to(m2)

# Title
title_html2 = '''
<div style="position: fixed; top: 15px; left: 50%; transform: translateX(-50%); z-index: 9999; 
            background-color: white; padding: 12px 25px; border-radius: 5px; 
            box-shadow: 2px 2px 5px rgba(0,0,0,0.3);">
    <h2 style="margin: 0; font-size: 22px; font-weight: 700; font-family: Arial, sans-serif;">
        NC Field Soil Texture Components
    </h2>
</div>
'''
m2.get_root().html.add_child(folium.Element(title_html2))

# Legend
legend_html2 = '''
<div style="position: fixed; bottom: 30px; left: 30px; z-index: 9999; 
            background-color: white; padding: 15px; border-radius: 5px; 
            box-shadow: 0 0 15px rgba(0,0,0,0.2); font-family: Arial, sans-serif; 
            font-size: 13px; min-width: 220px;">
    <div style="margin-bottom: 8px;">
        <strong>Layer:</strong>
        <select id="layer-select" onchange="switchLayer(this.value)" style="margin-left: 5px; padding: 4px;">
            <option value="clay">Clay (%)</option>
            <option value="sand">Sand (%)</option>
            <option value="silt">Silt (%)</option>
        </select>
    </div>
    <div id="legend-content">
        <div id="legend-clay-content">
            <strong>Clay (%)</strong><br>
            <span style="background: #0c2c84; color: white; padding: 3px 8px; margin-right: 3px;">40</span>
            <span style="background: #225ea8; color: white; padding: 3px 8px; margin-right: 3px;">32</span>
            <span style="background: #41b6c4; color: white; padding: 3px 8px; margin-right: 3px;">23</span>
            <span style="background: #c7e9b4; padding: 3px 8px; margin-right: 3px;">14</span>
            <span style="background: #ffffd9; padding: 3px 8px;">5</span><br>
            <span style="color: #666; font-size: 11px;">High ← → Low</span>
        </div>
        <div id="legend-sand-content" style="display: none;">
            <strong>Sand (%)</strong><br>
            <span style="background: #ffffd9; padding: 3px 8px; margin-right: 3px;">20</span>
            <span style="background: #c7e9b4; padding: 3px 8px; margin-right: 3px;">38</span>
            <span style="background: #41b6c4; color: white; padding: 3px 8px; margin-right: 3px;">55</span>
            <span style="background: #225ea8; color: white; padding: 3px 8px; margin-right: 3px;">72</span>
            <span style="background: #0c2c84; color: white; padding: 3px 8px;">90</span><br>
            <span style="color: #666; font-size: 11px;">Low ← → High</span>
        </div>
        <div id="legend-silt-content" style="display: none;">
            <strong>Silt (%)</strong><br>
            <span style="background: #0c2c84; color: white; padding: 3px 8px; margin-right: 3px;">55</span>
            <span style="background: #1d91c0; color: white; padding: 3px 8px; margin-right: 3px;">44</span>
            <span style="background: #7bccc4; color: white; padding: 3px 8px; margin-right: 3px;">32</span>
            <span style="background: #c7e9b4; padding: 3px 8px; margin-right: 3px;">21</span>
            <span style="background: #ffffd9; padding: 3px 8px;">5</span><br>
            <span style="color: #666; font-size: 11px;">High ← → Low</span>
        </div>
    </div>
</div>
'''
m2.get_root().html.add_child(folium.Element(legend_html2))

m2.save(DASH_DIR / 'farm_field_soil_components_dashboard.html')
print(f"Saved: {DASH_DIR / 'farm_field_soil_components_dashboard.html'}")

print("\nDashboard HTML files created successfully!")
print(f"Directory: {DASH_DIR}")
print(f"Center: lat={center_lat:.4f}, lon={center_lon:.4f}")
print(f"Zoom: 11 (vs default 8)")
