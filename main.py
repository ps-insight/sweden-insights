import streamlit as st

st.set_page_config(
    page_title="Sweden Insights", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Centered header with custom styling
st.markdown(
    """
    <style>
    .main-header {
        text-align: center;
        padding: 2rem 0 1rem 0;
        margin-bottom: 2rem;
    }
    .main-header h1 {
        font-size: 3rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
        color: #1f77b4;
    }
    .main-caption {
        text-align: center;
        color: #666;
        font-size: 1.1rem;
        margin-bottom: 2rem;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.markdown('<div class="main-header"><h1>Sweden Insights 🇸🇪</h1></div>', unsafe_allow_html=True)
st.markdown('<div class="main-caption">Interactive dashboards built on SCB open data</div>', unsafe_allow_html=True)

tab1, tab2 = st.tabs(["📈 Cost of Living", "🗺️ Migration Atlas"])

with tab1:
    from apps.cost_of_living import render as render_cost
    render_cost()

with tab2:
    from apps.migration_atlas import render as render_migration
    render_migration()