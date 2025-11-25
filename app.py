"""
Talent Intelligence Dashboard - Production UI/UX Refactored
Clean, Responsive, Professional Layout
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from sqlalchemy import text
from core.db import get_engine

# ============================================================================
# PAGE CONFIGURATION + CUSTOM CSS
# ============================================================================

st.set_page_config(
    page_title="Talent Intelligence Dashboard",
    page_icon="■",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for production-grade layout
st.markdown("""
<style>
    /* Main background */
    .main {
        background-color: #0F1419;
        padding: 1rem 2rem;
    }
    
    /* Remove default Streamlit padding */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 1400px;
    }
    
    /* Card styling */
    .metric-card {
        background: linear-gradient(135deg, #1a2332 0%, #253447 100%);
        border-radius: 12px;
        padding: 1.5rem;
        border: 1px solid rgba(74, 144, 226, 0.15);
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
        height: 100%;
        min-height: 140px;
    }
    
    .chart-card {
        background: rgba(26, 35, 50, 0.4);
        border-radius: 12px;
        padding: 1.5rem;
        border: 1px solid rgba(74, 144, 226, 0.1);
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
        height: 100%;
        backdrop-filter: blur(10px);
    }
    
    /* Make sure Streamlit elements stay inside card */
    .chart-card > div {
        background: transparent !important;
    }
    
    .chart-card .stPlotlyChart {
        background: transparent !important;
    }
    
    /* Typography */
    .card-label {
        color: #8B9DB8;
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.8px;
        font-weight: 600;
        margin-bottom: 0.75rem;
    }
    
    .card-value {
        color: #E8EDF3;
        font-size: 2.25rem;
        font-weight: 700;
        line-height: 1;
        margin-bottom: 0.5rem;
    }
    
    .card-subtitle {
        color: #6B7B94;
        font-size: 0.875rem;
    }
    
    .chart-title {
        color: #4A90E2;
        font-size: 1.125rem;
        font-weight: 600;
        margin-bottom: 1rem;
        letter-spacing: -0.3px;
    }
    
    /* Header */
    .dashboard-header {
        text-align: center;
        padding: 2rem 0 2.5rem 0;
        border-bottom: 1px solid rgba(74, 144, 226, 0.1);
        margin-bottom: 2rem;
    }
    
    .dashboard-title {
        color: #4A90E2;
        font-size: 2rem;
        font-weight: 600;
        margin: 0;
        letter-spacing: -0.5px;
    }
    
    .dashboard-subtitle {
        color: #6B7B94;
        font-size: 1rem;
        margin-top: 0.5rem;
    }
    
    /* Footer */
    .dashboard-footer {
        border-top: 1px solid rgba(74, 144, 226, 0.1);
        padding: 2rem 0 1rem 0;
        margin-top: 3rem;
        text-align: center;
        color: #6B7B94;
        font-size: 0.875rem;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Responsive gaps */
    [data-testid="column"] {
        padding: 0 0.75rem;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# DATA LOADING
# ============================================================================

@st.cache_resource
def get_db_engine():
    return get_engine()

engine = get_db_engine()

@st.cache_data(ttl=300)
def load_dashboard_data():
    with engine.connect() as conn:
        total_employees = pd.read_sql(
            "SELECT COUNT(DISTINCT employee_id) as count FROM employees", conn
        ).iloc[0]['count']
        
        hp_data = pd.read_sql(
            """SELECT 
                COUNT(DISTINCT employee_id) as hp_count,
                COUNT(DISTINCT employee_id) * 100.0 / (SELECT COUNT(*) FROM employees) as hp_pct
            FROM performance_yearly 
            WHERE rating = 5 
            AND year = (SELECT MAX(year) FROM performance_yearly)""", conn
        )
        
        perf_dist = pd.read_sql(
            """SELECT rating, COUNT(*) as count
            FROM performance_yearly
            WHERE year = (SELECT MAX(year) FROM performance_yearly)
            GROUP BY rating ORDER BY rating""", conn
        )
        
        top_comp = pd.read_sql(
            """SELECT cp.pillar_label, AVG(cy.score) as avg_score
            FROM competencies_yearly cy
            JOIN dim_competency_pillars cp ON cy.pillar_code = cp.pillar_code
            JOIN performance_yearly py ON cy.employee_id = py.employee_id 
                AND py.year = cy.year
            WHERE py.rating = 5 
            AND cy.year = (SELECT MAX(year) FROM competencies_yearly)
            GROUP BY cp.pillar_label ORDER BY avg_score DESC LIMIT 5""", conn
        )
        
        comp_gap = pd.read_sql(
            """SELECT 
                AVG(CASE WHEN py.rating = 5 THEN cy.score END) as hp_avg,
                AVG(CASE WHEN py.rating < 5 THEN cy.score END) as non_hp_avg
            FROM competencies_yearly cy
            JOIN performance_yearly py ON cy.employee_id = py.employee_id 
                AND py.year = cy.year
            WHERE cy.year = (SELECT MAX(year) FROM competencies_yearly)""", conn
        )
        
        cog_gap = pd.read_sql(
            """SELECT 
                AVG(CASE WHEN py.rating = 5 THEN pp.iq END) as hp_iq,
                AVG(CASE WHEN py.rating < 5 THEN pp.iq END) as non_hp_iq
            FROM profiles_psych pp
            JOIN employees e ON pp.employee_id = e.employee_id
            JOIN performance_yearly py ON e.employee_id = py.employee_id
            WHERE pp.iq IS NOT NULL
            AND py.year = (SELECT MAX(year) FROM performance_yearly)""", conn
        )
        
        position_count = pd.read_sql(
            "SELECT COUNT(DISTINCT position_id) as count FROM employees WHERE position_id IS NOT NULL", conn
        ).iloc[0]['count']

        # Fetch dynamic weights
        tgv_weights = pd.read_sql("SELECT tgv_name, tgv_weight FROM talent_group_weights", conn)
    
    return {
        'total_employees': total_employees,
        'hp_count': int(hp_data.iloc[0]['hp_count']),
        'hp_pct': hp_data.iloc[0]['hp_pct'],
        'perf_dist': perf_dist,
        'top_comp': top_comp,
        'comp_gap': comp_gap,
        'cog_gap': cog_gap,
        'position_count': position_count,
        'tgv_weights': tgv_weights
    }

# ============================================================================
# MAIN DASHBOARD
# ============================================================================

# Header
st.markdown("""
<div class="dashboard-header">
    <h1 class="dashboard-title">Talent Intelligence Dashboard</h1>
    <p class="dashboard-subtitle">Data-Driven Insights for Strategic Talent Management</p>
</div>
""", unsafe_allow_html=True)

try:
    data = load_dashboard_data()
    
    # ========================================================================
    # METRICS CARDS - FULL WIDTH GRID
    # ========================================================================
    
    col1, col2, col3, col4 = st.columns(4, gap="medium")
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="card-label">Total Employees</div>
            <div class="card-value">{data['total_employees']:,}</div>
            <div class="card-subtitle">Active in System</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="card-label">High Performers</div>
            <div class="card-value">{data['hp_count']:,}</div>
            <div class="card-subtitle">{data['hp_pct']:.1f}% of Total</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        avg_comp = data['top_comp']['avg_score'].mean()
        st.markdown(f"""
        <div class="metric-card">
            <div class="card-label">Avg Competency</div>
            <div class="card-value">{avg_comp:.1f}</div>
            <div class="card-subtitle">Top 5 HP Scores</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="card-label">Active Roles</div>
            <div class="card-value">{data['position_count']}</div>
            <div class="card-subtitle">Positions Analyzed</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # ========================================================================
    # CHARTS ROW - RESPONSIVE GRID
    # ========================================================================
    
    col1, col2 = st.columns(2, gap="medium")
    
    with col1:
        # Simple title only (no card background due to Streamlit limitations)
        st.markdown("""
        <div style='color: #4A90E2; font-size: 1.125rem; font-weight: 600; margin-bottom: 1rem;'>
            Performance Distribution
        </div>
        """, unsafe_allow_html=True)
        
        # Bar chart with visible labels
        fig_perf = go.Figure()
        
        colors = ['#4A90E2' if r < 5 else '#51CF66' for r in data['perf_dist']['rating']]
        
        fig_perf.add_trace(go.Bar(
            x=data['perf_dist']['rating'],
            y=data['perf_dist']['count'],
            marker_color=colors,
            marker_line_color='rgba(255,255,255,0.3)',
            marker_line_width=1,
            text=data['perf_dist']['count'],
            textposition='outside',
            textfont=dict(size=12, color='#E8EDF3', family='Inter'),
            hovertemplate='<b>Rating %{x}</b><br>Count: %{y}<extra></extra>',
            showlegend=False
        ))
        
        fig_perf.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            height=340,
            margin=dict(l=60, r=40, t=30, b=60),
            xaxis=dict(
                title=dict(text="Performance Rating", font=dict(size=11, color='#8B9DB8')),
                tickfont=dict(size=10, color='#8B9DB8'),
                showgrid=False,
                showline=True,
                linecolor='rgba(139, 157, 184, 0.2)',
                tickmode='linear'
            ),
            yaxis=dict(
                title=dict(text="Number of Employees", font=dict(size=11, color='#8B9DB8')),
                tickfont=dict(size=10, color='#8B9DB8'),
                showgrid=True,
                gridcolor='rgba(139, 157, 184, 0.1)',
                showline=False
            ),
            hoverlabel=dict(
                bgcolor='#1a2332',
                font_size=11,
                font_color='#E8EDF3',
                bordercolor='#4A90E2'
            ),
            font=dict(family='Inter, sans-serif')
        )
        
        st.plotly_chart(fig_perf, width="stretch", config={'displayModeBar': False})
        st.markdown("<br>", unsafe_allow_html=True)
    
    with col2:
        # Simple title only
        st.markdown("""
        <div style='color: #4A90E2; font-size: 1.125rem; font-weight: 600; margin-bottom: 1rem;'>
            Success Formula Weights
        </div>
        """, unsafe_allow_html=True)
        
        # Donut chart - compact and centered
        tgv_data = data['tgv_weights'].copy()
        # Convert decimal to percentage for display if needed, but pie chart handles values automatically.
        # Ensure column names match what we want to display
        tgv_data.rename(columns={'tgv_name': 'TGV', 'tgv_weight': 'Weight'}, inplace=True)
        # Multiply by 100 for better tooltip display if they are decimals 0.5 etc
        tgv_data['Weight'] = tgv_data['Weight'] * 100
        
        fig_tgv = go.Figure(data=[go.Pie(
            labels=tgv_data['TGV'],
            values=tgv_data['Weight'],
            hole=0.5,
            marker=dict(
                colors=['#1E3A5F', '#2E4A6F', '#4A90E2', '#6BA3E8', '#A8C5E8'],
                line=dict(color='rgba(255,255,255,0.3)', width=2)
            ),
            textinfo='label+percent',
            textfont=dict(size=10, color='#E8EDF3', family='Inter'),
            textposition='outside',
            hovertemplate='<b>%{label}</b><br>Weight: %{value}%<extra></extra>',
            showlegend=True
        )])
        
        fig_tgv.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            height=340,
            margin=dict(l=20, r=120, t=20, b=20),
            showlegend=True,
            legend=dict(
                orientation="v",
                yanchor="middle",
                y=0.5,
                xanchor="left",
                x=1.05,
                font=dict(size=9, color='#8B9DB8'),
                bgcolor='rgba(0,0,0,0)',
                bordercolor='rgba(0,0,0,0)'
            ),
            hoverlabel=dict(
                bgcolor='#1a2332',
                font_size=11,
                font_color='#E8EDF3',
                bordercolor='#4A90E2'
            ),
            font=dict(family='Inter, sans-serif')
        )
        
        st.plotly_chart(fig_tgv, width="stretch", config={'displayModeBar': False})
        st.markdown("<br>", unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # ========================================================================
    # INSIGHTS & COMPETENCIES ROW
    # ========================================================================
    
    col1, col2 = st.columns(2, gap="medium")
    
    with col1:
        st.markdown("""
        <div style='color: #4A90E2; font-size: 1.125rem; font-weight: 600; margin-bottom: 1rem;'>
            Key Insights
        </div>
        """, unsafe_allow_html=True)
        
        comp_gap_val = data['comp_gap'].iloc[0]['hp_avg'] - data['comp_gap'].iloc[0]['non_hp_avg']
        iq_gap_val = data['cog_gap'].iloc[0]['hp_iq'] - data['cog_gap'].iloc[0]['non_hp_iq']
        
        insights = [
            f"{data['hp_pct']:.1f}% of employees are High Performers",
            f"Competency gap: HPs score {comp_gap_val:.1f} points higher",
            f"Cognitive advantage: {iq_gap_val:.1f} IQ points higher in HPs",
            f"{data['position_count']} positions analyzed across organization",
            f"Top competency: {data['top_comp'].iloc[0]['pillar_label']} ({data['top_comp'].iloc[0]['avg_score']:.2f})"
        ]
        
        for i, insight in enumerate(insights, 1):
            st.markdown(f"""
            <div style='padding: 0.875rem 0; border-bottom: 1px solid rgba(74, 144, 226, 0.1);'>
                <span style='color: #4A90E2; font-size: 0.75rem; font-weight: 600; margin-right: 0.75rem;'>
                    {i:02d}
                </span>
                <span style='color: #C5CFE0; font-size: 0.9rem;'>
                    {insight}
                </span>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div style='color: #4A90E2; font-size: 1.125rem; font-weight: 600; margin-bottom: 1rem;'>
            Top Competencies (High Performers)
        </div>
        """, unsafe_allow_html=True)
        
        # Horizontal bar with data labels
        fig_comp = go.Figure()
        
        fig_comp.add_trace(go.Bar(
            x=data['top_comp']['avg_score'],
            y=data['top_comp']['pillar_label'],
            orientation='h',
            marker_color='#4A90E2',
            marker_line_color='rgba(255,255,255,0.3)',
            marker_line_width=1,
            text=[f"{score:.2f}" for score in data['top_comp']['avg_score']],
            textposition='outside',
            textfont=dict(size=10, color='#E8EDF3', family='Inter'),
            hovertemplate='<b>%{y}</b><br>Score: %{x:.2f}<extra></extra>',
            showlegend=False
        ))
        
        fig_comp.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            height=300,
            margin=dict(l=20, r=80, t=20, b=50),
            xaxis=dict(
                title=dict(text="Average Score", font=dict(size=11, color='#8B9DB8')),
                tickfont=dict(size=10, color='#8B9DB8'),
                showgrid=True,
                gridcolor='rgba(139, 157, 184, 0.1)',
                range=[0, 5],
                showline=True,
                linecolor='rgba(139, 157, 184, 0.2)'
            ),
            yaxis=dict(
                tickfont=dict(size=10, color='#8B9DB8'),
                showgrid=False,
                categoryorder='total ascending'
            ),
            hoverlabel=dict(
                bgcolor='#1a2332',
                font_size=11,
                font_color='#E8EDF3',
                bordercolor='#4A90E2'
            ),
            font=dict(family='Inter, sans-serif')
        )
        
        st.plotly_chart(fig_comp, width="stretch", config={'displayModeBar': False})
        st.markdown('</div>', unsafe_allow_html=True)
    
    # ========================================================================
    # FOOTER
    # ========================================================================
    
    st.markdown("""
    <div class="dashboard-footer">
        Talent Intelligence Dashboard © 2025. All rights reserved.
    </div>
    """, unsafe_allow_html=True)

except Exception as e:
    st.error(f"⚠️ Error loading dashboard: {str(e)}")
    if st.button("Test Connection"):
        from core.db import test_connection
        if test_connection():
            st.success("✅ Connected")
            st.rerun()
        else:
            st.error("❌ Failed")
