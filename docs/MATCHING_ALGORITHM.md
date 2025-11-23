# 📘 **MATCHING_ALGORITHM.md (Toggle-Ready Version)**

**Talent Matching Engine — Matching Algorithm Specification**
**Versi 3.1 — Benchmark-Driven Architecture + Manual Benchmark Toggle**

---

# 1. 🎯 Tujuan Dokumen

Dokumen ini mendefinisikan **logika resmi** algoritma Talent Matching Engine yang digunakan untuk menghitung:

* baseline score
* tv_match_rate
* tgv_match_rate
* final_match_rate
* mode operasi engine (Mode A/B/Default) dengan Benchmark Toggle

Dokumen ini merupakan **sumber kebenaran utama (single source of truth)** bagi semua implementasi:

* UI logic
* Python logic
* SQL engine
* Qwen Coder refactor

Semua kode **harus mengikuti** dokumen ini.

---

# 2. 🧠 Konsep Fundamental: Benchmark = “Profil Karyawan Ideal”

Talent Matching Engine menggunakan konsep:

> **“Semua skor karyawan dihitung berdasarkan ideal baseline group (benchmark group).”**

Benchmark group adalah **sekumpulan karyawan berkinerja tinggi** yang dipilih berdasarkan input user.

Dengan benchmark ini, engine menghitung:

* skor median kompetensi
* skor median kognitif
* skor mode kepribadian

Untuk menghasilkan baseline ideal, lalu membandingkannya dengan seluruh karyawan.

---

# 3. 🌙 Mode Operasi Engine (Dengan Benchmark Toggle)

Engine sekarang mendukung **tiga mode resmi** dan bekerja dengan *satu boolean baru*:
**`use_manual_as_benchmark (toggle)`**

Berikut mode-mode final:

---

## 🟦 **Mode A — Manual Selection (Toggle OFF)**

**Tujuan:**

> Menghasilkan **rekomendasi posisi** untuk satu/multiple karyawan tertentu.

**Kondisi UI:**

* manual_ids terisi
* toggle = OFF
* filter B nonaktif (disabled)

**Benchmark:** Tidak digunakan
**Fungsi SQL:** Tidak digunakan

**Output:**

* Untuk setiap employee_id → tampilkan ranking posisi terbaik
* Menggunakan fungsi:

  ```
  get_match_for_single_person(employee_id)
  ```

---

## 🟩 **Mode A — Manual Benchmark (Toggle ON)**

**Tujuan:**

> Menjadikan manual_ids sebagai benchmark ideal dan menampilkan ranking semua karyawan.

**Kondisi UI:**

* manual_ids terisi
* toggle = ON
* filter B nonaktif (disabled)

**Benchmark:**

```
final_bench = manual_ids
```

**SQL digunakan:**

```
run_standard_match_query(manual_ids_for_benchmark = manual_ids)
```

**Output:**
Ranking seluruh karyawan berdasarkan kesesuaian terhadap baseline manual.

---

## 🟧 **Mode B — Filter-Based Benchmark**

**Tujuan:**

> Menentukan benchmark group berdasarkan filter kriteria high performer.

**Kondisi UI:**

* manual_ids kosong
* toggle irrelevant
* filter B aktif (posisi, departemen, divisi, grade, dll.)

**Benchmark builder:**

```
final_bench = high performers (rating>=5) yang memenuhi semua filter B
```

**Output:**
Ranking seluruh karyawan berdasarkan baseline yang dihasilkan filter B.

---

## ⚫ **Default Mode**

**Kondisi UI:**

* manual_ids kosong
* filter B kosong
* toggle irrelevant

**Benchmark builder:**

```
final_bench = semua high performer rating >= 5
```

**Output:**
Ranking seluruh karyawan menggunakan baseline default.

---

# 4. 🧱 Blueprint Mode Table

| Mode                                 | manual_ids | toggle | filter B | Benchmark       | Output                       |
| ------------------------------------ | ---------- | ------ | -------- | --------------- | ---------------------------- |
| **Mode A – Position Recommendation** | ✔ ada      | OFF    | disabled | none            | rekomendasi posisi per orang |
| **Mode A – Manual Benchmark**        | ✔ ada      | ON     | disabled | manual_ids      | ranking seluruh karyawan     |
| **Mode B – Filter Benchmark**        | kosong     | OFF    | aktif    | HP via filter B | ranking seluruh karyawan     |
| **Default Mode**                     | kosong     | OFF    | kosong   | HP rating=5     | ranking seluruh karyawan     |

---

# 5. 🧩 Struktur Skoring (Hierarki 3 Level)

Scoring engine masih sama seperti versi sebelumnya.
Tidak ada perubahan pada rumus inti.

## 🟪 Level 1 — tv_match_rate

Bandingkan skor masing-masing variabel (TV) dengan baseline ideal.

### (A) Variabel Numerik Normal

Contoh: Kompetensi, IQ, GTQ, Pauli

```
tv_match_rate = (user_score / baseline_score) * 100
```

### (B) Variabel Numerik Terbalik (Reverse Scoring)

Contoh: PAPI I, K, Z, T

```
tv_match_rate = ((2 * baseline_score - user_score) / baseline_score) * 100
```

### (C) Variabel Kategorikal (MBTI, DISC)

```
match   → 100  
not match → 0
```

---

## 🟥 Level 2 — tgv_match_rate (Weighted Average)

Menggunakan `talent_variables_mapping`.

```
tgv_match_rate = SUM(tv_match_rate * tv_weight) / SUM(tv_weight)
```

---

## 🟦 Level 3 — final_match_rate (Weighted Sum)

Menggunakan `talent_group_weights`.

```
final_match_rate = SUM(tgv_match_rate * tgv_weight)
```

---

# 6. 🧬 Definisi Benchmark Final

Urutan penentuan benchmark:

### 1. Jika **manual_ids** dan **toggle ON**

→ final_bench = manual_ids (Mode A Benchmark)

### 2. Else jika filter B aktif

→ final_bench = HP rating>=5 yang cocok filter B (Mode B Benchmark)

### 3. Else (no inputs)

→ final_bench = HP rating>=5 (Default Benchmark)

---

# 7. 🔗 Hubungan Dengan SQL Engine

Matching algorithm ini diimplementasikan oleh SQL engine dengan pipeline CTE:

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

Aturan penting:

### ✔ SQL engine hanya dipanggil pada Mode A Benchmark, Mode B, dan Default

### ✔ SQL engine tidak dipanggil pada Mode A Recommendation

### ✔ Tidak ada filter kandidat dalam SQL final SELECT

---

# 8. 📌 Aturan Teknis yang Tidak Boleh Dilanggar

### ❌ 1. Tidak ada “Mode A+B” lagi

Sudah sepenuhnya digantikan toggle.

### ❌ 2. Filter B tidak boleh aktif atau digunakan ketika manual_ids ada

Toggle menjamin ini.

### ❌ 3. SQL final SELECT tidak boleh mengandung filter apapun

Sort/filter output dilakukan di Streamlit saja.

### ✔ 4. Baseline harus selalu berasal dari final_bench

Tidak boleh dari tempat lain.

### ✔ 5. Fallback baseline (HP rating>=5) wajib ada

Untuk memastikan baseline tidak kosong.

---

# 9. 🏁 Penutup

Dokumen ini menetapkan **desain final** algoritma Talent Matching Engine versi terbaru berbasis toggle-ready architecture.
Semua implementasi dan refactor di Python & SQL harus selaras dengan dokumen ini.

Jika terdapat perbedaan antara kode dan dokumen ini:
**Dokumen ini adalah referensi yang benar.**

---