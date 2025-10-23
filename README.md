# Heat Pump Modeling Tool (TESPy)

**Author:** Paul Evahn Padlan Villareal  
**Date:** 25 October 2025  

---

## Overview

This repository contains a Heat Pump Modeling Tool developed in Python using the [TESPy](https://github.com/oemof/tespy) library.  
It simulates design, off-design, parametric, and dataset-driven operating conditions for a vapor-compression heat pump system.

The tool demonstrates:
- Object-oriented engineering modeling in Python.
- Simulation of thermodynamic behavior under both steady and variable conditions.
- Integration with Excel datasets for real-world scenarios.
- Visualization of key performance metrics.

---

## Objectives

The goal is to build a flexible heat pump model that:

1. Simulates design and off-design operating points.
2. Allows for parameter adjustments (temperatures, efficiencies, and loads).
3. Processes time-series datasets to compute performance metrics.
4. Produces plots and CSV outputs summarizing system behavior.

---

## Model Description

### Components

| Component | TESPy Class | Description |
|------------|--------------|-------------|
| CycleCloser | `CycleCloser` | Closes the refrigerant loop for continuity. |
| Evaporator | `SimpleHeatExchanger` | Extracts heat from the low-temperature source. |
| Compressor | `Compressor` | Increases refrigerant pressure and temperature. |
| Condenser | `SimpleHeatExchanger` | Rejects heat to the high-temperature sink. |
| Expansion Valve | `Valve` | Reduces refrigerant pressure before the evaporator inlet. |

### Working Fluid
Refrigerant used: R134a

TESPy automatically calculates thermodynamic properties and ensures energy and mass balance consistency.

---

## Installation

### Create a clean environment
```bash
conda create -n hp_env python=3.11
conda activate hp_env
pip install tespy pandas matplotlib numpy
```

### Clone the repository
```bash
git clone https://github.com/<your-username>/heat-pump-model.git
cd heat-pump-model
```

---

## Simulation Modes

| Mode | Description | Command |
|------|--------------|----------|
| Design | Solves the heat pump under nominal (design) conditions. | `python heat_pump.py --mode design` |
| Off-Design | Solves for reduced source temperature (e.g., 5 °C drop). | `python heat_pump.py --mode offdesign` |
| Parametric Study | Performs parameter sweeps for source temp, sink temp, and compressor efficiency. | `python heat_pump.py --mode parametric` |
| Dataset Mode | Runs a time-series simulation using an Excel dataset of heat source/sink temperatures. | `python heat_pump.py --mode dataset --data HP_case_data.xlsx` |

---

## Input Dataset

Input data must be an Excel file (`.xlsx`) that contains heat source and heat sink temperatures.

### Example structure

| Time | T_source_in (°C) | T_sink_out (°C) |
|------|------------------:|----------------:|
| 0 | 25.0 | 70.0 |
| 1 | 26.5 | 71.0 |
| 2 | 27.0 | 72.0 |

Notes:
- The script automatically detects relevant column names containing “source”, “sink”, “inlet”, or “outlet”.
- It can process multiple sheets by merging them into a single dataset.

---

## Outputs

After each simulation, the following files are generated:

| File | Description |
|------|--------------|
| heat_pump_parametric.svg | COP plots from parametric study (vs. temperature & efficiency). |
| hp_timeseries_metrics.csv | Time-series results (COP, compressor power, Q values). |
| cop_timeseries.png | COP variation plot over dataset time index. |

### Example CSV Output

| index | T_source | T_sink | COP | P_comp_kW | Q_evap_kW | Q_cond_kW |
|------:|----------:|--------:|----:|-----------:|-----------:|-----------:|
| 0 | 25.0 | 70.0 | 3.52 | 284.5 | 1000 | -1285 |
| 1 | 26.5 | 71.0 | 3.60 | 278.0 | 1000 | -1280 |

---

## Key Calculations

For each simulation step, the model computes:

- Coefficient of Performance (COP) = |Q_cond| / P_comp  
- Compressor Power (P_comp)  
- Evaporator Heat (Q_evap)  
- Condenser Heat (Q_cond)  

These outputs help assess performance under variable thermal and electrical conditions.

---

## Section-by-Section Code Explanation (heat_pump.py)

### 1. File Header
```python
#!/usr/bin/env python3
# Heat Pump Modeling Tool using TESPy
# Author: Paul Evahn Padlan Villareal
```
This defines the script metadata and enables execution from the command line (`chmod +x heat_pump.py`).

---

### 2. Imports
```python
import argparse, pandas as pd, matplotlib.pyplot as plt, numpy as np
from tespy.networks import Network
from tespy.components import CycleCloser, Compressor, Valve, SimpleHeatExchanger
from tespy.connections import Connection
from tespy.tools.helpers import TESPyNetworkError
```
These libraries enable:
- CLI parsing (`argparse`)
- Data handling (`pandas`, `numpy`)
- Visualization (`matplotlib`)
- TESPy thermodynamic modeling

---

### 3. Class Definition
```python
class HeatPumpModel:
    def __init__(self, refrigerant="R134a"):
        self.network = Network(fluids=[refrigerant])
```
Defines the main object-oriented structure.  
The constructor initializes:
- TESPy Network with defined units (°C, bar, kW).
- Model components (CycleCloser, Evaporator, Compressor, etc.).
- Refrigerant composition (R134a).

---

### 4. Network Configuration
Connections define refrigerant flow:
```python
self.c1 = Connection(self.cc, 'out1', self.ev, 'in1')
self.c2 = Connection(self.ev, 'out1', self.cp, 'in1')
self.c3 = Connection(self.cp, 'out1', self.co, 'in1')
self.c4 = Connection(self.co, 'out1', self.va, 'in1')
self.c0 = Connection(self.va, 'out1', self.cc, 'in1')
```
TESPy uses these to maintain mass and energy continuity across the loop.

---

### 5. Default Parameters
```python
self.co.set_attr(pr=0.98, Q=-1000)
self.cp.set_attr(eta_s=0.85)
self.c2.set_attr(T=20, x=1)
self.c4.set_attr(T=80, x=0)
```
Defines nominal (design) conditions:
- Condenser provides 1000 kW heat at 80 °C.
- Compressor efficiency is 0.85.
- Evaporator outlet vapor is at 20 °C.

---

### 6. Safe Solver Function
```python
def safe_solve(self, mode='design', fallback_pr=4):
```
TESPy may fail under off-design states.  
This function retries with a fallback compressor pressure ratio if solver errors occur — ensuring model robustness.

---

### 7. Design Simulation
```python
def run_design(self):
    self.safe_solve('design')
```
Runs the nominal simulation and prints:
- COP  
- Compressor power  
- Condenser and evaporator loads  

---

### 8. Off-Design Simulation
```python
def run_offdesign(self, dT_source=-5):
```
Simulates reduced source temperature (e.g., colder ambient).  
Adjusts the evaporator outlet temp by –5 °C, solves, and reports new performance metrics.

---

### 9. Parametric Study
```python
def parametric_study(self):
```
Performs systematic sweeps for:
- T_source (0–40 °C)
- T_sink (60–100 °C)
- η_s (Compressor Efficiency) (0.75–0.95)

Each variable’s effect on COP is plotted and saved as `heat_pump_parametric.svg`.

---

### 10. Dataset Simulation
```python
def dataset_analysis(self, dataset_path):
```
Reads an Excel dataset and loops through temperature entries to:
- Update model parameters
- Run simulations for each time point
- Export results (`hp_timeseries_metrics.csv`)
- Plot COP time evolution (`cop_timeseries.png`)

---

### 11. Command-Line Interface (CLI)
```python
if __name__ == "__main__":
```
Allows users to select modes via command-line flags:
```bash
python heat_pump.py --mode design
python heat_pump.py --mode offdesign
python heat_pump.py --mode parametric
python heat_pump.py --mode dataset --data HP_case_data.xlsx
```

---

## Design vs. Off-Design Conditions

| Condition | Description | Example |
|------------|--------------|----------|
| Design | Optimal parameters (ηₛ = 0.85, source 40→10°C, sink 40→90°C, Q = 1000 kW). | `python heat_pump.py --mode design` |
| Off-Design | Part-load or reduced source temperature (e.g., –5 °C). | `python heat_pump.py --mode offdesign` |

---

## Visualization Examples

### Parametric Study (COP vs. Key Variables)
Output: `heat_pump_parametric.svg`

### COP Time Series (from dataset)
Output: `cop_timeseries.png`

---

## Notes & Recommendations
- The model is modular — additional components or refrigerants can be easily integrated.
- TESPy ensures thermodynamic consistency.
- Results are reproducible for both steady and transient-like dataset inputs.

---

## Questions or Support
If you have any questions, please contact:  
Email: pep.villareal@gmail.com

---

## References
- [TESPy Documentation](https://tespy.readthedocs.io/)
- OEMoF Energy Modeling Framework

---
