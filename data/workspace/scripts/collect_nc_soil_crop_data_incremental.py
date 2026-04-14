#!/usr/bin/env python3
"""Incremental SSURGO + CDL collection for NC Piedmont fields.
Saves after every field so partial results survive timeout.
"""

from __future__ import annotations

import json
import time
from collections import Counter
from datetime import date
from pathlib import Path

import geopandas as gpd
import pandas as pd
import requests
import rasterio
from rasterstats import zonal_stats

# ── Paths ──────────────────────────────────────────────────────────────────
REPO_ROOT = Path("/workspaces/my-farm-advisor")
WORKSPACE = REPO_ROOT / "data" / "workspace"
FIELDS_PATH = WORKSPACE / "NC_field_boundaries_EPSG4326_2026-04-01.geojson"
OUTPUT_DIR = WORKSPACE
CDL_CACHE_DIR = OUTPUT_DIR / "cdl_cache"
PROGRESS_FILE = OUTPUT_DIR / "nc_soil_progress.json"

# ── Constants ───────────────────────────────────────────────────────────────
STATE_FIPS = "37"
SDA_URL = "https://sdmdataaccess.sc.egov.usda.gov/Tabular/post.rest"
MAX_DEPTH_CM = 30
TARGET_YEARS = [2021, 2022, 2023, 2024, 2025]
TODAY = date.today().isoformat()

CDL_CODES = {
    0: "No Data", 1: "Corn", 5: "Soybeans", 6: "Winter Wheat",
    24: "Winter Wheat", 27: "Rye", 28: "Alfalfa", 33: "Wheat",
    36: "Forest", 38: "Grassland/Pasture", 39: "Woody Wetlands",
    43: "Open Water", 61: "Fallow/Idle Cropland", 63: "Misc Crops",
    67: "Cotton", 121: "Developed/Open Space", 141: "Deciduous Forest",
    176: "Grass/Pasture", 190: "Xmas Trees",
}


# ── SSURGO helpers ─────────────────────────────────────────────────────────

def _query_sda(sql: str) -> list[dict]:
    last_error = None
    for timeout_s in (60, 120):
        for attempt in range(1, 5):
            try:
                resp = requests.post(SDA_URL, data={"query": sql, "format": "JSON"}, timeout=timeout_s)
                resp.raise_for_status()
                result = resp.json()
                if "Table" not in result:
                    return []
                cols = [
                    "mukey", "muname", "compname", "comppct_r", "drainagecl",
                    "hzdept_r", "hzdepb_r", "om_r", "ph1to1h2o_r", "awc_r",
                    "claytotal_r", "sandtotal_r", "silttotal_r", "dbthirdbar_r", "cec7_r",
                ]
                return [dict(zip(cols, row)) for row in result["Table"]]
            except Exception as exc:
                last_error = exc
                if attempt < 4:
                    time.sleep(2 * attempt)
    raise RuntimeError(f"SDA failed: {last_error}")


def _build_soil_query(wkt: str, max_depth: int = 30) -> str:
    safe_wkt = wkt.replace("'", "''")
    return f"""
    SELECT DISTINCT
        mu.mukey, mu.muname, c.compname, c.comppct_r, c.drainagecl,
        ch.hzdept_r, ch.hzdepb_r, ch.om_r, ch.ph1to1h2o_r, ch.awc_r,
        ch.claytotal_r, ch.sandtotal_r, ch.silttotal_r, ch.dbthirdbar_r, ch.cec7_r
    FROM mapunit mu
    INNER JOIN component c ON mu.mukey = c.mukey
    LEFT JOIN chorizon ch ON c.cokey = ch.cokey
    WHERE mu.mukey IN (
        SELECT * FROM SDA_Get_Mukey_from_intersection_with_WktWgs84('{safe_wkt}')
    )
    AND (ch.hzdept_r < {max_depth} OR ch.hzdept_r IS NULL)
    ORDER BY c.comppct_r DESC, ch.hzdept_r ASC
    """


def _classify_drainage(dc: str) -> str:
    m = {
        "Excessively drained": "excessive", "Somewhat excessively drained": "excessive",
        "Well drained": "good", "Moderately well drained": "good",
        "Somewhat poorly drained": "poor", "Poorly drained": "poor", "Very poorly drained": "poor",
    }
    return m.get(str(dc), "unknown")


# ── Progress helpers ───────────────────────────────────────────────────────

def load_progress() -> dict:
    if PROGRESS_FILE.exists():
        return json.loads(PROGRESS_FILE.read_text())
    return {"soil_done": [], "soil_rows": [], "cdl_done": [], "cdl_rows": []}


def save_progress(p: dict):
    PROGRESS_FILE.write_text(json.dumps(p, indent=2))


def soil_output_path() -> Path:
    return OUTPUT_DIR / f"NC_soil_crop_data_EPSG4326_{TODAY}.csv"


def summary_output_path() -> Path:
    return OUTPUT_DIR / f"NC_soil_crop_data_summary_EPSG4326_{TODAY}.csv"


def cdl_output_path() -> Path:
    return OUTPUT_DIR / f"NC_soil_crop_data_cdl_EPSG4326_{TODAY}.csv"


def rotation_output_path() -> Path:
    return OUTPUT_DIR / f"NC_soil_crop_data_cdl_rotation_EPSG4326_{TODAY}.csv"


# ── CDL helpers ────────────────────────────────────────────────────────────

def _download_cdl(year: int) -> Path:
    CDL_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    path = CDL_CACHE_DIR / f"CDL_{year}_{STATE_FIPS}.tif"
    if path.exists():
        print(f"  [CDL {year}] cached")
        return path
    url = f"https://nassgeodata.gmu.edu/nass_data_cache/byfips/CDL_{year}_{STATE_FIPS}.tif"
    print(f"  [CDL {year}] downloading...", end=" ", flush=True)
    resp = requests.get(url, timeout=300)
    if resp.status_code == 404:
        raise RuntimeError(f"CDL {year} not available")
    resp.raise_for_status()
    path.write_bytes(resp.content)
    print(f"OK ({path.stat().st_size // 1024 // 1024} MB)")
    return path


def _extract_cdl(fields_gdf: gpd.GeoDataFrame, cdl_path: Path, year: int) -> list[dict]:
    rows = []
    with rasterio.open(cdl_path) as src:
        proj = fields_gdf.to_crs(src.crs)
        for _, field in proj.iterrows():
            stats = zonal_stats(field.geometry, str(src.name), categorical=True)
            counts = stats[0] if stats else {}
            total = int(sum(counts.values()))
            if total <= 0:
                rows.append({
                    "field_id": field["field_id"], "year": year,
                    "crop_code": 0, "crop_name": "No Data",
                    "pixel_count": 0, "pct": 0.0,
                })
                continue
            for code, cnt in sorted(counts.items(), key=lambda x: x[1], reverse=True):
                rows.append({
                    "field_id": field["field_id"], "year": year,
                    "crop_code": int(code),
                    "crop_name": CDL_CODES.get(int(code), f"Code_{code}"),
                    "pixel_count": int(cnt),
                    "pct": round(float(cnt) / total * 100.0, 2),
                })
    return rows


def _rotation_outlook(names: list[str]) -> dict:
    if not names:
        return {"predicted_next_crop": "Unknown", "rotation_confidence": "none"}
    current = names[-1]
    followers = [names[i+1] for i, c in enumerate(names[:-1]) if c == current]
    if followers:
        counter = Counter(followers)
        best_count = max(counter.values())
        best = sorted(n for n, cnt in counter.items() if cnt == best_count)[0]
        conf = "high" if best_count >= 2 else "medium"
    else:
        best = names[-2] if len(names) >= 2 else current
        conf = "low"
    return {"predicted_next_crop": best, "rotation_confidence": conf}


# ── Main ─────────────────────────────────────────────────────────────────

def main():
    progress = load_progress()
    soil_done = set(progress["soil_done"])
    cdl_done = set(progress["cdl_done"])
    soil_rows = progress["soil_rows"]
    cdl_rows = progress["cdl_rows"]

    # Load fields
    fields = gpd.read_file(FIELDS_PATH)
    print(f"Loaded {len(fields)} fields. Soil done: {len(soil_done)}, CDL done: {len(cdl_done)}")

    # ── Phase 1: SSURGO ─────────────────────────────────────────────────
    print("\n[PHASE 1] SSURGO")
    print("-" * 40)
    for idx, (_, field) in enumerate(fields.iterrows(), 1):
        fid = str(field["field_id"])
        if fid in soil_done:
            print(f"  [{idx}/{len(fields)}] {fid} already done")
            continue

        geom = field.geometry
        print(f"  [{idx}/{len(fields)}] {fid}...", end=" ", flush=True)
        rows = []
        method = "none"

        try:
            rows = _query_sda(_build_soil_query(geom.wkt, MAX_DEPTH_CM))
            method = "polygon"
        except Exception:
            try:
                cent = geom.centroid
                rows = _query_sda(_build_soil_query(f"POINT({cent.x} {cent.y})", MAX_DEPTH_CM))
                method = "centroid"
            except Exception as exc:
                print(f"FAILED ({exc})")
                soil_done.add(fid)
                progress["soil_done"].append(fid)
                save_progress(progress)
                continue

        for row in rows:
            row["field_id"] = fid
            for num_col in [
                "comppct_r", "hzdept_r", "hzdepb_r", "om_r", "ph1to1h2o_r",
                "awc_r", "claytotal_r", "sandtotal_r", "silttotal_r",
                "dbthirdbar_r", "cec7_r",
            ]:
                if num_col in row and row[num_col] is not None:
                    try:
                        row[num_col] = float(row[num_col])
                    except (ValueError, TypeError):
                        row[num_col] = None
        soil_rows.extend(rows)
        soil_done.add(fid)
        progress["soil_done"].append(fid)

        if rows:
            dom = sorted(rows, key=lambda r: float(r.get("comppct_r", 0) or 0), reverse=True)[0]
            print(f"OK ({method}) -- {dom.get('compname','?')} {dom.get('comppct_r','?')}%")
        else:
            print(f"OK ({method}) -- no data")
            soil_rows.append({"field_id": fid})

        save_progress(progress)
        time.sleep(0.5)

    # Save soil CSV
    if soil_rows:
        soil_df = pd.DataFrame(soil_rows)
        soil_df.to_csv(soil_output_path(), index=False)
        print(f"\n  Saved soil: {soil_df['field_id'].nunique()} fields, {len(soil_df)} rows")

    # ── Phase 2: Soil summary ──────────────────────────────────────────
    print("\n[PHASE 2] Soil Summary")
    print("-" * 40)
    if soil_rows:
        soil_df = pd.DataFrame(soil_rows)
        summaries = []
        for fid, grp in soil_df.groupby("field_id"):
            sorted_grp = grp.sort_values(["comppct_r", "hzdept_r"], ascending=[False, True])
            if sorted_grp.empty:
                continue
            dom = sorted_grp.iloc[0]

            def wt_avg(col):
                valid = grp[col].notna() & grp["comppct_r"].notna()
                if not valid.any():
                    return None
                vals = grp.loc[valid, col]
                weights = grp.loc[valid, "comppct_r"]
                return round(float((vals * weights).sum() / weights.sum()), 4)

            summaries.append({
                "field_id": fid,
                "n_mukeys": grp["mukey"].nunique(),
                "n_components": grp["compname"].nunique(),
                "n_horizons": len(grp),
                "dominant_soil": dom.get("compname"),
                "dominant_mukey": dom.get("mukey"),
                "dominant_muname": dom.get("muname"),
                "drainage_class": dom.get("drainagecl"),
                "drainage_category": _classify_drainage(str(dom.get("drainagecl", ""))),
                "avg_om_pct": wt_avg("om_r"),
                "avg_ph": wt_avg("ph1to1h2o_r"),
                "avg_cec": wt_avg("cec7_r"),
                "avg_clay_pct": wt_avg("claytotal_r"),
                "avg_sand_pct": wt_avg("sandtotal_r"),
                "avg_bulk_density": wt_avg("dbthirdbar_r"),
                "total_aws_inches": round(float(grp["awc_r"].sum()), 4) if "awc_r" in grp.columns else None,
            })
        if summaries:
            smry_df = pd.DataFrame(summaries)
            smry_df.to_csv(summary_output_path(), index=False)
            print(f"  Saved: {smry_df['field_id'].nunique()} fields")
            print(f"  Avg OM: {smry_df['avg_om_pct'].mean():.2f}%  Avg pH: {smry_df['avg_ph'].mean():.2f}")

    # ── Phase 3: CDL ───────────────────────────────────────────────────
    print(f"\n[PHASE 3] CDL ({len(TARGET_YEARS)} years)")
    print("-" * 40)
    for year in TARGET_YEARS:
        year_str = str(year)
        if year_str in cdl_done:
            print(f"  [CDL {year}] already done")
            continue

        try:
            cdl_path = _download_cdl(year)
        except RuntimeError as exc:
            print(f"  [CDL {year}] SKIP: {exc}")
            cdl_done.add(year_str)
            progress["cdl_done"].append(year_str)
            save_progress(progress)
            continue

        try:
            rows = _extract_cdl(fields, cdl_path, year)
            cdl_rows.extend(rows)
            cdl_done.add(year_str)
            progress["cdl_done"].append(year_str)
            save_progress(progress)

            if rows:
                top = (pd.DataFrame(rows).sort_values("pct", ascending=False)
                       .groupby("field_id").first()["crop_name"]
                       .value_counts().head(3))
                print(f"  [CDL {year}] {len(rows)} rows -- top: {dict(top)}")
        except Exception as exc:
            print(f"  [CDL {year}] FAILED: {exc}")

    # ── Phase 4: Rotation ────────────────────────────────────────────────
    print("\n[PHASE 4] Crop Rotation")
    print("-" * 40)
    if cdl_rows:
        cdl_df = pd.DataFrame(cdl_rows)
        cdl_df.to_csv(cdl_output_path(), index=False)
        print(f"  CDL saved: {len(cdl_df)} rows")

        pct_col = "pct"
        dominant = (
            cdl_df.sort_values(["field_id", "year", pct_col], ascending=[True, True, False])
            .groupby(["field_id", "year"], as_index=False).first()
        )
        rotation_rows = []
        for fid, grp in dominant.groupby("field_id"):
            ordered = grp.sort_values("year")
            names = ordered["crop_name"].tolist()
            trans = [f"{names[i]}->{names[i+1]}" for i in range(len(names)-1)]
            outlook = _rotation_outlook(names)
            rotation_rows.append({
                "field_id": fid,
                "rotation_sequence": " -> ".join(names),
                "rotation_count": len(trans),
                "rotation_patterns": "; ".join(sorted(set(trans))) if trans else "none",
                "history_years": len(ordered),
                "history_start_year": int(ordered["year"].min()),
                "history_end_year": int(ordered["year"].max()),
                "crop_diversity": int(ordered["crop_name"].nunique()),
                "corn_years": int((ordered["crop_name"] == "Corn").sum()),
                "soybean_years": int((ordered["crop_name"] == "Soybeans").sum()),
                **outlook,
            })
        if rotation_rows:
            rot_df = pd.DataFrame(rotation_rows)
            rot_df.to_csv(rotation_output_path(), index=False)
            print(f"  Rotation saved: {len(rot_df)} fields")

    # ── Summary JSON ───────────────────────────────────────────────────
    print("\n[DONE]")
    soil_df = pd.DataFrame(soil_rows) if soil_rows else pd.DataFrame()
    cdl_df = pd.DataFrame(cdl_rows) if cdl_rows else pd.DataFrame()

    summary_json = {
        "date": TODAY, "region": "piedmont", "state_fips": STATE_FIPS,
        "fields_in_boundary": len(fields),
        "fields_with_soil": soil_df["field_id"].nunique() if not soil_df.empty and "field_id" in soil_df.columns else 0,
        "soil_records": len(soil_df),
        "cdl_years_extracted": [int(y) for y in cdl_df["year"].unique()] if not cdl_df.empty and "year" in cdl_df.columns else [],
        "cdl_records": len(cdl_df),
        "soil_avg_om_pct": round(float(soil_df["om_r"].mean()), 2) if not soil_df.empty and "om_r" in soil_df.columns else None,
        "soil_avg_ph": round(float(soil_df["ph1to1h2o_r"].mean()), 2) if not soil_df.empty and "ph1to1h2o_r" in soil_df.columns else None,
    }
    json_path = OUTPUT_DIR / f"NC_soil_crop_data_summary_{TODAY}.json"
    json_path.write_text(json.dumps(summary_json, indent=2))

    # Cleanup
    PROGRESS_FILE.unlink(missing_ok=True)

    print(f"\nOutput files:")
    for p in sorted(OUTPUT_DIR.glob(f"NC_soil_crop_data*_{TODAY}.*")):
        print(f"  {p.name}  ({p.stat().st_size // 1024} KB)")
    if CDL_CACHE_DIR.exists():
        n = len(list(CDL_CACHE_DIR.glob("*.tif")))
        mb = sum(p.stat().st_size for p in CDL_CACHE_DIR.glob("*.tif")) // 1024 // 1024
        print(f"CDL cache: {n} files ({mb} MB)")


if __name__ == "__main__":
    main()
