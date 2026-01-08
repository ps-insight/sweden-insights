from typing import Optional
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

def line_chart(df: pd.DataFrame, x: str, y: str, color: str | None = None, title: str = ""):
    fig = px.line(df, x=x, y=y, color=color, title=title)
    fig.update_layout(
        margin=dict(l=10, r=10, t=50, b=10), 
        legend_title_text="",
        title_x=0.5  # Center the title
    )
    return fig


def cpi_index_chart(df: pd.DataFrame, x: str = "month", y: str = "Index", 
                    color: str = "Product group_label", title: str = "Index over time"):
    """Create a line chart for CPI index data."""
    if df.empty or y not in df.columns:
        return None
    fig = px.line(df, x=x, y=y, color=color, title=title)
    fig.update_layout(
        margin=dict(l=10, r=10, t=50, b=10), 
        legend_title_text="",
        title_x=0.5  # Center the title
    )
    return fig


def weights_chart(df: pd.DataFrame, x: str = "year", y: str = "Weights", 
                  color: str = "Product group_label", title: str = "Weights over time"):
    """Create a line chart for weights data with markers. Each product group is a separate line."""
    if df.empty or y not in df.columns:
        return None
    
    # Check if we have product group labels for multiple lines
    if color in df.columns and df[color].nunique() > 1:
        fig = px.line(df, x=x, y=y, color=color, title=title, markers=True)
        fig.update_layout(
            margin=dict(l=10, r=10, t=50, b=10), 
            legend_title_text="Product Group",
            title_x=0.5  # Center the title
        )
    else:
        # Single line if no color column or only one group
        fig = px.line(df, x=x, y=y, title=title, markers=True)
        fig.update_layout(
            margin=dict(l=10, r=10, t=50, b=10),
            title_x=0.5  # Center the title
        )
    
    return fig


def inflation_contribution_chart(df: pd.DataFrame, title: str = "Inflation Contribution by Product Group"):
    """
    Create a stacked area chart showing inflation contributions over time.
    Each product group's contribution = (Annual changes × Weights) / 100
    """
    if df.empty or "Contribution" not in df.columns:
        return None
    
    if "Product group_label" not in df.columns:
        return None
    
    # Create stacked area chart
    fig = px.area(
        df,
        x="month",
        y="Contribution",
        color="Product group_label",
        title=title,
        labels={
            "Contribution": "Contribution to Overall Inflation (%)",
            "month": "Month"
        }
    )
    
    fig.update_layout(
        margin=dict(l=10, r=10, t=50, b=10),
        legend_title_text="Product Group",
        hovermode='x unified',
        title_x=0.5  # Center the title
    )
    
    # Add horizontal line at y=0 for reference
    fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)
    
    return fig


def annual_changes_heatmap(heatmap_data: pd.DataFrame, title: str = "Annual Changes Heatmap"):
    """
    Create a heatmap showing annual changes by product group and year.
    
    Args:
        heatmap_data: Pivoted dataframe with product groups as rows, years as columns
        title: Chart title
    """
    if heatmap_data.empty:
        return None
    
    # Create heatmap using plotly
    fig = go.Figure(data=go.Heatmap(
        z=heatmap_data.values,
        x=heatmap_data.columns,
        y=heatmap_data.index,
        colorscale='RdYlGn_r',  # Red-Yellow-Green reversed (red = high inflation, green = low/deflation)
        colorbar=dict(title="Annual Change (%)"),
        text=heatmap_data.values.round(2),
        texttemplate='%{text}%',
        textfont={"size": 10},
        hovertemplate='<b>%{y}</b><br>Year: %{x}<br>Average Annual Change: %{z:.2f}%<extra></extra>'
    ))
    
    fig.update_layout(
        title=title,
        title_x=0.5,  # Center the title
        xaxis_title="Year",
        yaxis_title="Product Group",
        margin=dict(l=150, r=10, t=50, b=50),
        height=max(400, len(heatmap_data.index) * 40)  # Adjust height based on number of groups
    )
    
    # No need to rotate year labels - they're short
    fig.update_xaxes(tickangle=0)
    
    return fig


def _create_base_map_layout(title: str, height: int = 700, use_globe: bool = False) -> dict:
    """Create a base layout configuration for migration maps."""
    
    # Nordic-themed dark mode colors
    if use_globe:
        # 3D Globe projection - zoomed out view
        geo_config = dict(
            projection_type='orthographic',
            projection_rotation=dict(lon=15, lat=50, roll=0),  # Center on Europe
            projection_scale=0.6,  # Zoom out more - lower = more world visible
            showland=True,
            landcolor='#1e293b',  # Dark slate
            coastlinecolor='#475569',
            coastlinewidth=1,
            showocean=True,
            oceancolor='#0f172a',  # Deep dark blue
            showlakes=True,
            lakecolor='#0f172a',
            showcountries=True,
            countrycolor='#334155',
            countrywidth=0.5,
            bgcolor='#020617'  # Nearly black
        )
    else:
        # Natural Earth projection with dark theme - zoomed out to show most of world
        geo_config = dict(
            projection_type='natural earth',
            showland=True,
            landcolor='#1e293b',  # Dark slate
            coastlinecolor='#475569',
            coastlinewidth=1,
            showocean=True,
            oceancolor='#0f172a',  # Deep dark blue
            showlakes=True,
            lakecolor='#0f172a',
            showcountries=True,
            countrycolor='#334155',
            countrywidth=0.5,
            # Wide world view - fit most continents
            lataxis=dict(range=[-40, 85]),
            lonaxis=dict(range=[-100, 140]),
            bgcolor='#020617'  # Nearly black
        )
    
    return dict(
        title=dict(
            text=title,
            font=dict(size=22, color='#93c5fd', family='Arial, sans-serif', weight='bold'),  # Ice blue
            x=0.5,
            xanchor='center',
            y=0.98,
            yanchor='top'
        ),
        geo=geo_config,
        margin=dict(l=10, r=10, t=60, b=10),  # Small margins for centering
        height=height,
        width=None,  # Let it expand to container width
        autosize=True,
        uniformtext_minsize=8,
        uniformtext_mode='hide',
        paper_bgcolor='#020617',  # Nearly black
        plot_bgcolor='#020617',
        showlegend=False  # Remove legend
    )


def _create_arc_path(start_lon, start_lat, end_lon, end_lat, num_points=50):
    """
    Create a curved arc path between two geographic points.
    Uses great circle interpolation for realistic curved lines.
    """
    import numpy as np
    
    # Convert to radians
    lat1, lon1 = np.radians(start_lat), np.radians(start_lon)
    lat2, lon2 = np.radians(end_lat), np.radians(end_lon)
    
    # Create array of interpolation points
    t = np.linspace(0, 1, num_points)
    
    # Great circle interpolation
    d = np.arccos(np.sin(lat1) * np.sin(lat2) + 
                  np.cos(lat1) * np.cos(lat2) * np.cos(lon2 - lon1))
    
    if d == 0:
        # Points are the same
        return [start_lon], [start_lat]
    
    A = np.sin((1 - t) * d) / np.sin(d)
    B = np.sin(t * d) / np.sin(d)
    
    x = A * np.cos(lat1) * np.cos(lon1) + B * np.cos(lat2) * np.cos(lon2)
    y = A * np.cos(lat1) * np.sin(lon1) + B * np.cos(lat2) * np.sin(lon2)
    z = A * np.sin(lat1) + B * np.sin(lat2)
    
    # Convert back to degrees
    lat = np.degrees(np.arctan2(z, np.sqrt(x**2 + y**2)))
    lon = np.degrees(np.arctan2(y, x))
    
    return lon.tolist(), lat.tolist()


def immigration_flow_map(df: pd.DataFrame, year: Optional[int] = None, title: str = "Immigration to Sweden", use_globe: bool = False):
    """
    Create a world map showing immigration flows to Sweden.
    Line thickness represents immigration volume.
    
    Args:
        df: DataFrame with countrycode, Immigration, lat, lon columns
        year: Year for the visualization (for title)
        title: Chart title
        
    Returns:
        Plotly figure with world map and immigration flow lines
    """
    if df.empty or 'lat' not in df.columns or 'lon' not in df.columns:
        return None
    
    # Sweden coordinates
    sweden_lat, sweden_lon = 60.1282, 18.6435
    
    fig = go.Figure()
    
    # Filter for immigration flows only
    immigration_flows = df[df['Immigration'] > 0].copy()
    
    if not immigration_flows.empty:
        # Calculate max immigration for scaling
        max_immigration = immigration_flows['Immigration'].max()
        min_immigration = immigration_flows['Immigration'].min()
        
        for idx, (row_idx, row) in enumerate(immigration_flows.iterrows()):
            # Scale line width based on immigration volume (2-10px range)
            line_width = max(2, min(10, (row['Immigration'] / max_immigration) * 10))
            
            # Nordic gradient: light ice blue to bright cyan based on volume
            # Higher volume = brighter cyan
            volume_ratio = (row['Immigration'] - min_immigration) / (max_immigration - min_immigration) if max_immigration > min_immigration else 0.5
            
            # Create gradient from ice blue (#93c5fd) to bright cyan (#06b6d4)
            r = int(147 + (6 - 147) * volume_ratio)
            g = int(197 + (182 - 197) * volume_ratio)
            b = int(253 + (212 - 253) * volume_ratio)
            line_color = f'rgb({r}, {g}, {b})'
            
            country_name = row.get('countryname', row.get('countrycode', 'Unknown'))
            immigration_count = int(row['Immigration'])
            
            # Create curved arc path
            arc_lon, arc_lat = _create_arc_path(row['lon'], row['lat'], sweden_lon, sweden_lat, num_points=50)
            
            fig.add_trace(go.Scattergeo(
                lon=arc_lon,
                lat=arc_lat,
                mode='lines',
                line=dict(
                    width=line_width,
                    color=line_color
                ),
                opacity=0.8,
                name='Immigration',
                showlegend=False,
                hovertemplate=(
                    f"<b>{country_name} → Sweden</b><br>"
                    f"Immigration: {immigration_count:,} people<br>"
                    f"<extra></extra>"
                ),
                hoverinfo='text'
            ))
    
    # Add country markers with immigration numbers
    if not immigration_flows.empty:
        # Scale marker size based on immigration volume
        max_immigration = immigration_flows['Immigration'].max()
        marker_sizes = [
            max(10, min(25, (x / max_immigration) * 25))
            for x in immigration_flows['Immigration']
        ]
        
        fig.add_trace(go.Scattergeo(
            lon=immigration_flows['lon'],
            lat=immigration_flows['lat'],
            mode='markers',
            marker=dict(
                size=marker_sizes,
                color='#06b6d4',  # Bright cyan
                opacity=0.9,
                line=dict(width=2, color='#0891b2'),  # Darker cyan border
                sizemode='diameter'
            ),
            text=immigration_flows.get('countryname', immigration_flows.get('countrycode', '')),
            name='Origin Countries',
            showlegend=False,
            hovertemplate=(
                "<b>%{text}</b><br>" +
                "Immigration: %{customdata:,} people<br>" +
                "<extra></extra>"
            ),
            customdata=immigration_flows['Immigration']
        ))
    
    # Add Sweden marker (highlighted with glow effect)
    fig.add_trace(go.Scattergeo(
        lon=[sweden_lon],
        lat=[sweden_lat],
        mode='markers',
        marker=dict(
            size=30,
            color='#fbbf24',  # Golden yellow for Sweden
            line=dict(width=4, color='#f59e0b'),  # Amber border
            symbol='star',
            opacity=1
        ),
        text=['Sweden'],
        name='Sweden',
        showlegend=False,
        hovertemplate="<b>🇸🇪 Sweden</b><br>Destination for immigration<extra></extra>"
    ))
    
    # Update layout
    year_suffix = f" ({year})" if year else " (All Years)"
    full_title = f"🌍 {title}{year_suffix}"
    fig.update_layout(**_create_base_map_layout(full_title, use_globe=use_globe))
    
    return fig


def emigration_flow_map(df: pd.DataFrame, year: Optional[int] = None, title: str = "Emigration from Sweden", use_globe: bool = False):
    """
    Create a world map showing emigration flows from Sweden.
    Line thickness represents emigration volume.
    
    Args:
        df: DataFrame with countrycode, Emigration, lat, lon columns
        year: Year for the visualization (for title)
        title: Chart title
        
    Returns:
        Plotly figure with world map and emigration flow lines
    """
    if df.empty or 'lat' not in df.columns or 'lon' not in df.columns:
        return None
    
    # Sweden coordinates
    sweden_lat, sweden_lon = 60.1282, 18.6435
    
    fig = go.Figure()
    
    # Filter for emigration flows only
    emigration_flows = df[df['Emigration'] > 0].copy()
    
    if not emigration_flows.empty:
        # Calculate max emigration for scaling
        max_emigration = emigration_flows['Emigration'].max()
        min_emigration = emigration_flows['Emigration'].min()
        
        for idx, (row_idx, row) in enumerate(emigration_flows.iterrows()):
            # Scale line width based on emigration volume (2-10px range)
            line_width = max(2, min(10, (row['Emigration'] / max_emigration) * 10))
            
            # Warm gradient: light coral to bright orange based on volume
            # Higher volume = brighter orange
            volume_ratio = (row['Emigration'] - min_emigration) / (max_emigration - min_emigration) if max_emigration > min_emigration else 0.5
            
            # Create gradient from light coral (#fb923c) to bright orange/red (#f97316)
            r = int(251 + (249 - 251) * volume_ratio)
            g = int(146 + (115 - 146) * volume_ratio)
            b = int(60 + (22 - 60) * volume_ratio)
            line_color = f'rgb({r}, {g}, {b})'
            
            country_name = row.get('countryname', row.get('countrycode', 'Unknown'))
            emigration_count = int(row['Emigration'])
            
            # Create curved arc path
            arc_lon, arc_lat = _create_arc_path(sweden_lon, sweden_lat, row['lon'], row['lat'], num_points=50)
            
            fig.add_trace(go.Scattergeo(
                lon=arc_lon,
                lat=arc_lat,
                mode='lines',
                line=dict(
                    width=line_width,
                    color=line_color
                ),
                opacity=0.8,
                name='Emigration',
                showlegend=False,
                hovertemplate=(
                    f"<b>Sweden → {country_name}</b><br>"
                    f"Emigration: {emigration_count:,} people<br>"
                    f"<extra></extra>"
                ),
                hoverinfo='text'
            ))
    
    # Add country markers with emigration numbers
    if not emigration_flows.empty:
        # Scale marker size based on emigration volume
        max_emigration = emigration_flows['Emigration'].max()
        marker_sizes = [
            max(10, min(25, (x / max_emigration) * 25))
            for x in emigration_flows['Emigration']
        ]
        
        fig.add_trace(go.Scattergeo(
            lon=emigration_flows['lon'],
            lat=emigration_flows['lat'],
            mode='markers',
            marker=dict(
                size=marker_sizes,
                color='#f97316',  # Bright orange
                opacity=0.9,
                line=dict(width=2, color='#ea580c'),  # Darker orange border
                sizemode='diameter'
            ),
            text=emigration_flows.get('countryname', emigration_flows.get('countrycode', '')),
            name='Destination Countries',
            showlegend=False,
            hovertemplate=(
                "<b>%{text}</b><br>" +
                "Emigration: %{customdata:,} people<br>" +
                "<extra></extra>"
            ),
            customdata=emigration_flows['Emigration']
        ))
    
    # Add Sweden marker (highlighted with glow effect)
    fig.add_trace(go.Scattergeo(
        lon=[sweden_lon],
        lat=[sweden_lat],
        mode='markers',
        marker=dict(
            size=30,
            color='#fbbf24',  # Golden yellow for Sweden
            line=dict(width=4, color='#f59e0b'),  # Amber border
            symbol='star',
            opacity=1
        ),
        text=['Sweden'],
        name='Sweden',
        showlegend=False,
        hovertemplate="<b>🇸🇪 Sweden</b><br>Origin for emigration<extra></extra>"
    ))
    
    # Update layout
    year_suffix = f" ({year})" if year else " (All Years)"
    full_title = f"🌍 {title}{year_suffix}"
    fig.update_layout(**_create_base_map_layout(full_title, use_globe=use_globe))
    
    return fig


def migration_flow_map(df: pd.DataFrame, year: Optional[int] = None, title: str = "Migration Flows to/from Sweden"):
    """
    Create a world map showing migration flows to and from Sweden.
    Line thickness represents migration volume.
    
    Args:
        df: DataFrame with countrycode, Immigration, Emigration, lat, lon columns
        year: Year for the visualization (for title)
        title: Chart title
        
    Returns:
        Plotly figure with world map and flow lines
    """
    if df.empty or 'lat' not in df.columns or 'lon' not in df.columns:
        return None
    
    # Sweden coordinates
    sweden_lat, sweden_lon = 60.1282, 18.6435
    
    fig = go.Figure()
    
    # Add immigration flows (to Sweden) - green lines
    immigration_flows = df[df['Immigration'] > 0].copy()
    if not immigration_flows.empty:
        for idx, (row_idx, row) in enumerate(immigration_flows.iterrows()):
            fig.add_trace(go.Scattergeo(
                lon=[row['lon'], sweden_lon],
                lat=[row['lat'], sweden_lat],
                mode='lines',
                line=dict(
                    width=max(1, min(10, row['Immigration'] / 1000)),  # Scale line width
                    color='#2ca02c'  # Green for immigration
                ),
                opacity=0.6,
                name='Immigration',
                showlegend=bool(idx == 0),  # Convert to Python bool - only show once in legend
                hovertemplate=f"<b>{row.get('countryname', row['countrycode'])} → Sweden</b><br>Immigration: {row['Immigration']:,.0f}<extra></extra>"
            ))
    
    # Add emigration flows (from Sweden) - red lines
    emigration_flows = df[df['Emigration'] > 0].copy()
    if not emigration_flows.empty:
        for idx, (row_idx, row) in enumerate(emigration_flows.iterrows()):
            fig.add_trace(go.Scattergeo(
                lon=[sweden_lon, row['lon']],
                lat=[sweden_lat, row['lat']],
                mode='lines',
                line=dict(
                    width=max(1, min(10, row['Emigration'] / 1000)),  # Scale line width
                    color='#d62728'  # Red for emigration
                ),
                opacity=0.6,
                name='Emigration',
                showlegend=bool(idx == 0),  # Convert to Python bool - only show once in legend
                hovertemplate=f"<b>Sweden → {row.get('countryname', row['countrycode'])}</b><br>Emigration: {row['Emigration']:,.0f}<extra></extra>"
            ))
    
    # Add country markers
    fig.add_trace(go.Scattergeo(
        lon=df['lon'],
        lat=df['lat'],
        mode='markers',
        marker=dict(
            size=8,
            color='lightblue',
            line=dict(width=1, color='darkblue')
        ),
        text=df.get('countryname', df['countrycode']),
        name='Countries',
        hovertemplate="<b>%{text}</b><extra></extra>"
    ))
    
    # Add Sweden marker (highlighted)
    fig.add_trace(go.Scattergeo(
        lon=[sweden_lon],
        lat=[sweden_lat],
        mode='markers',
        marker=dict(
            size=15,
            color='#ff7f0e',  # Orange for Sweden
            line=dict(width=2, color='darkorange')
        ),
        text=['Sweden'],
        name='Sweden',
        hovertemplate="<b>Sweden</b><extra></extra>"
    ))
    
    # Update layout
    fig.update_layout(
        title=title + (f" ({year})" if year else ""),
        geo=dict(
            projection_type='natural earth',
            showland=True,
            landcolor='rgb(243, 243, 243)',
            coastlinecolor='rgb(204, 204, 204)',
            showocean=True,
            oceancolor='rgb(230, 245, 255)',
            showlakes=True,
            lakecolor='rgb(230, 245, 255)',
            showcountries=True,
            countrycolor='rgb(204, 204, 204)',
            lataxis=dict(range=[30, 75]),  # Focus on Europe/Northern hemisphere
            lonaxis=dict(range=[-20, 50])
        ),
        margin=dict(l=0, r=0, t=50, b=0),
        height=600,
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.01
        )
    )
    
    return fig