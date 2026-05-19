"""Detekcja discharges w TimeTrace.

Discharge = nag\u0142y skok count\u00f3w w oknie 6660 eV (injekcja zanieczyszczenia),
po kt\u00f3rym sygna\u0142 zanika eksponencjalnie do t\u0142a.

Algorytm
--------
1. T\u0142o = mediana ca\u0142ego trace (odporne na peaki).
2. Skala szumu = 1.4826 * MAD (przybli\u017cenie sigmy dla rozk\u0142adu normalnego).
3. Start: pierwsza ramka, gdzie sygna\u0142 > bg + peak_threshold_factor * scale
   ORAZ skok od poprzedniej ramki >= min_jump.
4. Finish: gdy sygna\u0142 wraca poni\u017cej bg + end_threshold_factor * scale
   przez min_quiet_frames ramek.
5. Filtrowanie: minimalna separacja, max d\u0142ugo\u015b\u0107.

Wszystkie progi konfigurowalne przez DischargeDetectionConfig.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import List
import numpy as np

from .model import TimeTrace, Discharge


@dataclass
class DischargeDetectionConfig:
    peak_threshold_factor: float = 3.0
    end_threshold_factor: float = 1.5
    min_jump: float = 20.0
    min_quiet_frames: int = 2
    min_separation_frames: int = 3
    max_frames_per_discharge: int = 25


def _robust_background_and_scale(values: np.ndarray) -> tuple[float, float]:
    bg = float(np.median(values))
    mad = float(np.median(np.abs(values - bg)))
    scale = max(1.4826 * mad, 1.0)
    return bg, scale


def detect_discharges(
    trace: TimeTrace,
    line_energy_eV: float,
    config: DischargeDetectionConfig | None = None,
) -> List[Discharge]:
    """Znajd\u017a discharges w przebiegu czasowym."""
    cfg = config or DischargeDetectionConfig()
    v = trace.values
    fn = trace.frame_numbers
    if len(v) < 3:
        return []

    bg, scale = _robust_background_and_scale(v)
    high_thr = bg + cfg.peak_threshold_factor * scale
    low_thr = bg + cfg.end_threshold_factor * scale
    above = v >= high_thr

    discharges: list[Discharge] = []
    i = 0
    n = len(v)
    last_finish_idx = -10**9
    discharge_no = 0

    while i < n:
        if not above[i]:
            i += 1
            continue
        prev = v[i - 1] if i > 0 else bg
        if (v[i] - prev) < cfg.min_jump and i > 0:
            i += 1
            continue
        if (i - last_finish_idx) < cfg.min_separation_frames:
            i += 1
            continue

        start_idx = i
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

        peak_idx = start_idx + int(np.argmax(v[start_idx:finish_idx + 1]))

        discharge_no += 1
        discharges.append(Discharge(
            discharge_no=discharge_no,
            channel_id=trace.channel_id,
            line_energy_eV=line_energy_eV,
            start_frame=int(fn[start_idx]),
            finish_frame=int(fn[finish_idx]),
            peak_frame=int(fn[peak_idx]),
        ))
        last_finish_idx = finish_idx
        i = finish_idx + 1

    return discharges
