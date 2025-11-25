# 📝 Case Study Brief — Data Analyst 2025 (rev 1.1)

## **Focus**

* Success Pattern Discovery
* SQL Logic Design
* AI-Powered Talent Matching
* Business Storytelling

---

# **Overview**

Company X sedang mengembangkan sistem **Talent Match Intelligence** untuk membantu para leader mengidentifikasi faktor apa yang membuat karyawan dengan performa tinggi sukses, serta menemukan individu lain yang memiliki karakteristik serupa untuk kebutuhan succession.

Dalam case ini, Anda akan mensimulasikan workflow analisis data nyata di balik sistem tersebut.

Anda akan:

1. **Menemukan faktor yang mendorong employee success.**
2. **Membentuk Success Formula** yang jelas dan dapat dijelaskan.
3. **Menerjemahkan logika tersebut ke SQL** untuk menghitung match score.
4. **Menyajikan hasil melalui aplikasi AI + dashboard** yang menghasilkan job profile dan visual insight.

> ⚠️ **Catatan Penting:**
> Dalam dunia nyata, Anda jarang mulai dengan pengetahuan lengkap. Case study ini dirancang untuk menguji kemampuan Anda dalam belajar, eksplorasi, dan adaptasi. Jika Anda tidak memiliki latar belakang HR/psikologi, Anda **diwajibkan** melakukan riset sendiri.

---

# **Dataset & ERD**

Anda akan menggunakan dataset **Study Case DA**, **Glossary Data**, dan ERD yang disediakan.

### **Tools Required**

| Category               | Tool / Platform                  | Notes                                            |
| ---------------------- | -------------------------------- | ------------------------------------------------ |
| Database               | Supabase (Postgres)              | Data storage, query, SQL logic                   |
| Programming & Analysis | Python / R / SQL                 | Analisis, query, formula exploration             |
| Visualization & App    | Streamlit / enterprise dashboard | Dashboard insight + visual job vacancy           |
| AI Model               | OpenRouter / free LLM            | Job requirements, descriptions, competency lists |
| Version Control        | GitHub                           | Script + documentation                           |
| Report Format          | PDF Case Study Report            | Mengikuti template                               |

---

# **Case Study Flow — The Red Thread**

---

# **Step 1 — Discover the Pattern of Success**

Tujuan pertama: **mengidentifikasi mengapa sebagian karyawan mendapatkan rating 5**, sementara lainnya tidak.

### Anda harus melakukan eksplorasi across:

* **Competency pillars**
  (`competencies_yearly` + `dim_competency_pillars`)
* **Psychometric profiles**
  (`papi_scores`, `profiles_psych`)
* **Behavioral data**
  (`strengths`)
* **Contextual factors**
  (grade, years_of_service_months, education, dan lainnya)

Gunakan visual storytelling:

* Heatmaps
* Radar charts
* Correlation plots
* Comparison matrices

**Tujuan:** menjelaskan *why*, bukan sekadar *what*.

---

## **Success Formula**

Anda harus menyintesis temuan menjadi sebuah **Success Formula** yang memiliki struktur bobot yang dapat dijelaskan.

> Catatan: contoh seperti
> `SuccessScore = 0.3*Cognitive + 0.2*Leadership + …`
> adalah **terlalu sederhana**.

Tantangan sebenarnya adalah menyeimbangkan banyak variabel yang saling berinteraksi.

Pada tahap ini, Anda **diperbolehkan** membuat formula berbasis rule-based logic.

### **Deliverable Step 1**

* Final Success Formula + justifikasi
* Analisis pendukung dan visual

---

# **Understanding TGV & TV**

### **Talent Group Variables (TGV)**

Kategori besar skill atau perilaku yang mempengaruhi performa.
Contoh: Leadership, Cognitive Ability, Personality, Teamwork, Technical Expertise.

### **Talent Variables (TV)**

Komponen terukur yang berada di dalam masing-masing TGV.
Contoh:

* **Cognitive** → IQ, Numerical Reasoning, Problem Solving
* **Leadership** → Strategic Thinking, Accountability

Setiap TV berkontribusi terhadap TGV-nya.

Dalam SQL Anda harus:

1. **Membandingkan masing-masing TV** kandidat vs benchmark → TV match rate
2. **Mengemudi TGV match rate** → rata-rata/berbobot dari TV dalam TGV tersebut
3. **Menggabungkan semua TGV ke Final Match Rate**

Ringkas:

* **TV = variabel terukur**
* **TGV = grup dari beberapa TV**

---

# **Step 2 — Operationalize the Logic in SQL**

Manager memilih satu atau lebih **benchmark** (employee rating = 5) untuk mendefinisikan profil ideal sebuah role.

SQL Anda harus menghitung tingkat kemiripan setiap employee terhadap benchmark tersebut.

Bobot dapat:

* equal weighting
* custom weighting pada level TV maupun TGV

---

## **Matching Algorithm**

Gunakan modular CTE.

### **1. Baseline Aggregation**

Untuk setiap TV → hitung baseline benchmark (median dari skor talent terpilih).

### **2. TV Match Rate**

#### **Numeric**

* Rumus standar:
  `match = user_score / benchmark_score * 100`
* Jika direction = *lower is better*:
  `((2 * benchmark_score – user_score) / benchmark_score) * 100`

#### **Categorical**

* exact match = **100%**
* mismatch = **0%**

---

### **3. TGV Match Rate**

* rata-rata TV match
* atau memakai custom weighting

---

### **4. Final Match Rate**

* weighted average dari seluruh TGV
* gunakan weights_config jika ada

---

## **Expected SQL Output Columns**

| Column           | Meaning                    |
| ---------------- | -------------------------- |
| employee_id      | Candidate ID               |
| directorate      | Directorate                |
| role             | Position title             |
| grade            | Grade / level              |
| tgv_name         | Talent Group Variable      |
| tv_name          | Talent Variable            |
| baseline_score   | Benchmark TV score         |
| user_score       | Candidate TV score         |
| tv_match_rate    | Match TV (%)               |
| tgv_match_rate   | Avg/weighted match per TGV |
| final_match_rate | Overall weighted match     |

---

# **Step 3 — Build the AI Talent App & Dashboard**

Aplikasi harus **dinamis** dan mampu menangani input baru **tanpa mengubah kode**.

### **Runtime Inputs**

* Role name
* Job level
* Role purpose
* Selected benchmark employee IDs

Ketika user submit:

1. Buat/parameterize **job_vacancy_id** dalam `talent_benchmarks`
2. Hitung ulang baseline dari selected benchmark
3. Re-run SQL parameterized
4. Regenerasi profile + ranking + visuals

---

## **Outputs**

### **1. AI-Generated Job Profile**

Menghasilkan:

* job requirements
* description
* key competencies

(dengan LLM apa pun—OpenRouter direkomendasikan)

### **2. Ranked Talent List**

Menampilkan minimal:

* employee_id
* name
* final_match_rate
* strengths / gaps per TGV & TV

### **3. Dashboard Visualization**

Visual interaktif yang mencakup:

* distribusi match rate
* top strengths/gaps
* benchmark vs candidate comparisons
* summary insights

> Dashboard harus membuat stakeholder *mengerti datanya*, bukan memamerkan UI.

---

# **Example**

Termasuk contoh tampilan halaman role information, job details, output tabel employee ranking. (lihat halaman 5–7 dokumen asli).

---

# **Skill Expectations (Job Requirements Section)**

* SQL: complex joins, window functions, CTEs, performance tuning basics
* R/Python: pandas/dplyr, statistics, prototyping (Streamlit/Shiny/Dash)
* BI tools: Looker, Power BI, Tableau
* Data modeling: star schema, metrics layer, version control
* Visualization + storytelling
* Analytical thinking
* Bias awareness
* Communication (English & Bahasa)

---

# **Glossary (Assessment Context)**

### **PAPI Kostick**

* Work-style preferences
* Data: `papi_scores` (1–9)
* Beberapa scale inverse (perhatikan Z/K inversions)

### **MBTI**

* 4 dichotomies
* Data: `profiles_psych.mbti`
* Perlu clean 16 valid types

### **DISC**

* Dominance, Influence, Steadiness, Conscientiousness
* Banyak varian format text
* Berguna untuk narrative fit

### **IQ / Cognitive Index**

* Data: `profiles_psych.iq`
* Range ~80–140

### **GTQ**

* 5 subtests (1–10)

### **TIKI**

* short attention/processing tests (1–10)

### **Pauli**

* continuous arithmetic task

### **Faxtor**

* internal composite (20–100)

### **CliftonStrengths**

* Top 14 themes
* Data: `strengths` (rank 1–14)

---

# **Data Dictionary (Ringkas)**

Dokumen mencantumkan:

### **1) Core Dimensions**

* `dim_companies`
* `dim_areas`
* `dim_positions`
* `dim_departments`
* `dim_divisions`
* `dim_directorates`
* `dim_grades`
* `dim_education`
* `dim_majors`
* `dim_competency_pillars`

### **2) Core Entities / Facts**

* `employees`
* `profiles_psych`
* `papi_scores`
* `strengths`
* `performance_yearly`
* `competencies_yearly`
* `employee_archetypes`

(Tabel-tabel lengkap dengan kolom dan PK/FK persis seperti file.)

---

# **Submission Package**

Anda harus mengirim **Case Study Report (PDF)** dengan struktur berikut:

## **1. Candidate Information**

* Full Name
* Email
* Repository link (⚠️ tidak boleh pakai kata "Rakamin")
* Repo harus berisi:

  * SQL scripts
  * App code + dashboard
  * README.md
  * Supporting assets

## **2. Main Report**

### A. Executive Summary

* overview
* objectives
* outcomes
* impact

### B. Success Pattern Discovery (Deliverable #1)

* proses analisis
* temuan
* insights
* visuals
* Final Success Formula + rationale

### C. SQL Logic & Algorithm (Deliverable #2)

* penjelasan pendekatan SQL
* struktur query & CTE
* snapshot output table

### D. AI App & Dashboard Overview

* deployment link
* input/output AI
* key visualizations
* screenshots

### E. Conclusion

* reflections
* challenges
* improvement ideas

### F. Additional Files

* notebooks
* visuals
* documentation
