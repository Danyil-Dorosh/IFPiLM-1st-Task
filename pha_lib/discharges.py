"""Detekcja injekcji w przebiegu czasowym.

Injekcja w naszych danych = nagły skok liczby fotonów w wyznaczonym oknie eV
(injekcja zanieczyszczenia), po czym sygnał wykładniczo zanika do tła.

Algorytm (prosty i czytelny — można potem podmienić)
-----------------------------------------------------
1. Estymujemy poziom tła (background) jako medianę całego przebiegu —
   to odporne na pojedyncze peaki (median nie ucieknie z powodu kilku
   wystrzałów).
2. Estymujemy „skalę szumu" jako MAD (median absolute deviation) lub
   po prostu odchylenie standardowe okolic mediany.
3. Injekcja zaczyna się w pierwszej ramce, gdzie sygnał skacze o
   `peak_threshold_factor * scale` powyżej tła ORAZ jest większy o co
   najmniej `min_jump` wartości od ramki poprzedniej.
4. Injekcja kończy się, gdy sygnał wraca do <= `end_threshold_factor*scale`
   powyżej tła i pozostaje tam co najmniej `min_quiet_frames` ramek.
5. Łączymy / odrzucamy zbyt krótkie / zbyt blisko siebie injekcje.

Parametry są nastrajalne — domyślne dobrane dla naszego zbioru testowego.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import List
import numpy as np

from .model import TimeTrace, Injection


@dataclass
class InjectionDetectionConfig:
    """Konfiguracja detekcji injekcji."""
    peak_threshold_factor: float = 3.0
    """Ile razy szumu ponad tło, aby uznać że to peak (start discharge).
    Domyślnie 3 sigma — typowy próg detekcji w fizyce."""

    end_threshold_factor: float = 1.5
    """Próg powrotu do tła (koniec discharge)."""

    min_jump: float = 20.0
    """Minimalny absolutny skok wartości (w jednostkach events) między
    ramką poprzednią a nową — chroni przed słabymi fluktuacjami."""

    min_quiet_frames: int = 2
    """Po ilu spokojnych ramkach uznajemy że discharge się skończył."""

    min_separation_frames: int = 3
    """Minimalna przerwa między dwoma discharges (jeśli mniej — łączymy)."""

    max_frames_per_discharge: int = 25
    """Maksymalna długość — chroni przed „discharge'em który nigdy się
    nie kończy" (zwykle to tło wzrasta)."""


def _robust_background_and_scale(values: np.ndarray) -> tuple[float, float]:
    """Mediana i MAD — robustne wobec peaków."""
    bg = float(np.median(values))
    mad = float(np.median(np.abs(values - bg)))
    # 1.4826 * MAD ≈ sigma dla rozkładu normalnego
    scale = max(1.4826 * mad, 1.0)
    return bg, scale


def detect_injections(
    trace: TimeTrace,
    line_energy_eV: float,
    config: InjectionDetectionConfig | None = None,
) -> List[Injection]:
    """Znajdź injekcje w przebiegu czasowym.

    Returns
    -------
    list of Injection
        Posortowane po `start_frame`. Lista może być pusta.
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

    # Wykryj kandydaty na start: ramka above z odpowiednio dużym skokiem względem
    # poprzedniej i niezbyt blisko poprzedniej injekcji.
    injections: list[Injection] = []
    i = 0
    n = len(v)
    last_finish_idx = -10**9
    injection_no = 0

    while i < n:
        if not above[i]:
            i += 1
            continue
        # potencjalny start
        prev = v[i - 1] if i > 0 else bg
        if (v[i] - prev) < cfg.min_jump and i > 0:
            i += 1
            continue
        if (i - last_finish_idx) < cfg.min_separation_frames:
            i += 1
            continue

        start_idx = i
        # znajdź koniec: pierwsze miejsce gdzie sygnał spadł poniżej low_thr
        # i pozostał taki min_quiet_frames ramek
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
