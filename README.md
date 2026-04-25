# Global Crisis Simulator

A lightweight network-based simulation framework for experimenting with how localized infrastructure shocks propagate through interconnected trade-style systems.

This project explores **structural fragility, cascading disruption behavior, and recovery dynamics**, rather than forecasting real-world geopolitical outcomes.

---

## Motivation

I built this simulator to better understand how localized failures in highly connected systems can propagate across global supply-style networks.

Most modeling projects focus on prediction. This one focuses on **structure**:

* chokepoints
* dependency chains
* recovery timing
* cascading failure behavior

The goal is to create an experimentation environment rather than a forecasting engine.

---

## What This Simulator Does

The simulator models a directed trade-style network where nodes represent countries or hubs and edges represent dependency relationships.

It allows:

* chokepoint disruptions
* clustered infrastructure shocks
* correlated multi-node failures
* recovery curve experiments
* fragility ranking across nodes
* scenario comparison across time

---

## Example Scenario Types

Included scenario library:

* Singapore chokepoint disruption
* clustered regional infrastructure shock
* multi-edge correlated trade slowdown
* temporary production collapse event
* recovery-lag cascade scenario

Each scenario tests how disruptions propagate through network structure rather than isolated nodes.

---

## Architecture

Pipeline structure:

```
Network Builder
    ↓
Shock Injection Engine
    ↓
Propagation Model
    ↓
Recovery Curve Logic
    ↓
Fragility Ranking
    ↓
Visualization Layer
```

See:

```
assets/architecture.png
```

---

## Design Decisions

This simulator intentionally prioritizes interpretability over predictive realism.

Key choices:

* Used NetworkX to iterate quickly on graph experiments
* Started with deterministic recovery curves before adding stochastic noise
* Modeled chokepoint severity as edge-capacity degradation rather than node removal
* Focused on structural fragility instead of macroeconomic forecasting

Future versions could incorporate real trade-weight matrices from UN Comtrade.

---

## Example Output Metrics

Simulation outputs include:

* unmet demand percentage over time
* recovery time after peak disruption
* area-under-shortage curve (AUC)
* node fragility ranking
* cascade severity index

These allow comparison between scenarios rather than single-point predictions.

---

## Limitations

This simulator uses a stylized dependency network rather than real global trade data.

Shock propagation is deterministic instead of probabilistic.

Recovery curves are linear approximations.

Fragility scoring is heuristic and intended for experimentation only.

The simulator is designed for **scenario exploration**, not forecasting.

---

## Running the Simulator

Example baseline simulation:

```
python scripts/run_all.py
```

Scenario comparison:

```
python scripts/run_scenario_suite.py
```

Fragility ranking:

```
python scripts/run_risk_report.py
```

---

## Example Experiments Included

The project supports:

* chokepoint stress testing
* dependency cascade visualization
* scenario severity comparison
* node importance ranking
* recovery timing experiments

---

## Repository Structure

```
Global-Crisis-Simulator/
│
├── src/
├── scripts/
├── notebooks/
├── assets/
│
├── runner.py
├── fragility.py
├── monte_carlo.py
```

---

## Future Improvements

Possible extensions:

* stochastic recovery curves
* Monte Carlo parameter sweeps
* real trade-weight calibration
* probabilistic cascade branching
* scenario ensembles

---

## Author

Zachary Amachee
CIS @ Baruch College
