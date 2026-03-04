from __future__ import annotations

import os
import pandas as pd

from src.monte_carlo import run_monte_carlo
from src.plotting import plot_hist

OUTDIR = "outputs"
DEFAULT_CSV = os.path.join("data", "sample_trade_flows.csv")


def choose_scale(trade_values: pd.Series, target_median_capacity: float = 100.0) -> float:
    tv = pd.to_numeric(trade_values, errors="coerce").dropna()
    tv = tv[tv > 0]
    if tv.empty:
        return 1e-12
    med = float(tv.median())
    return target_median_capacity / med


def main() -> None:
    os.makedirs(OUTDIR, exist_ok=True)

    if not os.path.exists(DEFAULT_CSV):
        raise FileNotFoundError(
            f"Missing {DEFAULT_CSV}. Create it with columns exporter,importer,trade_value,year."
        )

    trade_df = pd.read_csv(DEFAULT_CSV)

    required = {"exporter", "importer", "trade_value", "year"}
    missing = required - set(trade_df.columns)
    if missing:
        raise ValueError(f"{DEFAULT_CSV} is missing columns: {sorted(missing)}")

    trade_df["exporter"] = trade_df["exporter"].astype(str).str.upper().str.strip()
    trade_df["importer"] = trade_df["importer"].astype(str).str.upper().str.strip()
    trade_df["trade_value"] = pd.to_numeric(trade_df["trade_value"], errors="coerce").fillna(0.0)
    trade_df["year"] = pd.to_numeric(trade_df["year"], errors="coerce").fillna(0).astype(int)

    trade_df = trade_df[(trade_df["exporter"] != trade_df["importer"]) & (trade_df["trade_value"] > 0)].copy()
    trade_df = trade_df.groupby(["exporter", "importer", "year"], as_index=False)["trade_value"].sum()

    print("Loaded CSV:", DEFAULT_CSV)
    print("Rows:", len(trade_df))
    print(trade_df.head(10).to_string(index=False))

    flows_csv = os.path.join(OUTDIR, "sample_trade_flows_normalized.csv")
    trade_df.to_csv(flows_csv, index=False)
    print("Saved normalized flows to:", flows_csv)

    # Auto-scale so capacities aren't all clamped to the min
    scale = choose_scale(trade_df["trade_value"], target_median_capacity=100.0)
    min_capacity = 0.1

    print(f"Using edge_capacity_scale={scale:.3e} (median edge capacity ~100), min_capacity={min_capacity}")

    countries = sorted(set(trade_df["exporter"]).union(set(trade_df["importer"])))

    results = run_monte_carlo(
        n_trials=200,
        days=40,
        world_builder="trade_df",
        world_kwargs={
            "trade_df": trade_df,
            "countries": countries,
            "edge_capacity_scale": scale,
            "demand_scale": scale,
            "production_scale": scale,
            "inventory_days": 14.0,
            "min_capacity": min_capacity,
        },
    )

    summary_df = pd.DataFrame(
        [
            {
                "event_type": r.get("event_type"),
                "severity": r.get("severity"),
                "duration": r.get("duration"),
                "recovery": r.get("recovery"),
                "avg_shortage": r.get("avg_shortage"),
                "max_shortage": r.get("max_shortage"),
                "shortage_auc": r.get("shortage_auc"),
                "recovery_day": r.get("recovery_day"),
            }
            for r in results
        ]
    )

    summary_csv = os.path.join(OUTDIR, "sample_monte_carlo_summary.csv")
    summary_df.to_csv(summary_csv, index=False)
    print("Saved Monte Carlo summary to:", summary_csv)

    hist_png = os.path.join(OUTDIR, "sample_max_shortage_hist.png")
    plot_hist(
        summary_df["max_shortage"].astype(float).tolist(),
        "Sample data: Max shortage over trials",
        hist_png,
    )
    print("Saved histogram to:", hist_png)

    print("\nDone. Check outputs/ for CSV + PNG files.")


if __name__ == "__main__":
    main()
