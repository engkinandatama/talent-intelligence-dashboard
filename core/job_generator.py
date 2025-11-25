"""
Core module for the Talent Intelligence Dashboard
This file contains the core functions for database operations and data management
"""

import streamlit as st
from sqlalchemy import create_engine, text, MetaData, Table
from typing import Optional
import json


def get_engine():
    """
    Creates and returns a SQLAlchemy engine instance using credentials from Streamlit secrets.
    """
    # Use the same engine creation as in db.py for consistency
    from .db import get_engine as get_main_engine
    return get_main_engine()


def save_job_vacancy(role_name: str, job_level: str, role_purpose: str,
                     key_responsibilities: list, qualifications: list,
                     required_competencies: list, success_metrics: list = None) -> Optional[int]:
    """
    Save a job vacancy to the database.

    Args:
        role_name (str): Name of the role
        job_level (str): Job level
        role_purpose (str): Purpose of the role
        key_responsibilities (list): List of key responsibilities
        qualifications (list): List of qualifications
        required_competencies (list): List of required competencies
        success_metrics (list, optional): List of success metrics/KPIs. Defaults to None.

    Returns:
        Optional[int]: The ID of the newly created vacancy, or None if failed
    """
    try:
        engine = get_engine()
        metadata = MetaData()

        # Reflect the job_vacancies table or create if it doesn't exist
        with engine.connect() as conn:
            # Check if table exists
            result = conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_schema = 'public'
                    AND table_name = 'job_vacancies'
                );
            """))
            table_exists = result.scalar()

            if not table_exists:
                # Create the job_vacancies table if it doesn't exist
                create_table_sql = """
                CREATE TABLE public.job_vacancies (
                    vacancy_id SERIAL PRIMARY KEY,
                    role_name TEXT NOT NULL,
                    job_level TEXT,
                    role_purpose TEXT,
                    key_responsibilities TEXT[],
                    qualifications TEXT[],
                    required_competencies TEXT[],
                    success_metrics TEXT[] DEFAULT '{}',
                    created_at TIMESTAMPTZ DEFAULT now()
                );
                """
                conn.execute(text(create_table_sql))
                conn.commit()
                st.info("✅ Job vacancies table created successfully!")
            else:
                # Check if success_metrics column exists, if not add it
                check_col_sql = """
                SELECT EXISTS (
                    SELECT FROM information_schema.columns
                    WHERE table_schema = 'public'
                    AND table_name = 'job_vacancies'
                    AND column_name = 'success_metrics'
                );
                """
                col_exists = conn.execute(text(check_col_sql)).scalar()
                if not col_exists:
                    conn.execute(text("ALTER TABLE public.job_vacancies ADD COLUMN success_metrics TEXT[] DEFAULT '{}';"))
                    conn.commit()
                    # st.info("🔄 Database schema updated: Added success_metrics column.")

            # Now reflect the table
            job_vacancies_table = Table('job_vacancies', metadata, autoload_with=conn, schema='public')

            # Handle qualifications if it's a dict (convert to list of strings for TEXT[] column)
            final_qualifications = qualifications
            if isinstance(qualifications, dict):
                final_qualifications = []
                if 'education' in qualifications:
                    final_qualifications.append(f"Education: {qualifications['education']}")
                if 'experience' in qualifications:
                    final_qualifications.append(f"Experience: {qualifications['experience']}")
                if 'skills' in qualifications and isinstance(qualifications['skills'], list):
                    skills_str = ", ".join(qualifications['skills'])
                    final_qualifications.append(f"Skills: {skills_str}")
            
            # Handle required_competencies if it's a list of dicts (convert to list of strings)
            final_competencies = []
            if required_competencies:
                for comp in required_competencies:
                    if isinstance(comp, dict):
                        final_competencies.append(f"{comp.get('name', '')}: {comp.get('description', '')}")
                    else:
                        final_competencies.append(str(comp))
            else:
                final_competencies = required_competencies

            # Prepare the data as a single dictionary
            vacancy_data = {
                'role_name': role_name,
                'job_level': job_level,
                'role_purpose': role_purpose,
                'key_responsibilities': key_responsibilities,
                'qualifications': final_qualifications,
                'required_competencies': final_competencies,
                'success_metrics': success_metrics or []
            }

            # Execute the insert with RETURNING clause to get the inserted ID
            result = conn.execute(
                job_vacancies_table.insert().values(vacancy_data).returning(job_vacancies_table.c.vacancy_id)
            )
            inserted_id = result.scalar()
            conn.commit()

            return inserted_id

    except Exception as e:
        st.error(f"Error saving to database: {str(e)}")
        return None