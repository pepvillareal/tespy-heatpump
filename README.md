# Heat Pump Modeling Tool using TESPy

Author: **Paul Evahn Padlan Villareal**  
Email: **pep.villareal@gmail.com**  
Date: 2025-10-23

---

## Overview
This project implements a **heat pump modeling tool** using the [TESPy](https://github.com/oemof/tespy) library.  
It models a vapor compression heat pump capable of simulating **design**, **off-design**, and **time-series (dataset)** conditions.

The tool is object-oriented, reproducible, and provides visual and tabular performance metrics including COP, compressor power, and heat transfer rates.

---

## Features
- **Design simulation** at nominal operation conditions.
- **Off-design simulation** using TESPy’s saved design-state workflow.
- **Dataset-driven time series simulation** (e.g., ambient/source temperature changes).
- **Automatic fallback handling** if TESPy solver diverges.
- **Visualization outputs** for COP trends and system performance.

---

## Environment Setup

The project uses the following pinned dependencies:
```bash
# requirements.txt

python >=3.10,<3.12
tespy==0.9.6
pandas>=1.5,<2.0
matplotlib>=3.7,<3.9
openpyxl>=3.1,<3.2
numpy>=1.24,<1.26
```

### Install Environment
```bash
# Create environment (recommended)
conda create -n hp_env python=3.10
conda activate hp_env

# Install dependencies
pip install -r requirements.txt
```

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

## Running Simulations

### 1. Design Mode
Run a baseline design-point simulation and **save** the design case file (`design_case.json`).
```bash
python heat_pump.py --mode design
```
Output files:
- `design_case.json` — saved TESPy design state for offdesign use.
- `hp_design_documentation.txt` — model summary (optional if `document_model` is called).

### 2. Off-Design Mode
Use the saved design case to simulate altered source conditions (e.g., -5°C temperature shift):
```bash
python heat_pump.py --mode offdesign --design-path design_case.json
```
This will:
- Load the saved design state.
- Adjust evaporator inlet temperature.
- Solve using TESPy’s true `offdesign` mode.

Output files:
- `offdesign_results.csv` — numerical results.

### 3. Dataset Mode
Run time-series simulation using an Excel dataset.
```bash
python heat_pump.py --mode dataset --data HP_case_data.xlsx --design-path design_case.json
```
This command:
- Loads the specified dataset.
- Applies temperature pairs (source/sink) row-by-row.
- Runs each timestep as an offdesign solve.

Output files:
- `hp_timeseries_metrics.csv` — COP, Q_cond, Q_evap, Power per timestep.
- `hp_cop_timeseries.png` — plotted COP performance.

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

## Example Workflow (Notebook)

A minimal Jupyter notebook `run_demo.ipynb` is included with the following example:
```python
from heat_pump import HeatPumpModel

hp = HeatPumpModel()
# Step 1 — Design case
design_cop = hp.run_design(save_path='design_case.json')

# Step 2 — Off-design run
hp.run_offdesign(dT_source=-5, design_path='design_case.json')

# Step 3 — Dataset simulation
hp.dataset_analysis('HP_case_data.xlsx', design_path='design_case.json')
```
This notebook visualizes COP and performance trends interactively.

---

## Outputs Summary
| File | Description |
|------|--------------|
| `design_case.json` | Saved TESPy network for offdesign use |
| `offdesign_results.csv` | Results of off-design run |
| `hp_timeseries_metrics.csv` | Full time-series performance dataset |
| `hp_cop_timeseries.png` | COP vs time plot |
| `heat_pump_parametric.svg` | Parametric COP plots (optional) |

---

## Troubleshooting
- If TESPy convergence errors occur, the tool automatically retries with a fallback compressor pressure ratio (`pr=4`).
- Ensure your dataset columns contain clear source/sink temperature identifiers (`source`, `sink`, `T_in`, `T_out`, etc.).

---

## License
This project is distributed for evaluation and demonstration purposes under an **MIT-like open license**.

---

© 2025 Paul Evahn Padlan Villareal — All rights reserved.


