
import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text

# Database Connection
DB_URL = "postgresql://postgres.dolyfrxntkerdxgfvgqe:talent-match-intelligence@aws-1-ap-southeast-1.pooler.supabase.com:5432/postgres"
engine = create_engine(DB_URL)

def get_data():
    with engine.connect() as conn:
        print("📥 Loading data...")
        df_employees = pd.read_sql("SELECT * FROM employees", conn)
        df_performance = pd.read_sql("SELECT * FROM performance_yearly", conn)
        df_competencies = pd.read_sql("SELECT * FROM competencies_yearly", conn)
        df_comp_pillars = pd.read_sql("SELECT * FROM dim_competency_pillars", conn)
        df_psych = pd.read_sql("SELECT * FROM profiles_psych", conn)
        df_papi = pd.read_sql("SELECT * FROM papi_scores", conn)
        df_strengths = pd.read_sql("SELECT * FROM strengths", conn)
        
        with open('analysis/report_data.txt', 'w') as f:
            def log(msg):
                print(msg)
                f.write(msg + '\n')
            
            # Identify High Performers (Rating 5 in latest year)
            latest_year = df_performance['year'].max()
            df_perf_latest = df_performance[df_performance['year'] == latest_year]
            hp_ids = df_perf_latest[df_perf_latest['rating'] == 5]['employee_id'].tolist()
            
            log(f"\n--- GENERAL STATS ---")
            total_employees = len(df_perf_latest)
            total_hp = len(hp_ids)
            log(f"Total Employees (Year {latest_year}): {total_employees}")
            log(f"High Performers: {total_hp} ({total_hp/total_employees*100:.1f}%)")
            
            # Competency Gaps
            log(f"\n--- COMPETENCY GAPS ---")
            df_comp_latest = df_competencies[df_competencies['year'] == latest_year].merge(df_comp_pillars, on='pillar_code')
            df_comp_latest['is_hp'] = df_comp_latest['employee_id'].isin(hp_ids)
            
            gap_df = df_comp_latest.pivot_table(index='pillar_label', columns='is_hp', values='score', aggfunc='mean')
            gap_df['Gap'] = gap_df[True] - gap_df[False]
            gap_df = gap_df.sort_values('Gap', ascending=False)
            
            log(gap_df[['Gap']].head(5).to_string())
            
            # Cognitive Correlation
            log(f"\n--- COGNITIVE CORRELATION ---")
            df_cog = df_psych.merge(df_perf_latest[['employee_id', 'rating']], on='employee_id')
            for col in ['iq', 'gtq', 'tiki', 'pauli', 'faxtor']:
                corr = df_cog[col].corr(df_cog['rating'])
                log(f"{col}: {corr:.2f}")
                
            # PAPI Differentiators
            log(f"\n--- PAPI DIFFERENTIATORS ---")
            df_papi['is_hp'] = df_papi['employee_id'].isin(hp_ids)
            papi_gap = df_papi.pivot_table(index='scale_code', columns='is_hp', values='score', aggfunc='mean')
            papi_gap['Gap'] = papi_gap[True] - papi_gap[False]
            # Sort by absolute gap to find biggest differences
            papi_gap['AbsGap'] = papi_gap['Gap'].abs()
            log(papi_gap.sort_values('AbsGap', ascending=False).head(5).to_string())
            
            # MBTI Distribution for HPs
            log(f"\n--- MBTI DISTRIBUTION (HP) ---")
            hp_mbti = df_psych[df_psych['employee_id'].isin(hp_ids)]['mbti'].value_counts(normalize=True) * 100
            log(hp_mbti.head(3).to_string())
            
            # DISC Distribution for HPs
            log(f"\n--- DISC DISTRIBUTION (HP) ---")
            hp_disc = df_psych[df_psych['employee_id'].isin(hp_ids)]['disc'].value_counts(normalize=True) * 100
            log(hp_disc.head(3).to_string())
            
            # Top Strengths for HPs
            log(f"\n--- TOP STRENGTHS (HP) ---")
            log(f"Strengths Table Columns: {df_strengths.columns.tolist()}")
            
            # Try to find the strength name column
            strength_col = 'strength_name' if 'strength_name' in df_strengths.columns else 'theme' if 'theme' in df_strengths.columns else None
            
            if strength_col:
                hp_strengths = df_strengths[df_strengths['employee_id'].isin(hp_ids)]
                top_strengths = hp_strengths[strength_col].value_counts().head(5)
                hp_count = len(hp_ids)
                for name, count in top_strengths.items():
                    log(f"{name}: {count} ({count/hp_count*100:.1f}%)")
            else:
                log("Could not identify strength name column.")
                
            # Experience Stats
            log(f"\n--- EXPERIENCE STATS ---")
            df_emp_perf = df_employees.merge(df_perf_latest[['employee_id', 'rating']], on='employee_id')
            df_emp_perf['years_exp'] = df_emp_perf['years_of_service_months'] / 12.0
            
            median_hp = df_emp_perf[df_emp_perf['rating'] == 5]['years_exp'].median()
            median_non_hp = df_emp_perf[df_emp_perf['rating'] < 5]['years_exp'].median()
            
            log(f"Median Experience HP: {median_hp:.1f} years")
            log(f"Median Experience Non-HP: {median_non_hp:.1f} years")
            
            # Grade Distribution
            log(f"\n--- GRADE DISTRIBUTION (HP) ---")
            df_hp_grades = df_employees[df_employees['employee_id'].isin(hp_ids)].merge(pd.read_sql("SELECT * FROM dim_grades", conn), on='grade_id')
            log((df_hp_grades['name'].value_counts(normalize=True).head(3) * 100).to_string())

if __name__ == "__main__":
    get_data()
