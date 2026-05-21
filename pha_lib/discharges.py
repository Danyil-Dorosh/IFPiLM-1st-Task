"""Injection detection in a time trace.

In our data an injection = sudden jump of photon counts in the chosen
energy window (impurity injection), followed by an exponential decay
back to background.

Algorithm (simple and readable — can be replaced later)
------------------------------------------------------
1. Estimate background level as the median of the trace — robust to spikes.
2. Estimate noise scale using MAD (median absolute deviation) or similar.
3. An injection starts at the first frame where the signal exceeds
    `peak_threshold_factor * scale` above background AND is at least
    `min_jump` larger than the previous frame.
4. An injection ends when the signal returns to <= `end_threshold_factor*scale`
    above background and stays there for at least `min_quiet_frames` frames.
5. Merge or discard injections that are too short or too close.

Parameters are tunable — defaults chosen for our test dataset.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import List
import numpy as np

from .model import TimeTrace, Injection


@dataclass
class InjectionDetectionConfig:
    """Configuration for injection detection."""
    peak_threshold_factor: float = 3.0
    """How many noise units above background to consider a peak.
    Default 3 sigma — a common detection threshold in physics."""

    end_threshold_factor: float = 1.5
    """Threshold to consider the signal returned to background (end)."""

    min_jump: float = 20.0
    """Minimum absolute jump in events between frames — avoids weak fluctuations."""

    min_quiet_frames: int = 2
    """Number of consecutive quiet frames to consider the injection finished."""

    min_separation_frames: int = 3
    """Minimum separation in frames between two injections (otherwise merge)."""

    max_frames_per_discharge: int = 25
    """Maximum length of an injection (protects against non-ending traces)."""


def _robust_background_and_scale(values: np.ndarray) -> tuple[float, float]:
    """Median and MAD — robust against peaks."""
    bg = float(np.median(values))
    mad = float(np.median(np.abs(values - bg)))
    # 1.4826 * MAD ≈ sigma for a normal distribution
    scale = max(1.4826 * mad, 1.0)
    return bg, scale


def detect_injections(
    trace: TimeTrace,
    line_energy_eV: float,
    config: InjectionDetectionConfig | None = None,
) -> List[Injection]:
    """Find injections in a time trace.

    Returns
    -------
    list of Injection
        Sorted by `start_frame`. May return an empty list.
    """
    cfg = config or InjectionDetectionConfig()
    v = trace.values
    fn = trace.frame_numbers
    if len(v) < 3:
        return []

    bg, scale = _robust_background_and_scale(v)
    high_thr = bg + cfg.peak_threshold_factor * scale
    low_thr = bg + cfg.end_threshold_factor * scale

    above = v >= high_thr

    # Detect start candidates: an above-threshold frame with a sufficiently
    # large jump relative to the previous frame and not too close to the
    # previous injection.
    injections: list[Injection] = []
    i = 0
    n = len(v)
    last_finish_idx = -10**9
    injection_no = 0

    while i < n:
        if not above[i]:
            i += 1
            continue
        # potential start
        prev = v[i - 1] if i > 0 else bg
        if (v[i] - prev) < cfg.min_jump and i > 0:
            i += 1
            continue
        if (i - last_finish_idx) < cfg.min_separation_frames:
            i += 1
            continue

        start_idx = i
        # find finish: first place where signal drops below low_thr and
        # stays below for min_quiet_frames frames
        j = i
        quiet_count = 0
        while j < n:
            if v[j] < low_thr:
                quiet_count += 1
                if quiet_count >= cfg.min_quiet_frames:
                    break
            else:
                quiet_count = 0
            j += 1
            if (j - start_idx) >= cfg.max_frames_per_discharge:
                break
        finish_idx = min(j, n - 1)

        # peak inside [start, finish]
        peak_idx = start_idx + int(np.argmax(v[start_idx:finish_idx + 1]))

        injection_no += 1
        injections.append(Injection(
            injection_no=injection_no,
            channel_id=trace.channel_id,
            line_energy_eV=line_energy_eV,
            start_frame=int(fn[start_idx]),
            finish_frame=int(fn[finish_idx]),
            peak_frame=int(fn[peak_idx]),
        ))
        last_finish_idx = finish_idx
        i = finish_idx + 1

    return injections


detect_discharges = detect_injections
DischargeDetectionConfig = InjectionDetectionConfig
