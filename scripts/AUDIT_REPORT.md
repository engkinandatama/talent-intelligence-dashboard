# AUDIT REPORT: Year Filtering Issues Across Codebase
# Generated: 2025-11-26

## CRITICAL ISSUES FOUND:

### 1. core/matching.py (CRITICAL - Matching Engine Core)
**Lines 47-56 (filter_based_set):**
```sql
SELECT DISTINCT e.employee_id
FROM public.employees e
JOIN public.performance_yearly py USING(employee_id)
WHERE py.rating = p.min_hp_rating  -- ❌ NO YEAR FILTER
```

**Lines 61-65 (fallback_benchmark):**
```sql
SELECT py.employee_id
FROM public.performance_yearly py
WHERE py.rating = p.min_hp_rating  -- ❌ NO YEAR FILTER
```

**Impact:** Matching engine uses HP from ALL YEARS (735 = 36.6%) instead of LATEST YEAR (168 = 8.4%)

**Fix Required:** Add `AND py.year = (SELECT MAX(year) FROM performance_yearly)`

---

### 2. core/matching_breakdown.py (HIGH PRIORITY - Breakdown Analysis)
**Lines 51-54 (benchmark_employees):**
```sql
SELECT py.employee_id
FROM performance_yearly py
WHERE py.rating = 5
  AND NOT {use_custom_benchmark}  -- ❌ NO YEAR FILTER
```

**Line 344 (benchmark_n calculation):**
```sql
SELECT COUNT(DISTINCT employee_id) FROM performance_yearly WHERE rating = 5  -- ❌ NO YEAR FILTER
```

**Lines 243-246 (TGV weights - HARDCODED!):**
```python
CASE
    WHEN tgv_name = 'COGNITIVE' THEN 0.30  # ❌ Should be 0.10
    WHEN tgv_name = 'COMPETENCY' THEN 0.35  # ❌ Should be 0.50
    WHEN tgv_name = 'WORK_STYLE' THEN 0.20  # ❌ Should be 0.25
    ELSE 0.15
END AS tgv_weight
```

**Impact:** Detailed breakdown uses wrong benchmark AND wrong TGV weights!

**Fix Required:** 
1. Add year filter to benchmark selection
2. Fetch weights from `talent_group_weights` table instead of hardcoding

---

### 3. pages/3_Employee_Profile.py (MEDIUM PRIORITY - Display Only)
**Lines 256-260 (Performance display):**
```sql
SELECT rating
FROM performance_yearly
WHERE employee_id = %s
ORDER BY year DESC
LIMIT 1
```

**Status:** ✅ Actually CORRECT - uses LIMIT 1 with ORDER BY year DESC to get latest

---

### 4. app.py (FIXED)
✅ Already fixed in previous updates

---

## SUMMARY:
- **Files with Issues:** 2 critical (matching.py, matching_breakdown.py)
- **Total Issues:** 4 year filtering bugs + 1 hardcoded weights issue
- **Estimated Impact:** ALL matching results since dashboard launch are using wrong benchmark (36.6% vs 8.4%)
