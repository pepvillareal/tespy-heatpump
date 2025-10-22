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
    def safe_solve(self, mode='design', fallback_pr=4):
        """
        Wrapper for TESPy solve() with automatic compressor stabilization.
        If invalid values occur, retry with a fixed pressure ratio.
        """
        try:
            self.network.solve(mode=mode)
        except TESPyNetworkError:
            print("TESPy solver failed — retrying with fallback compressor pressure ratio...")
            self.cp.set_attr(pr=fallback_pr)
            self.network.solve(mode=mode)

        # Check if compressor results are physical
        if self.cp.P.val is None or self.cp.P.val < 0 or self.cp.pr.val < 1:
            print("Invalid compressor results detected, applying fallback (pr=4).")
            self.cp.set_attr(pr=fallback_pr)
            self.network.solve(mode=mode)

    # ------------------------------------------------------
    def run_design(self):
        """Run design-point simulation."""
        print("\n=== TESPy Design Simulation ===")
        self.safe_solve('design')
        self.network.print_results()

        COP = abs(self.co.Q.val) / self.cp.P.val
        print(f"\nDesign Results:")
        print(f"  COP                = {COP:.2f}")
        print(f"  Compressor Power   = {self.cp.P.val:.2f} kW")
        print(f"  Condenser Heat Q   = {self.co.Q.val:.2f} kW")
        print(f"  Evaporator Heat Q  = {self.ev.Q.val:.2f} kW")
        return COP

    # ------------------------------------------------------
    def run_offdesign(self, dT_source=-5):
        """Simulate off-design case (e.g., colder heat source)."""
        print("\n=== TESPy Off-Design Simulation ===")
        base_T = self.c2.T.val
        new_T = base_T + dT_source
        self.c2.set_attr(T=new_T)
        self.safe_solve('design')

        COP = abs(self.co.Q.val) / self.cp.P.val
        print(f"\nOff-Design Results (T_source={new_T:.1f} °C):")
        print(f"  COP                = {COP:.2f}")
        print(f"  Compressor Power   = {self.cp.P.val:.2f} kW")
        print(f"  Condenser Heat Q   = {self.co.Q.val:.2f} kW")
        print(f"  Evaporator Heat Q  = {self.ev.Q.val:.2f} kW")

        # Restore design condition
        self.c2.set_attr(T=base_T)
        return COP

    # ------------------------------------------------------
    def parametric_study(self):
        """Perform parametric study on source/sink temps and compressor efficiency."""
        print("\n=== TESPy Parametric Study ===")
        data = {
            'T_source': np.linspace(0, 40, 11),
            'T_sink': np.linspace(60, 100, 11),
            'eta_s': np.linspace(0.75, 0.95, 11)
        }
        COP = {key: [] for key in data}
        labels = {
            'T_source': 'Evaporation temperature (°C)',
            'T_sink': 'Condensation temperature (°C)',
            'eta_s': 'Compressor efficiency (-)'
        }

        for T in data['T_source']:
            self.c2.set_attr(T=T)
            self.safe_solve('design')
            COP['T_source'].append(abs(self.co.Q.val) / self.cp.P.val)
        self.c2.set_attr(T=20)

        for T in data['T_sink']:
            self.c4.set_attr(T=T)
            self.safe_solve('design')
            COP['T_sink'].append(abs(self.co.Q.val) / self.cp.P.val)
        self.c4.set_attr(T=80)

        for eta in data['eta_s']:
            self.cp.set_attr(eta_s=eta)
            self.safe_solve('design')
            COP['eta_s'].append(abs(self.co.Q.val) / self.cp.P.val)
        self.cp.set_attr(eta_s=0.85)

        fig, ax = plt.subplots(1, 3, sharey=True, figsize=(16, 6))
        for i, key in enumerate(data):
            ax[i].grid()
            ax[i].scatter(data[key], COP[key], color="#1f567d", s=70)
            ax[i].set_xlabel(labels[key])
        ax[0].set_ylabel("COP of the Heat Pump")
        plt.tight_layout()
        plt.savefig("heat_pump_parametric.svg")
        plt.show()
        print("Saved: heat_pump_parametric.svg")

    # ------------------------------------------------------
    def dataset_analysis(self, dataset_path):
        """Run time-series analysis based on dataset input."""
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

        if not (T_source_in and T_sink_out):
            print("Dataset does not contain recognizable temperature columns.")
            return

        print(f"Found columns: source temp={T_source_in}, sink temp={T_sink_out}")

        results = []
        for i, row in df.iterrows():
            try:
                T_src = float(row[T_source_in])
                T_sink = float(row[T_sink_out])
                if np.isnan(T_src) or np.isnan(T_sink):
                    continue

                # Skip physically unrealistic data
                if not (0 < T_src < 80 and 20 < T_sink < 120):
                    continue

                self.c2.set_attr(T=T_src)
                self.c4.set_attr(T=T_sink)
                self.safe_solve('design')

                COP = abs(self.co.Q.val) / self.cp.P.val
                results.append({
                    "index": i,
                    "T_source": T_src,
                    "T_sink": T_sink,
                    "COP": COP,
                    "P_comp_kW": self.cp.P.val,
                    "Q_evap_kW": self.ev.Q.val,
                    "Q_cond_kW": self.co.Q.val
                })
            except Exception as e:
                print(f"Skipping row {i} due to solver issue: {e}")

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
        plt.tight_layout()
        plt.savefig("cop_timeseries.png")
        plt.show()

        print("Saved: cop_timeseries.png")


# ======================================================
#  CLI ENTRY POINT
# ======================================================
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="TESPy Heat Pump Modeling Tool")
    parser.add_argument("--mode", type=str, default="design",
                        choices=["design", "offdesign", "parametric", "dataset"],
                        help="Simulation mode")
    parser.add_argument("--data", type=str, default=None,
                        help="Path to Excel dataset for 'dataset' mode")
    args = parser.parse_args()

    hp = HeatPumpModel(refrigerant="R134a")

    if args.mode == "design":
        hp.run_design()
    elif args.mode == "offdesign":
        hp.run_offdesign(dT_source=-5)
    elif args.mode == "parametric":
        hp.parametric_study()
    elif args.mode == "dataset":
        if args.data:
            hp.dataset_analysis(args.data)
        else:
            print("Please specify dataset path using --data option.")