import streamlit as st
from lib.scb_client import SCBClientCOL
from lib.cpi_logic import (
    get_top_level_product_groups, 
    process_cpi_data, 
    filter_top_level_product_groups, 
    process_weights_data,
    calculate_inflation_contributions,
    prepare_heatmap_data,
    get_top_categories_by_weight,
    get_top_inflation_drivers,
    calculate_inflation_impact
)
from lib.viz import cpi_index_chart, weights_chart, inflation_contribution_chart, annual_changes_heatmap


@st.cache_data(ttl=24*3600)
def get_client():
    return SCBClientCOL(table_id="KPI2020COICOPM")


@st.cache_data(ttl=24*3600)
def get_available_product_groups():
    """Get list of top-level (2-digit) product group labels for multiselect."""
    client = get_client()
    return get_top_level_product_groups(client)


@st.cache_data(ttl=6*3600)
def fetch_all_data(last_n_months: int, all_observations: list):
    """
    Fetch ALL top-level product groups data once.
    This is the only API call - all subsequent operations work on this cached dataframe.
    
    Args:
        last_n_months: Number of months to fetch
        all_observations: List of all observation types to fetch
        
    Returns:
        Complete dataframe with all top-level product groups
    """
    client = get_client()
    all_groups = get_available_product_groups()
    
    if not all_groups:
        return None
    
    # Fetch all top-level product groups at once
    df = client.fetch_cpi_dataframe(
        product_group_labels=all_groups,
        observations=all_observations,
        last_n_months=last_n_months,
        add_labels=True
    )
    
    # Filter to only top-level (2-digit) product groups
    df = filter_top_level_product_groups(df)
    
    return df


def render():
    """Render the Cost of Living UI."""
    # Add custom CSS for better styling
    st.markdown(
        """
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
        
        .section-header {
            font-size: 1.5rem;
            font-weight: 600;
            color: #1f77b4;
            margin-top: 2rem;
            margin-bottom: 1rem;
            padding-bottom: 0.5rem;
            border-bottom: 2px solid #e0e0e0;
            text-align: center !important;
        }
        .metric-box {
            background-color: #f8f9fa;
            padding: 1rem;
            border-radius: 0.5rem;
            margin: 0.5rem 0;
        }
        </style>
        """,
        unsafe_allow_html=True
    )
    
    # Main header
    st.markdown('<div class="section-header">Cost of Living Compass (CPI)</div>', unsafe_allow_html=True)

    # Context / explanation in a cleaner format
    with st.expander("📊 About this dashboard", expanded=False):
        st.markdown(
            """
            **Data source**: This dashboard uses the official Consumer Price Index (KPI) data from
            Statistics Sweden ([SCB](https://www.scb.se)) – table `KPI2020COICOPM`, which contains
            COICOP product groups (e.g. 01 Food, 04 Housing, etc.).

            **Metrics explained:**
            - **Index**: Shows the CPI index level over time. The base year is **2020** (index = 100 in 2020).
            - **Annual changes**: Year‑on‑year percentage change in the index.
            - **Monthly changes**: Month‑on‑month percentage change in the index.
            - **Weights**: The relative expenditure weight of each product group in the CPI basket,
              i.e. how important that group is in the overall cost of living.
            """
        )

    # Get only top-level (2-digit) product groups for the multiselect
    all_groups = get_available_product_groups()
    
    # Get observations - try to get from variables, but have fallback
    client = get_client()
    try:
        vars_ = client.get_variables()
        all_obs = vars_.get("observations", ["Index", "Annual changes", "Monthly changes", "Weights"])
    except Exception:
        # Fallback if get_variables fails
        all_obs = ["Index", "Annual changes", "Monthly changes", "Weights"]

    # Controls section
    st.markdown("### ⚙️ Controls")
    
    # Time range selector - this affects the initial data fetch
    last_n = st.slider("📅 Time Range (months)", 12, 240, 60, help="Select the number of months to analyze")

    # Fetch ALL data once based on time range
    # This is the only API call - cached based on last_n_months
    with st.spinner("🔄 Loading data from SCB..."):
        df_all = fetch_all_data(last_n_months=last_n, all_observations=all_obs)
    
    if df_all is None or df_all.empty:
        st.error("❌ Failed to load data. Please try again later.")
        return

    # Now all operations work on the cached dataframe
    # Filter available groups based on what's actually in the loaded data
    available_groups_in_data = sorted(df_all["Product group_label"].unique().tolist()) if "Product group_label" in df_all.columns else all_groups
    
    # Controls - Product Groups only (all metrics are always shown)
    selected_groups = st.multiselect(
        "🏷️ Product Groups",
        options=available_groups_in_data,
        default=[g for g in ["TOTAL", "FOOD AND NON-ALCOHOLIC BEVERAGES"] if g in available_groups_in_data],
        help="Select one or more product groups to analyze. All metrics will be displayed."
    )

    # Always use all observations/metrics
    selected_obs = all_obs

    if not selected_groups:
        st.info("ℹ️ Please select at least 1 product group to continue.")
        return

    # Inflation Impact Statement
    st.markdown("---")
    inflation_impact = calculate_inflation_impact(10000, df_all, base_year=2020)
    
    if inflation_impact:
        current_amount = inflation_impact['current_amount']
        total_inflation = inflation_impact['total_inflation']
        latest_month = inflation_impact['latest_month']
        latest_index = inflation_impact['latest_index']
        
        # Format month nicely
        month_str = latest_month.strftime("%B %Y") if hasattr(latest_month, 'strftime') else str(latest_month)
        
        st.markdown(
            f"""
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 2rem; border-radius: 1rem; color: white; margin: 1.5rem 0;">
                <div style="font-size: 1.1rem; margin-bottom: 1rem; opacity: 0.95;">
                    💰 <strong>Inflation Impact</strong>
                </div>
                <div style="font-size: 1.5rem; font-weight: 700; margin-bottom: 0.5rem;">
                    If you spent <strong>10,000 SEK</strong> per month in 2020, you would be spending about
                </div>
                <div style="font-size: 2.5rem; font-weight: 800; margin: 1rem 0; text-shadow: 2px 2px 4px rgba(0,0,0,0.2);">
                    {current_amount:,.0f} SEK
                </div>
                <div style="font-size: 1rem; opacity: 0.9; margin-top: 1rem;">
                    Total inflation since 2020: <strong>{total_inflation:+.2f}%</strong> | 
                    CPI Index ({month_str}): <strong>{latest_index:.2f}</strong>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    # Summary Section with Info Cards
    st.markdown("---")
    st.markdown('<div class="section-header">📋 Summary</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 🏆 Top 5 Categories by Weight")
        top_weights = get_top_categories_by_weight(df_all, top_n=5)
        
        if not top_weights.empty:
            for idx, row in top_weights.iterrows():
                with st.container():
                    st.markdown(
                        f"""
                        <div style="background-color: #f0f2f6; padding: 1rem; border-radius: 0.5rem; margin-bottom: 0.5rem; border-left: 4px solid #1f77b4;">
                            <div style="font-weight: 600; font-size: 1rem; color: #1f77b4;">{row['Product group_label']}</div>
                            <div style="font-size: 1.5rem; font-weight: 700; color: #333;">{row['Weights']:.2f}%</div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
        else:
            st.info("No weight data available.")
    
    with col2:
        st.markdown("#### 🔥 Top 5 Inflation Drivers")
        top_drivers = get_top_inflation_drivers(df_all, top_n=5)
        
        if not top_drivers.empty:
            for idx, row in top_drivers.iterrows():
                with st.container():
                    contribution_color = "#d62728" if row['Contribution'] > 0 else "#2ca02c"
                    st.markdown(
                        f"""
                        <div style="background-color: #f0f2f6; padding: 1rem; border-radius: 0.5rem; margin-bottom: 0.5rem; border-left: 4px solid {contribution_color};">
                            <div style="font-weight: 600; font-size: 1rem; color: #1f77b4;">{row['Product group_label']}</div>
                            <div style="font-size: 1.5rem; font-weight: 700; color: {contribution_color};">
                                {row['Contribution']:+.2f}%
                            </div>
                            <div style="font-size: 0.85rem; color: #666; margin-top: 0.25rem;">
                                Annual: {row['Annual changes']:+.2f}% | Weight: {row['Weights']:.2f}%
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
        else:
            st.info("No inflation driver data available.")

    # Filter the cached dataframe based on user selections
    # No API call here - just filtering the already loaded data
    df_filtered = df_all[
        (df_all["Product group_label"].isin(selected_groups))
    ].copy()

    # Process data using business logic layer (works on cached dataframe)
    # already_filtered_top_level=True since fetch_all_data already filtered
    processed = process_cpi_data(df_filtered, selected_groups, selected_obs, already_filtered_top_level=True)

    # Main visualizations section
    st.markdown("---")
    st.markdown('<div class="section-header">📊 Visualizations</div>', unsafe_allow_html=True)
    
    # Display index chart (works on cached dataframe)
    if not processed["index_data"].empty and "Index" in processed["index_data"].columns:
        st.markdown("#### Index Over Time")
        fig = cpi_index_chart(processed["index_data"])
        if fig:
            st.plotly_chart(fig, width='stretch')
        st.markdown("")  # Add spacing

    # Inflation Contribution Chart (always show if data available)
    if "Weights" in df_all.columns:
        st.markdown("---")
        st.markdown("#### Inflation Contribution Analysis")
        st.caption("Shows how much each product group contributes to overall inflation. Contribution = (Annual Change × Weight) / 100")
        
        contributions = calculate_inflation_contributions(
            df_all,
            selected_groups,
            already_filtered_top_level=True
        )
        
        if not contributions.empty:
            fig = inflation_contribution_chart(
                contributions,
                title=f"Inflation Contribution: {', '.join(selected_groups)}"
            )
            if fig:
                st.plotly_chart(fig, width='content')
        else:
            st.info("ℹ️ No contribution data available. Weights data is required.")
        st.markdown("")  # Add spacing

    # Heatmap Visualization (always show)
        st.markdown("---")
        st.markdown("#### Annual Changes Heatmap")
        st.caption("Color intensity shows average annual inflation rate by year: 🔴 Red = High inflation, 🟢 Green = Low/Deflation")
        
        heatmap_data = prepare_heatmap_data(
            df_all,
            selected_groups,
            already_filtered_top_level=True
        )
        
        if not heatmap_data.empty:
            fig = annual_changes_heatmap(
                heatmap_data,
                title=f"Annual Changes by Product Group and Month"
            )
            if fig:
                st.plotly_chart(fig, width='content')
        else:
            st.info("ℹ️ No heatmap data available.")
        st.markdown("")  # Add spacing

    # Separate section for Weights visualization
    st.markdown("---")
    st.markdown('<div class="section-header">⚖️ Weights Analysis</div>', unsafe_allow_html=True)
    st.markdown("#### Product Group Weights Over Time")
    st.caption("Shows the relative importance (weight) of each product group in the CPI basket")
    
    # Separate multiselect for weights - independent from main product groups
    selected_groups_weights = st.multiselect(
        "🏷️ Product Groups (for Weights)",
        options=available_groups_in_data,
        default=[g for g in ["TOTAL"] if g in available_groups_in_data],
        key="weights_product_groups",  # Unique key to keep it separate
        help="Select product groups to compare their weights over time"
    )
    
    # Process weights data separately using its own selected groups
    if selected_groups_weights:
        weights_by_year = process_weights_data(
            df_all, 
            selected_groups_weights, 
            already_filtered_top_level=True
        )
        
        if not weights_by_year.empty:
            fig = weights_chart(
                weights_by_year,
                title=f"Weight of {', '.join(selected_groups_weights)} over time"
            )
            if fig:
                st.plotly_chart(fig, width='content')
        else:
            st.info("ℹ️ No weights data available for selected product groups.")
    else:
        st.info("ℹ️ Please select at least 1 product group to view weights.")