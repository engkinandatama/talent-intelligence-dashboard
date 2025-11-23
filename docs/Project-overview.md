# 📘 **Project Overview — Talent Match Intelligence Dashboard**

**Versi 3.1 — Benchmark-Driven Architecture (Toggle-Ready Edition)**

---

# 1. 🎯 Visi & Tujuan Utama

Talent Match Intelligence Dashboard adalah sebuah **Platform Intelijen Talenta internal** yang dirancang untuk:

* Mengidentifikasi talenta terbaik dalam organisasi
* Membandingkan karyawan dengan profil *high performer* ideal
* Menghasilkan rekomendasi posisi optimal
* Mempercepat proses talent review & succession planning
* Menstandarkan keputusan HR berbasis data

Aplikasi ini dibangun dengan arsitektur modular menggunakan **Streamlit**, **PostgreSQL**, dan **SQL-based Talent Matching Engine**.

---

# 2. 🏗 Arsitektur Utama Aplikasi

Aplikasi terdiri dari 9 modul utama, yang saling terintegrasi namun tetap modular:

---

## **1. Home Dashboard**

Menampilkan metrik utama organisasi:

* Jumlah karyawan
* Distribusi rating
* Distribusi kompetensi
* Insight singkat kondisi talenta

---

## **2. Job Role Generator (AI-Assisted)**

Menghasilkan profil pekerjaan otomatis menggunakan LLM:

* Role purpose
* Key responsibilities
* Qualification
* Required competencies
* Dapat disimpan ke database

---

## **3. Talent Matching Engine (Inti Sistem)**

**Modul paling penting.**

Fungsi:

* Menjalankan algoritma *Talent Matching* terhadap seluruh karyawan
* Menghasilkan ranking kandidat berdasarkan **final_match_rate**
* Membangun benchmark otomatis dengan pendekatan **toggle-based baseline logic**

### Mode Operasi Engine:

| Mode                                              | Kapan digunakan?               | Output                                            |
| ------------------------------------------------- | ------------------------------ | ------------------------------------------------- |
| **Mode A — Position Recommendation** (toggle OFF) | User memilih manual_ids        | Rekomendasi posisi untuk orang tersebut           |
| **Mode A — Manual Benchmark** (toggle ON)         | User memilih manual_ids        | Ranking seluruh karyawan terhadap baseline manual |
| **Mode B — Filter Benchmark**                     | Manual kosong, filter UI aktif | Ranking seluruh karyawan terhadap baseline filter |
| **Default Mode**                                  | Tidak ada input                | Baseline = HP rating≥5, ranking seluruh karyawan  |

---

## **4. Employee Explorer**

Seperti mini-HRIS internal:

* Cari karyawan berdasarkan banyak kriteria
* Tabel interaktif dengan sorting & filtering
* Hyperlink ke detail profile

---

## **5. Employee Profile (360° View)**

Profil mendalam untuk setiap karyawan:

* Informasi personal & organisasi
* Grafik tren kinerja
* Radar chart kompetensi
* IQ, GTQ, MBTI, DISC
* CliftonStrengths
* Riwayat jabatan (jika tersedia)

---

## **6. Role Benchmarking**

Bandingkan peran terhadap beberapa kandidat:

* Profile ideal role
* Gap analysis per kandidat
* Radar chart perbandingan
* Insight kekuatan & kelemahan

---

## **7. Insights & Analytics**

Analisis makro organisasi:

* Heatmap kompetensi
* Distribusi kepribadian
* Analisis korelasi rating–masa kerja–kompetensi
* Strength clusters per departemen

---

## **8. Settings / Admin**

Konfigurasi dan pengaturan:

* Bobot TGV / TV
* Pengaturan koneksi database
* Theme mode (light/dark)

---

## **9. Authentication**

Layer otentikasi sederhana:

* Login berbasis password
* Proteksi halaman sensitif

---

# 3. 🧠 Arsitektur Logika Talent Matching (versi Toggle-Ready)

Aplikasi ini menggunakan **model matematika 3-level hierarkis**:

### **Level 1 — Talent Variable Match Rate (TV)**

Dihitung dari baseline:

* numeric → `(user_score / baseline_score) * 100`
* reverse numeric → `((2 * baseline_score - user_score)/baseline_score)*100`
* categorical → `100 if match else 0`

---

### **Level 2 — Talent Group Variable (TGV)**

Weighted average:

```
SUM(tv_match_rate * tv_weight) / SUM(tv_weight)
```

---

### **Level 3 — Final Match Rate**

Weighted sum:

```
SUM(tgv_match_rate * tgv_weight)
```

---

# 4. 🌐 Arsitektur Benchmark-Driven (Versi Toggle)

### **Mode A — toggle OFF**

Tidak menggunakan SQL engine.
Engine memakai fungsi alternatif:

```
get_match_for_single_person()
```

Menampilkan rekomendasi posisi untuk orang tersebut.

---

### **Mode A — toggle ON**

Benchmark = manual_ids
Filter B otomatis nonaktif.

---

### **Mode B**

Filter B aktif → benchmark dibangun dari high performer sesuai filter.

---

### **Default Mode**

Baseline = HP rating ≥ 5.

---

# 5. 🧩 SQL Engine Pipeline (CTE-Based)

SQL engine menggunakan pipeline 18 tahap (CTE berurutan):

1. params
2. manual_set
3. filter_based_set
4. fallback_benchmark
5. final_bench
6. latest
7. baseline_numeric
8. baseline_papi
9. baseline_cat
10. all_numeric_scores
11. numeric_tv
12. papi_tv
13. categorical_tv
14. all_tv
15. tgv_match
16. final_match
17. final_results
18. final SELECT (tanpa filter)

**Tidak ada filter tampilan pada final SELECT — filtering hanya di UI Streamlit.**

---

# 6. 🗃 Struktur Database Utama

* **employees** → data master
* **performance_yearly** → rating tahunan
* **competencies_yearly** → kompetensi pilar
* **profiles_psych** → IQ, GTQ, MBTI, DISC
* **papi_scores** → 20 skala PAPI
* **strengths** → CliftonStrengths
* **dim_*** → tabel dimensi organisasi
* **talent_variables_mapping** → bobot TV → TGV
* **talent_group_weights** → bobot TGV → final score

---

# 7. 🔌 Integrasi Backend (core/)

* `core/db.py` → koneksi database
* `core/matching.py` → pusat logika matching
* `core/job_generator.py` → save job vacancy
* `core/profiling.py` → load profil 360°

Matching engine bekerja berdasarkan:

* UI input (manual_ids, toggle, filter B)
* SQL template toggle-ready
* Panduan MATCHING_ALGORITHM & SQL_ENGINE_LOGIC

---

# 8. 🖼 UI & UX (pages/)

* Modularisasi per halaman
* Form input sederhana & UX ramah HR
* Table interaktif (sort, filter, export)
* Toggle benchmark untuk Mode A
* Filter B di-disable otomatis jika manual aktif

---

# 9. 🔐 Keamanan & Praktik Terbaik

* Semua kredensial hanya di `.streamlit/secrets.toml`
* Tidak ada hardcoding password
* Tidak ada SQL injection → gunakan parameter binding
* Error message harus aman (no stack trace)
* Hanya user terotorisasi bisa mengakses dashboard

---

# 10. 📦 Status Arsitektur Terbaru

Versi toggle-ready telah menghilangkan ambiguitas Mode A+B dan menyederhanakan UI:

### ✔ manual_ids aktif → filter B disabled

### ✔ toggle OFF → rekomendasi posisi

### ✔ toggle ON → manual benchmark

### ✔ manual kosong → filter B aktif (Mode B)

### ✔ filter B kosong → Default Mode

Fully aligned dengan MATCHING_ALGORITHM.md v3.1 dan SQL_ENGINE_LOGIC.md v3.1.

---

# 11. 🏁 Penutup

Dokumen ini memberikan overview lengkap tentang struktur arsitektur aplikasi, mode kerja engine, pipeline SQL, dan interaksi UI x backend.
Semua pengembangan baru harus mengikuti versi arsitektur toggle-ready ini.

Jika terdapat konflik antara kode dan dokumentasi:
**Dokumen ini adalah dasar kebenaran.**

---
