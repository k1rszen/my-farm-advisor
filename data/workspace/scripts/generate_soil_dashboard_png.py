#!/usr/bin/env python3
"""Generate final dashboard PNG screenshot

Creates a static PNG screenshot of the final dashboard map.
"""

import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from pathlib import Path

DATA_DIR = Path("/workspaces/my-farm-advisor/data/workspace")
DASH_DIR = DATA_DIR / "dashboard_assets"

# Load data
df = pd.read_csv(DATA_DIR / "NC_soil_crop_data_summary_EPSG4326_2026-04-01.csv")
gdf = gpd.read_file(DATA_DIR / "NC_field_boundaries_EPSG4326_2026-04-01.geojson")
gdf = gdf.merge(df, on='field_id', how='left')

# Project to EPSG:3857 for proper display
gdf_proj = gdf.to_crs(epsg=3857)

# Get center of largest field
gdf_proj['area_calc'] = gdf_proj.geometry.area
largest = gdf_proj.nlargest(1, 'area_calc').iloc[0]
center = largest.geometry.centroid

print(f"Largest field: {largest['field_id']} ({largest['area_acres']:.0f} acres)")

# Color function for pH (default layer)
def get_color(val, vmin, vmax, colors):
    if pd.isna(val):
        return '#cccccc'
    norm = (val - vmin) / (vmax - vmin)
    norm = max(0, min(1, norm))
    idx = int(norm * (len(colors) - 1))
    return colors[idx]

ph_colors = ['#ffffb2', '#fecc5c', '#fd8d3c', '#f03b20', '#bd0026']

def get_color_ph(val):
    return get_color(val, 4.5, 6.5, ph_colors)

# Create figure
fig, ax = plt.subplots(figsize=(14, 10), facecolor='white')
ax = fig.add_subplot(111)

# Bounds around largest field
buffer = 15000
bounds = largest.geometry.buffer(buffer).bounds
minx, miny, maxx, maxy = bounds

# Clip to bounds
gdf_clip = gdf_proj[
    (gdf_proj.geometry.centroid.x >= minx) & 
    (gdf_proj.geometry.centroid.x <= maxx) &
    (gdf_proj.geometry.centroid.y >= miny) & 
    (gdf_proj.geometry.centroid.y <= maxy)
]

if len(gdf_clip) == 0:
    gdf_clip = gdf_proj

# Plot with pH colors
gdf_clip['plot_color'] = gdf_clip['avg_ph'].apply(get_color_ph)
gdf_clip.plot(ax=ax, color=gdf_clip['plot_color'], edgecolor='black', linewidth=1, alpha=0.7)

# Add basemap
import contextily as ctx
ctx.add_basemap(ax, source=ctx.providers.CartoDB.Positron, zoom=14)
ax.set_xlim(minx, maxx)
ax.set_ylim(miny, maxy)
ax.axis('off')

# Title - centered, bold, dashboard style
ax.set_title('NC Field Soil Indicators', fontsize=22, fontweight='bold', pad=20)

# Add legend
legend_elements = [
    mpatches.Patch(facecolor='#bd0026', edgecolor='black', label='6.5'),
    mpatches.Patch(facecolor='#f03b20', edgecolor='black', label='5.5'),
    mpatches.Patch(facecolor='#fd8d3c', edgecolor='black', label='5.0'),
    mpatches.Patch(facecolor='#fecc5c', edgecolor='black', label='5.0'),
    mpatches.Patch(facecolor='#ffffb2', edgecolor='black', label='4.5'),
]
legend = ax.legend(handles=legend_elements, loc='lower left', title='Soil pH (default)', 
                   fontsize=11, title_fontsize=12, frameon=True, fancybox=True, shadow=True)

# Add North arrow
ax.text(0.97, 0.95, '⬆\nN', transform=ax.transAxes, fontsize=20, ha='center', va='top',
        bbox=dict(boxstyle='round', facecolor='white', alpha=0.9, edgecolor='gray'))

# Add note about layers
ax.text(0.98, 0.02, 'Dropdown: pH, OM, CEC, AWS,\nClay, Sand, Silt, Bulk Density\nZoomed on largest field (768 acres)', 
        transform=ax.transAxes, fontsize=9, ha='right', va='bottom',
        bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

plt.tight_layout()
plt.savefig(DASH_DIR / 'field_map_dashboard_final.png', dpi=150, bbox_inches='tight', facecolor='white')
plt.close()
print(f"Saved: {DASH_DIR / 'field_map_dashboard_final.png'}")
