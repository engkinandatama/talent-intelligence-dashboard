# Skema Database Supabase (PostgreSQL)

Berikut adalah struktur lengkap dari semua tabel yang digunakan dalam proyek ini.

### Tabel Utama (Facts)

- **`employees`**: Menyimpan data master karyawan. `employee_id` adalah `text`.
- **`performance_yearly`**: Menyimpan data rating kinerja tahunan.
- **`competencies_yearly`**: Menyimpan skor 10 pilar kompetensi tahunan.
- **`profiles_psych`**: Menyimpan data hasil tes psikometri (IQ, GTQ, MBTI, DISC, dll).
- **`papi_scores`**: Menyimpan 20 skor preferensi kerja PAPI Kostick.
- **`strengths`**: Menyimpan data 5 kekuatan teratas dari CliftonStrengths.

### Tabel Dimensi (Dimensions)

- `dim_companies`
- `dim_areas`
- `dim_positions`
- `dim_departments`
- `dim_divisions`
- `dim_directorates`
- `dim_grades`
- `dim_education`
- `dim_majors`
- `dim_competency_pillars`

### Tabel Konfigurasi Matching Engine

- **`talent_variables_mapping`**: Menyimpan pemetaan dan bobot dari setiap TV ke TGV-nya.
- **`talent_group_weights`**: Menyimpan bobot untuk setiap TGV dalam perhitungan skor final.

---

*Catatan: Skema `CREATE TABLE` lengkap ada di file terpisah jika diperlukan.*


### ini SQL-scheme dari supabase yang aku copy
-- WARNING: This schema is for context only and is not meant to be run.
-- Table order and constraints may not be valid for execution.

CREATE TABLE public.competencies_yearly (
  employee_id text NOT NULL,
  pillar_code character varying NOT NULL,
  year integer NOT NULL,
  score integer,
  CONSTRAINT competencies_yearly_pkey PRIMARY KEY (employee_id, pillar_code, year),
  CONSTRAINT competencies_yearly_employee_id_fkey FOREIGN KEY (employee_id) REFERENCES public.employees(employee_id),
  CONSTRAINT competencies_yearly_pillar_code_fkey FOREIGN KEY (pillar_code) REFERENCES public.dim_competency_pillars(pillar_code)
);
CREATE TABLE public.dim_areas (
  area_id integer NOT NULL DEFAULT nextval('dim_areas_area_id_seq'::regclass),
  name text NOT NULL,
  CONSTRAINT dim_areas_pkey PRIMARY KEY (area_id)
);
CREATE TABLE public.dim_companies (
  company_id integer NOT NULL DEFAULT nextval('dim_companies_company_id_seq'::regclass),
  name text NOT NULL,
  CONSTRAINT dim_companies_pkey PRIMARY KEY (company_id)
);
CREATE TABLE public.dim_competency_pillars (
  pillar_code character varying NOT NULL,
  pillar_label text NOT NULL,
  CONSTRAINT dim_competency_pillars_pkey PRIMARY KEY (pillar_code)
);
CREATE TABLE public.dim_departments (
  department_id integer NOT NULL DEFAULT nextval('dim_departments_department_id_seq'::regclass),
  name text NOT NULL,
  CONSTRAINT dim_departments_pkey PRIMARY KEY (department_id)
);
CREATE TABLE public.dim_directorates (
  directorate_id integer NOT NULL DEFAULT nextval('dim_directorates_directorate_id_seq'::regclass),
  name text NOT NULL,
  CONSTRAINT dim_directorates_pkey PRIMARY KEY (directorate_id)
);
CREATE TABLE public.dim_divisions (
  division_id integer NOT NULL DEFAULT nextval('dim_divisions_division_id_seq'::regclass),
  name text NOT NULL,
  CONSTRAINT dim_divisions_pkey PRIMARY KEY (division_id)
);
CREATE TABLE public.dim_education (
  education_id integer NOT NULL DEFAULT nextval('dim_education_education_id_seq'::regclass),
  name text NOT NULL,
  CONSTRAINT dim_education_pkey PRIMARY KEY (education_id)
);
CREATE TABLE public.dim_grades (
  grade_id integer NOT NULL DEFAULT nextval('dim_grades_grade_id_seq'::regclass),
  name text NOT NULL,
  CONSTRAINT dim_grades_pkey PRIMARY KEY (grade_id)
);
CREATE TABLE public.dim_majors (
  major_id integer NOT NULL DEFAULT nextval('dim_majors_major_id_seq'::regclass),
  name text NOT NULL,
  CONSTRAINT dim_majors_pkey PRIMARY KEY (major_id)
);
CREATE TABLE public.dim_positions (
  position_id integer NOT NULL DEFAULT nextval('dim_positions_position_id_seq'::regclass),
  name text NOT NULL,
  CONSTRAINT dim_positions_pkey PRIMARY KEY (position_id)
);
CREATE TABLE public.employees (
  employee_id text NOT NULL,
  fullname text,
  nip text,
  company_id integer,
  area_id integer,
  position_id integer,
  department_id integer,
  division_id integer,
  directorate_id integer,
  grade_id integer,
  education_id integer,
  major_id integer,
  years_of_service_months integer,
  CONSTRAINT employees_pkey PRIMARY KEY (employee_id),
  CONSTRAINT employees_company_id_fkey FOREIGN KEY (company_id) REFERENCES public.dim_companies(company_id),
  CONSTRAINT employees_area_id_fkey FOREIGN KEY (area_id) REFERENCES public.dim_areas(area_id),
  CONSTRAINT employees_position_id_fkey FOREIGN KEY (position_id) REFERENCES public.dim_positions(position_id),
  CONSTRAINT employees_department_id_fkey FOREIGN KEY (department_id) REFERENCES public.dim_departments(department_id),
  CONSTRAINT employees_division_id_fkey FOREIGN KEY (division_id) REFERENCES public.dim_divisions(division_id),
  CONSTRAINT employees_directorate_id_fkey FOREIGN KEY (directorate_id) REFERENCES public.dim_directorates(directorate_id),
  CONSTRAINT employees_grade_id_fkey FOREIGN KEY (grade_id) REFERENCES public.dim_grades(grade_id),
  CONSTRAINT employees_education_id_fkey FOREIGN KEY (education_id) REFERENCES public.dim_education(education_id),
  CONSTRAINT employees_major_id_fkey FOREIGN KEY (major_id) REFERENCES public.dim_majors(major_id)
);
CREATE TABLE public.papi_scores (
  employee_id text NOT NULL,
  scale_code text NOT NULL,
  score integer,
  CONSTRAINT papi_scores_pkey PRIMARY KEY (employee_id, scale_code),
  CONSTRAINT papi_scores_employee_id_fkey FOREIGN KEY (employee_id) REFERENCES public.employees(employee_id)
);
CREATE TABLE public.performance_yearly (
  employee_id text NOT NULL,
  year integer NOT NULL,
  rating integer,
  CONSTRAINT performance_yearly_pkey PRIMARY KEY (employee_id, year),
  CONSTRAINT performance_yearly_employee_id_fkey FOREIGN KEY (employee_id) REFERENCES public.employees(employee_id)
);
CREATE TABLE public.profiles_psych (
  employee_id text NOT NULL,
  pauli numeric,
  faxtor numeric,
  disc text,
  disc_word text,
  mbti text,
  iq numeric,
  gtq integer,
  tiki integer,
  CONSTRAINT profiles_psych_pkey PRIMARY KEY (employee_id),
  CONSTRAINT profiles_psych_employee_id_fkey FOREIGN KEY (employee_id) REFERENCES public.employees(employee_id)
);
CREATE TABLE public.strengths (
  employee_id text NOT NULL,
  rank integer NOT NULL,
  theme text,
  CONSTRAINT strengths_pkey PRIMARY KEY (employee_id, rank),
  CONSTRAINT strengths_employee_id_fkey FOREIGN KEY (employee_id) REFERENCES public.employees(employee_id)
);
CREATE TABLE public.talent_benchmarks (
  benchmark_id integer NOT NULL DEFAULT nextval('talent_benchmarks_benchmark_id_seq'::regclass),
  employee_id text,
  CONSTRAINT talent_benchmarks_pkey PRIMARY KEY (benchmark_id),
  CONSTRAINT talent_benchmarks_employee_id_fkey FOREIGN KEY (employee_id) REFERENCES public.employees(employee_id)
);
CREATE TABLE public.talent_group_weights (
  tgv_name text NOT NULL,
  tgv_weight numeric,
  CONSTRAINT talent_group_weights_pkey PRIMARY KEY (tgv_name)
);
CREATE TABLE public.talent_match_results (
  run_id uuid,
  employee_id text,
  final_match_rate numeric,
  created_at timestamp without time zone DEFAULT now(),
  CONSTRAINT talent_match_results_employee_id_fkey FOREIGN KEY (employee_id) REFERENCES public.employees(employee_id)
);
CREATE TABLE public.talent_variables_mapping (
  tv_name text NOT NULL,
  tgv_name text,
  tv_weight numeric,
  CONSTRAINT talent_variables_mapping_pkey PRIMARY KEY (tv_name)
);