# Global Crisis Simulator

A network-based simulator for analyzing how supply chain disruptions propagate through international trade flows. The project models countries as nodes, trade relationships as directed capacity-constrained edges, and measures system-wide shortages under shocks, export controls, and recovery dynamics.

## Trade Network Visualization

![Trade Network](outputs/sample_trade_network.png)

## Fragile Trade Links

![Fragility Chart](outputs/sample_fragility_top10.png)

## Shortage Distribution

![Monte Carlo Histogram](outputs/sample_max_shortage_hist.png)

## What this does

- Builds a directed trade network from bilateral trade flows
- Simulates inventory, production, and constrained trade fulfillment
- Applies shocks to trade capacity and models recovery
- Introduces export controls when domestic shortages rise
- Runs Monte Carlo simulations to estimate systemic risk
- Identifies fragile trade links whose disruption causes the largest shortages

## Project structure

src/
- world.py — builds the trade network
- simulate.py — daily inventory and trade simulation
- shocks.py — disruption modeling
- monte_carlo.py — simulation trials
- fragility.py — edge fragility analysis

scripts/
- generate_sample_data.py — generates a reproducible dataset
- run_real_data.py — runs simulations
- run_network_viz.py — builds the network visualization
- run_fragility.py — computes fragility rankings
- run_fragility_viz.py — plots the top fragile edges
- run_all.py — runs the full pipeline

## Quick start

Install dependencies:

python -m pip install -r requirements.txt

Run the simulator:

python -m scripts.run_all

Outputs will be written to the `outputs/` directory.

## Notes

This project models how supply chain disruptions propagate through trade networks using a simplified but extensible framework. It captures several real-world mechanisms including inventory buffering, demand volatility, capacity constraints, and export restrictions.

The framework can be extended to incorporate sector-specific networks, price dynamics, and real-world economic indicators.

