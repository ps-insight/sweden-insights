import streamlit as st

st.set_page_config(page_title="Sweden Insights", layout="wide")

st.title("Sweden Insights 🇸🇪")
st.caption("Interactive dashboards built on SCB open data")

tab1, tab2 = st.tabs(["📈 Cost of Living", "🗺️ Migration Atlas"])

with tab1:
    from apps.cost_of_living import render as render_cost
    render_cost()

with tab2:
    from apps.migration_atlas import render as render_migration
    render_migration()