import streamlit as st
import pandas as pd
from core.db import get_engine
from core.matching import run_match_query

st.set_page_config(page_title="Talent Matching", page_icon="🎯", layout="wide")

st.title("🎯 Talent Matching Engine")
st.caption("Temukan talenta internal terbaik berdasarkan profil benchmark.")

engine = get_engine()

# Fungsi untuk memuat data dropdown dari database
@st.cache_data(ttl=3600) # Cache data selama 1 jam
def load_dropdown_data():
    with engine.connect() as conn:
        # Mengambil nama posisi dari tabel dim_positions
        positions = pd.read_sql("SELECT position_id, name FROM dim_positions ORDER BY name", conn)
        # Mengambil nama karyawan dari tabel employees
        employees = pd.read_sql("SELECT employee_id, fullname FROM employees ORDER BY fullname", conn)
    return positions, employees

try:
    positions_df, employees_df = load_dropdown_data()
except Exception as e:
    st.error(f"Gagal memuat data untuk filter dari database: {e}")
    st.stop()

# --- UI Kontrol di Sidebar ---
st.sidebar.header("⚙️ Pengaturan Benchmark")

min_rating = st.sidebar.slider(
    "Rating Minimum 'High Performer'",
    min_value=1, max_value=5, value=5,
    help="Hanya karyawan dengan rating ini atau lebih tinggi yang akan dipertimbangkan dalam benchmark otomatis."
)

# --- Mode A: Benchmark Manual ---
st.sidebar.subheader("Mode A: Benchmark Manual")
manual_selection = st.sidebar.multiselect(
    "Pilih Karyawan Benchmark",
    options=[f"{row.employee_id} — {row.fullname}" for _, row in employees_df.iterrows()],
    help="Pilih 1-5 karyawan untuk dijadikan tolak ukur manual."
)
manual_ids = [item.split(" — ")[0] for item in manual_selection]

# --- Mode B: Benchmark Berdasarkan Posisi ---
st.sidebar.subheader("Mode B: Benchmark Berdasarkan Posisi")
position_name_map = dict(zip(positions_df['name'], positions_df['position_id']))
selected_position_name = st.sidebar.selectbox(
    "Pilih Posisi Target",
    options=["(Tidak ada)"] + list(position_name_map.keys()),
    help="Sistem akan otomatis menggunakan semua high-performer dari posisi ini sebagai benchmark."
)
target_position_id = None
if selected_position_name != "(Tidak ada)":
    target_position_id = position_name_map[selected_position_name]

st.sidebar.info("Anda bisa menggunakan Mode A, Mode B, atau keduanya secara bersamaan.")

# --- Tombol Eksekusi ---
if st.sidebar.button("🚀 Jalankan Talent Match", use_container_width=True):
    if not manual_ids and not target_position_id:
        st.warning("Silakan pilih setidaknya satu karyawan benchmark manual atau satu posisi target.")
    else:
        with st.spinner("Menjalankan algoritma Talent Matching... Ini mungkin memakan waktu beberapa saat."):
            try:
                result_df = run_match_query(
                    engine,
                    manual_ids=manual_ids,
                    target_position_id=target_position_id,
                    min_rating=min_rating
                )

                st.success("Perhitungan Talent Matching selesai!")
                st.subheader("📊 Peringkat Talenta")
                st.dataframe(result_df, use_container_width=True)

            except Exception as e:
                st.error(f"Terjadi kesalahan saat menjalankan query: {e}")
else:
    st.info("Atur parameter benchmark di sidebar kiri, lalu klik **Jalankan Talent Match**.")
