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
                     required_competencies: list) -> Optional[int]:
    """
    Save a job vacancy to the database.

    Args:
        role_name (str): Name of the role
        job_level (str): Job level
        role_purpose (str): Purpose of the role
        key_responsibilities (list): List of key responsibilities
        qualifications (list): List of qualifications
        required_competencies (list): List of required competencies

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
                    created_at TIMESTAMPTZ DEFAULT now()
                );
                """
                conn.execute(text(create_table_sql))
                conn.commit()
                st.info("✅ Job vacancies table created successfully!")

            # Now reflect the table
            job_vacancies_table = Table('job_vacancies', metadata, autoload_with=conn, schema='public')

            # Prepare the data as a single dictionary
            vacancy_data = {
                'role_name': role_name,
                'job_level': job_level,
                'role_purpose': role_purpose,
                'key_responsibilities': key_responsibilities,
                'qualifications': qualifications,
                'required_competencies': required_competencies
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