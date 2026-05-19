"""Budowa przebiegów czasowych z widm (TimeTrace) — osobno dla każdego kanału.

y(t) = suma countów w oknie [E_line - half_width, E_line + half_width]
       dla każdej ramki t.

Każdy kanał obrabiany NIEZALEŻNIE. Nigdy nie mieszamy Events1 z Events2.
"""
from __future__ import annotations
import numpy as np

from .model import EnergyChannelData, TimeTrace


def integrate_energy_window(
    channel: EnergyChannelData,
    center_eV: float,
    half_width_eV: float = 60.0,
) -> TimeTrace:
    """Zbuduj TimeTrace z widm 1 kanału — zwykła suma w oknie energii.

    Dla każdej ramki sumujemy counts (Events) we wszystkich binach, których
    energia E spełnia:
        center_eV - half_width_eV  <=  E  <=  center_eV + half_width_eV

    Parameters
    ----------
    channel : EnergyChannelData
        Dane z **jednego** kanału energetycznego (osobno!).
    center_eV : float
        Środek okna energii, np. 6660 eV dla linii Fe XXV.
    half_width_eV : float, default 60
        Pół-szerokość okna ±half_width_eV. Domyślne ±60 eV łapie linię Fe XXV
        razem z poszerzeniem dopplerowskim i rozdzielczością detektora.

    Returns
    -------
    TimeTrace
        values[i] = liczba zdarzeń w oknie w ramce i (typ float).
    """
    if half_width_eV <= 0:
        raise ValueError("half_width_eV must be positive")

    e = channel.energy_eV
    window_lo = float(center_eV - half_width_eV)
    window_hi = float(center_eV + half_width_eV)

    mask = (e >= window_lo) & (e <= window_hi)
    if not mask.any():
        raise ValueError(
            f"Energy window [{window_lo}, {window_hi}] eV is empty "
            f"(no bins fall inside)."
        )

    # Suma countów po wybranych binach, dla każdej ramki osobno
    values = channel.spectra[:, mask].sum(axis=1).astype(float)  # (n_frames,)

    return TimeTrace(
        frame_numbers=channel.frame_numbers.copy(),
        values=values,
        energy_window_eV=(window_lo, window_hi),
        channel_id=channel.channel_id,
    )