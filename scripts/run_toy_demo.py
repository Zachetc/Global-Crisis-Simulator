from __future__ import annotations
import os

from src.monte_carlo import run_monte_carlo
from src.plotting import plot_hist, plot_series

OUTDIR = "outputs"

def main():
    os.makedirs(OUTDIR, exist_ok=True)

    results = run_monte_carlo(
        n_trials=300,
        days=40,
        world_builder="toy",
    )

    max_shortages = [r["max_shortage"] for r in results]
    auc = [r["shortage_auc"] for r in results]

    plot_hist(max_shortages, "Toy world: Max shortage over trials", f"{OUTDIR}/toy_max_shortage_hist.png")
    plot_hist(auc, "Toy world: Shortage AUC over trials", f"{OUTDIR}/toy_shortage_auc_hist.png")

    example = results[0]["shortage_pct_series"]
    plot_series(example, "Toy world: Example shortage time series", f"{OUTDIR}/toy_example_series.png")

    print("Wrote outputs to:", OUTDIR)

if __name__ == "__main__":
    main()

