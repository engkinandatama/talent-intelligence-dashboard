"""
Core module for the Talent Intelligence Dashboard
This file contains the core functions for database operations and data management
"""

import streamlit as st
from sqlalchemy import create_engine, text
from typing import Optional
import json


def get_engine():
    """
    Creates and returns a SQLAlchemy engine instance using credentials from Streamlit secrets.
    """
    # Get database URL from secrets
    database_url = st.secrets["SUPABASE_URL"]
    
    # Create and return the engine
    engine = create_engine(database_url)
    return engine


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
        
        with engine.connect() as conn:
            # Insert the job data into the database
            insert_query = """
            INSERT INTO public.job_vacancies 
            (role_name, job_level, role_purpose, key_responsibilities, qualifications, required_competencies)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING vacancy_id;
            """
            
            result = conn.execute(insert_query, (
                role_name,
                job_level,
                role_purpose,
                key_responsibilities,
                qualifications,
                required_competencies
            ))
            
            vacancy_id = result.fetchone()[0]
            conn.commit()
            
            return vacancy_id
            
    except Exception as e:
        st.error(f"Error saving to database: {str(e)}")
        return None