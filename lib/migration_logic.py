"""
Business logic for Migration data processing.
Separates data transformation logic from UI layer.
"""
from typing import List, Dict, Optional
import pandas as pd
from lib.scb_client import SCBClientMigration


def get_country_code_to_name_mapping() -> Dict[str, str]:
    """
    Get mapping from ISO 3166-1 alpha-2 country codes to country names.
    
    Returns:
        Dictionary mapping country codes to country names
    """
    return {
        'AF': 'Afghanistan', 'AL': 'Albania', 'DZ': 'Algeria', 'AD': 'Andorra', 'AO': 'Angola',
        'AI': 'Anguilla', 'AG': 'Antigua and Barbuda', 'AR': 'Argentina', 'AM': 'Armenia',
        'AU': 'Australia', 'AT': 'Austria', 'AZ': 'Azerbaijan', 'BS': 'Bahamas', 'BH': 'Bahrain',
        'BD': 'Bangladesh', 'BB': 'Barbados', 'BY': 'Belarus', 'BE': 'Belgium', 'BZ': 'Belize',
        'BJ': 'Benin', 'BM': 'Bermuda', 'BT': 'Bhutan', 'BO': 'Bolivia', 'BA': 'Bosnia and Herzegovina',
        'BW': 'Botswana', 'BR': 'Brazil', 'VG': 'British Virgin Islands', 'BN': 'Brunei',
        'BG': 'Bulgaria', 'BF': 'Burkina Faso', 'BI': 'Burundi', 'KH': 'Cambodia', 'CM': 'Cameroon',
        'CA': 'Canada', 'CV': 'Cape Verde', 'KY': 'Cayman Islands', 'CF': 'Central African Republic',
        'TD': 'Chad', 'CL': 'Chile', 'CN': 'China', 'CO': 'Colombia', 'KM': 'Comoros',
        'CG': 'Congo', 'CD': 'Congo (DRC)', 'CR': 'Costa Rica', 'CI': "Côte d'Ivoire",
        'HR': 'Croatia', 'CU': 'Cuba', 'CY': 'Cyprus', 'CZ': 'Czech Republic', 'DK': 'Denmark',
        'DJ': 'Djibouti', 'DM': 'Dominica', 'DO': 'Dominican Republic', 'EC': 'Ecuador',
        'EG': 'Egypt', 'SV': 'El Salvador', 'GQ': 'Equatorial Guinea', 'ER': 'Eritrea',
        'EE': 'Estonia', 'SZ': 'Eswatini', 'ET': 'Ethiopia', 'FJ': 'Fiji', 'FI': 'Finland',
        'FR': 'France', 'GA': 'Gabon', 'GM': 'Gambia', 'GE': 'Georgia', 'DE': 'Germany',
        'GH': 'Ghana', 'GI': 'Gibraltar', 'GR': 'Greece', 'GD': 'Grenada', 'GT': 'Guatemala',
        'GN': 'Guinea', 'GW': 'Guinea-Bissau', 'GY': 'Guyana', 'HT': 'Haiti', 'HN': 'Honduras',
        'HK': 'Hong Kong', 'HU': 'Hungary', 'IS': 'Iceland', 'IN': 'India', 'ID': 'Indonesia',
        'IR': 'Iran', 'IQ': 'Iraq', 'IE': 'Ireland', 'IL': 'Israel', 'IT': 'Italy',
        'JM': 'Jamaica', 'JP': 'Japan', 'JO': 'Jordan', 'KZ': 'Kazakhstan', 'KE': 'Kenya',
        'KI': 'Kiribati', 'KP': 'North Korea', 'KR': 'South Korea', 'KW': 'Kuwait',
        'KG': 'Kyrgyzstan', 'LA': 'Laos', 'LV': 'Latvia', 'LB': 'Lebanon', 'LS': 'Lesotho',
        'LR': 'Liberia', 'LY': 'Libya', 'LI': 'Liechtenstein', 'LT': 'Lithuania', 'LU': 'Luxembourg',
        'MK': 'North Macedonia', 'MG': 'Madagascar', 'MW': 'Malawi', 'MY': 'Malaysia',
        'MV': 'Maldives', 'ML': 'Mali', 'MT': 'Malta', 'MH': 'Marshall Islands', 'MR': 'Mauritania',
        'MU': 'Mauritius', 'MX': 'Mexico', 'FM': 'Micronesia', 'MD': 'Moldova', 'MC': 'Monaco',
        'MN': 'Mongolia', 'ME': 'Montenegro', 'MA': 'Morocco', 'MZ': 'Mozambique', 'MM': 'Myanmar',
        'NA': 'Namibia', 'NR': 'Nauru', 'NP': 'Nepal', 'NL': 'Netherlands', 'NZ': 'New Zealand',
        'NI': 'Nicaragua', 'NE': 'Niger', 'NG': 'Nigeria', 'NO': 'Norway', 'OM': 'Oman',
        'PK': 'Pakistan', 'PW': 'Palau', 'PS': 'Palestine', 'PA': 'Panama', 'PG': 'Papua New Guinea',
        'PY': 'Paraguay', 'PE': 'Peru', 'PH': 'Philippines', 'PL': 'Poland', 'PT': 'Portugal',
        'QA': 'Qatar', 'RO': 'Romania', 'RU': 'Russia', 'RW': 'Rwanda', 'KN': 'Saint Kitts and Nevis',
        'LC': 'Saint Lucia', 'VC': 'Saint Vincent and the Grenadines', 'WS': 'Samoa',
        'SM': 'San Marino', 'ST': 'São Tomé and Príncipe', 'SA': 'Saudi Arabia', 'SN': 'Senegal',
        'RS': 'Serbia', 'SC': 'Seychelles', 'SL': 'Sierra Leone', 'SG': 'Singapore',
        'SK': 'Slovakia', 'SI': 'Slovenia', 'SB': 'Solomon Islands', 'SO': 'Somalia',
        'ZA': 'South Africa', 'ES': 'Spain', 'LK': 'Sri Lanka', 'SD': 'Sudan', 'SR': 'Suriname',
        'SE': 'Sweden', 'CH': 'Switzerland', 'SY': 'Syria', 'TW': 'Taiwan', 'TJ': 'Tajikistan',
        'TZ': 'Tanzania', 'TH': 'Thailand', 'TL': 'Timor-Leste', 'TG': 'Togo', 'TO': 'Tonga',
        'TT': 'Trinidad and Tobago', 'TN': 'Tunisia', 'TR': 'Turkey', 'TM': 'Turkmenistan',
        'TV': 'Tuvalu', 'UG': 'Uganda', 'UA': 'Ukraine', 'AE': 'United Arab Emirates',
        'GB': 'United Kingdom', 'US': 'United States', 'UY': 'Uruguay', 'UZ': 'Uzbekistan',
        'VU': 'Vanuatu', 'VA': 'Vatican City', 'VE': 'Venezuela', 'VN': 'Vietnam',
        'YE': 'Yemen', 'ZM': 'Zambia', 'ZW': 'Zimbabwe', 'XK': 'Kosovo', 'CS': 'Serbia and Montenegro',
        'SU': 'Soviet Union', 'YU': 'Yugoslavia', 'QT': 'Other/Unknown', 'ÖOF': 'Other/Unknown'
    }


def map_country_codes_to_names(df: pd.DataFrame) -> pd.DataFrame:
    """
    Replace country codes with country names in the dataframe.
    
    Args:
        df: DataFrame with 'countrycode' column
        
    Returns:
        DataFrame with 'countrycode' replaced by 'countryname' column
    """
    if df.empty or 'countrycode' not in df.columns:
        return df
    
    df = df.copy()
    
    # Get country code to name mapping
    country_map = get_country_code_to_name_mapping()
    
    # Map country codes to names
    df['countryname'] = df['countrycode'].map(country_map).fillna(df['countrycode'])
    
    # Optionally, keep both columns or replace countrycode
    # For now, we'll keep both - countrycode for coordinates, countryname for display
    
    return df


def calculate_net_migration(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate net migration (Immigration - Emigration) from migration dataframe.
    
    Args:
        df: DataFrame with Immigration and Emigration columns
        
    Returns:
        DataFrame with added 'net_migration' column
    """
    if df.empty:
        return df
    
    df = df.copy()
    
    # Calculate net migration
    if "Immigration" in df.columns and "Emigration" in df.columns:
        df["net_migration"] = df["Immigration"] - df["Emigration"]
    
    return df


def aggregate_by_year(df: pd.DataFrame, group_by: Optional[List[str]] = None) -> pd.DataFrame:
    """
    Aggregate migration data by year and optional other dimensions.
    
    Args:
        df: Migration dataframe
        group_by: List of columns to group by (default: ['year'])
        
    Returns:
        Aggregated dataframe
    """
    if df.empty:
        return df
    
    if group_by is None:
        group_by = ["year"]
    
    # Ensure all group_by columns exist
    group_by = [col for col in group_by if col in df.columns]
    
    if not group_by:
        return df
    
    # Columns to aggregate
    agg_cols = {}
    if "Immigration" in df.columns:
        agg_cols["Immigration"] = "sum"
    if "Emigration" in df.columns:
        agg_cols["Emigration"] = "sum"
    if "net_migration" in df.columns:
        agg_cols["net_migration"] = "sum"
    
    if not agg_cols:
        return df
    
    # Aggregate
    aggregated = df.groupby(group_by, as_index=False).agg(agg_cols)
    
    return aggregated


def get_top_immigration_countries(df: pd.DataFrame, top_n: int = 10, year: Optional[int] = None) -> pd.DataFrame:
    """
    Get top N countries by immigration.
    
    Args:
        df: Migration dataframe
        top_n: Number of top countries to return
        year: Specific year to filter (None = use latest year)
        
    Returns:
        DataFrame with top countries by immigration
    """
    if df.empty or "Immigration" not in df.columns or "countrycode" not in df.columns:
        return pd.DataFrame()
    
    df_filtered = df.copy()
    
    # Remove Sweden from the list (SE is the destination, not a source)
    if "countrycode" in df_filtered.columns:
        df_filtered = df_filtered[df_filtered["countrycode"].str.upper() != "SE"]
    
    # Filter by year if specified
    if year and "year" in df_filtered.columns:
        # Convert to string for comparison to handle type mismatch
        df_filtered = df_filtered[df_filtered["year"].astype(str) == str(year)]
    elif "year" in df_filtered.columns:
        # Use latest year if not specified
        latest_year = df_filtered["year"].max()
        df_filtered = df_filtered[df_filtered["year"].astype(str) == str(latest_year)]
    
    # Aggregate by country (sum across genders if gender column exists)
    if "gender" in df_filtered.columns:
        top_countries = (
            df_filtered
            .groupby("countrycode", as_index=False)["Immigration"]
            .sum()
            .nlargest(top_n, "Immigration")
            .sort_values("Immigration", ascending=False)
        )
    else:
        top_countries = (
            df_filtered
            .nlargest(top_n, "Immigration")[["countrycode", "Immigration"]]
            .sort_values("Immigration", ascending=False)
        )
    
    # Add country names if available in original dataframe
    if "countryname" in df_filtered.columns:
        country_name_map = df_filtered[["countrycode", "countryname"]].drop_duplicates().set_index("countrycode")["countryname"]
        top_countries["countryname"] = top_countries["countrycode"].map(country_name_map)
        # Reorder columns to show countryname first, drop countrycode
        cols = ["countryname", "Immigration"]
        top_countries = top_countries[[c for c in cols if c in top_countries.columns]]
        # Rename for better display
        top_countries = top_countries.rename(columns={"countryname": "Country", "Immigration": "Immigration"})
    else:
        # If no countryname, rename countrycode to Country for display
        top_countries = top_countries.rename(columns={"countrycode": "Country"})
    
    return top_countries


def get_top_emigration_countries(df: pd.DataFrame, top_n: int = 10, year: Optional[int] = None) -> pd.DataFrame:
    """
    Get top N countries by emigration.
    
    Args:
        df: Migration dataframe
        top_n: Number of top countries to return
        year: Specific year to filter (None = use latest year)
        
    Returns:
        DataFrame with top countries by emigration (includes countryname if available)
    """
    if df.empty or "Emigration" not in df.columns or "countrycode" not in df.columns:
        return pd.DataFrame()
    
    df_filtered = df.copy()
    
    # Remove Sweden from the list (SE is the source, not a destination)
    if "countrycode" in df_filtered.columns:
        df_filtered = df_filtered[df_filtered["countrycode"].str.upper() != "SE"]
    
    # Filter by year if specified
    if year and "year" in df_filtered.columns:
        # Convert to string for comparison to handle type mismatch
        df_filtered = df_filtered[df_filtered["year"].astype(str) == str(year)]
    elif "year" in df_filtered.columns:
        # Use latest year if not specified
        latest_year = df_filtered["year"].max()
        df_filtered = df_filtered[df_filtered["year"].astype(str) == str(latest_year)]
    
    # Aggregate by country (sum across genders if gender column exists)
    if "gender" in df_filtered.columns:
        top_countries = (
            df_filtered
            .groupby("countrycode", as_index=False)["Emigration"]
            .sum()
            .nlargest(top_n, "Emigration")
            .sort_values("Emigration", ascending=False)
        )
    else:
        top_countries = (
            df_filtered
            .nlargest(top_n, "Emigration")[["countrycode", "Emigration"]]
            .sort_values("Emigration", ascending=False)
        )
    
    # Add country names if available in original dataframe
    if "countryname" in df_filtered.columns:
        country_name_map = df_filtered[["countrycode", "countryname"]].drop_duplicates().set_index("countrycode")["countryname"]
        top_countries["countryname"] = top_countries["countrycode"].map(country_name_map)
        # Reorder columns to show countryname first, drop countrycode
        cols = ["countryname", "Emigration"]
        top_countries = top_countries[[c for c in cols if c in top_countries.columns]]
        # Rename for better display
        top_countries = top_countries.rename(columns={"countryname": "Country", "Emigration": "Emigration"})
    else:
        # If no countryname, rename countrycode to Country for display
        top_countries = top_countries.rename(columns={"countrycode": "Country"})
    
    return top_countries


def prepare_migration_flows(df: pd.DataFrame, year: Optional[int] = None, min_flow: int = 100) -> pd.DataFrame:
    """
    Prepare migration flow data for map visualization.
    Creates lines from/to Sweden with migration volumes.
    
    Args:
        df: Migration dataframe
        year: Specific year to filter (None = aggregate all years)
        min_flow: Minimum migration flow to include (filter small flows)
        
    Returns:
        DataFrame with flow data: countrycode, flow_type, volume, lat, lon
    """
    if df.empty:
        return pd.DataFrame()
    
    df_filtered = df.copy()
    
    # Filter by year if specified
    if year and "year" in df_filtered.columns:
        # Convert year to string for comparison if needed (handles type mismatch)
        df_filtered = df_filtered[df_filtered["year"].astype(str) == str(year)]
        if df_filtered.empty:
            return pd.DataFrame()
    
    # Check if required columns exist
    if "countrycode" not in df_filtered.columns:
        # Try to find the country column
        country_col = None
        for col in df_filtered.columns:
            if 'country' in col.lower() or 'land' in col.lower():
                country_col = col
                break
        
        if country_col:
            df_filtered = df_filtered.rename(columns={country_col: 'countrycode'})
        else:
            raise ValueError(f"Country column not found. Available columns: {list(df_filtered.columns)}")
    
    # Aggregate by country (sum across genders and years if needed)
    agg_dict = {}
    if "Immigration" in df_filtered.columns:
        agg_dict["Immigration"] = "sum"
    if "Emigration" in df_filtered.columns:
        agg_dict["Emigration"] = "sum"
    
    if not agg_dict:
        raise ValueError(f"Migration columns not found. Available columns: {list(df_filtered.columns)}")
    
    flows = df_filtered.groupby("countrycode", as_index=False).agg(agg_dict)
    
    if flows.empty:
        return pd.DataFrame()
    
    # Filter out small flows (use OR condition to keep countries with either immigration or emigration above threshold)
    # Fill NaN values with 0 for comparison
    flows = flows.fillna(0)
    
    # Build filter condition - keep rows where either immigration or emigration is above threshold
    filter_conditions = []
    if "Immigration" in flows.columns:
        filter_conditions.append(flows["Immigration"] >= min_flow)
    if "Emigration" in flows.columns:
        filter_conditions.append(flows["Emigration"] >= min_flow)
    
    if filter_conditions:
        # Combine conditions with OR
        combined_condition = filter_conditions[0]
        for condition in filter_conditions[1:]:
            combined_condition = combined_condition | condition
        flows = flows[combined_condition]
    else:
        # No migration columns, return empty
        return pd.DataFrame()
    
    if flows.empty:
        return pd.DataFrame()
    
    # Map country codes to names
    flows = map_country_codes_to_names(flows)
    
    # Get country coordinates
    flows = add_country_coordinates(flows)
    
    # Remove rows where coordinates are missing (lat/lon are None or NaN)
    if 'lat' in flows.columns and 'lon' in flows.columns:
        flows = flows.dropna(subset=['lat', 'lon'])
    
    return flows


def add_country_coordinates(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add latitude and longitude coordinates for countries.
    Uses a simple mapping of common country codes.
    
    Args:
        df: DataFrame with 'countrycode' column
        
    Returns:
        DataFrame with added 'lat' and 'lon' columns
    """
    # Common country coordinates (ISO 3166-1 alpha-2 codes)
    # This is a simplified mapping - for production, use pycountry or a geocoding service
    country_coords = {
        'SE': (60.1282, 18.6435),  # Sweden
        'NO': (60.4720, 8.4689),   # Norway
        'DK': (56.2639, 9.5018),   # Denmark
        'FI': (61.9241, 25.7482),  # Finland
        'DE': (51.1657, 10.4515),  # Germany
        'PL': (51.9194, 19.1451),  # Poland
        'GB': (55.3781, -3.4360),  # United Kingdom
        'US': (37.0902, -95.7129), # United States
        'FR': (46.2276, 2.2137),   # France
        'ES': (40.4637, -3.7492),  # Spain
        'IT': (41.8719, 12.5674),  # Italy
        'NL': (52.1326, 5.2913),   # Netherlands
        'BE': (50.5039, 4.4699),   # Belgium
        'CH': (46.8182, 8.2275),   # Switzerland
        'AT': (47.5162, 14.5501),  # Austria
        'IE': (53.4129, -8.2439),  # Ireland
        'IS': (64.9631, -19.0208), # Iceland
        'GR': (39.0742, 21.8243),  # Greece
        'PT': (39.3999, -8.2245),  # Portugal
        'CZ': (49.8175, 15.4730),  # Czech Republic
        'HU': (47.1625, 19.5033),  # Hungary
        'RO': (45.9432, 24.9668),  # Romania
        'BG': (42.7339, 25.4858),  # Bulgaria
        'HR': (45.1000, 15.2000),  # Croatia
        'SK': (48.6690, 19.6990),  # Slovakia
        'SI': (46.1512, 14.9955),  # Slovenia
        'EE': (58.5953, 25.0136),  # Estonia
        'LV': (56.8796, 24.6032),  # Latvia
        'LT': (55.1694, 23.8813),  # Lithuania
        'RU': (61.5240, 105.3188), # Russia
        'UA': (48.3794, 31.1656),  # Ukraine
        'BY': (53.7098, 27.9534),  # Belarus
        'TR': (38.9637, 35.2433),  # Turkey
        'IN': (20.5937, 78.9629),  # India
        'CN': (35.8617, 104.1954), # China
        'JP': (36.2048, 138.2529), # Japan
        'KR': (35.9078, 127.7669), # South Korea
        'TH': (15.8700, 100.9925), # Thailand
        'PH': (12.8797, 121.7740), # Philippines
        'VN': (14.0583, 108.2772), # Vietnam
        'ID': (-0.7893, 113.9213), # Indonesia
        'MY': (4.2105, 101.9758),  # Malaysia
        'SG': (1.3521, 103.8198),  # Singapore
        'AU': (-25.2744, 133.7751), # Australia
        'NZ': (-40.9006, 174.8860), # New Zealand
        'CA': (56.1304, -106.3468), # Canada
        'MX': (23.6345, -102.5528), # Mexico
        'BR': (-14.2350, -51.9253), # Brazil
        'AR': (-38.4161, -63.6167), # Argentina
        'CL': (-35.6751, -71.5430), # Chile
        'ZA': (-30.5595, 22.9375),  # South Africa
        'EG': (26.8206, 30.8025),   # Egypt
        'MA': (31.7917, -7.0926),   # Morocco
        'DZ': (28.0339, 1.6596),    # Algeria
        'TN': (33.8869, 9.5375),    # Tunisia
        'IQ': (33.2232, 43.6793),   # Iraq
        'IR': (32.4279, 53.6880),   # Iran
        'AF': (33.9391, 67.7100),   # Afghanistan
        'PK': (30.3753, 69.3451),   # Pakistan
        'BD': (23.6850, 90.3563),   # Bangladesh
        'LK': (7.8731, 80.7718),    # Sri Lanka
        'ET': (9.1450, 38.7667),    # Ethiopia
        'KE': (-0.0236, 37.9062),   # Kenya
        'NG': (9.0820, 8.6753),     # Nigeria
        'GH': (7.9465, -1.0232),    # Ghana
        'SN': (14.4974, -14.4524),  # Senegal
        'SO': (5.1521, 46.1996),    # Somalia
        'ER': (15.1794, 39.7823),   # Eritrea
    }
    
    df = df.copy()
    
    # Add coordinates
    df['lat'] = df['countrycode'].map(lambda x: country_coords.get(x, (None, None))[0])
    df['lon'] = df['countrycode'].map(lambda x: country_coords.get(x, (None, None))[1])
    
    # Filter out countries without coordinates
    df = df[df['lat'].notna() & df['lon'].notna()]
    
    return df
