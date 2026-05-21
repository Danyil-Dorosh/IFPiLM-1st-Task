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
