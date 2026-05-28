"""Adaptive point-selection fitter (external prototype).

This standalone script provides `adaptive_fit_injection()` which mirrors the
interface of `pha_lib.fit.fit_injection` but tries multiple `n_points` and
selects the best fit according to a simple residual metric.

Placed at project root as requested; loaded dynamically by `scripts/run_demo.py`.
"""
from __future__ import annotations
import numpy as np
from scipy.optimize import curve_fit

try:
    # when run from project scripts the package is on sys.path
    from pha_lib.model import TimeTrace, Injection, FitResult
    from pha_lib.fit import fit_injection
except Exception:
    # fallback to local imports if module path differs
    from model import TimeTrace, Injection, FitResult  # type: ignore
    from fit import fit_injection  # type: ignore


def _safe_param_errors(cov: np.ndarray | None, size: int) -> np.ndarray:
    """Return 1-sigma parameter errors from covariance, or NaNs if unavailable."""
    if cov is None:
        return np.full(size, np.nan, dtype=float)
    try:
        diag = np.diag(cov).astype(float)
        diag[diag < 0] = np.nan
        return np.sqrt(diag)
    except Exception:
        return np.full(size, np.nan, dtype=float)


def fit_injection_with_errors(
    trace: TimeTrace,
    injection: Injection,
    n_points: int,
) -> dict:
    """Fit A and tau for a fixed t_0 and background C, plus parameter errors.

    This mirrors the library fit but returns 1-sigma uncertainties from the
    covariance matrix so the notebook can inspect how coefficients change as
    the number of fitted points changes.
    """
    fn = trace.frame_numbers
    v = trace.values
    t_0 = float(injection.start_frame + 1)

    try:
        start_idx = int(np.where(fn == int(t_0))[0][0])
    except Exception:
        return {
            "n_points": n_points,
            "success": False,
            "message": f"t_0={int(t_0)} not in trace",
            "A": np.nan,
            "A_err": np.nan,
            "t_0": t_0,
            "t_0_err": 0.0,
            "tau": np.nan,
            "tau_err": np.nan,
            "C": np.nan,
            "C_err": np.nan,
            "rss": np.nan,
        }

    end_idx = min(start_idx + n_points, len(fn))
    n_avail = end_idx - start_idx
    if n_avail < 2:
        return {
            "n_points": n_points,
            "success": False,
            "message": f"too few points (n_avail={n_avail}, need >=2)",
            "A": np.nan,
            "A_err": np.nan,
            "t_0": t_0,
            "t_0_err": 0.0,
            "tau": np.nan,
            "tau_err": np.nan,
            "C": np.nan,
            "C_err": np.nan,
            "rss": np.nan,
        }

    t_data = fn[start_idx:end_idx].astype(float)
    y_data = v[start_idx:end_idx].astype(float)

    c_bg = float(np.median(v))
    def _model(t, A, tau):
        return A * np.exp(-(t - t_0) / tau) + c_bg

    p0 = (
        max(float(y_data[0] - c_bg), 1.0),
        1.0,
    )

    try:
        popt, pcov = curve_fit(_model, t_data, y_data, p0=p0, maxfev=5000)
        A, tau = map(float, popt)
        A_err, tau_err = _safe_param_errors(pcov, 2)
        resid = y_data - _model(t_data, A, tau)
        rss = float(np.sum(resid ** 2))
        return {
            "n_points": n_points,
            "success": True,
            "message": "ok",
            "A": A,
            "A_err": float(A_err),
            "t_0": t_0,
            "t_0_err": 0.0,
            "tau": tau,
            "tau_err": float(tau_err),
            "C": c_bg,
            "C_err": 0.0,
            "rss": rss,
        }
    except Exception as exc:
        return {
            "n_points": n_points,
            "success": False,
            "message": f"fit failed: {type(exc).__name__}: {exc}",
            "A": np.nan,
            "A_err": np.nan,
            "t_0": t_0,
            "t_0_err": 0.0,
            "tau": np.nan,
            "tau_err": np.nan,
            "C": np.nan,
            "C_err": np.nan,
            "rss": np.nan,
        }


def sweep_injection_point_counts(
    trace: TimeTrace,
    injection: Injection,
    min_points: int = 3,
    max_points: int = 15,
) -> list[dict]:
    """Fit the same injection for all point counts in the requested range."""
    rows: list[dict] = []
    for n_points in range(min_points, max_points + 1):
        row = fit_injection_with_errors(trace, injection, n_points=n_points)
        rows.append(row)
    return rows


def adaptive_fit_injection(
    trace: TimeTrace,
    injection: Injection,
    min_points: int = 3,
    max_points: int = 12,
    metric: str = "rss",
) -> FitResult:
    """Try multiple `n_points` and return best FitResult.

    This function is intentionally small and relies on the library's
    `fit_injection()` to perform individual fits; only the selection logic
    (residual evaluation) lives here so it can be iterated without changing
    library internals.
    """
    best_fit: FitResult | None = None
    best_score = float("inf")
    last_failure: FitResult | None = None

    fn = trace.frame_numbers
    v = trace.values

    try:
        start_idx = int(np.where(fn == int(injection.start_frame + 1))[0][0])
    except Exception:
        return fit_injection(trace, injection, n_points=min_points)

    for n in range(min_points, max_points + 1):
        fit = fit_injection(trace, injection, n_points=n)
        if not fit.success:
            last_failure = fit
            continue

        # compute model residuals on the points actually used
        end_idx = min(start_idx + fit.n_points, len(fn))
        t_data = fn[start_idx:end_idx].astype(float)
        y_data = v[start_idx:end_idx]
        # model value using fit params
        y_model = fit.A * np.exp(-(t_data - fit.t_0) / fit.tau) + fit.C
        resid = y_data - y_model

        if metric == "rss":
            score = float(np.sum(resid ** 2))
        else:
            score = float(np.sum(resid ** 2))

        if score < best_score or (score == best_score and (best_fit is None or fit.n_points > best_fit.n_points)):
            best_score = score
            best_fit = fit

    if best_fit is not None:
        best_fit.message = f"adaptive ok (metric={metric}, score={best_score:.3f})"
        return best_fit
    if last_failure is not None:
        return last_failure
    return fit_injection(trace, injection, n_points=min_points)


# alias for clarity
fit_injection_adaptive = adaptive_fit_injection
