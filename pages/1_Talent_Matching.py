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
    with st.expander("1. Mode Pencarian", expanded=True):
        # Mode A: Input teks untuk ID/Nama Karyawan (hanya ini)
        with st.container():
            st.subheader("Mode A: Input Manual Karyawan")
            manual_input = st.text_input("Cari Karyawan (berdasarkan Nama atau Employee ID)", placeholder="Ketik nama atau ID karyawan...")

            # Jika ada input, langsung lacak karyawan tanpa dropdown
            manual_ids = []
            if manual_input:
                search_results = employees_df[
                    employees_df['fullname'].str.contains(manual_input, case=False, na=False) |
                    employees_df['employee_id'].str.contains(manual_input, case=False, na=False)
                ]

                if not search_results.empty:
                    # Secara otomatis track semua hasil pencarian
                    manual_ids = search_results['employee_id'].tolist()
                    found_names = [f"{row.employee_id} — {row.fullname}" for _, row in search_results.iterrows()]
                    st.info(f"Ditemukan {len(found_names)} karyawan: {', '.join(found_names)}")
                else:
                    st.warning("Tidak ada karyawan ditemukan.")
            # Jika tidak ada input, manual_ids tetap kosong

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

# Tambahkan input jumlah hasil
with st.container():
    result_limit = st.number_input("Jumlah Hasil yang Ditampilkan",
                                   min_value=50,
                                   max_value=1000,
                                   value=200,
                                   step=50,
                                   help="Jumlah maksimum hasil yang akan ditampilkan")

# --- Tombol Eksekusi ---
run_button = st.button("🚀 Jalankan Talent Match", use_container_width=True, type="primary")

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

                st.success(f"Perhitungan selesai! Ditemukan kecocokan untuk {len(final_result_df)} posisi.")
                st.subheader("📊 Rekomendasi Posisi untuk Karyawan Terpilih")

                # Implementasi pagination
                if len(final_result_df) > result_limit:
                    # Inisialisasi session state untuk pagination
                    if 'current_page_a' not in st.session_state:
                        st.session_state.current_page_a = 0

                    items_per_page = min(50, result_limit)  # Batasi jumlah item per halaman
                    total_pages = (len(final_result_df) + items_per_page - 1) // items_per_page

                    # Filter data untuk halaman saat ini
                    start_idx = st.session_state.current_page_a * items_per_page
                    end_idx = min(start_idx + items_per_page, len(final_result_df))
                    current_page_data = final_result_df.iloc[start_idx:end_idx]

                    st.write(f"Halaman {st.session_state.current_page_a + 1} dari {total_pages}")

                    # Tampilkan hasil untuk halaman saat ini
                    st.dataframe(current_page_data, use_container_width=True)

                    # Tombol navigasi
                    col1, col2, col3 = st.columns([1, 2, 1])
                    with col1:
                        if st.button("◀ Sebelumnya", key="prev_a", disabled=(st.session_state.current_page_a == 0)):
                            st.session_state.current_page_a -= 1
                            st.rerun()
                    with col3:
                        if st.button("Berikutnya ▶", key="next_a", disabled=(st.session_state.current_page_a >= total_pages - 1)):
                            st.session_state.current_page_a += 1
                            st.rerun()
                    with col2:
                        pass
                else:
                    # Tampilkan semua hasil jika jumlahnya kurang dari atau sama dengan result_limit
                    st.dataframe(final_result_df, use_container_width=True)

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
                        limit=result_limit,  # Gunakan jumlah hasil yang ditentukan pengguna
                        manual_ids_to_filter=None
                    )
                    st.success(f"Perhitungan selesai! Ditemukan {len(result_df)} karyawan.")
                    st.subheader("📊 Peringkat Kecocokan Talenta")

                    # Implementasi pagination
                    if len(result_df) > result_limit:
                        # Inisialisasi session state untuk pagination
                        if 'current_page_b' not in st.session_state:
                            st.session_state.current_page_b = 0

                        items_per_page = min(50, result_limit)  # Batasi jumlah item per halaman
                        total_pages = (len(result_df) + items_per_page - 1) // items_per_page

                        # Filter data untuk halaman saat ini
                        start_idx = st.session_state.current_page_b * items_per_page
                        end_idx = min(start_idx + items_per_page, len(result_df))
                        current_page_data = result_df.iloc[start_idx:end_idx]

                        st.write(f"Halaman {st.session_state.current_page_b + 1} dari {total_pages}")

                        # Tampilkan hasil untuk halaman saat ini
                        st.dataframe(current_page_data, use_container_width=True)

                        # Tombol navigasi
                        col1, col2, col3 = st.columns([1, 2, 1])
                        with col1:
                            if st.button("◀ Sebelumnya", key="prev_b", disabled=(st.session_state.current_page_b == 0)):
                                st.session_state.current_page_b -= 1
                                st.rerun()
                        with col3:
                            if st.button("Berikutnya ▶", key="next_b", disabled=(st.session_state.current_page_b >= total_pages - 1)):
                                st.session_state.current_page_b += 1
                                st.rerun()
                        with col2:
                            pass
                    else:
                        # Tampilkan semua hasil jika jumlahnya kurang dari atau sama dengan result_limit
                        st.dataframe(result_df, use_container_width=True)
                except Exception as e:
                    st.error("Terjadi kesalahan saat menjalankan query.")
                    st.exception(e)
        else:
            # Mode B saja atau Mode A+B
            with st.spinner("Menjalankan algoritma Talent Matching..."):
                try:
                    result_df = run_standard_match_query(
                        engine,
                        manual_ids_for_benchmark=manual_ids if manual_ids else None,
                        target_position_id_for_benchmark=None,
                        filters=filters,
                        search_name=None,
                        rating_range=rating_range,  # Gunakan rentang rating dari slider
                        limit=result_limit,  # Gunakan jumlah hasil yang ditentukan pengguna
                        manual_ids_to_filter=None
                    )

                    # Jika mode A+B (Mode A+B aktif), hanya tampilkan karyawan dari Mode A
                    if mode_a_active and has_active_filters:
                        result_df = result_df[result_df['employee_id'].isin(manual_ids)]

                    st.success(f"Perhitungan selesai! Ditemukan {len(result_df)} kandidat yang cocok.")
                    st.subheader("📊 Peringkat Kecocokan Talenta")

                    # Implementasi pagination
                    if len(result_df) > result_limit:
                        # Inisialisasi session state untuk pagination
                        if 'current_page_other' not in st.session_state:
                            st.session_state.current_page_other = 0

                        items_per_page = min(50, result_limit)  # Batasi jumlah item per halaman
                        total_pages = (len(result_df) + items_per_page - 1) // items_per_page

                        # Filter data untuk halaman saat ini
                        start_idx = st.session_state.current_page_other * items_per_page
                        end_idx = min(start_idx + items_per_page, len(result_df))
                        current_page_data = result_df.iloc[start_idx:end_idx]

                        st.write(f"Halaman {st.session_state.current_page_other + 1} dari {total_pages}")

                        # Tampilkan hasil untuk halaman saat ini
                        st.dataframe(current_page_data, use_container_width=True)

                        # Tombol navigasi
                        col1, col2, col3 = st.columns([1, 2, 1])
                        with col1:
                            if st.button("◀ Sebelumnya", key="prev_other", disabled=(st.session_state.current_page_other == 0)):
                                st.session_state.current_page_other -= 1
                                st.rerun()
                        with col3:
                            if st.button("Berikutnya ▶", key="next_other", disabled=(st.session_state.current_page_other >= total_pages - 1)):
                                st.session_state.current_page_other += 1
                                st.rerun()
                        with col2:
                            pass
                    else:
                        # Tampilkan semua hasil jika jumlahnya kurang dari atau sama dengan result_limit
                        st.dataframe(result_df, use_container_width=True)
                except Exception as e:
                    st.error("Terjadi kesalahan saat menjalankan query.")
                    st.exception(e)
else:
    st.info("Atur Mode A atau Mode B di atas, lalu klik 'Jalankan Talent Match'.")
