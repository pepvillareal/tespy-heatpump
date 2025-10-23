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
