from __future__ import annotations
import networkx as nx


def set_edge_capacity(G: nx.DiGraph, u: str, v: str, new_capacity: float):
    if G.has_edge(u, v):
        G[u][v]["capacity"] = float(new_capacity)


def get_edge_capacity(G: nx.DiGraph, u: str, v: str) -> float:
    if G.has_edge(u, v):
        return float(G[u][v]["capacity"])
    raise KeyError(f"Edge {u}->{v} not found")


def reduce_edge_capacity(G: nx.DiGraph, u: str, v: str, pct: float):
    """Reduce capacity by pct in [0,1]."""
    if G.has_edge(u, v):
        G[u][v]["capacity"] = float(G[u][v]["capacity"]) * (1.0 - float(pct))


def shock_multiplier(t: int, duration: int, recovery: int, severity: float) -> float:
   
    severity = max(0.0, min(1.0, float(severity)))
    duration = max(0, int(duration))
    recovery = max(0, int(recovery))

    if t < duration:
        return 1.0 - severity

    if recovery <= 0:
        return 1.0

    r = t - duration
    if r >= recovery:
        return 1.0

    return (1.0 - severity) + (severity * (r + 1) / recovery)
