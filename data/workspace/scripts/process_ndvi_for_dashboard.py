#!/usr/bin/env python3
"""Process NDVI GeoTIFFs to embedded JSON arrays for dashboard.

Reads NDVI GeoTIFF files and outputs:
1. Simplified pixel arrays (downsampled to ~100x100)
2. Metadata (bounds, min/max/mean values)
3. All data embedded as JavaScript constants
"""

import json
import numpy as np
import rasterio
from pathlib import Path
from datetime import datetime

OUTPUT_DIR = Path("data/workspace/output")
TIFF_DIR = OUTPUT_DIR / "assignment-05"
DASHBOARD_DIR = OUTPUT_DIR / "dashboard"

DASHBOARD_DIR.mkdir(parents=True, exist_ok=True)

FIELD_IDS = [
    "osm-1476971106",
    "osm-1153259427", 
    "osm-260949778",
    "osm-1386621285",
    "osm-548794709",
    "osm-1305439648",
    "osm-1133139440",
    "osm-199889806",
    "osm-813157720",
    "osm-834363677",
]

TIFF_MAP = {
    "osm-260949778": "osm-260949778_NDVI_AWS_Sentinel2_4326_v2.tif",
    "osm-1476971106": "osm-1476971106_NDVI.tif",
    "osm-1153259427": "osm-1153259427_NDVI.tif",
    "osm-1386621285": "osm-1386621285_NDVI.tif",
    "osm-548794709": "osm-548794709_NDVI.tif",
    "osm-1305439648": "osm-1305439648_NDVI.tif",
    "osm-1133139440": "osm-1133139440_NDVI.tif",
    "osm-199889806": "osm-199889806_NDVI.tif",
    "osm-813157720": "osm-813157720_NDVI.tif",
    "osm-834363677": "osm-834363677_NDVI.tif",
}

TARGET_SIZE = 40

print("=" * 60)
print("NDVI GeoTIFF to JSON Array Processor")
print("=" * 60)

ndvi_data = {}

for field_id in FIELD_IDS:
    tiff_file = TIFF_DIR / TIFF_MAP[field_id]
    
    if not tiff_file.exists():
        print(f"  WARNING: {tiff_file} not found, skipping...")
        continue
    
    print(f"\nProcessing {field_id}...")
    
    with rasterio.open(tiff_file) as src:
        data = src.read(1)
        bounds = src.bounds
        
        nodata = src.nodata if src.nodata is not None else -9999
        
        valid_mask = (data != nodata) & (~np.isnan(data))
        valid_data = data[valid_mask]
        
        if len(valid_data) > 0:
            vmin = float(np.min(valid_data))
            vmax = float(np.max(valid_data))
            vmean = float(np.mean(valid_data))
        else:
            vmin = vmax = vmean = 0.0
        
        h, w = data.shape
        
        scale_h = max(1, h // TARGET_SIZE) if h > TARGET_SIZE else 1
        scale_w = max(1, w // TARGET_SIZE) if w > TARGET_SIZE else 1
        
        if h > TARGET_SIZE or w > TARGET_SIZE:
            downsampled = data[::scale_h, ::scale_w]
        else:
            downsampled = data
        
        target_h, target_w = downsampled.shape
        
        normalized = np.zeros_like(downsampled, dtype=np.uint8)
        for i in range(downsampled.shape[0]):
            for j in range(downsampled.shape[1]):
                val = downsampled[i, j]
                if val == nodata or np.isnan(val):
                    normalized[i, j] = 128
                else:
                    normalized[i, j] = int(((val + 1) / 2) * 255)
                    normalized[i, j] = max(0, min(255, normalized[i, j]))
        
        ndvi_data[field_id] = {
            "bounds": {
                "left": float(bounds.left),
                "right": float(bounds.right),
                "bottom": float(bounds.bottom),
                "top": float(bounds.top),
            },
            "stats": {
                "min": round(vmin, 4),
                "max": round(vmax, 4),
                "mean": round(vmean, 4),
            },
            "shape": [int(target_h), int(target_w)],
            "data": normalized.tolist(),
        }
        
        print(f"  Shape: {target_h}x{target_w}")
        print(f"  Bounds: {bounds}")
        print(f"  NDVI: min={vmin:.4f}, max={vmax:.4f}, mean={vmean:.4f}")

output_file = DASHBOARD_DIR / "ndvi_arrays.js"
with open(output_file, "w") as f:
    f.write(f"// NDVI Data - Generated {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    f.write("// Auto-generated from GeoTIFF files\n\n")
    f.write("const NDVI_DATA = ")
    json.dump(ndvi_data, f, indent=2)
    f.write(";\n")

print(f"\n{'=' * 60}")
print(f"Output: {output_file}")
print(f"Size: {output_file.stat().st_size / 1024:.1f} KB")
print(f"Fields processed: {len(ndvi_data)}")