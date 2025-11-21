import streamlit as st
from core.db import test_connection
from components.layout import load_css

st.set_page_config(
    page_title="Talent Match Intelligence",
    page_icon="🧠",
    layout="wide"
)

# Load CSS (global styling)
load_css()

st.title("🧠 Talent Match Intelligence")
st.caption("Enterprise Dashboard – powered by Supabase & Streamlit")

# Test DB connection
status = test_connection()
if status:
    st.success("Database connected successfully ✔")
else:
    st.error("Database failed to connect ❌")

st.markdown("---")

st.write("Selamat datang! Pilih menu pada sidebar untuk memulai analisis.")
