#!/usr/bin/env python3
"""
NDVI Processing for Top 10 NC Fields
Batch processing with Sentinel-2 (preferred) and Landsat 8/9 (fallback)
"""

import json
import time
import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
import requests
from pathlib import Path
from datetime import datetime, timedelta

PLANETARY_COMPUTER_SEARCH_URL = "https://planetarycomputer.microsoft.com/api/stac/v1/search"
PLANETARY_COMPUTER_TOKEN_URL = "https://planetarycomputer.microsoft.com/api/sas/v1/token"
SENTINEL_COLLECTION = "sentinel-2-l2a"
LANDSAT_COLLECTION = "landsat-c2-l2"
SENTINEL_CLOUD_CLASSES = {3, 8, 9, 10, 11}
LANDSAT_QA_MASK_BITS = (1, 2, 3, 4, 5)

OUTPUT_DIR = Path("/workspaces/my-farm-advisor/data/workspace/output/assignment-05")
FIELDS_PATH = "/workspaces/my-farm-advisor/data/workspace/NC_field_boundaries_EPSG4326_2026-04-01.geojson"

FIELDS_TO_PROCESS = [
    "osm-1153259427",  # Batch 1
    "osm-813157720",
    "osm-1305439648",
    "osm-1386621285",  # Batch 2
    "osm-1133139440",
    "osm-1476971106",
    "osm-834363677",   # Batch 3
    "osm-548794709",
    "osm-199889806",
]

EXISTING_FIELD = "osm-260949778"

_token_cache = {}


def get_token(collection: str) -> str:
    now = time.time()
    cached = _token_cache.get(collection)
    if cached is not None and cached[1] > now + 60:
        return cached[0]
    
    for attempt in range(5):
        try:
            resp = requests.get(f"{PLANETARY_COMPUTER_TOKEN_URL}/{collection}", timeout=60)
            if resp.status_code == 429:
                time.sleep(min(2**attempt, 20))
                continue
            resp.raise_for_status()
            token = str(resp.json()["token"])
            _token_cache[collection] = (token, now + 600)
            return token
        except Exception as e:
            if attempt == 4:
                raise e
            time.sleep(min(2**attempt, 20))
    return ""


def sign_href(href: str, collection: str) -> str:
    if collection not in (SENTINEL_COLLECTION, LANDSAT_COLLECTION):
        return href
    token = get_token(collection)
    sep = "&" if "?" in href else "?"
    return f"{href}{sep}{token}"


def search_scenes(collection: str, bbox: tuple, start_date: str, end_date: str, cloud_lt: float = 20):
    query = {"eo:cloud_cover": {"lt": cloud_lt}}
    if collection == LANDSAT_COLLECTION:
        query["platform"] = {"in": ["landsat-8", "landsat-9"]}
    
    body = {
        "collections": [collection],
        "bbox": list(bbox),
        "datetime": f"{start_date}/{end_date}",
        "limit": 20,
        "query": query,
    }
    
    resp = requests.post(PLANETARY_COMPUTER_SEARCH_URL, json=body, timeout=60)
    resp.raise_for_status()
    features = resp.json().get("features", [])
    
    features.sort(key=lambda f: (
        f.get("properties", {}).get("eo:cloud_cover", 100),
        -datetime.fromisoformat(f.get("properties", {}).get("datetime", "1970-01-01").replace("Z", "+00:00")).timestamp()
    ))
    return features


def get_field_geometry(field_id: str):
    fields = gpd.read_file(FIELDS_PATH)
    field = fields[fields['field_id'] == field_id].iloc[0]
    return field.geometry, field.geometry.bounds, fields[fields['field_id'] == field_id]


def download_and_clip(href: str, geometry, output_path: Path, target_crs: str = "EPSG:4326"):
    from rasterio.mask import mask
    from rasterio.warp import calculate_default_transform, reproject, Resampling
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with rasterio.open(href) as src:
        field_gdf = gpd.GeoDataFrame(geometry=[geometry], crs="EPSG:4326")
        field_proj = field_gdf.to_crs(src.crs)
        geom_json = json.loads(field_proj.to_json())['features'][0]['geometry']
        
        out_image, out_transform = mask(src, [geom_json], crop=True, nodata=0)
        profile = src.profile.copy()
    
    profile.update({
        'driver': 'GTiff',
        'height': out_image.shape[1],
        'width': out_image.shape[2],
        'transform': out_transform,
        'compress': 'lzw',
    })
    
    with rasterio.open(output_path, 'w', **profile) as dst:
        dst.write(out_image)
    
    if target_crs and str(rasterio.open(output_path).crs) != target_crs:
        with rasterio.open(output_path) as src:
            transform, width, height = calculate_default_transform(src.crs, target_crs, src.width, src.height, *src.bounds)
            profile = src.profile.copy()
            profile.update({'crs': target_crs, 'transform': transform, 'width': width, 'height': height})
            
            reprojected = output_path.with_name(output_path.stem + "_reprojected.tif")
            with rasterio.open(reprojected, 'w', **profile) as dst:
                reproject(
                    source=rasterio.band(src, 1),
                    destination=rasterio.band(dst, 1),
                    src_transform=src.transform, src_crs=src.crs,
                    dst_transform=transform, dst_crs=target_crs,
                    resampling=Resampling.bilinear,
                )
            output_path.unlink()
            reprojected.rename(output_path)
    
    return output_path


def get_landsat_ndvi(red_path: Path, nir_path: Path) -> np.ndarray:
    with rasterio.open(red_path) as src:
        red = src.read(1).astype('float32')
        red = np.where(red == 0, np.nan, red * 0.0000275 - 0.2)
    
    with rasterio.open(nir_path) as src:
        nir = src.read(1).astype('float32')
        nir = np.where(nir == 0, np.nan, nir * 0.0000275 - 0.2)
    
    denom = nir + red
    valid = np.isfinite(red) & np.isfinite(nir) & (denom != 0)
    ndvi = np.full(red.shape, np.nan, dtype='float32')
    ndvi[valid] = (nir[valid] - red[valid]) / denom[valid]
    ndvi = np.clip(ndvi, -1.0, 1.0)
    return ndvi


def get_sentinel_ndvi(red_path: Path, nir_path: Path, scl_path: Path = None) -> np.ndarray:
    with rasterio.open(red_path) as src:
        red = src.read(1).astype('float32')
        red = red / 10000.0
        red = np.where(red == 0, np.nan, red)
    
    with rasterio.open(nir_path) as src:
        nir = src.read(1).astype('float32')
        nir = nir / 10000.0
        nir = np.where(nir == 0, np.nan, nir)
    
    cloud_mask = np.zeros_like(red, dtype=bool)
    if scl_path and scl_path.exists():
        with rasterio.open(scl_path) as src:
            scl = src.read(1)
        cloud_mask = np.isin(scl, list(SENTINEL_CLOUD_CLASSES))
    
    denom = nir + red
    valid = np.isfinite(red) & np.isfinite(nir) & (denom != 0) & ~cloud_mask
    ndvi = np.full(red.shape, np.nan, dtype='float32')
    ndvi[valid] = (nir[valid] - red[valid]) / denom[valid]
    ndvi = np.clip(ndvi, -1.0, 1.0)
    return ndvi


def save_ndvi_raster(ndvi: np.ndarray, reference_path: Path, output_path: Path):
    with rasterio.open(reference_path) as src:
        profile = src.profile.copy()
    profile.update({'dtype': 'float32', 'nodata': np.nan, 'compress': 'lzw'})
    
    with rasterio.open(output_path, 'w', **profile) as dst:
        dst.write(ndvi, 1)
    return output_path


def create_ndvi_visualization(ndvi_path: Path, field_id: str, output_dir: Path):
    import matplotlib.pyplot as plt
    from matplotlib.colors import TwoSlopeNorm
    
    with rasterio.open(ndvi_path) as src:
        data = src.read(1)
        bounds = src.bounds
    
    valid = data[~np.isnan(data)]
    mean_val = np.mean(valid) if len(valid) > 0 else 0
    
    fig, ax = plt.subplots(figsize=(10, 8))
    norm = TwoSlopeNorm(vmin=-1.0, vcenter=0, vmax=1.0)
    im = ax.imshow(data, cmap='RdYlGn', norm=norm, extent=[bounds.left, bounds.right, bounds.bottom, bounds.top], origin='upper')
    
    cbar = plt.colorbar(im, ax=ax, shrink=0.8, extend='both')
    cbar.set_label('NDVI Value', fontsize=12)
    cbar.set_ticks(np.arange(-1.0, 1.1, 0.25))
    
    ax.set_title(f"NDVI - {field_id}\n(Mean: {mean_val:.4f})", fontsize=14, fontweight='bold')
    ax.set_xlabel('Longitude')
    ax.set_ylabel('Latitude')
    
    plt.tight_layout()
    output_path = output_dir / f"{field_id}_NDVI_color.png"
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    return output_path


def process_field(field_id: str, start_date: str, end_date: str):
    print(f"\n{'='*60}")
    print(f"Processing: {field_id}")
    print(f"{'='*60}")
    
    geometry, bbox, _ = get_field_geometry(field_id)
    print(f"Bounding box: {bbox}")
    
    red_path = OUTPUT_DIR / f"{field_id}_red.tif"
    nir_path = OUTPUT_DIR / f"{field_id}_nir.tif"
    ndvi_path = OUTPUT_DIR / f"{field_id}_NDVI.tif"
    
    if red_path.exists() and nir_path.exists():
        print("Using cached band files")
    else:
        print("\n[1/3] Searching Sentinel-2...")
        sentinel_features = search_scenes(SENTINEL_COLLECTION, bbox, start_date, end_date, cloud_lt=20)
        
        source = None
        if sentinel_features:
            print(f"  Found {len(sentinel_features)} Sentinel-2 scenes, using best")
            feat = sentinel_features[0]
            assets = feat.get('assets', {})
            
            red_key = 'red' if 'red' in assets else 'B04'
            nir_key = 'nir' if 'nir' in assets else 'B08'
            scl_key = 'scl' if 'scl' in assets else 'SCL'
            
            red_href = sign_href(assets[red_key]['href'], SENTINEL_COLLECTION)
            nir_href = sign_href(assets[nir_key]['href'], SENTINEL_COLLECTION)
            
            print(f"  Downloading Red band ({red_key})...")
            try:
                download_and_clip(red_href, geometry, red_path)
            except Exception as e:
                print(f"  Failed: {e}")
                red_path = None
            
            print(f"  Downloading NIR band ({nir_key})...")
            try:
                download_and_clip(nir_href, geometry, nir_path)
            except Exception as e:
                print(f"  Failed: {e}")
                nir_path = None
            
            if red_path and nir_path and red_path.exists() and nir_path.exists():
                source = 'sentinel2'
                scl_path = OUTPUT_DIR / f"{field_id}_scl.tif"
                if scl_key in assets:
                    try:
                        download_and_clip(sign_href(assets[scl_key]['href'], SENTINEL_COLLECTION), geometry, scl_path)
                    except:
                        pass
            else:
                red_path.unlink() if red_path and red_path.exists() else None
                nir_path.unlink() if nir_path and nir_path.exists() else None
                red_path = None
                nir_path = None
        
        if not source or not (red_path and nir_path and red_path.exists() and nir_path.exists()):
            print("\n[1/3] Searching Landsat 8/9 (fallback)...")
            landsat_features = search_scenes(LANDSAT_COLLECTION, bbox, start_date, end_date, cloud_lt=20)
            
            if landsat_features:
                print(f"  Found {len(landsat_features)} Landsat scenes, using best")
                feat = landsat_features[0]
                assets = feat.get('assets', {})
                
                red_href = sign_href(assets['red']['href'], LANDSAT_COLLECTION)
                nir_href = sign_href(assets['nir08']['href'], LANDSAT_COLLECTION)
                
                print("  Downloading Red band...")
                try:
                    download_and_clip(red_href, geometry, red_path)
                except Exception as e:
                    print(f"  Failed: {e}")
                    red_path = None
                
                print("  Downloading NIR band...")
                try:
                    download_and_clip(nir_href, geometry, nir_path)
                except Exception as e:
                    print(f"  Failed: {e}")
                    nir_path = None
                
                source = 'landsat8' if (red_path and nir_path and red_path.exists() and nir_path.exists()) else None
            else:
                print("  No suitable Landsat scenes found")
                source = None
        
        if not source:
            print(f"ERROR: No suitable imagery found for {field_id}")
            return None
    
    if not (red_path.exists() and nir_path.exists()):
        print(f"ERROR: Band files missing for {field_id}")
        return None
    
    print("\n[2/3] Computing NDVI...")
    if source == 'sentinel2':
        ndvi = get_sentinel_ndvi(red_path, nir_path)
    else:
        ndvi = get_landsat_ndvi(red_path, nir_path)
    
    save_ndvi_raster(ndvi, red_path, ndvi_path)
    print(f"  Saved: {ndvi_path}")
    
    print("\n[3/3] Creating visualization...")
    vis_path = create_ndvi_visualization(ndvi_path, field_id, OUTPUT_DIR)
    print(f"  Saved: {vis_path}")
    
    valid_ndvi = ndvi[~np.isnan(ndvi)]
    stats = {
        'field_id': field_id,
        'source': source,
        'ndvi_min': float(valid_ndvi.min()) if len(valid_ndvi) > 0 else None,
        'ndvi_max': float(valid_ndvi.max()) if len(valid_ndvi) > 0 else None,
        'ndvi_mean': float(valid_ndvi.mean()) if len(valid_ndvi) > 0 else None,
        'pixels': len(valid_ndvi),
    }
    print(f"\n  Stats: min={stats['ndvi_min']:.4f}, max={stats['ndvi_max']:.4f}, mean={stats['ndvi_mean']:.4f}")
    return stats


def main():
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
    
    print(f"Searching for scenes from {start_date} to {end_date}")
    
    results = []
    
    for field_id in FIELDS_TO_PROCESS:
        try:
            stats = process_field(field_id, start_date, end_date)
            if stats:
                results.append(stats)
        except Exception as e:
            print(f"ERROR processing {field_id}: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "="*60)
    print("SUMMARY - Batch 1 Results")
    print("="*60)
    for r in results:
        print(f"  {r['field_id']}: mean={r['ndvi_mean']:.4f}, source={r['source']}")
    
    df = pd.DataFrame(results)
    df.to_csv(OUTPUT_DIR / "ndvi_batch1_results.csv", index=False)
    print(f"\nResults saved to: {OUTPUT_DIR / 'ndvi_batch1_results.csv'}")


if __name__ == "__main__":
    main()