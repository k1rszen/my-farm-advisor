#!/usr/bin/env python3
"""Generate static dashboard PNG maps

Creates static PNG screenshots of the dashboard maps with legend/UI elements.
"""

import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.colors import LinearSegmentedColormap
import contextily as ctx
from pathlib import Path

DATA_DIR = Path("/workspaces/my-farm-advisor/data/workspace")
DASH_DIR = DATA_DIR / "dashboard_assets"
DASH_DIR.mkdir(parents=True, exist_ok=True)

# Load data
df = pd.read_csv(DATA_DIR / "NC_soil_crop_data_summary_EPSG4326_2026-04-01.csv")
gdf = gpd.read_file(DATA_DIR / "NC_field_boundaries_EPSG4326_2026-04-01.geojson")
gdf = gdf.merge(df, on='field_id', how='left')

# Project to a CRS in meters for proper display
gdf_proj = gdf.to_crs(epsg=3857)

# Get center of largest field in projected coordinates
gdf_proj['area_calc'] = gdf_proj.geometry.area
largest = gdf_proj.nlargest(1, 'area_calc').iloc[0]
center = largest.geometry.centroid

print(f"Largest field: {largest['field_id']} ({largest['area_acres']:.0f} acres)")
print(f"Center: x={center.x:.0f}, y={center.y:.0f}")

# Define color functions for each property
def get_color(val, vmin, vmax, colors):
    if pd.isna(val):
        return '#cccccc'
    norm = (val - vmin) / (vmax - vmin)
    norm = max(0, min(1, norm))
    idx = int(norm * (len(colors) - 1))
    return colors[idx]

# Color sequences (high to low for each property)
ph_colors = ['#bd0026', '#f03b20', '#fd8d3c', '#fecc5c', '#ffffb2']
om_colors = ['#1d91c0', '#41b6c4', '#7bccc4', '#c7e9b4', '#ffffe5']
cec_colors = ['#0c2c84', '#225ea8', '#41b6c4', '#c7e9b4', '#ffffd9']
aws_colors = ['#bd0026', '#f03b20', '#fd8d3c', '#fecc5c', '#ffffb2']

def get_color_ph(val):
    return get_color(val, 4.5, 6.5, ph_colors)

def get_color_om(val):
    return get_color(val, 0.5, 2.2, om_colors)

def get_color_cec(val):
    return get_color(val, 2.5, 14.0, cec_colors)

def get_color_aws(val):
    return get_color(val, 0.5, 9.0, aws_colors)

# Create a function to plot the map
def create_dashboard_map(ax, gdf_proj, color_func, title, legend_labels, legend_colors):
    # Filter to bounds around largest field
    buffer = 15000  # 15km buffer
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
    
    # Plot fields
    gdf_clip['color'] = gdf_clip['avg_ph'].apply(color_func)
    
    for idx, row in gdf_clip.iterrows():
        gdf_clip.geometry[idx].plot(ax=ax, color=row['color'], edgecolor='black', 
                                    linewidth=1, alpha=0.7)
    
    # Add basemap
    ctx.add_basemap(ax, source=ctx.providers.CartoDB.Positron, zoom=14)
    
    # Set bounds
    ax.set_xlim(minx, maxx)
    ax.set_ylim(miny, maxy)
    ax.axis('off')
    
    # Add title
    ax.set_title(title, fontsize=18, fontweight='bold', pad=20)
    
    return ax

# Create the first dashboard map (Soil Characteristics - showing pH)
fig, ax = plt.subplots(figsize=(14, 10), facecolor='white')
ax = fig.add_subplot(111)

# Get bounds around largest field
buffer = 15000
bounds = largest.geometry.buffer(buffer).bounds
minx, miny, maxx, maxy = bounds

# Clip data
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
ctx.add_basemap(ax, source=ctx.providers.CartoDB.Positron, zoom=14)
ax.set_xlim(minx, maxx)
ax.set_ylim(miny, maxy)
ax.axis('off')

# Title
ax.set_title('NC Field Soil Characteristics', fontsize=22, fontweight='bold', pad=20)

# Add legend manually
legend_elements = [
    mpatches.Patch(facecolor='#bd0026', edgecolor='black', label='6.5'),
    mpatches.Patch(facecolor='#f03b20', edgecolor='black', label='5.5'),
    mpatches.Patch(facecolor='#fd8d3c', edgecolor='black', label='5.0'),
    mpatches.Patch(facecolor='#fecc5c', edgecolor='black', label='5.0'),
    mpatches.Patch(facecolor='#ffffb2', edgecolor='black', label='4.5'),
]
ax.legend(handles=legend_elements, loc='lower left', title='Soil pH', fontsize=11, title_fontsize=12,
          frameon=True, fancybox=True, shadow=True)

# Add subtitle/note
ax.text(0.99, 0.02, 'Layers: pH, OM, CEC, Water Storage\nZoomed on largest field (768 acres)', 
        transform=ax.transAxes, fontsize=10, ha='right', va='bottom',
        bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

plt.tight_layout()
plt.savefig(DASH_DIR / 'farm_field_map_dashboard.png', dpi=150, bbox_inches='tight', facecolor='white')
plt.close()
print(f"Saved: {DASH_DIR / 'farm_field_map_dashboard.png'}")

# Create second dashboard map (Soil Texture - showing Clay)
fig2, ax2 = plt.subplots(figsize=(14, 10), facecolor='white')
ax2 = fig2.add_subplot(111)

# Plot with Clay colors
clay_colors = ['#0c2c84', '#225ea8', '#41b6c4', '#c7e9b4', '#ffffd9']
gdf_clip['plot_color_clay'] = gdf_clip['avg_clay_pct'].apply(
    lambda x: get_color(x, 5, 40, clay_colors)
)
gdf_clip.plot(ax=ax2, color=gdf_clip['plot_color_clay'], edgecolor='black', linewidth=1, alpha=0.7)

# Add basemap
ctx.add_basemap(ax2, source=ctx.providers.CartoDB.Positron, zoom=14)
ax2.set_xlim(minx, maxx)
ax2.set_ylim(miny, maxy)
ax2.axis('off')

# Title
ax2.set_title('NC Field Soil Texture Components', fontsize=22, fontweight='bold', pad=20)

# Add legend
legend_elements2 = [
    mpatches.Patch(facecolor='#0c2c84', edgecolor='black', label='40%'),
    mpatches.Patch(facecolor='#225ea8', edgecolor='black', label='32%'),
    mpatches.Patch(facecolor='#41b6c4', edgecolor='black', label='23%'),
    mpatches.Patch(facecolor='#c7e9b4', edgecolor='black', label='14%'),
    mpatches.Patch(facecolor='#ffffd9', edgecolor='black', label='5%'),
]
ax2.legend(handles=legend_elements2, loc='lower left', title='Clay (%)', fontsize=11, title_fontsize=12,
           frameon=True, fancybox=True, shadow=True)

# Add subtitle/note
ax2.text(0.99, 0.02, 'Layers: Clay, Sand, Silt\nZoomed on largest field (768 acres)', 
         transform=ax2.transAxes, fontsize=10, ha='right', va='bottom',
         bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

plt.tight_layout()
plt.savefig(DASH_DIR / 'farm_field_soil_components_dashboard.png', dpi=150, bbox_inches='tight', facecolor='white')
plt.close()
print(f"Saved: {DASH_DIR / 'farm_field_soil_components_dashboard.png'}")

print("\nDashboard PNG files created successfully!")
