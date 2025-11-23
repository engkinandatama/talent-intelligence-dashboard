# 📜 Spesifikasi Teknis & Blue Print SQL Talent Matching Engine

Dokumen ini adalah spesifikasi teknis yang **mengikat** untuk query SQL utama yang digunakan dalam `core/matching.py`. Tujuannya adalah untuk mendokumentasikan struktur, alur, dan justifikasi dari setiap *Common Table Expression* (CTE). Semua modifikasi pada query ini **HARUS** menghormati struktur yang telah ditetapkan di sini. **DILARANG KERAS** mengganti keseluruhan query ini dengan logika yang lebih sederhana seperti `SELECT ... WHERE`.

## Arsitektur Query: Pipeline Berbasis CTE

Query ini dirancang sebagai sebuah *pipeline* data yang mengalir dari satu CTE ke CTE berikutnya. Setiap CTE memiliki satu tanggung jawab spesifik. Mengubah urutan atau logika dasar dari CTE ini akan merusak keseluruhan algoritma.

---

### **Tahap 1: Penentuan Benchmark (Input & Seleksi)**

#### **CTE: `params`**
- **Tanggung Jawab:** Menangkap semua input dari antarmuka pengguna (UI) ke dalam satu tempat yang terisolasi.
- **Isi:** `manual_hp` (array ID karyawan), `role_position_id` (ID posisi), `min_hp_rating` (ambang batas rating).
- **Aturan:** Ini adalah satu-satunya bagian dari query yang nilainya diubah secara dinamis oleh Python menggunakan f-string.

#### **CTE: `manual_set`, `role_set`, `benchmark_set`, `fallback_benchmark`**
- **Tanggung Jawab:** Menggabungkan input dari `params` untuk membuat satu set `employee_id` yang akan menjadi benchmark.
- **Logika:** Menggunakan `UNION` untuk menggabungkan hasil dari Mode A (manual) dan Mode B (berdasarkan posisi). Menyediakan mekanisme *fallback* jika tidak ada benchmark yang dipilih.
- **Aturan:** Struktur `UNION` ini tidak boleh diubah.

#### **CTE: `final_bench`**
- **Tanggung Jawab:** Menghasilkan daftar `employee_id` final yang bersih dan unik untuk digunakan sebagai benchmark di seluruh query.
- **Output:** Satu kolom (`employee_id`) yang menjadi dasar untuk semua perhitungan baseline.

---

### **Tahap 2: Perhitungan Skor Baseline (Tolak Ukur)**

#### **CTE: `latest`**
- **Tanggung Jawab:** Menemukan tahun terbaru dari data kompetensi untuk memastikan kita hanya menggunakan data yang relevan.

#### **CTE: `baseline_numeric`, `baseline_papi`, `baseline_cat`**
- **Tanggung Jawab:** Menghitung **skor baseline** untuk setiap *Talent Variable* (TV).
- **Logika:**
    - `baseline_numeric` & `baseline_papi`: Menggunakan `PERCENTILE_CONT(0.5)` untuk menghitung **median** dari skor karyawan di dalam `final_bench`.
    - `baseline_cat`: Menggunakan `MODE()` untuk menemukan nilai kategorikal yang paling sering muncul (misalnya, tipe MBTI) di antara `final_bench`.
- **Aturan:** Metode agregasi (`PERCENTILE_CONT` dan `MODE`) ini adalah inti dari definisi "baseline" dan tidak boleh diganti dengan `AVG()` atau `MAX()` tanpa alasan yang sangat kuat.

---

### **Tahap 3: Perhitungan Skor Kecocokan TV (`tv_match_rate`)**

#### **CTE: `numeric_tv`, `papi_tv`, `categorical_tv`**
- **Tanggung Jawab:** Menghitung `tv_match_rate` untuk **SEMUA KARYAWAN** dengan membandingkan skor mereka dengan skor baseline yang dihitung di Tahap 2.
- **Logika:**
    - `numeric_tv`: Menerapkan rumus `(user_score / baseline_score) * 100`.
    - `papi_tv`: Menggunakan `CASE WHEN` untuk menerapkan logika **inverse scoring** pada skala PAPI tertentu (`Papi_I`, `Papi_K`, dll.).
    - `categorical_tv`: Menggunakan `CASE WHEN` untuk menerapkan logika **boolean match** (100 atau 0).
- **Aturan:** Rumus perhitungan di dalam `CASE WHEN` ini adalah implementasi langsung dari `MATCHING_ALGORITHM.md` dan tidak boleh diubah.

#### **CTE: `all_tv`**
- **Tanggung Jawab:** Menggabungkan hasil dari ketiga CTE di atas menjadi satu tabel besar menggunakan `UNION ALL`.
- **Output:** Sebuah tabel panjang yang berisi `employee_id`, `tv_name`, dan `tv_match_rate` untuk semua variabel dari semua karyawan.

---

### **Tahap 4: Agregasi ke Skor TGV dan Skor Final**

#### **CTE: `tgv_match`**
- **Tanggung Jawab:** Melakukan agregasi dari skor TV ke skor TGV.
- **Logika:** Menggunakan `GROUP BY employee_id, tgv_name` dan `JOIN` dengan tabel `talent_variables_mapping` untuk menghitung rata-rata tertimbang (`weighted average`).
- **Aturan:** Rumus `SUM(tv_match_rate * tv_weight) / SUM(tv_weight)` adalah definisi matematis dari skor TGV dan harus dipertahankan.

#### **CTE: `final_match`**
- **Tanggung Jawab:** Melakukan agregasi akhir dari skor TGV ke `final_match_rate`.
- **Logika:** Menggunakan `GROUP BY employee_id` dan `JOIN` dengan tabel `talent_group_weights` untuk menghitung rata-rata tertimbang akhir.
- **Aturan:** Ini adalah langkah kalkulasi terakhir sebelum penyajian data.

---

### **Tahap 5: Penyajian Hasil Akhir**

#### **Query Terakhir (Final `SELECT`)**
- **Tanggung Jawab:** Menggabungkan `final_match_rate` dengan data demografis dari tabel `employees` dan `dim_`, menerapkan filter kandidat (jika ada), dan mengurutkan hasilnya.
- **Logika:**
    - `JOIN` antara `final_match` dan `employees`.
    - Klausa `WHERE` dinamis yang ditambahkan oleh Python untuk memfilter hasil akhir (bukan untuk mengubah perhitungan).
    - `ORDER BY final_match_rate DESC`.
- **Aturan:** Filter tambahan dari UI **HANYA BOLEH** diterapkan di sini, di klausa `WHERE` pada query terakhir. Jangan pernah menambahkan filter di CTE tahap awal karena akan merusak perhitungan baseline.

---

Dengan adanya blue print ini, setiap permintaan modifikasi kepada AI harus spesifik. Contoh:

- **Permintaan yang Baik:** "Berdasarkan `SQL_ENGINE_LOGIC.md`, tambahkan kolom `division_name` dari `dim_divisions` ke dalam `Query Terakhir (Final SELECT)`."
- **Permintaan yang Buruk:** "Buatkan saya query untuk mencari karyawan berdasarkan divisi." (Ini akan memicu AI untuk membuat query baru dari nol).
