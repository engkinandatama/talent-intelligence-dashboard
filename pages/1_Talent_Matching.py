# pages/1_Talent_Matching.py

import streamlit as st
import pandas as pd
from core.db import get_engine
from core.matching import run_standard_match_query, get_match_for_single_person

st.set_page_config(page_title="Talent Matching", page_icon="🎯", layout="wide")

st.title("🎯 Talent Matching Engine")
st.caption("Temukan talenta internal terbaik berdasarkan profil benchmark.")

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
    st.error(f"Gagal memuat data filter dari database: {e}")
    st.stop()

# --- UI Panel Filter (Desain baru sesuai permintaan yang direvisi) ---
with st.container():
    st.header("⚙️ Pengaturan Pencarian & Benchmark")

    # Bagian Benchmark (Wajib untuk Matching)
    # Gunakan get() untuk mencegah error jika session_state belum diinisialisasi
    with st.expander("1. Mode Pencarian", expanded=st.session_state.get('expander_state', True)):
        # Mode A: Multi-select karyawan dengan chips
        with st.container():
            st.subheader("Mode A: Pilih Karyawan")

            # Siapkan daftar pilihan untuk multiselect
            employee_options = [f"{row.employee_id} — {row.fullname}" for _, row in employees_df.iterrows()]

            # Gunakan st.multiselect
            selected_employees_mode_a = st.multiselect(
                "Pilih satu atau beberapa karyawan",
                options=employee_options,
                help="Ketik untuk mencari, lalu pilih karyawan. Setiap karyawan yang dipilih akan dianalisis kecocokannya terhadap semua posisi."
            )

            # Ekstrak hanya employee_id dari hasil pilihan
            manual_ids = [item.split(" — ", 1)[0] for item in selected_employees_mode_a]

        st.divider()  # Pemisah antara Mode A dan Mode B

        # Mode B: Filter berdasarkan dimensi + rating
        with st.container():
            st.subheader("Mode B: Filter Kriteria")

            # Deteksi apakah Mode A aktif
            mode_a_active = len(manual_ids) > 0

            col1, col2 = st.columns(2)

            with col1:
                pos_map = dict(zip(positions_df['name'], positions_df['position_id']))
                # Ganti "(Semua)" dengan "None" agar lebih jelas bahwa filter tidak aktif
                pos_options = ["(Tidak dipilih)"] + list(pos_map.keys())
                pos_name = st.selectbox("Pilih Posisi", pos_options, index=0)
                filter_position_id = pos_map.get(pos_name) if pos_name != "(Tidak dipilih)" else None

            # Hanya tampilkan filter departemen jika Mode A tidak aktif
            with col2:
                if not mode_a_active:
                    dep_map = dict(zip(departments_df['name'], departments_df['department_id']))
                    dep_options = ["(Tidak dipilih)"] + list(dep_map.keys())
                    dep_name = st.selectbox("Pilih Departemen", dep_options, index=0)
                    filter_department_id = dep_map.get(dep_name) if dep_name != "(Tidak dipilih)" else None
                else:
                    st.info("Departemen tidak berlaku dalam Mode A+B")
                    filter_department_id = None  # Disable filter departemen jika Mode A aktif

            col3, col4 = st.columns(2)

            # Hanya tampilkan filter divisi jika Mode A tidak aktif
            with col3:
                if not mode_a_active:
                    div_map = dict(zip(divisions_df['name'], divisions_df['division_id']))
                    div_options = ["(Tidak dipilih)"] + list(div_map.keys())
                    div_name = st.selectbox("Pilih Divisi", div_options, index=0)
                    filter_division_id = div_map.get(div_name) if div_name != "(Tidak dipilih)" else None
                else:
                    st.info("Divisi tidak berlaku dalam Mode A+B")
                    filter_division_id = None  # Disable filter divisi jika Mode A aktif

            # Hanya tampilkan filter grade jika Mode A tidak aktif
            with col4:
                if not mode_a_active:
                    grade_map = dict(zip(grades_df['name'], grades_df['grade_id']))
                    grade_options = ["(Tidak dipilih)"] + list(grade_map.keys())
                    grade_name = st.selectbox("Pilih Grade", grade_options, index=0)
                    filter_grade_id = grade_map.get(grade_name) if grade_name != "(Tidak dipilih)" else None
                else:
                    st.info("Grade tidak berlaku dalam Mode A+B")
                    filter_grade_id = None  # Disable filter grade jika Mode A aktif

            # Tambahkan slider range rating untuk filter kandidat
            rating_range = st.slider(
                "Filter Berdasarkan Rentang Rating Kinerja",
                min_value=1,
                max_value=5,
                value=(1, 5)  # Defaultnya menampilkan semua rating
            )

            # Rating untuk benchmark selalu 5
            # Mode B aktif jika setidaknya satu filter dipilih (tidak "(Tidak dipilih)")
            if mode_a_active:
                # Jika Mode A aktif, hanya filter posisi yang berlaku
                mode_b_active = (filter_position_id is not None)
            else:
                # Jika Mode A tidak aktif, semua filter berlaku
                mode_b_active = (filter_position_id is not None or filter_department_id is not None or
                                 filter_division_id is not None or filter_grade_id is not None)

            # Jika semua filter tidak dipilih (default), kita tetap ingin Mode B aktif untuk menampilkan semua karyawan yang sesuai rating
            if not mode_b_active and not mode_a_active:
                # Dalam kasus ini, jika hanya Mode B yang diaktifkan tanpa filter aktif, tetap dianggap Mode B aktif
                # Ini untuk memungkinkan tampilan semua karyawan yang sesuai rating
                mode_b_active = True

            min_rating = 5  # Selalu gunakan 5 untuk benchmark

        # Penjelasan untuk skenario
        st.divider()
        st.markdown("**Penjelasan Mode:**")

        if manual_ids and not (filter_position_id or filter_department_id or filter_division_id or filter_grade_id):
            st.info("🔍 **Mode A Saja**: Menampilkan informasi profil untuk karyawan yang Anda input secara spesifik.")
        elif not manual_ids and (filter_position_id or filter_department_id or filter_division_id or filter_grade_id):
            st.info("⚙️ **Mode B Saja**: Menampilkan semua karyawan yang memenuhi kriteria filter dan rating performance yang ditentukan.")
        elif manual_ids and (filter_position_id or filter_department_id or filter_division_id or filter_grade_id):
            st.info("🔍⚙️ **Mode A & B**: Menampilkan tingkat kecocokan antara karyawan dari Mode A terhadap kriteria filter dari Mode B.")
        else:
            st.info("📋 **Default**: Jika tidak ada filter yang dipilih, sistem akan menampilkan semua karyawan dengan rating tinggi sebagai benchmark default.")

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

# --- Tombol Eksekusi ---
run_button = st.button("🚀 Jalankan Talent Match", use_container_width=True, type="primary")

# Tutup expander setelah tombol ditekan
if run_button:
    st.session_state['expander_state'] = False

# --- Area Hasil ---
if run_button:
    filters = {
        "position_id": filter_position_id if filter_position_id != "(Semua)" else None,
        "department_id": filter_department_id if filter_department_id != "(Semua)" else None,
        "division_id": filter_division_id if filter_division_id != "(Semua)" else None,
        "grade_id": filter_grade_id if filter_grade_id != "(Semua)" else None,
    }

    # Hapus filter yang tidak dipilih
    filters = {k: v for k, v in filters.items() if v is not None}

    mode_a_active = len(manual_ids) > 0
    # Periksa apakah ada filter aktif
    has_active_filters = (filter_position_id is not None or filter_department_id is not None or
                          filter_division_id is not None or filter_grade_id is not None)

    # Jika tidak ada filter aktif (semua None), tetap dianggap mode_b_active True untuk menampilkan semua karyawan dengan rating
    mode_b_active = has_active_filters or (not mode_a_active and not has_active_filters)

    if not manual_ids and not mode_b_active:
        st.warning("Harap tentukan karyawan (Mode A) atau pilih setidaknya satu filter (Mode B).")
    else:
        # Mode A saja: Menampilkan kecocokan karyawan terpilih terhadap berbagai posisi
        # Kita akan menghitung kecocokan karyawan yang dipilih terhadap benchmark dari setiap posisi
        if mode_a_active and not has_active_filters:
            st.success(f"Memproses kecocokan untuk {len(manual_ids)} karyawan terpilih...")

            all_final_results = []
            # Proses setiap karyawan secara individual
            for emp_id in manual_ids:
                with st.spinner(f"Menghitung rekomendasi posisi untuk {emp_id}..."):
                    # Gunakan fungsi get_match_for_single_person untuk karyawan ini
                    temp_result = get_match_for_single_person(engine, emp_id)
                    if not temp_result.empty:
                        all_final_results.append(temp_result)

            # Gabungkan semua hasil
            if all_final_results:
                final_result_df = pd.concat(all_final_results, ignore_index=True)

                # Simpan hasil ke session state dan reset halaman ke 1
                st.session_state.search_results = final_result_df
                st.session_state.current_page_a = 1  # Reset halaman ke 1 untuk Mode A
                st.session_state.last_mode_used = 'A'  # Tandai bahwa ini adalah Mode A

                st.toast(f"✅ Perhitungan selesai! Ditemukan kecocokan untuk {len(final_result_df)} posisi.", icon="🎉")
                st.subheader("📊 Rekomendasi Posisi untuk Karyawan Terpilih")

                # Implementasi pagination baru
                if final_result_df.empty:
                    st.warning("Tidak ada kandidat yang cocok dengan kriteria.")
                else:
                    # --- Implementasi Pagination Baru ---
                    items_per_page = 100  # Ganti dari 20 ke 100
                    total_items = len(final_result_df)
                    total_pages = (total_items + items_per_page - 1) // items_per_page

                    # Pastikan halaman saat ini tidak melebihi total halaman (jika filter berubah)
                    if st.session_state.current_page_a > total_pages:
                        st.session_state.current_page_a = 1

                    # "Potong" DataFrame untuk menampilkan data halaman saat ini
                    start_idx = (st.session_state.current_page_a - 1) * items_per_page
                    end_idx = min(start_idx + items_per_page, len(final_result_df))
                    paginated_df = final_result_df.iloc[start_idx:end_idx]

                    # Tampilkan tabel yang sudah dipaginasi
                    st.dataframe(paginated_df, use_container_width=True)

                    # Tampilan navigasi dan informasi halaman (baru)
                    st.divider()
                    col1, col2, col3, col4 = st.columns([2, 1, 1, 1])

                    with col2:
                        # Input untuk lompat ke halaman spesifik
                        page_num = st.number_input(
                            "Ke Halaman",
                            min_value=1,
                            max_value=total_pages,
                            value=st.session_state.current_page_a,
                            step=1,
                            label_visibility="collapsed",
                            key=f"jump_page_a_{hash(str(manual_ids))}"
                        )
                    with col3:
                        if st.button("◀", use_container_width=True, disabled=(st.session_state.current_page_a <= 1)):
                            if st.session_state.current_page_a > 1:
                                st.session_state.current_page_a -= 1
                            st.rerun()
                    with col4:
                        if st.button("▶", use_container_width=True, disabled=(st.session_state.current_page_a >= total_pages)):
                            if st.session_state.current_page_a < total_pages:
                                st.session_state.current_page_a += 1
                            st.rerun()
                    # Handling untuk input halaman
                    if page_num != st.session_state.current_page_a and 1 <= page_num <= total_pages:
                        st.session_state.current_page_a = page_num
                        st.rerun()

                # Tambahkan informasi tambahan
                st.info("Angka `final_match_rate` menunjukkan seberapa cocok karyawan terhadap posisi tersebut. Semakin tinggi nilainya, semakin cocok.")
            else:
                st.warning("Tidak ditemukan hasil untuk karyawan yang dipilih.")
        elif not mode_a_active and not has_active_filters:
            # Mode B saja tanpa filter aktif - tampilkan semua karyawan sesuai rating
            with st.spinner("Menjalankan algoritma Talent Matching..."):
                try:
                    result_df = run_standard_match_query(
                        engine,
                        manual_ids_for_benchmark=None,
                        target_position_id_for_benchmark=None,
                        filters={},
                        search_name=None,
                        rating_range=rating_range,  # Gunakan rentang rating dari slider
                        limit=10000,  # Gunakan jumlah hasil yang sangat tinggi untuk mengambil semua data
                        manual_ids_to_filter=None
                    )

                    # Simpan hasil ke session state dan reset halaman ke 1
                    st.session_state.search_results = result_df
                    st.session_state.current_page_b = 1  # Reset halaman ke 1 untuk Mode B
                    st.session_state.last_mode_used = 'B'  # Tandai bahwa ini adalah Mode B

                    st.toast(f"✅ Perhitungan selesai! Ditemukan {len(result_df)} karyawan.", icon="🎉")
                    st.subheader("📊 Peringkat Kecocokan Talenta")

                    # Implementasi pagination baru
                    if result_df.empty:
                        st.warning("Tidak ada kandidat yang cocok dengan kriteria.")
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
                        st.dataframe(paginated_df, use_container_width=True)

                        # Tampilan navigasi dan informasi halaman (baru)
                        st.divider()
                        col1, col2, col3, col4 = st.columns([2, 1, 1, 1])

                        with col2:
                            # Input untuk lompat ke halaman spesifik
                            page_num = st.number_input(
                                "Ke Halaman",
                                min_value=1,
                                max_value=total_pages,
                                value=st.session_state.current_page_b,
                                step=1,
                                label_visibility="collapsed",
                                key=f"jump_page_b_{hash(str(filters))}"
                            )
                        with col3:
                            if st.button("◀", use_container_width=True, disabled=(st.session_state.current_page_b <= 1)):
                                if st.session_state.current_page_b > 1:
                                    st.session_state.current_page_b -= 1
                                st.rerun()
                        with col4:
                            if st.button("▶", use_container_width=True, disabled=(st.session_state.current_page_b >= total_pages)):
                                if st.session_state.current_page_b < total_pages:
                                    st.session_state.current_page_b += 1
                                st.rerun()
                        # Handling untuk input halaman
                        if page_num != st.session_state.current_page_b and 1 <= page_num <= total_pages:
                            st.session_state.current_page_b = page_num
                            st.rerun()
                except Exception as e:
                    st.error("Terjadi kesalahan saat menjalankan query.")
                    st.exception(e)
        else:
            # Mode B saja atau Mode A+B
            with st.spinner("Menjalankan algoritma Talent Matching..."):
                try:
                    # Mode A+B: Kita ingin menentukan seberapa cocok karyawan dari Mode A terhadap kriteria yang ditentukan di Mode B
                    # Kita ingin mencari kecocokan karyawan dari Mode A terhadap benchmark dari kriteria Mode B
                    if mode_a_active and (filter_position_id or any(filters.values())):
                        # Mode A+B - Hitung kecocokan karyawan dari Mode A terhadap benchmark yang ditentukan oleh filter Mode B
                        # Kita gunakan filter dari Mode B untuk menentukan benchmark, dan filter hasil hanya untuk karyawan dari Mode A
                        result_df = run_standard_match_query(
                            engine,
                            manual_ids_for_benchmark=None,  # Jangan gunakan manual_ids sebagai benchmark
                            target_position_id_for_benchmark=filter_position_id,  # Gunakan posisi sebagai benchmark jika dipilih
                            filters=filters,  # Terapkan filter lainnya
                            search_name=None,
                            rating_range=rating_range,
                            limit=10000,  # Gunakan jumlah hasil yang sangat tinggi untuk mengambil semua data
                            manual_ids_to_filter=manual_ids  # Filter hasil hanya untuk karyawan dari Mode A
                        )

                        # Simpan hasil ke session state dan reset halaman ke 1
                        st.session_state.search_results = result_df
                        st.session_state.current_page_ab = 1  # Reset halaman ke 1 untuk Mode A+B
                        st.session_state.last_mode_used = 'AB'  # Tandai bahwa ini adalah Mode A+B
                    else:
                        # Mode B saja atau Mode A tanpa filter
                        result_df = run_standard_match_query(
                            engine,
                            manual_ids_for_benchmark=manual_ids if manual_ids else None,
                            target_position_id_for_benchmark=None,
                            filters=filters,
                            search_name=None,
                            rating_range=rating_range,
                            limit=10000,  # Gunakan jumlah hasil yang sangat tinggi untuk mengambil semua data
                            manual_ids_to_filter=None
                        )

                        # Simpan hasil ke session state dan reset halaman ke 1
                        if st.session_state.search_results is None:
                            st.session_state.search_results = result_df
                        st.session_state.current_page_b = 1  # Reset halaman ke 1 untuk Mode B
                        st.session_state.last_mode_used = 'B'  # Tandai bahwa ini adalah Mode B

                    # Tambahkan toast notification
                    st.toast(f"✅ Perhitungan selesai! Ditemukan {len(result_df)} kandidat yang cocok.", icon="🎉")
                    st.subheader("📊 Peringkat Kecocokan Talenta")

                    # Implementasi pagination dengan session_state yang terpisah untuk setiap mode
                    if result_df.empty:
                        st.warning("Tidak ada kandidat yang cocok dengan kriteria.")
                    else:
                        # Simpan hasil ke session state jika belum disimpan sebelumnya di mode ini
                        if mode_a_active and (filter_position_id or any(filters.values())):
                            # Mode A+B
                            st.session_state.search_results = result_df
                            mode_key = 'current_page_ab'
                        else:
                            # Mode B saja
                            if not hasattr(st.session_state, 'search_results') or st.session_state.search_results is None:
                                st.session_state.search_results = result_df
                            mode_key = 'current_page_b'

                        # Ambil data dari session state untuk pagination
                        current_result_df = st.session_state.search_results
                        items_per_page = 100  # Ganti dari 20 ke 100
                        total_items = len(current_result_df)
                        total_pages = (total_items + items_per_page - 1) // items_per_page

                        # Pastikan halaman saat ini tidak melebihi total halaman (jika filter berubah)
                        if st.session_state[mode_key] > total_pages:
                            st.session_state[mode_key] = 1

                        # "Potong" DataFrame untuk menampilkan data halaman saat ini
                        start_idx = (st.session_state[mode_key] - 1) * items_per_page
                        end_idx = min(start_idx + items_per_page, len(current_result_df))
                        paginated_df = current_result_df.iloc[start_idx:end_idx]

                        # Tampilkan tabel yang sudah dipaginasi
                        st.dataframe(paginated_df, use_container_width=True)

                        # Tampilan navigasi dan informasi halaman (baru)
                        st.divider()
                        col1, col2, col3, col4 = st.columns([2, 1, 1, 1])

                        with col2:
                            # Input untuk lompat ke halaman spesifik
                            page_num = st.number_input(
                                "Ke Halaman",
                                min_value=1,
                                max_value=total_pages,
                                value=st.session_state[mode_key],
                                step=1,
                                label_visibility="collapsed",
                                key=f"jump_page_ab_{mode_key}_{hash(str(manual_ids))}"
                            )
                        with col3:
                            if st.button("◀", use_container_width=True, disabled=(st.session_state[mode_key] <= 1), key=f"prev_btn_{mode_key}"):
                                if st.session_state[mode_key] > 1:
                                    st.session_state[mode_key] -= 1
                                st.rerun()
                        with col4:
                            if st.button("▶", use_container_width=True, disabled=(st.session_state[mode_key] >= total_pages), key=f"next_btn_{mode_key}"):
                                if st.session_state[mode_key] < total_pages:
                                    st.session_state[mode_key] += 1
                                st.rerun()
                        # Handling untuk input halaman
                        if page_num != st.session_state[mode_key] and 1 <= page_num <= total_pages:
                            st.session_state[mode_key] = page_num
                            st.rerun()
                except Exception as e:
                    st.error("Terjadi kesalahan saat menjalankan query.")
                    st.exception(e)
else:
    st.info("Atur Mode A atau Mode B di atas, lalu klik 'Jalankan Talent Match'.")

# Tampilkan hasil dari session state jika sudah ada (untuk menjaga hasil saat berpindah halaman)
# Ini akan aktif saat run_button tidak diklik tapi hasil sebelumnya masih ada di session_state
if not run_button and 'search_results' in st.session_state and st.session_state.search_results is not None and not st.session_state.search_results.empty:
    st.subheader("📊 Peringkat Kecocokan Talenta (Hasil Tersimpan)")

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
    st.dataframe(paginated_df, use_container_width=True)

    # Tampilan navigasi dan informasi halaman (baru)
    st.divider()
    cols = st.columns([3, 1, 0.5, 0.5, 1, 0.5, 0.5, 3])

    with cols[1]:
        # Tampilkan informasi halaman saat ini
        st.text(f"{st.session_state[mode_key]} / {total_pages}")

    with cols[2]:
        if st.button("◀", use_container_width=True, disabled=(st.session_state[mode_key] <= 1), key=f"nav_prev_final_{mode_key}"):
            if st.session_state[mode_key] > 1:
                st.session_state[mode_key] -= 1
            st.rerun()
    with cols[3]:
        if st.button("▶", use_container_width=True, disabled=(st.session_state[mode_key] >= total_pages), key=f"nav_next_final_{mode_key}"):
            if st.session_state[mode_key] < total_pages:
                st.session_state[mode_key] += 1
            st.rerun()

    with cols[5]:
        # Input untuk lompat ke halaman spesifik
        page_num = st.number_input(
            "Ke Hal.",
            min_value=1,
            max_value=total_pages,
            value=st.session_state[mode_key],
            step=1,
            label_visibility="collapsed",
            key=f"nav_jump_final_{mode_key}"
        )
    with cols[6]:
        if st.button("→", key=f"jump_final_{mode_key}"):
            if 1 <= page_num <= total_pages:
                st.session_state[mode_key] = page_num
                st.rerun()

    # Handling untuk input halaman
    if page_num != st.session_state[mode_key] and 1 <= page_num <= total_pages:
        st.session_state[mode_key] = page_num
        st.rerun()
