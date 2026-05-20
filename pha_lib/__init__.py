"""pha_lib — biblioteka do analizy danych z systemu PHA na W7-X.

Quick usage
-----------
>>> from pha_lib import io, pipeline, export
>>> discharge = io.load_united_txt("unitedc_62_239.txt", discharge_id="XP_test")
>>> results = pipeline.analyze_discharge(discharge, line_energy_eV=6660.0)
>>> # results = {1: DataFrame, 2: DataFrame} — osobno dla każdego kanału
>>> export.save_results_parquet(results, out_dir="output/")

Modules
-------
- model      : klasy danych (Discharge, EnergyChannelData, TimeTrace, Injection, FitResult)
- io         : czytanie wejścia (united .txt, folder test_<n>.txt; placeholder .pha)
- timetrace  : zamiana widm w przebieg czasowy (suma countów w oknie energii)
- discharges : detekcja injekcji w przebiegu czasowym
- fit        : 2-parametrowy fit y(t)=A*exp(-(t-t_0)/tau)+C
               (t_0 i C zafiksowane; wolne: A, tau)
- pipeline   : analyze_discharge — sklejony przepływ, zwraca dict[channel -> DataFrame]
- export     : zapis Parquet
- plotting   : wykresy diagnostyczne (TimeTrace + injekcje, fit per injection)
"""
from . import (  # noqa: F401
    model, io, timetrace, discharges, fit, pipeline, export, plotting,
)

__version__ = "0.3.0"