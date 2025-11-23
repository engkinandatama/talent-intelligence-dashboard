# 📖 Panduan Algoritma Talent Matching

Dokumen ini menjelaskan secara rinci logika dan metodologi di balik **Talent Matching Engine**. Ini adalah "otak" dari aplikasi dan menjadi dasar untuk semua perhitungan skor kecocokan. Semua kontributor, termasuk AI, harus merujuk ke dokumen ini saat bekerja dengan `core/matching.py`.

## 1. Filosofi Inti: Bukan Pencarian, Tapi Pencocokan

Tujuan utama algoritma ini **bukan untuk memfilter** karyawan berdasarkan kriteria (seperti `department = 'IT'`). Tujuannya adalah untuk **menghitung skor kecocokan (match score)** setiap karyawan terhadap sebuah profil "karyawan teladan" (benchmark).

Skor ini, yang disebut `final_match_rate`, merepresentasikan seberapa "mirip" seorang karyawan dengan profil sukses yang telah didefinisikan.

---

## 2. Struktur Algoritma: Model Pembobotan Hierarkis 3 Tingkat

Algoritma ini menggunakan model penilaian hierarkis yang terdiri dari 3 level perhitungan.

### **Level 3: `final_match_rate` (Skor Akhir)**
Ini adalah skor paling atas yang dilihat pengguna.

- **Rumus:** Rata-rata tertimbang (*weighted average*) dari semua skor TGV (Talent Group Variable).
- **Formula Matematis:**
  `Final Match Rate = Σ (Skor TGV * Bobot TGV)`
- **Implementasi:**
  - Skor TGV (`tgv_match_rate`) dihitung di level sebelumnya.
  - Bobot TGV (`tgv_weight`) diambil dari tabel `public.talent_group_weights`.
  - Perhitungan ini terjadi di CTE `final_match` dalam query SQL.

### **Level 2: `tgv_match_rate` (Skor Grup Talenta)**
Setiap TGV (misalnya, "Cognitive Ability", "Workstyle", "Competency") memiliki skornya sendiri.

- **Rumus:** Rata-rata tertimbang (*weighted average*) dari semua skor TV (Talent Variable) yang termasuk dalam grup tersebut.
- **Formula Matematis:**
  `Skor TGV = Σ (Skor TV * Bobot TV) / Σ (Bobot TV)`
- **Implementasi:**
  - Skor TV (`tv_match_rate`) dihitung di level paling dasar.
  - Bobot TV (`tv_weight`) dan pemetaan TV ke TGV diambil dari tabel `public.talent_variables_mapping`.
  - Perhitungan ini terjadi di CTE `tgv_match` dalam query SQL.

### **Level 1: `tv_match_rate` (Skor Variabel Individual)**
Ini adalah fondasi dari semua perhitungan, di mana skor setiap karyawan untuk satu variabel spesifik (misalnya, skor IQ, skor kompetensi FTC) dibandingkan dengan **skor baseline**.

- **Definisi Skor Baseline:** Skor baseline adalah **median (persentil ke-50)** dari skor karyawan yang termasuk dalam **set benchmark**. Ini merepresentasikan "skor ideal" dari seorang *high performer*.

Ada 3 jenis rumus di level ini:

#### **1. Logika Numerik Standar**
- **Untuk Variabel:** Kompetensi, skor kognitif (IQ, GTQ, Pauli), dan skor PAPI yang bersifat positif (semakin tinggi semakin baik).
- **Rumus:** `Match Rate = (Skor Karyawan / Skor Baseline) * 100`
- **Tujuan:** Mengukur seberapa dekat skor karyawan dengan skor ideal. Skor di atas 100 berarti melebihi ekspektasi.

#### **2. Logika Numerik Terbalik (Inverse Scoring)**
- **Untuk Variabel:** Skor PAPI yang bersifat negatif (semakin rendah semakin baik), seperti kecenderungan untuk impulsif atau terlalu agresif.
- **Variabel Spesifik:** `Papi_I`, `Papi_K`, `Papi_Z`, `Papi_T`.
- **Rumus:** `Match Rate = ((2 * Skor Baseline - Skor Karyawan) / Skor Baseline) * 100`
- **Tujuan:** Memberikan skor tinggi kepada karyawan yang memiliki skor rendah pada sifat-sifat yang tidak diinginkan ini.

#### **3. Logika Kategorikal (Boolean Match)**
- **Untuk Variabel:** Data kualitatif seperti tipe kepribadian.
- **Variabel Spesifik:** `mbti`, `disc`.
- **Rumus:**
  - `Match Rate = 100` jika tipe karyawan sama dengan tipe yang paling umum (*mode*) di antara set benchmark.
  - `Match Rate = 0` jika berbeda.
- **Tujuan:** Memberikan skor biner untuk kecocokan tipe.

---

## 3. Konsep Kunci: Definisi "Benchmark"

Algoritma ini sangat bergantung pada siapa yang dianggap sebagai "benchmark". Aplikasi ini mendukung dua mode utama untuk mendefinisikan benchmark:

- **Mode A (Manual):** Pengguna memilih 1 atau lebih `employee_id` secara manual.
- **Mode B (Berdasarkan Posisi):** Pengguna memilih sebuah `position_id`. Sistem secara otomatis akan mengambil semua karyawan di posisi tersebut yang memiliki `rating` di atas ambang batas (misalnya, `rating >= 5`).

**Logika Gabungan:**
- Jika pengguna memilih Mode A dan B, set benchmark adalah **gabungan (UNION)** dari kedua grup tersebut.
- **Fallback:** Jika tidak ada benchmark yang dipilih, sistem akan secara default menggunakan semua karyawan di perusahaan dengan `rating` di atas ambang batas sebagai benchmark.

---

## 4. Alur Eksekusi Query SQL (`run_match_query`)

Fungsi ini harus mengikuti alur berikut:

1.  **Membangun Set Benchmark:** Membuat CTE `final_bench` yang berisi daftar `employee_id` yang menjadi tolak ukur.
2.  **Menghitung Baseline:** Membuat CTE `baseline_numeric`, `baseline_papi`, dan `baseline_cat` untuk menghitung skor median (atau mode) dari set benchmark untuk setiap TV.
3.  **Menghitung Skor TV:** Membuat CTE `numeric_tv`, `papi_tv`, dan `categorical_tv` untuk menghitung `tv_match_rate` bagi **semua karyawan** dengan membandingkannya dengan skor baseline.
4.  **Menggabungkan Skor TV:** Menggunakan `UNION ALL` untuk menggabungkan semua skor TV ke dalam satu CTE besar (`all_tv`).
5.  **Menghitung Skor TGV:** Menggunakan `GROUP BY` dan `JOIN` dengan tabel `talent_variables_mapping` untuk menghitung `tgv_match_rate`.
6.  **Menghitung Skor Final:** Menggunakan `GROUP BY` dan `JOIN` dengan tabel `talent_group_weights` untuk menghitung `final_match_rate`.
7.  **Menyajikan Hasil:** Menggabungkan hasil akhir dengan tabel `employees` dan `dim_` untuk menampilkan informasi lengkap, menerapkan filter kandidat (jika ada), dan mengurutkannya.

Dengan mengikuti panduan ini, AI akan mengerti bahwa setiap permintaan modifikasi kode harus selaras dengan arsitektur algoritma yang kompleks ini, bukan sekadar membuat query `SELECT` biasa.
