# pages/1_Talent_Matching.py

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from core.db import get_engine
from core.matching import run_standard_match_query, get_match_for_single_person, execute_matching, validate_employee_data
from core.matching_breakdown import get_detailed_match_breakdown
from core.analysis_ui import render_detailed_analysis

st.set_page_config(page_title="Talent Matching", page_icon="🎯", layout="wide")

# Dark Theme CSS
st.markdown("""
<style>
    .main {
        background-color: #0F1419;
    }
    
    h1, h2, h3, h4 {
        color: #4A90E2;
    }
    
    [data-testid="stDataFrame"] {
        background: rgba(26, 35, 50, 0.4);
        border-radius: 8px;
    }
</style>
""", unsafe_allow_html=True)

st.title("🎯 Talent Matching Engine")
st.caption("Find the best internal talent based on benchmark profile.")

engine = get_engine()

# --- Memuat semua data untuk dropdown filter ---
@st.cache_data(ttl=3600)
def load_all_dimensions():
    with engine.connect() as conn:
        positions = pd.read_sql("SELECT position_id, name FROM dim_positions ORDER BY name", conn)
        employees = pd.read_sql("SELECT employee_id, fullname FROM employees ORDER BY fullname", conn)
        departments = pd.read_sql("SELECT department_id, name FROM dim_departments ORDER BY name", conn)
        divisions = pd.read_sql("SELECT division_id, name FROM dim_divisions ORDER BY name", conn)
        grades = pd.read_sql("SELECT grade_id, name FROM dim_grades ORDER BY name", conn)
    return positions, employees, departments, divisions, grades

try:
    positions_df, employees_df, departments_df, divisions_df, grades_df = load_all_dimensions()
except Exception as e:
    st.error(f"Failed to load filter data from database: {e}")
    st.stop()

# --- UI Panel Filter (Desain baru sesuai permintaan yang direvisi) ---
with st.container():
    st.header("⚙️ Search & Benchmark Settings")

    # Bagian Benchmark (Wajib untuk Matching)
    # Gunakan get() untuk mencegah error jika session_state belum diinisialisasi
    with st.expander("1. Search Mode", expanded=st.session_state.get('expander_state', True)):
        # Mode A: Multi-select karyawan dengan chips
        with st.container():
            st.subheader("Mode A: Select Employees")

            # Siapkan daftar pilihan untuk multiselect
            employee_options = [f"{row.employee_id} — {row.fullname}" for _, row in employees_df.iterrows()]

            # Gunakan st.multiselect
            selected_employees_mode_a = st.multiselect(
                "Select one or more employees",
                options=employee_options,
                help="Type to search, then select employees. Each selected employee will be analyzed for position match."
            )

            # Ekstrak hanya employee_id dari hasil pilihan
            manual_ids = [item.split(" — ", 1)[0] for item in selected_employees_mode_a]

            # Tambahkan toggle benchmark
            use_manual_as_benchmark = st.toggle("Use selected employees as Benchmark", value=False)

        st.divider()  # Pemisah antara Mode A dan Mode B

        # Mode B: Filter berdasarkan dimensi + rating
        with st.container():
            # Deteksi apakah Mode A aktif untuk menonaktifkan filter B
            mode_a_active = len(manual_ids) > 0

            with st.expander("Mode B: Filter Kriteria", expanded=not mode_a_active):
                if mode_a_active:
                    st.caption("⚠ Filter Mode B disembunyikan karena Mode A aktif.")
                    filter_position_id = None
                    filter_department_id = None
                    filter_division_id = None
                    filter_grade_id = None
                else:
                    col1, col2 = st.columns(2)

                    with col1:
                        pos_map = dict(zip(positions_df['name'], positions_df['position_id']))
                        # Ganti "(Not selected)" dengan "None" agar lebih jelas bahwa filter tidak aktif
                        pos_options = ["(Not selected)"] + list(pos_map.keys())
                        pos_name = st.selectbox("Select Position", pos_options, index=0)
                        filter_position_id = pos_map.get(pos_name) if pos_name != "(Not selected)" else None

                    # Tampilkan filter departemen
                    with col2:
                        dep_map = dict(zip(departments_df['name'], departments_df['department_id']))
                        dep_options = ["(Not selected)"] + list(dep_map.keys())
                        dep_name = st.selectbox("Select Department", dep_options, index=0)
                        filter_department_id = dep_map.get(dep_name) if dep_name != "(Not selected)" else None

                    col3, col4 = st.columns(2)

                    # Tampilkan filter divisi
                    with col3:
                        div_map = dict(zip(divisions_df['name'], divisions_df['division_id']))
                        div_options = ["(Not selected)"] + list(div_map.keys())
                        div_name = st.selectbox("Select Division", div_options, index=0)
                        filter_division_id = div_map.get(div_name) if div_name != "(Not selected)" else None

                    # Tampilkan filter grade
                    with col4:
                        grade_map = dict(zip(grades_df['name'], grades_df['grade_id']))
                        grade_options = ["(Not selected)"] + list(grade_map.keys())
                        grade_name = st.selectbox("Select Grade", grade_options, index=0)
                        filter_grade_id = grade_map.get(grade_name) if grade_name != "(Not selected)" else None

            # Buat dictionary filter
            filters = {}
            if filter_position_id:
                filters["position_id"] = filter_position_id
            if filter_department_id:
                filters["department_id"] = filter_department_id
            if filter_division_id:
                filters["division_id"] = filter_division_id
            if filter_grade_id:
                filters["grade_id"] = filter_grade_id

            min_rating = 5  # HP rating fixed = 5 (High Performer) based on system design

        # Penjelasan untuk skenario
        st.divider()
        st.markdown("**Mode Explanation:**")

        if manual_ids and not use_manual_as_benchmark:
            st.info(
                "🟦 **Mode A – Position Recommendation**\n"
                "The system will display the best position recommendations for selected employees."
            )
        elif manual_ids and use_manual_as_benchmark:
            st.success(
                "🟩 **Manual Benchmark Active**\n"
                "Selected employees are used as baseline to compare all employees."
            )
        elif not manual_ids and filters:
            st.info(
                "🟧 **Filter Benchmark Active**\n"
                "Benchmark is built from High Performers matching your filters."
            )
        else:
            st.warning(
                "⚫ **Default Benchmark**\n"
                "Sistem menggunakan High Performers (rating = 5) sebagai baseline."
            )

# --- Initialize Session State ---
if 'search_results' not in st.session_state:
    st.session_state.search_results = None
if 'current_page' not in st.session_state:
    st.session_state.current_page = 1
if 'current_page_a' not in st.session_state:
    st.session_state.current_page_a = 1
if 'current_page_b' not in st.session_state:
    st.session_state.current_page_b = 1
if 'current_page_ab' not in st.session_state:
    st.session_state.current_page_ab = 1
if 'last_mode_used' not in st.session_state:
    st.session_state.last_mode_used = 'B'  # Default mode adalah B
if 'expander_state' not in st.session_state:
    st.session_state.expander_state = True  # Defaultnya expander terbuka
# --- Initialize Editing State for All Pagination Modes ---
if 'editing_page_a' not in st.session_state:
    st.session_state.editing_page_a = False
if 'editing_page_b' not in st.session_state:
    st.session_state.editing_page_b = False
if 'editing_page_ab' not in st.session_state:
    st.session_state.editing_page_ab = False
if 'editing_page_final' not in st.session_state:
    st.session_state.editing_page_final = False

# --- Tombol Eksekusi ---
run_button = st.button("🚀 Run Talent Match", width="stretch", type="primary")

# Tutup expander setelah tombol ditekan
if run_button:
    st.session_state['expander_state'] = False

# --- Area Hasil ---
if run_button:
    mode_a_active = len(manual_ids) > 0
    has_active_filters = bool(filters)  # Check if filters dictionary is not empty

    if not manual_ids and not has_active_filters:
        st.warning("Please specify employees (Mode A) or select at least one filter (Mode B).")
    else:
        # Tentukan mode dan eksekusi pencarian
        if mode_a_active and not use_manual_as_benchmark:
            if not manual_ids:
                st.error("You must select at least one employee for Mode A.")
                st.stop()

            # Tampilkan pesan sukses
            st.success("Position recommendations successfully calculated.")

            # Ambil nama karyawan untuk tampilan yang lebih baik
            with engine.connect() as conn:
                # Konversi manual_ids ke format yang sesuai untuk query ANY
                emp_names = pd.read_sql("SELECT employee_id, fullname FROM employees WHERE employee_id = ANY(%s)",
                                        conn, params=(manual_ids,))
                emp_name_map = dict(zip(emp_names['employee_id'], emp_names['fullname']))

            # Proses setiap karyawan secara individual
            for emp_id in manual_ids:
                with st.spinner(f"Calculating position recommendations for {emp_id}..."):
                    # Validasi data karyawan terlebih dahulu
                    validate = validate_employee_data(emp_id, engine)
                    emp_name = emp_name_map.get(emp_id, emp_id)

                    if not validate["ok"]:
                        st.error(f"⚠ Data for {emp_name} is incomplete. Missing: {', '.join(validate['missing'])}")
                        # Tambahkan informasi ke session state sebagai catatan
                        if 'search_results' not in st.session_state or st.session_state.search_results is None:
                            st.session_state.search_results = pd.DataFrame()
                        continue  # Lewati perhitungan untuk employee ini

                    # Gunakan fungsi get_match_for_single_person untuk karyawan ini
                    df_reco = get_match_for_single_person(engine, emp_id)
                    if not df_reco.empty:
                        # Tampilkan header dengan nama karyawan
                        st.subheader(f"Position Recommendations for {emp_name}")

                        # Tambahkan Top 3 Podium untuk posisi teratas
                        if not df_reco.empty:
                            st.subheader("🏆 Top Position Recommendations")

                            # Ambil 3 posisi teratas
                            top_positions = df_reco.head(3).to_dict('records')

                            # Buat kolom untuk podium
                            cols = st.columns(len(top_positions))

                            # Definisikan peringkat
                            ranks = {
                                0: {"title": "🥇 1st Place", "size": "1.2rem"},
                                1: {"title": "🥈 2nd Place", "size": "1.1rem"},
                                2: {"title": "🥉 3rd Place", "size": "1.0rem"}
                            }

                            for i, position in enumerate(top_positions):
                                with cols[i]:
                                    with st.container(border=True):
                                        rank_info = ranks.get(i)
                                        st.markdown(f"<h5 style='text-align: center; font-size: {rank_info['size']};'>{rank_info['title']}</h5>", unsafe_allow_html=True)
                                        st.markdown(f"<p style='text-align: center; font-weight: bold;'>{position.get('position_name', 'N/A')}</p>", unsafe_allow_html=True)
                                        st.caption(f"Score: {position['final_match_rate']:.2f}")
                                        st.divider()

                                        st.markdown(f"**Current Position:** {position.get('position_name', 'N/A')}")

                                        # Tampilkan skor kecocokan
                                        st.metric("Match Score", f"{position['final_match_rate']:.2f}")

                            st.divider() # Tambahkan pemisah setelah podium

                        # Tampilkan tabel rekomendasi posisi untuk karyawan ini
                        st.dataframe(df_reco, width="stretch")

                        # Save results to session state for each employee
                        if 'search_results' not in st.session_state or st.session_state.search_results is None:
                            st.session_state.search_results = df_reco
                        else:
                            st.session_state.search_results = pd.concat([st.session_state.search_results, df_reco], ignore_index=True)
            if 'search_results' in st.session_state and st.session_state.search_results is not None and not st.session_state.search_results.empty:
                st.session_state.current_page_a = 1  # Reset halaman ke 1 untuk Mode A
                st.session_state.last_mode_used = 'A'  # Tandai bahwa ini adalah Mode A
        elif mode_a_active and use_manual_as_benchmark:
            # Mode A - Manual Benchmark
            st.success("Ranking of all employees based on manual benchmark is ready to display.")
            with st.spinner("Running Talent Matching algorithm with manual benchmark..."):
                try:
                    result_df = run_standard_match_query(
                        engine,
                        manual_ids_for_benchmark=manual_ids,
                        filters={},
                        search_name=None,
                        rating_range=(5, 5),  # HP rating fixed = 5 (High Performer) based on system design
                        limit=10000,
                        manual_ids_to_filter=None,
                        use_manual_as_benchmark=True,
                        min_rating=min_rating
                    )

                    # Save results to session state and reset page to 1
                    st.session_state.search_results = result_df
                    st.session_state.current_page_b = 1  # Reset halaman ke 1 untuk Mode B
                    st.session_state.last_mode_used = 'B'  # Tandai bahwa ini adalah Mode B

                    st.toast(f"✅ Calculation complete! Found {len(result_df)} employees.", icon="🎉")
                    st.subheader("📊 Talent Match Ranking (Manual Benchmark)")

                    # Tambahkan Top 3 Podium
                    if not result_df.empty:
                        st.subheader("🏆 Top Match Podium")

                        # Ambil 3 kandidat teratas
                        top_candidates = result_df.head(3).to_dict('records')

                        # Buat kolom untuk podium
                        cols = st.columns(len(top_candidates))

                        # Definisikan peringkat
                        ranks = {
                            0: {"title": "🥇 1st Place", "size": "1.2rem"},
                            1: {"title": "🥈 2nd Place", "size": "1.1rem"},
                            2: {"title": "🥉 3rd Place", "size": "1.0rem"}
                        }

                        for i, candidate in enumerate(top_candidates):
                            with cols[i]:
                                with st.container(border=True):
                                    rank_info = ranks.get(i)
                                    st.markdown(f"<h5 style='text-align: center; font-size: {rank_info['size']};'>{rank_info['title']}</h5>", unsafe_allow_html=True)
                                    st.markdown(f"<p style='text-align: center; font-weight: bold;'>{candidate['fullname']}</p>", unsafe_allow_html=True)
                                    st.caption(f"ID: {candidate['employee_id']}")
                                    st.divider()

                                    st.markdown(f"**Current Position:** {candidate.get('position_name', 'N/A')}")

                                    # Menampilkan konteks benchmark
                                    benchmark_context = "Manual Benchmark"
                                    st.markdown(f"**Benchmark:** {benchmark_context}")

                                    st.metric("Match Score", f"{candidate['final_match_rate']:.2f}")

                        st.divider() # Tambahkan pemisah setelah podium

                    # Implementasi pagination baru
                    if result_df.empty:
                        st.warning("No candidates match the criteria.")
                    else:
                        # --- Implementasi Pagination Baru ---
                        items_per_page = 100  # Ganti dari 20 ke 100
                        total_items = len(result_df)
                        total_pages = (total_items + items_per_page - 1) // items_per_page

                        # Pastikan halaman saat ini tidak melebihi total halaman (jika filter berubah)
                        if st.session_state.current_page_b > total_pages:
                            st.session_state.current_page_b = 1

                        # "Potong" DataFrame untuk menampilkan data halaman saat ini
                        start_idx = (st.session_state.current_page_b - 1) * items_per_page
                        end_idx = min(start_idx + items_per_page, len(result_df))
                        paginated_df = result_df.iloc[start_idx:end_idx]

                        # Tampilkan tabel yang sudah dipaginasi
                        st.dataframe(paginated_df, width="stretch")

                        # Gunakan 3 kolom untuk menempatkan pagination di tengah
                        _, mid_col, _ = st.columns([.3, .4, .3])

                        with mid_col:
                            # Gunakan 5 kolom untuk tata letak yang presisi
                            _, col1, col2, col3, _ = st.columns([.2, .1, .2, .1, .2]) # Kolom tengah lebih lebar

                            with col1:
                                # Tombol "Sebelumnya"
                                if st.button("◀", key=f"prev_page_b_{st.session_state.current_page_b}", width="stretch", disabled=(st.session_state.current_page_b <= 1)):
                                    st.session_state.editing_page_b = False # Keluar dari mode edit jika ada
                                    if st.session_state.current_page_b > 1:
                                        st.session_state.current_page_b -= 1
                                        st.rerun()

                            with col2:
                                # --- Logika untuk "Editable Text" ---

                                # Fungsi callback yang akan dijalankan saat input berubah (Enter ditekan)
                                def update_page_from_input_b():
                                    try:
                                        new_page = int(st.session_state[f'page_input_b_{st.session_state.current_page_b}'])
                                        if 1 <= new_page <= total_pages:
                                            st.session_state.current_page_b = new_page
                                    except (ValueError, TypeError):
                                        pass # Abaikan jika input tidak valid
                                    # Setelah input diproses, selalu kembali ke mode tampilan
                                    st.session_state.editing_page_b = False

                                # Tampilkan input atau teks berdasarkan state
                                if st.session_state.get('editing_page_b', False):
                                    st.text_input(
                                        "Page",
                                        value=str(st.session_state.current_page_b),
                                        key=f"page_input_b_{st.session_state.current_page_b}",
                                        on_change=update_page_from_input_b,
                                        label_visibility="collapsed"
                                    )
                                else:
                                    # Tampilkan teks yang bisa diklik untuk masuk ke mode edit
                                    if st.button(f"{st.session_state.current_page_b} / {total_pages}", key=f"page_display_button_b_{st.session_state.current_page_b}", width="stretch"):
                                        st.session_state.editing_page_b = True
                                        st.rerun() # Rerun to display text_input

                            with col3:
                                # Tombol "Berikutnya"
                                if st.button("▶", key=f"next_page_b_{st.session_state.current_page_b}", width="stretch", disabled=(st.session_state.current_page_b >= total_pages)):
                                    st.session_state.editing_page_b = False # Keluar dari mode edit jika ada
                                    if st.session_state.current_page_b < total_pages:
                                        st.session_state.current_page_b += 1
                                        st.rerun()

                        # CSS untuk membuat tombol dan input terlihat minimalis
                        st.markdown("""
            <style>
                /* Style untuk tombol navigasi */
                div[data-testid*="stButton"] > button[kind="secondary"] {
                    background-color: transparent; border: none; color: #2563EB; font-size: 1.2rem; font-weight: bold;
                }
                div[data-testid*="stButton"] > button[kind="secondary"]:hover { color: #FF4B4B; border: none; }
                div[data-testid*="stButton"] > button[kind="secondary"]:disabled { color: #4F4F4F; border: none; }

                /* Style untuk tombol yang menampilkan halaman (page_display) */
                div[data-testid*="stButton"] > button[data-testid="baseButton-secondary"] {
                    text-align: center;
                    background-color: transparent !important;
                    border: none !important;
                }

                /* Style untuk text input agar terlihat menyatu */
                div[data-testid="stTextInput"] input {
                    text-align: center;
                    background-color: transparent !important;
                    border: none !important;
                    border-bottom: 1px solid #4F4F4F !important;
                    outline: none;
                    box-shadow: none !important;
                    padding: 0px !important;
                    font-weight: bold;
                    font-size: 1rem;
                }
                div[data-testid="stTextInput"] input:focus {
                    border-bottom: 2px solid #2563EB !important;
                    box-shadow: none !important;
                }
            </style>
            """, unsafe_allow_html=True)
                except Exception as e:
                    st.error("Terjadi kesalahan saat menjalankan query.")
                    st.exception(e)
        elif not mode_a_active and has_active_filters:
            # Mode B - Filter Benchmark
            st.success("Filter-based benchmark successfully used for ranking calculation.")
            with st.spinner("Running Talent Matching algorithm with filter benchmark..."):
                try:
                    result_df = run_standard_match_query(
                        engine,
                        manual_ids_for_benchmark=None,
                        filters=filters,
                        search_name=None,
                        rating_range=(5, 5),  # HP rating fixed = 5 (High Performer) based on system design
                        limit=10000,
                        manual_ids_to_filter=None,
                        use_manual_as_benchmark=False,
                        min_rating=min_rating
                    )

                    # Save results to session state and reset page to 1
                    st.session_state.search_results = result_df
                    st.session_state.current_page_b = 1  # Reset halaman ke 1 untuk Mode B
                    st.session_state.last_mode_used = 'B'  # Tandai bahwa ini adalah Mode B

                    # Cek jika hasil kosong
                    if result_df.empty:
                        st.warning("No High Performers match your filters.")

                    st.toast(f"✅ Calculation complete! Found {len(result_df)} employees.", icon="🎉")
                    st.subheader("📊 Talent Match Ranking (Filter Benchmark)")

                    # Tambahkan Top 3 Podium
                    if not result_df.empty:
                        st.subheader("🏆 Top Match Podium")

                        # Ambil 3 kandidat teratas
                        top_candidates = result_df.head(3).to_dict('records')

                        # Buat kolom untuk podium
                        cols = st.columns(len(top_candidates))

                        # Definisikan peringkat
                        ranks = {
                            0: {"title": "🥇 1st Place", "size": "1.2rem"},
                            1: {"title": "🥈 2nd Place", "size": "1.1rem"},
                            2: {"title": "🥉 3rd Place", "size": "1.0rem"}
                        }

                        for i, candidate in enumerate(top_candidates):
                            with cols[i]:
                                with st.container(border=True):
                                    rank_info = ranks.get(i)
                                    st.markdown(f"<h5 style='text-align: center; font-size: {rank_info['size']};'>{rank_info['title']}</h5>", unsafe_allow_html=True)
                                    st.markdown(f"<p style='text-align: center; font-weight: bold;'>{candidate['fullname']}</p>", unsafe_allow_html=True)
                                    st.caption(f"ID: {candidate['employee_id']}")
                                    st.divider()

                                    st.markdown(f"**Current Position:** {candidate.get('position_name', 'N/A')}")

                                    # Menampilkan konteks benchmark
                                    benchmark_context = "Filter Benchmark"
                                    st.markdown(f"**Benchmark:** {benchmark_context}")

                                    st.metric("Match Score", f"{candidate['final_match_rate']:.2f}")

                        st.divider() # Tambahkan pemisah setelah podium

                    # Implementasi pagination baru
                    if result_df.empty:
                        st.warning("No candidates match the criteria.")
                    else:
                        # --- Implementasi Pagination Baru ---
                        items_per_page = 100  # Ganti dari 20 ke 100
                        total_items = len(result_df)
                        total_pages = (total_items + items_per_page - 1) // items_per_page

                        # Pastikan halaman saat ini tidak melebihi total halaman (jika filter berubah)
                        if st.session_state.current_page_b > total_pages:
                            st.session_state.current_page_b = 1

                        # "Potong" DataFrame untuk menampilkan data halaman saat ini
                        start_idx = (st.session_state.current_page_b - 1) * items_per_page
                        end_idx = min(start_idx + items_per_page, len(result_df))
                        paginated_df = result_df.iloc[start_idx:end_idx]

                        # Tampilkan tabel yang sudah dipaginasi
                        st.dataframe(paginated_df, width="stretch")

                        # Gunakan 3 kolom untuk menempatkan pagination di tengah
                        _, mid_col, _ = st.columns([.3, .4, .3])

                        with mid_col:
                            # Gunakan 5 kolom untuk tata letak yang presisi
                            _, col1, col2, col3, _ = st.columns([.2, .1, .2, .1, .2]) # Kolom tengah lebih lebar

                            with col1:
                                # Tombol "Sebelumnya"
                                if st.button("◀", key=f"prev_page_b_{st.session_state.current_page_b}", width="stretch", disabled=(st.session_state.current_page_b <= 1)):
                                    st.session_state.editing_page_b = False # Keluar dari mode edit jika ada
                                    if st.session_state.current_page_b > 1:
                                        st.session_state.current_page_b -= 1
                                        st.rerun()

                            with col2:
                                # --- Logika untuk "Editable Text" ---

                                # Fungsi callback yang akan dijalankan saat input berubah (Enter ditekan)
                                def update_page_from_input_b():
                                    try:
                                        new_page = int(st.session_state[f'page_input_b_{st.session_state.current_page_b}'])
                                        if 1 <= new_page <= total_pages:
                                            st.session_state.current_page_b = new_page
                                    except (ValueError, TypeError):
                                        pass # Abaikan jika input tidak valid
                                    # Setelah input diproses, selalu kembali ke mode tampilan
                                    st.session_state.editing_page_b = False

                                # Tampilkan input atau teks berdasarkan state
                                if st.session_state.get('editing_page_b', False):
                                    st.text_input(
                                        "Page",
                                        value=str(st.session_state.current_page_b),
                                        key=f"page_input_b_{st.session_state.current_page_b}",
                                        on_change=update_page_from_input_b,
                                        label_visibility="collapsed"
                                    )
                                else:
                                    # Tampilkan teks yang bisa diklik untuk masuk ke mode edit
                                    if st.button(f"{st.session_state.current_page_b} / {total_pages}", key=f"page_display_button_b_{st.session_state.current_page_b}", width="stretch"):
                                        st.session_state.editing_page_b = True
                                        st.rerun() # Rerun to display text_input

                            with col3:
                                # Tombol "Berikutnya"
                                if st.button("▶", key=f"next_page_b_{st.session_state.current_page_b}", width="stretch", disabled=(st.session_state.current_page_b >= total_pages)):
                                    st.session_state.editing_page_b = False # Keluar dari mode edit jika ada
                                    if st.session_state.current_page_b < total_pages:
                                        st.session_state.current_page_b += 1
                                        st.rerun()

                        # CSS untuk membuat tombol dan input terlihat minimalis
                        st.markdown("""
            <style>
                /* Style untuk tombol navigasi */
                div[data-testid*="stButton"] > button[kind="secondary"] {
                    background-color: transparent; border: none; color: #2563EB; font-size: 1.2rem; font-weight: bold;
                }
                div[data-testid*="stButton"] > button[kind="secondary"]:hover { color: #FF4B4B; border: none; }
                div[data-testid*="stButton"] > button[kind="secondary"]:disabled { color: #4F4F4F; border: none; }

                /* Style untuk tombol yang menampilkan halaman (page_display) */
                div[data-testid*="stButton"] > button[data-testid="baseButton-secondary"] {
                    text-align: center;
                    background-color: transparent !important;
                    border: none !important;
                }

                /* Style untuk text input agar terlihat menyatu */
                div[data-testid="stTextInput"] input {
                    text-align: center;
                    background-color: transparent !important;
                    border: none !important;
                    border-bottom: 1px solid #4F4F4F !important;
                    outline: none;
                    box-shadow: none !important;
                    padding: 0px !important;
                    font-weight: bold;
                    font-size: 1rem;
                }
                div[data-testid="stTextInput"] input:focus {
                    border-bottom: 2px solid #2563EB !important;
                    box-shadow: none !important;
                }
            </style>
            """, unsafe_allow_html=True)
                except Exception as e:
                    st.error("Terjadi kesalahan saat menjalankan query.")
                    st.exception(e)
        elif not mode_a_active and not has_active_filters:
            # Mode Default - Benchmark default (HP rating >= 5)
            st.info("Default benchmark used (High Performers rating ≥5).")
            with st.spinner("Running Talent Matching algorithm with default benchmark..."):
                try:
                    result_df = run_standard_match_query(
                        engine,
                        manual_ids_for_benchmark=None,
                        filters={},
                        search_name=None,
                        rating_range=(5, 5),  # HP rating fixed = 5 (High Performer) based on system design
                        limit=10000,
                        manual_ids_to_filter=None,
                        use_manual_as_benchmark=False,
                        min_rating=min_rating
                    )

                    # Save results to session state and reset page to 1
                    st.session_state.search_results = result_df
                    st.session_state.current_page_b = 1  # Reset halaman ke 1 untuk Mode B
                    st.session_state.last_mode_used = 'B'  # Tandai bahwa ini adalah Mode B

                    st.toast(f"✅ Calculation complete! Found {len(result_df)} employees.", icon="🎉")
                    st.subheader("📊 Talent Match Ranking (Default Benchmark)")

                    # Tambahkan Top 3 Podium
                    if not result_df.empty:
                        st.subheader("🏆 Top Match Podium")

                        # Ambil 3 kandidat teratas
                        top_candidates = result_df.head(3).to_dict('records')

                        # Buat kolom untuk podium
                        cols = st.columns(len(top_candidates))

                        # Definisikan peringkat
                        ranks = {
                            0: {"title": "🥇 1st Place", "size": "1.2rem"},
                            1: {"title": "🥈 2nd Place", "size": "1.1rem"},
                            2: {"title": "🥉 3rd Place", "size": "1.0rem"}
                        }

                        for i, candidate in enumerate(top_candidates):
                            with cols[i]:
                                with st.container(border=True):
                                    rank_info = ranks.get(i)
                                    st.markdown(f"<h5 style='text-align: center; font-size: {rank_info['size']};'>{rank_info['title']}</h5>", unsafe_allow_html=True)
                                    st.markdown(f"<p style='text-align: center; font-weight: bold;'>{candidate['fullname']}</p>", unsafe_allow_html=True)
                                    st.caption(f"ID: {candidate['employee_id']}")
                                    st.divider()

                                    st.markdown(f"**Current Position:** {candidate.get('position_name', 'N/A')}")

                                    # Menampilkan konteks benchmark
                                    benchmark_context = "Default Benchmark (HP rating = 5)"
                                    st.markdown(f"**Benchmark:** {benchmark_context}")

                                    st.metric("Match Score", f"{candidate['final_match_rate']:.2f}")

                        st.divider() # Tambahkan pemisah setelah podium

                    # Implementasi pagination baru
                    if result_df.empty:
                        st.warning("No candidates match the criteria.")
                    else:
                        # --- Implementasi Pagination Baru ---
                        items_per_page = 100  # Ganti dari 20 ke 100
                        total_items = len(result_df)
                        total_pages = (total_items + items_per_page - 1) // items_per_page

                        # Pastikan halaman saat ini tidak melebihi total halaman (jika filter berubah)
                        if st.session_state.current_page_b > total_pages:
                            st.session_state.current_page_b = 1

                        # "Potong" DataFrame untuk menampilkan data halaman saat ini
                        start_idx = (st.session_state.current_page_b - 1) * items_per_page
                        end_idx = min(start_idx + items_per_page, len(result_df))
                        paginated_df = result_df.iloc[start_idx:end_idx]

                        # Tampilkan tabel yang sudah dipaginasi
                        st.dataframe(paginated_df, width="stretch")

                        st.divider()

                        # Gunakan 3 kolom untuk menempatkan pagination di tengah
                        _, mid_col, _ = st.columns([.3, .4, .3])

                        with mid_col:
                            # Gunakan 5 kolom untuk tata letak yang presisi
                            _, col1, col2, col3, _ = st.columns([.2, .1, .2, .1, .2]) # Kolom tengah lebih lebar

                            with col1:
                                # Tombol "Sebelumnya"
                                if st.button("◀", key=f"prev_page_b_{st.session_state.current_page_b}", width="stretch", disabled=(st.session_state.current_page_b <= 1)):
                                    st.session_state.editing_page_b = False # Keluar dari mode edit jika ada
                                    if st.session_state.current_page_b > 1:
                                        st.session_state.current_page_b -= 1
                                        st.rerun()

                            with col2:
                                # --- Logika untuk "Editable Text" ---

                                # Fungsi callback yang akan dijalankan saat input berubah (Enter ditekan)
                                def update_page_from_input_b():
                                    try:
                                        new_page = int(st.session_state[f'page_input_b_{st.session_state.current_page_b}'])
                                        if 1 <= new_page <= total_pages:
                                            st.session_state.current_page_b = new_page
                                    except (ValueError, TypeError):
                                        pass # Abaikan jika input tidak valid
                                    # Setelah input diproses, selalu kembali ke mode tampilan
                                    st.session_state.editing_page_b = False

                                # Tampilkan input atau teks berdasarkan state
                                if st.session_state.get('editing_page_b', False):
                                    st.text_input(
                                        "Page",
                                        value=str(st.session_state.current_page_b),
                                        key=f"page_input_b_{st.session_state.current_page_b}",
                                        on_change=update_page_from_input_b,
                                        label_visibility="collapsed"
                                    )
                                else:
                                    # Tampilkan teks yang bisa diklik untuk masuk ke mode edit
                                    if st.button(f"{st.session_state.current_page_b} / {total_pages}", key=f"page_display_button_b_{st.session_state.current_page_b}", width="stretch"):
                                        st.session_state.editing_page_b = True
                                        st.rerun() # Rerun to display text_input

                            with col3:
                                # Tombol "Berikutnya"
                                if st.button("▶", key=f"next_page_b_{st.session_state.current_page_b}", width="stretch", disabled=(st.session_state.current_page_b >= total_pages)):
                                    st.session_state.editing_page_b = False # Keluar dari mode edit jika ada
                                    if st.session_state.current_page_b < total_pages:
                                        st.session_state.current_page_b += 1
                                        st.rerun()

                        # CSS untuk membuat tombol dan input terlihat minimalis
                        st.markdown("""
            <style>
                /* Style untuk tombol navigasi */
                div[data-testid*="stButton"] > button[kind="secondary"] {
                    background-color: transparent; border: none; color: #2563EB; font-size: 1.2rem; font-weight: bold;
                }
                div[data-testid*="stButton"] > button[kind="secondary"]:hover { color: #FF4B4B; border: none; }
                div[data-testid*="stButton"] > button[kind="secondary"]:disabled { color: #4F4F4F; border: none; }

                /* Style untuk tombol yang menampilkan halaman (page_display) */
                div[data-testid*="stButton"] > button[data-testid="baseButton-secondary"] {
                    text-align: center;
                    background-color: transparent !important;
                    border: none !important;
                }

                /* Style untuk text input agar terlihat menyatu */
                div[data-testid="stTextInput"] input {
                    text-align: center;
                    background-color: transparent !important;
                    border: none !important;
                    border-bottom: 1px solid #4F4F4F !important;
                    outline: none;
                    box-shadow: none !important;
                    padding: 0px !important;
                    font-weight: bold;
                    font-size: 1rem;
                }
                div[data-testid="stTextInput"] input:focus {
                    border-bottom: 2px solid #2563EB !important;
                    box-shadow: none !important;
                }
            </style>
            """, unsafe_allow_html=True)
                except Exception as e:
                    st.error("An error occurred while running query.")
                    st.exception(e)
else:
    st.info("Set Mode A or Mode B above, then click 'Run Talent Match'.")

# Tampilkan hasil dari session state jika sudah ada (untuk menjaga hasil saat berpindah halaman)
# Ini akan aktif saat run_button tidak diklik tapi hasil sebelumnya masih ada di session_state
if not run_button and 'search_results' in st.session_state and st.session_state.search_results is not None and not st.session_state.search_results.empty:
    st.subheader("📊 Talent Match Ranking (Saved Results)")

    # Tambahkan Top 3 Podium
    if not st.session_state.search_results.empty:
        st.subheader("🏆 Top Match Podium")

        # Ambil 3 kandidat teratas
        top_candidates = st.session_state.search_results.head(3).to_dict('records')

        # Buat kolom untuk podium
        cols = st.columns(len(top_candidates))

        # Definisikan peringkat
        ranks = {
            0: {"title": "🥇 1st Place", "size": "1.2rem"},
            1: {"title": "🥈 2nd Place", "size": "1.1rem"},
            2: {"title": "🥉 3rd Place", "size": "1.0rem"}
        }

        for i, candidate in enumerate(top_candidates):
            with cols[i]:
                with st.container(border=True):
                    rank_info = ranks.get(i)
                    st.markdown(f"<h5 style='text-align: center; font-size: {rank_info['size']};'>{rank_info['title']}</h5>", unsafe_allow_html=True)
                    st.markdown(f"<p style='text-align: center; font-weight: bold;'>{candidate['fullname']}</p>", unsafe_allow_html=True)
                    st.caption(f"ID: {candidate['employee_id']}")
                    st.divider()

                    st.markdown(f"**Current Position:** {candidate.get('position_name', 'N/A')}")

                    # Menampilkan konteks benchmark
                    benchmark_context = "Default" # Fallback
                    if 'benchmark_position' in candidate:
                        benchmark_context = candidate['benchmark_position']
                    st.markdown(f"**Benchmark:** {benchmark_context}")

                    st.metric("Match Score", f"{candidate['final_match_rate']:.2f}")

        st.divider() # Tambahkan pemisah setelah podium

    # Gunakan hasil dari session state
    current_result_df = st.session_state.search_results

    # Ambil informasi mode terakhir yang digunakan
    if 'last_mode_used' in st.session_state:
        last_mode = st.session_state.last_mode_used
    else:
        # Default ke mode B jika tidak ada informasi
        last_mode = 'B'

    # Tetapkan mode_key berdasarkan mode terakhir yang digunakan
    if last_mode == 'A':
        mode_key = 'current_page_a'
    elif last_mode == 'AB':
        mode_key = 'current_page_ab'
    else:  # Default ke B
        mode_key = 'current_page_b'

    items_per_page = 100  # Ganti dari 20 ke 100
    total_items = len(current_result_df)
    total_pages = (total_items + items_per_page - 1) // items_per_page

    # "Potong" DataFrame untuk menampilkan data halaman saat ini
    start_idx = (st.session_state[mode_key] - 1) * items_per_page
    end_idx = min(start_idx + items_per_page, len(current_result_df))
    paginated_df = current_result_df.iloc[start_idx:end_idx]

    # Tampilkan tabel yang sudah dipaginasi
    st.dataframe(paginated_df, width="stretch")

    # Tampilan navigasi dan informasi halaman (baru - dengan desain minimalis)
    st.divider()

    # Gunakan 3 kolom untuk menempatkan pagination di tengah
    _, mid_col, _ = st.columns([.3, .4, .3])

    with mid_col:
        # Gunakan 5 kolom untuk tata letak yang presisi
        _, col1, col2, col3, _ = st.columns([.2, .1, .2, .1, .2]) # Kolom tengah lebih lebar

        with col1:
            # Tombol "Sebelumnya"
            if st.button("◀", key=f"prev_page_final_{st.session_state[mode_key]}", width="stretch", disabled=(st.session_state[mode_key] <= 1)):
                st.session_state.editing_page_final = False # Keluar dari mode edit jika ada
                if st.session_state[mode_key] > 1:
                    st.session_state[mode_key] -= 1
                    st.rerun()

        with col2:
            # --- Logika untuk "Editable Text" ---

            # Fungsi callback yang akan dijalankan saat input berubah (Enter ditekan)
            def update_page_from_input_final():
                try:
                    new_page = int(st.session_state[f'page_input_final_{st.session_state[mode_key]}'])
                    if 1 <= new_page <= total_pages:
                        st.session_state[mode_key] = new_page
                except (ValueError, TypeError):
                    pass # Abaikan jika input tidak valid
                # Setelah input diproses, selalu kembali ke mode tampilan
                st.session_state.editing_page_final = False

            # Tampilkan input atau teks berdasarkan state
            if st.session_state.get('editing_page_final', False):
                st.text_input(
                    "Page",
                    value=str(st.session_state[mode_key]),
                    key=f"page_input_final_{st.session_state[mode_key]}",
                    on_change=update_page_from_input_final,
                    label_visibility="collapsed"
                )
            else:
                # Tampilkan teks yang bisa diklik untuk masuk ke mode edit
                if st.button(f"{st.session_state[mode_key]} / {total_pages}", key=f"page_display_button_final_{st.session_state[mode_key]}", width="stretch"):
                    st.session_state.editing_page_final = True
                    st.rerun() # Rerun to display text_input

        with col3:
            # Tombol "Berikutnya"
            if st.button("▶", key=f"next_page_final_{st.session_state[mode_key]}", width="stretch", disabled=(st.session_state[mode_key] >= total_pages)):
                st.session_state.editing_page_final = False # Keluar dari mode edit jika ada
                if st.session_state[mode_key] < total_pages:
                    st.session_state[mode_key] += 1
                    st.rerun()

    # CSS untuk membuat tombol dan input terlihat minimalis
    st.markdown("""
    <style>
        /* Style untuk tombol navigasi */
        div[data-testid*="stButton"] > button[kind="secondary"] {
            background-color: transparent; border: none; color: #2563EB; font-size: 1.2rem; font-weight: bold;
        }
        div[data-testid*="stButton"] > button[kind="secondary"]:hover { color: #FF4B4B; border: none; }
        div[data-testid*="stButton"] > button[kind="secondary"]:disabled { color: #4F4F4F; border: none; }

        /* Style untuk tombol yang menampilkan halaman (page_display) */
        div[data-testid*="stButton"] > button[data-testid="baseButton-secondary"] {
            text-align: center;
            background-color: transparent !important;
            border: none !important;
        }

        /* Style untuk text input agar terlihat menyatu */
        div[data-testid="stTextInput"] input {
            text-align: center;
            background-color: transparent !important;
            border: none !important;
            border-bottom: 1px solid #4F4F4F !important;
            outline: none;
            box-shadow: none !important;
            padding: 0px !important;
            font-weight: bold;
            font-size: 1rem;
        }
        div[data-testid="stTextInput"] input:focus {
            border-bottom: 2px solid #2563EB !important;
            box-shadow: none !important;
        }
    </style>
    """, unsafe_allow_html=True)

# ==================== DETAILED ANALYSIS SECTION ====================
# This section is placed at the END of the file, completely OUTSIDE all conditional blocks
# This ensures it persists across pagination and mode switches

if 'search_results' in st.session_state and st.session_state.search_results is not None:
    if not st.session_state.search_results.empty:
        # Determine benchmark IDs based on last mode used
        benchmark_ids_to_use = []
        
        if st.session_state.get('last_mode_used') == 'A' and 'manual_ids' in locals():
            # Mode A: Use manual employee IDs as benchmark
            benchmark_ids_to_use = manual_ids
        # else: Mode B or default - use empty list (will default to HP rating=5)
        
        try:
            render_detailed_analysis(
                results_df=st.session_state.search_results,
                benchmark_ids=benchmark_ids_to_use,
                engine=engine
            )
        except Exception as analysis_error:
            st.warning(f"Detailed analysis unavailable: {str(analysis_error)}")

# Footer
st.markdown('<br>', unsafe_allow_html=True)
st.markdown("""
<div style='text-align: center; color: #6B7B94; padding: 2rem 0;'>
    <small>Talent Intelligence Dashboard © 2025. All rights reserved.</small>
</div>
""", unsafe_allow_html=True)
