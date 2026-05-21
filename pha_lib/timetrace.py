"""Construct time traces from spectra (TimeTrace) — one channel at a time.

y(t) = sum of counts in window [E_line - half_width, E_line + half_width]
    for each frame t.

Each channel is processed INDEPENDENTLY. Never mix Events1 with Events2.
"""
from __future__ import annotations
import numpy as np

from .model import EnergyChannelData, TimeTrace


def integrate_energy_window(
    channel: EnergyChannelData,
    center_eV: float,
    half_width_eV: float = 60.0,
) -> TimeTrace:
    """Build a TimeTrace from one channel's spectra — simple sum in an energy window.

    For each frame we sum counts (Events) in all bins whose energy E satisfies:
        center_eV - half_width_eV  <=  E  <=  center_eV + half_width_eV

    Parameters
    ----------
    channel : EnergyChannelData
        Data from a single energy channel (processed separately).
    center_eV : float
        Center of the energy window, e.g. 6660 eV for the Fe XXV line.
    half_width_eV : float, default 60
        Half-width ±half_width_eV. Default ±60 eV captures the Fe XXV line
        including Doppler broadening and detector resolution.

    Returns
    -------
    TimeTrace
        values[i] = number of events in the window at frame i (float).
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

    # Sum counts across selected bins for each frame separately
    values = channel.spectra[:, mask].sum(axis=1).astype(float)  # (n_frames,)

    return TimeTrace(
        frame_numbers=channel.frame_numbers.copy(),
        values=values,
        energy_window_eV=(window_lo, window_hi),
        channel_id=channel.channel_id,
    )