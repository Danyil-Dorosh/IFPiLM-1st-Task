"""Wysokopoziomowy pipeline: Shot -> 2 result DataFrames (per kanał).

Ten moduł skleja wszystkie etapy w jeden „przepis":

    integrate_energy_window  ->  detect_discharges  ->  fit_discharge_two_strategies
                                                   ->  pandas.DataFrame

Output (zgodnie ze specyfikacją zadania)
----------------------------------------
2 DataFrame'y (dla kanału 1 i 2). Każdy wiersz = 1 discharge.

Kolumny:
    discharge_no       — numer kolejny discharge w shocie
    discharge_E        — energia linii [eV] (np. 6660.0)
    start_frame        — pierwsza ramka discharge
    finish_frame       — ostatnia ramka discharge (gdy wraca do tła)
    A_f, t_0_f, tau_f, C_f   — fit od PIERWSZEJ ramki (strategia "first")
    A,   t_0,   tau,   C     — fit od DRUGIEJ ramki   (strategia "second")

Uwaga: zgodnie z opisem zadania, w wyjściu były dwie kolumny "C" — tutaj
rozróżniam je jako `C_f` (od fit-from-first) i `C` (od fit-from-second),
żeby DataFrame miał unikalne nazwy kolumn.
"""
from __future__ import annotations
from typing import Iterable, Optional
import pandas as pd

from .model import Shot, ExpDecayFit
from .timetrace import integrate_energy_window
from .discharges import detect_discharges, DischargeDetectionConfig
from .fit import fit_discharge_two_strategies


RESULT_COLUMNS = [
    "discharge_no", "discharge_E",
    "start_frame", "finish_frame",
    "A_f", "t_0_f", "tau_f", "C_f",
    "A", "t_0", "tau", "C",
    # bonus diagnostics — przydatne do oceny jakości fitu
    "fit_first_success", "fit_first_message", "fit_first_n",
    "fit_second_success", "fit_second_message", "fit_second_n",
    "A_f_err", "tau_f_err", "A_err", "tau_err",
]


def _row_for_discharge(
    discharge_no, line_energy_eV, start_frame, finish_frame,
    fit_first: ExpDecayFit, fit_second: ExpDecayFit,
) -> dict:
    return {
        "discharge_no": discharge_no,
        "discharge_E": line_energy_eV,
        "start_frame": start_frame,
        "finish_frame": finish_frame,
        # strategia "first"
        "A_f":   fit_first.A,
        "t_0_f": fit_first.t_0,
        "tau_f": fit_first.tau,
        "C_f":   fit_first.C,
        # strategia "second"
        "A":   fit_second.A,
        "t_0": fit_second.t_0,
        "tau": fit_second.tau,
        "C":   fit_second.C,
        # diagnostic
        "fit_first_success":  fit_first.success,
        "fit_first_message":  fit_first.message,
        "fit_first_n":        fit_first.n_points,
        "fit_second_success": fit_second.success,
        "fit_second_message": fit_second.message,
        "fit_second_n":       fit_second.n_points,
        "A_f_err":   fit_first.A_err,
        "tau_f_err": fit_first.tau_err,
        "A_err":     fit_second.A_err,
        "tau_err":   fit_second.tau_err,
    }


def analyze_channel(
    shot: Shot,
    channel_id: int,
    line_energy_eV: float = 6660.0,
    half_width_eV: float = 50.0,
    n_points: int = 3,
    detection_config: Optional[DischargeDetectionConfig] = None,
) -> pd.DataFrame:
    """Pełny pipeline dla 1 kanału — zwraca DataFrame z wynikami fitu."""
    if channel_id not in shot.channels:
        raise KeyError(f"Channel {channel_id} not in shot {shot.shot_id}")

    channel = shot.channels[channel_id]
    trace = integrate_energy_window(
        channel, center_eV=line_energy_eV, half_width_eV=half_width_eV,
        label=f"line {line_energy_eV} eV (ch {channel_id})",
    )
    discharges = detect_discharges(trace, line_energy_eV, config=detection_config)

    rows = []
    for d in discharges:
        fit_first, fit_second = fit_discharge_two_strategies(
            trace, d, n_points=n_points,
        )
        rows.append(_row_for_discharge(
            discharge_no=d.discharge_no,
            line_energy_eV=line_energy_eV,
            start_frame=d.start_frame,
            finish_frame=d.finish_frame,
            fit_first=fit_first,
            fit_second=fit_second,
        ))

    if not rows:
        return pd.DataFrame(columns=RESULT_COLUMNS)
    return pd.DataFrame(rows, columns=RESULT_COLUMNS)


def analyze_shot(
    shot: Shot,
    line_energy_eV: float = 6660.0,
    half_width_eV: float = 50.0,
    n_points: int = 3,
    channels: Iterable[int] = (1, 2),
    detection_config: Optional[DischargeDetectionConfig] = None,
) -> dict[int, pd.DataFrame]:
    """Wykonaj pełną analizę dla wybranych kanałów.

    Returns
    -------
    dict[int, pd.DataFrame]
        Słownik {channel_id -> wynikowy DataFrame}.
    """
    out: dict[int, pd.DataFrame] = {}
    for ch in channels:
        out[ch] = analyze_channel(
            shot, channel_id=ch,
            line_energy_eV=line_energy_eV,
            half_width_eV=half_width_eV,
            n_points=n_points,
            detection_config=detection_config,
        )
    return out
