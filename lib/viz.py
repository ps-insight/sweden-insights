import pandas as pd
import plotly.express as px

def line_chart(df: pd.DataFrame, x: str, y: str, color: str | None = None, title: str = ""):
    fig = px.line(df, x=x, y=y, color=color, title=title)
    fig.update_layout(margin=dict(l=10, r=10, t=50, b=10), legend_title_text="")
    return fig