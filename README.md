# Talent Intelligence Dashboard

A modern HR analytics dashboard built with Streamlit for talent matching, job profile generation, and employee analytics.

## Features

### 1. Talent Matching Engine
Match employees to job positions using competency-based algorithms. Supports multiple benchmarking modes:
- Individual employee position recommendations
- Manual benchmark comparisons
- Filter-based talent search
- High performer profiling

### 2. AI Job Generator
Generate professional job descriptions using AI:
- Role purpose & responsibilities
- Required qualifications
- Competency requirements with context
- Export to JSON, text, or markdown
- AI-powered refinement

### 3. Employee Profile Viewer
Comprehensive employee analytics:
- Competency radar charts
- Performance history tracking
- PAPI work style analysis (20 scales)
- Career journey visualization
- Personalized development recommendations

## Tech Stack

- **Frontend:** Streamlit
- **Database:** PostgreSQL
- **AI:** Google Gemini API
- **Charts:** Plotly
- **Backend:** Python 3.x

## Installation

1. Clone the repository
```bash
git clone https://github.com/engkinandatama/talent-intelligence-dashboard.git
cd talent-intelligence-dashboard
```

2. Create virtual environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies
```bash
pip install -r requirements.txt
```

4. Set up environment variables
Create `.streamlit/secrets.toml`:
```toml
GEMINI_API_KEY = "your-gemini-api-key"

[database]
host = "your-db-host"
port = 5432
database = "your-database-name"
user = "your-username"
password = "your-password"
```

5. Run the application
```bash
streamlit run app.py
```

## Project Structure

```
talent-intelligence-dashboard/
├── app.py                    # Main dashboard
├── pages/
│   ├── 1_Talent_Matching.py  # Talent matching engine
│   ├── 2_Job_Generator.py    # AI job generator
│   └── 3_Employee_Profile.py # Employee analytics
├── core/
│   ├── db.py                 # Database connection
│   ├── matching.py           # Matching algorithms
│   ├── job_generator.py      # Job generation logic
│   └── utils.py              # Utility functions
├── components/               # Reusable UI components
└── docs/                     # Documentation

```

## Database Schema

Required tables:
- `employees` - Employee master data
- `competencies` - Competency definitions
- `employee_competencies` - Employee competency scores
- `positions` - Position master data
- `role_competency_mapping` - Required competencies per role
- `performance_history` - Historical performance data
- `papi_profiles` - PAPI assessment results
- `job_vacancies` - Generated job postings

See `docs/SQL-scheme.md` for detailed schema.

## Usage

### Talent Matching
1. Select Mode A (specific employees) or Mode B (filtered search)
2. Choose benchmark criteria
3. Click "Run Talent Match"
4. Review ranked results with match scores

### Job Generator
1. Enter role name and level
2. Select key competencies
3. Click "Generate Job Profile with AI"
4. Review and refine as needed
5. Save to database or export

### Employee Profile
1. Select employee from dropdown
2. View comprehensive analytics across multiple tabs
3. Explore competency breakdowns and recommendations
