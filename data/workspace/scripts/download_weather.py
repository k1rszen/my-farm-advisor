#!/usr/bin/env python3
"""Download NASA POWER weather data for top 5 largest NC fields."""

import time

import geopandas as gpd
import matplotlib.pyplot as plt
import pandas as pd
import requests
import seaborn as sns
from pathlib import Path
from shapely.geometry import Point

sns.set_style("whitegrid")
plt.rcParams["figure.dpi"] = 150

DATA_DIR = Path("/workspaces/my-farm-advisor/data/workspace")
OUTPUT_DIR = DATA_DIR / "output" / "assignment-06"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

API_URL = "https://power.larc.nasa.gov/api/temporal/daily/point"
PARAMS = ["T2M", "T2M_MAX", "T2M_MIN", "PRECTOTCORR", "ALLSKY_SFC_SW_DWN", "RH2M", "WS10M"]

START_DATE = "2020-01-01"
END_DATE = "2024-12-31"


def query_power(lat: float, lon: float, start: str, end: str) -> pd.DataFrame | None:
    """Query NASA POWER API for one point."""
    resp = requests.get(
        API_URL,
        params={
            "parameters": ",".join(PARAMS),
            "community": "AG",
            "longitude": lon,
            "latitude": lat,
            "start": start.replace("-", ""),
            "end": end.replace("-", ""),
            "format": "JSON",
        },
        timeout=60,
    )
    resp.raise_for_status()
    data = resp.json()

    param_data = data["properties"]["parameter"]
    dates = list(param_data[PARAMS[0]].keys())

    records = []
    for d in dates:
        row = {"date": pd.to_datetime(d, format="%Y%m%d")}
        for p in PARAMS:
            val = param_data.get(p, {}).get(d, -999.0)
            row[p] = val if val != -999.0 else None
        records.append(row)

    return pd.DataFrame(records)


def calculate_gdd(df: pd.DataFrame, base_temp: float = 10.0, cap_temp: float = 30.0) -> pd.DataFrame:
    """Calculate daily and cumulative GDD per field."""
    out = df.copy()
    out["date"] = pd.to_datetime(out["date"])
    out["year"] = out["date"].dt.year
    out["doy"] = out["date"].dt.dayofyear

    t_avg = ((out["T2M_MIN"] + out["T2M_MAX"]) / 2).clip(upper=cap_temp)
    out["gdd"] = (t_avg - base_temp).clip(lower=0)
    out["gdd_cumulative"] = out.sort_values("date").groupby("field_id")["gdd"].cumsum()

    return out


def create_visualizations(weather_gdd: pd.DataFrame, output_dir: Path) -> None:
    """Create temperature and GDD plots for each field."""
    for field_id in weather_gdd["field_id"].unique():
        field_data = weather_gdd[weather_gdd["field_id"] == field_id]
        years = field_data["year"].unique()

        for year in years:
            year_data = field_data[field_data["year"] == year].sort_values("date")
            if year_data.empty:
                continue

            fig, axes = plt.subplots(2, 1, figsize=(14, 8))

            ax1 = axes[0]
            ax1.fill_between(
                year_data["date"],
                year_data["T2M_MIN"],
                year_data["T2M_MAX"],
                alpha=0.3,
                label="Min/Max range",
            )
            ax1.plot(year_data["date"], year_data["T2M"], linewidth=0.8, label="Mean")
            ax1.axhline(0, color="grey", linewidth=0.5, linestyle="--")
            ax1.set_ylabel("Temperature (°C)")
            ax1.set_title(f"Daily Temperature — Field {field_id} ({year})")
            ax1.legend()

            ax2 = axes[1]
            ax2.plot(
                year_data["date"],
                year_data["gdd_cumulative"],
                linewidth=1.2,
                color="green",
            )
            ax2.set_ylabel("Cumulative GDD")
            ax2.set_xlabel("Date")
            ax2.set_title(f"Cumulative GDD — Field {field_id} ({year})")

            plt.tight_layout()
            plt.savefig(output_dir / f"weather_{field_id}_{year}.png", dpi=150)
            plt.close()

    print(f"Created {len(weather_gdd['field_id'].unique()) * len(years)} visualization(s)")


def main():
    print("Loading field boundaries...")
    fields = gpd.read_file(DATA_DIR / "NC_field_boundaries_EPSG4326_2026-04-01.geojson")
    fields["centroid"] = fields.geometry.centroid
    fields["lat"] = fields.centroid.y
    fields["lon"] = fields.centroid.x

    top5 = fields.nlargest(5, "area_acres")
    # Remove duplicate centroids - keep unique lat/lon pairs
    top5 = top5.drop_duplicates(subset=["lat", "lon"]).head(5)
    print(f"Selected top 5 fields by area (unique centroids):")
    print(top5[["field_id", "county_name", "area_acres", "lat", "lon"]].to_string(index=False))

    print(f"\nQuerying NASA POWER API for {len(top5)} fields...")
    print(f"Date range: {START_DATE} to {END_DATE}")

    all_weather = []
    for idx, row in top5.iterrows():
        field_id = row["field_id"]
        lat, lon = row["lat"], row["lon"]

        print(f"  Querying {field_id} at ({lat:.4f}, {lon:.4f})...")
        df = query_power(lat, lon, START_DATE, END_DATE)

        if df is not None:
            df.insert(0, "field_id", field_id)
            df.insert(1, "lat", lat)
            df.insert(2, "lon", lon)
            all_weather.append(df)

        time.sleep(1)

    weather = pd.concat(all_weather, ignore_index=True)
    print(f"\nRetrieved {len(weather)} rows")

    print("Calculating GDD...")
    weather_gdd = calculate_gdd(weather, base_temp=10.0)

    weather_gdd["month"] = weather_gdd["date"].dt.month
    weather_gdd["growing_season"] = weather_gdd["month"].isin([5, 6, 7, 8, 9])

    seasonal = (
        weather_gdd.groupby(["field_id", "year", "growing_season"])
        .agg(
            mean_temp=("T2M", "mean"),
            total_precip=("PRECTOTCORR", "sum"),
            total_solar=("ALLSKY_SFC_SW_DWN", "sum"),
            total_gdd=("gdd", "sum"),
            max_gdd_cumulative=("gdd_cumulative", "max"),
        )
        .reset_index()
    )

    growing_only = seasonal[seasonal["growing_season"]].copy()

    print("Creating visualizations...")
    create_visualizations(weather_gdd, OUTPUT_DIR)

    print("Saving outputs...")
    weather_csv = OUTPUT_DIR / "weather_top5_2020_2024.csv"
    weather_gdd.to_csv(weather_csv, index=False, date_format="%Y-%m-%d")
    print(f"  Saved daily weather: {weather_csv} ({len(weather_gdd)} rows)")

    weather_growing = weather_gdd[weather_gdd["growing_season"]].copy()
    weather_growing_csv = OUTPUT_DIR / "weather_top5_growing_season.csv"
    weather_growing.to_csv(weather_growing_csv, index=False, date_format="%Y-%m-%d")
    print(f"  Saved growing season weather: {weather_growing_csv} ({len(weather_growing)} rows)")

    summary_csv = OUTPUT_DIR / "weather_seasonal_summary.csv"
    growing_only.to_csv(summary_csv, index=False, date_format="%Y-%m-%d")
    print(f"  Saved seasonal summary: {summary_csv}")

    print("\nDone!")
    print(f"Output directory: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()