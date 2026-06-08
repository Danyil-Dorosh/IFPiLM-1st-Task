"""Data classes — physical objects used by the library."""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
import numpy as np


# Bump this when the Discharge structure or field meaning changes,
# so cached objects can be checked for compatibility quickly.
DISCHARGE_SCHEMA_VERSION = 1


@dataclass
class EnergyChannelData:
    """Data for one energy channel for an entire shot."""
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


#TODO
DISTCHARGE_FRAME_DT_S_INITVAL=0.05
@dataclass
class Discharge:
    """Single experimental discharge — collection of channels + metadata."""
    discharge_id: str
    channels: dict[int, EnergyChannelData]
    frame_dt_s: float = DISTCHARGE_FRAME_DT_S_INITVAL
    #TODO: move float = 0.05 to config, or at least to a constant in pipeline.py
    """Duration of a single frame in seconds (typically 50 ms)."""
    meta: dict = field(default_factory=dict)
    # When this object was created (useful for cache provenance/debugging).
    created_at: datetime = field(default_factory=datetime.now)
    # Structure version of this object; compare against DISCHARGE_SCHEMA_VERSION
    # to detect caches built by an older/different code layout.
    schema_version: int = DISCHARGE_SCHEMA_VERSION


@dataclass
class TimeTrace:
    """Sum of counts in an energy window as a function of frame number."""
    frame_numbers: np.ndarray
    values: np.ndarray
    energy_window_eV: tuple[float, float]
    channel_id: int


@dataclass
class Injection:
    """Single injection — frame range and peak frame."""
    injection_no: int
    channel_id: int
    line_energy_eV: float
    start_frame: int
    finish_frame: int
    peak_frame: int


@dataclass
class FitResult:
    """Fit result for y(t) = A * exp(-(t - t_0) / tau) + C.

    All values are in units of **frames** (not seconds).
    Conversion to seconds is performed in `pipeline.py` using `frame_dt_s`.
    """
    A: float
    t_0: float
    tau: float
    C: float
    success: bool = False
    message: str = ""
    n_points: int = 0