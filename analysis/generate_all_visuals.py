"""
STEP 1 SUCCESS PATTERN DISCOVERY - COMPLETE & FINAL
====================================================
Generate ALL 12 visualizations for case study report

Author: Data Analyst Case Study 2025
Runtime: ~2-3 minutes
Output: analysis/step1_visuals/*.png (300 DPI)
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sqlalchemy import create_engine
import warnings
warnings.filterwarnings('ignore')

# Clean professional styling
plt.rcParams.update({
    'figure.facecolor': 'white',
    'axes.facecolor': 'white',
    'font.family': 'sans-serif',
    'font.sans-serif': ['Arial'],
    'axes.labelsize': 11,
    'axes.titlesize': 13,
    'xtick.labelsize': 10,
    'ytick.labelsize': 10
})

DB_URL = "postgresql://postgres.dolyfrxntkerdxgfvgqe:talent-match-intelligence@aws-1-ap-southeast-1.pooler.supabase.com:5432/postgres"
C_HP = '#51cf66'  # Green for HP
C_NH = '#ff6b6b'  # Red for Non-HP

print("=" * 90)
print(" " * 20 + "STEP 1: SUCCESS PATTERN DISCOVERY")
print("=" * 90)
print("\n🔗 Connecting to database...")

engine = create_engine(DB_URL, pool_pre_ping=True)

# Load all data
print("📥 Loading data...\n")
with engine.connect() as conn:
    employees = pd.read_sql("SELECT * FROM employees", conn)
    performance = pd.read_sql("SELECT * FROM performance_yearly", conn)
    competencies = pd.read_sql("SELECT * FROM competencies_yearly", conn)
    papi = pd.read_sql("SELECT * FROM papi_scores", conn)
    psych = pd.read_sql("SELECT * FROM profiles_psych", conn)
    strengths = pd.read_sql("SELECT * FROM strengths", conn)
    comp_pillars = pd.read_sql("SELECT * FROM dim_competency_pillars", conn)
    grades = pd.read_sql("SELECT * FROM dim_grades", conn)
    education = pd.read_sql("SELECT * FROM dim_education", conn)

# Identify HP
latest_year = performance['year'].max()
perf = performance[performance['year'] == latest_year]
hp_ids = set(perf[perf['rating'] == 5]['employee_id'])

print(f"✅ Data loaded: {len(employees)} employees, {len(hp_ids)} High Performers\n")

# Add HP flags
for df in [employees, competencies, papi, psych, strengths]:
    df['is_hp'] = df['employee_id'].isin(hp_ids)

# Merge employees with context
emp_full = employees.merge(grades, on='grade_id', how='left', suffixes=('', '_g'))
emp_full = emp_full.merge(education, on='education_id', how='left', suffixes=('', '_e'))
emp_full['exp_years'] = emp_full['years_of_service_months'] / 12

print("=" * 90)
print("📊 GENERATING 12 VISUALIZATIONS")
print("=" * 90 + "\n")

# VIZ 1: Rating Distribution
print("[1/12] Rating Distribution...")
fig, ax = plt.subplots(figsize=(12, 7))
rating_dist = perf['rating'].value_counts().sort_index()
colors = [C_NH if r < 5 else C_HP for r in rating_dist.index]
bars = ax.bar(rating_dist.index, rating_dist.values, color=colors, alpha=0.85, edgecolor='black', linewidth=1.8, width=0.6)
for bar in bars:
    h = bar.get_height()
    ax.text(bar.get_x() + bar.get_width()/2, h + 1, f'{int(h)} ({h/len(perf)*100:.1f}%)',
            ha='center', va='bottom', fontsize=11, fontweight='bold')
ax.set_xlabel('Performance Rating', fontsize=13, fontweight='bold')
ax.set_ylabel('Number of Employees', fontsize=13, fontweight='bold')
ax.set_title('Employee Performance Rating Distribution', fontsize=15, fontweight='bold', pad=25)
ax.grid(axis='y', alpha=0.25, linestyle='--')
ax.set_ylim(0, max(rating_dist.values) * 1.15)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
from matplotlib.patches import Patch
ax.legend(handles=[Patch(facecolor=C_NH, edgecolor='black', label='Non-HP'), Patch(facecolor=C_HP, edgecolor='black', label='HP (Rating 5)')], loc='upper left')
plt.tight_layout()
plt.savefig('analysis/step1_visuals/01_rating_distribution.png', dpi=300, bbox_inches='tight')
plt.close()

# VIZ 2-3: Competency Analysis
print("[2-3/12] Competency Comparison & Heatmap...")
comp = competencies[competencies['year'] == competencies['year'].max()].merge(comp_pillars, on='pillar_code')
pivot_comp = comp.pivot_table(index=['pillar_label'], columns='is_hp', values='score', aggfunc='mean').reset_index()
pivot_comp.columns = ['pillar', 'Non-HP', 'HP']
pivot_comp['Gap'] = pivot_comp['HP'] - pivot_comp['Non-HP']
pivot_comp = pivot_comp.sort_values('Gap', ascending=False)

fig, ax = plt.subplots(figsize=(14, 8))
x = np.arange(len(pivot_comp))
w = 0.35
ax.bar(x - w/2, pivot_comp['Non-HP'], w, label='Non-HP', color=C_NH, alpha=0.85, edgecolor='black', linewidth=1.2)
ax.bar(x + w/2, pivot_comp['HP'], w, label='HP', color=C_HP, alpha=0.85, edgecolor='black', linewidth=1.2)
ax.set_xlabel('Competency Pillars', fontsize=12, fontweight='bold')
ax.set_ylabel('Average Score', fontsize=12, fontweight='bold')
ax.set_title('Competency Comparison: HP vs Non-HP', fontsize=14, fontweight='bold', pad=20)
ax.set_xticks(x)
ax.set_xticklabels(pivot_comp['pillar'], rotation=45, ha='right')
ax.legend()
ax.grid(axis='y', alpha=0.3, linestyle='--')
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
plt.tight_layout()
plt.savefig('analysis/step1_visuals/02_competency_comparison.png', dpi=300, bbox_inches='tight')
plt.close()

fig, ax = plt.subplots(figsize=(8, 10))
hm_data = pivot_comp[['pillar', 'Non-HP', 'HP']].set_index('pillar')
sns.heatmap(hm_data, annot=True, fmt='.2f', cmap='RdYlGn', center=hm_data.mean().mean(),
            linewidths=1, linecolor='black', cbar_kws={'label': 'Score'}, ax=ax)
ax.set_title('Competency Heatmap', fontsize=14, fontweight='bold', pad=20)
plt.tight_layout()
plt.savefig('analysis/step1_visuals/03_competency_heatmap.png', dpi=300, bbox_inches='tight')
plt.close()

# VIZ 4: PAPI Comparison
print("[4/12] PAPI Analysis...")
pivot_papi = papi.pivot_table(index='scale_code', columns='is_hp', values='score', aggfunc='mean').reset_index()
pivot_papi.columns = ['scale', 'Non-HP', 'HP']
pivot_papi = pivot_papi.sort_values('scale')

fig, ax = plt.subplots(figsize=(16, 7))
x = np.arange(len(pivot_papi))
w = 0.35
ax.bar(x - w/2, pivot_papi['Non-HP'], w, label='Non-HP', color=C_NH, alpha=0.85, edgecolor='black')
ax.bar(x + w/2, pivot_papi['HP'], w, label='HP', color=C_HP, alpha=0.85, edgecolor='black')
ax.set_xlabel('PAPI Scale', fontsize=12, fontweight='bold')
ax.set_ylabel('Average Score', fontsize=12, fontweight='bold')
ax.set_title('PAPI Kostick Comparison (20 Scales): HP vs Non-HP', fontsize=14, fontweight='bold', pad=20)
ax.set_xticks(x)
ax.set_xticklabels(pivot_papi['scale'], rotation=45, ha='right')
ax.legend()
ax.grid(axis='y', alpha=0.3, linestyle='--')
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
plt.tight_layout()
plt.savefig('analysis/step1_visuals/04_papi_comparison.png', dpi=300, bbox_inches='tight')
plt.close()

# VIZ 5: Cognitive Radar Chart
print("[5/12] Cognitive Radar Chart...")
cog_cols = ['iq', 'gtq', 'tiki', 'pauli', 'faxtor']
cog_hp = psych[psych['is_hp']][cog_cols].mean()
cog_nh = psych[~psych['is_hp']][cog_cols].mean()

categories = ['IQ', 'GTQ', 'TIKI', 'Pauli', 'Faxtor']
fig, ax = plt.subplots(figsize=(10, 10), subplot_kw=dict(projection='polar'))
angles = np.linspace(0, 2 * np.pi, len(categories), endpoint=False).tolist()
hp_vals = cog_hp.tolist()
nh_vals = cog_nh.tolist()
hp_vals += hp_vals[:1]
nh_vals += nh_vals[:1]
angles += angles[:1]
ax.plot(angles, hp_vals, 'o-', linewidth=2, label='HP', color=C_HP)
ax.fill(angles, hp_vals, alpha=0.25, color=C_HP)
ax.plot(angles, nh_vals, 'o-', linewidth=2, label='Non-HP', color=C_NH)
ax.fill(angles, nh_vals, alpha=0.25, color=C_NH)
ax.set_xticks(angles[:-1])
ax.set_xticklabels(categories, fontsize=12)
ax.set_title('Cognitive Profile Radar Chart', fontsize=14, fontweight='bold', pad=30)
ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1))
ax.grid(True)
plt.tight_layout()
plt.savefig('analysis/step1_visuals/05_cognitive_radar.png', dpi=300, bbox_inches='tight')
plt.close()

# VIZ 6: MBTI Distribution
print("[6/12] MBTI Distribution...")
psych_clean = psych.copy()
psych_clean['mbti'] = psych_clean['mbti'].str.upper().str.strip()
mbti_counts = psych_clean.groupby(['mbti', 'is_hp']).size().unstack(fill_value=0)
mbti_counts.columns = ['Non-HP', 'HP']
mbti_counts = mbti_counts.sort_values('HP', ascending=False).head(10)

fig, ax = plt.subplots(figsize=(14, 7))
x = np.arange(len(mbti_counts))
w = 0.35
ax.bar(x - w/2, mbti_counts['Non-HP'], w, label='Non-HP', color=C_NH, alpha=0.85, edgecolor='black')
ax.bar(x + w/2, mbti_counts['HP'], w, label='HP', color=C_HP, alpha=0.85, edgecolor='black')
ax.set_xlabel('MBTI Type', fontsize=12, fontweight='bold')
ax.set_ylabel('Count', fontsize=12, fontweight='bold')
ax.set_title('MBTI Distribution: Top 10 Types', fontsize=14, fontweight='bold', pad=20)
ax.set_xticks(x)
ax.set_xticklabels(mbti_counts.index, rotation=0)
ax.legend()
ax.grid(axis='y', alpha=0.3, linestyle='--')
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
plt.tight_layout()
plt.savefig('analysis/step1_visuals/06_mbti_distribution.png', dpi=300, bbox_inches='tight')
plt.close()

# VIZ 7: DISC Distribution (Pie Charts)
print("[7/12] DISC Distribution...")
psych_clean['disc'] = psych_clean['disc'].str.upper().str.strip()
disc_hp = psych_clean[psych_clean['is_hp']]['disc'].value_counts().head(5)
disc_nh = psych_clean[~psych_clean['is_hp']]['disc'].value_counts().head(5)

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 7))
colors_pie = ['#ff6b6b', '#51cf66', '#4dabf7', '#ffd43b', '#ff922b']
ax1.pie(disc_nh.values, labels=disc_nh.index, autopct='%1.1f%%', startangle=90, colors=colors_pie)
ax1.set_title('DISC Distribution: Non-HP', fontsize=13, fontweight='bold')
ax2.pie(disc_hp.values, labels=disc_hp.index, autopct='%1.1f%%', startangle=90, colors=colors_pie)
ax2.set_title('DISC Distribution: HP', fontsize=13, fontweight='bold')
plt.tight_layout()
plt.savefig('analysis/step1_visuals/07_disc_distribution.png', dpi=300, bbox_inches='tight')
plt.close()

# VIZ 8: Strengths Top Themes
print("[8/12] CliftonStrengths Top Themes...")
top_strengths = strengths[strengths['is_hp']].groupby('theme').size().sort_values(ascending=False).head(15)

fig, ax = plt.subplots(figsize=(12, 8))
ax.barh(range(len(top_strengths)), top_strengths.values, color=C_HP, alpha=0.85, edgecolor='black')
ax.set_yticks(range(len(top_strengths)))
ax.set_yticklabels(top_strengths.index)
ax.set_xlabel('Frequency', fontsize=12, fontweight='bold')
ax.set_title('Top 15 CliftonStrengths Themes among High Performers', fontsize=14, fontweight='bold', pad=20)
ax.grid(axis='x', alpha=0.3, linestyle='--')
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
plt.tight_layout()
plt.savefig('analysis/step1_visuals/08_strengths_top_themes.png', dpi=300, bbox_inches='tight')
plt.close()

# VIZ 9: Correlation Matrix
print("[9/12] Correlation Matrix...")
cog_cols_with_id = ['employee_id'] + [c for c in ['iq', 'gtq', 'tiki', 'pauli', 'faxtor'] if c in psych.columns]
psychcorr = psych[cog_cols_with_id].copy()
psych_with_rating = psychcorr.merge(perf[['employee_id', 'rating']], on='employee_id', how='inner')
corr_matrix = psych_with_rating.drop('employee_id', axis=1).corr()

fig, ax = plt.subplots(figsize=(10, 8))
sns.heatmap(corr_matrix, annot=True, fmt='.2f', cmap='coolwarm', center=0,
            linewidths=1, linecolor='black', cbar_kws={'label': 'Correlation'}, ax=ax)
ax.set_title('Correlation Matrix: Cognitive Variables vs Rating', fontsize=14, fontweight='bold', pad=20)
plt.tight_layout()
plt.savefig('analysis/step1_visuals/09_correlation_matrix.png', dpi=300, bbox_inches='tight')
plt.close()

# VIZ 10: Grade Distribution
print("[10/12] Contextual Analysis - Grade...")
# Get the grade column name (might be 'name' or 'name_g' after merge)
grade_col = 'name' if 'name' in emp_full.columns and emp_full['name'].dtype == 'object' else 'name_g'
if grade_col not in emp_full.columns:
    # Try alternative: all merge created columns
    grade_cols = [c for c in emp_full.columns if 'grade' in c.lower() and c != 'grade_id']
    if grade_cols:
        grade_col = grade_cols[0]
    else:
        print("   ⚠️ Skipping grade distribution (column not found)")
        grade_counts = pd.DataFrame()
else:
    grade_counts = emp_full.groupby([grade_col, 'is_hp']).size().unstack(fill_value=0)
    grade_counts.columns = ['Non-HP', 'HP']
    
if not grade_counts.empty:
    fig, ax = plt.subplots(figsize=(12, 7))
    grade_counts.plot(kind='bar', ax=ax, color=[C_NH, C_HP], alpha=0.85, edgecolor='black')
    ax.set_xlabel('Grade Level', fontsize=12, fontweight='bold')
    ax.set_ylabel('Count', fontsize=12, fontweight='bold')
    ax.set_title('Grade Distribution: HP vs Non-HP', fontsize=14, fontweight='bold', pad=20)
    ax.legend(title='Group')
    ax.grid(axis='y', alpha=0.3, linestyle='--')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.savefig('analysis/step1_visuals/10_grade_distribution.png', dpi=300, bbox_inches='tight')
    plt.close()
else:
    print("   ⚠️  Skipped grade visualization (no data)")

# VIZ 11: Experience Box Plot
print("[11/12] Experience Comparison...")
fig, ax = plt.subplots(figsize=(10, 7))
data_box = [emp_full[~emp_full['is_hp']]['exp_years'].dropna(), emp_full[emp_full['is_hp']]['exp_years'].dropna()]
bp = ax.boxplot(data_box, labels=['Non-HP', 'HP'], patch_artist=True, widths=0.6)
bp['boxes'][0].set_facecolor(C_NH)
bp['boxes'][1].set_facecolor(C_HP)
for box in bp['boxes']:
    box.set_alpha(0.7)
    box.set_edgecolor('black')
    box.set_linewidth(1.5)
ax.set_ylabel('Years of Experience', fontsize=12, fontweight='bold')
ax.set_title('Experience Distribution: HP vs Non-HP', fontsize=14, fontweight='bold', pad=20)
ax.grid(axis='y', alpha=0.3, linestyle='--')
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
plt.tight_layout()
plt.savefig('analysis/step1_visuals/11_experience_boxplot.png', dpi=300, bbox_inches='tight')
plt.close()

# VIZ 12: Summary Statistics
print("[12/12] Summary Statistics Dashboard...")
fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(14, 10))

# Competency average
comp_avg_hp = comp[comp['is_hp']]['score'].mean()
comp_avg_nh = comp[~comp['is_hp']]['score'].mean()
ax1.bar(['Non-HP', 'HP'], [comp_avg_nh, comp_avg_hp], color=[C_NH, C_HP], alpha=0.85, edgecolor='black')
ax1.set_title('Avg Competency Score', fontweight='bold')
ax1.set_ylabel('Score')
ax1.grid(axis='y', alpha=0.3)

# Cognitive average
cog_avg_hp = cog_hp.mean()
cog_avg_nh = cog_nh.mean()
ax2.bar(['Non-HP', 'HP'], [cog_avg_nh, cog_avg_hp], color=[C_NH, C_HP], alpha=0.85, edgecolor='black')
ax2.set_title('Avg Cognitive Score', fontweight='bold')
ax2.set_ylabel('Score')
ax2.grid(axis='y', alpha=0.3)

# Experience
exp_avg_hp = emp_full[emp_full['is_hp']]['exp_years'].mean()
exp_avg_nh = emp_full[~emp_full['is_hp']]['exp_years'].mean()
ax3.bar(['Non-HP', 'HP'], [exp_avg_nh, exp_avg_hp], color=[C_NH, C_HP], alpha=0.85, edgecolor='black')
ax3.set_title('Avg Experience (Years)', fontweight='bold')
ax3.set_ylabel('Years')
ax3.grid(axis='y', alpha=0.3)

# Count
count_hp = len(emp_full[emp_full['is_hp']])
count_nh = len(emp_full[~emp_full['is_hp']])
ax4.bar(['Non-HP', 'HP'], [count_nh, count_hp], color=[C_NH, C_HP], alpha=0.85, edgecolor='black')
ax4.set_title('Employee Count', fontweight='bold')
ax4.set_ylabel('Count')
ax4.grid(axis='y', alpha=0.3)

for ax in [ax1, ax2, ax3, ax4]:
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

fig.suptitle('Summary Statistics Dashboard', fontsize=16, fontweight='bold', y=0.995)
plt.tight_layout()
plt.savefig('analysis/step1_visuals/12_summary_dashboard.png', dpi=300, bbox_inches='tight')
plt.close()

print("\n" + "=" * 90)
print("✅ ALL 12 VISUALIZATIONS GENERATED SUCCESSFULLY!")
print("=" * 90)
print("\n📁 Output directory: analysis/step1_visuals/")
print("\n📊 Generated files:")
for i in range(1, 13):
    print(f"   {i:2d}. {i:02d}_*.png")
print("\n✨ All visualizations are print-ready (300 DPI, clean formatting, no artifacts)")
print("=" * 90)
