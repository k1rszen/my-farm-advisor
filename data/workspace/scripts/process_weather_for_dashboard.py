#!/usr/bin/env python3
"""Process weather CSV data for dashboard.

Reads weather_top10_2020_2024.csv and outputs:
1. Monthly aggregated temperature and precipitation
2. 2024 vs 5-year average (2020-2024) comparisons
3. JavaScript constants for embedded dashboard
"""

import pandas as pd
import json
from pathlib import Path
from datetime import datetime

DATA_DIR = Path("data/workspace/output")
DASHBOARD_DIR = DATA_DIR / "dashboard"

print("=" * 60)
print("Weather Data Processor for Dashboard")
print("=" * 60)

weather_df = pd.read_csv(DATA_DIR / "assignment-06/weather_top10_2020_2024.csv")

print(f"\nLoaded {len(weather_df)} weather records")
print(f"Fields: {weather_df['field_id'].nunique()}")
print(f"Years: {sorted(weather_df['year'].unique())}")

months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", 
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

weather_data = {}

for field_id in weather_df['field_id'].unique():
    field_df = weather_df[weather_df['field_id'] == field_id].copy()
    
    monthly_stats = []
    
    for month in range(1, 13):
        month_df = field_df[field_df['month'] == month]
        
        data_2024 = month_df[month_df['year'] == 2024]
        data_5yr = month_df
        
        temp_2024 = data_2024['T2M'].mean() if len(data_2024) > 0 else None
        temp_5yr = data_5yr['T2M'].mean() if len(data_5yr) > 0 else None
        
        precip_2024 = data_2024['PRECTOTCORR'].sum() if len(data_2024) > 0 else None
        precip_5yr = data_5yr['PRECTOTCORR'].sum() / 5 if len(data_5yr) > 0 else None
        
        monthly_stats.append({
            "month": months[month - 1],
            "temp_2024": round(temp_2024, 1) if temp_2024 else 0,
            "temp_5yr": round(temp_5yr, 1) if temp_5yr else 0,
            "precip_2024": round(precip_2024, 1) if precip_2024 else 0,
            "precip_5yr": round(precip_5yr, 1) if precip_5yr else 0,
        })
    
    weather_data[field_id] = {
        "monthly": monthly_stats,
        "annual": {
            "temp_2024": round(field_df[field_df['year'] == 2024]['T2M'].mean(), 1),
            "temp_5yr": round(field_df['T2M'].mean(), 1),
            "precip_2024": round(field_df[field_df['year'] == 2024]['PRECTOTCORR'].sum(), 1),
            "precip_5yr": round(field_df['PRECTOTCORR'].sum() / 5, 1),
        }
    }

output_file = DASHBOARD_DIR / "weather_data.js"
with open(output_file, "w") as f:
    f.write(f"// Weather Data - Generated {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    f.write("// Monthly aggregates: 2024 vs 5-year average (2020-2024)\n\n")
    f.write("const WEATHER_DATA = ")
    json.dump(weather_data, f, indent=2)
    f.write(";\n")

print(f"\n{'=' * 60}")
print(f"Output: {output_file}")
print(f"Size: {output_file.stat().st_size / 1024:.1f} KB")

sample_field = list(weather_data.keys())[0]
print(f"\nSample data for {sample_field}:")
print(f"  Annual temp 2024: {weather_data[sample_field]['annual']['temp_2024']}°C")
print(f"  Annual precip 2024: {weather_data[sample_field]['annual']['precip_2024']}mm")
print(f"  Jan 2024 temp: {weather_data[sample_field]['monthly'][0]['temp_2024']}°C")
print(f"  Jan precip 5yr avg: {weather_data[sample_field]['monthly'][0]['precip_5yr']}mm")