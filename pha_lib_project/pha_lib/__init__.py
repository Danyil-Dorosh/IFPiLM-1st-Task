"""pha_lib — biblioteka do analizy danych z systemu PHA na W7-X.

High-level usage
----------------
>>> from pha_lib import io, pipeline, export
>>> shot = io.load_united_txt("unitedc_62_239.txt", shot_id="XP_test")
>>> df_ch1, df_ch2 = pipeline.analyze_shot(shot, line_energy_eV=6660.0)
>>> export.save_results_parquet(df_ch1, df_ch2, out_dir="output/")

Architectural layers (każdy moduł = jedno zadanie)
--------------------------------------------------
- model      : klasy danych (Shot, FrameSpectrum, EnergyChannelData, TimeTrace,
               Discharge, ExpDecayFit). To jest „kręgosłup" biblioteki.
- io         : czytanie wejścia (united .txt, pojedyncze test_<n>.txt, w przyszłości .pha).
- timetrace  : zamiana sekwencji widm w przebieg czasowy (suma countów w oknie energii).
- discharges : detekcja początku i końca discharges na bazie TimeTrace.
- fit        : dopasowanie y(t) = A*exp(-(t-t0)/tau) + C z różnymi strategiami startu.
- pipeline   : wysokopoziomowy „przepis", który łączy wszystko w 2 DataFrame'y.
- export     : zapis wyników (Parquet, opcjonalnie CSV).
- plotting   : wykresy diagnostyczne (trace + fit).
"""

from . import model, io, timetrace, discharges, fit, pipeline, export, plotting  # noqa: F401

__version__ = "0.1.0"
