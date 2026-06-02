"""Configuration objects for the pha_lib package."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class InjectionDetectionConfig:
    """Configuration for injection detection."""

    threshold_factor: float = 3.0
    """Noise units above background to consider the detection threshold.

    The same threshold is used both for detecting a peak (start) and for
    considering the signal returned to background (end).
    """

    min_jump: float = 20.0
    """Minimum absolute jump in events between frames."""

    min_quiet_frames: int = 2
    """Consecutive quiet frames required to consider an injection finished."""

    min_separation_frames: int = 3
    """Minimum frame separation between two injections (otherwise merge)."""

    max_frames_per_discharge: int = 17
    """Maximum length of one injection in frames."""


# Backward-compatible terminology alias.
DischargeDetectionConfig = InjectionDetectionConfig