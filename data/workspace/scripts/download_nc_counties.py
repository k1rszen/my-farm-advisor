#!/usr/bin/env python3
"""Download NC Piedmont counties from US Census Bureau TIGER/Line."""

import io
import tempfile
import zipfile
from pathlib import Path

import geopandas as gpd
import requests

OUTPUT_DIR = Path(__file__).resolve().parents[2] / "data" / "my-farm-advisor" / "shared" / "geoadmin" / "l2_counties"
OUTPUT_PATH = OUTPUT_DIR / "counties_usa.geojson"

NC_PIEDMONT_FIPS = [
    ("37", "051", "Cumberland"),
    ("37", "093", "Hoke"),
    ("37", "165", "Scotland"),
    ("37", "153", "Richmond"),
    ("37", "007", "Anson"),
    ("37", "179", "Union"),
    ("37", "167", "Stanly"),
    ("37", "025", "Cabarrus"),
    ("37", "159", "Rowan"),
    ("37", "097", "Iredell"),
    ("37", "057", "Davidson"),
    ("37", "059", "Davie"),
    ("37", "197", "Yadkin"),
    ("37", "067", "Forsyth"),
    ("37", "081", "Guilford"),
    ("37", "001", "Alamance"),
    ("37", "151", "Randolph"),
    ("37", "037", "Chatham"),
    ("37", "105", "Lee"),
    ("37", "125", "Moore"),
    ("37", "123", "Montgomery"),
    ("37", "069", "Franklin"),
    ("37", "077", "Granville"),
    ("37", "145", "Person"),
    ("37", "157", "Rockingham"),
]

CENSUS_URL = "https://www2.census.gov/geo/tiger/TIGER2023/COUNTY/tl_2023_us_county.zip"


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    print("Downloading US Counties from Census Bureau...")
    resp = requests.get(CENSUS_URL, timeout=120)
    resp.raise_for_status()
    
    with zipfile.ZipFile(io.BytesIO(resp.content)) as z:
        names = z.namelist()
        shp_name = [n for n in names if n.endswith(".shp")][0]
        base = shp_name.replace(".shp", "")
        
        with tempfile.TemporaryDirectory() as tmpdir:
            for ext in [".shp", ".dbf", ".shx", ".prj", ".cpg"]:
                part_name = base + ext
                if part_name in names:
                    (Path(tmpdir) / part_name).write_bytes(z.read(part_name))
            
            gdf = gpd.read_file(Path(tmpdir) / shp_name)
    
    print(f"Loaded {len(gdf)} counties")
    
    fips_set = {c[1] for c in NC_PIEDMONT_FIPS}
    filtered = gdf[
        (gdf["STATEFP"] == "37") & (gdf["COUNTYFP"].isin(fips_set))
    ].copy()
    
    filtered["state_fips"] = filtered["STATEFP"].astype(str).str.zfill(2)
    filtered["county_fips"] = filtered["COUNTYFP"].astype(str).str.zfill(3)
    filtered["county_name"] = filtered["NAME"]
    
    print(f"Filtered to {len(filtered)} NC Piedmont counties")
    
    filtered.to_file(OUTPUT_PATH, driver="GeoJSON")
    print(f"Saved to {OUTPUT_PATH}")
    
    return filtered


if __name__ == "__main__":
    main()
