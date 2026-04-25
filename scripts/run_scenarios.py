from __future__ import annotations

import os
import random
from dataclasses import dataclass
from typing import List, Tuple, Optional

import pandas as pd

from src.world import build_world_from_trade_df
from src.shocks import get_edge_capacity, set_edge_capacity, shock_multiplier
from src.simulate import step


OUTDIR = "outputs"
CSV_PATH = os.path.join("data", "sample_trade_flows.csv")


@dataclass
class Scenario:
    name: str
    # If provided, reduce capacity on any edge touching these nodes
    nodes: Optional[List[str]] = None
    # Specific directed edges to shock (u, v)
    edges: Optional[List[Tuple[str, str]]] = None
    # Shock parameters
    severity: float = 0.6
    duration: int = 10
    recovery: int = 15


def _load_trade_df() -> pd.DataFrame:
    df = pd.read_csv(CSV_PATH)
    df["exporter"] = df["exporter"].astype(str).str.upper().str.strip()
    df["importer"] = df["importer"].astype(str).str.upper().str.strip()
    df["trade_value"] = pd.to_numeric(df["trade_value"], errors="coerce").fillna(0.0)
    df["year"] = pd.to_numeric(df.get("year", 2022), errors="coerce").fillna(2022).astype(int)
    df = df[(df["exporter"] != df["importer"]) & (df["trade_value"] > 0)].copy()
    return df


def _auto_scale_capacity(df: pd.DataFrame, target_median_capacity: float = 100.0, min_capacity: float = 0.1) -> float:
    vals = pd.to_numeric(df["trade_value"], errors="coerce").fillna(0.0)
    med = float(vals.median()) if len(vals) else 1.0
    if med <= 0:
        return 1.0
    return target_median_capacity / med


def _pick_shock_edges(G, scenario: Scenario) -> List[Tuple[str, str]]:
    if scenario.edges:
        return [(u, v) for (u, v) in scenario.edges if G.has_edge(u, v)]

    if scenario.nodes:
        nodes = set(scenario.nodes)
        e = []
        for (u, v) in G.edges():
            if u in nodes or v in nodes:
                e.append((u, v))
        return e

    # Fallback: pick a few random edges
    edges = list(G.edges())
    random.shuffle(edges)
    return edges[:5]


def _run_single_scenario(
    *,
    scenario: Scenario,
    days: int,
    export_buffer: float,
    inventory_days: float,
    export_policy_alpha: float,
) -> dict:
    df = _load_trade_df()
    scale = _auto_scale_capacity(df)

    countries = sorted(set(df["exporter"]).union(set(df["importer"])))

    G = build_world_from_trade_df(
        df,
        countries=countries,
        edge_capacity_scale=scale,
        demand_scale=scale,
        production_scale=scale,
        inventory_days=inventory_days,
        min_capacity=0.1,
    )

    # Attach export policy parameters (simulate.py reads these)
    for n in G.nodes():
        G.nodes[n]["export_buffer"] = float(export_buffer)
        G.nodes[n]["export_policy_alpha"] = float(export_policy_alpha)

    shock_edges = _pick_shock_edges(G, scenario)
    if not shock_edges:
        return {
            "scenario": scenario.name,
            "severity": scenario.severity,
            "duration": scenario.duration,
            "recovery": scenario.recovery,
            "edges_shocked": 0,
            "avg_shortage": None,
            "max_shortage": None,
            "shortage_auc": None,
        }

    base_caps = {(u, v): get_edge_capacity(G, u, v) for (u, v) in shock_edges}

    shortage_series: List[float] = []
    for t in range(int(days)):
        mult = shock_multiplier(t, scenario.duration, scenario.recovery, scenario.severity)
        for (u, v) in shock_edges:
            set_edge_capacity(G, u, v, base_caps[(u, v)] * mult)

        out = step(G)
        shortage_series.append(float(out["shortage_pct"]))

    avg_shortage = sum(shortage_series) / len(shortage_series) if shortage_series else 0.0
    max_shortage = max(shortage_series) if shortage_series else 0.0
    auc = sum(shortage_series)

    return {
        "scenario": scenario.name,
        "severity": scenario.severity,
        "duration": scenario.duration,
        "recovery": scenario.recovery,
        "edges_shocked": len(shock_edges),
        "avg_shortage": avg_shortage,
        "max_shortage": max_shortage,
        "shortage_auc": auc,
    }


def main() -> None:
    os.makedirs(OUTDIR, exist_ok=True)

    # Scenarios are intentionally generic labels; the model is a framework, not a forecast.
    scenarios = [
        Scenario(name="China export disruption", nodes=["CHN"], severity=0.65, duration=12, recovery=18),
        Scenario(name="US export controls", nodes=["USA"], severity=0.55, duration=10, recovery=14),
        Scenario(name="Singapore hub disruption", nodes=["SGP"], severity=0.70, duration=8, recovery=16),
        Scenario(name="EU logistics disruption", nodes=["DEU", "FRA", "NLD", "ITA", "ESP", "GBR"], severity=0.50, duration=10, recovery=15),
        Scenario(name="Broad commodity shock (multi-edge)", edges=None, nodes=None, severity=0.45, duration=14, recovery=20),
    ]

    rows = []
    for sc in scenarios:
        r = _run_single_scenario(
            scenario=sc,
            days=40,
            export_buffer=0.05,
            inventory_days=7.0,
            export_policy_alpha=0.9,
        )
        rows.append(r)

    summary = pd.DataFrame(rows)
    out_csv = os.path.join(OUTDIR, "scenario_summary.csv")
    summary.to_csv(out_csv, index=False)
    print("Saved scenario summary to:", out_csv)

    # Plot comparison chart
    import matplotlib.pyplot as plt

    plot_df = summary.copy()
    plot_df["max_shortage"] = pd.to_numeric(plot_df["max_shortage"], errors="coerce").fillna(0.0)
    plot_df = plot_df.sort_values("max_shortage", ascending=True)

    plt.figure(figsize=(11, 6))
    plt.barh(plot_df["scenario"], plot_df["max_shortage"])
    plt.xlabel("Max shortage (peak % unmet demand)")
    plt.title("Scenario Comparison (Peak Shortage)")
    plt.tight_layout()

    out_png = os.path.join(OUTDIR, "scenario_comparison.png")
    plt.savefig(out_png, dpi=200, bbox_inches="tight")
    plt.close()
    print("Saved scenario chart to:", out_png)


if __name__ == "__main__":
    main()
