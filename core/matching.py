# core/matching.py

import pandas as pd
from sqlalchemy import text

def run_match_query(engine, manual_ids=None, target_position_id=None, filters=None, search_name=None, rating_range=(1, 5), limit=200):
    """
    Menjalankan pipeline SQL Talent Matching lengkap dengan dukungan filter tambahan.
    """
    # --- Menyiapkan Parameter Benchmark ---
    if manual_ids:
        manual_array_sql = "ARRAY[" + ",".join(f"'{eid.strip()}'" for eid in manual_ids) + "]::text[]"
    else:
        manual_array_sql = "ARRAY[]::text[]"

    role_sql = "NULL" if not target_position_id else str(int(target_position_id))

    # Menentukan apakah fallback benchmark harus digunakan
    use_fallback = not manual_ids and not target_position_id

    # --- Menyiapkan Parameter Filter Tambahan ---
    filter_conditions = []
    params = {
        'min_rating_filter': int(rating_range[0]),
        'max_rating_filter': int(rating_range[1]),
        'limit_val': limit
    }
    if filters:
        for key, value in filters.items():
            if value is not None:
                condition = f"e.{key} = :{key}"
                filter_conditions.append(condition)
                params[key] = value

    filter_clause = ""
    if filter_conditions:
        filter_clause = " AND " + " AND ".join(filter_conditions)

    # Tambahkan kondisi filter rating ke filter_clause jika ada filter lainnya
    rating_filter_condition = f"py.rating BETWEEN :min_rating_filter AND :max_rating_filter"
    if filter_clause:
        filter_clause = "WHERE " + rating_filter_condition + " AND " + filter_clause[5:]  # menghapus 'WHERE '
    else:
        filter_clause = "WHERE " + rating_filter_condition

    if search_name:
        filter_clause += " AND e.fullname ILIKE :search_name"
        params['search_name'] = f"%{search_name}%"

    # --- SQL Engine Lengkap ---
    sql = f"""
    WITH params AS (
        SELECT
            {manual_array_sql} AS manual_hp,
            {role_sql}::int AS role_position_id,
            {str(use_fallback).lower()} AS use_fallback
    ),
    manual_set AS (SELECT unnest(manual_hp) AS employee_id FROM params),
    role_set AS (SELECT DISTINCT e.employee_id FROM employees e JOIN performance_yearly py USING(employee_id) JOIN params p ON TRUE WHERE py.rating >= 5 AND p.role_position_id IS NOT NULL AND e.position_id = p.role_position_id),
    benchmark_set AS (SELECT employee_id FROM manual_set UNION SELECT employee_id FROM role_set),
    fallback_benchmark AS (SELECT py.employee_id FROM performance_yearly py JOIN params p ON TRUE WHERE py.rating >= 5 AND p.use_fallback),
    bench_with_flag AS (
        SELECT employee_id, 1 as is_from_manual_or_role FROM benchmark_set
        UNION ALL
        SELECT employee_id, 0 as is_from_manual_or_role FROM fallback_benchmark
    ),
    final_bench AS (
        -- Jika ada benchmark manual/role, hanya gunakan itu; jika tidak, gunakan fallback
        SELECT employee_id FROM bench_with_flag WHERE is_from_manual_or_role = 1
        UNION
        SELECT employee_id FROM bench_with_flag WHERE is_from_manual_or_role = 0
            AND NOT EXISTS (SELECT 1 FROM bench_with_flag WHERE is_from_manual_or_role = 1)
    ),
    latest AS (SELECT (SELECT MAX(year) FROM competencies_yearly) AS comp_year),
    baseline_numeric AS (SELECT tv_name, PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY score) AS baseline_score FROM (SELECT c.pillar_code AS tv_name, c.score::numeric AS score FROM competencies_yearly c JOIN latest l ON c.year = l.comp_year WHERE c.employee_id IN (SELECT employee_id FROM final_bench) UNION ALL SELECT 'iq', p.iq::numeric FROM profiles_psych p WHERE p.employee_id IN (SELECT employee_id FROM final_bench) UNION ALL SELECT 'gtq', p.gtq::numeric FROM profiles_psych p WHERE p.employee_id IN (SELECT employee_id FROM final_bench) UNION ALL SELECT 'tiki', p.tiki::numeric FROM profiles_psych p WHERE p.employee_id IN (SELECT employee_id FROM final_bench) UNION ALL SELECT 'faxtor', p.faxtor::numeric FROM profiles_psych p WHERE p.employee_id IN (SELECT employee_id FROM final_bench) UNION ALL SELECT 'pauli', p.pauli::numeric FROM profiles_psych p WHERE p.employee_id IN (SELECT employee_id FROM final_bench)) x GROUP BY tv_name),
    all_numeric_scores AS (SELECT employee_id, pillar_code AS tv_name, score::numeric AS user_score FROM competencies_yearly JOIN latest l ON competencies_yearly.year = l.comp_year UNION ALL SELECT employee_id, 'iq', iq::numeric FROM profiles_psych UNION ALL SELECT employee_id, 'gtq', gtq::numeric FROM profiles_psych UNION ALL SELECT employee_id, 'tiki', tiki::numeric FROM profiles_psych UNION ALL SELECT employee_id, 'faxtor', faxtor::numeric FROM profiles_psych UNION ALL SELECT employee_id, 'pauli', pauli::numeric FROM profiles_psych),
    numeric_tv AS (SELECT sc.employee_id, bn.tv_name, bn.baseline_score, sc.user_score, (sc.user_score / NULLIF(bn.baseline_score,0)) * 100 AS tv_match_rate FROM all_numeric_scores sc JOIN baseline_numeric bn USING(tv_name)),
    reverse_list AS (SELECT UNNEST(ARRAY['Papi_I','Papi_K','Papi_Z','Papi_T']) AS scale_code),
    baseline_papi AS (SELECT ps.scale_code AS tv_name, PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY ps.score) AS baseline_score, (rl.scale_code IS NOT NULL) AS is_reverse FROM papi_scores ps JOIN final_bench fb USING(employee_id) LEFT JOIN reverse_list rl ON ps.scale_code = rl.scale_code GROUP BY ps.scale_code, rl.scale_code),
    papi_tv AS (SELECT ps.employee_id, bp.tv_name, bp.baseline_score, ps.score::numeric AS user_score, CASE WHEN bp.is_reverse THEN ((2 * bp.baseline_score - ps.score::numeric) / NULLIF(bp.baseline_score,0)) * 100 ELSE (ps.score::numeric / NULLIF(bp.baseline_score,0)) * 100 END AS tv_match_rate FROM papi_scores ps JOIN baseline_papi bp ON ps.scale_code = bp.tv_name),
    baseline_cat AS (SELECT 'mbti' AS tv_name, MODE() WITHIN GROUP (ORDER BY UPPER(TRIM(mbti))) AS baseline_value FROM profiles_psych p JOIN final_bench fb USING(employee_id) UNION ALL SELECT 'disc', MODE() WITHIN GROUP (ORDER BY UPPER(TRIM(disc))) FROM profiles_psych p JOIN final_bench fb USING(employee_id)),
    categorical_tv AS (SELECT p.employee_id, bc.tv_name, 1 AS baseline_score, 1 AS user_score, CASE WHEN (bc.tv_name = 'mbti' AND UPPER(TRIM(p.mbti)) = bc.baseline_value) OR (bc.tv_name = 'disc' AND UPPER(TRIM(p.disc)) = bc.baseline_value) THEN 100 ELSE 0 END AS tv_match_rate FROM profiles_psych p CROSS JOIN baseline_cat bc),
    all_tv AS (SELECT * FROM numeric_tv UNION ALL SELECT * FROM papi_tv UNION ALL SELECT * FROM categorical_tv),
    tv_map AS (SELECT tv_name, tgv_name, tv_weight FROM talent_variables_mapping),
    tgv_match AS (SELECT a.employee_id, m.tgv_name, SUM(a.tv_match_rate * m.tv_weight) / SUM(m.tv_weight) AS tgv_match_rate FROM all_tv a JOIN tv_map m USING(tv_name) GROUP BY a.employee_id, m.tgv_name),
    final_match AS (SELECT employee_id, SUM(tgv_match_rate * g.tgv_weight) AS final_match_rate FROM tgv_match t JOIN talent_group_weights g USING(tgv_name) GROUP BY employee_id)

    SELECT
        e.employee_id,
        e.fullname,
        pos.name as position_name,
        dep.name as department_name,
        div.name as division_name,
        py.rating,
        fm.final_match_rate
    FROM final_match fm
    JOIN employees e USING(employee_id)
    JOIN performance_yearly py USING(employee_id)
    LEFT JOIN dim_positions pos ON e.position_id = pos.position_id
    LEFT JOIN dim_departments dep ON e.department_id = dep.department_id
    LEFT JOIN dim_divisions div ON e.division_id = div.division_id
    {filter_clause}
    ORDER BY final_match_rate DESC
    LIMIT :limit_val;
    """

    with engine.connect() as conn:
        df = pd.read_sql(text(sql), conn, params=params)

    # Hapus kolom rating dari hasil jika tidak ingin ditampilkan di UI
    df = df.drop(columns=['rating'], errors='ignore')

    return df
