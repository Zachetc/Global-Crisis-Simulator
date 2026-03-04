# Global Supply Chain Crisis Simulator

A Python simulation framework for analyzing cascading supply shortages in an international trade network.  
The model represents countries as nodes connected by directed trade flows and evaluates how disruptions propagate through the system under stochastic shock scenarios.

The simulator uses Monte Carlo trials to estimate the severity, duration, and recovery dynamics of supply shocks. It also computes edge-level fragility scores to identify trade relationships that contribute disproportionately to systemic risk.

## Model Overview

### Network Representation
- Nodes represent countries or regions.
- Directed edges represent trade flows from exporter to importer.
- Edge capacity is proportional to trade value and scaled internally to maintain simulation stability.

Each node maintains:
- production capacity
- demand
- inventory buffer

### Simulation Dynamics
The system evolves in daily time steps:

1. Nodes satisfy demand using production and available inventory.
2. Remaining inventory becomes available for export.
3. Export supply is allocated across outgoing trade edges.
4. Inventory is updated based on imports received and domestic demand.

### Shock Scenarios
Monte Carlo trials sample disruption events that temporarily reduce edge capacity.

### Fragility Analysis
The simulator evaluates the systemic importance of individual trade edges by reducing their capacity and measuring the resulting increase in global shortage levels.

## Repository Structure

data/
sample_trade_flows.csv

src/
simulation engine

scripts/
analysis pipelines

outputs/
generated results

## Running the Simulation

python -m scripts.run_all

## License
MIT
