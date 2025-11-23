# Project Overview: Talent Match Intelligence Dashboard (Ultimate Edition)

## 1. Visi & Tujuan Utama Aplikasi

Aplikasi ini adalah sebuah **Platform Intelijen Talenta (Talent Intelligence Platform)** yang komprehensif, dibangun menggunakan Streamlit dengan arsitektur modular. Tujuannya adalah menyediakan alat bantu strategis bagi para pemimpin dan manajer HR untuk semua siklus manajemen talenta internal, mulai dari perencanaan peran hingga penempatan dan pengembangan karyawan.

**Fungsi Inti Platform:**
1.  **Perencanaan Peran (Role Planning):** Membantu mendefinisikan peran dan kebutuhan kompetensi menggunakan bantuan AI.
2.  **Pencocokan Talenta (Talent Matching):** Menemukan dan me-ranking talenta internal yang paling cocok untuk sebuah peran.
3.  **Eksplorasi Talenta (Talent Exploration):** Menyediakan database karyawan yang mudah dicari dan dianalisis.
4.  **Analisis Mendalam (Deep Dive Analysis):** Menawarkan profil 360 derajat dari setiap karyawan.
5.  **Wawasan Strategis (Strategic Insights):** Memberikan gambaran umum tentang kekuatan dan kelemahan talenta di seluruh organisasi.

---

## 2. Arsitektur & Struktur Halaman (9 Modul Utama)

Aplikasi ini akan terdiri dari 9 modul utama, yang diimplementasikan sebagai halaman terpisah dalam aplikasi multi-halaman Streamlit.

### **Modul 1: `Home Dashboard` (Halaman Utama)**
- **Tujuan:** Memberikan pandangan "mata burung" (bird's-eye view) tentang kondisi talenta organisasi.
- **Fitur:**
    -   Kartu metrik utama (Total Karyawan, Rata-rata Kinerja, Jumlah High Performer).
    -   Grafik distribusi rating kinerja dan sebaran kompetensi.
    -   Pintasan cepat ke modul-modul lain.

### **Modul 2: `Job Role Generator (AI)`**
- **Tujuan:** Mengotomatiskan pembuatan profil pekerjaan (Job Profile).
- **Fitur:**
    -   Form input untuk `Role Name` dan `Job Level`.
    -   Tombol "Generate with AI" yang memanggil LLM.
    -   AI akan menghasilkan: Tujuan Peran, Tanggung Jawab Utama, Kualifikasi, dan Kompetensi Inti.
    -   Hasil dapat disimpan atau di-copy.

### **Modul 3: `Talent Matching Engine` (Mesin Pencocokan)**
- **Tujuan:** **MODUL INTI.** Menjalankan algoritma untuk me-ranking kandidat berdasarkan skor kecocokan.
- **Fitur:**
    -   Panel **Benchmark** (Mode A: Manual, Mode B: Berdasarkan Posisi).
    -   Panel **Filter Kandidat** (opsional, untuk menyaring hasil akhir).
    -   Tombol "Jalankan Talent Match".
    -   Tabel hasil peringkat berdasarkan `final_match_rate`.

### **Modul 4: `Employee Explorer` (Eksplorasi Karyawan)**
- **Tujuan:** Menyediakan antarmuka seperti HRIS untuk mencari dan memfilter semua karyawan.
- **Fitur:**
    -   Panel filter lengkap (posisi, departemen, divisi, dll.).
    -   Tabel besar dengan **pagination** untuk menampilkan ribuan data.
    -   Setiap nama karyawan adalah **hyperlink** ke halaman profil detail.

### **Modul 5: `Employee Detail Page` (Profil Detail Karyawan)**
- **Tujuan:** Menampilkan profil 360 derajat dari satu karyawan.
- **Akses:** Halaman dinamis yang diakses melalui hyperlink dari modul lain (URL dengan parameter `?employee_id=...`).
- **Konten:**
    -   Info pribadi dan posisi.
    -   Grafik tren kinerja.
    -   **Radar Chart** kompetensi.
    -   "Kartu Statistik" untuk data psikometri (IQ, MBTI, DISC).
    -   Daftar kekuatan (CliftonStrengths).

### **Modul 6: `Role Benchmarking` (Analisis Peran)**
- **Tujuan:** Membandingkan profil ideal sebuah peran dengan kandidat potensial.
- **Fitur:**
    -   Pilih sebuah peran yang sudah didefinisikan.
    -   Sistem menampilkan profil kompetensi dan perilaku ideal untuk peran tersebut.
    -   Membandingkan beberapa kandidat secara berdampingan (side-by-side) dengan profil ideal.
    -   Menampilkan **analisis kesenjangan (gap analysis)**.

### **Modul 7: `Insights & Analytics` (Dasbor Analitik)**
- **Tujuan:** Memberikan wawasan strategis dari data agregat.
- **Fitur:**
    -   **Heatmap** kompetensi di seluruh departemen.
    -   Distribusi tipe kepribadian (MBTI/DISC) di seluruh perusahaan.
    -   Analisis korelasi antara masa kerja, rating, dan skor kompetensi.

### **Modul 8: `Settings / Admin` (Pengaturan)**
- **Tujuan:** Mengelola konfigurasi aplikasi.
- **Fitur:**
    -   Mengubah bobot TGV dan TV untuk algoritma matching.
    -   Mengelola koneksi database.
    -   Pengaturan tema (Light/Dark mode).

### **Modul 9: `Authentication` (Otentikasi)**
- **Tujuan:** Membatasi akses hanya untuk pengguna yang berwenang.
- **Fitur:**
    -   Halaman login sederhana (misalnya, menggunakan kata sandi tunggal atau daftar pengguna yang diizinkan).
    -   Ini adalah lapisan keamanan dasar, bukan sistem RBAC (Role-Based Access Control) yang kompleks.

---

## 3. Logika Inti di Balik Layar (`core/matching.py`)

Logika `run_match_query` tetap menjadi pusat dari aplikasi ini. Fungsi ini akan dipanggil terutama oleh **Modul 3 (Talent Matching Engine)** dan **Modul 6 (Role Benchmarking)**. Logikanya tetap sama: membangun satu query SQL besar untuk menghitung `final_match_rate` berdasarkan sistem pembobotan hierarkis 3 tingkat (TV -> TGV -> Final Score).

1.  **`params`**: Mengambil input dari UI (benchmark manual, posisi target, rating min).
2.  **`final_bench`**: Menentukan set `employee_id` yang akan menjadi benchmark.
3.  **`baseline_numeric`, `baseline_papi`, `baseline_cat`**: Menghitung **skor baseline (median)** untuk setiap variabel (TV) dari karyawan di dalam `final_bench`.
4.  **`numeric_tv`, `papi_tv`, `categorical_tv`**: Menghitung **`tv_match_rate`** untuk setiap karyawan di seluruh perusahaan dengan membandingkan skor mereka dengan skor baseline. Di sinilah logika *inverse scoring* dan *boolean match* diterapkan.
5.  **`all_tv`**: Menggabungkan semua hasil `tv_match_rate` menjadi satu tabel besar.
6.  **`tgv_match`**: Melakukan agregasi (rata-rata tertimbang) dari `tv_match_rate` menjadi `tgv_match_rate` berdasarkan bobot di tabel `talent_variables_mapping`.
7.  **`final_match`**: Melakukan agregasi akhir dari `tgv_match_rate` menjadi `final_match_rate` berdasarkan bobot di tabel `talent_group_weights`.
8.  **Query Terakhir**: Menggabungkan hasil `final_match` dengan tabel `employees` dan `dim_` lainnya untuk menampilkan informasi lengkap, lalu menerapkan filter kandidat (jika ada), dan mengurutkannya berdasarkan `final_match_rate` tertinggi.

**Penting:** Filter kandidat (departemen, nama, dll.) diterapkan di **klausa `WHERE` paling akhir**, setelah semua skor `final_match_rate` dihitung. Filter ini tidak boleh mempengaruhi perhitungan benchmark atau baseline.