CREATE TABLE public.job_vacancies (
    vacancy_id SERIAL PRIMARY KEY,
    role_name TEXT NOT NULL,
    job_level TEXT,
    role_purpose TEXT,
    key_responsibilities TEXT[],
    qualifications TEXT[],
    required_competencies TEXT[],
    created_at TIMESTAMPTZ DEFAULT now()
);