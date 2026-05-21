"""Fit y(t) = A * exp(-(t - t_0)/tau) + C for a single injection.

Convention
----------
- `t_0` is an INPUT to the fit (always = start_frame + 1 — the second
    point of the burst and the first point used in fitting). It is not a free
    parameter.
- `C` is an INPUT to the fit (median of the whole trace = background).
    It is not a free parameter.
- Free parameters: A, tau. We fit 2 unknowns on >=2 points using least-squares.

All values in `FitResult` are in units of FRAMES. Conversion to seconds is
handled in `pipeline.py` (multiply by `frame_dt_s`).
"""
from __future__ import annotations
import numpy as np
from scipy.optimize import curve_fit

from model import TimeTrace, Injection, FitResult


def exp_decay_model(t, A, t_0, tau, C):
    """y(t) = A * exp(-(t - t_0)/tau) + C — full model (for plotting)."""
    return A * np.exp(-(t - t_0) / tau) + C


def fit_injection(
    trace: TimeTrace,
    injection: Injection,
    n_points: int = 3,
) -> FitResult:
    """Fit an exponential for a single injection.

    Uses `n_points` frames starting from `start_frame + 1` (second point of the burst).
    `t_0` is fixed to start_frame + 1. `C` is fixed to the trace median.
    SciPy fits only A and tau.

    Returns
    -------
    FitResult
        All values are in units of frames.
    """
    fn = trace.frame_numbers
    v = trace.values

    # 1. t_0 = second point of the burst = first point used for fitting
    t_0 = float(injection.start_frame + 1)

    # 2. C = median of the whole trace (background)
    C_bg = float(np.median(v))

    # 3. Find index of t_0 in the trace
    try:
        start_idx = int(np.where(fn == int(t_0))[0][0])
    except IndexError:
        return FitResult(
            A=np.nan, t_0=t_0, tau=np.nan, C=C_bg,
            success=False, message=f"t_0={int(t_0)} not in trace",
        )

    # 4. Select n_points starting from t_0 (inclusive)
    end_idx = min(start_idx + n_points, len(fn))
    n_avail = end_idx - start_idx
    if n_avail < 2:
        return FitResult(
            A=np.nan, t_0=t_0, tau=np.nan, C=C_bg, n_points=n_avail,
            success=False, message=f"too few points (n_avail={n_avail}, need >=2)",
        )

    t_data = fn[start_idx:end_idx].astype(float)
    y_data = v[start_idx:end_idx]

    # 5. 2-parameter model: t_0 and C substituted as constants (closure)
    def _model(t, A, tau):
        return A * np.exp(-(t - t_0) / tau) + C_bg

    # Initial guess: A = first point minus background, tau = 1 frame
    p0 = (
        max(float(y_data[0] - C_bg), 1.0),
        1.0,
    )

    try:
        popt, _ = curve_fit(_model, t_data, y_data, p0=p0, maxfev=5000)
        A, tau = popt
        return FitResult(
            A=float(A), t_0=t_0, tau=float(tau), C=C_bg,
            success=True, message="ok", n_points=n_avail,
        )
    except Exception as e:
        return FitResult(
            A=np.nan, t_0=t_0, tau=np.nan, C=C_bg,
            success=False, message=f"fit failed: {type(e).__name__}: {e}",
            n_points=n_avail,
        )

#Wired with initial shot-discharge-injection terminology confusion
fit_discharge = fit_injection