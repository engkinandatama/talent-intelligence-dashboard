-- ===================================================================================
-- GOLDEN TEMPLATE: TALENT MATCHING ENGINE
-- ===================================================================================
-- Proyek: Talent Match Intelligence Dashboard
-- Versi: 2.0 (Stabil, Sesuai Skema Final)
--
-- ATURAN KETAT:
-- 1. JANGAN MENGUBAH STRUKTUR CTE ATAU URUTANNYA.
-- 2. JANGAN MENGGANTI LOGIKA INTI (PERCENTILE_CONT, MODE, RUMUS MATCHING).
-- 3. MODIFIKASI HANYA DIIZINKAN PADA BAGIAN YANG DITANDAI (misal: Final SELECT).
-- 4. NILAI PARAMETER (ditandai dengan {}) AKAN DIISI SECARA DINAMIS OLEH PYTHON.
-- ===================================================================================

WITH
-- -----------------------------------------------------------------------------------
-- TAHAP 1: PENENTUAN BENCHMARK
-- Tanggung Jawab: Mengambil input dari UI dan membuat satu set 'employee_id' benchmark.
-- -----------------------------------------------------------------------------------
params AS (
    SELECT
        {manual_array_sql} AS manual_hp,         -- Diisi oleh Python: ARRAY['EMP1', 'EMP2']::text[]
        {role_sql}::int AS role_position_id,     -- Diisi oleh Python: e.g., 4 atau NULL
        {min_rating}::int AS min_hp_rating       -- Diisi oleh Python: e.g., 5
),

-- CTE untuk benchmark dari Mode A (Manual)
manual_set AS (
    SELECT unnest(manual_hp) AS employee_id FROM params
),

-- CTE untuk benchmark dari Mode B (Berdasarkan Posisi)
role_set AS (
    SELECT DISTINCT e.employee_id
    FROM public.employees e
    JOIN public.performance_yearly py USING(employee_id)
    JOIN params p ON TRUE
    WHERE py.rating >= p.min_hp_rating
      AND p.role_position_id IS NOT NULL
      AND e.position_id = p.role_position_id
),

-- CTE untuk menggabungkan benchmark Mode A dan B
benchmark_set AS (
    SELECT employee_id FROM manual_set
    UNION
    SELECT employee_id FROM role_set
),

-- CTE Fallback jika tidak ada benchmark yang dipilih
fallback_benchmark AS (
    SELECT py.employee_id
    FROM public.performance_yearly py
    JOIN params p ON TRUE
    WHERE py.rating >= p.min_hp_rating
),

-- CTE Final: Menghasilkan daftar benchmark yang bersih dan unik
final_bench AS (
    SELECT DISTINCT employee_id FROM benchmark_set
    UNION
    SELECT DISTINCT employee_id FROM fallback_benchmark
    WHERE NOT EXISTS (SELECT 1 FROM benchmark_set)
),

-- -----------------------------------------------------------------------------------
-- TAHAP 2: PERHITUNGAN SKOR BASELINE
-- Tanggung Jawab: Menghitung skor median/mode dari set benchmark untuk setiap variabel.
-- -----------------------------------------------------------------------------------
latest AS (
    SELECT (SELECT MAX(year) FROM public.competencies_yearly) AS comp_year
),

baseline_numeric AS (
    SELECT tv_name, PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY score) AS baseline_score
    FROM (
        SELECT c.pillar_code AS tv_name, c.score::numeric AS score FROM public.competencies_yearly c JOIN latest l ON c.year = l.comp_year WHERE c.employee_id IN (SELECT employee_id FROM final_bench)
        UNION ALL SELECT 'iq', p.iq::numeric FROM public.profiles_psych p WHERE p.employee_id IN (SELECT employee_id FROM final_bench)
        UNION ALL SELECT 'gtq', p.gtq::numeric FROM public.profiles_psych p WHERE p.employee_id IN (SELECT employee_id FROM final_bench)
        UNION ALL SELECT 'tiki', p.tiki::numeric FROM public.profiles_psych p WHERE p.employee_id IN (SELECT employee_id FROM final_bench)
        UNION ALL SELECT 'faxtor', p.faxtor::numeric FROM public.profiles_psych p WHERE p.employee_id IN (SELECT employee_id FROM final_bench)
        UNION ALL SELECT 'pauli', p.pauli::numeric FROM public.profiles_psych p WHERE p.employee_id IN (SELECT employee_id FROM final_bench)
    ) x GROUP BY tv_name
),

baseline_papi AS (
    SELECT
        ps.scale_code AS tv_name,
        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY ps.score) AS baseline_score,
        (rl.scale_code IS NOT NULL) AS is_reverse
    FROM public.papi_scores ps
    JOIN final_bench fb USING(employee_id)
    LEFT JOIN (SELECT UNNEST(ARRAY['Papi_I','Papi_K','Papi_Z','Papi_T']) AS scale_code) rl ON ps.scale_code = rl.scale_code
    GROUP BY ps.scale_code, rl.scale_code
),

baseline_cat AS (
    SELECT 'mbti' AS tv_name, MODE() WITHIN GROUP (ORDER BY UPPER(TRIM(mbti))) AS baseline_value FROM public.profiles_psych p JOIN final_bench fb USING(employee_id)
    UNION ALL
    SELECT 'disc', MODE() WITHIN GROUP (ORDER BY UPPER(TRIM(disc))) FROM public.profiles_psych p JOIN final_bench fb USING(employee_id)
),

-- -----------------------------------------------------------------------------------
-- TAHAP 3: PERHITUNGAN SKOR KECOCOKAN TV (tv_match_rate)
-- Tanggung Jawab: Menghitung skor untuk semua karyawan berdasarkan baseline.
-- -----------------------------------------------------------------------------------
all_numeric_scores AS (
    SELECT employee_id, pillar_code AS tv_name, score::numeric AS user_score FROM public.competencies_yearly JOIN latest l ON competencies_yearly.year = l.comp_year
    UNION ALL SELECT employee_id, 'iq', iq::numeric FROM public.profiles_psych
    UNION ALL SELECT employee_id, 'gtq', gtq::numeric FROM public.profiles_psych
    UNION ALL SELECT employee_id, 'tiki', tiki::numeric FROM public.profiles_psych
    UNION ALL SELECT employee_id, 'faxtor', faxtor::numeric FROM public.profiles_psych
    UNION ALL SELECT employee_id, 'pauli', pauli::numeric FROM public.profiles_psych
),

numeric_tv AS (
    SELECT sc.employee_id, bn.tv_name, (sc.user_score / NULLIF(bn.baseline_score,0)) * 100 AS tv_match_rate
    FROM all_numeric_scores sc JOIN baseline_numeric bn USING(tv_name)
),

papi_tv AS (
    SELECT ps.employee_id, bp.tv_name,
           CASE WHEN bp.is_reverse THEN ((2 * bp.baseline_score - ps.score::numeric) / NULLIF(bp.baseline_score,0)) * 100 ELSE (ps.score::numeric / NULLIF(bp.baseline_score,0)) * 100 END AS tv_match_rate
    FROM public.papi_scores ps JOIN baseline_papi bp ON ps.scale_code = bp.tv_name
),

categorical_tv AS (
    SELECT p.employee_id, bc.tv_name,
           CASE WHEN (bc.tv_name = 'mbti' AND UPPER(TRIM(p.mbti)) = bc.baseline_value) OR (bc.tv_name = 'disc' AND UPPER(TRIM(p.disc)) = bc.baseline_value) THEN 100 ELSE 0 END AS tv_match_rate
    FROM public.profiles_psych p CROSS JOIN baseline_cat bc
),

all_tv AS (
    SELECT employee_id, tv_name, tv_match_rate FROM numeric_tv
    UNION ALL
    SELECT employee_id, tv_name, tv_match_rate FROM papi_tv
    UNION ALL
    SELECT employee_id, tv_name, tv_match_rate FROM categorical_tv
),

-- -----------------------------------------------------------------------------------
-- TAHAP 4: AGREGASI SKOR (TGV & FINAL)
-- Tanggung Jawab: Menggabungkan skor TV menjadi TGV, lalu menjadi skor final.
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
        employee_id,
        SUM(tgv_match_rate * g.tgv_weight) AS final_match_rate
    FROM tgv_match t
    JOIN public.talent_group_weights g USING(tgv_name)
    GROUP BY employee_id
),

-- -----------------------------------------------------------------------------------
-- TAHAP 5: PENYAJIAN HASIL AKHIR
-- Tanggung Jawab: Menggabungkan skor dengan data karyawan dan menerapkan filter.
-- -----------------------------------------------------------------------------------
final_results AS (
    SELECT
        e.employee_id,
        e.fullname,
        pos.name as position_name,
        dep.name as department_name,
        div.name as division_name,
        g.name as grade_name,
        fm.final_match_rate
    FROM final_match fm
    JOIN public.employees e USING(employee_id)
    LEFT JOIN public.dim_positions pos ON e.position_id = pos.position_id
    LEFT JOIN public.dim_departments dep ON e.department_id = dep.department_id
    LEFT JOIN public.dim_divisions div ON e.division_id = div.division_id
    LEFT JOIN public.dim_grades g ON e.grade_id = g.grade_id
)

-- Final SELECT statement
-- Filter tambahan dari UI akan diterapkan di klausa WHERE di sini.
SELECT *
FROM final_results
{filter_clause}  -- Diisi oleh Python: e.g., WHERE department_name = 'IT'
ORDER BY final_match_rate DESC
LIMIT 200;
