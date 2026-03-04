import random
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional

import networkx as nx


Edge = Tuple[str, str]


@dataclass
class ShockSpec:
    edges: List[Edge]
    severity: float
    duration: int
    recovery: int
    event_type: str


def _clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, float(x)))


def _edge_weights(G: nx.DiGraph) -> Dict[Edge, float]:
    
    weights: Dict[Edge, float] = {}
    try:
        bc = nx.edge_betweenness_centrality(G, normalized=True)
    except Exception:
        bc = {}

    for (u, v, data) in G.edges(data=True):
        cap = float(data.get("capacity", 0.0))
        w = cap * float(bc.get((u, v), 1.0))
        weights[(u, v)] = max(0.0, w)

    # ensure non-zero
    if all(w <= 0 for w in weights.values()):
        for e in weights:
            weights[e] = 1.0
    return weights


def _weighted_sample_without_replacement(items: List[Edge], weights: Dict[Edge, float], k: int) -> List[Edge]:
    """
    Simple weighted sampling w/out replacement (good enough for small graphs).
    """
    k = max(0, min(int(k), len(items)))
    chosen: List[Edge] = []
    pool = items[:]
    for _ in range(k):
        total = sum(max(0.0, weights.get(e, 0.0)) for e in pool)
        if total <= 0:
            chosen.append(pool.pop(random.randrange(len(pool))))
            continue
        r = random.random() * total
        acc = 0.0
        pick_idx = 0
        for i, e in enumerate(pool):
            acc += max(0.0, weights.get(e, 0.0))
            if acc >= r:
                pick_idx = i
                break
        chosen.append(pool.pop(pick_idx))
    return chosen


def _choose_correlated_shock(G: nx.DiGraph, severity: float, duration: int, recovery: int) -> ShockSpec:
    
    edges = list(G.edges())
    w = _edge_weights(G)

    roll = random.random()
    if roll < 0.45:
        # chokepoint
        e = _weighted_sample_without_replacement(edges, w, k=1)
        return ShockSpec(edges=e, severity=severity, duration=duration, recovery=recovery, event_type="chokepoint")

    if roll < 0.75:
        # cluster around a node (port closure / regional disruption)
        node = random.choice(list(G.nodes()))
        incident = list(G.out_edges(node)) + list(G.in_edges(node))
        incident = list({(u, v) for (u, v) in incident if G.has_edge(u, v)})
        if not incident:
            e = _weighted_sample_without_replacement(edges, w, k=2)
            return ShockSpec(edges=e, severity=severity, duration=duration, recovery=recovery, event_type="cluster_fallback")

        # shock 50-100% of incident, capped
        frac = random.uniform(0.5, 1.0)
        k = max(1, min(len(incident), int(round(frac * len(incident))), 6))
        e = _weighted_sample_without_replacement(incident, w, k=k)
        return ShockSpec(edges=e, severity=severity, duration=duration, recovery=recovery, event_type=f"cluster@{node}")

    # multi-edge random (but weighted)
    k = min(len(edges), random.randint(2, 4))
    e = _weighted_sample_without_replacement(edges, w, k=k)
    return ShockSpec(edges=e, severity=severity, duration=duration, recovery=recovery, event_type="multi")


def run_trial(
    days: int,
    severity: float,
    duration: int,
    recovery: int,
    *,
    world_builder: str = "toy",
    world_kwargs: Optional[dict] = None,
    demand_vol_sigma: float = 0.10,
    demand_vol_rho: float = 0.70,
    export_buffer: float = 0.0,
) -> dict:

    from src.simulate import step
    from src.shocks import get_edge_capacity, set_edge_capacity, shock_multiplier
    from src.world import build_toy_world, build_world_from_trade_df

    world_kwargs = world_kwargs or {}

    if world_builder == "toy":
        G = build_toy_world(**world_kwargs)
    elif world_builder == "trade_df":
        G = build_world_from_trade_df(**world_kwargs)
    else:
        raise ValueError(f"Unknown world_builder='{world_builder}'")

    # Cache base values for demand mean reversion
    for n in G.nodes():
        if "base_demand" not in G.nodes[n]:
            G.nodes[n]["base_demand"] = float(G.nodes[n].get("demand", 0.0))
        if "base_local_production" not in G.nodes[n]:
            G.nodes[n]["base_local_production"] = float(G.nodes[n].get("local_production", 0.0))

    # Choose correlated shock spec (Part C)
    spec = _choose_correlated_shock(
        G,
        severity=_clamp(severity, 0.0, 0.95),
        duration=max(0, int(duration)),
        recovery=max(0, int(recovery)),
    )

    # Snapshot base capacities for shocked edges
    base_caps = {(u, v): get_edge_capacity(G, u, v) for (u, v) in spec.edges}

    # Demand volatility (Part B/C realism): AR(1) multiplier per node
    demand_mult = {n: 1.0 for n in G.nodes()}

    # Optional: one-time production shock at t=0 (kept from your old idea, but cleaner)
    did_prod_shock = False
    prod_shock_node = None
    prod_shock_factor = 1.0
    if random.random() < 0.30:
        did_prod_shock = True
        prod_shock_node = random.choice(list(G.nodes()))
        prod_shock_factor = random.uniform(0.4, 0.8)
        G.nodes[prod_shock_node]["local_production"] = float(G.nodes[prod_shock_node]["local_production"]) * prod_shock_factor

    # Part B: time series
    shortage_pct_series: List[float] = []
    total_unmet_series: List[float] = []
    total_demand_series: List[float] = []
    unmet_by_node_series: List[Dict[str, float]] = []

    for t in range(int(days)):
        # Update demand with AR(1)-style volatility around base_demand
        for n, data in G.nodes(data=True):
            base = float(data["base_demand"])
            eps = random.gauss(0.0, float(demand_vol_sigma))
            demand_mult[n] = _clamp(demand_vol_rho * demand_mult[n] + (1.0 - demand_vol_rho) * 1.0 + eps, 0.6, 1.6)
            data["demand"] = base * demand_mult[n]

        # Apply shock multiplier to capacities
        mult = shock_multiplier(t, spec.duration, spec.recovery, spec.severity)
        for (u, v) in spec.edges:
            set_edge_capacity(G, u, v, base_caps[(u, v)] * mult)

        # Step simulation
        out = step(G, export_buffer=export_buffer)

        shortage_pct_series.append(float(out["shortage_pct"]))
        total_unmet_series.append(float(out["total_unmet"]))
        total_demand_series.append(float(out["total_demand"]))
        unmet_by_node_series.append(dict(out.get("unmet_by_node", {})))

    avg_shortage = sum(shortage_pct_series) / len(shortage_pct_series) if shortage_pct_series else 0.0
    max_shortage = max(shortage_pct_series) if shortage_pct_series else 0.0

    # "recovery day": first day after peak that returns below 25% of peak, if it happens
    peak = max_shortage
    recovery_day = None
    if peak > 0 and shortage_pct_series:
        threshold = 0.25 * peak
        peak_idx = shortage_pct_series.index(peak)
        for i in range(peak_idx, len(shortage_pct_series)):
            if shortage_pct_series[i] <= threshold:
                recovery_day = i
                break

    return {
        "event_type": spec.event_type,
        "shocked_edges": spec.edges,
        "severity": spec.severity,
        "duration": spec.duration,
        "recovery": spec.recovery,
        "did_prod_shock": did_prod_shock,
        "prod_shock_node": prod_shock_node,
        "prod_shock_factor": prod_shock_factor,
        # Part B output:
        "shortage_pct_series": shortage_pct_series,
        "total_unmet_series": total_unmet_series,
        "total_demand_series": total_demand_series,
        "unmet_by_node_series": unmet_by_node_series,
        # Summaries (still useful):
        "avg_shortage": avg_shortage,
        "max_shortage": max_shortage,
        "recovery_day": recovery_day,
        # Area-under-curve style loss:
        "shortage_auc": sum(shortage_pct_series),
    }


def run_monte_carlo(
    n_trials: int = 200,
    days: int = 30,
    *,
    severity_min: float = 0.25,
    severity_max: float = 0.85,
    duration_min: int = 3,
    duration_max: int = 14,
    recovery_min: int = 3,
    recovery_max: int = 14,
    world_builder: str = "toy",
    world_kwargs: Optional[dict] = None,
) -> List[dict]:

    results: List[dict] = []
    world_kwargs = world_kwargs or {}

    for _ in range(int(n_trials)):
        sev = random.uniform(severity_min, severity_max)
        dur = random.randint(duration_min, duration_max)
        rec = random.randint(recovery_min, recovery_max)

        results.append(
            run_trial(
                days=days,
                severity=sev,
                duration=dur,
                recovery=rec,
                world_builder=world_builder,
                world_kwargs=world_kwargs,
            )
        )

    return results
