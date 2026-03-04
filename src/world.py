from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Iterable

import networkx as nx
import pandas as pd


def build_toy_world() -> nx.DiGraph:
   
    G = nx.DiGraph()

    # Nodes: local production, demand, inventory
    G.add_node("CHN", local_production=180, demand=90,  inventory=25)
    G.add_node("SGP", local_production=20,  demand=45,  inventory=10)   # hub is tight
    G.add_node("USA", local_production=120, demand=165, inventory=20)   # import-dependent
    G.add_node("EU",  local_production=130, demand=185, inventory=20)   # import-dependent
    G.add_node("IND", local_production=90,  demand=150, inventory=15)   # import-dependent

    # Base demand for volatility logic
    for n in G.nodes:
        G.nodes[n]["base_demand"] = float(G.nodes[n]["demand"])
        G.nodes[n]["base_local_production"] = float(G.nodes[n]["local_production"])

    # Edges: capacities
    G.add_edge("CHN", "SGP", capacity=200)
    G.add_edge("SGP", "USA", capacity=120)
    G.add_edge("SGP", "EU",  capacity=120)
    G.add_edge("USA", "EU", capacity=80)
    G.add_edge("EU", "IND", capacity=70)
    G.add_edge("CHN", "IND", capacity=25)

    return G


def build_world_from_trade_df(
    trade_df: pd.DataFrame,
    *,
    exporter_col: str = "exporter",
    importer_col: str = "importer",
    value_col: str = "trade_value",
    countries: Optional[Iterable[str]] = None,
    edge_capacity_scale: float = 1.0,
    demand_scale: float = 1.0,
    production_scale: float = 1.0,
    inventory_days: float = 10.0,
    min_capacity: float = 1.0,
) -> nx.DiGraph:
  
    df = trade_df.copy()

    for c in (exporter_col, importer_col):
        df[c] = df[c].astype(str).str.upper().str.strip()
    df[value_col] = pd.to_numeric(df[value_col], errors="coerce").fillna(0.0)

    if countries is not None:
        keep = set(str(x).upper().strip() for x in countries)
        df = df[df[exporter_col].isin(keep) & df[importer_col].isin(keep)].copy()

    # Aggregate in case data has multiple rows per pair
    df = (
        df.groupby([exporter_col, importer_col], as_index=False)[value_col]
        .sum()
    )

    # Node totals
    exports = df.groupby(exporter_col)[value_col].sum().to_dict()
    imports = df.groupby(importer_col)[value_col].sum().to_dict()

    all_nodes = sorted(set(exports.keys()) | set(imports.keys()))
    G = nx.DiGraph()

    # Add nodes
    for n in all_nodes:
        exp = float(exports.get(n, 0.0))
        imp = float(imports.get(n, 0.0))

        demand = demand_scale * imp
        local_prod = production_scale * exp

        # crude inventory proxy: X days of demand (annualized)
        inv = (demand * float(inventory_days) / 365.0) if demand > 0 else 0.0

        G.add_node(
            n,
            local_production=local_prod,
            demand=demand,
            inventory=inv,
            base_demand=float(demand),
            base_local_production=float(local_prod),
        )

    # Add edges (capacity)
    for row in df.itertuples(index=False):
        u = getattr(row, exporter_col)
        v = getattr(row, importer_col)
        val = float(getattr(row, value_col))

        cap = max(min_capacity, edge_capacity_scale * val)
        if u != v and cap > 0:
            G.add_edge(u, v, capacity=cap)

    return G

