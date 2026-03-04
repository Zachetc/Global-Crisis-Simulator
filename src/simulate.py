import networkx as nx


def _float(x, default=0.0) -> float:
    try:
        return float(x)
    except Exception:
        return float(default)


def step(
    G: nx.DiGraph,
    *,
    export_buffer: float = 0.0,
    export_policy_alpha: float = 0.9,
) -> dict:
    """
    One simulation day.

    export_buffer: baseline fraction of inventory held back from exports (0..1)
    export_policy_alpha: additional retention triggered by domestic shortage (0..1)
        keep_frac = export_buffer + export_policy_alpha * shortage_ratio
    """

    unmet = {n: 0.0 for n in G.nodes()}
    demand_by_node = {n: 0.0 for n in G.nodes()}

    # 1) Local satisfaction
    for n, data in G.nodes(data=True):
        lp = _float(data.get("local_production", 0.0))
        inv = _float(data.get("inventory", 0.0))
        dem = _float(data.get("demand", 0.0))

        demand_by_node[n] = dem

        available_local = lp + inv
        used = min(available_local, dem)

        unmet[n] = dem - used
        G.nodes[n]["inventory"] = available_local - used

    # 2) Exports (endogenous export retention under domestic stress)
    exportable = {}
    base_keep = max(0.0, min(1.0, float(export_buffer)))
    alpha = max(0.0, min(1.0, float(export_policy_alpha)))

    for u in G.nodes():
        inv = _float(G.nodes[u].get("inventory", 0.0))
        dem = max(1e-12, _float(demand_by_node.get(u, 0.0), 0.0))

        shortage_ratio = max(0.0, min(1.0, _float(unmet.get(u, 0.0), 0.0) / dem))
        keep_frac = max(0.0, min(1.0, base_keep + alpha * shortage_ratio))

        keep = keep_frac * inv
        exportable[u] = max(0.0, inv - keep)

    # 3) Shipments proportional to outgoing capacities
    for u in G.nodes():
        out_edges = list(G.out_edges(u, data=True))
        if not out_edges:
            continue

        avail = exportable.get(u, 0.0)
        if avail <= 0:
            continue

        caps = []
        total_cap = 0.0
        for (uu, v, edata) in out_edges:
            cap = _float(edata.get("capacity", 0.0))
            caps.append(cap)
            total_cap += cap

        if total_cap <= 0:
            continue

        total_ship = min(avail, total_cap)

        shipped_sum = 0.0
        for i, (uu, v, edata) in enumerate(out_edges):
            cap = caps[i]
            if cap <= 0:
                continue

            sent = total_ship * (cap / total_cap)
            shipped_sum += sent

            used = min(sent, unmet[v])
            unmet[v] -= used
            leftover = sent - used
            G.nodes[v]["inventory"] = _float(G.nodes[v].get("inventory", 0.0)) + leftover

        G.nodes[u]["inventory"] = max(0.0, _float(G.nodes[u].get("inventory", 0.0)) - shipped_sum)

    total_demand = sum(_float(demand_by_node.get(n, 0.0), 0.0) for n in G.nodes())
    total_unmet = sum(unmet.values())

    return {
        "total_demand": total_demand,
        "total_unmet": total_unmet,
        "shortage_pct": (total_unmet / total_demand) if total_demand else 0.0,
        "unmet_by_node": dict(unmet),
    }
