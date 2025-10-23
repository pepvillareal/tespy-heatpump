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
Defines script metadata and allows command-line execution.

### 2. Imports
Imports Python libraries (argparse, pandas, matplotlib, numpy) and TESPy modules for modeling.

### 3. Class Definition
Encapsulates all model setup and methods within `HeatPumpModel` for modularity and reuse.

### 4. Network Configuration
Defines all TESPy components and their interconnections for the refrigerant circuit.

### 5. Default Parameters
Sets design operating conditions (ηₛ = 0.85, Q_cond = 1000 kW, etc.).

### 6. Safe Solver Function
Ensures model stability by retrying failed TESPy solutions with fallback pressure ratios.

### 7. Design Simulation
Runs nominal operation and prints COP, compressor power, and heat rates.

### 8. Off-Design Simulation
Simulates reduced source temperature and outputs new performance data.

### 9. Parametric Study
Sweeps T_source, T_sink, and ηₛ to analyze COP trends and saves a plot.

### 10. Dataset Simulation
Loads Excel data, iterates through entries, computes COP, saves results (CSV and plot).

### 11. Command-Line Interface (CLI)
Allows mode selection via terminal using `--mode` and `--data` arguments.

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
