import streamlit as st
import google.generativeai as genai
from core.job_generator import save_job_vacancy
import json
from datetime import datetime
from core.db import get_engine
import pandas as pd

# Page configuration
st.set_page_config(
    page_title="AI Job Generator",
    page_icon="🤖",
    layout="wide"
)

st.title("🤖 AI Job Role Generator")
st.markdown("""
Generate comprehensive job descriptions using AI. Enter the role name, level, and main competencies,
and our AI will create a complete job profile with responsibilities, qualifications, and required competencies.
""")

# Initialize session state for generated content
if 'generated_profile' not in st.session_state:
    st.session_state.generated_profile = None
if 'edit_mode' not in st.session_state:
    st.session_state.edit_mode = False

# Fetch competencies from database
@st.cache_data
def get_competency_options():
    try:
        engine = get_engine()
        with engine.connect() as conn:
            # Get the competency pillars from the database
            df = pd.read_sql("SELECT pillar_code, pillar_label FROM public.dim_competency_pillars", conn)
            # Return both code and label options
            return df
    except Exception as e:
        st.error(f"Error loading competency options: {str(e)}")
        return pd.DataFrame(columns=['pillar_code', 'pillar_label'])

# Get competency options
competency_df = get_competency_options()
competency_options = competency_df['pillar_label'].tolist() if not competency_df.empty else []

# --- Input Form with 3 columns ---
with st.form("job_generator_form"):
    col1, col2, col3 = st.columns(3)

    with col1:
        role_name = st.text_input("Role Name", placeholder="e.g., Senior Software Engineer")

    with col2:
        job_level = st.selectbox("Job Level",
            ["Entry Level", "Mid Level", "Senior Level", "Lead Level", "Manager", "Director", "VP"])

    with col3:
        selected_competencies = st.multiselect("Kompetensi Utama (Opsional)",
            options=competency_options,
            placeholder="Pilih kompetensi utama...")

    # Additional context field
    job_context = st.text_area("Additional Context (Optional)",
        placeholder="e.g., Team size, industry, specific requirements, company culture...",
        height=150)

    # Generate button
    submitted = st.form_submit_button("🚀 Generate Job Profile with AI", type="primary")

# Handle form submission
if submitted:
    if not role_name:
        st.error("Role Name is required.")
    else:
        with st.spinner("Generating job profile..."):
            try:
                # Configure API (this will need to be set up in secrets.toml)
                api_key = st.secrets["GEMINI_API_KEY"]
                genai.configure(api_key=api_key)

                # Initialize the model
                model = genai.GenerativeModel('gemini-2.5-flash-lite')

                # Prepare competency context
                competency_context = ", ".join(selected_competencies) if selected_competencies else "No specific competencies mentioned"

                # Create a detailed prompt for the AI
                prompt = f"""
                Generate a comprehensive job description for a {job_level} {role_name}.

                Context: {job_context if job_context else 'No additional context provided.'}
                Main Competencies: {competency_context}

                Please provide the following sections in a structured format:
                1. Role Purpose: A brief paragraph explaining the main purpose of the role
                2. Key Responsibilities: A detailed list of 5-8 key responsibilities
                3. Qualifications: A list of 5-7 required qualifications (education, certifications, experience)
                4. Required Competencies: A list of 5-8 soft and hard competencies required for this role

                Return the response in JSON format with the following keys:
                {{
                    "role_purpose": "...",
                    "key_responsibilities": [...],
                    "qualifications": [...],
                    "required_competencies": [...]
                }}
                """

                # Generate content
                response = model.generate_content(prompt)

                # Parse the response
                content = response.text.strip()

                # Remove any markdown formatting if present
                if content.startswith("```json"):
                    content = content[7:]  # Remove ```json
                if content.endswith("```"):
                    content = content[:-3]  # Remove ```

                # Parse JSON
                job_data = json.loads(content)

                # Store in session state
                st.session_state.generated_profile = job_data

                # Show success toast
                st.toast("✅ Job description generated successfully!", icon="🎉")

            except Exception as e:
                st.error(f"Error generating job profile: {str(e)}")
                st.session_state.generated_profile = None

# Toggle function for edit mode
def toggle_edit_mode():
    st.session_state.edit_mode = not st.session_state.edit_mode

# --- Display results in View or Edit Mode ---
if st.session_state.generated_profile:
    # Get data from session state
    job_data = st.session_state.generated_profile

    # Create columns for the edit button in the top-right
    _, btn_col = st.columns([4, 1])
    with btn_col:
        # Toggle button to switch between View and Edit modes
        st.button(
            "✏️ Edit" if not st.session_state.edit_mode else "❌ Batalkan Edit",
            on_click=toggle_edit_mode,
            key="toggle_edit_btn"
        )

    if st.session_state.edit_mode:
        # --- EDIT MODE ---
        st.subheader("Generated Job Description (Editing)")
        with st.form("edit_profile_form"):
            # Convert responsibilities, qualifications, and competencies to newline-separated strings for editing
            responsibilities_str = "\n".join(job_data.get("key_responsibilities", []))
            qualifications_str = "\n".join(job_data.get("qualifications", []))
            competencies_str = "\n".join(job_data.get("required_competencies", []))

            # Create editable text areas
            edited_role_purpose = st.text_area(
                "Role Purpose",
                value=job_data.get("role_purpose", ""),
                height=120
            )

            edited_responsibilities = st.text_area(
                "Key Responsibilities",
                value=responsibilities_str,
                height=200,
                help="Separate each responsibility with a new line"
            )

            edited_qualifications = st.text_area(
                "Qualifications",
                value=qualifications_str,
                height=150,
                help="Separate each qualification with a new line"
            )

            edited_competencies = st.text_area(
                "Required Competencies",
                value=competencies_str,
                height=150,
                help="Separate each competency with a new line"
            )

            # Convert edited text back to lists
            responsibilities_list = [item.strip() for item in edited_responsibilities.split('\n') if item.strip()]
            qualifications_list = [item.strip() for item in edited_qualifications.split('\n') if item.strip()]
            competencies_list = [item.strip() for item in edited_competencies.split('\n') if item.strip()]

            submitted = st.form_submit_button("💾 Simpan Perubahan", type="primary")
            if submitted:
                # Update session state with edited data
                st.session_state.generated_profile['role_purpose'] = edited_role_purpose
                st.session_state.generated_profile['key_responsibilities'] = responsibilities_list
                st.session_state.generated_profile['qualifications'] = qualifications_list
                st.session_state.generated_profile['required_competencies'] = competencies_list

                st.session_state.edit_mode = False  # Return to view mode
                st.toast("✅ Perubahan disimpan sementara.", icon="👍")
                st.rerun()
    else:
        # --- VIEW MODE (Clean Display) ---
        st.subheader("Generated Job Description")

        # Display role purpose
        st.markdown("#### Role Purpose")
        st.markdown(job_data.get("role_purpose", ""))

        # Display key responsibilities
        st.markdown("#### Key Responsibilities")
        responsibilities = job_data.get("key_responsibilities", [])
        if responsibilities:
            for resp in responsibilities:
                st.markdown(f"- {resp}")
        else:
            st.markdown("- No responsibilities defined")

        # Display qualifications
        st.markdown("#### Qualifications")
        qualifications = job_data.get("qualifications", [])
        if qualifications:
            for qual in qualifications:
                st.markdown(f"- {qual}")
        else:
            st.markdown("- No qualifications defined")

        # Display required competencies
        st.markdown("#### Required Competencies")
        competencies = job_data.get("required_competencies", [])
        if competencies:
            for comp in competencies:
                st.markdown(f"- {comp}")
        else:
            st.markdown("- No competencies defined")

    # Button to save directly to database (always visible)
    if st.button("💾 Simpan ke Database", type="primary"):
        try:
            # Get the current data from session state (may have been edited in View mode)
            current_profile = st.session_state.generated_profile
            # Use the current values from the profile
            vacancy_data = {
                "role_name": role_name,
                "job_level": job_level,
                "role_purpose": current_profile.get('role_purpose', ''),
                "key_responsibilities": current_profile.get('key_responsibilities', []),
                "qualifications": current_profile.get('qualifications', []),
                "required_competencies": current_profile.get('required_competencies', [])
            }
            vacancy_id = save_job_vacancy(
                role_name=vacancy_data["role_name"],
                job_level=vacancy_data["job_level"],
                role_purpose=vacancy_data["role_purpose"],
                key_responsibilities=vacancy_data["key_responsibilities"],
                qualifications=vacancy_data["qualifications"],
                required_competencies=vacancy_data["required_competencies"]
            )

            if vacancy_id:
                st.toast(f"✅ Lowongan (ID: {vacancy_id}) berhasil disimpan!", icon="🎉")
                # Set state to show reset button
                st.session_state.show_reset_button = True
            else:
                st.error("❌ Gagal menyimpan lowongan ke database")
        except Exception as e:
            st.error(f"Gagal menyimpan ke database: {str(e)}")

    # Show reset button if save was successful
    if 'show_reset_button' in st.session_state and st.session_state.show_reset_button:
        if st.button("Buat Lowongan Baru Lagi", type="secondary"):
            # Clear the session state to reset the form
            del st.session_state.generated_profile
            del st.session_state.show_reset_button
            if 'edit_mode' in st.session_state:
                del st.session_state.edit_mode
            st.rerun()

# Add instructions
with st.expander("📋 Instructions"):
    st.markdown("""
    1. Enter the role name and select the job level
    2. Select main competencies from the multiselect (optional)
    3. Provide any additional context about the role (optional)
    4. Click "Generate Job Profile with AI" to create the content
    5. Review and edit the generated content as needed
    6. Click "Simpan ke Database" to save the job description in the database
    """)