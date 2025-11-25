# core/matching.py

import pandas as pd
from sqlalchemy import text

# Template SQL Engine Toggle-Ready
SQL_TEMPLATE = """
-- ===================================================================================
-- GOLDEN TEMPLATE: TALENT MATCHING ENGINE (TOGGLE-READY)
-- ===================================================================================
-- Proyek : Talent Match Intelligence Dashboard
-- Versi  : 3.1 (Benchmark-Driven + Manual Benchmark Toggle)
-- ===================================================================================

WITH
-- -----------------------------------------------------------------------------------
-- TAHAP 1: PARAMETER & PEMBENTUK BENCHMARK
-- -----------------------------------------------------------------------------------
params AS (
    SELECT
        -- Diisi oleh Python (ARRAY['EMP001','EMP002']::text[] atau ARRAY[]::text[])
        {manual_array_sql}                            AS manual_hp,

        -- FILTER BENCHMARK (MODE B) - DIISI PYTHON (angka atau NULL)
        {filter_position_id}::int                     AS filter_position_id,
        {filter_department_id}::int                   AS filter_department_id,
        {filter_division_id}::int                     AS filter_division_id,
        {filter_grade_id}::int                        AS filter_grade_id,

        -- MINIMUM RATING UNTUK HIGH PERFORMER (biasanya 5)
        {min_rating}::int                             AS min_hp_rating,

        -- TOGGLE: GUNAKAN MANUAL_ID SEBAGAI BENCHMARK?
        -- TRUE  = Mode A (Manual Benchmark)
        -- FALSE = Mode B / Default (Manual kosong)
        {use_manual_as_benchmark}::boolean            AS use_manual_as_benchmark
),

-- Kumpulan manual benchmark (Mode A dengan toggle ON)
manual_set AS (
    SELECT unnest(p.manual_hp) AS employee_id
    FROM params p
),

-- Kumpulan benchmark berbasis filter (Mode B)
-- HP rating fixed = 5 (High Performer) based on system design
filter_based_set AS (
    SELECT DISTINCT e.employee_id
    FROM public.employees e
    JOIN public.performance_yearly py USING(employee_id)
    JOIN params p ON TRUE
    WHERE py.rating = p.min_hp_rating  -- HP rating fixed = 5 (High Performer) based on system design
      AND (p.filter_position_id   IS NULL OR e.position_id   = p.filter_position_id)
      AND (p.filter_department_id IS NULL OR e.department_id = p.filter_department_id)
      AND (p.filter_division_id   IS NULL OR e.division_id   = p.filter_division_id)
      AND (p.filter_grade_id      IS NULL OR e.grade_id      = p.filter_grade_id)
),

-- Fallback benchmark jika tidak ada manual & filter
-- HP rating fixed = 5 (High Performer) based on system design
fallback_benchmark AS (
    SELECT py.employee_id
    FROM public.performance_yearly py
    JOIN params p ON TRUE
    WHERE py.rating = p.min_hp_rating  -- HP rating fixed = 5 (High Performer) based on system design
),

-- FINAL BENCHMARK GROUP (final_bench)
-- Aturan:
--   1) Jika use_manual_as_benchmark = TRUE dan manual_hp tidak kosong:
--        final_bench = manual_set
--   2) Jika manual kosong & filter menghasilkan data:
--        final_bench = filter_based_set
--   3) Jika tidak ada input sama sekali:
--        final_bench = fallback_benchmark
final_bench AS (
    -- Kasus 1: Manual Benchmark (Mode A - Toggle ON)
    SELECT ms.employee_id
    FROM manual_set ms
    JOIN params p ON TRUE
    WHERE p.use_manual_as_benchmark

    UNION

    -- Kasus 2: Filter Benchmark (Mode B) - Hanya jika tidak menggunakan manual
    SELECT fb.employee_id
    FROM filter_based_set fb
    JOIN params p ON TRUE
    WHERE NOT p.use_manual_as_benchmark
      AND NOT EXISTS (SELECT 1 FROM manual_set)

    UNION

    -- Kasus 3: Fallback Benchmark (Default Mode)
    SELECT fb2.employee_id
    FROM fallback_benchmark fb2
    JOIN params p ON TRUE
    WHERE NOT p.use_manual_as_benchmark
      AND NOT EXISTS (SELECT 1 FROM manual_set)
      AND NOT EXISTS (SELECT 1 FROM filter_based_set)
),

-- -----------------------------------------------------------------------------------
-- TAHAP 2: PERHITUNGAN SKOR BASELINE
-- -----------------------------------------------------------------------------------
latest AS (
    SELECT (SELECT MAX(year) FROM public.competencies_yearly) AS comp_year
),

baseline_numeric AS (
    SELECT tv_name,
           PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY score) AS baseline_score
    FROM (
        SELECT c.employee_id,
               c.pillar_code AS tv_name,
               c.score::numeric AS score
        FROM public.competencies_yearly c
        JOIN latest l ON c.year = l.comp_year
        WHERE c.employee_id IN (SELECT employee_id FROM final_bench)

        UNION ALL
        SELECT p.employee_id, 'iq'::text, p.iq::numeric
        FROM public.profiles_psych p
        WHERE p.employee_id IN (SELECT employee_id FROM final_bench)

        UNION ALL
        SELECT p.employee_id, 'gtq'::text, p.gtq::numeric
        FROM public.profiles_psych p
        WHERE p.employee_id IN (SELECT employee_id FROM final_bench)

        UNION ALL
        SELECT p.employee_id, 'tiki'::text, p.tiki::numeric
        FROM public.profiles_psych p
        WHERE p.employee_id IN (SELECT employee_id FROM final_bench)

        UNION ALL
        SELECT p.employee_id, 'faxtor'::text, p.faxtor::numeric
        FROM public.profiles_psych p
        WHERE p.employee_id IN (SELECT employee_id FROM final_bench)

        UNION ALL
        SELECT p.employee_id, 'pauli'::text, p.pauli::numeric
        FROM public.profiles_psych p
        WHERE p.employee_id IN (SELECT employee_id FROM final_bench)
    ) x
    GROUP BY tv_name
),

baseline_papi AS (
    SELECT
        ps.scale_code AS tv_name,
        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY ps.score) AS baseline_score,
        (rl.scale_code IS NOT NULL) AS is_reverse
    FROM public.papi_scores ps
    JOIN final_bench fb USING(employee_id)
    LEFT JOIN (
        SELECT UNNEST(ARRAY['Papi_I','Papi_K','Papi_Z','Papi_T']) AS scale_code
    ) rl ON ps.scale_code = rl.scale_code
    GROUP BY ps.scale_code, rl.scale_code
),

baseline_cat AS (
    SELECT
        'mbti' AS tv_name,
        MODE() WITHIN GROUP (ORDER BY UPPER(TRIM(mbti))) AS baseline_value
    FROM public.profiles_psych p
    JOIN final_bench fb USING(employee_id)

    UNION ALL

    SELECT
        'disc' AS tv_name,
        MODE() WITHIN GROUP (ORDER BY UPPER(TRIM(disc))) AS baseline_value
    FROM public.profiles_psych p
    JOIN final_bench fb USING(employee_id)
),

-- -----------------------------------------------------------------------------------
-- TAHAP 3: PERHITUNGAN tv_match_rate UNTUK SEMUA KARYAWAN
-- -----------------------------------------------------------------------------------
all_numeric_scores AS (
    SELECT
        c.employee_id,
        c.pillar_code AS tv_name,
        c.score::numeric AS user_score
    FROM public.competencies_yearly c
    JOIN latest l ON c.year = l.comp_year

    UNION ALL

    SELECT p.employee_id, 'iq'::text, p.iq::numeric
    FROM public.profiles_psych p

    UNION ALL

    SELECT p.employee_id, 'gtq'::text, p.gtq::numeric
    FROM public.profiles_psych p

    UNION ALL

    SELECT p.employee_id, 'tiki'::text, p.tiki::numeric
    FROM public.profiles_psych p

    UNION ALL

    SELECT p.employee_id, 'faxtor'::text, p.faxtor::numeric
    FROM public.profiles_psych p

    UNION ALL

    SELECT p.employee_id, 'pauli'::text, p.pauli::numeric
    FROM public.profiles_psych p
),

numeric_tv AS (
    SELECT
        sc.employee_id,
        bn.tv_name,
        (sc.user_score / NULLIF(bn.baseline_score, 0)) * 100 AS tv_match_rate
    FROM all_numeric_scores sc
    JOIN baseline_numeric bn USING(tv_name)
),

papi_tv AS (
    SELECT
        ps.employee_id,
        bp.tv_name,
        CASE
            WHEN bp.is_reverse THEN ((2 * bp.baseline_score - ps.score::numeric)
                                      / NULLIF(bp.baseline_score, 0)) * 100
            ELSE (ps.score::numeric / NULLIF(bp.baseline_score, 0)) * 100
        END AS tv_match_rate
    FROM public.papi_scores ps
    JOIN baseline_papi bp ON ps.scale_code = bp.tv_name
),

categorical_tv AS (
    SELECT
        p.employee_id,
        bc.tv_name,
        CASE
            WHEN (bc.tv_name = 'mbti'
                  AND UPPER(TRIM(p.mbti)) = bc.baseline_value)
              OR (bc.tv_name = 'disc'
                  AND UPPER(TRIM(p.disc)) = bc.baseline_value)
            THEN 100
            ELSE 0
        END AS tv_match_rate
    FROM public.profiles_psych p
    CROSS JOIN baseline_cat bc
),

all_tv AS (
    SELECT employee_id, tv_name, tv_match_rate FROM numeric_tv
    UNION ALL
    SELECT employee_id, tv_name, tv_match_rate FROM papi_tv
    UNION ALL
    SELECT employee_id, tv_name, tv_match_rate FROM categorical_tv
),

-- -----------------------------------------------------------------------------------
-- TAHAP 4: AGREGASI TGV & SKOR AKHIR
-- -----------------------------------------------------------------------------------
tgv_match AS (
    SELECT
        a.employee_id,
        m.tgv_name,
        SUM(a.tv_match_rate * m.tv_weight) / SUM(m.tv_weight) AS tgv_match_rate
    FROM all_tv a
    JOIN public.talent_variables_mapping m USING(tv_name)
    GROUP BY a.employee_id, m.tgv_name
),

final_match AS (
    SELECT
        t.employee_id,
        SUM(t.tgv_match_rate * g.tgv_weight) AS final_match_rate
    FROM tgv_match t
    JOIN public.talent_group_weights g USING(tgv_name)
    GROUP BY t.employee_id
),

-- -----------------------------------------------------------------------------------
-- TAHAP 5: PENYAJIAN HASIL AKHIR
-- -----------------------------------------------------------------------------------
final_results AS (
    SELECT
        e.employee_id,
        e.fullname,
        pos.name AS position_name,
        dep.name AS department_name,
        div.name AS division_name,
        g.name   AS grade_name,
        ROUND(e.years_of_service_months / 12.0, 1) AS experience_years,
        fm.final_match_rate
    FROM final_match fm
    JOIN public.employees e USING(employee_id)
    LEFT JOIN public.dim_positions   pos ON e.position_id   = pos.position_id
    LEFT JOIN public.dim_departments dep ON e.department_id = dep.department_id
    LEFT JOIN public.dim_divisions   div ON e.division_id   = div.division_id
    LEFT JOIN public.dim_grades      g   ON e.grade_id      = g.grade_id
)

-- ===================================================================================
-- FINAL SELECT
-- Catatan:
-- - TIDAK ADA FILTER TAMBAHAN DI SINI.
-- - SORT/FILTER UNTUK TAMPILAN DILAKUKAN DI LEVEL STREAMLIT (UI), BUKAN DI SQL.
-- ===================================================================================
SELECT *
FROM final_results
ORDER BY final_match_rate DESC
LIMIT 200;
"""


# ===================================================================================
# FUNGSI UTAMA 1: get_match_for_single_person
# ===================================================================================
# Tujuan: Khusus untuk Mode A (toggle OFF). Menghitung kecocokan satu karyawan terhadap
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
# Tujuan: Khusus untuk Mode A (toggle ON), Mode B, dan Mode Default.
#        Ini adalah mesin SQL utama kita yang akan berisi semua CTEs
#        untuk menghasilkan daftar karyawan unik berdasarkan benchmark toggle-ready.
# ===================================================================================
def run_standard_match_query(engine, manual_ids_for_benchmark=None, target_position_id_for_benchmark=None,
                             filters=None, search_name=None,
                             rating_range=(1, 5), limit=200, manual_ids_to_filter=None,
                             use_manual_as_benchmark=False, min_rating=5):
    """
    Skenario 2 & 3: Menjalankan pipeline SQL Talent Matching standar untuk mencari banyak orang.
    Sekarang dengan dukungan toggle untuk menentukan apakah manual_ids digunakan sebagai benchmark.
    """
    # --- Bagian 1: Menyiapkan Parameter dari Python untuk dikirim ke SQL ---

    # Persiapan manual_array_sql
    if manual_ids_for_benchmark:
        manual_array_sql = "ARRAY[" + ",".join(f"'{eid.strip()}'" for eid in manual_ids_for_benchmark) + "]::text[]"
    else:
        manual_array_sql = "ARRAY[]::text[]"

    # Persiapan filter parameter
    if filters:
        filter_position_id_sql = str(filters.get("position_id")) if filters.get("position_id") else "NULL"
        filter_department_id_sql = str(filters.get("department_id")) if filters.get("department_id") else "NULL"
        filter_division_id_sql = str(filters.get("division_id")) if filters.get("division_id") else "NULL"
        filter_grade_id_sql = str(filters.get("grade_id")) if filters.get("grade_id") else "NULL"
    else:
        filter_position_id_sql = "NULL"
        filter_department_id_sql = "NULL"
        filter_division_id_sql = "NULL"
        filter_grade_id_sql = "NULL"

    # --- Bagian 2: Format SQL dengan Parameter Toggle-Ready ---
    sql = SQL_TEMPLATE.format(
        manual_array_sql=manual_array_sql,
        filter_position_id=filter_position_id_sql,
        filter_department_id=filter_department_id_sql,
        filter_division_id=filter_division_id_sql,
        filter_grade_id=filter_grade_id_sql,
        min_rating=min_rating,
        use_manual_as_benchmark=str(use_manual_as_benchmark).lower()
    )

    # --- Bagian 3: Eksekusi Query dan Mengembalikan Hasil ---
    with engine.connect() as conn:
        df = pd.read_sql(text(sql), conn)

    # Jika manual_ids_to_filter digunakan (untuk Mode A - rekomendasi posisi), filter hasilnya
    if manual_ids_to_filter:
        df = df[df['employee_id'].isin(manual_ids_to_filter)]

    return df


import math

def is_missing(value):
    return value is None or value == "" or (isinstance(value, float) and math.isnan(value))

def validate_employee_data(employee_id, engine):
    """
    Cek kelengkapan data competency, psychometrics, papi, mbti, disc
    Return dict:
    { "ok": True/False, "missing": [...], "detail": "..." }
    """
    with engine.connect() as conn:
        # Cek data karyawan
        emp_query = """
        SELECT
            e.employee_id,
            e.position_id,
            e.department_id,
            e.division_id,
            e.grade_id,
            p.iq,
            p.gtq,
            p.tiki,
            p.pauli,
            p.faxtor,
            p.mbti,
            p.disc
        FROM employees e
        LEFT JOIN profiles_psych p ON e.employee_id = p.employee_id
        WHERE e.employee_id = %s
        """

        emp_data = pd.read_sql(emp_query, conn, params=(employee_id,))

        missing_items = []

        if emp_data.empty:
            return {
                "ok": False,
                "missing": ["employee_data"],
                "detail": "Employee data not found in database"
            }

        row = emp_data.iloc[0]

        # Cek missing metadata
        if is_missing(row['position_id']):
            missing_items.append("position_id")
        if is_missing(row['department_id']):
            missing_items.append("department_id")
        if is_missing(row['division_id']):
            missing_items.append("division_id")
        if is_missing(row['grade_id']):
            missing_items.append("grade_id")

        # Cek missing psychometric
        if is_missing(row['iq']):
            missing_items.append("iq")
        if is_missing(row['gtq']):
            missing_items.append("gtq")
        if is_missing(row['tiki']):
            missing_items.append("tiki")
        if is_missing(row['pauli']):
            missing_items.append("pauli")
        if is_missing(row['faxtor']):
            missing_items.append("faxtor")
        if is_missing(row['mbti']) or (row['mbti'] and str(row['mbti']).strip() == ''):
            missing_items.append("mbti")
        if is_missing(row['disc']) or (row['disc'] and str(row['disc']).strip() == ''):
            missing_items.append("disc")

        # Cek competency pillars
        comp_query = """
        SELECT pillar_code
        FROM competencies_yearly
        WHERE employee_id = %s AND year = (SELECT MAX(year) FROM competencies_yearly)
        """

        comp_data = pd.read_sql(comp_query, conn, params=(employee_id,))
        if comp_data.empty:
            missing_items.append("competencies")

        # Cek PAPI scores
        papi_query = """
        SELECT COUNT(*) as count
        FROM papi_scores
        WHERE employee_id = %s
        """

        papi_data = pd.read_sql(papi_query, conn, params=(employee_id,))
        papi_count = papi_data.iloc[0]['count'] if not papi_data.empty else 0

        # PAPI Kostick memiliki 20 skala - cek apakah semua tersedia
        if papi_count < 20:
            missing_items.append("papi_scores")

        if missing_items:
            return {
                "ok": False,
                "missing": missing_items,
                "detail": f"Missing data: {', '.join(missing_items)}"
            }
        else:
            return {
                "ok": True,
                "missing": [],
                "detail": "All required data available"
            }


# ===================================================================================
# FUNGSI WRAPPER: execute_matching
# ===================================================================================
# Tujuan: Menangani logika mode operasi berdasarkan parameter toggle-ready
# ===================================================================================
def execute_matching(engine, manual_ids, filters, use_manual_as_benchmark):
    """
    Wrapper untuk menentukan mode operasi:
    - Mode A Benchmark (manual_ids + toggle ON): run_standard_match_query(...manual benchmark...)
    - Mode A Recommendation (manual_ids + toggle OFF): get_match_for_single_person()
    - Mode B Benchmark (manual kosong + filter aktif): run_standard_match_query(filters=filters)
    - Default Mode (tidak ada input): run_standard_match_query()
    """
    if manual_ids:
        if use_manual_as_benchmark:
            # Mode A Benchmark: Gunakan manual_ids sebagai benchmark
            return run_standard_match_query(
                engine,
                manual_ids_for_benchmark=manual_ids,
                use_manual_as_benchmark=True
            )
        else:
            # Mode A Recommendation: Gunakan fungsi rekomendasi posisi
            # Ambil satu employee_id jika multiple manual_ids
            if isinstance(manual_ids, list) and len(manual_ids) > 0:
                employee_id = manual_ids[0]
            else:
                employee_id = manual_ids
            return get_match_for_single_person(engine, employee_id)
    elif filters and any(filters.values()):
        # Mode B Benchmark: Gunakan filter untuk membentuk benchmark
        return run_standard_match_query(
            engine,
            filters=filters,
            use_manual_as_benchmark=False
        )
    else:
        # Default Mode: Gunakan benchmark default (HP rating fixed = 5)
        return run_standard_match_query(
            engine,
            use_manual_as_benchmark=False
        )
