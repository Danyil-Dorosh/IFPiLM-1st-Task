"""Budowa przebiegów czasowych z widm (TimeTrace).

Główna operacja: dla każdej ramki sumujemy counts w wybranym oknie energii
[E_center - half_width, E_center + half_width]. Pozwala to przejść z reprezentacji
frame×bin do prostej krzywej (frame -> N events) — czyli takiej formy, na której
działa fitowanie eksponensa.

Dlaczego okno, a nie pojedynczy bin?
------------------------------------
- Linia emisyjna ma naturalną szerokość (Doppler, instrumental broadening,
  detector resolution).
- Center przesuwa się trochę na osi energii (kalibracja, drift).
Stąd używamy okna ~50–100 eV wokół centrum linii (parametr `half_width_eV`).
"""
from __future__ import annotations
import numpy as np

from .model import EnergyChannelData, TimeTrace


def integrate_energy_window(
    channel: EnergyChannelData,
    center_eV: float,
    half_width_eV: float = 50.0,
    label: str = "",
) -> TimeTrace:
    """Zsumuj counts w oknie [center - half, center + half] dla każdej ramki.

    Parameters
    ----------
    channel : EnergyChannelData
        Dane z 1 kanału (n_frames × n_bins).
    center_eV : float
        Środek okna energii (np. 6660 eV dla badanej linii).
    half_width_eV : float, default 50
        Pół-szerokość okna w eV. Wartość 50 eV daje zwykle dobry kompromis
        między łapaniem całej linii a niewchodzeniem w sąsiednie linie/tło.
    label : str
        Etykieta opisowa, np. "Fe XXV @ 6660 eV".

    Returns
    -------
    TimeTrace
        Suma countów w oknie dla każdej ramki.
    """
    if half_width_eV <= 0:
        raise ValueError("half_width_eV must be positive")

    e = channel.energy_eV
    mask = (e >= center_eV - half_width_eV) & (e <= center_eV + half_width_eV)
    if not mask.any():
        raise ValueError(
            f"Energy window [{center_eV - half_width_eV}, "
            f"{center_eV + half_width_eV}] eV is empty — check the energy axis."
        )

    # spectra shape (n_frames, n_bins) — sumujemy po ostatnim wymiarze
    values = channel.spectra[:, mask].sum(axis=1)

    return TimeTrace(
        frame_numbers=channel.frame_numbers.copy(),
        values=values.astype(float),
        energy_window_eV=(center_eV - half_width_eV, center_eV + half_width_eV),
        channel_id=channel.channel_id,
        label=label or f"window {center_eV} +/- {half_width_eV} eV",
    )
