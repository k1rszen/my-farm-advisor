import rasterio
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import numpy as np
from pathlib import Path
import geopandas as gpd

OUTPUT_DIR = Path("data/workspace/output/assignment-05")

FIELDS_PATH = "data/workspace/NC_field_boundaries_EPSG4326_2026-04-01.geojson"

fields = gpd.read_file(FIELDS_PATH)
largest = fields.loc[fields['area_acres'].idxmax()]
field_id = largest['field_id']

band_config = {
    'B2_Blue': {
        'name': 'Blue Band (B2)',
        'colormap': 'Blues',
        'file': 'osm-260949778_B2_Blue_EPSG4326.tif'
    },
    'B3_Green': {
        'name': 'Green Band (B3)',
        'colormap': 'Greens',
        'file': 'osm-260949778_B3_Green_EPSG4326.tif'
    },
    'B4_Red': {
        'name': 'Red Band (B4)',
        'colormap': 'Reds',
        'file': 'osm-260949778_B4_Red_EPSG4326.tif'
    },
    'B5_NIR': {
        'name': 'Near-Infrared Band (B5)',
        'colormap': 'hot_r',
        'file': 'osm-260949778_B5_NIR_EPSG4326.tif'
    },
    'B6_SWIR1': {
        'name': 'SWIR1 Band (B6)',
        'colormap': 'inferno',
        'file': 'osm-260949778_B6_SWIR1_EPSG4326.tif'
    },
    'B7_SWIR2': {
        'name': 'SWIR2 Band (B7)',
        'colormap': 'viridis',
        'file': 'osm-260949778_B7_SWIR2_EPSG4326.tif'
    }
}

for band_key, config in band_config.items():
    filepath = OUTPUT_DIR / config['file']
    
    with rasterio.open(filepath) as src:
        data = src.read(1)
        bounds = src.bounds
        transform = src.transform
        
        valid_data = data[data != 0]
        mean_val = valid_data.mean() if len(valid_data) > 0 else 0
        
        extent = [
            bounds.left,
            bounds.right,
            bounds.bottom,
            bounds.top
        ]
    
    fig, ax = plt.subplots(figsize=(10, 8))
    
    im = ax.imshow(
        data,
        cmap=config['colormap'],
        extent=extent,
        origin='upper'
    )
    
    cbar = plt.colorbar(im, ax=ax, shrink=0.8)
    cbar.set_label('Pixel Value (0-255)', fontsize=10)
    
    ax.set_title(f"NC Field - {field_id}\n{config['name']}\n(Mean: {mean_val:.2f})", fontsize=14, fontweight='bold')
    ax.set_xlabel('Longitude', fontsize=12)
    ax.set_ylabel('Latitude', fontsize=12)
    
    ax.set_xlim(extent[0], extent[1])
    ax.set_ylim(extent[2], extent[3])
    
    plt.tight_layout()
    
    output_path = OUTPUT_DIR / f"{field_id}_{band_key}_color.png"
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    print(f"Saved: {output_path}")

print("\n=== Generated Color Images ===")
for f in sorted(OUTPUT_DIR.iterdir()):
    if f.suffix == '.png' and 'color' in f.name:
        print(f"  {f.name}")