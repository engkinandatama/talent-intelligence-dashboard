import streamlit as st
from sqlalchemy import create_engine

def get_engine():
    DB_USER = st.secrets["DB_USER"]
    DB_PASS = st.secrets["DB_PASS"]
    DB_HOST = st.secrets["DB_HOST"]
    DB_PORT = st.secrets["DB_PORT"]
    DB_NAME = st.secrets["DB_NAME"]

    url = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    return create_engine(url)

def test_connection():
    try:
        engine = get_engine()
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        return True
    except Exception as e:
        print("DB ERROR:", e)
        return False
