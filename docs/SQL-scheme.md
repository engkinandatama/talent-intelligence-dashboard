# Database Schema

## Overview

This document describes the database structure for the Talent Intelligence Dashboard. The schema uses PostgreSQL and follows a star schema design with fact and dimension tables.

## Core Tables

### Fact Tables

**employees**
- Master employee data
- Primary key: `employee_id` (text)
- Contains basic employee information, position, department, grade

**performance_yearly**
- Annual performance ratings
- Links employees to their yearly performance scores

**competencies_yearly**
- Competency scores across 10 pillars
- Tracked annually for each employee

**profiles_psych**
- Psychometric test results
- Includes IQ, GTQ, MBTI, DISC, Pauli scores

**papi_scores**
- PAPI Kostick work preferences (20 scales)
- Measures work style and behavioral tendencies

**strengths**
- CliftonStrengths data
- Top 5 strengths per employee

### Dimension Tables

- `dim_companies` - Company master data
- `dim_areas` - Business areas
- `dim_positions` - Job positions
- `dim_departments` - Departments
- `dim_divisions` - Divisions
- `dim_directorates` - Directorates
- `dim_grades` - Job grades
- `dim_education` - Education levels
- `dim_majors` - Academic majors
- `dim_competency_pillars` - Competency framework definitions

### Configuration Tables

**talent_variables_mapping**
- Maps individual variables (TV) to talent groups (TGV)
- Defines weights for each variable

**talent_group_weights**
- Defines weights for each talent group in final scoring

**job_vacancies** (Optional)
- Stores generated job profiles
- Created by Job Generator feature

---

## Complete SQL Schema

```sql
-- Main fact tables
CREATE TABLE public.employees (
  employee_id text NOT NULL PRIMARY KEY,
  fullname text NOT NULL,
  position_id integer,
  department_id integer,
  division_id integer,
  grade_id integer,
  education_id integer,
  major_id integer,
  -- Additional fields as needed
  CONSTRAINT employees_position_fkey FOREIGN KEY (position_id) REFERENCES dim_positions(position_id),
  CONSTRAINT employees_department_fkey FOREIGN KEY (department_id) REFERENCES dim_departments(department_id),
  CONSTRAINT employees_division_fkey FOREIGN KEY (division_id) REFERENCES dim_divisions(division_id),
  CONSTRAINT employees_grade_fkey FOREIGN KEY (grade_id) REFERENCES dim_grades(grade_id),
  CONSTRAINT employees_education_fkey FOREIGN KEY (education_id) REFERENCES dim_education(education_id)
);

CREATE TABLE public.performance_yearly (
  employee_id text NOT NULL,
  year integer NOT NULL,
  rating integer,
  CONSTRAINT performance_yearly_pkey PRIMARY KEY (employee_id, year),
  CONSTRAINT performance_yearly_employee_fkey FOREIGN KEY (employee_id) REFERENCES employees(employee_id)
);

CREATE TABLE public.competencies_yearly (
  employee_id text NOT NULL,
  pillar_code varchar NOT NULL,
  year integer NOT NULL,
  score integer,
  CONSTRAINT competencies_yearly_pkey PRIMARY KEY (employee_id, pillar_code, year),
  CONSTRAINT competencies_yearly_employee_fkey FOREIGN KEY (employee_id) REFERENCES employees(employee_id),
  CONSTRAINT competencies_yearly_pillar_fkey FOREIGN KEY (pillar_code) REFERENCES dim_competency_pillars(pillar_code)
);

CREATE TABLE public.profiles_psych (
  employee_id text NOT NULL PRIMARY KEY,
  iq integer,
  gtq integer,
  pauli integer,
  mbti text,
  disc text,
  CONSTRAINT profiles_psych_employee_fkey FOREIGN KEY (employee_id) REFERENCES employees(employee_id)
);

CREATE TABLE public.papi_scores (
  employee_id text NOT NULL,
  scale_code varchar NOT NULL,
  score integer,
  CONSTRAINT papi_scores_pkey PRIMARY KEY (employee_id, scale_code),
  CONSTRAINT papi_scores_employee_fkey FOREIGN KEY (employee_id) REFERENCES employees(employee_id)
);

CREATE TABLE public.strengths (
  employee_id text NOT NULL,
  rank integer NOT NULL,
  strength_name text,
  CONSTRAINT strengths_pkey PRIMARY KEY (employee_id, rank),
  CONSTRAINT strengths_employee_fkey FOREIGN KEY (employee_id) REFERENCES employees(employee_id)
);

-- Dimension tables
CREATE TABLE public.dim_positions (
  position_id serial PRIMARY KEY,
  name text NOT NULL
);

CREATE TABLE public.dim_departments (
  department_id serial PRIMARY KEY,
  name text NOT NULL
);

CREATE TABLE public.dim_divisions (
  division_id serial PRIMARY KEY,
  name text NOT NULL
);

CREATE TABLE public.dim_grades (
  grade_id serial PRIMARY KEY,
  name text NOT NULL
);

CREATE TABLE public.dim_education (
  education_id serial PRIMARY KEY,
  name text NOT NULL
);

CREATE TABLE public.dim_competency_pillars (
  pillar_code varchar PRIMARY KEY,
  pillar_label text NOT NULL
);

-- Configuration tables for matching engine
CREATE TABLE public.talent_variables_mapping (
  tv_code varchar PRIMARY KEY,
  tv_name text,
  tgv_code varchar,
  tgv_name text,
  weight numeric
);

CREATE TABLE public.talent_group_weights (
  tgv_code varchar PRIMARY KEY,
  tgv_name text,
  weight numeric
);
```

---

## Key Relationships

- Employees → Performance (1:N, yearly records)
- Employees → Competencies (1:N, yearly × 10 pillars)
- Employees → Psychometric Profile (1:1)
- Employees → PAPI Scores (1:20, one per scale)
- Employees → Strengths (1:5, top 5 strengths)
- Employees → Dimensions (N:1, position, department, grade, etc.)

## Notes

- `employee_id` is text type to support flexible ID formats
- Yearly data (performance, competencies) uses composite primary keys
- All dimension tables use auto-incrementing integer IDs
- Configuration tables support the matching algorithm's weighted scoring

For job vacancy schema, see `job_vacancies_schema.sql`.