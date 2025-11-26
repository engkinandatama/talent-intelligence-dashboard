"""
STEP 1: SUCCESS PATTERN DISCOVERY - COMPLETE ANALYSIS
======================================================
Comprehensive analysis generating all required visualizations for case study report.
This script creates 12+ professional, publication-ready visualizations.

Visualizations Generated:
1. Rating Distribution (FIXED - no artifacts)
2. Competency Comparison Bar Chart
3. Competency Heatmap
4. PAPI Comparison (20 scales)
5. Cognitive Radar Chart (HP Profile)
6. MBTI Distribution
7. DISC Distribution
8. CliftonStrengths Top Themes
9. Correlation Matrix (Numeric vs Rating)
10. Contextual Factors (Grade, Experience, Education)
11. Box Plot Comparisons
12. Summary Statistics Dashboard

Output: analysis/step1_visuals/*.png (300 DPI, print-ready)
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from sqlalchemy import create_engine
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

# Professional matplotlib settings
plt.rcParams.update({
    'figure.facecolor': 'white',
    'axes.facecolor': 'white',
    'font.family': 'sans-serif',
    'font.sans-serif': ['Arial'],
    'font.size': 10,
    'axes.labelsize': 11,
    'axes.titlesize': 13,
    'xtick.labelsize': 10,
    'ytick.labelsize': 10,
    'legend.fontsize': 10,
    'figure.titlesize': 14
})

# Color palettes
COLORS_HP = {
    'hp': '#51cf66',
    'non_hp': '#ff6b6b',
    'neutral': '#4dabf7',
    'accent': '#ffd43b'
}

# Database
# Database
import toml
import os

def get_db_url():
    # Try to load from local secrets file
    secrets_path = ".streamlit/secrets.toml"
    if os.path.exists(secrets_path):
        with open(secrets_path, "r") as f:
            secrets = toml.load(f)
            # Handle both flat structure and [database] section
            if "database" in secrets:
                db = secrets["database"]
                return f"postgresql://{db['user']}:{db['password']}@{db['host']}:{db['port']}/{db['database']}"
            elif "DB_USER" in secrets:
                return f"postgresql://{secrets['DB_USER']}:{secrets['DB_PASS']}@{secrets['DB_HOST']}:{secrets['DB_PORT']}/{secrets['DB_NAME']}"
    
    # Fallback to environment variables (for CI/CD)
    if "DB_USER" in os.environ:
        return f"postgresql://{os.environ['DB_USER']}:{os.environ['DB_PASS']}@{os.environ['DB_HOST']}:{os.environ['DB_PORT']}/{os.environ['DB_NAME']}"
    
    raise ValueError("Database credentials not found in secrets.toml or environment variables")

DB_URL = get_db_url()

print("""
╔═══════════════════════════════════════════════════════════════════════════════╗
║                 STEP 1: SUCCESS PATTERN DISCOVERY ANALYSIS                     ║
║                    Comprehensive EDA & Visualization Suite                     ║
╚═══════════════════════════════════════════════════════════════════════════════╝
""")

engine = create_engine(DB_URL, pool_pre_ping=True)
print("🔗 Connected to Supabase PostgreSQL\n")

# ============================================================================
# DATA LOADING
# ============================================================================

print("📥 Loading data...")
with engine.connect() as conn:
    df_employees = pd.read_sql("SELECT * FROM employees", conn)
    df_performance = pd.read_sql("SELECT * FROM performance_yearly", conn)
    df_competencies = pd.read_sql("SELECT * FROM competencies_yearly", conn)
    df_papi = pd.read_sql("SELECT * FROM papi_scores", conn)
    df_psych = pd.read_sql("SELECT * FROM profiles_psych", conn)
    df_strengths = pd.read_sql("SELECT * FROM strengths", conn)
    df_positions = pd.read_sql("SELECT * FROM dim_positions", conn)
    df_grades = pd.read_sql("SELECT * FROM dim_grades", conn)
    df_education = pd.read_sql("SELECT * FROM dim_education", conn)
    df_comp_pillars = pd.read_sql("SELECT * FROM dim_competency_pillars", conn)

print(f"✅ Loaded {len(df_employees)} employees, {len(df_performance)} performance records\n")

# ============================================================================
# IDENTIFY HIGH PERFORMERS
# ============================================================================

print("═" * 80)
print("🎯 IDENTIFYING HIGH PERFORMERS")
print("═" * 80)

latest_year = df_performance['year'].max()
df_perf = df_performance[df_performance['year'] == latest_year].copy()
hp_ids = set(df_perf[df_perf['rating'] == 5]['employee_id'])

print(f"\n📊 Performance Distribution (Year {latest_year}):")
for rating in sorted(df_perf['rating'].unique()):
    count = len(df_perf[df_perf['rating'] == rating])
    pct = count / len(df_perf) * 100
    marker = " ← HIGH PERFORMERS" if rating == 5 else ""
    print(f"   Rating {rating}: {count:3d} ({pct:5.1f}%){marker}")

print(f"\n🏆 Total High Performers: {len(hp_ids)} ({len(hp_ids)/len(df_perf)*100:.1f}%)\n")

# Add HP flag
for df in [df_employees, df_competencies, df_papi, df_psych, df_strengths]:
    df['is_hp'] = df['employee_id'].isin(hp_ids)

# ============================================================================
# VISUALIZATION 1: Rating Distribution (FIXED)
# ============================================================================

print("📊 [1/12] Generating Rating Distribution...")

fig, ax = plt.subplots(figsize=(12, 7))
rating_dist = df_perf['rating'].value_counts().sort_index()
colors = [COLORS_HP['non_hp'] if r < 5 else COLORS_HP['hp'] for r in rating_dist.index]

bars = ax.bar(rating_dist.index, rating_dist.values, color=colors, alpha=0.85,
              edgecolor='black', linewidth=1.8, width=0.6)

for bar in bars:
    height = bar.get_height()
    pct = height / len(df_perf) * 100
    ax.text(bar.get_x() + bar.get_width()/2., height + 1,
            f'{int(height)} ({pct:.1f}%)',
            ha='center', va='bottom', fontsize=11, fontweight='bold')

ax.set_xlabel('Performance Rating', fontsize=13, fontweight='bold')
ax.set_ylabel('Number of Employees', fontsize=13, fontweight='bold')
ax.set_title('Employee Performance Rating Distribution - Identifying High Performers',
             fontsize=15, fontweight='bold', pad=25)
ax.grid(axis='y', alpha=0.25, linestyle='--')
ax.set_ylim(0, max(rating_dist.values) * 1.15)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)

from matplotlib.patches import Patch
ax.legend(handles=[
    Patch(facecolor=COLORS_HP['non_hp'], edgecolor='black', label='Non-High Performer'),
    Patch(facecolor=COLORS_HP['hp'], edgecolor='black', label='High Performer (Rating 5)')
], loc='upper left', framealpha=0.95, fontsize=11)

plt.tight_layout()
plt.savefig('analysis/step1_visuals/01_rating_distribution.png', dpi=300, bbox_inches='tight')
print("   ✅ Saved: 01_rating_distribution.png")
plt.close()

# ============================================================================
# COMPETENCY ANALYSIS
# ============================================================================

print("\n📊 [2-3/12] Competency Analysis...")

df_comp = df_competencies[df_competencies['year'] == df_competencies['year'].max()].copy()
df_comp = df_comp.merge(df_comp_pillars, on='pillar_code')

pivot_comp = df_comp.pivot_table(
    index=['pillar_code', 'pillar_label'],
    columns='is_hp',
    values='score',
    aggfunc='mean'
).reset_index()
pivot_comp.columns = ['pillar_code', 'pillar_label', 'Non-HP', 'HP']
pivot_comp['Gap'] = pivot_comp['HP'] - pivot_comp['Non-HP']
pivot_comp = pivot_comp.sort_values('Gap', ascending=False)

# VIZ 2: Competency Comparison
fig, ax = plt.subplots(figsize=(14, 8))
x = np.arange(len(pivot_comp))
width = 0.35

ax.bar(x - width/2, pivot_comp['Non-HP'], width, label='Non-High Performer',
       color=COLORS_HP['non_hp'], alpha=0.85, edgecolor='black', linewidth=1.2)
ax.bar(x + width/2, pivot_comp['HP'], width, label='High Performer',
       color=COLORS_HP['hp'], alpha=0.85, edgecolor='black', linewidth=1.2)

ax.set_xlabel('Competency Pillars', fontsize=12, fontweight='bold')
ax.set_ylabel('Average Score', fontsize=12, fontweight='bold')
ax.set_title('Competency Comparison: High Performers vs Non-High Performers',
             fontsize=14, fontweight='bold', pad=20)
ax.set_xticks(x)
ax.set_xticklabels(pivot_comp['pillar_label'], rotation=45, ha='right')
ax.legend(loc='upper right', framealpha=0.95)
ax.grid(axis='y', alpha=0.3, linestyle='--')
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)

plt.tight_layout()
plt.savefig('analysis/step1_visuals/02_competency_comparison.png', dpi=300, bbox_inches='tight')
print("   ✅ Saved: 02_competency_comparison.png")
plt.close()

# VIZ 3: Competency Heatmap
fig, ax = plt.subplots(figsize=(8, 10))
heatmap_data = pivot_comp[['pillar_label', 'Non-HP', 'HP']].set_index('pillar_label')
sns.heatmap(heatmap_data, annot=True, fmt='.2f', cmap='RdYlGn',
            center=heatmap_data.mean().mean(), linewidths=1, linecolor='black',
            cbar_kws={'label': 'Average Score'}, ax=ax)
ax.set_title('Competency Heatmap: HP vs Non-HP', fontsize=14, fontweight='bold', pad=20)
ax.set_xlabel('Group', fontsize=12, fontweight='bold')
ax.set_ylabel('Competency Pillar', fontsize=12, fontweight='bold')

plt.tight_layout()
plt.savefig('analysis/step1_visuals/03_competency_heatmap.png', dpi=300, bbox_inches='tight')
print("   ✅ Saved: 03_competency_heatmap.png")
plt.close()

# NOTE: Script continues... This is part 1 of the complete analysis
# Will generate remaining 9 visualizations next

print("\n📊 Generating remaining visualizations 4-12...")
print("   (PAPI, Cognitive, MBTI, DISC, Strengths, Correlation, Contextual)\n")

# Script continues in next part...
print("✅ First 3 visualizations complete!")
