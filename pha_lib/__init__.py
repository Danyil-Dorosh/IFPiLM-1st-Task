"""pha_lib — library for analysing PHA system data from W7-X.

Quick usage
-----------
>>> from pha_lib import io, pipeline, export
>>> discharge = io.load_united_txt("unitedc_62_239.txt", discharge_id="XP_test")
>>> results = pipeline.analyze_discharge(discharge, line_energy_eV=6660.0)
>>> # results = {1: DataFrame, 2: DataFrame} — separate DataFrame per channel
>>> export.save_results_parquet(results, out_dir="output/")

Modules
-------
- model      : data classes (Discharge, EnergyChannelData, TimeTrace, Injection, FitResult)
- io         : input readers (unified .txt, folder test_<n>.txt; placeholder .pha)
- timetrace  : convert spectra to time traces (sum of counts in energy window)
- discharges : injection detection in time traces
- fit        : 2-parameter fit y(t)=A*exp(-(t-t_0)/tau)+C
               (t_0 and C fixed; free: A, tau)
- pipeline   : analyze_discharge — composed flow, returns dict[channel -> DataFrame]
- export     : Parquet export utilities
- plotting   : diagnostic plots (TimeTrace + injections, fit per injection)
"""
from . import (  # noqa: F401
    model, io, timetrace, discharges, fit, pipeline, export, plotting,
)

__version__ = "0.3.0"