"""Wykresy diagnostyczne — pomagają zobaczyć, czy fit ma sens fizyczny.

W fizyce wykres to nie ozdoba, tylko narzędzie kontroli jakości.
Minimum:
- przebieg czasowy (TimeTrace) z zaznaczonymi discharges,
- nakładka modelu fitu na punkty użyte do dopasowania.
"""
from __future__ import annotations
from typing import Iterable, Optional
import numpy as np
import matplotlib.pyplot as plt

from .model import TimeTrace, Injection, FitResult
from .fit import exp_decay_model


def plot_timetrace_with_injections(
    trace: TimeTrace,
    injections: Iterable[Injection] = (),
    ax: Optional[plt.Axes] = None,
    title: Optional[str] = None,
):
    """Narysuj TimeTrace + zaznacz zakresy injekcji (start..finish)."""
    if ax is None:
        fig, ax = plt.subplots(figsize=(11, 4))
    ax.plot(trace.frame_numbers, trace.values, "-o", ms=3,
            color="tab:blue", label="events in window")
    for d in injections:
        ax.axvspan(d.start_frame - 0.5, d.finish_frame + 0.5,
                   alpha=0.15, color="tab:orange")
        ax.axvline(d.start_frame, color="tab:orange", lw=1)
        ax.text(d.start_frame, ax.get_ylim()[1] * 0.95,
                f"#{d.injection_no}", color="tab:orange", fontsize=9)
    ax.set_xlabel("frame")
    ax.set_ylabel("events (sum in energy window)")
    lo, hi = trace.energy_window_eV
    ax.set_title(title or f"Channel {trace.channel_id}: "
                          f"window [{lo:.0f}, {hi:.0f}] eV")
    ax.grid(alpha=0.3)
    ax.legend(loc="upper right")
    return ax


def plot_injection_fit(
    trace: TimeTrace,
    discharge: Injection,
    fit: FitResult,
    n_points: int = 3,
    pad: int = 4,
    ax: Optional[plt.Axes] = None,
):
    """Narysuj punkty injekcji + krzywą dopasowanego modelu.

    Konwencja (zgodna z fit.py):
    - punkty użyte do fitu zaczynają się od start_frame + 1 (drugi punkt burstu),
      bierzemy n_points kolejnych ramek.
    - t_0 fitu = start_frame + 1 (zafiksowane).
    - C fitu  = mediana całego trace (zafiksowane).
    """
    if ax is None:
        fig, ax = plt.subplots(figsize=(7, 4.5))

    fn = trace.frame_numbers
    v = trace.values
    s = discharge.start_frame
    e = discharge.finish_frame

    # context window (kilka ramek przed i po discharge)
    lo, hi = s - pad, e + pad
    mask = (fn >= lo) & (fn <= hi)
    ax.plot(fn[mask], v[mask], "o-", ms=4, color="0.4", alpha=0.7,
            label="data (context)")

    # punkty użyte do fitu: od start_frame + 1, n_points sztuk
    try:
        si = int(np.where(fn == s + 1)[0][0])
    except IndexError:
        si = None

    if si is not None:
        end_a = min(si + n_points, len(fn))
        ax.plot(fn[si:end_a], v[si:end_a], "o", ms=9, mfc="none",
                mec="tab:red", mew=2, label="fit pts")

    # krzywa modelu
    if fit.success:
        t_dense = np.linspace(s - 0.5, e + 0.5, 200)
        y_model = exp_decay_model(t_dense, fit.A, fit.t_0, fit.tau, fit.C)
        ax.plot(t_dense, y_model, "-", color="tab:red",
                label=f"fit: τ={fit.tau:.2f} fr, A={fit.A:.1f}")

    # poziom tła C (mediana trace)
    ax.axhline(fit.C, color="tab:gray", ls=":", lw=1, label=f"C={fit.C:.1f}")

    ax.set_xlabel("frame")
    ax.set_ylabel("events")
    ax.set_title(f"Injection #{discharge.injection_no} "
                 f"(ch {discharge.channel_id}, frames {s}–{e})")
    ax.grid(alpha=0.3)
    ax.legend(fontsize=8)
    return ax


plot_timetrace_with_discharges = plot_timetrace_with_injections
plot_discharge_fit = plot_injection_fit