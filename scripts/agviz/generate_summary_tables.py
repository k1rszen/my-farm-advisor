#!/usr/bin/env python3
"""Generate Farm Characteristics Summary Tables

Creates summary statistics tables for farm characteristics including:
- Soil properties quantitative traits
- Crop rotation statistics
- Drainage class distribution
- Predicted crop distribution

Output: data/workspace/output/crop_summary_stats.csv
"""

import pandas as pd
from pathlib import Path

DATA_DIR = Path("/workspaces/my-farm-advisor/data/workspace")
OUTPUT_DIR = DATA_DIR / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

soil_df = pd.read_csv(DATA_DIR / "NC_soil_crop_data_summary_EPSG4326_2026-04-01.csv")
rotation_df = pd.read_csv(DATA_DIR / "NC_soil_crop_data_cdl_rotation_EPSG4326_2026-04-01.csv")

def compute_summary_stats(df, columns, label):
    stats = df[columns].describe().T
    stats['median'] = df[columns].median()
    stats = stats[['count', 'mean', 'std', 'min', '25%', '50%', '75%', 'max', 'median']]
    stats.index.name = 'trait'
    return stats

soil_traits = ['avg_om_pct', 'avg_ph', 'avg_cec', 'avg_clay_pct', 'avg_sand_pct', 'avg_bulk_density', 'total_aws_inches']
soil_stats = compute_summary_stats(soil_df, soil_traits, 'soil')

rotation_traits = ['crop_diversity', 'corn_years', 'soybean_years']
rotation_stats = compute_summary_stats(rotation_df, rotation_traits, 'rotation')

drainage_dist = soil_df['drainage_class'].value_counts(dropna=False).to_frame('count')
drainage_dist.index.name = 'drainage_class'

pred_crop_dist = rotation_df['predicted_next_crop'].value_counts().to_frame('count')
pred_crop_dist.index.name = 'predicted_next_crop'

conf_dist = rotation_df['rotation_confidence'].value_counts().to_frame('count')
conf_dist.index.name = 'confidence_level'

with pd.ExcelWriter(OUTPUT_DIR / 'crop_summary_stats.xlsx') as writer:
    soil_stats.to_excel(writer, sheet_name='Soil_Properties')
    rotation_stats.to_excel(writer, sheet_name='Rotation_Stats')
    drainage_dist.to_excel(writer, sheet_name='Drainage_Distribution')
    pred_crop_dist.to_excel(writer, sheet_name='Predicted_Crop')
    conf_dist.to_excel(writer, sheet_name='Confidence_Distribution')

soil_stats['category'] = 'soil'
rotation_stats['category'] = 'rotation'
soil_stats = soil_stats.reset_index()
rotation_stats = rotation_stats.reset_index()

combined = pd.concat([soil_stats, rotation_stats], ignore_index=True)
combined = combined[['category', 'trait', 'count', 'mean', 'std', 'min', '25%', '50%', '75%', 'max', 'median']]
combined.to_csv(OUTPUT_DIR / 'crop_summary_stats.csv', index=False)

print("=" * 70)
print("FARM CHARACTERISTICS SUMMARY TABLES")
print("=" * 70)

print("\n--- Soil Properties Summary ---")
print(soil_stats.to_string(index=False))

print("\n--- Crop Rotation Summary ---")
print(rotation_stats.to_string(index=False))

print("\n--- Drainage Class Distribution ---")
print(drainage_dist.to_string())

print("\n--- Predicted Next Crop Distribution ---")
print(pred_crop_dist.to_string())

print("\n--- Rotation Confidence Distribution ---")
print(conf_dist.to_string())

print(f"\n✓ Saved to: {OUTPUT_DIR / 'crop_summary_stats.csv'}")
print(f"✓ Also saved to: {OUTPUT_DIR / 'crop_summary_stats.xlsx'}")
