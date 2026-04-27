#!/usr/bin/env python3
"""Generate NDVI color images as base64 for dashboard embedding.

Reads NDVI GeoTIFF files and outputs:
1. PNG images using RdYlGn colormap (matching generate_ndvi.py)
2. Base64 encoded strings stored in JavaScript format
3. Metadata: bounds, shape, stats for each field
"""

import base64
import io
import json
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
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

print("=" * 60)
print("NDVI Color Image Generator for Dashboard")
print("=" * 60)

ndvi_color_data = {}

for field_id in FIELD_IDS:
    tiff_file = TIFF_DIR / TIFF_MAP[field_id]
    
    if not tiff_file.exists():
        print(f"  WARNING: {tiff_file} not found, skipping...")
        continue
    
    print(f"\nProcessing {field_id}...")
    
    with rasterio.open(tiff_file) as src:
        data = src.read(1)
        bounds = src.bounds
        
        nodata_val = src.nodata if src.nodata is not None else -9999
        
        valid_mask = (data != nodata_val) & (~np.isnan(data))
        valid_data = data[valid_mask]
        
        if len(valid_data) > 0:
            vmin = float(np.min(valid_data))
            vmax = float(np.max(valid_data))
            vmean = float(np.mean(valid_data))
        else:
            vmin = vmax = vmean = 0.0
        
        h, w = data.shape
        print(f"  Shape: {h}x{w}")
        print(f"  NDVI range: {vmin:.4f} to {vmax:.4f} (mean: {vmean:.4f})")
        
        extent = [bounds.left, bounds.right, bounds.bottom, bounds.top]
        
        fig, ax = plt.subplots(figsize=(10, 8))
        
        im = ax.imshow(
            data,
            cmap='RdYlGn',
            vmin=-1.0,
            vmax=1.0,
            extent=extent,
            origin='upper'
        )
        
        ax.set_xlim(extent[0], extent[1])
        ax.set_ylim(extent[2], extent[3])
        ax.set_axis_off()
        
        plt.tight_layout(pad=0)
        
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=80, bbox_inches='tight', pad_inches=0, transparent=True)
        plt.close()
        
        buf.seek(0)
        img_bytes = buf.read()
        b64_image = base64.b64encode(img_bytes).decode('utf-8')
        
        ndvi_color_data[field_id] = {
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
            "shape": [int(h), int(w)],
            "image": b64_image,
        }
        
        print(f"  Image size: {len(img_bytes) / 1024:.1f} KB")

output_file = DASHBOARD_DIR / "ndvi_color_data.js"
with open(output_file, "w") as f:
    f.write(f"// NDVI Color Images - Generated {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    f.write("// Auto-generated from GeoTIFF files using RdYlGn colormap\n\n")
    f.write("const NDVI_COLOR_DATA = ")
    json.dump(ndvi_color_data, f, indent=2)
    f.write(";\n")

print(f"\n{'=' * 60}")
print(f"Output: {output_file}")
print(f"Size: {output_file.stat().st_size / 1024:.1f} KB")
print(f"Fields processed: {len(ndvi_color_data)}")