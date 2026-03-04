from __future__ import annotations
from copy import deepcopy

def run_days(G, days: int) -> float:
    from src.simulate import step
    shortages = []
    for _ in range(days):
        m = step(G)
        shortages.append(float(m["shortage_pct"]))
    return sum(shortages) / len(shortages) if shortages else 0.0

def edge_fragility_ranking(days: int = 20, reduction_pct: float = 0.8) -> list[dict]:
    from src.world import build_toy_world

    baseG = build_toy_world()
    baseline = run_days(deepcopy(baseG), days)

    results = []
    for (u, v, data) in list(baseG.edges(data=True)):
        G = deepcopy(baseG)

        if "capacity" in G[u][v]:
            G[u][v]["capacity"] = float(G[u][v]["capacity"]) * (1.0 - reduction_pct)

        shocked = run_days(G, days)

        results.append({
            "u": u,
            "v": v,
            "baseline_avg_shortage": baseline,
            "shocked_avg_shortage": shocked,
            "delta": shocked - baseline,
        })

    results.sort(key=lambda r: r["delta"], reverse=True)
    return results
