"""
Business logic for Cost of Living (CPI) data processing.
Separates data transformation logic from UI layer.
"""
from typing import List, Dict, Tuple
import pandas as pd
from lib.scb_client import SCBClientCOL


def filter_top_level_product_groups(df: pd.DataFrame) -> pd.DataFrame:
    """
    Filter dataframe to keep only 2-digit product group codes.
    Excludes sub-headers with decimal points (e.g., "01.1", "01.10").
    
    Args:
        df: DataFrame with "Product group" column
        
    Returns:
        Filtered DataFrame with only 2-digit codes
    """
    if "Product group" not in df.columns:
        return df
    
    return df[df["Product group"].str.match(r'^\d{2}$', na=False)].copy()


def get_top_level_product_groups(client: SCBClientCOL) -> List[str]:
    """
    Get product group labels that correspond to 2-digit codes only.
    This excludes sub-categories like "01.1", "01.10", etc.
    
    Args:
        client: SCBClientCOL instance
        
    Returns:
        List of product group labels for top-level (2-digit) categories only
    """
    try:
        # Get code-to-label mapping from client
        code_to_label = client.get_product_group_code_mapping()
        
        if not code_to_label:
            # Fallback: try to get all groups from variables
            try:
                variables = client.get_variables()
                return variables.get("Product group", [])
            except Exception:
                # If that also fails, return empty list
                return []
        
        # Filter codes to only 2-digit ones
        top_level_codes = [
            code for code in code_to_label.keys()
            if pd.Series([str(code)]).str.match(r'^\d{2}$', na=False).iloc[0]
        ]
        
        # Get corresponding labels
        top_level_labels = [
            code_to_label[code] 
            for code in top_level_codes 
            if code in code_to_label
        ]
        
        return top_level_labels
        
    except Exception:
        # Fallback: try to get all groups if anything fails
        try:
            variables = client.get_variables()
            return variables.get("Product group", [])
        except Exception:
            # If everything fails, return empty list
            return []


def process_cpi_data(
    df: pd.DataFrame,
    selected_groups: List[str],
    selected_observations: List[str],
    already_filtered_top_level: bool = False
) -> Dict[str, pd.DataFrame]:
    """
    Process CPI dataframe: filter, transform, and prepare for visualization.
    
    Args:
        df: CPI dataframe (may already be filtered to top-level groups)
        selected_groups: Selected product group labels
        selected_observations: Selected observation types
        already_filtered_top_level: If True, skip top-level filtering (already done)
        
    Returns:
        Dictionary with processed dataframes:
        - 'filtered': Filtered by selected groups and top-level codes
        - 'index_data': Data for index visualization
        - 'weights_data': Data for weights visualization
        - 'weights_by_year': Aggregated weights by year
    """
    # Filter to top-level product groups only (if not already done)
    if not already_filtered_top_level:
        df = filter_top_level_product_groups(df)
    
    # Filter by selected groups
    if "Product group_label" in df.columns:
        df_filtered = df[df["Product group_label"].isin(selected_groups)].copy()
    else:
        df_filtered = df.copy()
    
    # Prepare index data
    index_data = df_filtered.copy() if "Index" in df_filtered.columns else pd.DataFrame()
    
    # Prepare weights data
    weights_data = df_filtered[
        (df_filtered["Product group_label"].isin(selected_groups)) &
        (df_filtered["Weights"].notna())
    ].copy()
    
    # Aggregate weights by year
    weights_by_year = pd.DataFrame()
    if not weights_data.empty and "month" in weights_data.columns:
        weights_data["year"] = weights_data["month"].dt.year
        weights_by_year = (
            weights_data
            .groupby("year", as_index=False)["Weights"]
            .mean()
        )
    
    return {
        "filtered": df_filtered,
        "index_data": index_data,
        "weights_data": weights_data,
        "weights_by_year": weights_by_year
    }


def process_weights_data(
    df: pd.DataFrame,
    selected_groups: List[str],
    already_filtered_top_level: bool = False
) -> pd.DataFrame:
    """
    Process weights data separately with its own product group selection.
    Each product group is kept separate for individual line charts.
    
    Args:
        df: CPI dataframe (may already be filtered to top-level groups)
        selected_groups: Selected product group labels for weights
        already_filtered_top_level: If True, skip top-level filtering (already done)
        
    Returns:
        Aggregated weights dataframe by year and product group (one line per group)
    """
    # Filter to top-level product groups only (if not already done)
    if not already_filtered_top_level:
        df = filter_top_level_product_groups(df)
    
    # Filter by selected groups for weights
    if "Product group_label" in df.columns:
        weights_data = df[
            (df["Product group_label"].isin(selected_groups)) &
            (df["Weights"].notna())
        ].copy()
    else:
        weights_data = df[df["Weights"].notna()].copy()
    
    # Aggregate weights by year AND product group (keep groups separate)
    weights_by_year = pd.DataFrame()
    if not weights_data.empty and "month" in weights_data.columns:
        weights_data["year"] = weights_data["month"].dt.year
        
        # Group by both year and product group to keep each group as separate line
        if "Product group_label" in weights_data.columns:
            weights_by_year = (
                weights_data
                .groupby(["year", "Product group_label"], as_index=False)["Weights"]
                .mean()
            )
        else:
            # Fallback if no product group label
            weights_by_year = (
                weights_data
                .groupby("year", as_index=False)["Weights"]
                .mean()
            )
    
    return weights_by_year


def calculate_inflation_contributions(
    df: pd.DataFrame,
    selected_groups: List[str],
    already_filtered_top_level: bool = False
) -> pd.DataFrame:
    """
    Calculate inflation contributions for each product group.
    Contribution = (Annual changes × Weights) / 100
    
    Args:
        df: CPI dataframe (may already be filtered to top-level groups)
        selected_groups: Selected product group labels
        already_filtered_top_level: If True, skip top-level filtering (already done)
        
    Returns:
        Dataframe with inflation contributions by month and product group
    """
    # Filter to top-level product groups only (if not already done)
    if not already_filtered_top_level:
        df = filter_top_level_product_groups(df)
    
    # Filter by selected groups
    if "Product group_label" in df.columns:
        df_filtered = df[
            (df["Product group_label"].isin(selected_groups)) &
            (df["Annual changes"].notna()) &
            (df["Weights"].notna())
        ].copy()
    else:
        df_filtered = df[
            (df["Annual changes"].notna()) &
            (df["Weights"].notna())
        ].copy()
    
    if df_filtered.empty:
        return pd.DataFrame()
    
    # Calculate contribution: (Annual changes × Weights) / 100
    df_filtered["Contribution"] = (df_filtered["Annual changes"] * df_filtered["Weights"]) / 100
    
    # Keep relevant columns
    result = df_filtered[["month", "Product group_label", "Contribution", "Annual changes", "Weights"]].copy()
    
    return result


def prepare_heatmap_data(
    df: pd.DataFrame,
    selected_groups: List[str],
    already_filtered_top_level: bool = False
) -> pd.DataFrame:
    """
    Prepare data for heatmap visualization of annual changes aggregated by year.
    
    Args:
        df: CPI dataframe (may already be filtered to top-level groups)
        selected_groups: Selected product group labels
        already_filtered_top_level: If True, skip top-level filtering (already done)
        
    Returns:
        Pivoted dataframe ready for heatmap: rows = product groups, columns = years
    """
    # Filter to top-level product groups only (if not already done)
    if not already_filtered_top_level:
        df = filter_top_level_product_groups(df)
    
    # Filter by selected groups
    if "Product group_label" in df.columns:
        df_filtered = df[
            (df["Product group_label"].isin(selected_groups)) &
            (df["Annual changes"].notna())
        ].copy()
    else:
        df_filtered = df[df["Annual changes"].notna()].copy()
    
    if df_filtered.empty or "Annual changes" not in df_filtered.columns:
        return pd.DataFrame()
    
    # Extract year from month column
    if "month" in df_filtered.columns:
        df_filtered["year"] = df_filtered["month"].dt.year
    else:
        return pd.DataFrame()
    
    # Aggregate annual changes by year and product group (average across months in each year)
    if "Product group_label" in df_filtered.columns:
        # Group by year and product group, then average the annual changes
        yearly_data = (
            df_filtered
            .groupby(["Product group_label", "year"], as_index=False)["Annual changes"]
            .mean()
        )
        
        # Pivot: product groups as rows, years as columns, annual changes as values
        heatmap_data = yearly_data.pivot_table(
            index="Product group_label",
            columns="year",
            values="Annual changes",
            aggfunc="mean"
        )
    else:
        return pd.DataFrame()
    
    return heatmap_data


def get_top_categories_by_weight(df: pd.DataFrame, top_n: int = 5) -> pd.DataFrame:
    """
    Get top N categories by weight (most recent available).
    
    Args:
        df: CPI dataframe
        top_n: Number of top categories to return
        
    Returns:
        Dataframe with top categories by weight
    """
    if df.empty or "Weights" not in df.columns or "Product group_label" not in df.columns:
        return pd.DataFrame()
    
    # Filter to only rows with weights
    weights_data = df[df["Weights"].notna()].copy()
    
    # Exclude TOTAL category
    if "Product group_label" in weights_data.columns:
        weights_data = weights_data[
            ~weights_data["Product group_label"].str.upper().str.contains("TOTAL", na=False)
        ]
    
    if weights_data.empty:
        return pd.DataFrame()
    
    # Get most recent month
    if "month" in weights_data.columns:
        latest_month = weights_data["month"].max()
        latest_data = weights_data[weights_data["month"] == latest_month].copy()
    else:
        latest_data = weights_data.copy()
    
    # Get top N by weight
    top_categories = (
        latest_data
        .nlargest(top_n, "Weights")[["Product group_label", "Weights"]]
        .sort_values("Weights", ascending=False)
    )
    
    return top_categories


def get_top_inflation_drivers(df: pd.DataFrame, top_n: int = 5) -> pd.DataFrame:
    """
    Get top N drivers of inflation based on contribution.
    Contribution = (Annual Change × Weight) / 100
    
    Args:
        df: CPI dataframe
        top_n: Number of top drivers to return
        
    Returns:
        Dataframe with top inflation drivers
    """
    if df.empty:
        return pd.DataFrame()
    
    # Need both Annual changes and Weights
    if "Annual changes" not in df.columns or "Weights" not in df.columns:
        return pd.DataFrame()
    
    if "Product group_label" not in df.columns:
        return pd.DataFrame()
    
    # Filter to rows with both annual changes and weights
    driver_data = df[
        (df["Annual changes"].notna()) &
        (df["Weights"].notna())
    ].copy()
    
    # Exclude TOTAL category
    if "Product group_label" in driver_data.columns:
        driver_data = driver_data[
            ~driver_data["Product group_label"].str.upper().str.contains("TOTAL", na=False)
        ]
    
    if driver_data.empty:
        return pd.DataFrame()
    
    # Get most recent month
    if "month" in driver_data.columns:
        latest_month = driver_data["month"].max()
        latest_data = driver_data[driver_data["month"] == latest_month].copy()
    else:
        latest_data = driver_data.copy()
    
    # Calculate contribution
    latest_data["Contribution"] = (latest_data["Annual changes"] * latest_data["Weights"]) / 100
    
    # Get top N by contribution
    top_drivers = (
        latest_data
        .nlargest(top_n, "Contribution")[["Product group_label", "Contribution", "Annual changes", "Weights"]]
        .sort_values("Contribution", ascending=False)
    )
    
    return top_drivers


def calculate_inflation_impact(base_amount: float, df: pd.DataFrame, base_year: int = 2020) -> dict:
    """
    Calculate how much a base amount from the base year would be worth today.
    
    Args:
        base_amount: Amount in base year (e.g., 10000 SEK in 2020)
        df: CPI dataframe with Index data
        base_year: Base year for CPI (default 2020, where index = 100)
        
    Returns:
        Dictionary with:
        - 'current_amount': Calculated current amount
        - 'latest_index': Latest index value
        - 'latest_month': Latest month in data
        - 'total_inflation': Total inflation percentage since base year
    """
    if df.empty or "Index" not in df.columns:
        return None
    
    # Filter for TOTAL product group if available
    if "Product group_label" in df.columns:
        total_data = df[df["Product group_label"] == "TOTAL"].copy()
        if total_data.empty:
            # If TOTAL not available, use first available group
            total_data = df.copy()
    else:
        total_data = df.copy()
    
    if total_data.empty or "month" not in total_data.columns:
        return None
    
    # Get latest month's index
    latest_month = total_data["month"].max()
    latest_data = total_data[total_data["month"] == latest_month]
    
    if latest_data.empty or "Index" not in latest_data.columns:
        return None
    
    latest_index = latest_data["Index"].iloc[0]
    
    # Calculate current amount: base_amount * (current_index / base_index)
    # Base index is 100 for year 2020
    base_index = 100.0
    current_amount = base_amount * (latest_index / base_index)
    
    # Calculate total inflation percentage
    total_inflation = ((latest_index - base_index) / base_index) * 100
    
    return {
        'current_amount': current_amount,
        'latest_index': latest_index,
        'latest_month': latest_month,
        'total_inflation': total_inflation
    }
