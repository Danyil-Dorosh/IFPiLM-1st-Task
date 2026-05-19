"""Klasy danych (dataclasses) — fizyczne obiekty na których pracuje biblioteka.

Filozofia
---------
- Surowe dane liczbowe trzymamy jako numpy.ndarray (szybkie, niskopoziomowe).
- Metadane i wyniki trzymamy jako dataclass / pandas.DataFrame.
- Nie mieszamy parsera plików z analizą — każdy obiekt jest „głupi i czysty".
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional
import numpy as np


# ---------- pojedyncza ramka, jeden kanał -----------------------------------

@dataclass
class FrameSpectrum:
    """Widmo z 1 ramki, 1 kanału energetycznego.

    Attributes
    ----------
    frame_no : int
        Numer ramki w shocie.
    channel_id : int
        Numer kanału energetycznego (1, 2, 3...).
    energy_eV : np.ndarray
        Oś energii (eV), shape (n_bins,).
    counts : np.ndarray
        Liczba zdarzeń (photonów) w każdym binie energii, shape (n_bins,).
    """
    frame_no: int
    channel_id: int
    energy_eV: np.ndarray
    counts: np.ndarray


# ---------- pojedynczy kanał, wszystkie ramki shotu --------------------------

@dataclass
class EnergyChannelData:
    """Dane jednego kanału energetycznego dla całego shotu.

    Notes
    -----
    Tablica `spectra` ma shape (n_frames, n_bins). Energia jest wspólna dla
    wszystkich ramek (oś detektora się nie zmienia w trakcie shotu), więc
    `energy_eV` jest 1D.
    """
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


# ---------- cały shot --------------------------------------------------------

@dataclass
class Shot:
    """Pełny shot — kolekcja kanałów + metadane.

    Notes
    -----
    `frame_dt_s` to czas trwania jednej ramki (typowo ~50 ms = 0.05 s).
    Oś czasu danej ramki to `frame_no * frame_dt_s` (jeśli numeracja zaczyna
    się od 0) — w naszym przypadku zwykle używamy po prostu numerów ramek.
    """
    shot_id: str
    channels: dict[int, EnergyChannelData]
    frame_dt_s: float = 0.05
    meta: dict = field(default_factory=dict)


# ---------- przebieg czasowy -------------------------------------------------

@dataclass
class TimeTrace:
    """Suma countów w oknie energii w funkcji ramki/czasu.

    Used for: detekcja discharges + dopasowanie y(t)=A*exp(-(t-t0)/tau)+C.
    """
    frame_numbers: np.ndarray   # shape (n_frames,)
    values: np.ndarray          # shape (n_frames,)
    energy_window_eV: tuple[float, float]
    channel_id: int
    label: str = ""


# ---------- discharge --------------------------------------------------------

@dataclass
class Discharge:
    """Pojedynczy discharge wewnątrz shotu — zakres ramek i kanał.

    `peak_frame` to ramka z najwyższym sygnałem (zwykle używana jako t_0
    w trybie „skip first frame").
    """
    discharge_no: int
    channel_id: int
    line_energy_eV: float
    start_frame: int
    finish_frame: int
    peak_frame: int


# ---------- wynik dopasowania ------------------------------------------------

@dataclass
class ExpDecayFit:
    """Wynik dopasowania y(t) = A * exp(-(t - t_0) / tau) + C.

    Attributes
    ----------
    A, t_0, tau, C : float
        Parametry dopasowania.
    A_err, t_0_err, tau_err, C_err : float
        Niepewności (sqrt(diag(cov))). NaN jeśli niedostępne.
    n_points : int
        Liczba punktów użytych do dopasowania.
    success : bool
        Czy curve_fit się udał.
    message : str
        Wiadomość diagnostyczna (np. "ok", "too few points", "fit failed: ...").
    """
    A: float
    t_0: float
    tau: float
    C: float
    A_err: float = float("nan")
    t_0_err: float = float("nan")
    tau_err: float = float("nan")
    C_err: float = float("nan")
    n_points: int = 0
    success: bool = False
    message: str = ""

    @classmethod
    def failed(cls, message: str) -> "ExpDecayFit":
        nan = float("nan")
        return cls(A=nan, t_0=nan, tau=nan, C=nan, success=False, message=message)
