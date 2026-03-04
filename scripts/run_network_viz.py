from __future__ import annotations

import os
import math
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt

OUTDIR = "outputs"
CSV_PATH = os.path.join("data", "sample_trade_flows.csv")

TOP_EDGES_TO_PLOT = 80
LABEL_TOP_NODES = 10


def main() -> None:
    os.makedirs(OUTDIR, exist_ok=True)

    df = pd.read_csv(CSV_PATH)
    df["exporter"] = df["exporter"].astype(str).str.upper().str.strip()
    df["importer"] = df["importer"].astype(str).str.upper().str.strip()
    df["trade_value"] = pd.to_numeric(df["trade_value"], errors="coerce").fillna(0.0)

    df = df[(df["exporter"] != df["importer"]) & (df["trade_value"] > 0)].copy()
    df = df.groupby(["exporter", "importer"], as_index=False)["trade_value"].sum()

    df_plot = df.sort_values("trade_value", ascending=False).head(TOP_EDGES_TO_PLOT).copy()

    # Directed graph for drawing
    G = nx.DiGraph()
    for r in df_plot.itertuples(index=False):
        G.add_edge(r.exporter, r.importer, weight=float(r.trade_value))

    # Use an undirected version for layout (cleaner geometry)
    Gu = nx.Graph()
    for (u, v, data) in G.edges(data=True):
        w = float(data.get("weight", 1.0))
        if Gu.has_edge(u, v):
            Gu[u][v]["weight"] += w
        else:
            Gu.add_edge(u, v, weight=w)

    # Layout: Kamada-Kawai tends to spread small/medium graphs nicely
    pos = nx.kamada_kawai_layout(Gu, weight="weight")

    weights = [G[u][v]["weight"] for (u, v) in G.edges()]
    w_min = min(weights) if weights else 1.0
    w_max = max(weights) if weights else 1.0

    def edge_width(w: float) -> float:
        if w <= 0:
            return 0.6
        x = (math.log10(w) - math.log10(w_min)) / (math.log10(w_max) - math.log10(w_min) + 1e-9)
        return 0.8 + 4.0 * x

    widths = [edge_width(w) for w in weights]

    # Node sizes by total degree (in+out) so hubs visually stand out
    deg = {n: (G.in_degree(n) + G.out_degree(n)) for n in G.nodes()}
    d_min = min(deg.values()) if deg else 1
    d_max = max(deg.values()) if deg else 1

    def node_size(d: int) -> float:
        if d_max == d_min:
            return 650
        x = (d - d_min) / (d_max - d_min)
        return 500 + 1200 * x

    node_sizes = [node_size(deg.get(n, 0)) for n in G.nodes()]

    # Label only the top hubs
    top_nodes = set(sorted(deg, key=deg.get, reverse=True)[:LABEL_TOP_NODES])
    labels = {n: n for n in G.nodes() if n in top_nodes}

    plt.figure(figsize=(13, 9))

    nx.draw_networkx_nodes(G, pos, node_size=node_sizes)

    nx.draw_networkx_edges(
        G,
        pos,
        arrows=True,
        width=widths,
        alpha=0.55,
        arrowstyle="-|>",
        arrowsize=11,
        connectionstyle="arc3,rad=0.10",
    )

    nx.draw_networkx_labels(
        G,
        pos,
        labels=labels,
        font_size=10,
        bbox=dict(facecolor="white", edgecolor="none", alpha=0.7, pad=0.3),
    )

    plt.title(f"Trade Network Core (Top {TOP_EDGES_TO_PLOT} edges by value)")
    plt.axis("off")

    out_png = os.path.join(OUTDIR, "sample_trade_network.png")
    plt.savefig(out_png, dpi=220, bbox_inches="tight")
    plt.close()

    print("Saved network visualization to:", out_png)


if __name__ == "__main__":
    main()
