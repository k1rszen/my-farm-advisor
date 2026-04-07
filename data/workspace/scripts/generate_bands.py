import os
import json
import geopandas as gpd
from pathlib import Path
import rasterio
from rasterio.mask import mask
from rasterio.warp import calculate_default_transform, reproject, Resampling
import numpy as np

OUTPUT_DIR = Path("data/workspace/output/assignment-05")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

FIELDS_PATH = "data/workspace/NC_field_boundaries_EPSG4326_2026-04-01.geojson"

print("Loading field boundaries...")
fields = gpd.read_file(FIELDS_PATH)
largest = fields.loc[fields['area_acres'].idxmax()]

field_id = largest['field_id']
field_geom = largest.geometry
bbox = largest.geometry.bounds
min_lon, min_lat, max_lon, max_lat = bbox

print(f"\nLargest field: {field_id} ({largest['area_acres']:.2f} acres)")
print(f"Bounding box: {min_lon}, {min_lat}, {max_lon}, {max_lat}")

from pystac_client import Client
import planetary_computer
import requests

print("\nSearching Microsoft Planetary Computer...")
catalog = Client.open("https://planetarycomputer.microsoft.com/api/stac/v1")

search = catalog.search(
    collections=["landsat-c2-l2"],
    bbox=[min_lon, min_lat, max_lon, max_lat]
)

items = list(search.items())
filtered = [i for i in items if i.properties.get('eo:cloud_cover', 100) <= 20]
sorted_items = sorted(filtered, key=lambda x: x.properties.get('eo:cloud_cover', 100))
best = sorted_items[0]

print(f"Best scene: {best.id}")
print(f"  Date: {best.datetime.date()}")
print(f"  Cloud cover: {best.properties.get('eo:cloud_cover')}%")

band_mapping = {
    'B2_Blue': 'blue',
    'B3_Green': 'green',
    'B4_Red': 'red',
    'B5_NIR': 'nir08',
    'B6_SWIR1': 'swir16',
    'B7_SWIR2': 'swir22'
}

def get_field_geom_for_crs(crs):
    field_gdf = gpd.GeoDataFrame(geometry=[field_geom], crs="EPSG:4326")
    field_proj = field_gdf.to_crs(crs)
    return json.loads(field_proj.to_json())['features'][0]['geometry']

raw_dir = OUTPUT_DIR / "raw"
raw_dir.mkdir(exist_ok=True)

raster_crs = None
field_geom_proj = None

for band_key, band_name in band_mapping.items():
    print(f"\n--- Processing {band_key} ({band_name}) ---")
    
    if band_name not in best.assets:
        print(f"  ERROR: Band {band_name} not available")
        continue
    
    asset = best.assets[band_name]
    href = planetary_computer.sign(asset).href
    
    output_path = raw_dir / f"{field_id}_{band_key}_raw.tif"
    
    if not output_path.exists():
        response = requests.get(href, stream=True)
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"  Downloaded: {output_path}")
    else:
        print(f"  Using cached: {output_path}")
    
    if raster_crs is None:
        with rasterio.open(output_path) as src:
            raster_crs = src.crs
            print(f"  Raster CRS: {raster_crs}")
        field_geom_proj = get_field_geom_for_crs(raster_crs)
    
    clipped_path = OUTPUT_DIR / f"{field_id}_{band_key}_clipped.tif"
    
    with rasterio.open(output_path) as src:
        out_image, out_transform = mask(src, [field_geom_proj], crop=True, nodata=0)
        out_meta = src.meta.copy()
    
    out_meta.update({
        'driver': 'GTiff',
        'height': out_image.shape[1],
        'width': out_image.shape[2],
        'transform': out_transform,
        'compress': 'lzw'
    })
    
    with rasterio.open(clipped_path, 'w', **out_meta) as dst:
        dst.write(out_image)
    
    valid_data = out_image[out_image != 0]
    if len(valid_data) > 0:
        print(f"  Raw stats: min={valid_data.min()}, max={valid_data.max()}, mean={valid_data.mean():.2f}")
    
    scaled_path = OUTPUT_DIR / f"{field_id}_{band_key}_EPSG4326.tif"
    with rasterio.open(clipped_path) as src:
        data = src.read(1).astype('float32')
        
        valid_mask = (data != 0) & (~np.isnan(data))
        
        scaled = np.zeros_like(data, dtype='uint8')
        scaled[valid_mask] = ((data[valid_mask] / 10000.0) * 255).astype('uint8')
        
        out_meta = src.meta.copy()
        out_meta.update({
            'dtype': 'uint8',
            'nodata': 0,
            'compress': 'lzw'
        })
        
        with rasterio.open(scaled_path, 'w', **out_meta) as dst:
            dst.write(scaled, 1)
    
    valid_scaled = scaled[scaled != 0]
    if len(valid_scaled) > 0:
        print(f"  Scaled (0-255) stats: min={valid_scaled.min()}, max={valid_scaled.max()}, mean={valid_scaled.mean():.2f}")
    
    wgs84_path = OUTPUT_DIR / f"{field_id}_{band_key}_WGS84.tif"
    
    with rasterio.open(scaled_path) as src:
        data_in = src.read(1)
        
        transform, width, height = calculate_default_transform(
            src.crs, 'EPSG:4326', src.width, src.height, *src.bounds
        )
        
        kwargs = src.meta.copy()
        kwargs.update({
            'crs': 'EPSG:4326',
            'transform': transform,
            'width': width,
            'height': height
        })
        
        data_out = np.zeros((height, width), dtype='uint8')
        
        reproject(
            source=data_in,
            destination=data_out,
            src_transform=src.transform,
            src_crs=src.crs,
            dst_transform=transform,
            dst_crs='EPSG:4326',
            resampling=Resampling.bilinear,
            src_nodata=0,
            dst_nodata=0
        )
        
        with rasterio.open(wgs84_path, 'w', **kwargs) as dst:
            dst.write(data_out, 1)
    
    with rasterio.open(wgs84_path) as src:
        data = src.read(1)
        valid = data[data != 0]
        if len(valid) > 0:
            print(f"  WGS84 stats: min={valid.min()}, max={valid.max()}, mean={valid.mean():.2f}")

print("\n=== Generated Files ===")
for f in sorted(OUTPUT_DIR.iterdir()):
    if f.suffix == '.tif':
        print(f"  {f.name}")

print("\n=== Band Summary (EPSG4326 scaled 0-255) ===")
import pandas as pd
summary = []
for f in sorted(OUTPUT_DIR.iterdir()):
    if f.suffix == '.tif' and 'EPSG4326' in f.name:
        with rasterio.open(f) as src:
            data = src.read(1)
            valid = data[data != 0]
            if len(valid) > 0:
                summary.append({
                    'band': f.stem.split('_')[-1],
                    'min': int(valid.min()),
                    'max': int(valid.max()),
                    'mean': float(valid.mean()),
                    'pixels': len(valid)
                })

df = pd.DataFrame(summary)
print(df.to_string(index=False))
df.to_csv(OUTPUT_DIR / 'band_summary.csv', index=False)
print(f"\nSummary saved to: {OUTPUT_DIR / 'band_summary.csv'}")