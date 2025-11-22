# core/matching.py

import pandas as pd
from sqlalchemy import text

# ===================================================================================
# FUNGSI UTAMA 1: get_match_for_single_person
# ===================================================================================
# Tujuan: Khusus untuk Mode A. Menghitung kecocokan satu karyawan terhadap
#         benchmark dari SEMUA posisi yang ada di perusahaan.
# ===================================================================================
def get_match_for_single_person(engine, employee_id, limit=200):
    """
    Skenario 1: Menghitung kecocokan satu karyawan terhadap benchmark dari SEMUA posisi.
    """
    # Ambil semua posisi yang ada untuk dijadikan benchmark
    with engine.connect() as conn:
        positions_df = pd.read_sql("SELECT position_id, name FROM dim_positions", conn)
    
    all_results = []
    
    # Lakukan iterasi untuk setiap posisi sebagai benchmark
    for _, pos_row in positions_df.iterrows():
        # Untuk setiap posisi, jalankan query matching standar.
        # Kita hanya tertarik pada skor dari karyawan yang kita cari (manual_ids_to_filter).
        df = run_standard_match_query(
            engine,
            target_position_id_for_benchmark=pos_row['position_id'],
            manual_ids_to_filter=[employee_id] # Filter hasil untuk menampilkan karyawan ini saja
        )
        if not df.empty:
            # Tambahkan kolom untuk menandai benchmark posisi mana yang digunakan
            df['benchmark_position'] = pos_row['name']
            all_results.append(df)
            
    if not all_results:
        return pd.DataFrame()
        
    # Gabungkan semua hasil dan urutkan berdasarkan skor tertinggi
    final_df = pd.concat(all_results, ignore_index=True)
    return final_df.sort_values('final_match_rate', ascending=False).head(limit)


# ===================================================================================
# FUNGSI UTAMA 2: run_standard_match_query
# ===================================================================================
# Tujuan: Khusus untuk Mode B dan Mode Default. Ini adalah mesin SQL utama kita
#         yang akan berisi semua CTEs untuk menghasilkan daftar karyawan unik.
# ===================================================================================
def run_standard_match_query(engine, manual_ids_for_benchmark=None, target_position_id_for_benchmark=None, 
                             filters=None, search_name=None, 
                             rating_range=(1, 5), limit=200, manual_ids_to_filter=None):
    """
    Skenario 2 & 3: Menjalankan pipeline SQL Talent Matching standar untuk mencari banyak orang.
    """
    # --- Bagian 1: Menyiapkan Parameter dari Python untuk dikirim ke SQL ---
    use_fallback = not manual_ids_for_benchmark and not target_position_id_for_benchmark
    
    if manual_ids_for_benchmark:
        manual_array_sql = "ARRAY[" + ",".join(f"'{eid.strip()}'" for eid in manual_ids_for_benchmark) + "]::text[]"
    else:
        manual_array_sql = "ARRAY[]::text[]"

    role_sql = "NULL" if not target_position_id_for_benchmark else str(int(target_position_id_for_benchmark))

    # --- Bagian 2: Menyiapkan Parameter untuk Filter Klausa WHERE ---
    filter_conditions = []
    params = {
        'min_rating_filter': rating_range[0],
        'max_rating_filter': rating_range[1],
        'limit_val': limit
    }
    if filters:
        for key, value in filters.items():
            if value is not None:
                filter_conditions.append(f"e.{key} = :{key}")
                params[key] = value
    
    filter_clause = ""
    if filter_conditions:
        filter_clause = "AND " + " AND ".join(filter_conditions)

    if search_name:
        filter_clause += " AND e.fullname ILIKE :search_name"
        params['search_name'] = f"%{search_name}%"
        
    if manual_ids_to_filter:
        filter_clause += " AND e.employee_id = ANY(:manual_ids_to_filter)"
        params['manual_ids_to_filter'] = manual_ids_to_filter

    # --- Bagian 3: String SQL Lengkap dengan Semua CTEs ---
    # (Akan kita isi di potongan berikutnya)
    sql = f"""
    -- Placeholder untuk query SQL lengkap
    SELECT 1; 
    """

    # --- Bagian 3: String SQL Lengkap dengan Semua CTEs ---
    sql = f"""
    WITH params AS (
        SELECT 
            {manual_array_sql} AS manual_hp,
            {role_sql}::int AS role_position_id,
            {use_fallback} AS use_fallback
    ),
    manual_set AS (SELECT unnest(manual_hp) AS employee_id FROM params),
    role_set AS (SELECT DISTINCT e.employee_id FROM employees e JOIN performance_yearly py USING(employee_id) JOIN params p ON TRUE WHERE py.rating >= 5 AND p.role_position_id IS NOT NULL AND e.position_id = p.role_position_id),
    benchmark_set AS (SELECT employee_id FROM manual_set UNION SELECT employee_id FROM role_set),
    fallback_benchmark AS (SELECT py.employee_id FROM performance_yearly py JOIN params p ON TRUE WHERE py.rating >= 5 AND p.use_fallback),
    final_bench AS (SELECT DISTINCT employee_id FROM benchmark_set UNION SELECT DISTINCT employee_id FROM fallback_benchmark WHERE NOT EXISTS (SELECT 1 FROM benchmark_set)),
    
    latest AS (SELECT (SELECT MAX(year) FROM competencies_yearly) AS comp_year),
    
    baseline_numeric AS (
        SELECT tv_name, PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY score) AS baseline_score 
        FROM (
            SELECT c.pillar_code AS tv_name, c.score::numeric AS score FROM competencies_yearly c JOIN latest l ON c.year = l.comp_year WHERE c.employee_id IN (SELECT employee_id FROM final_bench)
            UNION ALL SELECT 'iq', p.iq::numeric FROM profiles_psych p WHERE p.employee_id IN (SELECT employee_id FROM final_bench)
            UNION ALL SELECT 'gtq', p.gtq::numeric FROM profiles_psych p WHERE p.employee_id IN (SELECT employee_id FROM final_bench)
            UNION ALL SELECT 'tiki', p.tiki::numeric FROM profiles_psych p WHERE p.employee_id IN (SELECT employee_id FROM final_bench)
            UNION ALL SELECT 'faxtor', p.faxtor::numeric FROM profiles_psych p WHERE p.employee_id IN (SELECT employee_id FROM final_bench)
            UNION ALL SELECT 'pauli', p.pauli::numeric FROM profiles_psych p WHERE p.employee_id IN (SELECT employee_id FROM final_bench)
        ) x GROUP BY tv_name
    ),
    
    all_numeric_scores AS (
        SELECT employee_id, pillar_code AS tv_name, score::numeric AS user_score FROM competencies_yearly JOIN latest l ON competencies_yearly.year = l.comp_year
        UNION ALL SELECT employee_id, 'iq', iq::numeric FROM profiles_psych
        UNION ALL SELECT employee_id, 'gtq', gtq::numeric FROM profiles_psych
        UNION ALL SELECT employee_id, 'tiki', tiki::numeric FROM profiles_psych
        UNION ALL SELECT employee_id, 'faxtor', faxtor::numeric FROM profiles_psych
        UNION ALL SELECT employee_id, 'pauli', pauli::numeric FROM profiles_psych
    ),

    numeric_tv AS (
        SELECT sc.employee_id, bn.tv_name, (sc.user_score / NULLIF(bn.baseline_score, 0)) * 100 AS tv_match_rate 
        FROM all_numeric_scores sc JOIN baseline_numeric bn USING(tv_name)
    ),

    papi_tv AS (
        SELECT ps.employee_id, bp.tv_name, 
               CASE WHEN bp.is_reverse THEN ((2 * bp.baseline_score - ps.score::numeric) / NULLIF(bp.baseline_score, 0)) * 100 
                    ELSE (ps.score::numeric / NULLIF(bp.baseline_score, 0)) * 100 
               END AS tv_match_rate 
        FROM papi_scores ps 
        JOIN (
            SELECT ps.scale_code AS tv_name, 
                   PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY ps.score) AS baseline_score, 
                   (rl.scale_code IS NOT NULL) AS is_reverse 
            FROM papi_scores ps 
            JOIN final_bench fb USING(employee_id) 
            LEFT JOIN (SELECT UNNEST(ARRAY['Papi_I','Papi_K','Papi_Z','Papi_T']) AS scale_code) rl ON ps.scale_code = rl.scale_code 
            GROUP BY ps.scale_code, rl.scale_code
        ) bp ON ps.scale_code = bp.tv_name
    ),

    categorical_tv AS (
        SELECT p.employee_id, bc.tv_name, 
               CASE WHEN (bc.tv_name = 'mbti' AND UPPER(TRIM(p.mbti)) = bc.baseline_value) OR (bc.tv_name = 'disc' AND UPPER(TRIM(p.disc)) = bc.baseline_value) THEN 100 ELSE 0 END AS tv_match_rate 
        FROM profiles_psych p 
        CROSS JOIN (
            SELECT 'mbti' AS tv_name, MODE() WITHIN GROUP (ORDER BY UPPER(TRIM(mbti))) AS baseline_value FROM profiles_psych p JOIN final_bench fb USING(employee_id)
            UNION ALL
            SELECT 'disc', MODE() WITHIN GROUP (ORDER BY UPPER(TRIM(disc))) FROM profiles_psych p JOIN final_bench fb USING(employee_id)
        ) bc
    ),

    all_tv AS (
        SELECT employee_id, tv_name, tv_match_rate FROM numeric_tv
        UNION ALL
        SELECT employee_id, tv_name, tv_match_rate FROM papi_tv
        UNION ALL
        SELECT employee_id, tv_name, tv_match_rate FROM categorical_tv
    ),

    tgv_match AS (
        SELECT a.employee_id, m.tgv_name, SUM(a.tv_match_rate * m.tv_weight) / SUM(m.tv_weight) AS tgv_match_rate 
        FROM all_tv a 
        JOIN talent_variables_mapping m USING(tv_name) 
        GROUP BY a.employee_id, m.tgv_name
    ),

    final_match AS (
        SELECT employee_id, SUM(tgv_match_rate * g.tgv_weight) AS final_match_rate 
        FROM tgv_match t 
        JOIN talent_group_weights g USING(tgv_name) 
        GROUP BY employee_id
    )
    
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
    JOIN performance_yearly py ON e.employee_id = py.employee_id AND py.year = (SELECT MAX(year) FROM performance_yearly)
    LEFT JOIN dim_positions pos ON e.position_id = pos.position_id
    LEFT JOIN dim_departments dep ON e.department_id = dep.department_id
    LEFT JOIN dim_divisions div ON e.division_id = div.division_id
    WHERE py.rating BETWEEN :min_rating_filter AND :max_rating_filter {filter_clause}
    ORDER BY final_match_rate DESC
    LIMIT :limit_val;
    """

    # --- Bagian 4: Eksekusi Query dan Mengembalikan Hasil ---
    with engine.connect() as conn:
        df = pd.read_sql(text(sql), conn, params=params)
    
    return df
