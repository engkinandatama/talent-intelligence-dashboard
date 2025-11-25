import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from core.db import get_engine
import numpy as np

# Page config
st.set_page_config(
    page_title="Employee Profile",
    page_icon="👤",
    layout="wide"
)

# Dark RPG Theme CSS
st.markdown("""
<style>
    /* Main Background */
    .main {
        background: linear-gradient(135deg, #0F1419 0%, #1a2332 100%);
    }
    
    /* OVERRIDE STREAMLIT DEFAULT CONTAINERS */
    /* Main vertical blocks - THESE should have background */
    [data-testid="stVerticalBlock"] > [style*="flex-direction: column;"] > [data-testid="stVerticalBlock"] {
        background: linear-gradient(135deg, rgba(26, 35, 50, 0.5) 0%, rgba(37, 52, 71, 0.5) 100%) !important;
        border: 1px solid rgba(74, 144, 226, 0.2) !important;
        border-radius: 16px !important;
        padding: 0 !important;
        margin-bottom: 1.5rem !important;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3) !important;
        backdrop-filter: blur(10px) !important;
        overflow: visible !important;
    }
    
    /* Remove borders from columns inside */
    div[data-testid="column"] {
        border: none !important;
        background: transparent !important;
    }
    
    /* Override selectbox container */
    div[data-baseweb="select"] {
        border: none !important;
    }
    
    /* Remove metric container borders */
    div[data-testid="metric-container"] {
        border: none !important;
        background: transparent !important;
    }
    
    /* Profile Card - NOW TRANSPARENT (just wrapper) */
    .profile-card {
        background: transparent !important;
        border: none !important;
        border-radius: 0px;
        padding: 0;
        margin-bottom: 0;
        box-shadow: none !important;
    }
    
    /* Character Header */
    .character-header {
        display: flex;
        align-items: center;
        gap: 2rem;
        margin-bottom: 2rem;
        padding: 1.5rem;
        background: linear-gradient(135deg, rgba(26, 35, 50, 0.4) 0%, rgba(37, 52, 71, 0.4) 100%);
        border-radius: 16px;
        border: 1px solid rgba(74, 144, 226, 0.1);
    }
    
    .avatar-box {
        width: 120px;
        height: 120px;
        background: linear-gradient(135deg, #4A90E2, #51CF66);
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 3rem;
        border: 4px solid rgba(255, 255, 255, 0.2);
        box-shadow: 0 0 30px rgba(74, 144, 226, 0.5);
    }
    
    .character-info h1 {
        color: #E8EDF3;
        font-size: 2.5rem;
        margin: 0;
        text-shadow: 0 2px 10px rgba(74, 144, 226, 0.5);
    }
    
    .character-title {
        color: #4A90E2;
        font-size: 1.2rem;
        margin-top: 0.5rem;
    }
    
    /* HP Bar */
    .hp-bar-container {
        background: rgba(0, 0, 0, 0.3);
        border-radius: 10px;
        height: 30px;
        overflow: visible;
        position: relative;
        border: none;
    }
    
    .hp-bar {
        height: 100%;
        background: linear-gradient(90deg, #ff6b6b, #51cf66);
        transition: width 0.5s ease;
        box-shadow: 0 0 20px rgba(81, 207, 102, 0.6);
        border-radius: 10px;
    }
    
    .hp-text {
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        color: white;
        font-weight: bold;
        text-shadow: 0 2px 4px rgba(0,0,0,0.8);
        z-index: 10;
    }
    
    /* Stat Box */
    .stat-box {
        background: linear-gradient(135deg, rgba(26, 35, 50, 0.6) 0%, rgba(37, 52, 71, 0.6) 100%);
        border: 1px solid rgba(74, 144, 226, 0.2);
        border-radius: 12px;
        padding: 1.5rem;
        text-align: center;
        transition: transform 0.2s;
        backdrop-filter: blur(5px);
    }
    
    .stat-box:hover {
        transform: translateY(-5px);
        border-color: rgba(74, 144, 226, 0.5);
    }
    
    .stat-label {
        color: #8B9DB8;
        font-size: 0.9rem;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    .stat-value {
        color: #51CF66;
        font-size: 2.5rem;
        font-weight: bold;
        margin: 0.5rem 0;
        text-shadow: 0 2px 10px rgba(81, 207, 102, 0.5);
    }
    
    /* Badge */
    .badge {
        display: inline-block;
        background: linear-gradient(135deg, #4A90E2, #51CF66);
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        margin: 0.25rem;
        font-size: 0.9rem;
        font-weight: 600;
        box-shadow: 0 4px 12px rgba(74, 144, 226, 0.4);
    }
    
    /* Section Title */
    .section-title {
        color: #4A90E2;
        font-size: 1.5rem;
        font-weight: 600;
        margin-bottom: 1rem;
        text-transform: uppercase;
        letter-spacing: 2px;
    }
    
    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background: transparent;
        border-bottom: 1px solid rgba(74, 144, 226, 0.2);
    }
    
    .stTabs [data-baseweb="tab"] {
        background: rgba(26, 35, 50, 0.4);
        border: 1px solid rgba(74, 144, 226, 0.2);
        border-radius: 8px 8px 0 0;
        padding: 0.5rem 1rem;
    }
    
    .stTabs [aria-selected="true"] {
        background: rgba(74, 144, 226, 0.3);
        border-bottom-color: transparent;
    }
</style>
""", unsafe_allow_html=True)

# Database connection
@st.cache_resource
def get_db_engine():
    return get_engine()

engine = get_db_engine()

# Data loading functions
@st.cache_data(ttl=300)
def load_employee_list():
    query = """
    SELECT 
        e.employee_id,
        e.fullname,
        pos.name as position_name,
        dept.name as department_name,
        g.name as grade_name
    FROM employees e
    LEFT JOIN dim_positions pos ON e.position_id = pos.position_id
    LEFT JOIN dim_departments dept ON e.department_id = dept.department_id
    LEFT JOIN dim_grades g ON e.grade_id = g.grade_id
    ORDER BY e.fullname
    """
    with engine.connect() as conn:
        return pd.read_sql(query, conn)

@st.cache_data(ttl=300)
def load_employee_profile(employee_id):
    """Load complete employee profile data"""
    
    # Basic info
    basic_query = """
    SELECT 
        e.employee_id,
        e.fullname,
        pos.name as position_name,
        dept.name as department_name,
        div.name as division_name,
        g.name as grade_name,
        edu.name as education_name,
        e.years_of_service_months
    FROM employees e
    LEFT JOIN dim_positions pos ON e.position_id = pos.position_id
    LEFT JOIN dim_departments dept ON e.department_id = dept.department_id
    LEFT JOIN dim_divisions div ON e.division_id = div.division_id
    LEFT JOIN dim_grades g ON e.grade_id = g.grade_id
    LEFT JOIN dim_education edu ON e.education_id = edu.education_id
    WHERE e.employee_id = %s
    """
    
    # Performance
    perf_query = """
    SELECT rating
    FROM performance_yearly
    WHERE employee_id = %s
    ORDER BY year DESC
    LIMIT 1
    """
    
    # Competencies
    comp_query = """
    SELECT 
        cp.pillar_label,
        cy.score
    FROM competencies_yearly cy
    JOIN dim_competency_pillars cp ON cy.pillar_code = cp.pillar_code
    WHERE cy.employee_id = %s
      AND cy.year = (SELECT MAX(year) FROM competencies_yearly)
    ORDER BY cy.score DESC
    """
    
    # Cognitive
    cog_query = """
    SELECT iq, gtq, tiki, pauli, faxtor, mbti, disc
    FROM profiles_psych
    WHERE employee_id = %s
    """
    
    # Strengths
    strengths_query = """
    SELECT theme, rank
    FROM strengths
    WHERE employee_id = %s
    ORDER BY rank
    LIMIT 5
    """
    
    with engine.connect() as conn:
        basic_df = pd.read_sql(basic_query, conn, params=(employee_id,))
        perf_df = pd.read_sql(perf_query, conn, params=(employee_id,))
        comp_df = pd.read_sql(comp_query, conn, params=(employee_id,))
        cog_df = pd.read_sql(cog_query, conn, params=(employee_id,))
        strengths_df = pd.read_sql(strengths_query, conn, params=(employee_id,))
    
    return {
        'basic': basic_df.iloc[0] if not basic_df.empty else None,
        'performance': perf_df.iloc[0]['rating'] if not perf_df.empty else 0,
        'competencies': comp_df,
        'cognitive': cog_df.iloc[0] if not cog_df.empty else None,
        'strengths': strengths_df
    }

# Main UI
st.markdown('<div class="profile-card">', unsafe_allow_html=True)

# Employee selector
employees_df = load_employee_list()
employee_options = {f"{row['fullname']} - {row['position_name']}": row['employee_id'] 
                   for _, row in employees_df.iterrows()}

selected_label = st.selectbox(
    "🔍 Select Employee to View Profile",
    options=list(employee_options.keys()),
    help="Type to search by name"
)

selected_employee_id = employee_options[selected_label]

st.markdown('</div>', unsafe_allow_html=True)

# Load profile data
profile = load_employee_profile(selected_employee_id)

if profile['basic'] is None:
    st.error("Employee data not found")
    st.stop()

# Character Header
st.markdown('<div class="profile-card">', unsafe_allow_html=True)
st.markdown(f"""
<div class="character-header">
    <div class="avatar-box">👤</div>
    <div class="character-info">
        <h1>{profile['basic']['fullname']}</h1>
        <div class="character-title">{profile['basic']['position_name']}</div>
        <div style="color: #8B9DB8; margin-top: 0.5rem;">
            {profile['basic']['department_name']} • {profile['basic']['grade_name']}
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# HP Bar (Performance Rating)
rating = profile['performance']
hp_percent = (rating / 5) * 100

st.markdown('<div class="section-title">⭐ Performance Level</div>', unsafe_allow_html=True)
st.markdown(f"""
<div class="hp-bar-container">
    <div class="hp-bar" style="width: {hp_percent}%"></div>
    <div class="hp-text">RATING: {rating} / 5 ⭐ ({hp_percent:.0f}%)</div>
</div>
""", unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# Stats Row (Level, Experience, Attributes)
st.markdown('<br>', unsafe_allow_html=True)
col1, col2, col3, col4 = st.columns(4)

exp_years = profile['basic']['years_of_service_months'] / 12

with col1:
    st.markdown(f"""
    <div class="stat-box">
        <div class="stat-label">🎯 Level</div>
        <div class="stat-value">{profile['basic']['grade_name']}</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="stat-box">
        <div class="stat-label">⏳ Experience</div>
        <div class="stat-value">{exp_years:.1f}Y</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    avg_comp = profile['competencies']['score'].mean() if not profile['competencies'].empty else 0
    st.markdown(f"""
    <div class="stat-box">
        <div class="stat-label">💪 Avg Competency</div>
        <div class="stat-value">{avg_comp:.1f}</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    iq = profile['cognitive']['iq'] if profile['cognitive'] is not None else 0
    st.markdown(f"""
    <div class="stat-box">
        <div class="stat-label">🧠 Intelligence</div>
        <div class="stat-value">{iq:.0f}</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown('<br>', unsafe_allow_html=True)

# Main Content - 2 columns
col_left, col_right = st.columns([1, 1])

with col_left:
    # Competencies Radar Chart
    st.markdown('<div class="profile-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">📊 Competency Stats</div>', unsafe_allow_html=True)
    
    if not profile['competencies'].empty:
        fig_radar = go.Figure()
        
        fig_radar.add_trace(go.Scatterpolar(
            r=profile['competencies']['score'].tolist(),
            theta=profile['competencies']['pillar_label'].tolist(),
            fill='toself',
            line_color='#4A90E2',
            fillcolor='rgba(74, 144, 226, 0.3)',
            name='Current Level'
        ))
        
        # Max line (perfect 5.0)
        fig_radar.add_trace(go.Scatterpolar(
            r=[5.0] * len(profile['competencies']),
            theta=profile['competencies']['pillar_label'].tolist(),
            fill='toself',
            line=dict(color='#51CF66', dash='dash'),
            fillcolor='rgba(81, 207, 102, 0.1)',
            name='Max Level'
        ))
        
        fig_radar.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 5],
                    tickfont=dict(size=10, color='#8B9DB8'),
                    gridcolor='rgba(139, 157, 184, 0.2)'
                ),
                angularaxis=dict(
                    tickfont=dict(size=11, color='#E8EDF3')
                ),
                bgcolor='rgba(0,0,0,0)'
            ),
            showlegend=True,
            legend=dict(
                font=dict(size=10, color='#8B9DB8'),
                bgcolor='rgba(0,0,0,0)'
            ),
            height=400,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=80, r=80, t=40, b=40)
        )
        
        st.plotly_chart(fig_radar, width="stretch", config={'displayModeBar': False})
    else:
        st.info("No competency data available")
    
    st.markdown('</div>', unsafe_allow_html=True)

with col_right:
    # Cognitive Skills
    st.markdown('<div class="profile-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">🧠 Cognitive Abilities</div>', unsafe_allow_html=True)
    
    if profile['cognitive'] is not None:
        cog_data = {
            'IQ': profile['cognitive']['iq'],
            'GTQ': profile['cognitive']['gtq'],
            'TIKI': profile['cognitive']['tiki'],
            'Pauli': profile['cognitive']['pauli'],
            'Faxtor': profile['cognitive']['faxtor']
        }
        
        # Normalize to 0-100 scale for visual
        for skill, value in cog_data.items():
            if pd.notna(value):
                normalized = min((value / 150) * 100, 100)  # Assuming max ~150
                st.markdown(f"**{skill}**: {value:.0f}", unsafe_allow_html=True)
                st.progress(normalized / 100)
            else:
                st.markdown(f"**{skill}**: N/A", unsafe_allow_html=True)
                st.progress(0)
    else:
        st.info("No cognitive data available")
    
    st.markdown('</div>', unsafe_allow_html=True)

# Bottom Row - Strengths & Personality
st.markdown('<br>', unsafe_allow_html=True)
col_bottom1, col_bottom2 = st.columns([1, 1])

with col_bottom1:
    st.markdown('<div class="profile-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">🏆 Top Strengths</div>', unsafe_allow_html=True)
    
    if not profile['strengths'].empty:
        # Create single HTML block with all badges
        badges_html = '<div style="display: flex; flex-wrap: wrap; gap: 0.5rem;">'
        for _, strength in profile['strengths'].iterrows():
            badges_html += f'<span class="badge">#{strength["rank"]} {strength["theme"]}</span>'
        badges_html += '</div>'
        st.markdown(badges_html, unsafe_allow_html=True)
    else:
        st.info("No strengths data available")
    
    st.markdown('</div>', unsafe_allow_html=True)

with col_bottom2:
    st.markdown('<div class="profile-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">🎭 Personality Type</div>', unsafe_allow_html=True)
    
    if profile['cognitive'] is not None:
        mbti = profile['cognitive']['mbti'] if pd.notna(profile['cognitive']['mbti']) else 'N/A'
        disc = profile['cognitive']['disc'] if pd.notna(profile['cognitive']['disc']) else 'N/A'
        
        st.markdown(f"""
        <div style="background: rgba(74, 144, 226, 0.1); padding: 1rem; border-radius: 8px; margin-bottom: 0.5rem;">
            <div style="color: #8B9DB8; font-size: 0.9rem;">MBTI Type</div>
            <div style="color: #4A90E2; font-size: 1.5rem; font-weight: bold;">{mbti}</div>
        </div>
        <div style="background: rgba(81, 207, 102, 0.1); padding: 1rem; border-radius: 8px;">
            <div style="color: #8B9DB8; font-size: 0.9rem;">DISC Profile</div>
            <div style="color: #51CF66; font-size: 1.5rem; font-weight: bold;">{disc}</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.info("No personality data available")
    
    st.markdown('</div>', unsafe_allow_html=True)

# ==============================================================================
# DETAILED ANALYSIS TABS
# ==============================================================================
st.markdown('<br><br>', unsafe_allow_html=True)
st.markdown('<div class="section-title" style="text-align: center;">📊 Detailed Analysis</div>', unsafe_allow_html=True)

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🎯 PAPI Work Style", 
    "📈 Performance History", 
    "🔍 Complete Profile (360°)",
    "🛤️ Career Journey",
    "💡 Development Plan"
])

# TAB 1: PAPI Work Style (20 Scales)
with tab1:
    st.markdown('<div class="profile-card">', unsafe_allow_html=True)
    st.markdown("### 🎯 PAPI Kostick - Work Style Preferences (20 Scales)")
    
    # Load PAPI data
    papi_query = """
    SELECT scale_code, score
    FROM papi_scores
    WHERE employee_id = %s
    ORDER BY scale_code
    """
    with engine.connect() as conn:
        papi_df = pd.read_sql(papi_query, conn, params=(selected_employee_id,))
    
    if not papi_df.empty:
        # Create horizontal bar chart
        fig_papi = go.Figure()
        
        # Color based on score (higher = greener, lower = redder)
        colors = ['#51CF66' if score >= 5 else '#FFD43B' if score >= 3 else '#FF6B6B' 
                  for score in papi_df['score']]
        
        fig_papi.add_trace(go.Bar(
            y=papi_df['scale_code'],
            x=papi_df['score'],
            orientation='h',
            marker_color=colors,
            marker_line_color='rgba(255,255,255,0.3)',
            marker_line_width=1,
            text=[f"{score:.1f}" for score in papi_df['score']],
            textposition='outside',
            textfont=dict(size=10, color='#E8EDF3'),
            hovertemplate='<b>%{y}</b><br>Score: %{x:.1f}<extra></extra>'
        ))
        
        fig_papi.update_layout(
            xaxis=dict(
                range=[0, 10],
                title=dict(text="Score (1-9 scale)", font=dict(size=11, color='#8B9DB8')),
                tickfont=dict(size=10, color='#8B9DB8'),
                showgrid=True,
                gridcolor='rgba(139, 157, 184, 0.1)'
            ),
            yaxis=dict(
                tickfont=dict(size=10, color='#8B9DB8'),
                autorange="reversed"
            ),
            height=600,
            margin=dict(l=80, r=80, t=20, b=60),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            hoverlabel=dict(bgcolor='#1a2332', font_color='#E8EDF3', bordercolor='#4A90E2')
        )
        
        st.plotly_chart(fig_papi, width="stretch", config={'displayModeBar': False})
        
        st.info("💡 **Note:** I, K, Z, T scales are reverse-scored (lower is better)")
    else:
        st.warning("No PAPI data available for this employee")
    
    st.markdown('</div>', unsafe_allow_html=True)

# TAB 2: Performance History
with tab2:
    st.markdown('<div class="profile-card">', unsafe_allow_html=True)
    st.markdown("### 📈 Performance Rating Trend Over Years")
    
    # Load performance history
    perf_history_query = """
    SELECT year, rating
    FROM performance_yearly
    WHERE employee_id = %s
    ORDER BY year
    """
    with engine.connect() as conn:
        perf_history_df = pd.read_sql(perf_history_query, conn, params=(selected_employee_id,))
    
    if not perf_history_df.empty:
        fig_perf = go.Figure()
        
        fig_perf.add_trace(go.Scatter(
            x=perf_history_df['year'],
            y=perf_history_df['rating'],
            mode='lines+markers',
            line=dict(color='#4A90E2', width=3),
            marker=dict(size=12, color='#51CF66', line=dict(width=2, color='#4A90E2')),
            fill='tozeroy',
            fillcolor='rgba(74, 144, 226, 0.2)',
            hovertemplate='<b>Year %{x}</b><br>Rating: %{y}<extra></extra>'
        ))
        
        fig_perf.update_layout(
            xaxis=dict(
                title=dict(text="Year", font=dict(size=12, color='#8B9DB8')),
                tickfont=dict(size=11, color='#8B9DB8'),
                showgrid=True,
                gridcolor='rgba(139, 157, 184, 0.1)',
                dtick=1,  # Force 1 year intervals
                tickformat='d'  # Integer format (no decimals)
            ),
            yaxis=dict(
                title=dict(text="Performance Rating", font=dict(size=12, color='#8B9DB8')),
                tickfont=dict(size=11, color='#8B9DB8'),
                range=[0, 5.5],
                showgrid=True,
                gridcolor='rgba(139, 157, 184, 0.1)'
            ),
            height=400,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            hoverlabel=dict(bgcolor='#1a2332', font_color='#E8EDF3', bordercolor='#4A90E2'),
            margin=dict(l=60, r=40, t=40, b=60)
        )
        
        st.plotly_chart(fig_perf, width="stretch", config={'displayModeBar': False})
        
        # Performance stats
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("📊 Average Rating", f"{perf_history_df['rating'].mean():.2f}")
        with col2:
            st.metric("⬆️ Peak Rating", f"{perf_history_df['rating'].max():.0f}")
        with col3:
            trend = "📈 Improving" if perf_history_df.iloc[-1]['rating'] > perf_history_df.iloc[0]['rating'] else "📉 Declining" if perf_history_df.iloc[-1]['rating'] < perf_history_df.iloc[0]['rating'] else "➡️ Stable"
            st.metric("📊 Trend", trend)
    else:
        st.warning("No performance history available")
    
    st.markdown('</div>', unsafe_allow_html=True)

# TAB 3: Complete 360° Profile
with tab3:
    st.markdown('<div class="profile-card">', unsafe_allow_html=True)
    st.markdown("### 🔍 Complete Talent Profile (All Variables)")
    
    # Collect all TVs
    all_tvs = []
    
    # Competencies (10 TVs)
    for _, row in profile['competencies'].iterrows():
        all_tvs.append({
            'TGV': 'COMPETENCY',
            'Variable': row['pillar_label'],
            'Score': f"{row['score']:.2f}",  # Convert to string
            'Type': 'Numeric'
        })
    
    # Cognitive (5 TVs)
    if profile['cognitive'] is not None:
        for col in ['iq', 'gtq', 'tiki', 'pauli', 'faxtor']:
            if pd.notna(profile['cognitive'][col]):
                all_tvs.append({
                    'TGV': 'COGNITIVE',
                    'Variable': col.upper(),
                    'Score': f"{profile['cognitive'][col]:.2f}",  # Convert to string
                    'Type': 'Numeric'
                })
    
    # PAPI (20 TVs)
    if not papi_df.empty:
        for _, row in papi_df.iterrows():
            all_tvs.append({
                'TGV': 'WORK_STYLE',
                'Variable': f"PAPI-{row['scale_code']}",
                'Score': f"{row['score']:.2f}",  # Convert to string
                'Type': 'Numeric'
            })
    
    # Personality (2 TVs)
    if profile['cognitive'] is not None:
        all_tvs.append({
            'TGV': 'PERSONALITY',
            'Variable': 'MBTI',
            'Score': profile['cognitive']['mbti'] if pd.notna(profile['cognitive']['mbti']) else 'N/A',
            'Type': 'Categorical'
        })
        all_tvs.append({
            'TGV': 'PERSONALITY',
            'Variable': 'DISC',
            'Score': profile['cognitive']['disc'] if pd.notna(profile['cognitive']['disc']) else 'N/A',
            'Type': 'Categorical'
        })
    
    # Strengths (Top 5)
    for _, strength in profile['strengths'].iterrows():
        all_tvs.append({
            'TGV': 'STRENGTHS',
            'Variable': strength['theme'],
            'Score': f"Rank #{strength['rank']}",
            'Type': 'Categorical'
        })
    
    # Create DataFrame
    complete_df = pd.DataFrame(all_tvs)
    
    if not complete_df.empty:
        st.dataframe(
            complete_df,
            column_config={
                'TGV': st.column_config.TextColumn('Group', width='medium'),
                'Variable': st.column_config.TextColumn('Talent Variable', width='large'),
                'Score': st.column_config.TextColumn('Score / Value', width='medium'),  # Changed to TextColumn
                'Type': st.column_config.TextColumn('Type', width='small')
            },
            hide_index=True,
            width="stretch",
            height=500
        )
        
        st.success(f"✅ **Total Variables:** {len(complete_df)} across {complete_df['TGV'].nunique()} Talent Groups")
    else:
        st.warning("Unable to compile complete profile")
    
    st.markdown('</div>', unsafe_allow_html=True)

# TAB 4: Career Journey
with tab4:
    st.markdown('<div class="profile-card">', unsafe_allow_html=True)
    st.markdown("### 🛤️ Career Journey & Timeline")
    
    st.info("📌 **Current Status:**")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"**Position:** {profile['basic']['position_name']}")
    with col2:
        st.markdown(f"**Department:** {profile['basic']['department_name']}")
    with col3:
        st.markdown(f"**Grade:** {profile['basic']['grade_name']}")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Career stats
    st.markdown("#### 📊 Career Statistics")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("🕒 Total Experience", f"{exp_years:.1f} years")
    with col2:
        years_since_promotion = exp_years % 3  # Placeholder logic
        st.metric("📅 Time in Current Role", f"{years_since_promotion:.1f} years")
    with col3:
        st.metric("🎓 Education", profile['basic']['education_name'])
    
    st.markdown('</div>', unsafe_allow_html=True)

# TAB 5: Development Plan
with tab5:
    st.markdown('<div class="profile-card">', unsafe_allow_html=True)
    st.markdown("### 💡 Personalized Development Plan")
    
    # AI-Generated Recommendations (rule-based for now)
    st.markdown("#### 🎯 Recommended Focus Areas")
    
    # Find weakest competencies
    if not profile['competencies'].empty:
        weakest_comps = profile['competencies'].nsmallest(3, 'score')
        
        st.markdown("**🔧 Areas for Improvement:**")
        for _, comp in weakest_comps.iterrows():
            st.markdown(f"""
            <div style="background: rgba(255, 107, 107, 0.1); padding: 1rem; border-radius: 8px; border-left: 4px solid #FF6B6B; margin-bottom: 0.5rem;">
                <div style="color: #FF6B6B; font-weight: bold;">{comp['pillar_label']}</div>
                <div style="color: #8B9DB8; font-size: 0.9rem;">Current: {comp['score']:.2f} / 5.0 • Gap to excellence: {5.0 - comp['score']:.2f} points</div>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Find strengths
    if not profile['competencies'].empty:
        strongest_comps = profile['competencies'].nlargest(3, 'score')
        
        st.markdown("**💪 Continue Leveraging:**")
        for _, comp in strongest_comps.iterrows():
            st.markdown(f"""
            <div style="background: rgba(81, 207, 102, 0.1); padding: 1rem; border-radius: 8px; border-left: 4px solid #51CF66; margin-bottom: 0.5rem;">
                <div style="color: #51CF66; font-weight: bold;">{comp['pillar_label']}</div>
                <div style="color: #8B9DB8; font-size: 0.9rem;">Current: {comp['score']:.2f} / 5.0 • Keep excelling!</div>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Career trajectory
    st.markdown("#### 🚀 Suggested Career Path")
    
    if rating >= 4:
        st.success("✨ **High Performer Track:** You're on track for leadership roles!")
        st.markdown("""
        **Recommended Next Steps:**
        - Consider leadership training programs
        - Seek mentorship opportunities
        - Take on stretch assignments
        - Develop strategic thinking skills
        """)
    elif rating >= 3:
        st.info("📈 **Growth Track:** Continue developing core competencies")
        st.markdown("""
        **Recommended Next Steps:**
        - Focus on closing competency gaps
        - Seek feedback from manager
        - Enroll in skill-building workshops
        - Set SMART goals for improvement
        """)
    else:
        st.warning("🎯 **Development Track:** Build foundational skills")
        st.markdown("""
        **Recommended Next Steps:**
        - Work closely with mentor
        - Complete core training modules
        - Request regular check-ins
        - Focus on one competency at a time
        """)
    
    st.markdown('</div>', unsafe_allow_html=True)

# Footer
st.markdown('<br>', unsafe_allow_html=True)
st.markdown("""
<div style='text-align: center; color: #6B7B94; padding: 2rem 0;'>
    <small>Talent Intelligence Dashboard © 2025. All rights reserved.</small>
</div>
""", unsafe_allow_html=True)
