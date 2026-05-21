"""Diagnostic plots — help assess whether the fit makes physical sense.

In physics, a plot is a quality-control tool, not decoration.
Minimum plots:
- time trace (TimeTrace) with highlighted injections,
- overlay of the fitted model on the points used for fitting.
"""
from __future__ import annotations
from typing import Iterable, Optional
import numpy as np
import matplotlib.pyplot as plt

from model import TimeTrace, Injection, FitResult
from fit import exp_decay_model


def plot_timetrace_with_injections(
    trace: TimeTrace,
    injections: Iterable[Injection] = (),
    ax: Optional[plt.Axes] = None,
    title: Optional[str] = None,
):
    """Plot a TimeTrace and highlight injection ranges (start..finish)."""
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
    """Plot injection points and the fitted model curve.

    Convention (same as in fit.py):
    - fit points start at start_frame + 1 (second point of the burst),
      take n_points consecutive frames.
    - fit t_0 = start_frame + 1 (fixed).
    - fit C  = median of the whole trace (fixed).
    """
    if ax is None:
        fig, ax = plt.subplots(figsize=(7, 4.5))

    fn = trace.frame_numbers
    v = trace.values
    s = discharge.start_frame
    e = discharge.finish_frame

    # context window (a few frames before and after the injection)
    lo, hi = s - pad, e + pad
    mask = (fn >= lo) & (fn <= hi)
    ax.plot(fn[mask], v[mask], "o-", ms=4, color="0.4", alpha=0.7,
            label="data (context)")

    # points used for fitting: from start_frame + 1, n_points long
    try:
        si = int(np.where(fn == s + 1)[0][0])
    except IndexError:
        si = None

    if si is not None:
        end_a = min(si + n_points, len(fn))
        ax.plot(fn[si:end_a], v[si:end_a], "o", ms=9, mfc="none",
                mec="tab:red", mew=2, label="fit pts")

    # model curve
    if fit.success:
        t_dense = np.linspace(s - 0.5, e + 0.5, 200)
        y_model = exp_decay_model(t_dense, fit.A, fit.t_0, fit.tau, fit.C)
        ax.plot(t_dense, y_model, "-", color="tab:red",
                label=f"fit: τ={fit.tau:.2f} fr, A={fit.A:.1f}")

    # background level C (median of the trace)
    ax.axhline(fit.C, color="tab:gray", ls=":", lw=1, label=f"C={fit.C:.1f}")

    ax.set_xlabel("frame")
    ax.set_ylabel("events")
    ax.set_title(f"Injection #{discharge.injection_no} "
                 f"(ch {discharge.channel_id}, frames {s}–{e})")
    ax.grid(alpha=0.3)
    ax.legend(fontsize=8)
    return ax

#Wired with initial shot-discharge-injection terminology confusion
plot_timetrace_with_discharges = plot_timetrace_with_injections
plot_discharge_fit = plot_injection_fit