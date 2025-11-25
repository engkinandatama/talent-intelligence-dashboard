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

# Dark Theme CSS
st.markdown("""
<style>
    .main {
        background-color: #0F1419;
    }
    
    h1, h2, h3, h4 {
        color: #4A90E2;
    }
    
    .stForm {
        background: rgba(26, 35, 50, 0.4);
        padding: 2rem;
        border-radius: 12px;
        border: 1px solid rgba(74, 144, 226, 0.2);
    }
    
    [data-testid="stExpanderHeader"] {
        background: rgba(26, 35, 50, 0.6);
        border-radius: 8px;
    }
    
    /* Form inputs */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(74, 144, 226, 0.3);
        color: #E8EDF3;
    }
    
    /* Buttons */
    .stButton > button {
        border-radius: 8px;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

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

# --- Helper Functions for Export ---
def format_as_text(data):
    text = f"JOB DESCRIPTION: {data.get('position_name')} ({data.get('level')})\n"
    text += "=" * 50 + "\n\n"
    
    text += "ROLE PURPOSE:\n"
    text += f"{data.get('role_purpose')}\n\n"
    
    text += "KEY RESPONSIBILITIES:\n"
    for i, item in enumerate(data.get('key_responsibilities', []), 1):
        text += f"{i}. {item}\n"
    text += "\n"
    
    text += "QUALIFICATIONS:\n"
    quals = data.get('qualifications', {})
    if isinstance(quals, dict):
        text += f"Education: {quals.get('education', 'N/A')}\n"
        text += f"Experience: {quals.get('experience', 'N/A')}\n"
        text += "Skills:\n"
        for skill in quals.get('skills', []):
            text += f"- {skill}\n"
    else:
        text += str(quals)
    text += "\n"
    
    text += "REQUIRED COMPETENCIES:\n"
    for comp in data.get('required_competencies', []):
        if isinstance(comp, dict):
            text += f"{comp.get('name')}: {comp.get('description')}\n"
        else:
            text += f"- {comp}\n"
            
    return text

def format_as_markdown(data):
    md = f"# Job Description: {data.get('position_name')}\n"
    md += f"**Level:** {data.get('level')}\n\n"
    
    md += "## 📌 Role Purpose\n"
    md += f"{data.get('role_purpose')}\n\n"
    
    md += "## ▸ Key Responsibilities\n"
    for item in data.get('key_responsibilities', []):
        md += f"- {item}\n"
    md += "\n"
    
    md += "## △ Qualifications\n"
    quals = data.get('qualifications', {})
    if isinstance(quals, dict):
        md += f"- **Education:** {quals.get('education', 'N/A')}\n"
        md += f"- **Experience:** {quals.get('experience', 'N/A')}\n"
        md += "- **Skills:** " + ", ".join([f"`{s}`" for s in quals.get('skills', [])]) + "\n"
    else:
        md += str(quals)
    md += "\n"
    
    md += "## ◆ Required Competencies\n"
    for comp in data.get('required_competencies', []):
        if isinstance(comp, dict):
            md += f"### {comp.get('name')}\n"
            md += f"{comp.get('description')}\n"
        else:
            md += f"- {comp}\n"
            
    return md

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
    submitted = st.form_submit_button("▸ Generate Job Profile with AI", type="primary")

# Handle form submission
if submitted:
    # Validation
    errors = []
    
    if not role_name:
        errors.append("❌ Role Name is required")
    elif len(role_name) < 3:
        errors.append("❌ Role Name must be at least 3 characters")
    
    if len(selected_competencies) > 10:
        errors.append("⚠️ Maximum 10 competencies recommended")
    
    if errors:
        for error in errors:
            st.error(error)
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
You are an expert HR consultant.

TASK: Create a **concise, high-impact** job description for:
- **Position:** {role_name}
- **Level:** {job_level}
- **Key Competencies:** {competency_context}
- **Context:** {job_context if job_context else 'Standard corporate environment'}

INSTRUCTIONS:
1. **Tone**: Professional, punchy, and direct. Avoid fluff.
2. **Role Purpose**: 2-3 powerful sentences defining the role's core value.
3. **Qualifications**: Be specific. Don't just list "Degree"; say "Bachelor's in X required". Don't just say "Coding"; say "Proficiency in Python/SQL".
4. **Competencies**: Don't just state the level. Explain **briefly** how this skill is applied in THIS specific role.

REQUIRED OUTPUT (JSON format):
{{
  "position_name": "{role_name}",
  "level": "{job_level}",
  "role_purpose": "Strategic summary of the role's purpose.",
  "key_responsibilities": [
    "Action-oriented responsibility 1",
    "Action-oriented responsibility 2",
    "... (6-8 items)"
  ],
  "qualifications": {{
    "education": "Specific degree requirement (e.g., 'Bachelor's in Computer Science or equivalent')",
    "experience": "Specific experience requirement (e.g., '5+ years in product management')",
    "skills": [
      "Hard Skill 1",
      "Hard Skill 2",
      "..."
    ]
  }},
  "required_competencies": [
    {{
      "name": "Competency Name",
      "description": "Brief, specific explanation of how this skill is applied in this role (1 sentence)."
    }},
    "... (6-8 items)"
  ]
}}

IMPORTANT:
- Return ONLY valid JSON.
- NO Success Metrics.
- Competencies must have 'description' explaining the application, NOT just 'level'.
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

    # Action buttons at top (2 columns: Edit | Save)
    st.markdown("### ◆ Generated Job Profile")
    col1, col2 = st.columns(2)
    
    with col1:
        st.button(
            "✏️ Edit Profile" if not st.session_state.edit_mode else "❌ Cancel Edit",
            width="stretch",
            on_click=toggle_edit_mode
        )
    
    with col2:
        save_btn_top = st.button("▪ Save to Database", type="primary", width="stretch", key="save_top")

    if st.session_state.edit_mode:
        # --- EDIT MODE ---
        st.subheader("Generated Job Description (Editing)")
        with st.form("edit_profile_form"):
            # Convert responsibilities and competencies to strings
            responsibilities_str = "\n".join(job_data.get("key_responsibilities", []))
            
            # Handle qualifications (now a dict with strings/lists)
            quals = job_data.get("qualifications", {})
            qual_edu = quals.get("education", "")
            qual_exp = quals.get("experience", "")
            qual_skills = "\n".join(quals.get("skills", []))
            
            # Handle competencies (list of dicts)
            comp_list = job_data.get("required_competencies", [])
            comp_str_list = []
            for c in comp_list:
                comp_str_list.append(f"{c.get('name')}: {c.get('description')}")
            competencies_str = "\n".join(comp_str_list)

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

            st.markdown("#### Qualifications")
            edited_edu = st.text_input("Education", value=qual_edu)
            edited_exp = st.text_input("Experience", value=qual_exp)
            edited_skills = st.text_area(
                "Skills",
                value=qual_skills,
                height=100,
                help="Separate each skill with a new line"
            )

            edited_competencies = st.text_area(
                "Required Competencies (Format: Name: Description)",
                value=competencies_str,
                height=200,
                help="Format: Competency Name: Description"
            )

            submitted = st.form_submit_button("▪ Save Changes", type="primary")
            if submitted:
                # Update session state with edited data
                st.session_state.generated_profile['role_purpose'] = edited_role_purpose
                st.session_state.generated_profile['key_responsibilities'] = [item.strip() for item in edited_responsibilities.split('\n') if item.strip()]
                
                # Update qualifications
                st.session_state.generated_profile['qualifications'] = {
                    "education": edited_edu,
                    "experience": edited_exp,
                    "skills": [item.strip() for item in edited_skills.split('\n') if item.strip()]
                }
                
                # Parse competencies back to dicts
                new_comps = []
                for line in edited_competencies.split('\n'):
                    if line.strip():
                        parts = line.split(':', 1)
                        if len(parts) >= 2:
                            new_comps.append({"name": parts[0].strip(), "description": parts[1].strip()})
                        else:
                            new_comps.append({"name": line.strip(), "description": ""})
                st.session_state.generated_profile['required_competencies'] = new_comps

                st.session_state.edit_mode = False  # Return to view mode
                st.toast("✅ Perubahan disimpan sementara.", icon="👍")
                st.rerun()
    else:
        # --- VIEW MODE (Collapsible Sections) ---
        
        # Role Purpose
        with st.expander("📌 Role Purpose", expanded=True):
            st.markdown(job_data.get("role_purpose", "_No purpose defined_"))
        
        # Key Responsibilities
        with st.expander("🎯 Key Responsibilities", expanded=True):
            responsibilities = job_data.get("key_responsibilities", [])
            if responsibilities:
                for i, resp in enumerate(responsibilities, 1):
                    st.markdown(f"{i}. {resp}")
            else:
                st.info("No responsibilities defined")
        
        # Qualifications
        with st.expander("🎓 Qualifications", expanded=True):
            qualifications = job_data.get("qualifications", {})
            
            if isinstance(qualifications, dict):
                st.markdown(f"**📚 Education:** {qualifications.get('education', 'N/A')}")
                st.markdown(f"**💼 Experience:** {qualifications.get('experience', 'N/A')}")
                
                st.markdown("**⚡ Key Skills:**")
                skills = qualifications.get('skills', [])
                if skills:
                    # Display skills as tags/pills
                    st.markdown(" ".join([f"`{skill}`" for skill in skills]))
                else:
                    st.markdown("_No specific skills listed_")
            else:
                # Fallback for old format
                st.write(qualifications)
        
        # Required Competencies (Structured Table View) - FEATURE 2
        with st.expander("💪 Required Competencies", expanded=True):
            competencies = job_data.get("required_competencies", [])
            if competencies:
                # Display in structured table format
                st.markdown("**Competency Requirements:**")
                
                # Create a structured table
                comp_data = []
                for comp in competencies:
                    if isinstance(comp, dict):
                        comp_data.append({
                            "Competency": comp.get('name', 'Unknown'),
                            "Application Context": comp.get('description', 'N/A')
                        })
                    else:
                        comp_data.append({
                            "Competency": str(comp),
                            "Application Context": "N/A"
                        })
                
                if comp_data:
                    # Display as formatted table
                    for idx, comp in enumerate(comp_data, 1):
                        st.markdown(f"**{idx}. {comp['Competency']}**")
                        st.markdown(f"   └─ *{comp['Application Context']}*")
                        if idx < len(comp_data):
                            st.markdown("")
            else:
                st.info("No competencies defined")

    # --- PHASE 3: REVISION & EXPORT ---
    st.divider()
    
    # 1. Revision Workflow
    with st.expander("⚡ Request Revisions / Refine"):
        st.info("Want to adjust the output? Tell the AI what to change.")
        refinement_instructions = st.text_area(
            "Instructions for AI",
            placeholder="e.g., Make the tone more senior, emphasize leadership skills, remove the requirement for X..."
        )
        if st.button("⟳ Refine with AI"):
            if not refinement_instructions:
                st.warning("Please enter instructions first.")
            else:
                with st.spinner("Refining job profile..."):
                    try:
                        # Configure API
                        api_key = st.secrets["GEMINI_API_KEY"]
                        genai.configure(api_key=api_key)
                        model = genai.GenerativeModel('gemini-2.5-flash-lite')
                        
                        # Create refinement prompt
                        refinement_prompt = f"""
You are an expert HR consultant.
TASK: Refine the following job description based on user feedback.

CURRENT PROFILE (JSON):
{json.dumps(job_data)}

USER FEEDBACK:
"{refinement_instructions}"

INSTRUCTIONS:
1. Apply the user's feedback strictly.
2. Maintain the same JSON structure.
3. Keep the "Concise, Punchy, Direct" tone.

REQUIRED OUTPUT (JSON format):
(Same structure as before)
"""
                        response = model.generate_content(refinement_prompt)
                        content = response.text.strip()
                        if content.startswith("```json"):
                            content = content[7:]
                        if content.endswith("```"):
                            content = content[:-3]
                            
                        new_job_data = json.loads(content)
                        st.session_state.generated_profile = new_job_data
                        st.toast("✓ Profile refined successfully!", icon="◆")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Refinement failed: {str(e)}")

    # 2. Export Functionality
    st.markdown("### ↓ Export Options")
    col_exp1, col_exp2, col_exp3 = st.columns(3)
    
    with col_exp1:
        st.download_button(
            label="□ Download JSON",
            data=json.dumps(job_data, indent=2),
            file_name=f"{job_data.get('position_name', 'job')}_profile.json",
            mime="application/json",
            width="stretch"
        )
        
    with col_exp2:
        st.download_button(
            label="□ Download Text",
            data=format_as_text(job_data),
            file_name=f"{job_data.get('position_name', 'job')}_profile.txt",
            mime="text/plain",
            width="stretch"
        )
        
    with col_exp3:
        st.download_button(
            label="📑 Download Markdown",
            data=format_as_markdown(job_data),
            file_name=f"{job_data.get('position_name', 'job')}_profile.md",
            mime="text/markdown",
            width="stretch"
        )

    # Save button logic (handles both top and bottom buttons)
    if save_btn_top or st.button("▪ Save to Database", type="primary", width="stretch", key="save_bottom"):
        try:
            # Get the current data from session state (may have been edited in View mode)
            current_profile = st.session_state.generated_profile
            
            # Use the current values from the profile
            vacancy_data = {
                "role_name": role_name,
                "job_level": job_level,
                "role_purpose": current_profile.get('role_purpose', ''),
                "key_responsibilities": current_profile.get('key_responsibilities', []),
                "qualifications": current_profile.get('qualifications', {}), 
                "required_competencies": current_profile.get('required_competencies', []),
                "success_metrics": []
            }
            
            vacancy_id = save_job_vacancy(
                role_name=vacancy_data["role_name"],
                job_level=vacancy_data["job_level"],
                role_purpose=vacancy_data["role_purpose"],
                key_responsibilities=vacancy_data["key_responsibilities"],
                qualifications=vacancy_data["qualifications"], 
                required_competencies=vacancy_data["required_competencies"],
                success_metrics=vacancy_data["success_metrics"]
            )

            if vacancy_id:
                st.toast(f"✅ Vacancy (ID: {vacancy_id}) successfully saved!", icon="🎉")
                # Store vacancy_id for talent matching link - FEATURE 1
                st.session_state.last_saved_vacancy_id = vacancy_id
                st.session_state.show_reset_button = True
            else:
                st.error("❌ Failed to save vacancy to database")
        except Exception as e:
            st.error(f"Failed to save to database: {str(e)}")

    # Show action buttons if save was successful - FEATURE 1
    if 'show_reset_button' in st.session_state and st.session_state.show_reset_button:
        st.success("✅ Job vacancy saved successfully!")
        
        col_action1, col_action2 = st.columns(2)
        
        with col_action1:
            # Link to Talent Matching - FEATURE 1
            if st.button("▸ Find Matching Talents", type="primary", width="stretch"):
                # Store vacancy info for talent matching page
                if 'last_saved_vacancy_id' in st.session_state:
                    st.session_state.talent_match_vacancy_id = st.session_state.last_saved_vacancy_id
                    st.session_state.talent_match_role_name = role_name
                st.switch_page("pages/1_Talent_Matching.py")
        
        with col_action2:
            if st.button("□ Create Another Job", type="secondary", width="stretch"):
                # Clear the session state to reset the form
                del st.session_state.generated_profile
                del st.session_state.show_reset_button
                if 'edit_mode' in st.session_state:
                    del st.session_state.edit_mode
                if 'last_saved_vacancy_id' in st.session_state:
                    del st.session_state.last_saved_vacancy_id
                st.rerun()
            qualifications = job_data.get("qualifications", {})
            
            if isinstance(qualifications, dict):
                st.markdown(f"**📚 Education:** {qualifications.get('education', 'N/A')}")
                st.markdown(f"**💼 Experience:** {qualifications.get('experience', 'N/A')}")
                
                st.markdown("**⚡ Key Skills:**")
                skills = qualifications.get('skills', [])
                if skills:
                    # Display skills as tags/pills
                    st.markdown(" ".join([f"`{skill}`" for skill in skills]))
                else:
                    st.markdown("_No specific skills listed_")
            else:
                # Fallback for old format
                st.write(qualifications)
        
        # Required Competencies (Structured Table View) - FEATURE 2
        with st.expander("💪 Required Competencies", expanded=True):
            competencies = job_data.get("required_competencies", [])
            if competencies:
                # Display in structured table format
                st.markdown("**Competency Requirements:**")
                
                # Create a structured table
                comp_data = []
                for comp in competencies:
                    if isinstance(comp, dict):
                        comp_data.append({
                            "Competency": comp.get('name', 'Unknown'),
                            "Application Context": comp.get('description', 'N/A')
                        })
                    else:
                        comp_data.append({
                            "Competency": str(comp),
                            "Application Context": "N/A"
                        })
                
                if comp_data:
                    # Display as formatted table
                    for idx, comp in enumerate(comp_data, 1):
                        st.markdown(f"**{idx}. {comp['Competency']}**")
                        st.markdown(f"   └─ *{comp['Application Context']}*")
                        if idx < len(comp_data):
                            st.markdown("")
            else:
                st.info("No competencies defined")

    # --- PHASE 3: REVISION & EXPORT ---
    st.divider()
    
    # 1. Revision Workflow
    with st.expander("⚡ Request Revisions / Refine"):
        st.info("Want to adjust the output? Tell the AI what to change.")
        refinement_instructions = st.text_area(
            "Instructions for AI",
            placeholder="e.g., Make the tone more senior, emphasize leadership skills, remove the requirement for X..."
        )
        if st.button("⟳ Refine with AI"):
            if not refinement_instructions:
                st.warning("Please enter instructions first.")
            else:
                with st.spinner("Refining job profile..."):
                    try:
                        # Configure API
                        api_key = st.secrets["GEMINI_API_KEY"]
                        genai.configure(api_key=api_key)
                        model = genai.GenerativeModel('gemini-2.5-flash-lite')
                        
                        # Create refinement prompt
                        refinement_prompt = f"""
You are an expert HR consultant.
TASK: Refine the following job description based on user feedback.

CURRENT PROFILE (JSON):
{json.dumps(job_data)}

USER FEEDBACK:
"{refinement_instructions}"

INSTRUCTIONS:
1. Apply the user's feedback strictly.
2. Maintain the same JSON structure.
3. Keep the "Concise, Punchy, Direct" tone.

REQUIRED OUTPUT (JSON format):
(Same structure as before)
"""
                        response = model.generate_content(refinement_prompt)
                        content = response.text.strip()
                        if content.startswith("```json"):
                            content = content[7:]
                        if content.endswith("```"):
                            content = content[:-3]
                            
                        new_job_data = json.loads(content)
                        st.session_state.generated_profile = new_job_data
                        st.toast("✓ Profile refined successfully!", icon="◆")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Refinement failed: {str(e)}")

    # 2. Export Functionality
    st.markdown("### ↓ Export Options")
    col_exp1, col_exp2, col_exp3 = st.columns(3)
    
    with col_exp1:
        st.download_button(
            label="□ Download JSON",
            data=json.dumps(job_data, indent=2),
            file_name=f"{job_data.get('position_name', 'job')}_profile.json",
            mime="application/json",
            width="stretch"
        )
        
    with col_exp2:
        st.download_button(
            label="□ Download Text",
            data=format_as_text(job_data),
            file_name=f"{job_data.get('position_name', 'job')}_profile.txt",
            mime="text/plain",
            width="stretch"
        )
        
    with col_exp3:
        st.download_button(
            label="📑 Download Markdown",
            data=format_as_markdown(job_data),
            file_name=f"{job_data.get('position_name', 'job')}_profile.md",
            mime="text/markdown",
            width="stretch"
        )

    # Save button logic (handles both top and bottom buttons)
    if save_btn_top or st.button("▪ Save to Database", type="primary", width="stretch", key="save_bottom"):
        try:
            # Get the current data from session state (may have been edited in View mode)
            current_profile = st.session_state.generated_profile
            
            # Use the current values from the profile
            vacancy_data = {
                "role_name": role_name,
                "job_level": job_level,
                "role_purpose": current_profile.get('role_purpose', ''),
                "key_responsibilities": current_profile.get('key_responsibilities', []),
                "qualifications": current_profile.get('qualifications', {}), 
                "required_competencies": current_profile.get('required_competencies', []),
                "success_metrics": []
            }
            
            vacancy_id = save_job_vacancy(
                role_name=vacancy_data["role_name"],
                job_level=vacancy_data["job_level"],
                role_purpose=vacancy_data["role_purpose"],
                key_responsibilities=vacancy_data["key_responsibilities"],
                qualifications=vacancy_data["qualifications"], 
                required_competencies=vacancy_data["required_competencies"],
                success_metrics=vacancy_data["success_metrics"]
            )

            if vacancy_id:
                st.toast(f"✅ Vacancy (ID: {vacancy_id}) successfully saved!", icon="🎉")
                # Store vacancy_id for talent matching link - FEATURE 1
                st.session_state.last_saved_vacancy_id = vacancy_id
                st.session_state.show_reset_button = True
            else:
                st.error("❌ Failed to save vacancy to database")
        except Exception as e:
            st.error(f"Failed to save to database: {str(e)}")

    # Show action buttons if save was successful - FEATURE 1
    if 'show_reset_button' in st.session_state and st.session_state.show_reset_button:
        st.success("✅ Job vacancy saved successfully!")
        
        col_action1, col_action2 = st.columns(2)
        
        with col_action1:
            # Link to Talent Matching - FEATURE 1
            if st.button("▸ Find Matching Talents", type="primary", width="stretch"):
                # Store vacancy info for talent matching page
                if 'last_saved_vacancy_id' in st.session_state:
                    st.session_state.talent_match_vacancy_id = st.session_state.last_saved_vacancy_id
                    st.session_state.talent_match_role_name = role_name
                st.switch_page("pages/1_Talent_Matching.py")
        
        with col_action2:
            if st.button("□ Create Another Job", type="secondary", width="stretch"):
                # Clear the session state to reset the form
                del st.session_state.generated_profile
                del st.session_state.show_reset_button
                if 'edit_mode' in st.session_state:
                    del st.session_state.edit_mode
                if 'last_saved_vacancy_id' in st.session_state:
                    del st.session_state.last_saved_vacancy_id
                st.rerun()

# Add instructions
with st.expander("≡ Instructions"):
    st.markdown("""
    1. Enter the role name and select the job level
    2. Select main competencies from the multiselect (optional)
    3. Provide any additional context about the role (optional)
    4. Click "Generate Job Profile with AI" to create the content
    5. Review and edit the generated content as needed
    6. Use "Request Revisions" to refine the content with AI
    7. Download the profile in your preferred format
    8. Click "Save to Database" to save the job description in the database
    9. After saving, click "Find Matching Talents" to find candidates
    """)

# Footer
st.markdown('<br>', unsafe_allow_html=True)
st.markdown("""
<div style='text-align: center; color: #6B7B94; padding: 2rem 0;'>
    <small>Talent Intelligence Dashboard © 2025. All rights reserved.</small>
</div>
""", unsafe_allow_html=True)