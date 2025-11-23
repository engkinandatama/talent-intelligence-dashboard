import streamlit as st
import google.generativeai as genai
from core.job_generator import save_job_vacancy
import json
from datetime import datetime

# Page configuration
st.set_page_config(
    page_title="AI Job Generator",
    page_icon="🤖",
    layout="wide"
)

st.title("🤖 AI Job Role Generator")
st.markdown("""
Generate comprehensive job descriptions using AI. Enter the role name and level, 
and our AI will create a complete job profile with responsibilities, qualifications, and required competencies.
""")

# Initialize session state for generated content
if 'generated_job' not in st.session_state:
    st.session_state.generated_job = None

# Input fields
col1, col2 = st.columns(2)
with col1:
    role_name = st.text_input("Role Name", placeholder="e.g., Senior Software Engineer")
with col2:
    job_level = st.selectbox("Job Level", 
        ["Entry Level", "Mid Level", "Senior Level", "Lead Level", "Manager", "Director", "VP"])

# Additional context
job_context = st.text_area("Additional Context (Optional)", 
    placeholder="e.g., Team size, industry, specific requirements, company culture...",
    height=150)

# Generate button
if st.button("🚀 Generate Job Description with AI", type="primary", disabled=not role_name):
    with st.spinner("Generating job description..."):
        try:
            # Configure API (this will need to be set up in secrets.toml)
            api_key = st.secrets["GEMINI_API_KEY"]
            genai.configure(api_key=api_key)
            
            # Initialize the model
            model = genai.GenerativeModel('gemini-2.5-flash-lite')
            
            # Create a detailed prompt for the AI
            prompt = f"""
            Generate a comprehensive job description for a {job_level} {role_name}. 

            Context: {job_context if job_context else 'No additional context provided.'}

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
            st.session_state.generated_job = job_data
            
            st.success("Job description generated successfully!")
            
        except Exception as e:
            st.error(f"Error generating job description: {str(e)}")
            st.session_state.generated_job = None

# Display generated content if available
if st.session_state.generated_job:
    job_data = st.session_state.generated_job
    
    st.subheader("Generated Job Description")
    
    # Display role purpose
    st.markdown("### Role Purpose")
    st.markdown(job_data.get("role_purpose", "No role purpose provided."))
    
    # Display key responsibilities
    st.markdown("### Key Responsibilities")
    responsibilities = job_data.get("key_responsibilities", [])
    if responsibilities:
        for i, resp in enumerate(responsibilities, 1):
            st.markdown(f"{i}. {resp}")
    
    # Display qualifications
    st.markdown("### Qualifications")
    qualifications = job_data.get("qualifications", [])
    if qualifications:
        for i, qual in enumerate(qualifications, 1):
            st.markdown(f"{i}. {qual}")
    
    # Display required competencies
    st.markdown("### Required Competencies")
    competencies = job_data.get("required_competencies", [])
    if competencies:
        for i, comp in enumerate(competencies, 1):
            st.markdown(f"{i}. {comp}")

    # Save to database button
    if st.button("💾 Save to Database", type="secondary"):
        vacancy_id = save_job_vacancy(
            role_name=role_name,
            job_level=job_level,
            role_purpose=job_data.get("role_purpose"),
            key_responsibilities=job_data.get("key_responsibilities", []),
            qualifications=job_data.get("qualifications", []),
            required_competencies=job_data.get("required_competencies", [])
        )

        if vacancy_id:
            st.success(f"Job description saved successfully with ID: {vacancy_id}")
        else:
            st.error("Failed to save job description to database")

# Add instructions
with st.expander("📋 Instructions"):
    st.markdown("""
    1. Enter the role name and select the job level
    2. Provide any additional context about the role (optional)
    3. Click "Generate Job Description with AI" to create the content
    4. Review the generated content
    5. Click "Save to Database" to store the job description in the database
    """)