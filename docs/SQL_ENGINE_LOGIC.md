# 📘 **SQL_ENGINE_LOGIC.md (Toggle-Ready Version)**

**Talent Matching Engine — SQL Execution Blueprint**
**Versi 3.1 — Toggle-Based Benchmark Architecture**

---

# 1. 🎯 Tujuan Dokumen

Dokumen ini menjelaskan logika resmi untuk membangun SQL query Talent Matching Engine, termasuk:

* Struktur pipeline CTE (tidak boleh diubah)
* Cara baseline dibentuk berdasarkan mode dan toggle
* Aturan penggunaan filter UI
* Kapan SQL dipanggil dan kapan tidak
* Penjelasan detail alur Mode A/B/Default
* Ketentuan ketat yang wajib diikuti Qwen Coder & developer

Dokumen ini adalah dasar bagi `core/matching.py` dan SQL template engine.

---

# 2. 🏛 Prinsip Fundamental Engine (Toggle-Ready)

### 🟩 **Prinsip 1 — Benchmark dibangun hanya dari baseline builder**

Baseline builder = manual_ids (toggle ON) atau filter UI (Mode B).

### 🟩 **Prinsip 2 — Filter UI tidak boleh memfilter hasil akhir**

Tidak boleh ada `WHERE` di final SELECT selain filter bawaan rating (HP selection).

### 🟩 **Prinsip 3 — Mode A toggle OFF tidak menggunakan SQL sama sekali**

Karena output-nya adalah rekomendasi posisi per orang.

### 🟩 **Prinsip 4 — Mode A toggle ON menjadikan manual_ids baseline absolut**

Semua filter B diabaikan dan disabled.

### 🟩 **Prinsip 5 — Mode Default fallback = HP rating ≥ 5**

Jika tidak ada input dari user.

---

# 3. 🧭 Mode Operasi SQL Engine

SQL engine hanya dipanggil pada mode berikut:

| Mode                    | SQL Dipanggil? | Benchmark Group    |
| ----------------------- | -------------- | ------------------ |
| **Mode A (toggle OFF)** | ❌ Tidak        | Tidak ada baseline |
| **Mode A (toggle ON)**  | ✔ Ya           | manual_ids         |
| **Mode B**              | ✔ Ya           | HP via filters     |
| **Default**             | ✔ Ya           | HP ≥ 5             |

---

# 4. 🔧 Blueprint Pipeline CTE (WAJIB DIPERTAHANKAN)

SQL Engine menggunakan pipeline berurutan seperti:

```
params
manual_set
filter_based_set
fallback_benchmark
final_bench
latest
baseline_numeric
baseline_papi
baseline_cat
all_numeric_scores
numeric_tv
papi_tv
categorical_tv
all_tv
tgv_match
final_match
final_results
```

✔ Urutan ini **wajib**
✔ Nama CTE **wajib**
✔ Isi fundamental tidak boleh diganti (kecuali benchmark construction)

---

# 5. 📌 Tahap Benchmark Construction (Toggle-Based)

## 5.1 CTE: params

Berisi semua input UI:

* manual_hp (ARRAY text)
* filter_position_id
* filter_department_id
* filter_division_id
* filter_grade_id
* rating_min (biasanya 5)
* flag_manual_mode
* **flag_use_manual_as_benchmark (toggle)**

Toggle sangat penting untuk membedakan Mode A Benchmark vs Mode A Recommendation.

---

## 5.2 CTE: manual_set

```
SELECT unnest(manual_hp) AS employee_id
```

Jika manual kosong → hasil 0 row.

---

## 5.3 CTE: filter_based_set

Dipakai **hanya jika manual kosong & filter UI aktif**.

```
SELECT DISTINCT e.employee_id
FROM employees e
JOIN performance_yearly py USING(employee_id)
JOIN params p ON TRUE
WHERE py.rating >= p.rating_min
  AND (p.filter_position_id IS NULL OR e.position_id = p.filter_position_id)
  AND (p.filter_department_id IS NULL OR e.department_id = p.filter_department_id)
  AND (p.filter_division_id IS NULL OR e.division_id = p.filter_division_id)
  AND (p.filter_grade_id IS NULL OR e.grade_id = p.filter_grade_id)
```

---

## 5.4 CTE: fallback_benchmark

Jika **manual kosong** dan **filter kosong**, maka:

```
SELECT employee_id
FROM performance_yearly
WHERE rating >= 5
```

---

## 5.5 CTE: final_bench (Aturan Kunci Toggle)

Aturan final benchmark:

```
Jika flag_use_manual_as_benchmark = TRUE:
        final_bench = manual_set
Else jika manual kosong dan filter aktif:
        final_bench = filter_based_set
Else jika tidak ada input sama sekali:
        final_bench = fallback_benchmark
```

Implementasi SQL:

```
SELECT DISTINCT employee_id
FROM manual_set
WHERE (SELECT use_manual_as_benchmark FROM params)

UNION

SELECT DISTINCT employee_id
FROM filter_based_set
WHERE NOT (SELECT use_manual_as_benchmark FROM params)
  AND (SELECT manual_hp IS NULL OR cardinality(manual_hp) = 0)

UNION

SELECT DISTINCT employee_id
FROM fallback_benchmark
WHERE cardinality(manual_hp) = 0
  AND filter_based_set empty
```

---

# 6. 📊 Tahap Baseline Calculation

(BERSIFAT WAJIB DAN TIDAK BOLEH DIUBAH)

## 6.1 baseline_numeric

Menggunakan median:

```
PERCENTILE_CONT(0.5)
```

## 6.2 baseline_papi

Median + reverse logic untuk PAPI I, K, Z, T.

## 6.3 baseline_cat

Menggunakan mode:

```
MODE() WITHIN GROUP
```

---

# 7. 🧬 Tahap Match Rate Calculation

## numeric_tv

```
(user_score / baseline_score) * 100
```

## papi_tv

```
((2 * baseline_score - user_score) / baseline_score) * 100
```

## categorical_tv

```
match → 100
not match → 0
```

---

# 8. 🔗 Tahap Agregasi

## TGV aggregations

```
SUM(tv_match_rate * tv_weight) / SUM(tv_weight)
```

## Final score

```
SUM(tgv_match_rate * tgv_weight)
```

---

# 9. 🏁 Final SELECT (Tidak Ada Filter)

**ATURAN SUPER KETAT:**

> **Final SELECT tidak boleh memiliki filter apapun.**
> Semua filter UI adalah benchmark builder, bukan hasil filter.

Final SELECT wajib:

```
SELECT
    e.employee_id,
    e.fullname,
    pos.name AS position_name,
    dep.name AS department_name,
    div.name AS division_name,
    g.name AS grade_name,
    years_of_service_months / 12.0 AS experience_years,
    final_match_rate
FROM final_match fm
JOIN employees e USING(employee_id)
LEFT JOIN dim_positions pos USING(position_id)
LEFT JOIN dim_departments dep USING(department_id)
LEFT JOIN dim_divisions div USING(division_id)
LEFT JOIN dim_grades g USING(grade_id)
ORDER BY final_match_rate DESC
```

---

# 10. 🧪 Integrasi Dengan Python (Core Logic)

Python menjalankan:

```
if manual_ids:
    if toggle ON:
        # Mode A Benchmark
        df = run_standard_match_query(manual_ids_for_benchmark=manual_ids)
    else:
        # Mode A Recommendation
        df = get_match_for_single_person()
else:
    if filters_B:
        # Mode B
        df = run_standard_match_query(filters=filters_B)
    else:
        # Default Mode
        df = run_standard_match_query()
```

Filter B otomatis disabled ketika manual_ids ada.

---

# 11. ❌ Larangan dalam SQL Engine

SQL Engine **tidak boleh** melakukan:

* ❌ filtering kandidat pada final SELECT
* ❌ benchmark bercampur filter dan manual
* ❌ skip fallback baseline
* ❌ skip median/mode baseline
* ❌ mengubah urutan CTE
* ❌ menghapus reverse-scoring PAPI
* ❌ menggunakan AVG sebagai baseline

---

# 12. ✔ Kewajiban dalam SQL Engine

* Baseline harus dihitung dari `final_bench`
* Scoring harus dihitung untuk **semua karyawan**
* Benchmark harus selalu minimal 1 orang
* Fallback baseline wajib tersedia
* Output selalu berupa ranking lengkap

---

# 13. 🏁 Penutup

Dokumen ini mendefinisikan blueprint final untuk Talent Matching SQL Engine versi toggle-based.
Segala bentuk refactor, patch, atau perbaikan kode **wajib mengacu** pada dokumen ini.

Jika terjadi pertentangan antara kode dan dokumen ini:
**Dokumen ini adalah referensi tertinggi dan benar.**

---
