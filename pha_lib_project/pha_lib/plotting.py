"""Wykresy diagnostyczne — pomagają zobaczyć, czy fit ma sens fizyczny.

W fizyce wykres to nie ozdoba, tylko narzędzie kontroli jakości.
Minimum:
- przebieg czasowy (TimeTrace) z zaznaczonymi discharges,
- nakładka modelu fitu na punkty,
- szybki podgląd widma jednej ramki (sanity check).
"""
from __future__ import annotations
from typing import Iterable, Optional
import numpy as np
import matplotlib.pyplot as plt

from .model import TimeTrace, Discharge, ExpDecayFit
from .fit import exp_decay_model


def plot_timetrace_with_discharges(
    trace: TimeTrace,
    discharges: Iterable[Discharge] = (),
    ax: Optional[plt.Axes] = None,
    title: Optional[str] = None,
):
    """Narysuj TimeTrace + zaznacz zakresy discharges (start..finish)."""
    if ax is None:
        fig, ax = plt.subplots(figsize=(11, 4))
    ax.plot(trace.frame_numbers, trace.values, "-o", ms=3,
            color="tab:blue", label="events in window")
    for d in discharges:
        ax.axvspan(d.start_frame - 0.5, d.finish_frame + 0.5,
                   alpha=0.15, color="tab:orange")
        ax.axvline(d.start_frame, color="tab:orange", lw=1)
        ax.text(d.start_frame, ax.get_ylim()[1] * 0.95,
                f"#{d.discharge_no}", color="tab:orange", fontsize=9)
    ax.set_xlabel("frame")
    ax.set_ylabel("events (sum in energy window)")
    ax.set_title(title or f"Channel {trace.channel_id}: {trace.label}")
    ax.grid(alpha=0.3)
    ax.legend(loc="upper right")
    return ax


def plot_discharge_fit(
    trace: TimeTrace,
    discharge: Discharge,
    fit_first: ExpDecayFit,
    fit_second: ExpDecayFit,
    n_points: int = 3,
    pad: int = 4,
    ax: Optional[plt.Axes] = None,
):
    """Narysuj punkty discharge + dwie krzywe (fit od pierwszej i drugiej ramki)."""
    if ax is None:
        fig, ax = plt.subplots(figsize=(7, 4.5))

    fn = trace.frame_numbers
    v = trace.values
    s = discharge.start_frame
    e = discharge.finish_frame

    # context window
    lo, hi = s - pad, e + pad
    mask = (fn >= lo) & (fn <= hi)
    ax.plot(fn[mask], v[mask], "o-", ms=4, color="0.4", alpha=0.7,
            label="data (context)")

    # punkty użyte do fitu
    si = int(np.where(fn == s)[0][0])
    end_a = min(si + n_points, len(fn))
    ax.plot(fn[si:end_a], v[si:end_a], "o", ms=9, mfc="none",
            mec="tab:red", mew=2, label=f'fit "first" pts')

    end_b = min(si + 1 + n_points, len(fn))
    ax.plot(fn[si + 1:end_b], v[si + 1:end_b], "o", ms=14, mfc="none",
            mec="tab:green", mew=1.5, label=f'fit "second" pts')

    # krzywe modelu
    t_dense = np.linspace(s - 0.5, e + 0.5, 200)
    if fit_first.success:
        y_a = exp_decay_model(t_dense, fit_first.A, fit_first.t_0,
                              fit_first.tau, fit_first.C)
        ax.plot(t_dense, y_a, "--", color="tab:red",
                label=f"first: τ={fit_first.tau:.2f} fr")
    if fit_second.success:
        y_b = exp_decay_model(t_dense, fit_second.A, fit_second.t_0,
                              fit_second.tau, fit_second.C)
        ax.plot(t_dense, y_b, "-", color="tab:green",
                label=f"second: τ={fit_second.tau:.2f} fr")

    ax.set_xlabel("frame")
    ax.set_ylabel("events")
    ax.set_title(f"Discharge #{discharge.discharge_no} "
                 f"(ch {discharge.channel_id}, frames {s}–{e})")
    ax.grid(alpha=0.3)
    ax.legend(fontsize=8)
    return ax
