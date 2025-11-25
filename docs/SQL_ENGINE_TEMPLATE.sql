-- ===================================================================================
-- GOLDEN TEMPLATE: TALENT MATCHING ENGINE (TOGGLE-READY)
-- ===================================================================================
-- Project : Talent Match Intelligence Dashboard
-- Version : 3.1 (Benchmark-Driven + Manual Benchmark Toggle)
--
-- CORE RULES:
-- 1. CTE STRUCTURE & ORDER MUST NOT BE CHANGED.
-- 2. CORE LOGIC (PERCENTILE_CONT, MODE, MATCHING FORMULAS) MUST NOT BE ALTERED.
-- 3. MODIFICATIONS ONLY ALLOWED IN PARAMETER SECTIONS.
-- 4. NO CANDIDATE FILTERING IN FINAL SELECT (ALL FILTERS = BENCHMARK BUILDER).
-- 5. PARAMETER VALUES `{...}` WILL BE DYNAMICALLY FILLED BY PYTHON.
-- ===================================================================================

WITH
-- -----------------------------------------------------------------------------------
-- STAGE 1: PARAMETERS & BENCHMARK BUILDER
-- -----------------------------------------------------------------------------------
params AS (
    SELECT
        -- Filled by Python (ARRAY['EMP001','EMP002']::text[] or ARRAY[]::text[])
        {manual_array_sql}                            AS manual_hp,

        -- BENCHMARK FILTERS (MODE B) - FILLED BY PYTHON (int or NULL)
        {filter_position_id}::int                     AS filter_position_id,
        {filter_department_id}::int                   AS filter_department_id,
        {filter_division_id}::int                     AS filter_division_id,
        {filter_grade_id}::int                        AS filter_grade_id,

        -- MINIMUM RATING FOR HIGH PERFORMER (usually 5)
        {min_rating}::int                             AS min_hp_rating,

        -- TOGGLE: USE MANUAL_ID AS BENCHMARK?
        -- TRUE  = Mode A (Manual Benchmark)
        -- FALSE = Mode B / Default (Manual empty)
        {use_manual_as_benchmark}::boolean            AS use_manual_as_benchmark
),

-- Manual Benchmark Set (Mode A with toggle ON)
manual_set AS (
    SELECT unnest(p.manual_hp) AS employee_id
    FROM params p
),

-- Filter-Based Benchmark Set (Mode B)
filter_based_set AS (
    SELECT DISTINCT e.employee_id
    FROM public.employees e
    JOIN public.performance_yearly py USING(employee_id)
    JOIN params p ON TRUE
    WHERE py.rating >= p.min_hp_rating
      AND (p.filter_position_id   IS NULL OR e.position_id   = p.filter_position_id)
      AND (p.filter_department_id IS NULL OR e.department_id = p.filter_department_id)
      AND (p.filter_division_id   IS NULL OR e.division_id   = p.filter_division_id)
      AND (p.filter_grade_id      IS NULL OR e.grade_id      = p.filter_grade_id)
),

-- Fallback Benchmark (Default Mode)
fallback_benchmark AS (
    SELECT py.employee_id
    FROM public.performance_yearly py
    JOIN params p ON TRUE
    WHERE py.rating >= p.min_hp_rating
),

-- FINAL BENCHMARK GROUP (final_bench)
-- Logic:
--   1) IF use_manual_as_benchmark = TRUE AND manual_hp not empty:
--        final_bench = manual_set
--   2) IF manual empty & filters yield data:
--        final_bench = filter_based_set
--   3) IF no input at all:
--        final_bench = fallback_benchmark
final_bench AS (
    -- Case 1: Manual Benchmark (Mode A - Toggle ON)
    SELECT ms.employee_id
    FROM manual_set ms
    JOIN params p ON TRUE
    WHERE p.use_manual_as_benchmark

    UNION

    -- Case 2: Filter Benchmark (Mode B) - Only if NOT using manual
    SELECT fb.employee_id
    FROM filter_based_set fb
    JOIN params p ON TRUE
    WHERE NOT p.use_manual_as_benchmark
      AND NOT EXISTS (SELECT 1 FROM manual_set)

    UNION

    -- Case 3: Fallback Benchmark (Default Mode)
    SELECT fb2.employee_id
    FROM fallback_benchmark fb2
    JOIN params p ON TRUE
    WHERE NOT p.use_manual_as_benchmark
      AND NOT EXISTS (SELECT 1 FROM manual_set)
      AND NOT EXISTS (SELECT 1 FROM filter_based_set)
),

-- -----------------------------------------------------------------------------------
-- STAGE 2: BASELINE SCORE CALCULATION
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
-- STAGE 3: TV MATCH RATE CALCULATION FOR ALL EMPLOYEES
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
-- STAGE 4: TGV AGGREGATION & FINAL SCORE
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
-- STAGE 5: FINAL OUTPUT FORMATTING
-- -----------------------------------------------------------------------------------
final_results AS (
    SELECT
        e.employee_id,
        e.fullname,
        pos.name AS position_name,
        dep.name AS department_name,
        div.name AS division_name,
        dir.name AS directorate_name, -- Added Directorate
        g.name AS grade_name,
        ROUND(e.years_of_service_months / 12.0, 1) AS experience_years,
        ROUND(fm.final_match_rate, 2) AS final_match_rate
    FROM final_match fm
    JOIN public.employees e ON fm.employee_id = e.employee_id
    LEFT JOIN public.dim_positions pos ON e.position_id = pos.position_id
    LEFT JOIN public.dim_departments dep ON e.department_id = dep.department_id
    LEFT JOIN public.dim_divisions div ON e.division_id = div.division_id
    LEFT JOIN public.dim_directorates dir ON e.directorate_id = dir.directorate_id -- Assumed Join
    LEFT JOIN public.dim_grades g ON e.grade_id = g.grade_id
)

SELECT * FROM final_results
ORDER BY final_match_rate DESC
LIMIT 200;
