# Helper function for detailed candidate analysis

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from core.matching_breakdown import get_detailed_match_breakdown

def render_detailed_analysis(results_df, benchmark_ids, engine):
    """
    Renders detailed TGV/TV analysis for selected candidate from results.
    
    Args:
        results_df: DataFrame with matching results
        benchmark_ids: List of employee IDs used as benchmark
        engine: Database engine
    """
    
    if results_df.empty:
        return
    
    st.markdown("---")
    st.markdown("### 🔍 Detailed Candidate Analysis")
    st.caption("Select a candidate from the results to view detailed profile comparison")
    
    # Create searchable selectbox
    candidate_options = {}
    for idx, row in results_df.head(50).iterrows():  # Limit to top 50 for performance
        label = f"{row['fullname']} - {row.get('position_name', 'N/A')} ({row['final_match_rate']:.1f}%)"
        candidate_options[label] = row['employee_id']
    
    selected_label = st.selectbox(
        "🔍 Type to search candidate:",
        options=list(candidate_options.keys()),
        index=0,
        help="Start typing to search by name. Select to view detailed breakdown."
    )
    
    selected_employee_id = candidate_options[selected_label]
    
    # Get detailed breakdown
    try:
        with st.spinner("Loading detailed analysis..."):
            breakdown = get_detailed_match_breakdown(
                engine=engine,
                employee_id=selected_employee_id,
                benchmark_ids=benchmark_ids
            )
        
        if not breakdown or breakdown['tv_details'].empty:
            st.warning("No detailed data available for this candidate")
            return
        
        # Display employee info header
        emp_info = breakdown['employee_info']
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Name", emp_info.get('fullname', 'N/A'))
        with col2:
            st.metric("Position", emp_info.get('position_name', 'N/A'))
        with col3:
            st.metric("Grade", emp_info.get('grade_name', 'N/A'))
        with col4:
            st.metric("Match Score", f"{breakdown['final_score']:.1f}%")
        
        st.markdown(f"**Benchmark:** {breakdown['benchmark_n']} employees")
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Section 1: TGV Visualizations (2 columns)
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 📈 TGV Match Profile")
            
            # Radar chart
            tgv_summary = breakdown['tgv_summary']
            
            fig_radar = go.Figure()
            
            # Candidate profile
            fig_radar.add_trace(go.Scatterpolar(
                r=tgv_summary['tgv_match_rate'].tolist(),
                theta=tgv_summary['tgv_name'].tolist(),
                fill='toself',
                name='Candidate',
                line_color='#4A90E2',
                fillcolor='rgba(74, 144, 226, 0.3)'
            ))
            
            # Benchmark line (100% perfect match)
            fig_radar.add_trace(go.Scatterpolar(
                r=[100] * len(tgv_summary),
                theta=tgv_summary['tgv_name'].tolist(),
                name='Perfect Match',
                line=dict(color='#51CF66', dash='dash'),
                fillcolor='rgba(81, 207, 102, 0.1)',
                fill='toself'
            ))
            
            fig_radar.update_layout(
                polar=dict(
                    radialaxis=dict(
                        visible=True,
                        range=[0, 100],
                        showticklabels=True,
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
                plot_bgcolor='rgba(0,0,0,0)'
            )
            
            st.plotly_chart(fig_radar, use_container_width=True, config={'displayModeBar': False})
        
        with col2:
            st.markdown("#### 💪 Strengths & Development Needs")
            
            # Get top/bottom TVs
            tv_details = breakdown['tv_details'].copy()
            tv_sorted = tv_details.sort_values('tv_match_rate')
            
            bottom_5 = tv_sorted.head(5)  # Development needs (gaps)
            top_5 = tv_sorted.tail(5)     # Strengths
            
            combined = pd.concat([bottom_5, top_5]).sort_values('tv_match_rate')
            
            # Horizontal bar chart
            colors = ['#FF6B6B' if rate < 80 else '#51CF66' for rate in combined['tv_match_rate']]
            
            fig_bar = go.Figure()
            
            fig_bar.add_trace(go.Bar(
                y=combined['tv_label'],
                x=combined['tv_match_rate'],
                orientation='h',
                marker_color=colors,
                marker_line_color='rgba(255,255,255,0.3)',
                marker_line_width=1,
                text=[f"{rate:.0f}%" for rate in combined['tv_match_rate']],
                textposition='outside',
                textfont=dict(size=10, color='#E8EDF3'),
                hovertemplate='<b>%{y}</b><br>Match: %{x:.1f}%<extra></extra>',
                showlegend=False
            ))
            
            fig_bar.update_layout(
                xaxis=dict(
                    range=[0, 105],
                    title=dict(
                        text="Match Rate (%)",
                        font=dict(size=11, color='#8B9DB8')
                    ),
                    tickfont=dict(size=10, color='#8B9DB8'),
                    showgrid=True,
                    gridcolor='rgba(139, 157, 184, 0.1)'
                ),
                yaxis=dict(
                    tickfont=dict(size=10, color='#8B9DB8')
                ),
                height=400,
                margin=dict(l=150, r=40, t=20, b=50),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                hoverlabel=dict(
                    bgcolor='#1a2332',
                    font_color='#E8EDF3',
                    bordercolor='#4A90E2'
                )
            )
            
            st.plotly_chart(fig_bar, use_container_width=True, config={'displayModeBar': False})
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Section 2: Match Distribution Histogram
        st.markdown("#### 📊 Talent Pool Distribution")
        
        # Create bins
        bins = [0, 20, 40, 60, 80, 100]
        labels = ['0-20%', '20-40%', '40-60%', '60-80%', '80-100%']
        
        results_df_copy = results_df.copy()
        results_df_copy['match_bin'] = pd.cut(results_df_copy['final_match_rate'], bins=bins, labels=labels)
        bin_counts = results_df_copy['match_bin'].value_counts().sort_index()
        
        fig_hist = go.Figure()
        
        fig_hist.add_trace(go.Bar(
            x=bin_counts.index.astype(str),
            y=bin_counts.values,
            marker_color='#4A90E2',
            marker_line_color='rgba(255,255,255,0.3)',
            marker_line_width=1,
            text=bin_counts.values,
            textposition='outside',
            textfont=dict(size=11, color='#E8EDF3'),
            hovertemplate='<b>%{x}</b><br>Candidates: %{y}<extra></extra>',
            showlegend=False
        ))
        
        fig_hist.update_layout(
            xaxis=dict(
                title=dict(
                    text="Match Rate Range",
                    font=dict(size=11, color='#8B9DB8')
                ),
                tickfont=dict(size=10, color='#8B9DB8')
            ),
            yaxis=dict(
                title=dict(
                    text="Number of Candidates",
                    font=dict(size=11, color='#8B9DB8')
                ),
                tickfont=dict(size=10, color='#8B9DB8'),
                showgrid=True,
                gridcolor='rgba(139, 157, 184, 0.1)'
            ),
            height=300,
            margin=dict(l=60, r=40, t=30, b=60),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            hoverlabel=dict(
                bgcolor='#1a2332',
                font_color='#E8EDF3',
                bordercolor='#4A90E2'
            )
        )
        
        st.plotly_chart(fig_hist, use_container_width=True, config={'displayModeBar': False})
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Section 3: Categorized Comparison Table
        st.markdown("#### 🔍 Detailed Comparison by Category")
        st.caption("Variables grouped by TGV dimension. Green = Strength, Red = Development Need")
        
        tv_details['gap'] = tv_details['user_score'] - tv_details['baseline_score']
        
        # Group by TGV
        tgv_categories = ['COMPETENCY', 'COGNITIVE', 'WORK_STYLE']  # Main TGVs with data
        
        for tgv_name in tgv_categories:
            tgv_data = tv_details[tv_details['tgv_name'] == tgv_name].copy()
            
            if tgv_data.empty:
                continue
            
            # Get TGV match rate for display
            tgv_match = tgv_summary[tgv_summary['tgv_name'] == tgv_name]['tgv_match_rate']
            tgv_match_val = tgv_match.iloc[0] if not tgv_match.empty else 0
            
            with st.expander(f"**{tgv_name.replace('_', ' ').title()}** (Match: {tgv_match_val:.1f}%)", expanded=(tgv_name == 'COMPETENCY')):
                # Prepare display dataframe
                display_df = tgv_data[['tv_label', 'baseline_score', 'user_score', 'gap', 'tv_match_rate']].copy()
                display_df['gap'] = display_df['gap'].round(2)
                display_df['baseline_score'] = display_df['baseline_score'].round(2)
                display_df['user_score'] = display_df['user_score'].round(2)
                display_df['tv_match_rate'] = display_df['tv_match_rate'].round(1)
                
                # Add status column
                display_df['status'] = display_df['gap'].apply(
                    lambda x: '✓ Strength' if x > 0.5 else '⚠ Gap' if x < -0.5 else '= Even'
                )
               
                # Style function for rows
                def highlight_rows(row):
                    if row['gap'] > 0.5:
                        return ['background-color: rgba(81, 207, 102, 0.15)'] * len(row)
                    elif row[' gap'] < -0.5:
                        return ['background-color: rgba(255, 107, 107, 0.15)'] * len(row)
                    else:
                        return [''] * len(row)
                
                st.dataframe(
                    display_df,
                    column_config={
                        'tv_label': 'Variable',
                        'baseline_score': st.column_config.NumberColumn('Benchmark', format="%.2f"),
                        'user_score': st.column_config.NumberColumn('Candidate', format="%.2f"),
                        'gap': st.column_config.NumberColumn('Gap', format="%.2f"),
                        'tv_match_rate': st.column_config.ProgressColumn('Match %', format="%.1f%%", min_value=0, max_value=100),
                        'status': 'Status'
                    },
                    hide_index=True,
                    use_container_width=True
                )
        
        #  Section 4: Export Functionality
        st.markdown("<br>", unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        
        with col1:
            # Prepare CSV data
            csv_data = tv_details[['tgv_name', 'tv_label', 'baseline_score', 'user_score', 'gap', 'tv_match_rate']].copy()
            csv = csv_data.to_csv(index=False)
            
            st.download_button(
                label="📄 Export Comparison (CSV)",
                data=csv,
                file_name=f"talent_comparison_{selected_employee_id}.csv",
                mime="text/csv",
                use_container_width=True
            )
        
        with col2:
            # Prepare summary text
            summary_text = f"""
TALENT MATCH ANALYSIS SUMMARY
{'='*50}

Candidate: {emp_info.get('fullname', 'N/A')}
Position: {emp_info.get('position_name', 'N/A')}
Grade: {emp_info.get('grade_name', 'N/A')}
Overall Match: {breakdown['final_score']:.1f}%
Benchmark: {breakdown['benchmark_n']} employees

TGV BREAKDOWN:
{'-'*50}
"""
            for _, row in tgv_summary.iterrows():
                summary_text += f"{row['tgv_name']}: {row['tgv_match_rate']:.1f}%\n"
            
            summary_text += f"\nTOP 5 STRENGTHS:\n{'-'*50}\n"
            for _, row in top_5.iterrows():
                summary_text += f"{row['tv_label']}: {row['tv_match_rate']:.1f}%\n"
            
            summary_text += f"\nDEVELOPMENT NEEDS:\n{'-'*50}\n"
            for _, row in bottom_5.iterrows():
                summary_text += f"{row['tv_label']}: {row['tv_match_rate']:.1f}%\n"
            
            st.download_button(
                label="📥 Export Summary (TXT)",
                data=summary_text,
                file_name=f"talent_summary_{selected_employee_id}.txt",
                mime="text/plain",
                use_container_width=True
            )
    
    except Exception as e:
        st.error(f"Error loading detailed analysis: {str(e)}")
        st.exception(e)
