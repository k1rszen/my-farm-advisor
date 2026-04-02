#!/usr/bin/env python3
"""Field Data EDA Analysis

Explores NC soil/crop data and CDL rotation data using .describe() and .info().
Generates summary statistics and visualization figures.

Outputs:
- data/workspace/plots/*.png - Visualization figures
- Console: Summary statistics tables
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
from pathlib import Path

sns.set_style("whitegrid")
plt.rcParams['figure.dpi'] = 150

DATA_DIR = Path("/workspaces/my-farm-advisor/data/workspace")
OUTPUT_DIR = DATA_DIR / "plots"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

print("=" * 70)
print("EXPLORATORY DATA ANALYSIS: NC Field Data")
print("=" * 70)

# Load datasets
soil_df = pd.read_csv(DATA_DIR / "NC_soil_crop_data_summary_EPSG4326_2026-04-01.csv")
rotation_df = pd.read_csv(DATA_DIR / "NC_soil_crop_data_cdl_rotation_EPSG4326_2026-04-01.csv")

print(f"\nLoaded datasets:")
print(f"  Soil/Crop Summary: {soil_df.shape[0]} fields x {soil_df.shape[1]} columns")
print(f"  CDL Rotation: {rotation_df.shape[0]} fields x {rotation_df.shape[1]} columns")

# =============================================================================
# PART 1: DATA PROFILING (eda-explore)
# =============================================================================
print("\n" + "=" * 70)
print("PART 1: DATA PROFILING")
print("=" * 70)

print("\n--- SOIL/CROP DATA: .info() ---")
soil_df.info()

print("\n--- SOIL/CROP DATA: .describe() ---")
desc = soil_df.describe()
print(desc.T)

print("\n--- CDL ROTATION DATA: .info() ---")
rotation_df.info()

print("\n--- CDL ROTATION DATA: .describe() ---")
rot_desc = rotation_df.describe()
print(rot_desc.T)

# Missing values
print("\n--- Missing Values: Soil Data ---")
missing_soil = soil_df.isnull().sum()
print(missing_soil[missing_soil > 0] if missing_soil.sum() > 0 else "No missing values")

print("\n--- Missing Values: Rotation Data ---")
missing_rot = rotation_df.isnull().sum()
print(missing_rot[missing_rot > 0] if missing_rot.sum() > 0 else "No missing values")

# =============================================================================
# PART 2: SOIL PROPERTIES VISUALIZATIONS
# =============================================================================
print("\n" + "=" * 70)
print("PART 2: SOIL PROPERTIES ANALYSIS")
print("=" * 70)

# Numeric columns for analysis
numeric_cols = ['avg_om_pct', 'avg_ph', 'avg_cec', 'avg_clay_pct', 'avg_sand_pct', 'avg_bulk_density', 'total_aws_inches']

# 1. Histogram: pH Distribution
fig, ax = plt.subplots(figsize=(10, 6))
sns.histplot(data=soil_df, x='avg_ph', bins=12, kde=True, color='steelblue', ax=ax)
ax.set_title('Soil pH Distribution', fontsize=14, fontweight='bold')
ax.set_xlabel('Average pH', fontsize=12)
ax.set_ylabel('Frequency', fontsize=12)
ax.axvline(soil_df['avg_ph'].mean(), color='red', linestyle='--', label=f"Mean: {soil_df['avg_ph'].mean():.2f}")
ax.legend()
plt.tight_layout()
plt.savefig(OUTPUT_DIR / "soil_ph_distribution.png", dpi=300, bbox_inches='tight')
plt.close()
print("Created: plots/soil_ph_distribution.png")

# 2. Histogram: Organic Matter
fig, ax = plt.subplots(figsize=(10, 6))
sns.histplot(data=soil_df, x='avg_om_pct', bins=12, kde=True, color='forestgreen', ax=ax)
ax.set_title('Organic Matter Distribution', fontsize=14, fontweight='bold')
ax.set_xlabel('Organic Matter (%)', fontsize=12)
ax.set_ylabel('Frequency', fontsize=12)
ax.axvline(soil_df['avg_om_pct'].mean(), color='red', linestyle='--', label=f"Mean: {soil_df['avg_om_pct'].mean():.2f}%")
ax.legend()
plt.tight_layout()
plt.savefig(OUTPUT_DIR / "soil_om_distribution.png", dpi=300, bbox_inches='tight')
plt.close()
print("Created: plots/soil_om_distribution.png")

# 3. Scatter: pH vs Organic Matter
fig, ax = plt.subplots(figsize=(10, 6))
sns.scatterplot(data=soil_df, x='avg_ph', y='avg_om_pct', hue='drainage_class', s=100, alpha=0.7, ax=ax)
ax.set_title('Soil pH vs Organic Matter by Drainage Class', fontsize=14, fontweight='bold')
ax.set_xlabel('Average pH', fontsize=12)
ax.set_ylabel('Organic Matter (%)', fontsize=12)
ax.legend(title='Drainage Class', bbox_to_anchor=(1.05, 1), loc='upper left')
plt.tight_layout()
plt.savefig(OUTPUT_DIR / "soil_ph_vs_om.png", dpi=300, bbox_inches='tight')
plt.close()
print("Created: plots/soil_ph_vs_om.png")

# 4. Correlation Heatmap: Soil Properties
fig, ax = plt.subplots(figsize=(10, 8))
corr_cols = ['avg_om_pct', 'avg_ph', 'avg_cec', 'avg_clay_pct', 'avg_sand_pct', 'avg_bulk_density', 'total_aws_inches']
corr_matrix = soil_df[corr_cols].corr()
sns.heatmap(corr_matrix, annot=True, cmap='coolwarm', center=0, fmt='.2f', square=True, ax=ax)
ax.set_title('Soil Properties Correlation Matrix', fontsize=14, fontweight='bold')
plt.tight_layout()
plt.savefig(OUTPUT_DIR / "soil_correlation_heatmap.png", dpi=300, bbox_inches='tight')
plt.close()
print("Created: plots/soil_correlation_heatmap.png")

# 5. Box Plot: pH by Drainage Class
drainage_valid = soil_df[soil_df['drainage_class'].notna() & (soil_df['drainage_class'] != '')]
fig, ax = plt.subplots(figsize=(12, 6))
sns.boxplot(data=drainage_valid, x='drainage_class', y='avg_ph', palette='Set2', ax=ax)
ax.set_title('Soil pH by Drainage Class', fontsize=14, fontweight='bold')
ax.set_xlabel('Drainage Class', fontsize=12)
ax.set_ylabel('Average pH', fontsize=12)
ax.tick_params(axis='x', rotation=30)
plt.tight_layout()
plt.savefig(OUTPUT_DIR / "soil_ph_by_drainage.png", dpi=300, bbox_inches='tight')
plt.close()
print("Created: plots/soil_ph_by_drainage.png")

# 6. Box Plot: Available Water Storage by Drainage Class
fig, ax = plt.subplots(figsize=(12, 6))
sns.boxplot(data=drainage_valid, x='drainage_class', y='total_aws_inches', palette='Set2', ax=ax)
ax.set_title('Available Water Storage by Drainage Class', fontsize=14, fontweight='bold')
ax.set_xlabel('Drainage Class', fontsize=12)
ax.set_ylabel('Total AWS (inches)', fontsize=12)
ax.tick_params(axis='x', rotation=30)
plt.tight_layout()
plt.savefig(OUTPUT_DIR / "soil_aws_by_drainage.png", dpi=300, bbox_inches='tight')
plt.close()
print("Created: plots/soil_aws_by_drainage.png")

# =============================================================================
# PART 3: CDL ROTATION ANALYSIS
# =============================================================================
print("\n" + "=" * 70)
print("PART 3: CDL ROTATION ANALYSIS")
print("=" * 70)

# 7. Bar Chart: Crop Diversity Distribution
fig, ax = plt.subplots(figsize=(10, 6))
diversity_counts = rotation_df['crop_diversity'].value_counts().sort_index()
sns.barplot(x=diversity_counts.index, y=diversity_counts.values, palette='viridis', ax=ax)
ax.set_title('Crop Diversity Distribution Across Fields', fontsize=14, fontweight='bold')
ax.set_xlabel('Number of Different Crops in Rotation', fontsize=12)
ax.set_ylabel('Number of Fields', fontsize=12)
for i, v in enumerate(diversity_counts.values):
    ax.text(i, v + 0.1, str(v), ha='center', fontweight='bold')
plt.tight_layout()
plt.savefig(OUTPUT_DIR / "rotation_crop_diversity.png", dpi=300, bbox_inches='tight')
plt.close()
print("Created: plots/rotation_crop_diversity.png")

# 8. Bar Chart: Predicted Next Crop
fig, ax = plt.subplots(figsize=(12, 6))
pred_crop_counts = rotation_df['predicted_next_crop'].value_counts()
sns.barplot(x=pred_crop_counts.index, y=pred_crop_counts.values, palette='magma', ax=ax)
ax.set_title('Predicted Next Crop Distribution', fontsize=14, fontweight='bold')
ax.set_xlabel('Predicted Crop', fontsize=12)
ax.set_ylabel('Number of Fields', fontsize=12)
ax.tick_params(axis='x', rotation=45)
plt.tight_layout()
plt.savefig(OUTPUT_DIR / "rotation_predicted_crop.png", dpi=300, bbox_inches='tight')
plt.close()
print("Created: plots/rotation_predicted_crop.png")

# 9. Bar Chart: Rotation Confidence
fig, ax = plt.subplots(figsize=(8, 5))
conf_counts = rotation_df['rotation_confidence'].value_counts()
sns.barplot(x=conf_counts.index, y=conf_counts.values, palette='coolwarm', ax=ax)
ax.set_title('Rotation Confidence Levels', fontsize=14, fontweight='bold')
ax.set_xlabel('Confidence Level', fontsize=12)
ax.set_ylabel('Number of Fields', fontsize=12)
for i, v in enumerate(conf_counts.values):
    ax.text(i, v + 0.1, str(v), ha='center', fontweight='bold')
plt.tight_layout()
plt.savefig(OUTPUT_DIR / "rotation_confidence.png", dpi=300, bbox_inches='tight')
plt.close()
print("Created: plots/rotation_confidence.png")

# 10. Stacked Bar: Corn vs Soybean Years
fig, ax = plt.subplots(figsize=(10, 6))
x = range(len(rotation_df))
width = 0.6
ax.bar(x, rotation_df['corn_years'], width, label='Corn Years', color='gold')
ax.bar(x, rotation_df['soybean_years'], width, bottom=rotation_df['corn_years'], label='Soybean Years', color='olivedrab')
ax.set_xlabel('Field Index', fontsize=12)
ax.set_ylabel('Years in Rotation (out of 5)', fontsize=12)
ax.set_title('Corn vs Soybean Rotation History', fontsize=14, fontweight='bold')
ax.legend()
plt.tight_layout()
plt.savefig(OUTPUT_DIR / "rotation_corn_soybean.png", dpi=300, bbox_inches='tight')
plt.close()
print("Created: plots/rotation_corn_soybean.png")

# =============================================================================
# PART 4: COMBINED ANALYSIS
# =============================================================================
print("\n" + "=" * 70)
print("PART 4: COMBINED ANALYSIS")
print("=" * 70)

# Merge datasets on field_id
merged_df = pd.merge(soil_df, rotation_df, on='field_id', how='inner')
print(f"\nMerged dataset: {merged_df.shape[0]} fields")

# 11. Scatter: Crop Diversity vs Organic Matter
fig, ax = plt.subplots(figsize=(10, 6))
sns.scatterplot(data=merged_df, x='crop_diversity', y='avg_om_pct', hue='drainage_category', s=100, alpha=0.7, ax=ax)
ax.set_title('Crop Diversity vs Organic Matter', fontsize=14, fontweight='bold')
ax.set_xlabel('Crop Diversity (unique crops)', fontsize=12)
ax.set_ylabel('Organic Matter (%)', fontsize=12)
ax.legend(title='Drainage', bbox_to_anchor=(1.05, 1), loc='upper left')
plt.tight_layout()
plt.savefig(OUTPUT_DIR / "combined_diversity_vs_om.png", dpi=300, bbox_inches='tight')
plt.close()
print("Created: plots/combined_diversity_vs_om.png")

# 12. Box Plot: Corn Years by Drainage Category
corn_by_drainage = merged_df[merged_df['drainage_category'].notna()]
fig, ax = plt.subplots(figsize=(10, 6))
sns.boxplot(data=corn_by_drainage, x='drainage_category', y='corn_years', palette='Set2', ax=ax)
ax.set_title('Corn Years in Rotation by Drainage Category', fontsize=14, fontweight='bold')
ax.set_xlabel('Drainage Category', fontsize=12)
ax.set_ylabel('Corn Years (out of 5)', fontsize=12)
plt.tight_layout()
plt.savefig(OUTPUT_DIR / "combined_corn_by_drainage.png", dpi=300, bbox_inches='tight')
plt.close()
print("Created: plots/combined_corn_by_drainage.png")

# =============================================================================
# SUMMARY TABLE
# =============================================================================
print("\n" + "=" * 70)
print("SUMMARY STATISTICS")
print("=" * 70)

print("\n--- Soil Properties Summary ---")
summary_stats = soil_df[numeric_cols].agg(['mean', 'std', 'min', 'max']).T
summary_stats['median'] = soil_df[numeric_cols].median()
print(summary_stats.round(3))

print("\n--- Rotation Summary ---")
rot_summary = rotation_df[['rotation_count', 'crop_diversity', 'corn_years', 'soybean_years']].agg(['mean', 'std', 'min', 'max']).T
rot_summary['median'] = rotation_df[['rotation_count', 'crop_diversity', 'corn_years', 'soybean_years']].median()
print(rot_summary.round(2))

print("\n" + "=" * 70)
print(f"ANALYSIS COMPLETE")
print(f"All plots saved to: {OUTPUT_DIR}")
print("=" * 70)
