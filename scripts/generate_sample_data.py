from __future__ import annotations

import os
import random
from typing import List, Tuple, Dict
import pandas as pd


OUT_CSV = os.path.join("data", "sample_trade_flows.csv")


def _weighted_choice(items: List[str], weights: List[float]) -> str:
    total = sum(weights)
    r = random.random() * total
    acc = 0.0
    for item, w in zip(items, weights):
        acc += w
        if acc >= r:
            return item
    return items[-1]


def _make_country_universe() -> Dict[str, str]:
    # country -> region (used for mild clustering)
    return {
        # North America
        "USA": "NAM", "CAN": "NAM", "MEX": "NAM",
        # South America
        "BRA": "SAM", "ARG": "SAM", "CHL": "SAM", "COL": "SAM", "PER": "SAM",
        # Europe
        "DEU": "EUR", "FRA": "EUR", "GBR": "EUR", "ITA": "EUR", "ESP": "EUR", "NLD": "EUR",
        "SWE": "EUR", "NOR": "EUR", "POL": "EUR", "CHE": "EUR", "BEL": "EUR", "AUT": "EUR",
        # East / SE Asia
        "CHN": "EAS", "JPN": "EAS", "KOR": "EAS", "TWN": "EAS", "HKG": "EAS",
        "SGP": "SEA", "VNM": "SEA", "THA": "SEA", "MYS": "SEA", "IDN": "SEA", "PHL": "SEA",
        # South Asia
        "IND": "SAS", "PAK": "SAS", "BGD": "SAS", "LKA": "SAS",
        # Middle East
        "SAU": "MENA", "ARE": "MENA", "QAT": "MENA", "ISR": "MENA", "TUR": "MENA",
        # Africa
        "ZAF": "AFR", "NGA": "AFR", "EGY": "AFR", "KEN": "AFR", "MAR": "AFR",
        # Oceania
        "AUS": "OCE", "NZL": "OCE",
        # Eurasia
        "RUS": "EUE",
    }


def _hub_weights(countries: List[str]) -> List[float]:
    # Make a few hubs naturally more likely to appear as exporters/importers.
    hub = {"USA", "CHN", "DEU", "IND", "JPN", "KOR", "SGP", "NLD", "GBR", "FRA"}
    weights = []
    for c in countries:
        if c in hub:
            weights.append(6.0)
        else:
            weights.append(1.5)
    return weights


def _heavy_tail_value() -> float:
    # Lognormal gives a heavy tail (few huge flows, many medium flows).
    # We output values in USD-like magnitudes, but they’re just inputs to the model.
    v = random.lognormvariate(mu=23.0, sigma=1.0)  # ~1e10 to 1e12 range typical
    return float(max(5e7, min(v, 2.5e12)))


def generate_trade_flows(
    *,
    year: int = 2022,
    n_edges: int = 500,
    seed: int = 7,
    same_region_bias: float = 0.55,
) -> pd.DataFrame:
    random.seed(seed)

    universe = _make_country_universe()
    countries = sorted(universe.keys())
    regions = universe

    weights = _hub_weights(countries)

    edges: Dict[Tuple[str, str], float] = {}

    # Pre-build region to members
    region_members: Dict[str, List[str]] = {}
    for c, r in regions.items():
        region_members.setdefault(r, []).append(c)

    while len(edges) < n_edges:
        exporter = _weighted_choice(countries, weights)

        # Choose importer with mild regional clustering
        exp_region = regions[exporter]
        if random.random() < same_region_bias:
            candidates = [x for x in region_members[exp_region] if x != exporter]
            if not candidates:
                candidates = [x for x in countries if x != exporter]
        else:
            # cross-region
            candidates = [x for x in countries if x != exporter and regions[x] != exp_region]
            if not candidates:
                candidates = [x for x in countries if x != exporter]

        importer = random.choice(candidates)

        # Avoid perfect symmetry dominance; allow both directions but not forced
        key = (exporter, importer)
        if key in edges:
            continue

        val = _heavy_tail_value()

        # Some exporter/importer pairs are naturally "bigger" if a hub is involved
        if exporter in {"USA", "CHN"} or importer in {"USA", "CHN"}:
            val *= random.uniform(1.2, 2.2)
        if exporter in {"SGP", "NLD"} or importer in {"SGP", "NLD"}:
            val *= random.uniform(1.1, 1.8)

        # Clamp again after multipliers
        val = float(max(5e7, min(val, 2.5e12)))
        edges[key] = val

    df = pd.DataFrame(
        [{"exporter": u, "importer": v, "trade_value": tv, "year": int(year)} for (u, v), tv in edges.items()]
    )

    # Clean + aggregate (should already be unique)
    df["exporter"] = df["exporter"].astype(str).str.upper().str.strip()
    df["importer"] = df["importer"].astype(str).str.upper().str.strip()
    df["trade_value"] = pd.to_numeric(df["trade_value"], errors="coerce").fillna(0.0)
    df = df[(df["exporter"] != df["importer"]) & (df["trade_value"] > 0)].copy()
    df = df.groupby(["exporter", "importer", "year"], as_index=False)["trade_value"].sum()

    return df


def main() -> None:
    os.makedirs(os.path.dirname(OUT_CSV), exist_ok=True)

    df = generate_trade_flows(year=2022, n_edges=500, seed=7, same_region_bias=0.55)
    df.to_csv(OUT_CSV, index=False)

    print("Wrote:", OUT_CSV)
    print("Rows:", len(df))
    print(df.head(12).to_string(index=False))


if __name__ == "__main__":
    main()
