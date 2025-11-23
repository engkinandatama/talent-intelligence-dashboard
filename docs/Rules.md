```markdown
# 📜 Panduan Kode, Keamanan, dan Praktik Terbaik
## Proyek: Talent Match Intelligence Dashboard

Dokumen ini adalah "Konstitusi" atau seperangkat aturan yang **wajib** diikuti dalam seluruh siklus pengembangan proyek "Talent Match Intelligence Dashboard". Tujuannya adalah untuk membangun aplikasi yang aman, andal, mudah dikelola, dan berkualitas enterprise. Semua kontributor, baik manusia maupun AI (seperti Qwen Code CLI), harus mematuhi panduan ini tanpa kecuali.

---

## 🏛️ Bagian 1: Aturan Keamanan & Kredensial (Prioritas Tertinggi)

Keamanan adalah aspek non-negotiable. Kelalaian dalam hal ini dapat menyebabkan kebocoran data dan kegagalan proyek.

### **Rule 1.1: Kredensial Tidak Boleh Ada di Dalam Kode (Zero Hardcoding)**
- **Larangan Keras:** *Password*, *API key*, *token*, *connection string*, atau informasi sensitif lainnya **TIDAK BOLEH** ditulis secara langsung (hardcoded) di dalam file kode sumber (`.py`, `.sql`, `.ipynb`).
- **Contoh Pelanggaran (DILARANG):**
  ```python
  # DILARANG KERAS - Ini adalah pelanggaran keamanan serius.
  DB_URL = "postgresql://postgres:MySuperSecretPassword@db.host.com:5432/postgres"
  engine = create_engine(DB_URL)
  ```
- **Praktik yang Benar:** Semua kredensial **HARUS** dimuat dari file `.streamlit/secrets.toml` yang tidak dilacak oleh Git. Gunakan `st.secrets` untuk mengaksesnya.
- **Contoh Benar:**
  ```python
  # BENAR - Kredensial dimuat dari lingkungan yang aman.
  db_url = st.secrets["DB_URL"]
  engine = create_engine(db_url)
  ```

### **Rule 1.2: Isolasi File `secrets.toml` dari Kontrol Versi**
- File `.streamlit/secrets.toml` **WAJIB** dimasukkan ke dalam file `.gitignore` di direktori utama proyek.
- Ini adalah lapisan pertahanan untuk memastikan kredensial pengembangan lokal tidak sengaja ter-commit dan terekspos di repositori publik seperti GitHub.
- **Isi `.gitignore` (minimal):**
  ```
  # Abaikan file kredensial Streamlit
  .streamlit/secrets.toml

  # Abaikan virtual environment
  venv/
  ```

### **Rule 1.3: Validasi dan Sanitasi Input Pengguna Secara Ketat**
- **Prinsip Utama:** **"Never Trust User Input."** Semua data yang berasal dari luar aplikasi (input pengguna, parameter URL, data dari API eksternal) harus dianggap tidak aman.
- **SQL Injection:** Selalu gunakan **parameterized queries** (query berparameter) saat berinteraksi dengan database. **JANGAN PERNAH** menggunakan f-string atau konkatenasi string untuk memasukkan nilai ke dalam query SQL.
  - **Contoh Benar (Aman):**
    ```python
    # Menggunakan placeholder :name
    sql = "SELECT * FROM employees WHERE fullname ILIKE :name"
    df = pd.read_sql(text(sql), conn, params={"name": f"%{search_term}%"})
    ```
  - **Contoh Salah (Sangat Berbahaya):**
    ```python
    # DILARANG - Rentan terhadap SQL Injection.
    sql = f"SELECT * FROM employees WHERE fullname ILIKE '%{search_term}%'"
    df = pd.read_sql(sql, conn)
    ```
- **Prompt Injection:** Saat berinteraksi dengan LLM, sanitasi input pengguna untuk mencegah instruksi berbahaya yang dapat membajak prompt.

### **Rule 1.4: Penanganan Error yang Informatif namun Aman**
- **Untuk Pengguna:** Jangan pernah menampilkan detail error teknis (seperti *stack trace* lengkap, pesan error database, atau isi variabel) di antarmuka pengguna. Ini dapat membocorkan informasi tentang struktur internal aplikasi.
- **Praktik yang Benar:**
  1.  Gunakan blok `try...except Exception as e:`.
  2.  Jika terjadi error, tampilkan pesan yang umum dan ramah pengguna (contoh: "Oops! Terjadi kesalahan. Silakan coba lagi nanti.").
  3.  Untuk keperluan *debugging*, catat (*log*) detail error lengkap ke konsol terminal atau file log di *backend*. Gunakan `st.exception(e)` hanya selama fase pengembangan lokal.

---

## 🏗️ Bagian 2: Aturan Arsitektur & Struktur Kode

Struktur yang baik adalah kunci untuk aplikasi yang dapat tumbuh dan dikelola.

### **Rule 2.1: Pemisahan Tanggung Jawab yang Jelas (Separation of Concerns)**
- **`pages/`**: Folder ini **HANYA** berisi kode yang mengatur **tampilan (UI)** dan **interaksi pengguna (UX)** untuk setiap halaman. File di sini tidak boleh berisi logika bisnis yang kompleks atau query SQL mentah. Tugas utamanya adalah memanggil fungsi dari `core` dan menampilkan hasilnya.
- **`core/`**: Folder ini adalah **"otak"** aplikasi. Semua logika inti berada di sini.
  - `db.py`: Bertanggung jawab tunggal untuk membuat dan mengelola koneksi database (`get_engine`).
  - `matching.py`: Berisi semua logika dan query SQL untuk algoritma *talent matching*.
  - `profiling.py`: Berisi logika untuk mengambil dan memproses data untuk halaman profil detail karyawan.
  - `ai_generator.py`: Berisi semua interaksi dengan LLM, termasuk *prompt engineering*.
- **`components/`**: Berisi fungsi-fungsi untuk membuat komponen UI yang dapat digunakan kembali di berbagai halaman (misalnya, `render_metric_card()`, `create_radar_chart()`).
- **`assets/`**: Berisi file statis seperti CSS, gambar, dan font.

### **Rule 2.2: Alur Impor yang Tegas untuk Mencegah Impor Sirkular**
- **Aturan Hirarki:**
    - `pages/` dapat mengimpor dari `core/` dan `components/`.
    - `core/` dapat mengimpor modul lain di dalam `core/` (misal: `matching.py` mengimpor `db.py`).
    - `core/` **TIDAK BOLEH** mengimpor apa pun dari `pages/` atau `components/`.
    - `components/` idealnya bersifat mandiri dan tidak mengimpor dari `core/` atau `pages/`. Ia menerima data sebagai argumen fungsi.

### **Rule 2.3: Fungsional dan Modular**
- Hindari penulisan logika kompleks di level global file. Bungkus semua logika ke dalam fungsi-fungsi yang jelas, memiliki satu tanggung jawab (Single Responsibility Principle), dan mudah diuji.
- Gunakan nama fungsi yang deskriptif (e.g., `load_active_employees` lebih baik daripada `get_data`).

---

## 🎨 Bagian 3: Aturan Gaya Penulisan Kode (Code Style)

Konsistensi membuat kode lebih mudah dibaca dan dipahami oleh semua orang.

### **Rule 3.1: Penamaan yang Jelas dan Konsisten (PEP 8)**
- **Variabel & Fungsi:** Gunakan `snake_case` (e.g., `final_match_rate`, `run_match_query`).
- **Konstanta:** Gunakan `UPPER_SNAKE_CASE` (e.g., `MIN_RATING_THRESHOLD`).
- **Nama File:** Gunakan `snake_case` (e.g., `talent_matching.py`).
- **Boolean:** Gunakan nama yang menjawab pertanyaan ya/tidak (e.g., `is_benchmark`, `has_filters`).

### **Rule 3.2: Dokumentasi adalah Kewajiban**
- Setiap fungsi **HARUS** memiliki *docstring* yang menjelaskan:
    1.  Apa tujuan fungsi tersebut (satu kalimat singkat).
    2.  Argumen yang diterima (`Parameters`).
    3.  Apa yang dikembalikannya (`Returns`).
- Gunakan komentar `#` untuk menjelaskan baris kode yang rumit, non-intuitif, atau memiliki alasan bisnis tertentu.

### **Rule 3.3: Jaga Kebersihan Kode**
- Hapus kode yang tidak digunakan (kode yang di-komentar, fungsi lama, variabel sisa).
- Gunakan *formatter* kode otomatis seperti **Black** atau **Ruff** untuk menjaga konsistensi format di seluruh proyek.

---

> Dokumen ini adalah hukum tertinggi dalam proyek ini. Setiap perubahan atau penambahan aturan harus didiskusikan dan disetujui. Dengan mematuhi panduan ini, kita memastikan produk akhir yang kita bangun tidak hanya fungsional, tetapi juga berkualitas tinggi, aman, dan profesional.
```