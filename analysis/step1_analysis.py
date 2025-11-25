"""
Step 1 Success Pattern Discovery - Data Analysis & Visualization Script
==========================================================================
This script performs comprehensive EDA to identify success patterns among high performers
and generates professional visualizations for the case study report.

Author: Data Analyst Case Study 2025
Date: November 25, 2025
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from sqlalchemy import create_engine, text
import warnings
warnings.filterwarnings('ignore')

# Set professional styling
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")
pd.set_option('display.max_columns', None)

# Database connection
DB_URL = "postgresql://postgres.dolyfrxntkerdxgfvgqe:talent-match-intelligence@aws-1-ap-southeast-1.pooler.supabase.com:5432/postgres"
engine = create_engine(DB_URL, pool_pre_ping=True)

print("=" * 80)
print("STEP 1: SUCCESS PATTERN DISCOVERY ANALYSIS")
print("=" * 80)
print("\n📊 Loading data from Supabase...")

# ============================================================================
# DATA EXTRACTION
# ============================================================================

with engine.connect() as conn:
    # Core tables
    df_employees = pd.read_sql("SELECT * FROM employees", conn)
    df_performance = pd.read_sql("SELECT * FROM performance_yearly", conn)
    df_competencies = pd.read_sql("SELECT * FROM competencies_yearly", conn)
    df_papi = pd.read_sql("SELECT * FROM papi_scores", conn)
    df_psych = pd.read_sql("SELECT * FROM profiles_psych", conn)
    df_strengths = pd.read_sql("SELECT * FROM strengths", conn)
    
    # Dimensions
    df_positions = pd.read_sql("SELECT * FROM dim_positions", conn)
    df_departments = pd.read_sql("SELECT * FROM dim_departments", conn)
    df_grades = pd.read_sql("SELECT * FROM dim_grades", conn)
    df_education = pd.read_sql("SELECT * FROM dim_education", conn)
    df_comp_pillars = pd.read_sql("SELECT * FROM dim_competency_pillars", conn)

print(f"✅ Data loaded successfully!")
print(f"   - Employees: {len(df_employees)}")
print(f"   - Performance records: {len(df_performance)}")
print(f"   - Competency records: {len(df_competencies)}")
print(f"   - PAPI records: {len(df_papi)}")
print(f"   - Psychometric profiles: {len(df_psych)}")
print(f"   - Strengths records: {len(df_strengths)}")

# ============================================================================
# IDENTIFY HIGH PERFORMERS
# ============================================================================

print("\n" + "=" * 80)
print("🎯 IDENTIFYING HIGH PERFORMERS (Rating = 5)")
print("=" * 80)

# Get latest year performance
latest_year = df_performance['year'].max()
df_perf_latest = df_performance[df_performance['year'] == latest_year].copy()

# Identify High Performers
df_hp = df_perf_latest[df_perf_latest['rating'] == 5].copy()
hp_ids = df_hp['employee_id'].unique()

print(f"\n📈 Performance Distribution:")
rating_dist = df_perf_latest['rating'].value_counts().sort_index()
for rating, count in rating_dist.items():
    percentage = (count / len(df_perf_latest)) * 100
    bar = "█" * int(percentage / 2)
    print(f"   Rating {rating}: {count:4d} ({percentage:5.1f}%) {bar}")

print(f"\n🏆 High Performers (Rating 5): {len(hp_ids)} employees ({len(hp_ids)/len(df_perf_latest)*100:.1f}%)")

# Add HP flag to all dataframes
df_employees['is_hp'] = df_employees['employee_id'].isin(hp_ids)
df_competencies['is_hp'] = df_competencies['employee_id'].isin(hp_ids)
df_papi['is_hp'] = df_papi['employee_id'].isin(hp_ids)
df_psych['is_hp'] = df_psych['employee_id'].isin(hp_ids)
df_strengths['is_hp'] = df_strengths['employee_id'].isin(hp_ids)

# ============================================================================
# VISUALIZATION 1: RATING DISTRIBUTION
# ============================================================================

print("\n📊 Generating Visualization 1: Rating Distribution...")

fig, ax = plt.subplots(figsize=(10, 6))
colors = ['#ff6b6b' if r < 5 else '#51cf66' for r in rating_dist.index]
bars = ax.bar(rating_dist.index, rating_dist.values, color=colors, alpha=0.8, edgecolor='black', linewidth=1.5)

# Add value labels on bars
for bar in bars:
    height = bar.get_height()
    ax.text(bar.get_x() + bar.get_width()/2., height,
            f'{int(height)}\\n({height/len(df_perf_latest)*100:.1f}%)',
            ha='center', va='bottom', fontsize=10, fontweight='bold')

ax.set_xlabel('Performance Rating', fontsize=12, fontweight='bold')
ax.set_ylabel('Number of Employees', fontsize=12, fontweight='bold')
ax.set_title('Employee Performance Rating Distribution\\n(Identifying High Performers)', 
             fontsize=14, fontweight='bold', pad=20)
ax.grid(axis='y', alpha=0.3, linestyle='--')
ax.set_xticks(rating_dist.index)

# Add legend
from matplotlib.patches import Patch
legend_elements = [Patch(facecolor='#ff6b6b', label='Non-High Performer'),
                   Patch(facecolor='#51cf66', label='High Performer (Rating 5)')]
ax.legend(handles=legend_elements, loc='upper left', framealpha=0.9)

plt.tight_layout()
plt.savefig('analysis/step1_visuals/01_rating_distribution.png', dpi=300, bbox_inches='tight')
print("   ✅ Saved: 01_rating_distribution.png")
plt.close()

# ============================================================================
# COMPETENCY ANALYSIS
# ============================================================================

print("\n" + "=" * 80)
print("💼 COMPETENCY ANALYSIS (10 Pillars)")
print("=" * 80)

# Get latest competency data
latest_comp_year = df_competencies['year'].max()
df_comp_latest = df_competencies[df_competencies['year'] == latest_comp_year].copy()

# Merge with pillar labels
df_comp_latest = df_comp_latest.merge(df_comp_pillars, on='pillar_code', how='left')

# Pivot: HP vs Non-HP
pivot_comp = df_comp_latest.pivot_table(
    index=['pillar_code', 'pillar_label'],
    columns='is_hp',
    values='score',
    aggfunc='mean'
).reset_index()

pivot_comp.columns = ['pillar_code', 'pillar_label', 'Non-HP', 'HP']
pivot_comp['Difference'] = pivot_comp['HP'] - pivot_comp['Non-HP']
pivot_comp['Pct_Improvement'] = (pivot_comp['Difference'] / pivot_comp['Non-HP']) * 100
pivot_comp = pivot_comp.sort_values('Difference', ascending=False)

print("\\n📊 Competency Comparison (HP vs Non-HP):")
print("-" * 80)
print(f"{'Pillar':<30} {'Non-HP':>8} {'HP':>8} {'Diff':>8} {'% Imp':>8}")
print("-" * 80)
for _, row in pivot_comp.iterrows():
    print(f"{row['pillar_label']:<30} {row['Non-HP']:>8.2f} {row['HP']:>8.2f} "
          f"{row['Difference']:>8.2f} {row['Pct_Improvement']:>7.1f}%")

# VISUALIZATION 2: Competency Comparison Bar Chart
print("\\n📊 Generating Visualization 2: Competency Comparison...")

fig, ax = plt.subplots(figsize=(14, 8))
x = np.arange(len(pivot_comp))
width = 0.35

bars1 = ax.bar(x - width/2, pivot_comp['Non-HP'], width, label='Non-High Performer',
               color='#ff9999', alpha=0.8, edgecolor='black', linewidth=1)
bars2 = ax.bar(x + width/2, pivot_comp['HP'], width, label='High Performer',
               color='#66b3ff', alpha=0.8, edgecolor='black', linewidth=1)

ax.set_xlabel('Competency Pillars', fontsize=12, fontweight='bold')
ax.set_ylabel('Average Score', fontsize=12, fontweight='bold')
ax.set_title('Competency Comparison: High Performers vs Non-High Performers\\n(10 Core Pillars)',
             fontsize=14, fontweight='bold', pad=20)
ax.set_xticks(x)
ax.set_xticklabels(pivot_comp['pillar_label'], rotation=45, ha='right')
ax.legend(loc='upper left', framealpha=0.9, fontsize=10)
ax.grid(axis='y', alpha=0.3, linestyle='--')
ax.set_ylim(0, max(pivot_comp['HP'].max(), pivot_comp['Non-HP'].max()) * 1.1)

plt.tight_layout()
plt.savefig('analysis/step1_visuals/02_competency_comparison.png', dpi=300, bbox_inches='tight')
print("   ✅ Saved: 02_competency_comparison.png")
plt.close()

# VISUALIZATION 3: Competency Heatmap
print("\\n📊 Generating Visualization 3: Competency Heatmap...")

# Create pivot for heatmap
heatmap_data = df_comp_latest.pivot_table(
    index='pillar_label',
    columns='is_hp',
    values='score',
    aggfunc='mean'
)
heatmap_data.columns = ['Non-HP', 'HP']

fig, ax = plt.subplots(figsize=(8, 10))
sns.heatmap(heatmap_data, annot=True, fmt='.2f', cmap='RdYlGn', center=heatmap_data.mean().mean(),
            linewidths=1, linecolor='black', cbar_kws={'label': 'Average Score'},
            ax=ax, vmin=heatmap_data.min().min(), vmax=heatmap_data.max().max())
ax.set_title('Competency Heatmap: HP vs Non-HP\\n(Color: Red=Low, Green=High)',
             fontsize=14, fontweight='bold', pad=20)
ax.set_xlabel('Group', fontsize=12, fontweight='bold')
ax.set_ylabel('Competency Pillar', fontsize=12, fontweight='bold')

plt.tight_layout()
plt.savefig('analysis/step1_visuals/03_competency_heatmap.png', dpi=300, bbox_inches='tight')
print("   ✅ Saved: 03_competency_heatmap.png")
plt.close()

print("\\n✅ Script execution completed! Check 'analysis/step1_visuals/' for outputs.")
print("=" * 80)
