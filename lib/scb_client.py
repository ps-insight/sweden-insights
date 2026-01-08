from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Optional, List, Dict, Any
import pandas as pd
import requests
import json
from pyscbwrapper import SCB


def months_range(start: str, end: str) -> List[str]:
    """
    start/end format: 'YYYY-MM' (e.g. '2020-01')
    returns: ['2020M01', '2020M02', ...]
    """
    idx = pd.period_range(start=start, end=end, freq="M")
    return [f"{p.year}M{p.month:02d}" for p in idx]


def pxweb_payload_to_df(payload: Dict[str, Any]) -> pd.DataFrame:
    """
    Convert PxWeb-style payload to DataFrame.
    payload:
      {
        'columns': [{'text':..., 'type': 'd'|'t'|'c', ...}, ...],
        'data': [{'key':[...], 'values':[...]}]
      }
    """
    dim_cols = [c["text"] for c in payload["columns"] if c["type"] in ("d", "t")]
    val_cols = [c["text"] for c in payload["columns"] if c["type"] == "c"]

    rows = []
    for item in payload.get("data", []):
        key = item["key"]
        vals = item["values"]
        row = dict(zip(dim_cols, key))
        row.update(dict(zip(val_cols, vals)))
        rows.append(row)

    df = pd.DataFrame(rows)

    # tidy types
    if "month" in df.columns:
        df["month"] = pd.to_datetime(df["month"].str.replace("M", "-"), format="%Y-%m", errors="coerce")
    for c in val_cols:
        df[c] = pd.to_numeric(df[c], errors="coerce")

    return df


@dataclass
class SCBClientCOL:
    """
    Cost of Living (CPI) client using pyscbwrapper.
    """
    language: str = "en"
    table_id: str = "KPI2020COICOPM"  # all COICOP levels (lots of product groups)

    def _scb(self) -> SCB:
        """Create and initialize SCB client instance."""
        scb = SCB(self.language)
        scb.go_down("PR", "PR0101", "PR0101A", self.table_id)
        # Ensure the SCB object is properly initialized
        # Calling info() might help initialize the connection
        try:
            scb.info()
        except Exception:
            # If info() fails, continue anyway - get_variables might still work
            pass
        return scb

    def get_variables(self) -> Dict[str, List[str]]:
        """
        Wrapper-provided variables (labels).
        Useful for UI options.
        """
        try:
            scb = self._scb()
            return scb.get_variables()
        except (KeyError, Exception) as e:
            # If get_variables fails, return empty dict with default structure
            # This can happen if the API response structure is unexpected
            return {
                "Product group": [],
                "observations": ["Index", "Annual changes", "Monthly changes", "Weights"],
                "month": []
            }

    def get_product_group_code_mapping(self) -> Dict[str, str]:
        """
        Get mapping from product group codes to labels.
        Queries minimal data to establish the code-to-label relationship.
        
        Returns:
            Dictionary mapping product group codes to labels
        """
        try:
            scb = self._scb()
            variables = self.get_variables()  # Use our wrapped method with error handling
            all_product_groups = variables.get("Product group", [])
            
            if not all_product_groups:
                return {}
            
            # Query minimal data to get code-to-label mapping
            all_months = variables.get("month", [])
            if not all_months:
                return {}
            
            # Use most recent month for minimal data transfer
            sample_month = all_months[-1]
            
            scb.set_query(
                product_groups=list(all_product_groups),
                observations=["Index"],
                month=[sample_month],
            )
            
            payload = scb.get_data()
            product_codes = sorted({item["key"][0] for item in payload.get("data", [])})
            
            # Create mapping (same approach as fetch_cpi_dataframe)
            code_to_label = dict(zip(product_codes, all_product_groups))
            
            return code_to_label
        except Exception:
            # Return empty dict if anything fails
            return {}

    def fetch_cpi_dataframe(
        self,
        *,
        product_group_labels: Iterable[str],
        observations: Iterable[str] = ("Index", "Annual changes", "Monthly changes", "Weights"),
        months: Optional[Iterable[str]] = None,
        start: Optional[str] = '2020-01',   # 'YYYY-MM'
        end: Optional[str] = '2025-12',     # 'YYYY-MM'
        last_n_months: Optional[int] = None,
        add_labels: bool = True,
    ) -> pd.DataFrame:
        """
        Fetch CPI data and return a tidy dataframe.

        Choose ONE of:
          - months=[...]
          - start='YYYY-MM', end='YYYY-MM'
          - last_n_months=60  (uses latest N months from wrapper metadata)
        """
        scb = self._scb()
        variables = self.get_variables()  # Use our wrapped method with error handling

        # derive months if needed
        if months is None:
            if start and end:
                months = months_range(start, end)
            elif last_n_months:
                all_months = variables.get("month", [])
                if not all_months:
                    raise ValueError("Could not find 'month' variable from get_variables().")
                months = all_months[-int(last_n_months):]
            else:
                raise ValueError("Provide months=..., or start/end, or last_n_months=...")

        # Query using wrapper-friendly parameter names
        scb.set_query(
            product_groups=list(product_group_labels),
            observations=list(observations),
            month=list(months),
        )

        payload = scb.get_data()
        df = pxweb_payload_to_df(payload)

        # Map product group code -> label using your notebook approach
        if add_labels and "Product group" in df.columns:
            product_groups = variables.get("Product group", [])
            product_codes = sorted({item["key"][0] for item in payload.get("data", [])})

            # notebook mapping
            code_to_label = dict(zip(product_codes, product_groups))

            df["Product group_label"] = df["Product group"].map(code_to_label).fillna(df["Product group"])

        return df


def pxweb_payload_to_migration_df(payload: Dict[str, Any]) -> pd.DataFrame:
    """
    Convert PxWeb-style payload to DataFrame for migration data.
    Includes column renaming to English.
    
    Args:
        payload: PxWeb API response with columns and data
        
    Returns:
        DataFrame with renamed columns (countrycode, gender, year, Immigration, Emigration)
    """
    columns = payload.get('columns', [])
    
    # Store column metadata for later reference
    col_metadata = {c.get("code", ""): c.get("text", "") for c in columns}
    
    # Use "text" field for column names, fallback to "code" if text not available
    dim_cols = []
    dim_col_codes = []  # Store codes for reference
    for c in columns:
        if c.get("type") in ("d", "t"):
            col_name = c.get("text") or c.get("code", "")
            if col_name:
                dim_cols.append(col_name)
                dim_col_codes.append(c.get("code", ""))
    
    val_cols = [c.get("text") or c.get("code", "") for c in columns if c.get("type") == "c"]
    val_cols = [c for c in val_cols if c]
    
    # Extract data
    rows = []
    for item in payload.get("data", []):
        key = item.get("key", [])
        vals = item.get("values", [])
        row = dict(zip(dim_cols, key))
        row.update(dict(zip(val_cols, vals)))
        rows.append(row)
    
    # Create dataframe
    df = pd.DataFrame(rows)
    
    # If countrycode column is missing, check if Fodelseland code exists in metadata
    if 'countrycode' not in df.columns and 'födelseland' not in df.columns and 'Fodelseland' not in df.columns:
        # Find Fodelseland column by code
        for idx, col_code in enumerate(dim_col_codes):
            if col_code == 'Fodelseland':
                # Country is at this index in the key
                if dim_cols[idx] in df.columns:
                    # Column exists but wasn't renamed - rename it now
                    df = df.rename(columns={dim_cols[idx]: 'countrycode'})
                else:
                    # Extract from key if column name doesn't match
                    country_key_idx = idx
                    df['countrycode'] = [item['key'][country_key_idx] for item in payload.get("data", [])]
                break
    
    # Clean up data types
    for col in val_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    
    # Rename columns to English (handle both Swedish and English column names)
    rename_map = {}
    
    # Check which columns exist and create rename mapping
    if 'födelseland' in df.columns:
        rename_map['födelseland'] = 'countrycode'
    elif 'Fodelseland' in df.columns:
        rename_map['Fodelseland'] = 'countrycode'
    elif 'countrycode' not in df.columns:
        # Try to find any column that might be country code
        for col in df.columns:
            if 'land' in col.lower() or 'country' in col.lower():
                rename_map[col] = 'countrycode'
                break
    
    if 'kön' in df.columns:
        rename_map['kön'] = 'gender'
    elif 'Kon' in df.columns:
        rename_map['Kon'] = 'gender'
    elif 'gender' not in df.columns:
        for col in df.columns:
            if 'kön' in col.lower() or 'kon' in col.lower() or 'sex' in col.lower():
                rename_map[col] = 'gender'
                break
    
    if 'år' in df.columns:
        rename_map['år'] = 'year'
    elif 'Tid' in df.columns:
        rename_map['Tid'] = 'year'
    elif 'year' not in df.columns:
        for col in df.columns:
            if 'år' in col.lower() or 'tid' in col.lower() or 'year' in col.lower():
                rename_map[col] = 'year'
                break
    
    if 'Invandringar' in df.columns:
        rename_map['Invandringar'] = 'Immigration'
    elif 'BE0101M3' in df.columns:
        rename_map['BE0101M3'] = 'Immigration'
    
    if 'Utvandringar' in df.columns:
        rename_map['Utvandringar'] = 'Emigration'
    elif 'BE0101M4' in df.columns:
        rename_map['BE0101M4'] = 'Emigration'
    
    if rename_map:
        df = df.rename(columns=rename_map)
    
    # Map gender values: 1 = Male, 2 = Female
    if 'gender' in df.columns:
        df['gender'] = df['gender'].map({'1': 'Male', '2': 'Female', 1: 'Male', 2: 'Female'}).fillna(df['gender'])
    
    # Debug: Check final columns
    # print(f"DataFrame columns after renaming: {list(df.columns)}")
    # print(f"Sample data: {df.head()}")
    
    return df


@dataclass
class SCBClientMigration:
    """
    Migration data client for SCB API.
    Handles immigration and emigration data.
    """
    language: str = "sv"  # Swedish for migration data
    table_id: str = "ImmiEmiFod"
    api_url: str = "https://api.scb.se/OV0104/v1/doris/sv/ssd/START/BE/BE0101/BE0101J/ImmiEmiFod"
    
    def _get_available_countries(self) -> List[str]:
        """
        Get all available country codes from the API metadata.
        
        Returns:
            List of country codes
        """
        try:
            # Query metadata endpoint
            metadata_url = self.api_url.replace("/doris/", "/doris/en/")
            response = requests.get(metadata_url, timeout=30)
            response.raise_for_status()
            metadata = response.json()
            
            # Find Fodelseland variable and extract values
            for var in metadata.get("variables", []):
                if var.get("code") == "Fodelseland":
                    # Extract country codes from values
                    countries = [val.get("value") for val in var.get("values", [])]
                    return countries
        except Exception:
            pass
        
        # Fallback: return common country codes if metadata fetch fails
        return [
            'AF', 'AL', 'DZ', 'AD', 'AO', 'AI', 'AG', 'AR', 'AM', 'AU', 'AZ', 'BS', 'BH', 'BD', 'BB',
            'BY', 'BE', 'BZ', 'BJ', 'BM', 'BT', 'BO', 'BA', 'BW', 'BR', 'BN', 'BG', 'BF', 'BI', 'KH',
            'CM', 'CA', 'CV', 'KY', 'CF', 'TD', 'CL', 'CN', 'CO', 'KM', 'CG', 'CD', 'CR', 'CI', 'HR',
            'CU', 'CY', 'CZ', 'DK', 'DJ', 'DM', 'DO', 'EC', 'EG', 'SV', 'GQ', 'ER', 'EE', 'ET', 'FJ',
            'FI', 'FR', 'GA', 'GM', 'GE', 'DE', 'GH', 'GR', 'GD', 'GT', 'GN', 'GW', 'GY', 'HT', 'HN',
            'HK', 'HU', 'IS', 'IN', 'ID', 'IR', 'IQ', 'IE', 'IL', 'IT', 'JM', 'JP', 'JO', 'KZ', 'KE',
            'KI', 'KP', 'KR', 'KW', 'KG', 'LA', 'LV', 'LB', 'LS', 'LR', 'LY', 'LI', 'LT', 'LU', 'MK',
            'MG', 'MW', 'MY', 'MV', 'ML', 'MT', 'MH', 'MR', 'MU', 'MX', 'FM', 'MD', 'MC', 'MN', 'ME',
            'MA', 'MZ', 'MM', 'NA', 'NR', 'NP', 'NL', 'NZ', 'NI', 'NE', 'NG', 'NO', 'OM', 'PK', 'PW',
            'PA', 'PG', 'PY', 'PE', 'PH', 'PL', 'PT', 'QA', 'RO', 'RU', 'RW', 'KN', 'LC', 'VC', 'WS',
            'SM', 'ST', 'SA', 'SN', 'RS', 'SC', 'SL', 'SG', 'SK', 'SI', 'SB', 'SO', 'ZA', 'ES', 'LK',
            'SD', 'SR', 'SZ', 'SE', 'CH', 'SY', 'TW', 'TJ', 'TZ', 'TH', 'TL', 'TG', 'TO', 'TT', 'TN',
            'TR', 'TM', 'TV', 'UG', 'UA', 'AE', 'GB', 'US', 'UY', 'UZ', 'VU', 'VA', 'VE', 'VN', 'YE',
            'ZM', 'ZW'
        ]
    
    def fetch_migration_dataframe(
        self,
        *,
        countries: Optional[List[str]] = None,
        genders: Optional[List[str]] = None,
        years: Optional[List[int]] = None,
        start_year: Optional[int] = None,
        end_year: Optional[int] = None,
    ) -> pd.DataFrame:
        """
        Fetch migration data from SCB API.
        
        Args:
            countries: List of country codes (e.g., ['SE', 'DE', 'US']). None = all countries
            genders: List of gender codes ('1' = male, '2' = female). None = all genders
            years: List of years. None = use start_year/end_year
            start_year: Start year for data range
            end_year: End year for data range
            
        Returns:
            DataFrame with columns: countrycode, gender, year, Immigration, Emigration
        """
    
        query = {
        "query": [
            {
            "code": "Fodelseland",
            "selection": {
                "filter": "vs:LandISOAlfa2-96J",
                "values": [
                "AF",
                "AL",
                "DZ",
                "AD",
                "AO",
                "AI",
                "AG",
                "AR",
                "AM",
                "AU",
                "AZ",
                "BS",
                "BH",
                "BD",
                "BB",
                "BY",
                "BE",
                "BZ",
                "BJ",
                "BM",
                "BT",
                "BO",
                "BA",
                "BW",
                "BR",
                "VG",
                "BN",
                "BG",
                "BF",
                "BI",
                "CF",
                "CL",
                "CO",
                "CR",
                "CY",
                "DK",
                "CD",
                "DJ",
                "DM",
                "DO",
                "EC",
                "EG",
                "GQ",
                "SV",
                "CI",
                "ER",
                "EE",
                "SZ",
                "ET",
                "FJ",
                "PH",
                "FI",
                "FR",
                "AE",
                "GB",
                "US",
                "GA",
                "GM",
                "GZ",
                "GE",
                "GH",
                "GI",
                "GR",
                "GD",
                "GT",
                "GN",
                "GW",
                "GY",
                "HT",
                "VA",
                "HN",
                "HK",
                "IN",
                "ID",
                "IQ",
                "IR",
                "IE",
                "IS",
                "IL",
                "IT",
                "JM",
                "JP",
                "YE",
                "JO",
                "YU",
                "KH",
                "CM",
                "CA",
                "CV",
                "KZ",
                "KE",
                "CN",
                "KG",
                "KI",
                "KM",
                "CG",
                "XK",
                "HR",
                "CU",
                "KW",
                "LA",
                "LS",
                "LV",
                "LB",
                "LR",
                "LY",
                "LI",
                "LT",
                "LU",
                "MG",
                "MW",
                "MY",
                "MV",
                "ML",
                "MT",
                "MA",
                "MH",
                "MR",
                "MU",
                "MX",
                "FM",
                "MZ",
                "MD",
                "MC",
                "MN",
                "ME",
                "MM",
                "NA",
                "NR",
                "NL",
                "NP",
                "NI",
                "NE",
                "NG",
                "KP",
                "MK",
                "NO",
                "NZ",
                "OM",
                "PK",
                "PW",
                "PS",
                "PA",
                "PG",
                "PY",
                "PE",
                "PL",
                "PT",
                "QA",
                "RO",
                "RW",
                "RU",
                "KN",
                "LC",
                "VC",
                "SB",
                "WS",
                "SM",
                "ST",
                "SA",
                "CH",
                "SN",
                "RS",
                "CS",
                "SC",
                "SL",
                "SG",
                "SK",
                "SI",
                "SO",
                "SU",
                "ES",
                "LK",
                "SD",
                "SR",
                "SE",
                "ZA",
                "KR",
                "SS",
                "SY",
                "TJ",
                "TW",
                "TZ",
                "TD",
                "TH",
                "CZ",
                "QT",
                "TG",
                "TO",
                "TT",
                "TN",
                "TR",
                "TM",
                "TV",
                "DE",
                "UG",
                "UA",
                "HU",
                "UY",
                "UZ",
                "VU",
                "VE",
                "VN",
                "ZM",
                "ZW",
                "AT",
                "TL",
                "ÖOF"
                ]
            }
            },
            {
            "code": "Kon",
            "selection": {
                "filter": "item",
                "values": [
                "1",
                "2"
                ]
            }
            }
        ],
        "response": {
            "format": "json"
        }
        }
        
        # Make API request
        session = requests.Session()
        try:
            response = session.post(self.api_url, json=query, timeout=30)
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            # Provide more helpful error message
            error_detail = ""
            try:
                error_detail = response.text
            except:
                pass
            raise ValueError(f"SCB API error: {e}. Response: {error_detail}")
        
        # Parse response
        response_json = json.loads(response.content.decode('utf-8-sig'))
        
        # Debug: Check response structure
        # print(f"Response columns: {[c.get('code') for c in response_json.get('columns', [])]}")
        # print(f"Response has data: {len(response_json.get('data', []))} items")
        
        # Convert to dataframe
        df = pxweb_payload_to_migration_df(response_json)
        
        # Final check: if countrycode is still missing, extract directly from response
        if 'countrycode' not in df.columns:
            columns_meta = response_json.get('columns', [])
            # Find Fodelseland column index
            for idx, col in enumerate(columns_meta):
                if col.get('code') == 'Fodelseland':
                    # Extract countrycode from key array
                    if response_json.get('data') and len(response_json['data']) > 0:
                        if 'key' in response_json['data'][0] and len(response_json['data'][0]['key']) > idx:
                            df['countrycode'] = [item['key'][idx] for item in response_json.get('data', [])]
                            break
        
        return df