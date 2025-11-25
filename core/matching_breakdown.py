
# ===================================================================================
# FUNGSI BARU: get_detailed_match_breakdown
# ===================================================================================
# Tujuan: Mendapatkan breakdown detail TV-level dan TGV-level untuk satu employee
#         Digunakan untuk visualisasi gap analysis di dashboard
# ===================================================================================
def get_detailed_match_breakdown(engine, employee_id, benchmark_ids=None):
    """
    Dapatkan detailed breakdown match rate untuk satu employee terhadap benchmark.
    
    Args:
        engine: SQLAlchemy engine
        employee_id (str): ID karyawan yang akan dianalisis
        benchmark_ids (list): List employee IDs untuk benchmark. 
                              Jika None, gunakan semua HP (rating=5)
    
    Returns:
        dict dengan keys:
            - 'tv_details': DataFrame [tgv_name, tv_name, tv_label, baseline_score, user_score, tv_match_rate, tv_weight]
            - 'tgv_summary': DataFrame [tgv_name, tgv_match_rate, tgv_weight]
            - 'final_score': float - final match rate (0-100)
            - 'employee_info': dict - basic employee information
    """
    
    import pandas as pd
    from sqlalchemy import text
    
    # Input validation
    if not employee_id or not isinstance(employee_id, str) or employee_id.strip() == '':
        raise ValueError("employee_id must be a non-empty string")
    
    # Prepare benchmark IDs
    if benchmark_ids and len(benchmark_ids) > 0:
        benchmark_array_sql = "ARRAY[" + ",".join(f"'{eid.strip()}'" for eid in benchmark_ids) + "]::text[]"
        use_custom_benchmark = "true"
    else:
        benchmark_array_sql = "ARRAY[]::text[]"
        use_custom_benchmark = "false"
    
    # SQL Query for detailed breakdown
    breakdown_sql = f"""
    WITH
    -- Benchmark selection
    benchmark_employees AS (
        SELECT unnest({benchmark_array_sql}) AS employee_id
        WHERE {use_custom_benchmark}
        
        UNION ALL
        
        SELECT py.employee_id
        FROM performance_yearly py
        WHERE py.rating = 5
          AND NOT {use_custom_benchmark}
    ),
    
    -- Baseline calculations (simplified from main template)
    baseline_numeric AS (
        SELECT
            cy.pillar_code AS tv_name,
            'COMPETENCY' AS tgv_name,
            cp.pillar_label AS tv_label,
            PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY cy.score) AS baseline_score,
            1.0 AS tv_weight
        FROM competencies_yearly cy
        JOIN benchmark_employees be ON cy.employee_id = be.employee_id
        JOIN dim_competency_pillars cp ON cy.pillar_code = cp.pillar_code
        WHERE cy.year = (SELECT MAX(year) FROM competencies_yearly)
        GROUP BY cy.pillar_code, cp.pillar_label
    ),
    
    baseline_cognitive AS (
        SELECT tv_name, 'COGNITIVE' AS tgv_name, tv_label, baseline_score, tv_weight
        FROM (
            SELECT 'IQ' AS tv_name, 'IQ Score' AS tv_label,
                   PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY pp.iq) AS baseline_score,
                   0.25 AS tv_weight
            FROM profiles_psych pp
            JOIN benchmark_employees be ON pp.employee_id = be.employee_id
            WHERE pp.iq IS NOT NULL
            
            UNION ALL
            
            SELECT 'GTQ', 'GTQ Score',
                   PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY pp.gtq),
                   0.25
            FROM profiles_psych pp
            JOIN benchmark_employees be ON pp.employee_id = be.employee_id
            WHERE pp.gtq IS NOT NULL
            
            UNION ALL
            
            SELECT 'TIKI', 'TIKI Score',
                   PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY pp.tiki),
                   0.20
            FROM profiles_psych pp
            JOIN benchmark_employees be ON pp.employee_id = be.employee_id
            WHERE pp.tiki IS NOT NULL
            
            UNION ALL
            
            SELECT 'Pauli', 'Pauli Score',
                   PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY pp.pauli),
                   0.15
            FROM profiles_psych pp
            JOIN benchmark_employees be ON pp.employee_id = be.employee_id
            WHERE pp.pauli IS NOT NULL
            
            UNION ALL
            
            SELECT 'Faxtor', 'Faxtor Score',
                   PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY pp.faxtor),
                   0.15
            FROM profiles_psych pp
            JOIN benchmark_employees be ON pp.employee_id = be.employee_id
            WHERE pp.faxtor IS NOT NULL
        ) cog
    ),
    
    baseline_papi AS (
        SELECT
            ps.scale_code AS tv_name,
            'WORK_STYLE' AS tgv_name,
            ps.scale_code AS tv_label,
            PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY ps.score) AS baseline_score,
            CASE 
                WHEN ps.scale_code IN ('N', 'L', 'F') THEN 0.25
                WHEN ps.scale_code IN ('I', 'K', 'Z', 'T') THEN 0.10
                ELSE 0.05
            END AS tv_weight
        FROM papi_scores ps
        JOIN benchmark_employees be ON ps.employee_id = be.employee_id
        GROUP BY ps.scale_code
    ),
    
    -- User (candidate) scores
    user_competencies AS (
        SELECT
            cy.pillar_code AS tv_name,
            cy.score AS user_score
        FROM competencies_yearly cy
        WHERE cy.employee_id = '{employee_id}'
          AND cy.year = (SELECT MAX(year) FROM competencies_yearly)
    ),
    
    user_cognitive AS (
        SELECT tv_name, user_score
        FROM (
            SELECT 'IQ' AS tv_name, pp.iq AS user_score
            FROM profiles_psych pp WHERE pp.employee_id = '{employee_id}'
            UNION ALL
            SELECT 'GTQ', pp.gtq FROM profiles_psych pp WHERE pp.employee_id = '{employee_id}'
            UNION ALL
            SELECT 'TIKI', pp.tiki FROM profiles_psych pp WHERE pp.employee_id = '{employee_id}'
            UNION ALL
            SELECT 'Pauli', pp.pauli FROM profiles_psych pp WHERE pp.employee_id = '{employee_id}'
            UNION ALL
            SELECT 'Faxtor', pp.faxtor FROM profiles_psych pp WHERE pp.employee_id = '{employee_id}'
        ) cog
        WHERE user_score IS NOT NULL
    ),
    
    user_papi AS (
        SELECT
            ps.scale_code AS tv_name,
            ps.score AS user_score
        FROM papi_scores ps
        WHERE ps.employee_id = '{employee_id}'
    ),
    
    -- TV match calculations
    tv_matches AS (
        -- Competencies
        SELECT
            bn.tgv_name,
            bn.tv_name,
            bn.tv_label,
            bn.baseline_score,
            COALESCE(uc.user_score, 0) AS user_score,
            CASE
                WHEN bn.baseline_score > 0 THEN
                    LEAST((COALESCE(uc.user_score, 0) / bn.baseline_score) * 100, 100)
                ELSE 50
            END AS tv_match_rate,
            bn.tv_weight
        FROM baseline_numeric bn
        LEFT JOIN user_competencies uc ON bn.tv_name = uc.tv_name
        
        UNION ALL
        
        -- Cognitive
        SELECT
            bc.tgv_name,
            bc.tv_name,
            bc.tv_label,
            bc.baseline_score,
            COALESCE(ucog.user_score, 0) AS user_score,
            CASE
                WHEN bc.baseline_score > 0 THEN
                    LEAST((COALESCE(ucog.user_score, 0) / bc.baseline_score) * 100, 100)
                ELSE 50
            END AS tv_match_rate,
            bc.tv_weight
        FROM baseline_cognitive bc
        LEFT JOIN user_cognitive ucog ON bc.tv_name = ucog.tv_name
        
        UNION ALL
        
        -- PAPI (with reverse scoring for I, K, Z, T)
        SELECT
            bp.tgv_name,
            bp.tv_name,
            bp.tv_label,
            bp.baseline_score,
            COALESCE(up.user_score, 0) AS user_score,
            CASE
                WHEN bp.tv_name IN ('I', 'K', 'Z', 'T') THEN
                    -- Reverse scoring: lower is better
                    CASE
                        WHEN bp.baseline_score > 0 THEN
                            LEAST(((2 * bp.baseline_score - COALESCE(up.user_score, 0)) / bp.baseline_score) * 100, 100)
                        ELSE 50
                    END
                ELSE
                    -- Normal scoring: higher is better
                    CASE
                        WHEN bp.baseline_score > 0 THEN
                            LEAST((COALESCE(up.user_score, 0) / bp.baseline_score) * 100, 100)
                        ELSE 50
                    END
            END AS tv_match_rate,
            bp.tv_weight
        FROM baseline_papi bp
        LEFT JOIN user_papi up ON bp.tv_name = up.tv_name
    ),
    
    -- TGV aggregation
    tgv_aggregation AS (
        SELECT
            tgv_name,
            SUM(tv_match_rate * tv_weight) / NULLIF(SUM(tv_weight), 0) AS tgv_match_rate,
            CASE
                WHEN tgv_name = 'COGNITIVE' THEN 0.30
                WHEN tgv_name = 'COMPETENCY' THEN 0.35
                WHEN tgv_name = 'WORK_STYLE' THEN 0.20
                ELSE 0.15
            END AS tgv_weight
        FROM tv_matches
        GROUP BY tgv_name
    ),
    
    -- Final score
    final_calculation AS (
        SELECT
            SUM(tgv_match_rate * tgv_weight) / NULLIF(SUM(tgv_weight), 0) AS final_match_rate
        FROM tgv_aggregation
    )
    
    SELECT
        'TV_DETAILS' AS result_type,
        tm.tgv_name,
        tm.tv_name,
        tm.tv_label,
        tm.baseline_score,
        tm.user_score,
        tm.tv_match_rate,
        tm.tv_weight,
        NULL::numeric AS tgv_match_rate,
        NULL::numeric AS tgv_weight,
        NULL::numeric AS final_match_rate
    FROM tv_matches tm
    
    UNION ALL
    
    SELECT
        'TGV_SUMMARY',
        tgv_name,
        NULL,
        NULL,
        NULL,
        NULL,
        NULL,
        NULL,
        tgv_match_rate,
        tgv_weight,
        NULL
    FROM tgv_aggregation
    
    UNION ALL
    
    SELECT
        'FINAL_SCORE',
        NULL,
        NULL,
        NULL,
        NULL,
        NULL,
        NULL,
        NULL,
        NULL,
        NULL,
        final_match_rate
    FROM final_calculation
    """
    
    # Execute query
    with engine.connect() as conn:
        df_result = pd.read_sql(text(breakdown_sql), conn)
    
    # Separate results
    tv_details = df_result[df_result['result_type'] == 'TV_DETAILS'][[
        'tgv_name', 'tv_name', 'tv_label', 'baseline_score', 'user_score', 'tv_match_rate', 'tv_weight'
    ]].copy()
    
    tgv_summary = df_result[df_result['result_type'] == 'TGV_SUMMARY'][[
        'tgv_name', 'tgv_match_rate', 'tgv_weight'
    ]].copy()
    
    final_row = df_result[df_result['result_type'] == 'FINAL_SCORE']
    final_score = final_row['final_match_rate'].iloc[0] if not final_row.empty else 0.0
    
    # Get employee info
    with engine.connect() as conn:
        emp_query = """
        SELECT 
            e.employee_id,
            e.fullname,
            pos.name AS position_name,
            dept.name AS department_name,
            g.name AS grade_name
        FROM employees e
        LEFT JOIN dim_positions pos ON e.position_id = pos.position_id
        LEFT JOIN dim_departments dept ON e.department_id = dept.department_id  
        LEFT JOIN dim_grades g ON e.grade_id = g.grade_id
        WHERE e.employee_id = %s
        """
        emp_info = pd.read_sql(emp_query, conn, params=(employee_id,))
        employee_info = emp_info.to_dict('records')[0] if not emp_info.empty else {}
    
    # Get benchmark count
    benchmark_n = len(benchmark_ids) if benchmark_ids else 0
    if benchmark_n == 0:
        with engine.connect() as conn:
            benchmark_n = pd.read_sql("SELECT COUNT(DISTINCT employee_id) FROM performance_yearly WHERE rating = 5", conn).iloc[0, 0]
    
    return {
        'tv_details': tv_details,
        'tgv_summary': tgv_summary,
        'final_score': final_score,
        'employee_info': employee_info,
        'benchmark_n': benchmark_n
    }

