import os
import json
import geopandas as gpd
from pathlib import Path
import rasterio
from rasterio.mask import mask
from rasterio.warp import calculate_default_transform, reproject, Resampling
import numpy as np
import matplotlib.pyplot as plt

OUTPUT_DIR = Path("data/workspace/output/assignment-05")
RAW_DIR = OUTPUT_DIR / "raw"

FIELDS_PATH = "data/workspace/NC_field_boundaries_EPSG4326_2026-04-01.geojson"

print("Loading field boundaries...")
fields = gpd.read_file(FIELDS_PATH)
largest = fields.loc[fields['area_acres'].idxmax()]

field_id = largest['field_id']
field_geom = largest.geometry
bbox = largest.geometry.bounds
min_lon, min_lat, max_lon, max_lat = bbox

print(f"Field: {field_id} ({largest['area_acres']:.2f} acres)")

raster_crs = "EPSG:32617"
field_gdf = gpd.GeoDataFrame(geometry=[field_geom], crs="EPSG:4326")
field_proj = field_gdf.to_crs(raster_crs)
field_geom_proj = json.loads(field_proj.to_json())['features'][0]['geometry']

print("\n=== Loading and clipping bands ===")

red_path = RAW_DIR / f"{field_id}_B4_Red_raw.tif"
nir_path = RAW_DIR / f"{field_id}_B5_NIR_raw.tif"

with rasterio.open(red_path) as src:
    red_out, red_transform = mask(src, [field_geom_proj], crop=True, nodata=0)
    red_meta = src.meta.copy()
    print(f"Red band clipped: shape={red_out.shape}")

with rasterio.open(nir_path) as src:
    nir_out, nir_transform = mask(src, [field_geom_proj], crop=True, nodata=0)
    nir_meta = src.meta.copy()
    print(f"NIR band clipped: shape={nir_out.shape}")

print("\n=== Calculating NDVI ===")

red = red_out[0].astype('float32')
nir = nir_out[0].astype('float32')

ndvi = np.where(
    (nir + red) > 0,
    (nir - red) / (nir + red),
    np.nan
)

valid_ndvi = ndvi[~np.isnan(ndvi)]
print(f"NDVI range: {valid_ndvi.min():.4f} to {valid_ndvi.max():.4f}")
print(f"NDVI mean: {valid_ndvi.mean():.4f}")
print(f"Valid pixels: {len(valid_ndvi)}")

ndvi_safe = np.where(np.isnan(ndvi), -9999, ndvi).astype('float32')

print("\n=== Saving NDVI UTM GeoTIFF ===")

utm_path = OUTPUT_DIR / f"{field_id}_NDVI_UTM.tif"
utm_meta = red_meta.copy()
utm_meta.update({
    'driver': 'GTiff',
    'height': ndvi_safe.shape[0],
    'width': ndvi_safe.shape[1],
    'transform': red_transform,
    'dtype': 'float32',
    'nodata': -9999,
    'compress': 'lzw'
})

with rasterio.open(utm_path, 'w', **utm_meta) as dst:
    dst.write(ndvi_safe, 1)
print(f"Saved: {utm_path}")

print("\n=== Reprojecting to EPSG:4326 ===")

epsg4326_path = OUTPUT_DIR / f"{field_id}_NDVI_EPSG4326.tif"

transform_4326, width, height = calculate_default_transform(
    raster_crs, 'EPSG:4326', ndvi_safe.shape[1], ndvi_safe.shape[0],
    field_proj.to_crs(raster_crs).total_bounds[0],
    field_proj.to_crs(raster_crs).total_bounds[1],
    field_proj.to_crs(raster_crs).total_bounds[2],
    field_proj.to_crs(raster_crs).total_bounds[3]
)

epsg_meta = {
    'driver': 'GTiff',
    'dtype': 'float32',
    'nodata': -9999,
    'compress': 'lzw',
    'crs': 'EPSG:4326',
    'transform': transform_4326,
    'width': width,
    'height': height,
    'count': 1
}

data_out = np.full((height, width), -9999.0, dtype='float32')

reproject(
    source=ndvi_safe,
    destination=data_out,
    src_transform=red_transform,
    src_crs=raster_crs,
    dst_transform=transform_4326,
    dst_crs='EPSG:4326',
    resampling=Resampling.bilinear,
    src_nodata=-9999,
    dst_nodata=-9999
)

with rasterio.open(epsg4326_path, 'w', **epsg_meta) as dst:
    dst.write(data_out, 1)
print(f"Saved: {epsg4326_path}")

print("\n=== Generating NDVI Color Visualization ===")

with rasterio.open(epsg4326_path) as src:
    data = src.read(1)
    bounds = src.bounds
    
    valid_data = data[(data != -9999) & (~np.isnan(data))]
    mean_val = valid_data.mean() if len(valid_data) > 0 else 0
    
    extent = [bounds.left, bounds.right, bounds.bottom, bounds.top]

fig, ax = plt.subplots(figsize=(10, 8))

vmin, vmax = -1.0, 1.0
im = ax.imshow(
    data,
    cmap='RdYlGn',
    vmin=vmin,
    vmax=vmax,
    extent=extent,
    origin='upper'
)

cbar = plt.colorbar(im, ax=ax, shrink=0.8, extend='both')
cbar.set_label('NDVI Value', fontsize=12)
cbar.set_ticks(np.arange(-1.0, 1.1, 0.25))

ax.set_title(f"NC Field - {field_id}\nNDVI (Mean: {mean_val:.4f})", fontsize=14, fontweight='bold')
ax.set_xlabel('Longitude', fontsize=12)
ax.set_ylabel('Latitude', fontsize=12)

ax.set_xlim(extent[0], extent[1])
ax.set_ylim(extent[2], extent[3])

plt.tight_layout()

png_path = OUTPUT_DIR / f"{field_id}_NDVI_color.png"
plt.savefig(png_path, dpi=150, bbox_inches='tight')
plt.close()
print(f"Saved: {png_path}")

print("\n=== NDVI Summary ===")
print(f"Field: {field_id}")
print(f"Location: Guilford County, NC")
print(f"Area: {largest['area_acres']:.2f} acres")
print(f"NDVI Min: {valid_ndvi.min():.4f}")
print(f"NDVI Max: {valid_ndvi.max():.4f}")
print(f"NDVI Mean: {valid_ndvi.mean():.4f}")

import pandas as pd
summary = pd.DataFrame([{
    'field_id': field_id,
    'county': largest['county_name'],
    'area_acres': largest['area_acres'],
    'ndvi_min': round(valid_ndvi.min(), 4),
    'ndvi_max': round(valid_ndvi.max(), 4),
    'ndvi_mean': round(valid_ndvi.mean(), 4),
    'pixels': len(valid_ndvi)
}])
summary.to_csv(OUTPUT_DIR / 'ndvi_summary.csv', index=False)
print(f"\nSummary saved to: {OUTPUT_DIR / 'ndvi_summary.csv'}")