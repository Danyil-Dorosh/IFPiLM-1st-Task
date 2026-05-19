"""Klasy danych \u2014 fizyczne obiekty na kt\u00f3rych pracuje biblioteka."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional
import numpy as np


@dataclass
class EnergyChannelData:
    """Dane jednego kana\u0142u energetycznego dla ca\u0142ego shotu."""
    channel_id: int
    frame_numbers: np.ndarray   # shape (n_frames,)
    energy_eV: np.ndarray       # shape (n_bins,)
    spectra: np.ndarray         # shape (n_frames, n_bins)

    @property
    def n_frames(self) -> int:
        return self.spectra.shape[0]

    @property
    def n_bins(self) -> int:
        return self.spectra.shape[1]


@dataclass
class Shot:
    """Pe\u0142ny shot \u2014 kolekcja kana\u0142\u00f3w + metadane."""
    shot_id: str
    channels: dict[int, EnergyChannelData]
    frame_dt_s: float = 0.05
    """Czas trwania jednej ramki w sekundach (typowo 50 ms)."""
    meta: dict = field(default_factory=dict)


@dataclass
class TimeTrace:
    """Suma count\u00f3w w oknie energii w funkcji ramki."""
    frame_numbers: np.ndarray
    values: np.ndarray
    energy_window_eV: tuple[float, float]
    channel_id: int


@dataclass
class Discharge:
    """Pojedynczy discharge \u2014 zakres ramek + ramka peaku."""
    discharge_no: int
    channel_id: int
    line_energy_eV: float
    start_frame: int
    finish_frame: int
    peak_frame: int


@dataclass
class FitResult:
    """Wynik fitu y(t) = A * exp(-(t - t_0) / tau) + C.

    Wszystkie warto\u015bci w jednostkach **ramek** (nie sekund) \u2014
    konwersja na sekundy odbywa si\u0119 w pipeline.py przez frame_dt_s.
    """
    A: float
    t_0: float
    tau: float
    C: float
    success: bool = False
    message: str = ""
    n_points: int = 0
