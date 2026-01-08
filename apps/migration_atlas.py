import streamlit as st
import pandas as pd
from lib.viz import line_chart, immigration_flow_map, emigration_flow_map
from lib.scb_client import SCBClientMigration
from lib.migration_logic import (
    calculate_net_migration,
    aggregate_by_year,
    get_top_immigration_countries,
    get_top_emigration_countries,
    prepare_migration_flows,
    map_country_codes_to_names
)


def style_migration_table(df: pd.DataFrame, value_col: str, color_scheme: str = "blue") -> pd.DataFrame:
    """
    Style migration tables with bars, gradients, and formatting.
    
    Args:
        df: DataFrame with Country and migration data columns
        value_col: Name of the value column (Immigration or Emigration)
        color_scheme: Color scheme ('blue' for immigration, 'orange' for emigration)
    
    Returns:
        Styled DataFrame
    """
    if df.empty:
        return df
    
    # Make a copy and handle NaN values
    df_styled = df.copy()
    
    # Drop any rows with NaN values in the value column
    if value_col in df_styled.columns:
        df_styled = df_styled.dropna(subset=[value_col])
    
    if df_styled.empty:
        return df_styled
    
    # Reset index after dropping NaN rows
    df_styled = df_styled.reset_index(drop=True)
    
    # Store numeric values BEFORE formatting for bar creation
    numeric_values = df_styled[value_col].values.copy()
    max_val = numeric_values.max() if len(numeric_values) > 0 else 1
    
    # Add rank column with medals for top 3
    df_styled.insert(0, '🏆', range(1, len(df_styled) + 1))
    
    # Replace top 3 ranks with medals
    if len(df_styled) >= 1:
        df_styled.loc[0, '🏆'] = '🥇'
    if len(df_styled) >= 2:
        df_styled.loc[1, '🏆'] = '🥈'
    if len(df_styled) >= 3:
        df_styled.loc[2, '🏆'] = '🥉'
    
    # Format numbers with commas and no decimals - handle potential NaN
    def format_number(x):
        try:
            if pd.isna(x):
                return "0"
            return f'{int(x):,}'
        except (ValueError, TypeError):
            return "0"
    
    df_styled[value_col] = df_styled[value_col].apply(format_number)
    
    # Add visual bar column
    def create_bar(value, max_value, color):
        """Create an HTML progress bar"""
        try:
            if pd.isna(value):
                return '<div style="width: 0%; height: 20px;"></div>'
            
            if isinstance(value, str):
                # Extract numeric value from formatted string
                value = float(value.replace(',', ''))
            
            width = int((value / max_value) * 100) if max_value > 0 else 0
            
            if color == "blue":
                bar_color = "#06b6d4"  # Cyan
                bg_color = "#0e7490"   # Dark cyan
            else:  # orange
                bar_color = "#f97316"  # Orange
                bg_color = "#c2410c"   # Dark orange
            
            return f'<div style="background: linear-gradient(90deg, {bar_color} 0%, {bg_color} 100%); width: {width}%; height: 20px; border-radius: 3px;"></div>'
        except (ValueError, TypeError):
            return '<div style="width: 0%; height: 20px;"></div>'
    
    # Add bar column before value column - use the stored numeric values
    if len(numeric_values) > 0:
        df_styled.insert(len(df_styled.columns) - 1, '📊', 
                        [create_bar(v, max_val, color_scheme) for v in numeric_values])
    
    return df_styled


@st.cache_data(ttl=24*3600)
def get_migration_client():
    return SCBClientMigration()


@st.cache_data(ttl=6*3600)
def fetch_migration_data(start_year: int, end_year: int):
    """Fetch migration data from SCB API."""
    client = get_migration_client()
    return client.fetch_migration_dataframe(
        start_year=start_year,
        end_year=end_year
    )


def render():
    st.subheader("Migration & Movement Atlas (data from 2010)")
    
    # Custom CSS for center alignment and styled tables
    st.markdown("""
    <style>
    /* Center align all headings and titles */
    h1, h2, h3, h4, h5, h6 {
        text-align: center !important;
    }
    
    .stMarkdown h1, .stMarkdown h2, .stMarkdown h3, .stMarkdown h4, .stMarkdown h5, .stMarkdown h6 {
        text-align: center !important;
    }
    
    /* Center align captions */
    .stCaption {
        text-align: center !important;
    }
    
    /* Style the migration tables */
    table {
        width: 100%;
        border-collapse: collapse;
        font-family: 'Arial', sans-serif;
        background-color: #1e293b;
        border-radius: 8px;
        overflow: hidden;
    }
    
    thead tr {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        color: #93c5fd;
        text-align: left;
        font-weight: bold;
        font-size: 14px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    thead th {
        padding: 15px 12px;
        border-bottom: 2px solid #475569;
        text-align: center !important;
    }
    
    tbody td {
        padding: 12px;
        border-bottom: 1px solid #334155;
        color: #e2e8f0;
        font-size: 14px;
    }
    
    tbody tr {
        background-color: #1e293b;
        transition: all 0.3s ease;
    }
    
    tbody tr:hover {
        background-color: #334155;
        transform: translateX(2px);
    }
    
    tbody tr:nth-child(1) {
        background: linear-gradient(90deg, rgba(6, 182, 212, 0.15) 0%, rgba(30, 41, 59, 1) 100%);
    }
    
    tbody tr:nth-child(2) {
        background: linear-gradient(90deg, rgba(6, 182, 212, 0.1) 0%, rgba(30, 41, 59, 1) 100%);
    }
    
    tbody tr:nth-child(3) {
        background: linear-gradient(90deg, rgba(6, 182, 212, 0.05) 0%, rgba(30, 41, 59, 1) 100%);
    }
    
    /* Medal styling */
    tbody tr:nth-child(1) td:first-child {
        font-size: 20px;
    }
    
    tbody tr:nth-child(2) td:first-child {
        font-size: 18px;
    }
    
    tbody tr:nth-child(3) td:first-child {
        font-size: 16px;
    }
    
    /* Make number columns bold */
    tbody td:last-child {
        font-weight: bold;
        color: #93c5fd;
        text-align: right;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Controls
    col1, col2 = st.columns(2)
    with col1:
        start_year = st.slider("Start Year", 2010, 2023, 2010)
    with col2:
        end_year = st.slider("End Year", 2010, 2023, 2023)
    
    if start_year > end_year:
        st.error("Start year must be less than or equal to end year.")
        return
    
    # Fetch data
    with st.spinner("Loading migration data from SCB..."):
        df = fetch_migration_data(start_year, end_year)
    
    if df.empty:
        st.error("No data available for the selected years.")
        return
    
    # Debug: Show column names if countrycode is missing
    if "countrycode" not in df.columns:
        st.warning(f"⚠️ Column 'countrycode' not found. Available columns: {list(df.columns)}")
        st.dataframe(df.head())  # Show first few rows for debugging
        return
    
    # Map country codes to country names
    df = map_country_codes_to_names(df)
    
    # Calculate net migration
    df = calculate_net_migration(df)
    
    # Aggregate by year for overall net migration
    df_yearly = aggregate_by_year(df, group_by=["year"])
    
    # Display net migration chart
    if not df_yearly.empty and "net_migration" in df_yearly.columns:
        st.plotly_chart(
            line_chart(df_yearly, x="year", y="net_migration", title="Net Migration Over Time"),
            width='stretch'
        )
    
    # Migration Flow Maps
    st.markdown("---")
    st.markdown("#### 🌍 Migration Flow Maps")
    
    # Controls for maps
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Prepare year selector with "All Years" option
        if "year" in df.columns:
            available_years = sorted(df["year"].unique().tolist(), reverse=True)
            year_options = ["All Years"] + [str(year) for year in available_years]
        else:
            year_options = ["All Years"]
        
        selected_year_option = st.selectbox(
            "Select Year for Maps",
            options=year_options,
            index=0  # Default to "All Years"
        )
    
    with col2:
        use_globe = st.checkbox(
            "🌐 3D Globe View",
            value=False,
            help="Switch to an interactive 3D globe projection centered on Sweden"
        )
    
    # Parse selected year
    if selected_year_option == "All Years":
        selected_year = None
    else:
        selected_year = int(selected_year_option)
    
    # Prepare flow data for maps
    # Lower min_flow threshold to show more data, especially for single years
    min_flow_threshold = 10 if selected_year else 50
    flow_data = prepare_migration_flows(df, year=selected_year, min_flow=min_flow_threshold)
    
    if not flow_data.empty:
        # Display two maps stacked vertically
        st.markdown("##### 🟢 Immigration to Sweden")
        st.caption("Countries of origin → Sweden • Cyan gradient lines indicate migration volume")
        fig_immigration = immigration_flow_map(flow_data, year=selected_year, title="Immigration to Sweden", use_globe=use_globe)
        if fig_immigration:
            st.plotly_chart(fig_immigration, width='stretch', config={'displayModeBar': True, 'displaylogo': False})
        else:
            st.info("No immigration data available.")
        
        st.markdown("---")
        
        st.markdown("##### 🔴 Emigration from Sweden")
        st.caption("Sweden → Destination countries • Orange gradient lines indicate migration volume")
        fig_emigration = emigration_flow_map(flow_data, year=selected_year, title="Emigration from Sweden", use_globe=use_globe)
        if fig_emigration:
            st.plotly_chart(fig_emigration, width='stretch', config={'displayModeBar': True, 'displaylogo': False})
        else:
            st.info("No emigration data available.")
    else:
        if selected_year:
            st.info(f"No significant migration flows found for {selected_year} (minimum threshold: {min_flow_threshold} people). Try selecting 'All Years' to see aggregated data.")
        else:
            st.info("No flow data available for the selected period.")
    
    # Top countries section
    st.markdown("---")
    st.markdown("### 📊 Top Migration Countries")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 🟢 Top Immigration Sources")
        st.caption("Countries with highest immigration to Sweden")
        top_immigration = get_top_immigration_countries(df, top_n=10)
        if not top_immigration.empty:
            styled_immigration = style_migration_table(top_immigration, "Immigration", "blue")
            st.markdown(styled_immigration.to_html(escape=False, index=False), unsafe_allow_html=True)
        else:
            st.info("No immigration data available.")
    
    with col2:
        st.markdown("#### 🔴 Top Emigration Destinations")
        st.caption("Countries with highest emigration from Sweden")
        top_emigration = get_top_emigration_countries(df, top_n=10)
        if not top_emigration.empty:
            styled_emigration = style_migration_table(top_emigration, "Emigration", "orange")
            st.markdown(styled_emigration.to_html(escape=False, index=False), unsafe_allow_html=True)
        else:
            st.info("No emigration data available.")