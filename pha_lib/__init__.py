"""pha_lib — biblioteka do analizy danych z systemu PHA na W7-X.

Quick usage
-----------
>>> from pha_lib import io, pipeline, export
>>> shot = io.load_united_txt("unitedc_62_239.txt", shot_id="XP_test")
>>> results = pipeline.analyze_shot(shot, line_energy_eV=6660.0)
>>> # results = {1: DataFrame, 2: DataFrame} — osobno dla każdego kanału
>>> export.save_results_parquet(results, out_dir="output/")

Modules
-------
- model      : klasy danych (Shot, EnergyChannelData, TimeTrace, Discharge, FitResult)
- io         : czytanie wejścia (united .txt, folder test_<n>.txt; placeholder .pha)
- timetrace  : zamiana widm w przebieg czasowy (suma countów w oknie energii)
- discharges : detekcja start/finish ramek discharge
- fit        : 2-parametrowy fit y(t)=A*exp(-(t-t_0)/tau)+C
               (t_0 i C zafiksowane; wolne: A, tau)
- pipeline   : analyze_shot — sklejony przepływ, zwraca dict[channel -> DataFrame]
- export     : zapis Parquet
- plotting   : wykresy diagnostyczne (TimeTrace + discharges, fit per discharge)
"""
from . import (  # noqa: F401
    model, io, timetrace, discharges, fit, pipeline, export, plotting,
)

__version__ = "0.3.0"