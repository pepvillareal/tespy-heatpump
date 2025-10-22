# Heat Pump Modeling Tool (TESPy)

**Author:** Paul Evahn Padlan Villareal
**Date:** 25 October 2025  

---

## Overview

This repository provides a **flexible heat pump modeling tool** built with the [TESPy](https://github.com/oemof/tespy) library.  
It simulates **design**, **off-design**, and **dataset-driven** operating conditions for a vapor-compression heat pump.

The model calculates:
- **Coefficient of Performance (COP)**
- **Compressor power consumption**
- **Condenser and evaporator heat transfer rates**
- Optional time-series performance plots using real input data

This tool is intended as a **demonstration of engineering modeling and simulation capabilities** using Python and TESPy.

---

## Features

| Simulation Type | Description |
|------------------|-------------|
| **Design** | Simulates optimal operating point (ηₛ = 0.85, Q = 1000 kW). |
| **Off-design** | Models part-load or altered source/sink temperatures (e.g. –5 °C source change). |
| **Parametric study** | Performs temperature and compressor-efficiency sweeps, plotting COP trends. |
| **Dataset-driven** | Reads real temperature and flow data from Excel, calculates COP and heat transfer over time. |

---

## Model Structure

The heat pump system includes:
- **CycleCloser**: closes the refrigerant circuit  
- **Evaporator**: heat source side (low temperature)  
- **Compressor**: raises refrigerant pressure  
- **Condenser**: heat sink side (high temperature)  
- **Expansion Valve**: throttles refrigerant back to low pressure  

Refrigerant: **R134a**

TESPy handles thermodynamic property evaluation and mass/energy balance.

---

## Installation

### Create a clean environment (recommended)
```bash
conda create -n hp_env python=3.11
conda activate hp_env