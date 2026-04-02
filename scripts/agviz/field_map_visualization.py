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

# Get bounds for north arrow placement
bounds = gdf.total_bounds

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
    
    # Add field labels (acres) at centroids
    centroids = gdf.geometry.centroid
    for geom, acres in zip(centroids, gdf['area_acres']):
        if pd.notna(acres):
            ax.annotate(f"{acres:.0f}", xy=(geom.x, geom.y), fontsize=6, ha='center', va='center',
                       color='black', weight='bold', 
                       bbox=dict(boxstyle='round,pad=0.2', facecolor='white', alpha=0.7, edgecolor='none'))
    
    ax.set_title(props['label'], fontsize=12, fontweight='bold')
    ax.set_xlabel('Longitude')
    ax.set_ylabel('Latitude')
    ax.set_axis_off()
    
    # Add north arrow (top-right of each subplot)
    ax.annotate('N', xy=(0.95, 0.95), xycoords='axes fraction', fontsize=14, fontweight='bold',
               ha='center', va='bottom', color='black',
               arrowprops=dict(arrowstyle='->', lw=1.5, color='black'))

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

# Add labels to features - create copy with label property
gdf_labeled = gdf.copy()
gdf_labeled['label'] = gdf_labeled['area_acres'].apply(lambda x: f"{x:.0f} ac" if pd.notna(x) else "")
gdf_json = json.loads(gdf_labeled.to_json())

# Feature groups
fg_ph = folium.FeatureGroup(name='Soil pH (default)', show=True)
fg_om = folium.FeatureGroup(name='Organic Matter (%)', show=False)
fg_cec = folium.FeatureGroup(name='CEC (meq/100g)', show=False)
fg_aws = folium.FeatureGroup(name='Available Water Storage', show=False)

# Add layers with labels
folium.GeoJson(gdf_json, style_function=style_ph, tooltip=folium.GeoJsonTooltip(fields=tooltip_fields, aliases=tooltip_aliases),
               labels=True).add_to(fg_ph)
folium.GeoJson(gdf_json, style_function=style_om, tooltip=folium.GeoJsonTooltip(fields=tooltip_fields, aliases=tooltip_aliases),
               labels=True).add_to(fg_om)
folium.GeoJson(gdf_json, style_function=style_cec, tooltip=folium.GeoJsonTooltip(fields=tooltip_fields, aliases=tooltip_aliases),
               labels=True).add_to(fg_cec)
folium.GeoJson(gdf_json, style_function=style_aws, tooltip=folium.GeoJsonTooltip(fields=tooltip_fields, aliases=tooltip_aliases),
               labels=True).add_to(fg_aws)

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

# Add north arrow (top-right)
north_arrow_html = '''
<div style="position: fixed; top: 10px; right: 10px; z-index: 9999; background-color: white; padding: 8px; border-radius: 5px; box-shadow: 2px 2px 5px rgba(0,0,0,0.3);">
    <div style="text-align: center;">
        <span style="font-size: 20px;">⬆</span><br>
        <span style="font-size: 10px; font-weight: bold;">N</span>
    </div>
</div>
'''
m.get_root().html.add_child(folium.Element(north_arrow_html))

# Legend definitions for each layer
legends = {
    'ph': {
        'title': 'Soil pH',
        'colors': ['#ffffb2', '#fecc5c', '#fd8d3c', '#f03b20', '#bd0026'],
        'labels': ['4.5 (Acidic)', '5.0', '5.5', '6.0', '6.5 (Alkaline)']
    },
    'om': {
        'title': 'Organic Matter (%)',
        'colors': ['#ffffe5', '#c7e9b4', '#7bccc4', '#41b6c4', '#1d91c0'],
        'labels': ['0.5% (Low)', '0.9%', '1.3%', '1.7%', '2.2% (High)']
    },
    'cec': {
        'title': 'CEC (meq/100g)',
        'colors': ['#ffffd9', '#c7e9b4', '#41b6c4', '#225ea8', '#0c2c84'],
        'labels': ['2.5 (Low)', '5.4', '8.2', '11.1', '14.0 (High)']
    },
    'aws': {
        'title': 'Available Water Storage (in)',
        'colors': ['#ffffb2', '#fecc5c', '#fd8d3c', '#f03b20', '#bd0026'],
        'labels': ['0.5 (Low)', '2.6', '4.8', '7.0', '9.0 (High)']
    }
}

# Add legend for each layer using StyleMap with LegendControl pattern
# Add CSS for legends
legend_css = '''
<style>
.legend {padding: 6px 8px;font: 12px Arial, Helvetica, sans-serif;background: white;box-shadow: 0 0 15px rgba(0,0,0,0.2);border-radius: 5px;line-height: 18px;color: #555;}
.legend-title {font-weight: bold;margin-bottom: 5px;}
.legend-color {height: 18px;width: 18px;float: left;margin-right: 8px;opacity: 0.8;border-radius: 3px;}
</style>
'''

# Add legend for pH layer (default visible)
ph_legend = f'''
<div id="legend-ph" class="folium-map" style="display: block;">
    <div class="legend" style="position: fixed; bottom: 30px; left: 30px; z-index: 9999;">
        <div class="legend-title">{legends['ph']['title']}</div>
        <div><div class="legend-color" style="background: {legends['ph']['colors'][4]};"></div>{legends['ph']['labels'][4]}</div>
        <div><div class="legend-color" style="background: {legends['ph']['colors'][3]};"></div>{legends['ph']['labels'][3]}</div>
        <div><div class="legend-color" style="background: {legends['ph']['colors'][2]};"></div>{legends['ph']['labels'][2]}</div>
        <div><div class="legend-color" style="background: {legends['ph']['colors'][1]};"></div>{legends['ph']['labels'][1]}</div>
        <div><div class="legend-color" style="background: {legends['ph']['colors'][0]};"></div>{legends['ph']['labels'][0]}</div>
    </div>
</div>
'''

om_legend = f'''
<div id="legend-om" class="folium-map" style="display: none;">
    <div class="legend" style="position: fixed; bottom: 30px; left: 30px; z-index: 9999;">
        <div class="legend-title">{legends['om']['title']}</div>
        <div><div class="legend-color" style="background: {legends['om']['colors'][4]};"></div>{legends['om']['labels'][4]}</div>
        <div><div class="legend-color" style="background: {legends['om']['colors'][3]};"></div>{legends['om']['labels'][3]}</div>
        <div><div class="legend-color" style="background: {legends['om']['colors'][2]};"></div>{legends['om']['labels'][2]}</div>
        <div><div class="legend-color" style="background: {legends['om']['colors'][1]};"></div>{legends['om']['labels'][1]}</div>
        <div><div class="legend-color" style="background: {legends['om']['colors'][0]};"></div>{legends['om']['labels'][0]}</div>
    </div>
</div>
'''

cec_legend = f'''
<div id="legend-cec" class="folium-map" style="display: none;">
    <div class="legend" style="position: fixed; bottom: 30px; left: 30px; z-index: 9999;">
        <div class="legend-title">{legends['cec']['title']}</div>
        <div><div class="legend-color" style="background: {legends['cec']['colors'][4]};"></div>{legends['cec']['labels'][4]}</div>
        <div><div class="legend-color" style="background: {legends['cec']['colors'][3]};"></div>{legends['cec']['labels'][3]}</div>
        <div><div class="legend-color" style="background: {legends['cec']['colors'][2]};"></div>{legends['cec']['labels'][2]}</div>
        <div><div class="legend-color" style="background: {legends['cec']['colors'][1]};"></div>{legends['cec']['labels'][1]}</div>
        <div><div class="legend-color" style="background: {legends['cec']['colors'][0]};"></div>{legends['cec']['labels'][0]}</div>
    </div>
</div>
'''

aws_legend = f'''
<div id="legend-aws" class="folium-map" style="display: none;">
    <div class="legend" style="position: fixed; bottom: 30px; left: 30px; z-index: 9999;">
        <div class="legend-title">{legends['aws']['title']}</div>
        <div><div class="legend-color" style="background: {legends['aws']['colors'][4]};"></div>{legends['aws']['labels'][4]}</div>
        <div><div class="legend-color" style="background: {legends['aws']['colors'][3]};"></div>{legends['aws']['labels'][3]}</div>
        <div><div class="legend-color" style="background: {legends['aws']['colors'][2]};"></div>{legends['aws']['labels'][2]}</div>
        <div><div class="legend-color" style="background: {legends['aws']['colors'][1]};"></div>{legends['aws']['labels'][1]}</div>
        <div><div class="legend-color" style="background: {legends['aws']['colors'][0]};"></div>{legends['aws']['labels'][0]}</div>
    </div>
</div>
'''

# Add legends and toggle logic
legend_script = f'''
<script>
{legend_css}
document.getElementById('map').appendChild(document.getElementById('legend-ph'));
document.getElementById('map').appendChild(document.getElementById('legend-om'));
document.getElementById('map').appendChild(document.getElementById('legend-cec'));
document.getElementById('map').appendChild(document.getElementById('legend-aws'));

function updateLegend(layerName) {{
    document.getElementById('legend-ph').style.display = 'none';
    document.getElementById('legend-om').style.display = 'none';
    document.getElementById('legend-cec').style.display = 'none';
    document.getElementById('legend-aws').style.display = 'none';
    
    if (layerName === 'Soil pH (default)') document.getElementById('legend-ph').style.display = 'block';
    else if (layerName === 'Organic Matter (%)') document.getElementById('legend-om').style.display = 'block';
    else if (layerName === 'CEC (meq/100g)') document.getElementById('legend-cec').style.display = 'block';
    else if (layerName === 'Available Water Storage') document.getElementById('legend-aws').style.display = 'block';
}}

// Override layer control to update legend
var originalOnRemove = L.Control.Layers.prototype._onRemoveLayerClick;
L.Control.Layers.prototype._onRemoveLayerClick = function(e) {{
    originalOnRemove.call(this, e);
    updateLegend(this._activeLayers()[0]);
}};

var originalOnAddLayer = L.Control.Layers.prototype._onAddLayerClick;
L.Control.Layers.prototype._onAddLayerClick = function(e) {{
    originalOnAddLayer.call(this, e);
    updateLegend(this._activeLayers()[0]);
}};
</script>
'''

m.get_root().html.add_child(folium.Element(legend_script))

# Add legend HTML elements to map
m.get_root().html.add_child(folium.Element(ph_legend))
m.get_root().html.add_child(folium.Element(om_legend))
m.get_root().html.add_child(folium.Element(cec_legend))
m.get_root().html.add_child(folium.Element(aws_legend))

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
