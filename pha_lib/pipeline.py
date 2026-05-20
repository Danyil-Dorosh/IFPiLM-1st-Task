"""Wysokopoziomowy pipeline: Discharge -> 2 osobne DataFrame'y (po jednym na kanał).

KAŻDY KANAŁ LECZONY OSOBNO. Nigdy nie sumujemy Events1+Events2.

Output (zgodnie ze specyfikacją zadania)
----------------------------------------
Per kanał — jeden wiersz na discharge, kolumny:

    injection_no       — numer kolejny w discharge
    discharge_E        — energia linii [eV]
    start_frame        — pierwsza ramka discharge (= pierwszy punkt burstu)
    finish_frame       — ostatnia ramka discharge

    A_f, t_0_f, tau_f, C_f   — współczynniki w jednostkach **ramek**
    A,   t_0,   tau,   C     — współczynniki w jednostkach **sekund**

Suffix `_f` = "for frames". Bez suffixu = sekundy.

Konwersja:
    t_0 = t_0_f * frame_dt_s
    tau = tau_f * frame_dt_s
    A   = A_f   (amplituda — bez wymiaru czasu, kopia)
    C   = C_f   (tło — bez wymiaru czasu, kopia)
"""
from __future__ import annotations
from typing import Iterable, Optional
import pandas as pd

from .model import Discharge, FitResult
from .timetrace import integrate_energy_window
from .discharges import detect_injections, InjectionDetectionConfig
from .fit import fit_injection


RESULT_COLUMNS = [
    "injection_no", "discharge_E",
    "start_frame", "finish_frame",
    "A_f", "t_0_f", "tau_f", "C_f",
    "A",   "t_0",   "tau",   "C",
    "fit_success", "fit_message",
]


def _row(injection_no, line_E, start, finish, fit: FitResult, frame_dt_s: float) -> dict:
    return {
        "injection_no": injection_no,
        "discharge_E":  line_E,
        "start_frame":  start,
        "finish_frame": finish,
        # --- jednostki: RAMKI ---
        "A_f":   fit.A,
        "t_0_f": fit.t_0,
        "tau_f": fit.tau,
        "C_f":   fit.C,
        # --- jednostki: SEKUNDY ---
        # t_0 i tau mnożymy przez frame_dt_s.
        # A i C to amplitudy (liczba zdarzeń) — bez wymiaru czasu, więc kopia.
        "A":   fit.A,
        "t_0": fit.t_0 * frame_dt_s,
        "tau": fit.tau * frame_dt_s,
        "C":   fit.C,
        "fit_success": fit.success,
        "fit_message": fit.message,
    }


def analyze_channel(
    discharge: Discharge,
    channel_id: int,
    line_energy_eV: float = 6660.0,
    half_width_eV: float = 60.0,
    n_points: int = 3,
    detection_config: Optional[InjectionDetectionConfig] = None,
) -> pd.DataFrame:
    """Pełny pipeline dla 1 kanału — zwraca DataFrame z wynikami fitu.

    Parameters
    ----------
    discharge : Discharge
        Załadowany discharge (z io.load_united_txt).
    channel_id : int
        1 lub 2.
    line_energy_eV : float
        Środek okna energii (domyślnie Fe XXV @ 6660 eV).
    half_width_eV : float
        Połowa szerokości okna ±half_width_eV (domyślnie 60 eV).
    n_points : int
        Ile punktów wziąć do fitu, licząc od start_frame+1 (drugi punkt burstu).
    detection_config : DischargeDetectionConfig | None
        Parametry wykrywania discharges (None → defaults).
    """
    if channel_id not in discharge.channels:
        raise KeyError(f"Channel {channel_id} not in discharge {discharge.discharge_id}")

    channel = discharge.channels[channel_id]
    trace = integrate_energy_window(channel, line_energy_eV, half_width_eV)
    injections = detect_injections(trace, line_energy_eV, detection_config)

    rows = []
    for d in injections:
        fit = fit_injection(trace, d, n_points=n_points)
        rows.append(_row(
            injection_no=d.injection_no,
            line_E=line_energy_eV,
            start=d.start_frame,
            finish=d.finish_frame,
            fit=fit,
            frame_dt_s=discharge.frame_dt_s,
        ))

    if not rows:
        return pd.DataFrame(columns=RESULT_COLUMNS)
    return pd.DataFrame(rows, columns=RESULT_COLUMNS)


def analyze_discharge(
    discharge: Discharge,
    line_energy_eV: float = 6660.0,
    half_width_eV: float = 60.0,
    n_points: int = 3,
    channels: Iterable[int] = (1, 2),
    detection_config: Optional[InjectionDetectionConfig] = None,
) -> dict[int, pd.DataFrame]:
    """Wykonaj pełną analizę dla wybranych kanałów (osobno).

    Returns
    -------
    dict[int, pd.DataFrame]
        {channel_id -> wynikowy DataFrame}. Kanały SĄ NIEZALEŻNE.
    """
    return {
        ch: analyze_channel(
            discharge, channel_id=ch,
            line_energy_eV=line_energy_eV,
            half_width_eV=half_width_eV,
            n_points=n_points,
            detection_config=detection_config,
        )
        for ch in channels
    }


analyze_shot = analyze_discharge