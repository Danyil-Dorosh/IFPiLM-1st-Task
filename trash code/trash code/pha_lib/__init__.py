"""pha_lib — biblioteka do analizy danych z systemu PHA na W7-X.

Quick usage
-----------
>>> from pha_lib import io, pipeline, export
>>> shot = io.load_united_txt("unitedc_62_239.txt", shot_id="XP_test")
>>> results = pipeline.analyze_shot(shot, line_energy_eV=6660.0)
>>> # results = {1: DataFrame, 2: DataFrame} — osobno dla ka\u017cdego kana\u0142u
>>> export.save_results_parquet(results, out_dir="output/")

Modules
-------
- model      : klasy danych (Shot, EnergyChannelData, TimeTrace, Discharge, FitResult)
- io         : czytanie wej\u015bcia (united .txt, folder test_<n>.txt; placeholder .pha)
- timetrace  : zamiana widm w przebieg czasowy (suma countów w oknie energii)
- discharges : detekcja start/finish ramek discharge
- fit        : 3-parametrowy fit y(t)=A*exp(-(t-t_0)/tau)+C z t_0 zafiksowanym
- pipeline   : analyze_shot \u2014 sklejony przep\u0142yw, zwraca dict[channel -> DataFrame]
- export     : zapis Parquet
"""
from . import model, io, timetrace, discharges, fit, pipeline, export  # noqa: F401

__version__ = "0.2.0"
