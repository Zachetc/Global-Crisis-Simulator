import networkx as nx

def step(G: nx.DiGraph) -> dict:
    unmet = {}

    # 1) Each node satisfies its own demand using local_production + inventory
    for n, data in G.nodes(data=True):
        available_local = float(data["local_production"] + data["inventory"])
        demand = float(data["demand"])

        used = min(available_local, demand)
        unmet[n] = demand - used

        # remaining becomes inventory (local buffer)
        G.nodes[n]["inventory"] = available_local - used

    # 2) Ship export_supply across edges (this is what shocks will impact)
    export_pool = {n: float(G.nodes[n]["export_supply"]) for n in G.nodes()}

    for u in G.nodes():
        outgoing = list(G.out_edges(u, data=True))
        if not outgoing or export_pool[u] <= 0:
            continue

        # distribute export supply proportional to edge capacity
        total_cap = sum(float(edata["capacity"]) for _, _, edata in outgoing)
        if total_cap <= 0:
            continue

        for _, v, edata in outgoing:
            cap = float(edata["capacity"])
            sent = min(export_pool[u] * (cap / total_cap), cap)
            export_pool[u] -= sent

            # receiver uses imports to reduce unmet demand first, then stores leftovers
            used = min(sent, unmet[v])
            unmet[v] -= used
            leftover = sent - used
            G.nodes[v]["inventory"] += leftover

    total_demand = sum(float(G.nodes[n]["demand"]) for n in G.nodes())
    total_unmet = sum(unmet.values())

    return {
        "total_demand": total_demand,
        "total_unmet": total_unmet,
        "shortage_pct": total_unmet / total_demand if total_demand else 0.0
    }
