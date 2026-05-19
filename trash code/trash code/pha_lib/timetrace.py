"""Budowa przebiegów czasowych z widm (TimeTrace) — osobno dla każdego kanału.

y(t) = (suma countów w oknie linii) − (continuum_per_bin) × (n_binów_linii)

Dlaczego odejmujemy continuum?
------------------------------
W oknie 6660 ± 70 eV nie ma tylko fotony z linii Fe XXV — jest też
bremsstrahlung continuum, którego strumień też rośnie podczas discharge
(plazma jest gorętsza). Bez odejmowania continuum nasze y(t) zawiera oba
składniki, a tylko linia ma czysty exp-decay charakter. Pasma (sidebands)
lewo i prawo od linii dają nam estymatę continuum-per-bin **w tej samej
ramce**, którą mnożymy przez liczbę binów linii i odejmujemy.

Channels are processed independently — we never mix Events1 + Events2.
"""
from __future__ import annotations
from typing import Optional
import numpy as np

from .model import EnergyChannelData, TimeTrace


def integrate_energy_window(
    channel: EnergyChannelData,
    center_eV: float,
    half_width_eV: float = 70.0,
    continuum_left_eV: Optional[tuple[float, float]] = None,
    continuum_right_eV: Optional[tuple[float, float]] = None,
    subtract_continuum: bool = True,
) -> TimeTrace:
    """Zbuduj TimeTrace z widm 1 kanału, z opcjonalnym odejmowaniem continuum.

    Parameters
    ----------
    channel : EnergyChannelData
        Dane z **jednego** kanału energetycznego.
    center_eV : float
        Środek linii, np. 6660 eV.
    half_width_eV : float, default 70
        Pół-szerokość okna linii. Linia Fe XXV ma dość szeroką obwiednię
        (Doppler + detector resolution), w naszych danych ±70 eV łapie cały
        bump bez znaczącego "przeciekania" continuum.
    continuum_left_eV : (lo, hi), optional
        Zakres lewego pasma do estymacji continuum. Domyślnie:
        [center - 3*half, center - half - 10] eV.
    continuum_right_eV : (lo, hi), optional
        Zakres prawego pasma. Domyślnie:
        [center + half + 10, center + 3*half] eV.
    subtract_continuum : bool, default True
        Jeśli False, zwracamy zwykłą sumę w oknie linii (bez odejmowania).
        Jeśli True — odejmujemy continuum estymowany z sidebandzów.

    Returns
    -------
    TimeTrace
        values = events przypisane do **samej linii** (po odjęciu continuum).
        Mogą być lekko ujemne dla cichych ramek — to fluktuacje statystyczne,
        nie błąd.
    """
    if half_width_eV <= 0:
        raise ValueError("half_width_eV must be positive")

    e = channel.energy_eV
    line_mask = (e >= center_eV - half_width_eV) & (e <= center_eV + half_width_eV)
    if not line_mask.any():
        raise ValueError(
            f"Line window [{center_eV - half_width_eV}, "
            f"{center_eV + half_width_eV}] eV is empty."
        )

    raw_line_sum = channel.spectra[:, line_mask].sum(axis=1)  # (n_frames,)
    window_lo = float(center_eV - half_width_eV)
    window_hi = float(center_eV + half_width_eV)

    if not subtract_continuum:
        return TimeTrace(
            frame_numbers=channel.frame_numbers.copy(),
            values=raw_line_sum.astype(float),
            energy_window_eV=(window_lo, window_hi),
            channel_id=channel.channel_id,
        )

    # Domyślne sidebandy: po obu stronach okna linii
    if continuum_left_eV is None:
        continuum_left_eV = (center_eV - 3 * half_width_eV,
                             center_eV - half_width_eV - 10.0)
    if continuum_right_eV is None:
        continuum_right_eV = (center_eV + half_width_eV + 10.0,
                              center_eV + 3 * half_width_eV)

    left_mask = (e >= continuum_left_eV[0]) & (e <= continuum_left_eV[1])
    right_mask = (e >= continuum_right_eV[0]) & (e <= continuum_right_eV[1])
    side_mask = left_mask | right_mask

    if not side_mask.any():
        raise ValueError(
            "Continuum sideband mask is empty — check continuum_left_eV and "
            "continuum_right_eV against the energy axis range."
        )

    n_line_bins = int(line_mask.sum())
    contm_per_bin = channel.spectra[:, side_mask].mean(axis=1)  # (n_frames,)
    contm_in_line_window = contm_per_bin * n_line_bins
    values = (raw_line_sum - contm_in_line_window).astype(float)

    return TimeTrace(
        frame_numbers=channel.frame_numbers.copy(),
        values=values,
        energy_window_eV=(window_lo, window_hi),
        channel_id=channel.channel_id,
    )
