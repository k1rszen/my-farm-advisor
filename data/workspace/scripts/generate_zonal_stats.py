#!/usr/bin/env python3
"""
Generate zonal statistics by integrating soil, NDVI, and weather data at field level.

This script performs zonal statistics to integrate multi-source geospatial data:
1. Soil Data - Field-level aggregated soil properties (pH, OM, AWC, drainage)
2. NDVI Raster - Extract vegetation indices per field polygon
3. Weather Data - Seasonal aggregations per field (temperature, precipitation, GDD)

Output: Unified field-level summary with all integrated data sources.
"""

import pandas as pd
import geopandas as gpd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import sys

try:
    from rasterstats import zonal_stats
    import rasterio
except ImportError:
    print("ERROR: rasterstats and rasterio are required. Install with:")
    print("  pip install rasterstats rasterio")
    sys.exit(1)

sns.set_style("whitegrid")
plt.rcParams['figure.dpi'] = 150

DATA_DIR = Path("/workspaces/my-farm-advisor/data/workspace")
OUTPUT_DIR = DATA_DIR / "output" / "assignment-07"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def load_fields():
    """Load field boundaries from GeoJSON and compute centroids."""
    fields = gpd.read_file(DATA_DIR / "NC_field_boundaries_EPSG4326_2026-04-01.geojson")
    fields["centroid"] = fields.geometry.centroid
    fields["lat"] = fields.centroid.y
    fields["lon"] = fields.centroid.x
    print(f"[FIELDS] Loaded {len(fields)} fields, CRS: {fields.crs}")
    return fields


def aggregate_soil(soil_df):
    """Aggregate soil properties by field_id."""
    soil_agg = soil_df.groupby("field_id").agg(
        mukey_count=("mukey", "nunique"),
        drainage_primary=("drainagecl", lambda x: x.mode().iloc[0] if len(x.mode()) > 0 else None),
        om_mean=("om_r", "mean"),
        om_min=("om_r", "min"),
        om_max=("om_r", "max"),
        ph_mean=("ph1to1h2o_r", "mean"),
        ph_min=("ph1to1h2o_r", "min"),
        ph_max=("ph1to1h2o_r", "max"),
        awc_mean=("awc_r", "mean"),
        clay_mean=("claytotal_r", "mean"),
        sand_mean=("sandtotal_r", "mean"),
        cec_mean=("cec7_r", "mean"),
    ).reset_index()

    soil_agg = soil_agg.round(2)
    print(f"[SOIL] Aggregated to {len(soil_agg)} fields")
    return soil_agg


def extract_ndvi_zonal_multi(fields_gdf, ndvi_dir):
    """Extract zonal statistics from multiple NDVI rasters (one per field)."""
    field_ids = fields_gdf["field_id"].tolist()
    
    ndvi_rasters = {
        "osm-260949778": "osm-260949778_NDVI_EPSG4326.tif",
        "osm-1153259427": "osm-1153259427_NDVI.tif",
        "osm-813157720": "osm-813157720_NDVI.tif",
        "osm-1305439648": "osm-1305439648_NDVI.tif",
        "osm-1386621285": "osm-1386621285_NDVI.tif",
        "osm-1133139440": "osm-1133139440_NDVI.tif",
        "osm-1476971106": "osm-1476971106_NDVI.tif",
        "osm-834363677": "osm-834363677_NDVI.tif",
        "osm-548794709": "osm-548794709_NDVI.tif",
        "osm-199889806": "osm-199889806_NDVI.tif",
    }
    
    all_stats = []
    
    for field_id in field_ids:
        if field_id not in ndvi_rasters:
            continue
        
        raster_name = ndvi_rasters[field_id]
        raster_path = ndvi_dir / raster_name
        
        if not raster_path.exists():
            print(f"[NDVI] WARNING: Raster not found for {field_id}: {raster_path}")
            continue
        
        field_geom = fields_gdf[fields_gdf["field_id"] == field_id].copy()
        
        try:
            stats = zonal_stats(
                field_geom,
                str(raster_path),
                stats=["mean", "std", "min", "max", "median", "count"],
                prefix="ndvi_"
            )
            
            if stats:
                stat_row = stats[0]
                stat_row["field_id"] = field_id
                all_stats.append(stat_row)
                print(f"[NDVI] {field_id}: mean={stat_row['ndvi_mean']:.4f}, count={stat_row['ndvi_count']}")
        except Exception as e:
            print(f"[NDVI] ERROR processing {field_id}: {e}")
    
    if not all_stats:
        return pd.DataFrame(columns=["field_id", "ndvi_mean", "ndvi_std", "ndvi_min", "ndvi_max", "ndvi_median", "ndvi_count"])
    
    ndvi_df = pd.DataFrame(all_stats)
    print(f"[NDVI] Extracted stats for {len(ndvi_df)} fields")
    return ndvi_df


def aggregate_weather(weather_df):
    """Aggregate weather data by field for growing season (Apr-Sep)."""
    weather_df["date"] = pd.to_datetime(weather_df["date"])
    weather_df["year"] = weather_df["date"].dt.year
    weather_df["month"] = weather_df["date"].dt.month

    def calc_gdd(row, base=10, cap=30):
        t_avg = ((row["T2M_MIN"] + row["T2M_MAX"]) / 2)
        t_adj = min(max(t_avg, base), cap)
        return max(t_adj - base, 0)

    weather_df["gdd"] = weather_df.apply(calc_gdd, axis=1)

    weather_growing = weather_df[(weather_df["month"] >= 4) & (weather_df["month"] <= 9)]

    weather_agg = weather_growing.groupby("field_id").agg(
        temp_mean=("T2M", "mean"),
        temp_max_mean=("T2M_MAX", "mean"),
        temp_min_mean=("T2M_MIN", "mean"),
        precip_total=("PRECTOTCORR", "sum"),
        precip_days=("PRECTOTCORR", lambda x: (x > 0).sum()),
        gdd_total=("gdd", "sum"),
        solar_total=("ALLSKY_SFC_SW_DWN", "sum"),
        years=("year", "nunique")
    ).reset_index()

    weather_agg = weather_agg.round(2)
    print(f"[WEATHER] Aggregated for {len(weather_agg)} fields (growing season Apr-Sep)")
    return weather_agg


def integrate_all_sources(fields, soil_agg, ndvi_df, weather_agg):
    """Merge all data sources into single integrated dataframe."""
    integrated = fields[["field_id", "county_name", "area_acres", "lat", "lon"]].copy()

    integrated = integrated.merge(soil_agg, on="field_id", how="left")
    integrated = integrated.merge(ndvi_df, on="field_id", how="left")
    integrated = integrated.merge(weather_agg, on="field_id", how="left")

    print(f"[INTEGRATED] {len(integrated)} fields with all sources merged")
    return integrated


def generate_visualizations(integrated, output_dir):
    """Generate and save visualizations."""
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))

    ax1 = axes[0, 0]
    ax1.barh(integrated["field_id"], integrated["om_mean"], color="brown")
    ax1.set_xlabel("Organic Matter (%)")
    ax1.set_title("Mean Organic Matter by Field")

    ax2 = axes[0, 1]
    ax2.barh(integrated["field_id"], integrated["ph_mean"], color="green")
    ax2.set_xlabel("pH")
    ax2.set_title("Mean pH by Field")
    ax2.axvline(6.5, color="grey", linestyle="--", alpha=0.5, label="Optimal")
    ax2.axvline(5.5, color="grey", linestyle="--", alpha=0.5)

    ax3 = axes[1, 0]
    if "ndvi_mean" in integrated.columns:
        ndvi_data = integrated[integrated["ndvi_mean"].notna()]
        if len(ndvi_data) > 0:
            ax3.barh(ndvi_data["field_id"], ndvi_data["ndvi_mean"], color="darkgreen")
            ax3.set_xlabel("NDVI Mean")
            ax3.set_title("Mean NDVI by Field")
            for i, v in enumerate(ndvi_data["ndvi_mean"]):
                ax3.text(v + 0.01, i, f"{v:.3f}", va='center', fontsize=8)
        else:
            ax3.text(0.5, 0.5, "No NDVI data available", ha="center")
    else:
        ax3.text(0.5, 0.5, "No NDVI data available", ha="center")

    ax4 = axes[1, 1]
    gdd_annual = integrated["gdd_total"] / integrated["years"]
    ax4.barh(integrated["field_id"], gdd_annual, color="orange")
    ax4.set_xlabel("Annual GDD (growing season)")
    ax4.set_title("Mean GDD by Field")

    plt.tight_layout()
    plt.savefig(output_dir / "zonal_stats_summary.png", dpi=150)
    print(f"[VIS] Saved zonal_stats_summary.png")

    fig2, ax = plt.subplots(figsize=(10, 6))
    ax.scatter(integrated["om_mean"], integrated["gdd_total"], s=100, alpha=0.7)
    for i, row in integrated.iterrows():
        ax.annotate(row["field_id"][:10], (row["om_mean"], row["gdd_total"]), fontsize=8)
    ax.set_xlabel("Organic Matter (%)")
    ax.set_ylabel("Growing Season GDD")
    ax.set_title("Organic Matter vs. GDD by Field")
    plt.tight_layout()
    plt.savefig(output_dir / "om_vs_gdd.png", dpi=150)
    print(f"[VIS] Saved om_vs_gdd.png")


def main():
    print("=" * 60)
    print("Zonal Statistics Generator")
    print("=" * 60)

    print("\n--- Loading Field Boundaries ---")
    fields = load_fields()

    print("\n--- Loading and Aggregating Soil Data ---")
    soil = pd.read_csv(DATA_DIR / "NC_soil_crop_data_EPSG4326_2026-04-01.csv")
    print(f"[SOIL] Loaded {len(soil)} soil records")
    soil_agg = aggregate_soil(soil)

    print("\n--- Extracting NDVI Zonal Stats ---")
    ndvi_dir = DATA_DIR / "output" / "assignment-05"
    ndvi_df = extract_ndvi_zonal_multi(fields, ndvi_dir)

    print("\n--- Loading and Aggregating Weather Data ---")
    weather = pd.read_csv(DATA_DIR / "output" / "assignment-06" / "weather_top23_2020_2024.csv")
    print(f"[WEATHER] Loaded {len(weather)} daily weather records")
    weather_agg = aggregate_weather(weather)

    print("\n--- Integrating All Data Sources ---")
    integrated = integrate_all_sources(fields, soil_agg, ndvi_df, weather_agg)

    print("\n--- Saving CSV Output ---")
    output_csv = OUTPUT_DIR / "zonal_integration_summary.csv"
    integrated.to_csv(output_csv, index=False)
    print(f"[OUTPUT] Saved {output_csv}")

    print("\n--- Generating Visualizations ---")
    generate_visualizations(integrated, OUTPUT_DIR)

    print("\n--- Data Coverage Summary ---")
    coverage = pd.DataFrame({
        "field_id": integrated["field_id"],
        "soil": integrated[["om_mean", "ph_mean", "awc_mean"]].notna().all(axis=1),
        "ndvi": integrated["ndvi_mean"].notna() if "ndvi_mean" in integrated.columns else False,
        "weather": integrated["gdd_total"].notna()
    })
    print(coverage.to_string(index=False))
    print(f"\nFields with all three sources: {coverage[['soil', 'ndvi', 'weather']].all(axis=1).sum()}")

    print("\n" + "=" * 60)
    print("COMPLETE - All outputs saved to", OUTPUT_DIR)
    print("=" * 60)


if __name__ == "__main__":
    main()