from __future__ import annotations

import os
from copy import deepcopy
import pandas as pd

from src.simulate import step
from src.world import build_world_from_trade_df

OUTDIR = "outputs"
CSV_PATH = os.path.join("data", "sample_trade_flows.csv")

DAYS = 30
REDUCTION_PCT = 0.80

INVENTORY_DAYS = 7.0
EXPORT_BUFFER = 0.05
EXPORT_POLICY_ALPHA = 0.90

MIN_CAPACITY = 0.1


def choose_scale(trade_values: pd.Series, target_median_capacity: float = 100.0) -> float:
    tv = pd.to_numeric(trade_values, errors="coerce").dropna()
    tv = tv[tv > 0]
    if tv.empty:
        return 1e-12
    med = float(tv.median())
    return target_median_capacity / med


def run_days(G, days: int) -> float:
    shortages = []
    for _ in range(days):
        m = step(G, export_buffer=EXPORT_BUFFER, export_policy_alpha=EXPORT_POLICY_ALPHA)
        shortages.append(float(m["shortage_pct"]))
    return sum(shortages) / len(shortages) if shortages else 0.0


def main() -> None:
    os.makedirs(OUTDIR, exist_ok=True)

    trade_df = pd.read_csv(CSV_PATH)
    trade_df["exporter"] = trade_df["exporter"].astype(str).str.upper().str.strip()
    trade_df["importer"] = trade_df["importer"].astype(str).str.upper().str.strip()
    trade_df["trade_value"] = pd.to_numeric(trade_df["trade_value"], errors="coerce").fillna(0.0)
    trade_df = trade_df[(trade_df["exporter"] != trade_df["importer"]) & (trade_df["trade_value"] > 0)].copy()
    trade_df = trade_df.groupby(["exporter", "importer", "year"], as_index=False)["trade_value"].sum()

    countries = sorted(set(trade_df["exporter"]).union(set(trade_df["importer"])))

    scale = choose_scale(trade_df["trade_value"], target_median_capacity=100.0)

    G0 = build_world_from_trade_df(
        trade_df,
        countries=countries,
        edge_capacity_scale=scale,
        demand_scale=scale,
        production_scale=scale,
        inventory_days=INVENTORY_DAYS,
        min_capacity=MIN_CAPACITY,
    )

    baseline = run_days(deepcopy(G0), DAYS)
    print("Baseline settings:")
    print(f"  DAYS={DAYS}")
    print(f"  INVENTORY_DAYS={INVENTORY_DAYS}")
    print(f"  EXPORT_BUFFER={EXPORT_BUFFER}")
    print(f"  EXPORT_POLICY_ALPHA={EXPORT_POLICY_ALPHA}")
    print(f"  edge_capacity_scale={scale:.3e}  MIN_CAPACITY={MIN_CAPACITY}")
    print(f"  Baseline avg shortage = {baseline:.6f}")

    results = []
    for (u, v, data) in list(G0.edges(data=True)):
        G = deepcopy(G0)

        base_cap = float(G[u][v].get("capacity", 0.0))
        G[u][v]["capacity"] = base_cap * (1.0 - REDUCTION_PCT)

        shocked = run_days(G, DAYS)

        results.append(
            {
                "u": u,
                "v": v,
                "baseline_avg_shortage": baseline,
                "shocked_avg_shortage": shocked,
                "delta": shocked - baseline,
                "base_capacity": base_cap,
                "shocked_capacity": float(G[u][v]["capacity"]),
            }
        )

    results.sort(key=lambda r: r["delta"], reverse=True)

    out_csv = os.path.join(OUTDIR, "sample_fragility_edges.csv")
    pd.DataFrame(results).to_csv(out_csv, index=False)
    print("Saved fragility ranking to:", out_csv)

    print("\nTop 10 edges by fragility delta:")
    print(pd.DataFrame(results).head(10).to_string(index=False))


if __name__ == "__main__":
    main()
