-- Migration: Add success_metrics column to job_vacancies
-- Date: 2025-11-25
-- Description: Adds success_metrics TEXT[] column to store KPIs/performance metrics for job roles

-- Migration
ALTER TABLE public.job_vacancies 
ADD COLUMN IF NOT EXISTS success_metrics TEXT[] DEFAULT '{}';

-- Verify
-- Run: SELECT column_name, data_type, column_default FROM information_schema.columns WHERE table_name='job_vacancies';
