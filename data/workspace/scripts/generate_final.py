import os
import json
import geopandas as gpd
from pathlib import Path
import rasterio
from rasterio.warp import calculate_default_transform, reproject, Resampling
import numpy as np
import pandas as pd

OUTPUT_DIR = Path("data/workspace/output/assignment-05")

FIELDS_PATH = "data/workspace/NC_field_boundaries_EPSG4326_2026-04-01.geojson"

print("Loading field boundaries...")
fields = gpd.read_file(FIELDS_PATH)
largest = fields.loc[fields['area_acres'].idxmax()]

field_id = largest['field_id']

print(f"\nLargest field: {field_id} ({largest['area_acres']:.2f} acres)")

band_mapping = {
    'B2_Blue': 'blue',
    'B3_Green': 'green',
    'B4_Red': 'red',
    'B5_NIR': 'nir08',
    'B6_SWIR1': 'swir16',
    'B7_SWIR2': 'swir22'
}

raw_dir = OUTPUT_DIR / "raw"

summary = []

for band_key, band_name in band_mapping.items():
    raw_path = raw_dir / f"{field_id}_{band_key}_raw.tif"
    clipped_path = OUTPUT_DIR / f"{field_id}_{band_key}_clipped.tif"
    
    if not clipped_path.exists():
        print(f"Clipped file not found: {clipped_path}")
        continue
    
    print(f"\n--- Processing {band_key} ({band_name}) ---")
    
    with rasterio.open(clipped_path) as src:
        data = src.read(1).astype('float32')
        original_crs = src.crs
        original_transform = src.transform
        original_bounds = src.bounds
        
        valid_mask = (data != 0) & (~np.isnan(data))
        scaled = np.zeros_like(data, dtype='uint8')
        scaled[valid_mask] = ((data[valid_mask] / 10000.0) * 255).astype('uint8')
        
        out_meta = {
            'driver': 'GTiff',
            'dtype': 'uint8',
            'nodata': 0,
            'compress': 'lzw',
            'crs': original_crs,
            'transform': original_transform,
            'height': data.shape[0],
            'width': data.shape[1],
            'count': 1
        }
        
        utm_path = OUTPUT_DIR / f"{field_id}_{band_key}_UTM.tif"
        with rasterio.open(utm_path, 'w', **out_meta) as dst:
            dst.write(scaled, 1)
    
    valid_scaled = scaled[scaled != 0]
    if len(valid_scaled) > 0:
        print(f"  UTM stats: min={valid_scaled.min()}, max={valid_scaled.max()}, mean={valid_scaled.mean():.2f}")
        summary.append({
            'band': band_key.split('_')[-1],
            'min': int(valid_scaled.min()),
            'max': int(valid_scaled.max()),
            'mean': round(float(valid_scaled.mean()), 2),
            'pixels': len(valid_scaled)
        })
    
    epsg4326_path = OUTPUT_DIR / f"{field_id}_{band_key}_EPSG4326.tif"
    
    transform, width, height = calculate_default_transform(
        original_crs, 'EPSG:4326', scaled.shape[1], scaled.shape[0], *original_bounds
    )
    
    kwargs = {
        'driver': 'GTiff',
        'dtype': 'uint8',
        'nodata': 0,
        'compress': 'lzw',
        'crs': 'EPSG:4326',
        'transform': transform,
        'width': width,
        'height': height,
        'count': 1
    }
    
    data_out = np.zeros((height, width), dtype='uint8')
    
    reproject(
        source=scaled,
        destination=data_out,
        src_transform=original_transform,
        src_crs=original_crs,
        dst_transform=transform,
        dst_crs='EPSG:4326',
        resampling=Resampling.bilinear,
        src_nodata=0,
        dst_nodata=0
    )
    
    with rasterio.open(epsg4326_path, 'w', **kwargs) as dst:
        dst.write(data_out, 1)
    
    with rasterio.open(epsg4326_path) as src:
        data = src.read(1)
        valid = data[data != 0]
        if len(valid) > 0:
            print(f"  EPSG4326 stats: min={valid.min()}, max={valid.max()}, mean={valid.mean():.2f}")

print("\n=== Generated Final Files ===")
for f in sorted(OUTPUT_DIR.iterdir()):
    if f.suffix == '.tif' and 'clipped' not in f.name:
        print(f"  {f.name}")

print("\n=== Band Summary ===")
df = pd.DataFrame(summary)
print(df.to_string(index=False))
df.to_csv(OUTPUT_DIR / 'band_summary.csv', index=False)
print(f"\nSummary saved to: {OUTPUT_DIR / 'band_summary.csv'}")