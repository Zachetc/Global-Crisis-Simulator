import networkx as nx

def reduce_edge_capacity(G: nx.DiGraph, u: str, v: str, pct: float):
    if G.has_edge(u, v):
        G[u][v]["capacity"] *= (1.0 - pct)
