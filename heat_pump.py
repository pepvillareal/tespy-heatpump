#!/usr/bin/env python3
# ======================================================
# Heat Pump Modeling Tool using TESPy
# Author: Paul Evahn Padlan Villareal
# Date: 2025-10-22
# ======================================================
"""
Heat Pump Modeling Tool
-----------------------
This script models a simple vapor compression heat pump system using TESPy.

Features:
- Simulates design and off-design conditions
- Reads a dataset of heat source/sink data
- Calculates COP, compressor power, and heat transfer rates
- Plots time-series performance
- Automatically stabilizes compressor if solver finds invalid states
"""

import argparse
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from tespy.networks import Network
from tespy.components import CycleCloser, Compressor, Valve, SimpleHeatExchanger
from tespy.connections import Connection
from tespy.tools.helpers import TESPyNetworkError


# ======================================================
#  CLASS: HeatPumpModel
# ======================================================
class HeatPumpModel:
    def __init__(self, refrigerant="R134a"):
        """Initialize the heat pump network."""
        self.refrigerant = refrigerant
        self.network = Network(fluids=[refrigerant])
        self.network.set_attr(
            T_unit="C",
            p_unit="bar",
            h_unit="kJ / kg",
            Q_unit="kW",
            P_unit="kW"
        )

        # Components
        self.cc = CycleCloser('cycle closer')
        self.ev = SimpleHeatExchanger('evaporator')
        self.co = SimpleHeatExchanger('condenser')
        self.va = Valve('expansion valve')
        self.cp = Compressor('compressor')

        # Connections
        self.c1 = Connection(self.cc, 'out1', self.ev, 'in1', label='1')
        self.c2 = Connection(self.ev, 'out1', self.cp, 'in1', label='2')
        self.c3 = Connection(self.cp, 'out1', self.co, 'in1', label='3')
        self.c4 = Connection(self.co, 'out1', self.va, 'in1', label='4')
        self.c0 = Connection(self.va, 'out1', self.cc, 'in1', label='0')

        self.network.add_conns(self.c1, self.c2, self.c3, self.c4, self.c0)

        # Define fluid composition only once (avoid TESPy loop conflicts)
        self.c1.set_attr(fluid={refrigerant: 1})

        # Default design specifications
        self.co.set_attr(pr=0.98, Q=-1000)   # condenser load (kW)
        self.ev.set_attr(pr=0.98)
        self.cp.set_attr(eta_s=0.85)
        self.c2.set_attr(T=20, x=1)           # evaporator outlet
        self.c4.set_attr(T=80, x=0)           # condenser outlet

    # ------------------------------------------------------
    
def safe_solve(self, mode='design', design_path=None, fallback_pr=4):
        """
        Wrapper for TESPy solve() with optional design_path forwarding for offdesign.
        Retries once with a fallback compressor pressure ratio if the solver fails.
        """
        try:
            if design_path:
                self.network.solve(mode=mode, design_path=design_path)
            else:
                self.network.solve(mode=mode)
        except TESPyNetworkError as e:
            print(f"TESPy solver failed in {mode} mode: {e}")
            # only attempt a controlled fallback for design solves
            if mode == 'design':
                print("Retrying design solve with fallback compressor pr=\"{0}\"".format(fallback_pr))
                self.cp.set_attr(pr=fallback_pr)
                self.network.solve(mode=mode)
            else:
                raise

        # basic sanity checks for compressor results
        if getattr(self.cp, 'P', None) and (self.cp.P.val is None or self.cp.P.val < 0):
            print("Warning: compressor power invalid after solve. Attempting single fallback solve.")
            self.cp.set_attr(pr=fallback_pr)
            if design_path:
                self.network.solve(mode=mode, design_path=design_path)
            else:
                self.network.solve(mode=mode)


    # ------------------------------------------------------
    
def run_design(self, save_path='design_case.json'):
        """Run design-point simulation and save design state for later off-design runs."""
        print("\n=== TESPy Design Simulation ===")
        self.safe_solve('design')
        self.network.print_results()

        # save design case for offdesign use
        try:
            self.network.save(save_path)
            print(f"Design case saved to {save_path}")
        except Exception as e:
            print(f"Warning: could not save design case: {e}")

        COP = abs(self.co.Q.val) / self.cp.P.val if self.cp.P.val else None
        print(f"\nDesign Results:")
        print(f"  COP                = {COP:.2f}" if COP else "  COP                = None")
        print(f"  Compressor Power   = {self.cp.P.val:.2f} kW")
        print(f"  Condenser Heat Q   = {self.co.Q.val:.2f} kW")
        print(f"  Evaporator Heat Q  = {self.ev.Q.val:.2f} kW")
        return COP

def run_offdesign(self, dT_source=-5, design_path='design_case.json'):
        """Simulate off-design case (e.g., colder heat source) using saved design case."""
        print("\n=== TESPy Off-Design Simulation ===")
        base_T = self.c2.T.val
        new_T = base_T + dT_source
        self.c2.set_attr(T=new_T)

        # run offdesign using the saved design case
        self.safe_solve(mode='offdesign', design_path=design_path)

        COP = abs(self.co.Q.val) / self.cp.P.val if self.cp.P.val else None
        print(f"\nOff-Design Results (T_source={new_T:.1f} °C):")
        print(f"  COP                = {COP:.2f}" if COP else "  COP                = None")
        print(f"  Compressor Power   = {self.cp.P.val:.2f} kW")
        print(f"  Condenser Heat Q   = {self.co.Q.val:.2f} kW")
        print(f"  Evaporator Heat Q  = {self.ev.Q.val:.2f} kW")

        # Restore original temperature (keeps object state like original script)
        self.c2.set_attr(T=base_T)
        return COP

def dataset_analysis(self, dataset_path, design_path='design_case.json'):
        """Run time-series analysis based on dataset input using offdesign solves."""
        print("\n=== Dataset-Based Simulation ===")
        xls = pd.ExcelFile(dataset_path)
        df = pd.concat([xls.parse(s) for s in xls.sheet_names], ignore_index=True)

        def find_col(cols, keys):
            for k in keys:
                for c in cols:
                    if k.lower() in c.lower():
                        return c
            return None

        T_source_in = find_col(df.columns, ["source", "T_in", "inlet"])
        T_sink_out = find_col(df.columns, ["sink", "T_out", "outlet"])

        if T_source_in is None or T_sink_out is None:
            print("Dataset does not contain recognizable temperature columns.")
            return

        print(f"Found columns: source temp={T_source_in}, sink temp={T_sink_out}")

        results = []
        for i, row in df.iterrows():
            try:
                T_src = float(row[T_source_in])
                T_sink = float(row[T_sink_out])
            except Exception:
                continue

            # basic sanity filter
            if np.isnan(T_src) or np.isnan(T_sink):
                continue

            # set boundary temps on connections (match original style)
            self.c1.set_attr(T=T_src)
            self.c4.set_attr(T=T_sink)

            try:
                # run offdesign solve relative to saved design case
                self.safe_solve(mode='offdesign', design_path=design_path)
                COP = abs(self.co.Q.val / self.cp.P.val) if self.cp.P.val else None
                results.append({
                    'T_source': T_src,
                    'T_sink': T_sink,
                    'COP': COP,
                    'Q_cond_kW': abs(self.co.Q.val) if self.co.Q.val is not None else None,
                    'Q_evap_kW': abs(self.ev.Q.val) if self.ev.Q.val is not None else None,
                    'Power_kW': abs(self.cp.P.val) if self.cp.P.val is not None else None
                })
            except Exception as e:
                # record failed point as NaNs
                results.append({
                    'T_source': T_src,
                    'T_sink': T_sink,
                    'COP': None,
                    'Q_cond_kW': None,
                    'Q_evap_kW': None,
                    'Power_kW': None
                })

        res_df = pd.DataFrame(results)
        res_df.to_csv("hp_timeseries_metrics.csv", index=False)
        print(f"\nSaved: hp_timeseries_metrics.csv ({len(res_df)} points)")

        if len(res_df) == 0:
            print("No valid simulation points found — check dataset ranges or inputs.")
            return

        plt.figure(figsize=(10, 4))
        plt.plot(res_df["COP"], label="COP")
        plt.title("COP Time Series")
        plt.xlabel("Time Index")
        plt.ylabel("COP (-)")
        plt.grid()
        plt.legend()
        plt.tight_layout()
        plt.savefig('hp_cop_timeseries.png')
        print('Saved: hp_cop_timeseries.png')
