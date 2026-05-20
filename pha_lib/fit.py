"""Dopasowanie y(t) = A * exp(-(t - t_0)/tau) + C dla jednej injekcji.

Konwencja
---------
- t_0 jest INPUT-em do fitu (zawsze = start_frame + 1, czyli drugi punkt
  burstu = pierwszy punkt brany do dopasowania). NIE jest wolnym parametrem.
- C jest INPUT-em do fitu (mediana całego trace = poziom tła).
  NIE jest wolnym parametrem.
- Wolne parametry: A, tau. Fitujemy 2 niewiadome na 3 punktach
  → least-squares (overdetermined, numerycznie zdrowe).

Wszystkie wartości w `FitResult` są w jednostkach RAMEK. Konwersja na sekundy
odbywa się w pipeline.py (mnożenie przez frame_dt_s).
"""
from __future__ import annotations
import numpy as np
from scipy.optimize import curve_fit

from .model import TimeTrace, Injection, FitResult


def exp_decay_model(t, A, t_0, tau, C):
    """y(t) = A * exp(-(t - t_0)/tau) + C — pełny model (dla rysowania)."""
    return A * np.exp(-(t - t_0) / tau) + C


def fit_injection(
    trace: TimeTrace,
    injection: Injection,
    n_points: int = 3,
) -> FitResult:
    """Dopasuj eksponensę dla jednej injekcji.

    Bierze n_points ramek zaczynając od start_frame + 1 (drugi punkt burstu).
    t_0 zafiksowane na start_frame + 1. C zafiksowane na medianie trace.
    scipy fituje tylko A i tau.

    Returns
    -------
    FitResult
        Wszystkie wartości w jednostkach ramek.
    """
    fn = trace.frame_numbers
    v = trace.values

    # 1. t_0 = drugi punkt burstu = pierwszy punkt brany do fitu
    t_0 = float(injection.start_frame + 1)

    # 2. C = mediana całego trace (tło)
    C_bg = float(np.median(v))

    # 3. Znajdź index t_0 w trace
    try:
        start_idx = int(np.where(fn == int(t_0))[0][0])
    except IndexError:
        return FitResult(
            A=np.nan, t_0=t_0, tau=np.nan, C=C_bg,
            success=False, message=f"t_0={int(t_0)} not in trace",
        )

    # 4. Wybierz n_points punktów od t_0 włącznie
    end_idx = min(start_idx + n_points, len(fn))
    n_avail = end_idx - start_idx
    if n_avail < 2:
        return FitResult(
            A=np.nan, t_0=t_0, tau=np.nan, C=C_bg, n_points=n_avail,
            success=False, message=f"too few points (n_avail={n_avail}, need >=2)",
        )

    t_data = fn[start_idx:end_idx].astype(float)
    y_data = v[start_idx:end_idx]

    # 5. Model 2-parametrowy: t_0 i C podstawione jako stałe (closure)
    def _model(t, A, tau):
        return A * np.exp(-(t - t_0) / tau) + C_bg

    # Initial guess: A = pierwszy punkt minus tło, tau = 1 ramka
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


fit_discharge = fit_injection