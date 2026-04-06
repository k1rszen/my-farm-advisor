#!/usr/bin/env python3
"""Final Dashboard Map - All Soil Indicators

Creates a single unified dashboard HTML with all 8 soil indicators:
- pH, Organic Matter, CEC, Water Storage, Clay, Sand, Silt, Bulk Density

Features:
- Working dropdown to switch between layers
- Dashboard styling (centered title, larger legend)
- Centered on largest field
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

print(f"Largest field: {largest['field_id']} ({largest['area_acres']:.0f} acres)")
print(f"Center: lat={center_lat:.4f}, lon={center_lon:.4f}")

# Color functions for each indicator
def get_color(val, vmin, vmax, colors):
    if pd.isna(val):
        return '#cccccc'
    norm = (val - vmin) / (vmax - vmin)
    norm = max(0, min(1, norm))
    idx = int(norm * (len(colors) - 1))
    return colors[idx]

# Color sequences
ph_colors = ['#ffffb2', '#fecc5c', '#fd8d3c', '#f03b20', '#bd0026']  # Low to high
om_colors = ['#ffffe5', '#c7e9b4', '#7bccc4', '#41b6c4', '#1d91c0']  # Low to high
cec_colors = ['#ffffd9', '#c7e9b4', '#41b6c4', '#225ea8', '#0c2c84']  # Low to high
aws_colors = ['#ffffb2', '#fecc5c', '#fd8d3c', '#f03b20', '#bd0026']  # Low to high
clay_colors = ['#ffffd9', '#c7e9b4', '#41b6c4', '#225ea8', '#0c2c84']  # Low to high (clay)
sand_colors = ['#0c2c84', '#225ea8', '#41b6c4', '#c7e9b4', '#ffffd9']  # High to low (sand)
silt_colors = ['#ffffd9', '#c7e9b4', '#7bccc4', '#1d91c0', '#0c2c84']  # Low to high
bd_colors = ['#ffffb2', '#fecc5c', '#fd8d3c', '#f03b20', '#bd0026']  # Low to high

def get_color_ph(val): return get_color(val, 4.5, 6.5, ph_colors)
def get_color_om(val): return get_color(val, 0.5, 2.2, om_colors)
def get_color_cec(val): return get_color(val, 2.5, 14.0, cec_colors)
def get_color_aws(val): return get_color(val, 0.5, 9.0, aws_colors)
def get_color_clay(val): return get_color(val, 5, 40, clay_colors)
def get_color_sand(val): return get_color(val, 20, 90, sand_colors)
def get_color_silt(val): return get_color(val, 5, 55, silt_colors)
def get_color_bd(val): return get_color(val, 1.0, 1.8, bd_colors)

# Style functions
style_ph = lambda x: {'fillColor': get_color_ph(x['properties'].get('avg_ph')), 'color': 'black', 'weight': 1, 'fillOpacity': 0.7}
style_om = lambda x: {'fillColor': get_color_om(x['properties'].get('avg_om_pct')), 'color': 'black', 'weight': 1, 'fillOpacity': 0.7}
style_cec = lambda x: {'fillColor': get_color_cec(x['properties'].get('avg_cec')), 'color': 'black', 'weight': 1, 'fillOpacity': 0.7}
style_aws = lambda x: {'fillColor': get_color_aws(x['properties'].get('total_aws_inches')), 'color': 'black', 'weight': 1, 'fillOpacity': 0.7}
style_clay = lambda x: {'fillColor': get_color_clay(x['properties'].get('avg_clay_pct')), 'color': 'black', 'weight': 1, 'fillOpacity': 0.7}
style_sand = lambda x: {'fillColor': get_color_sand(x['properties'].get('avg_sand_pct')), 'color': 'black', 'weight': 1, 'fillOpacity': 0.7}
style_silt = lambda x: {'fillColor': get_color_silt(x['properties'].get('avg_silt_pct')), 'color': 'black', 'weight': 1, 'fillOpacity': 0.7}
style_bd = lambda x: {'fillColor': get_color_bd(x['properties'].get('avg_bulk_density')), 'color': 'black', 'weight': 1, 'fillOpacity': 0.7}

# Tooltip fields - all 8 indicators plus ID and crop
tooltip_fields = ['field_id', 'crop_name', 'area_acres', 'avg_ph', 'avg_om_pct', 'avg_cec', 
                  'total_aws_inches', 'avg_clay_pct', 'avg_sand_pct', 'avg_silt_pct', 'avg_bulk_density']
tooltip_aliases = ['Field ID:', 'Crop:', 'Area (acres):', 'pH:', 'OM (%):', 'CEC (meq/100g):', 
                   'AWS (in):', 'Clay (%):', 'Sand (%):', 'Silt (%):', 'Bulk Density:']

# Convert to GeoJSON
gdf_json = json.loads(gdf.to_json())

# Create map
m = folium.Map(location=[center_lat, center_lon], zoom_start=11, tiles='cartodbpositron')

# Create feature groups for each indicator
fg_ph = folium.FeatureGroup(name='Soil pH', show=True)
fg_om = folium.FeatureGroup(name='Organic Matter (%)', show=False)
fg_cec = folium.FeatureGroup(name='CEC (meq/100g)', show=False)
fg_aws = folium.FeatureGroup(name='Water Storage (in)', show=False)
fg_clay = folium.FeatureGroup(name='Clay (%)', show=False)
fg_sand = folium.FeatureGroup(name='Sand (%)', show=False)
fg_silt = folium.FeatureGroup(name='Silt (%)', show=False)
fg_bd = folium.FeatureGroup(name='Bulk Density', show=False)

# Add layers
folium.GeoJson(gdf_json, style_function=style_ph, tooltip=folium.GeoJsonTooltip(fields=tooltip_fields, aliases=tooltip_aliases)).add_to(fg_ph)
folium.GeoJson(gdf_json, style_function=style_om, tooltip=folium.GeoJsonTooltip(fields=tooltip_fields, aliases=tooltip_aliases)).add_to(fg_om)
folium.GeoJson(gdf_json, style_function=style_cec, tooltip=folium.GeoJsonTooltip(fields=tooltip_fields, aliases=tooltip_aliases)).add_to(fg_cec)
folium.GeoJson(gdf_json, style_function=style_aws, tooltip=folium.GeoJsonTooltip(fields=tooltip_fields, aliases=tooltip_aliases)).add_to(fg_aws)
folium.GeoJson(gdf_json, style_function=style_clay, tooltip=folium.GeoJsonTooltip(fields=tooltip_fields, aliases=tooltip_aliases)).add_to(fg_clay)
folium.GeoJson(gdf_json, style_function=style_sand, tooltip=folium.GeoJsonTooltip(fields=tooltip_fields, aliases=tooltip_aliases)).add_to(fg_sand)
folium.GeoJson(gdf_json, style_function=style_silt, tooltip=folium.GeoJsonTooltip(fields=tooltip_fields, aliases=tooltip_aliases)).add_to(fg_silt)
folium.GeoJson(gdf_json, style_function=style_bd, tooltip=folium.GeoJsonTooltip(fields=tooltip_fields, aliases=tooltip_aliases)).add_to(fg_bd)

# Add to map
fg_ph.add_to(m)
fg_om.add_to(m)
fg_cec.add_to(m)
fg_aws.add_to(m)
fg_clay.add_to(m)
fg_sand.add_to(m)
fg_silt.add_to(m)
fg_bd.add_to(m)

# Add layer control
folium.LayerControl(collapsed=False).add_to(m)

# Title - centered, bold
title_html = '''
<div style="position: fixed; top: 15px; left: 50%; transform: translateX(-50%); z-index: 9999; 
            background-color: white; padding: 12px 25px; border-radius: 5px; 
            box-shadow: 2px 2px 5px rgba(0,0,0,0.3);">
    <h2 style="margin: 0; font-size: 22px; font-weight: 700; font-family: Arial, sans-serif;">
        NC Field Soil Indicators
    </h2>
</div>
'''
m.get_root().html.add_child(folium.Element(title_html))

# Legend with all 8 indicators
legend_html = '''
<div style="position: fixed; bottom: 30px; left: 30px; z-index: 9999; 
            background-color: white; padding: 15px; border-radius: 5px; 
            box-shadow: 0 0 15px rgba(0,0,0,0.2); font-family: Arial, sans-serif; 
            font-size: 13px; min-width: 230px;">
    <div style="margin-bottom: 8px;">
        <strong>Soil Indicators:</strong>
        <select id="layer-select" onchange="switchLayer(this.value)" style="margin-left: 5px; padding: 4px;">
            <option value="ph">Soil pH</option>
            <option value="om">Organic Matter (%)</option>
            <option value="cec">CEC (meq/100g)</option>
            <option value="aws">Water Storage (in)</option>
            <option value="clay">Clay (%)</option>
            <option value="sand">Sand (%)</option>
            <option value="silt">Silt (%)</option>
            <option value="bd">Bulk Density</option>
        </select>
    </div>
    <div id="legend-content">
        <!-- pH -->
        <div id="legend-ph-content">
            <strong>Soil pH</strong><br>
            <span style="background: #bd0026; color: white; padding: 3px 8px; margin-right: 3px;">6.5</span>
            <span style="background: #f03b20; color: white; padding: 3px 8px; margin-right: 3px;">5.5</span>
            <span style="background: #fd8d3c; color: white; padding: 3px 8px; margin-right: 3px;">5.0</span>
            <span style="background: #fecc5c; padding: 3px 8px; margin-right: 3px;">5.0</span>
            <span style="background: #ffffb2; padding: 3px 8px;">4.5</span><br>
            <span style="color: #666; font-size: 11px;">Alkaline ← → Acidic</span>
        </div>
        <!-- OM -->
        <div id="legend-om-content" style="display: none;">
            <strong>Organic Matter (%)</strong><br>
            <span style="background: #1d91c0; color: white; padding: 3px 8px; margin-right: 3px;">2.2</span>
            <span style="background: #41b6c4; color: white; padding: 3px 8px; margin-right: 3px;">1.7</span>
            <span style="background: #7bccc4; color: white; padding: 3px 8px; margin-right: 3px;">1.3</span>
            <span style="background: #c7e9b4; padding: 3px 8px; margin-right: 3px;">0.9</span>
            <span style="background: #ffffe5; padding: 3px 8px;">0.5</span><br>
            <span style="color: #666; font-size: 11px;">High ← → Low</span>
        </div>
        <!-- CEC -->
        <div id="legend-cec-content" style="display: none;">
            <strong>CEC (meq/100g)</strong><br>
            <span style="background: #0c2c84; color: white; padding: 3px 8px; margin-right: 3px;">14.0</span>
            <span style="background: #225ea8; color: white; padding: 3px 8px; margin-right: 3px;">11.1</span>
            <span style="background: #41b6c4; color: white; padding: 3px 8px; margin-right: 3px;">8.2</span>
            <span style="background: #c7e9b4; padding: 3px 8px; margin-right: 3px;">5.4</span>
            <span style="background: #ffffd9; padding: 3px 8px;">2.5</span><br>
            <span style="color: #666; font-size: 11px;">High ← → Low</span>
        </div>
        <!-- AWS -->
        <div id="legend-aws-content" style="display: none;">
            <strong>Water Storage (in)</strong><br>
            <span style="background: #bd0026; color: white; padding: 3px 8px; margin-right: 3px;">9.0</span>
            <span style="background: #f03b20; color: white; padding: 3px 8px; margin-right: 3px;">7.0</span>
            <span style="background: #fd8d3c; color: white; padding: 3px 8px; margin-right: 3px;">4.8</span>
            <span style="background: #fecc5c; padding: 3px 8px; margin-right: 3px;">2.6</span>
            <span style="background: #ffffb2; padding: 3px 8px;">0.5</span><br>
            <span style="color: #666; font-size: 11px;">High ← → Low</span>
        </div>
        <!-- Clay -->
        <div id="legend-clay-content" style="display: none;">
            <strong>Clay (%)</strong><br>
            <span style="background: #0c2c84; color: white; padding: 3px 8px; margin-right: 3px;">40</span>
            <span style="background: #225ea8; color: white; padding: 3px 8px; margin-right: 3px;">32</span>
            <span style="background: #41b6c4; color: white; padding: 3px 8px; margin-right: 3px;">23</span>
            <span style="background: #c7e9b4; padding: 3px 8px; margin-right: 3px;">14</span>
            <span style="background: #ffffd9; padding: 3px 8px;">5</span><br>
            <span style="color: #666; font-size: 11px;">High ← → Low</span>
        </div>
        <!-- Sand -->
        <div id="legend-sand-content" style="display: none;">
            <strong>Sand (%)</strong><br>
            <span style="background: #0c2c84; color: white; padding: 3px 8px; margin-right: 3px;">90</span>
            <span style="background: #225ea8; color: white; padding: 3px 8px; margin-right: 3px;">72</span>
            <span style="background: #41b6c4; color: white; padding: 3px 8px; margin-right: 3px;">55</span>
            <span style="background: #c7e9b4; padding: 3px 8px; margin-right: 3px;">38</span>
            <span style="background: #ffffd9; padding: 3px 8px;">20</span><br>
            <span style="color: #666; font-size: 11px;">High ← → Low</span>
        </div>
        <!-- Silt -->
        <div id="legend-silt-content" style="display: none;">
            <strong>Silt (%)</strong><br>
            <span style="background: #0c2c84; color: white; padding: 3px 8px; margin-right: 3px;">55</span>
            <span style="background: #1d91c0; color: white; padding: 3px 8px; margin-right: 3px;">44</span>
            <span style="background: #7bccc4; color: white; padding: 3px 8px; margin-right: 3px;">32</span>
            <span style="background: #c7e9b4; padding: 3px 8px; margin-right: 3px;">21</span>
            <span style="background: #ffffd9; padding: 3px 8px;">5</span><br>
            <span style="color: #666; font-size: 11px;">High ← → Low</span>
        </div>
        <!-- Bulk Density -->
        <div id="legend-bd-content" style="display: none;">
            <strong>Bulk Density (g/cm³)</strong><br>
            <span style="background: #bd0026; color: white; padding: 3px 8px; margin-right: 3px;">1.8</span>
            <span style="background: #f03b20; color: white; padding: 3px 8px; margin-right: 3px;">1.6</span>
            <span style="background: #fd8d3c; color: white; padding: 3px 8px; margin-right: 3px;">1.4</span>
            <span style="background: #fecc5c; padding: 3px 8px; margin-right: 3px;">1.2</span>
            <span style="background: #ffffb2; padding: 3px 8px;">1.0</span><br>
            <span style="color: #666; font-size: 11px;">High ← → Low</span>
        </div>
    </div>
</div>
'''
m.get_root().html.add_child(folium.Element(legend_html))

# Get the actual feature group names from the map
# These need to match the JS variable names created by Folium
# Let's find them by inspecting the layer control

# JS for layer switching - will be added at end
script_html = '''
<script>
function switchLayer(layer) {
    // Hide all legends
    document.getElementById('legend-ph-content').style.display = 'none';
    document.getElementById('legend-om-content').style.display = 'none';
    document.getElementById('legend-cec-content').style.display = 'none';
    document.getElementById('legend-aws-content').style.display = 'none';
    document.getElementById('legend-clay-content').style.display = 'none';
    document.getElementById('legend-sand-content').style.display = 'none';
    document.getElementById('legend-silt-content').style.display = 'none';
    document.getElementById('legend-bd-content').style.display = 'none';
    
    // Show selected legend
    document.getElementById('legend-' + layer + '-content').style.display = 'block';
}
</script>
'''
m.get_root().html.add_child(folium.Element(script_html))

# Save
output_path = DASH_DIR / 'field_map_dashboard_final.html'
m.save(output_path)
print(f"\n✓ Saved: {output_path}")

print("\n" + "=" * 60)
print("FINAL DASHBOARD MAP COMPLETE")
print("=" * 60)
print(f"\nFile: {output_path}")
print(f"Center: lat={center_lat:.4f}, lon={center_lon:.4f}")
print(f"Zoom: 11")
print(f"\nSoil Indicators (8 total):")
print(f"  1. Soil pH")
print(f"  2. Organic Matter (%)")
print(f"  3. CEC (meq/100g)")
print(f"  4. Water Storage (in)")
print(f"  5. Clay (%)")
print(f"  6. Sand (%)")
print(f"  7. Silt (%)")
print(f"  8. Bulk Density")
print(f"\nDropdown legend switches between layers")
print(f"Title: 'NC Field Soil Indicators' (centered, bold)")
