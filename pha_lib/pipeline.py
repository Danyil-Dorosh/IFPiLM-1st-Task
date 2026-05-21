"""High-level pipeline: Discharge -> two separate DataFrames (one per channel).

EACH CHANNEL IS PROCESSED INDEPENDENTLY. Never sum Events1+Events2.

Output (task specification)
----------------------------
Per channel — one row per detected injection, columns:

    injection_no       — sequential number of the injection within the discharge
    discharge_E        — line energy [eV]
    start_frame        — first frame of the injection (first burst point)
    finish_frame       — last frame of the injection

    A_f, t_0_f, tau_f, C_f   — fit parameters in units of **frames**
    A,   t_0,   tau,   C     — fit parameters converted to **seconds**

Suffix `_f` = "for frames". No suffix = seconds.

Conversion:
    t_0 = t_0_f * frame_dt_s
    tau = tau_f * frame_dt_s
    A   = A_f   (amplitude — count units, copied)
    C   = C_f   (background — count units, copied)
"""
from __future__ import annotations
from typing import Iterable, Optional
import pandas as pd

from model import Discharge, FitResult
from timetrace import integrate_energy_window
from discharges import detect_injections, InjectionDetectionConfig
from fit import fit_injection


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
        # --- units: FRAMES ---
        "A_f":   fit.A,
        "t_0_f": fit.t_0,
        "tau_f": fit.tau,
        "C_f":   fit.C,
        # --- units: SECONDS ---
        # multiply t_0 and tau by frame_dt_s.
        # A and C are amplitudes (event counts) — not time-dependent, so copied.
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
    """Full pipeline for one channel — returns a DataFrame with fit results.

    Parameters
    ----------
    discharge : Discharge
        Loaded Discharge (from io.load_united_txt).
    channel_id : int
        1 or 2.
    line_energy_eV : float
        Center of the energy window (default Fe XXV @ 6660 eV).
    half_width_eV : float
        Half-width ±half_width_eV (default 60 eV).
    n_points : int
        Number of points to use for fitting, counting from start_frame+1.
    detection_config : DischargeDetectionConfig | None
        Injection detection parameters (None → defaults).
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
    """Run full analysis for the selected channels (separately).

    Returns
    -------
    dict[int, pd.DataFrame]
        {channel_id -> resulting DataFrame}. Channels are INDEPENDENT.
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

#Wired with initial shot-discharge-injection terminology confusion
analyze_shot = analyze_discharge