from __future__ import annotations

from typing import Dict, List
import time
import requests
import pandas as pd

# Classic Comtrade API
BASE_URL = "https://comtrade.un.org/data/api/get"

ISO3_TO_M49: Dict[str, int] = {
    "USA": 842,
    "CHN": 156,
    "IND": 356,
    "DEU": 276,
    "SGP": 702,
    "GBR": 826,
    "FRA": 250,
    "ITA": 380,
    "JPN": 392,
    "KOR": 410,
    "CAN": 124,
    "MEX": 484,
    "BRA": 76,
    "AUS": 36,
    "RUS": 643,
    "TUR": 792,
    "ZAF": 710,
    "NLD": 528,
    "ESP": 724,
}


def _flow_to_rg(flow_code: str) -> str:
    flow_code = flow_code.upper().strip()
    if flow_code == "X":
        return "2"  # exports
    if flow_code == "M":
        return "1"  # imports
    raise ValueError("flow_code must be 'X' or 'M'")


def fetch_trade_flows(
    *,
    year: int,
    reporters_iso3: List[str],
    cmd_code: str,
    flow_code: str = "X",
    max_records: int = 500,
    partner: str = "all",
    timeout: int = 60,
    sleep_s: float = 0.35,
) -> pd.DataFrame:
    """
    Fetch trade flows from UN Comtrade Classic API and normalize to:
      exporter, importer, trade_value, year

    Robustness:
      - Forces JSON via fmt=json
      - If JSON parse fails, prints status + a snippet of response text
    """

    rg = _flow_to_rg(flow_code)
    rows = []

    for rep_iso in reporters_iso3:
        rep_iso = rep_iso.upper().strip()
        rep_code = ISO3_TO_M49.get(rep_iso)
        if rep_code is None:
            print(f"Skipping unknown reporter ISO3: {rep_iso}")
            continue

        params = {
            "max": int(max_records),
            "type": "C",
            "freq": "A",
            "px": "HS",
            "ps": str(year),
            "r": str(rep_code),
            "p": str(partner),
            "rg": str(rg),
            "cc": str(cmd_code),
            "fmt": "json",          # IMPORTANT: force JSON output
            "head": "M",            # keep metadata minimal
        }

        print(f"Requesting reporter={rep_iso} year={year} cc={cmd_code} flow={flow_code} partner={partner} ...")
        r = requests.get(BASE_URL, params=params, timeout=timeout)

        # Handle non-200
        if r.status_code != 200:
            print(f"  HTTP {r.status_code}. First 300 chars:\n{r.text[:300]}\n")
            continue

        # Parse JSON robustly
        try:
            js = r.json()
        except Exception:
            print("  Response was not JSON. First 300 chars:")
            print(r.text[:300])
            print("\nFull URL used:")
            print(r.url)
            continue

        dataset = js.get("dataset") or []
        print(f"  returned rows: {len(dataset)}")

        for it in dataset:
            reporter_iso = it.get("rt3ISO")
            partner_iso = it.get("pt3ISO")
            tv = it.get("TradeValue")

            if not reporter_iso or not partner_iso or tv is None:
                continue

            try:
                tv_f = float(tv)
            except Exception:
                continue

            if tv_f <= 0:
                continue

            reporter_iso = str(reporter_iso).upper()
            partner_iso = str(partner_iso).upper()

            # Direction: exports are reporter -> partner; imports reverse
            if flow_code.upper() == "X":
                exp, imp = reporter_iso, partner_iso
            else:
                exp, imp = partner_iso, reporter_iso

            if exp == imp:
                continue

            rows.append({"exporter": exp, "importer": imp, "trade_value": tv_f, "year": int(year)})

        # small pause to be nice to the API
        time.sleep(float(sleep_s))

    if not rows:
        return pd.DataFrame(columns=["exporter", "importer", "trade_value", "year"])

    df = pd.DataFrame(rows)
    df = df.groupby(["exporter", "importer", "year"], as_index=False)["trade_value"].sum()
    return df
