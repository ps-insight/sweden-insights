import streamlit as st
import pandas as pd
from lib.viz import line_chart

def render():
    st.subheader("Migration & Movement Atlas")
    st.info("Next: wire net migration by region + map + rankings.")

    # placeholder demo data
    df = pd.DataFrame({
        "year": list(range(2010, 2025)),
        "net_migration": [50000 + i * 1200 for i in range(15)]
    })
    st.plotly_chart(line_chart(df, x="year", y="net_migration", title="Demo: Net migration"), use_container_width=True)