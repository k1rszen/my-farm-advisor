#!/usr/bin/env python3
"""Collect field boundaries from NC Piedmont counties via OSM Overpass API.

Target: 25 counties, 1 largest field per county, >=3 acres.
Output: data/workspace/NC_field_boundaries_EPSG4326_<date>.geojson
Saves progress incrementally so partial results survive timeout.
"""

import json
import time
from datetime import date
from pathlib import Path
from typing import Any

import geopandas as gpd
import pandas as pd
import requests
from shapely.geometry import Polygon

REPO_ROOT = Path(__file__).resolve().parents[2]
COUNTIES_PATH = REPO_ROOT / "data" / "my-farm-advisor" / "shared" / "geoadmin" / "l2_counties" / "counties_usa.geojson"
OUTPUT_DIR = REPO_ROOT / "data" / "workspace"
SCRIPT_DIR = OUTPUT_DIR / "scripts"
PROGRESS_FILE = OUTPUT_DIR / "nc_piedmont_progress.json"
DONE_FILE = OUTPUT_DIR / "nc_piedmont_done.geojson"

OVERPASS_URLS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://lz4.overpass-api.de/api/interpreter",
]
MIN_ACRES = 3.0
OVERPASS_TIMEOUT = 300
OVERPASS_RETRIES = 5

TARGET_COUNTIES = [
    {"state_fips": "37", "county_fips": "051", "county_name": "Cumberland"},
    {"state_fips": "37", "county_fips": "093", "county_name": "Hoke"},
    {"state_fips": "37", "county_fips": "165", "county_name": "Scotland"},
    {"state_fips": "37", "county_fips": "153", "county_name": "Richmond"},
    {"state_fips": "37", "county_fips": "007", "county_name": "Anson"},
    {"state_fips": "37", "county_fips": "179", "county_name": "Union"},
    {"state_fips": "37", "county_fips": "167", "county_name": "Stanly"},
    {"state_fips": "37", "county_fips": "025", "county_name": "Cabarrus"},
    {"state_fips": "37", "county_fips": "159", "county_name": "Rowan"},
    {"state_fips": "37", "county_fips": "097", "county_name": "Iredell"},
    {"state_fips": "37", "county_fips": "057", "county_name": "Davidson"},
    {"state_fips": "37", "county_fips": "059", "county_name": "Davie"},
    {"state_fips": "37", "county_fips": "197", "county_name": "Yadkin"},
    {"state_fips": "37", "county_fips": "067", "county_name": "Forsyth"},
    {"state_fips": "37", "county_fips": "081", "county_name": "Guilford"},
    {"state_fips": "37", "county_fips": "001", "county_name": "Alamance"},
    {"state_fips": "37", "county_fips": "151", "county_name": "Randolph"},
    {"state_fips": "37", "county_fips": "037", "county_name": "Chatham"},
    {"state_fips": "37", "county_fips": "105", "county_name": "Lee"},
    {"state_fips": "37", "county_fips": "125", "county_name": "Moore"},
    {"state_fips": "37", "county_fips": "123", "county_name": "Montgomery"},
    {"state_fips": "37", "county_fips": "069", "county_name": "Franklin"},
    {"state_fips": "37", "county_fips": "077", "county_name": "Granville"},
    {"state_fips": "37", "county_fips": "145", "county_name": "Person"},
    {"state_fips": "37", "county_fips": "157", "county_name": "Rockingham"},
]


def _load_counties() -> gpd.GeoDataFrame:
    if not COUNTIES_PATH.exists():
        raise FileNotFoundError(
            f"Counties file not found at {COUNTIES_PATH}. "
            "Run: python data/workspace/scripts/download_nc_counties.py"
        )
    return gpd.read_file(COUNTIES_PATH)


def _query_overpass(bbox: tuple[float, float, float, float]) -> dict[str, Any]:
    south, west, north, east = bbox
    query = f"""
    [out:json][timeout:{OVERPASS_TIMEOUT}];
    (
      way["landuse"~"farmland|orchard|vineyard|meadow"]({south},{west},{north},{east});
    );
    out geom;
    """
    last_error: Exception | None = None
    for endpoint in OVERPASS_URLS:
        for attempt in range(1, OVERPASS_RETRIES + 1):
            try:
                response = requests.post(endpoint, data={"data": query}, timeout=OVERPASS_TIMEOUT + 30)
                response.raise_for_status()
                return response.json()
            except Exception as exc:
                last_error = exc
                wait = 5.0 * attempt
                print(f"    Attempt {attempt} failed ({exc}), waiting {wait}s...")
                time.sleep(wait)
    raise RuntimeError(f"Overpass query failed for all endpoints: {last_error}")


def _elements_to_fields(
    elements: list[dict[str, Any]],
    county_geom: Any,
    county: dict[str, str],
) -> gpd.GeoDataFrame:
    records: list[dict[str, Any]] = []
    county_gdf = gpd.GeoDataFrame([{"geometry": county_geom}], crs="EPSG:4326")

    for element in elements:
        if element.get("type") != "way":
            continue
        geometry_points = element.get("geometry", [])
        if len(geometry_points) < 4:
            continue
        ring = [(point["lon"], point["lat"]) for point in geometry_points]
        if ring[0] != ring[-1]:
            ring.append(ring[0])

        try:
            polygon = Polygon(ring)
            if not polygon.is_valid or polygon.is_empty or polygon.area == 0:
                continue
        except Exception:
            continue

        field_gdf = gpd.GeoDataFrame([{"geometry": polygon}], crs="EPSG:4326")
        clipped = gpd.overlay(field_gdf, county_gdf, how="intersection")
        if clipped.empty:
            continue
        clipped_geom = clipped.geometry.iloc[0]
        if clipped_geom.is_empty:
            continue

        tags = element.get("tags", {})
        records.append(
            {
                "field_id": f"osm-{element.get('id')}",
                "source": "OpenStreetMap/Overpass",
                "crop_name": str(tags.get("crop") or tags.get("landuse", "Unknown")),
                "state_fips": county["state_fips"],
                "county_fips": county["county_fips"],
                "county_name": county["county_name"],
                "region": "piedmont",
                "geometry": clipped_geom,
            }
        )

    if not records:
        return gpd.GeoDataFrame(
            columns=["field_id", "geometry"], geometry="geometry", crs="EPSG:4326"
        )

    gdf = gpd.GeoDataFrame(records, geometry="geometry", crs="EPSG:4326")
    gdf = gdf.drop_duplicates(subset=["field_id"]).reset_index(drop=True)
    gdf["area_acres"] = gdf.to_crs("EPSG:5070").geometry.area / 4046.8564224
    gdf = gdf[gdf["area_acres"] >= MIN_ACRES].copy()
    return gdf


def _select_largest(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    if gdf.empty:
        return gdf
    return gdf.sort_values("area_acres", ascending=False).head(1).reset_index(drop=True)


def _load_progress() -> dict[str, Any]:
    if PROGRESS_FILE.exists():
        with PROGRESS_FILE.open() as f:
            return json.load(f)
    return {"collected": [], "skipped": [], "fields": {}}


def _save_progress(progress: dict[str, Any]):
    with PROGRESS_FILE.open("w") as f:
        json.dump(progress, f, indent=2)


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    SCRIPT_DIR.mkdir(parents=True, exist_ok=True)

    counties_gdf = _load_counties()
    progress = _load_progress()
    collected_counties = set(progress["collected"])
    skipped_counties = set(progress["skipped"])

    print(f"Resuming: {len(collected_counties)} collected, {len(skipped_counties)} skipped")

    for county in TARGET_COUNTIES:
        county_fips = county["county_fips"]
        county_name = county["county_name"]

        if county_name in collected_counties:
            print(f"[SKIP] {county_name}: already collected")
            continue
        if county_name in skipped_counties:
            print(f"[SKIP] {county_name}: previously skipped")
            continue

        match = counties_gdf[
            (counties_gdf["state_fips"].astype(str).str.zfill(2) == county["state_fips"])
            & (counties_gdf["county_fips"].astype(str).str.zfill(3) == county_fips)
        ]
        if match.empty:
            print(f"[SKIP] {county_name}: not found in counties layer")
            skipped_counties.add(county_name)
            progress["skipped"].append(county_name)
            _save_progress(progress)
            continue

        county_geom = match.geometry.iloc[0]
        bounds = match.total_bounds
        bbox = (float(bounds[1]), float(bounds[0]), float(bounds[3]), float(bounds[2]))

        print(f"[QUERY] {county_name}...", end=" ", flush=True)
        try:
            payload = _query_overpass(bbox)
        except RuntimeError as exc:
            print(f"FAILED ({exc})")
            skipped_counties.add(county_name)
            progress["skipped"].append(county_name)
            _save_progress(progress)
            continue

        fields = _elements_to_fields(
            elements=payload.get("elements", []),
            county_geom=county_geom,
            county=county,
        )

        if fields.empty:
            print("no eligible fields")
            skipped_counties.add(county_name)
            progress["skipped"].append(county_name)
            _save_progress(progress)
            continue

        selected = _select_largest(fields)
        
        # Save individual field to done file
        if DONE_FILE.exists():
            done_gdf = gpd.read_file(DONE_FILE)
            new_gdf = gpd.GeoDataFrame(pd.concat([done_gdf, selected], ignore_index=True), crs="EPSG:4326")
        else:
            new_gdf = selected
        new_gdf.to_file(DONE_FILE, driver="GeoJSON")

        collected_counties.add(county_name)
        progress["collected"].append(county_name)
        progress["fields"][county_name] = {
            "field_id": selected["field_id"].iloc[0],
            "area_acres": round(float(selected["area_acres"].iloc[0]), 2),
            "crop_name": selected["crop_name"].iloc[0],
        }
        _save_progress(progress)

        print(
            f"OK -- {selected['area_acres'].iloc[0]:.1f} acres "
            f"({selected['crop_name'].iloc[0]})"
        )

    # Finalize
    if not DONE_FILE.exists():
        raise RuntimeError("No fields collected")

    merged = gpd.read_file(DONE_FILE)
    merged = merged.sort_values("county_name").reset_index(drop=True)

    output_date = date.today().isoformat()
    geojson_path = OUTPUT_DIR / f"NC_field_boundaries_EPSG4326_{output_date}.geojson"
    merged.to_file(geojson_path, driver="GeoJSON")
    print(f"\n[Saved] {geojson_path} ({len(merged)} fields)")

    # Clean up temp files
    PROGRESS_FILE.unlink(missing_ok=True)
    DONE_FILE.unlink(missing_ok=True)

    summary = {
        "date": output_date,
        "min_acres": MIN_ACRES,
        "region": "piedmont",
        "state_fips": "37",
        "counties_targeted": len(TARGET_COUNTIES),
        "fields_collected": len(merged),
        "total_area_acres": round(float(merged["area_acres"].sum()), 2),
        "fields_by_county": progress["fields"],
        "skipped_counties": list(skipped_counties),
    }

    summary_path = OUTPUT_DIR / f"NC_field_boundaries_summary_{output_date}.json"
    with summary_path.open("w") as fh:
        json.dump(summary, fh, indent=2)
    print(f"[Saved] {summary_path}")

    return summary


if __name__ == "__main__":
    main()
