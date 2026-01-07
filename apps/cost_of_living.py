import streamlit as st
from lib.scb_client import SCBClientCOL

@st.cache_data(ttl=24*3600)
def get_client():
    return SCBClientCOL(table_id="KPI2020COICOPM")  # lots of product groups

@st.cache_data(ttl=6*3600)
def fetch_df(product_groups, observations, last_n):
    client = get_client()
    return client.fetch_cpi_dataframe(
        product_group_labels=product_groups,
        observations=observations,
        last_n_months=last_n,
        add_labels=True
    )

def render():
    st.subheader("Cost of Living Compass (CPI)")

    client = get_client()
    vars_ = client.get_variables()

    all_groups = vars_.get("Product group", [])
    all_obs = vars_.get("observations", ["Index", "Annual changes", "Monthly changes", "Weights"])

    selected_groups = st.multiselect(
        "Product groups",
        options=all_groups,
        default=[g for g in ["TOTAL", "FOOD AND NON-ALCOHOLIC BEVERAGES"] if g in all_groups]
    )

    selected_obs = st.multiselect(
        "Observations",
        options=all_obs,
        default=[o for o in ["Index", "Annual changes"] if o in all_obs]
    )

    last_n = st.slider("Last N months", 12, 240, 60)

    if not selected_groups or not selected_obs:
        st.info("Select at least 1 product group and 1 observation.")
        return

    df = fetch_df(selected_groups, selected_obs, last_n)

    st.dataframe(df.head(50), use_container_width=True)

    if "Index" in df.columns:
        import plotly.express as px
        fig = px.line(df, x="month", y="Index", color="Product group_label", title="Index over time")
        st.plotly_chart(fig, use_container_width=True)