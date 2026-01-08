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
st.markdown('<div class="main-caption">Interactive dashboards exploring Swedish economic and demographic trends (Data from scb.se)</div>', unsafe_allow_html=True)

# Enhanced navigation with styled cards
st.markdown("""
<style>
.nav-container {
    display: flex;
    gap: 1rem;
    margin: 2rem 0;
    justify-content: center;
}

.nav-card {
    flex: 1;
    max-width: 400px;
    padding: 1.5rem;
    border-radius: 12px;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    transition: all 0.3s ease;
    cursor: pointer;
    text-align: center;
}

.nav-card:hover {
    transform: translateY(-5px);
    box-shadow: 0 8px 12px rgba(0, 0, 0, 0.2);
}

.nav-card.selected {
    background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%);
    box-shadow: 0 8px 16px rgba(59, 130, 246, 0.4);
}

.nav-card-icon {
    font-size: 3rem;
    margin-bottom: 0.5rem;
}

.nav-card-title {
    font-size: 1.5rem;
    font-weight: 700;
    color: white;
    margin-bottom: 0.5rem;
}

.nav-card-description {
    font-size: 0.95rem;
    color: rgba(255, 255, 255, 0.9);
    line-height: 1.4;
}

/* Enhanced radio button styling */
.stRadio > div {
    display: flex;
    justify-content: center;
    gap: 1rem;
}

.stRadio [role="radiogroup"] {
    display: flex;
    gap: 1rem;
    justify-content: center;
}

.stRadio label {
    background: linear-gradient(135deg, #f0f4f8 0%, #e2e8f0 100%);
    padding: 1rem 2rem;
    border-radius: 10px;
    border: 2px solid transparent;
    font-weight: 600;
    font-size: 1.1rem;
    transition: all 0.3s ease;
    cursor: pointer;
    color: #1e293b !important;
}

.stRadio label:hover {
    background: linear-gradient(135deg, #e2e8f0 0%, #cbd5e1 100%);
    transform: translateY(-2px);
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
    color: #0f172a !important;
}

.stRadio label[data-checked="true"] {
    background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%) !important;
    color: white !important;
    border: 2px solid #1e40af;
    box-shadow: 0 6px 12px rgba(59, 130, 246, 0.3);
}

.stRadio div[role="radiogroup"] label div {
    color: inherit !important;
}

.stRadio div[role="radiogroup"] label span {
    color: inherit !important;
}
</style>
""", unsafe_allow_html=True)

# Create navigation using radio buttons with custom styling
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    selected_page = st.radio(
        "Navigation",
        ["📈 Consumer Price Insights", "🌍 Migration Patterns"],
        horizontal=True,
        label_visibility="collapsed"
    )

# Remove the duplicate tab styling CSS that was for tabs (not being used)
st.markdown("""
<style>
/* Minimal additional styling */
.stRadio [data-baseweb="radio"] {
    width: auto;
}
</style>
""", unsafe_allow_html=True)

# Add page info banner
if "Consumer Price" in selected_page:
    st.markdown("""
    <div style="background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%); 
                padding: 1rem; 
                border-radius: 8px; 
                border-left: 4px solid #3b82f6; 
                margin: 1rem 0 2rem 0;">
        <div style="display: flex; align-items: center; gap: 1rem;">
            <div style="font-size: 2rem;">📊</div>
            <div>
                <div style="font-weight: 600; color: #1e40af; margin-bottom: 0.25rem;">Consumer Price Index (CPI) & Cost of Living</div>
                <div style="font-size: 0.9rem; color: #475569;">
                    Track inflation trends, product categories, weights, and their impact on Swedish households
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
    <div style="background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%); 
                padding: 1rem; 
                border-radius: 8px; 
                border-left: 4px solid #10b981; 
                margin: 1rem 0 2rem 0;">
        <div style="display: flex; align-items: center; gap: 1rem;">
            <div style="font-size: 2rem;">🌍</div>
            <div>
                <div style="font-weight: 600; color: #065f46; margin-bottom: 0.25rem;">Migration Patterns & Demographics</div>
                <div style="font-size: 0.9rem; color: #475569;">
                    Explore immigration and emigration flows with interactive world maps and historical trends
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# Render based on selection
try:
    if "Consumer Price" in selected_page:
        from apps.cost_of_living import render as render_cost
        render_cost()
    else:
        from apps.migration_atlas import render as render_migration
        render_migration()
except Exception as e:
    st.error(f"Error loading page: {str(e)}")
    st.exception(e)