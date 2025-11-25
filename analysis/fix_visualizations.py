"""
STEP 1 - FIXED VISUALIZATIONS (Clean & Professional)
=====================================================
Fixed version without artifacts for PDF report
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sqlalchemy import create_engine
import warnings
warnings.filterwarnings('ignore')

# Professional styling - cleaner
plt.rcParams['figure.facecolor'] = 'white'
plt.rcParams['axes.facecolor'] = 'white'
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['Arial', 'DejaVu Sans']
sns.set_palette("husl")

# Database connection
DB_URL = "postgresql://postgres.dolyfrxntkerdxgfvgqe:talent-match-intelligence@aws-1-ap-southeast-1.pooler.supabase.com:5432/postgres"
engine = create_engine(DB_URL, pool_pre_ping=True)

print("Fixing visualizations - removing artifacts...")

# Load data
with engine.connect() as conn:
    df_performance = pd.read_sql("SELECT * FROM performance_yearly", conn)

# Get latest performance
latest_year = df_performance['year'].max()
df_perf_latest = df_performance[df_performance['year'] == latest_year].copy()

# Rating distribution
rating_dist = df_perf_latest['rating'].value_counts().sort_index()

# ============================================================================
# VISUALIZATION 1 (FIXED): Rating Distribution - Clean Version
# ============================================================================

fig, ax = plt.subplots(figsize=(12, 7))

# Colors
colors = ['#ff6b6b' if r < 5 else '#51cf66' for r in rating_dist.index]

# Create bars
bars = ax.bar(rating_dist.index, rating_dist.values, color=colors, alpha=0.85, 
              edgecolor='black', linewidth=1.8, width=0.6)

# Add value labels on bars
for bar in bars:
    height = bar.get_height()
    percentage = (height / len(df_perf_latest)) * 100
    # FIX: Use proper string formatting, no \n in f-string
    label_text = f'{int(height)} ({percentage:.1f}%)'
    ax.text(bar.get_x() + bar.get_width()/2., height + 1,
            label_text,
            ha='center', va='bottom', fontsize=11, fontweight='bold')

ax.set_xlabel('Performance Rating', fontsize=13, fontweight='bold')
ax.set_ylabel('Number of Employees', fontsize=13, fontweight='bold')

# FIX: Single line title, no newline character
ax.set_title('Employee Performance Rating Distribution - Identifying High Performers', 
             fontsize=15, fontweight='bold', pad=25)

ax.grid(axis='y', alpha=0.25, linestyle='--', linewidth=0.8)
ax.set_xticks(rating_dist.index)
ax.set_ylim(0, max(rating_dist.values) * 1.15)

# Spines styling
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['left'].set_linewidth(1.5)
ax.spines['bottom'].set_linewidth(1.5)

# Legend
from matplotlib.patches import Patch
legend_elements = [
    Patch(facecolor='#ff6b6b', edgecolor='black', label='Non-High Performer (Rating 1-4)'),
    Patch(facecolor='#51cf66', edgecolor='black', label='High Performer (Rating 5)')
]
ax.legend(handles=legend_elements, loc='upper left', framealpha=0.95, 
          fontsize=11, edgecolor='black', fancybox=False)

plt.tight_layout()
plt.savefig('analysis/step1_visuals/01_rating_distribution.png', 
            dpi=300, bbox_inches='tight', facecolor='white', edgecolor='none')
print("✅ Fixed: 01_rating_distribution.png")
plt.close()

print("\n✅ Visualization fixed successfully! No more artifacts.")
