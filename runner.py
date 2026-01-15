from src.world import build_toy_world
from src.simulate import step
from src.shocks import reduce_edge_capacity
from src.plotting import plot_series

import csv
import os

def run_scenario(name: str, shock: bool):
    G = build_toy_world()

    if shock:
        reduce_edge_capacity(G, "CHN", "SGP", pct=0.8)

    history = []

    for t in range(10):
        m = step(G)
        m["day"] = t
        m["scenario"] = name
        history.append(m)
        print(f"{name} Day {t}: {m}")

    return history

def main():
    os.makedirs("outputs", exist_ok=True)

    print("=== RUNNING BASELINE ===")
    baseline = run_scenario("baseline", shock=False)

    print("\n=== RUNNING SHOCK ===")
    shock = run_scenario("shock_chokepoint", shock=True)

    # Plot graphs
    plot_series(
        [r["shortage_pct"] for r in baseline],
        "Baseline Shortage Over Time",
        "outputs/baseline_shortage.png"
    )

    plot_series(
        [r["shortage_pct"] for r in shock],
        "Chokepoint Shock Shortage Over Time",
        "outputs/shock_shortage.png"
    )

    # Save CSV
    with open("outputs/summary.csv", "w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["scenario", "day", "total_demand", "total_unmet", "shortage_pct"]
        )
        writer.writeheader()
        writer.writerows(baseline + shock)

    print("\nSaved files to /outputs folder")

if __name__ == "__main__":
    main()
