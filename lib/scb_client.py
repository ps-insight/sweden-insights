from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Optional, List, Dict, Any
import pandas as pd
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
        scb = SCB(self.language)
        scb.go_down("PR", "PR0101", "PR0101A", self.table_id)
        return scb

    def get_variables(self) -> Dict[str, List[str]]:
        """
        Wrapper-provided variables (labels).
        Useful for UI options.
        """
        scb = self._scb()
        return scb.get_variables()

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
        variables = scb.get_variables()

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