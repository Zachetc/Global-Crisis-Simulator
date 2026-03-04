from __future__ import annotations

from typing import Optional
import pandas as pd
import requests


WITS_BASE = "https://wits.worldbank.org/API/V1"


def fetch_trade_flows_placeholder(
    *,
    year: int,
    reporter: str,
    partner: str,
    indicator: str = "XPRT-USD",  # placeholder
    timeout: int = 45,
) -> pd.DataFrame:
   
    reporter = reporter.upper().strip()
    partner = partner.upper().strip()

    # TODO: replace with actual WITS endpoint + params
    url = f"{WITS_BASE}/placeholder"
    params = {"year": year, "reporter": reporter, "partner": partner, "indicator": indicator}

    r = requests.get(url, params=params, timeout=timeout)
    r.raise_for_status()

    js = r.json()
    # TODO: parse js properly
    val = float(js.get("trade_value", 0.0))

    return pd.DataFrame(
        [{"exporter": reporter, "importer": partner, "trade_value": val, "year": int(year)}]
    )
