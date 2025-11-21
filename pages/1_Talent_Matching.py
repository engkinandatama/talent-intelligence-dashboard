import streamlit as st
import pandas as pd
from core.db import get_engine
from core.matching import run_match_query

engine = get_engine()

st.title("🎯 Talent Matching Engine")
st.caption("Find the best internal talent match based on benchmarked skill profiles.")

st.markdown("---")

# ------------------------------------------------
# Sidebar Filters
# ------------------------------------------------
st.sidebar.header("⚙️ Benchmark Settings")

min_rating = st.sidebar.slider(
    "Minimum rating considered 'High Performer'",
    1, 5, 5
)

# Load positions for role-based benchmark
positions = pd.read_sql("SELECT position_id, name FROM dim_positions ORDER BY name", engine)
position_map = dict(zip(positions["name"], positions["position_id"]))

selected_position = st.sidebar.selectbox(
    "Role-Based Benchmark Position (optional)",
    ["(None)"] + list(position_map.keys())
)

role_id = None if selected_position == "(None)" else position_map[selected_position]

# Load HP list for manual benchmark
hp_df = pd.read_sql("""
    SELECT e.employee_id, e.fullname
    FROM employees e
    JOIN performance_yearly p USING(employee_id)
    WHERE p.rating >= 5
    ORDER BY fullname
""", engine)

hp_df["label"] = hp_df["employee_id"] + " — " + hp_df["fullname"]

manual_selected = st.sidebar.multiselect(
    "Manual High Performers (optional)",
    hp_df["label"],
)

manual_ids = [x.split(" — ")[0] for x in manual_selected]

st.sidebar.markdown("💡 You may select manual, role-based, or both.")

run_button = st.sidebar.button("🚀 Run Talent Match")

# ------------------------------------------------
# Run Engine
# ------------------------------------------------
if run_button:
    st.subheader("📊 Ranked Talent List")

    with st.spinner("Running Talent Matching Engine..."):
        df = run_match_query(manual_ids, role_id, min_rating)

    df_view = df.copy()
    df_view["final_match_rate"] = df_view["final_match_rate"].round(2)

    st.dataframe(df_view, use_container_width=True)

    # Show Top Candidate
    if len(df_view):
        top = df_view.iloc[0]

        st.markdown("---")
        st.subheader("🏅 Top Match")

        st.success(f"""
        **{top['fullname']}**  
        ID: `{top['employee_id']}`  
        **Match Score:** {top['final_match_rate']:.2f}
        """)

else:
    st.info("Set filters on the left, then click **Run Talent Match**.")
