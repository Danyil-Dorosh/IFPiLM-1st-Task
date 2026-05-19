"""Dopasowanie y(t) = A * exp(-(t - t_0) / tau) + C do przebiegu czasowego.

Dlaczego ten model?
-------------------
Po injekcji zanieczyszczenia jego koncentracja w plazmie spada wykładniczo
(transport + recycling), więc liczba detected photonów też zanika
wykładniczo. `tau` to tzw. „confinement time" zanieczyszczenia, a `C`
to poziom tła (continuum + dark counts).

Strategie dopasowania (zgodne z opisem zadania)
-----------------------------------------------
- `"first"`  — fit zaczynamy od pierwszej ramki discharge.
- `"second"` — fit zaczynamy od DRUGIEJ ramki (zwykle właściwej, bo pierwsza
              jeszcze może być na zboczu wzrastającym injekcji).
Standardowo zwracamy oba — kolumny w wynikowej tabeli pasują do specyfikacji
„*_f" (od first) oraz bez sufiksu (od second).

Liczba punktów do fitu
----------------------
Domyślnie używamy 3 ramek (start, start+1, start+2 / start, start+1, start+2
zależnie od strategii). Dla `n_points >= 4` parametry są lepiej określone,
ale zwykle po >3 ramkach tło zaczyna dominować i fit traci sens fizyczny.
"""
from __future__ import annotations
from typing import Optional
import numpy as np
from scipy.optimize import curve_fit

from .model import TimeTrace, Discharge, ExpDecayFit


def exp_decay_model(t: np.ndarray, A: float, t_0: float, tau: float, C: float) -> np.ndarray:
    """y(t) = A * exp(-(t - t_0) / tau) + C."""
    return A * np.exp(-(t - t_0) / tau) + C


def _initial_guess(t: np.ndarray, y: np.ndarray) -> tuple[float, float, float, float]:
    """Heurystyczny start dla curve_fit.

    A     = max(y) - min(y)
    t_0   = t[argmax(y)]
    tau   = (t[-1] - t[0]) / 2  (umiarkowany rozsądek)
    C     = min(y)
    """
    A = float(np.max(y) - np.min(y))
    t_0 = float(t[int(np.argmax(y))])
    span = float(t[-1] - t[0]) if len(t) > 1 else 1.0
    tau = max(span / 2.0, 1e-3)
    C = float(np.min(y))
    return A, t_0, tau, C


def fit_exp_decay(
    t: np.ndarray,
    y: np.ndarray,
    p0: Optional[tuple[float, float, float, float]] = None,
    fix_t_0: Optional[float] = None,
    fix_C: Optional[float] = None,
    use_bounds: bool = True,
) -> ExpDecayFit:
    """Dopasuj model A*exp(-(t-t_0)/tau)+C do danych (t, y).

    Parameters
    ----------
    t, y : np.ndarray
        Punkty do dopasowania (np. ramki vs. liczba eventów).
    p0 : optional initial guess
        Jeśli None — używamy `_initial_guess`.
    fix_t_0 : float, optional
        Jeśli podane, t_0 jest stały podczas fitu.
        Przydatne, gdy chcemy zafiksować t_0 na konkretnej ramce.
    fix_C : float, optional
        Jeśli podane, C jest stałe podczas fitu. Bardzo użyteczne dla 3 punktów —
        zamiast 3-param exact fit dostajemy 2-param least-squares (A, tau)
        z fizycznie sensownym tłem (np. mediana całego trace).
    use_bounds : bool
        Jeśli True (domyślnie), narzucamy fizyczne ograniczenia:
            A   >= 0   (amplituda peaku, nie negatywna)
            tau >= 1e-3  (stała czasowa zaniku, dodatnia)
            C   >= 0   (poziom tła, nieujemny)
            t_0 in [t[0]-(t[-1]-t[0]), t[-1]]  (rozsądny zakres)
        To zapobiega niefizycznym dopasowaniom typu A=-1843 lub tau=22975.

    Returns
    -------
    ExpDecayFit
        success=True jeśli się udało; w przeciwnym razie failed(...).
    """
    t = np.asarray(t, dtype=float)
    y = np.asarray(y, dtype=float)
    n = len(t)

    if n < 3:
        return ExpDecayFit.failed(f"too few points (n={n}, need >=3)")

    span = float(t[-1] - t[0]) if n > 1 else 1.0
    y_max = float(np.max(y))

    try:
        if fix_t_0 is None:
            if p0 is None:
                p0 = _initial_guess(t, y)
            if use_bounds:
                lower = (0.0, t[0] - span, 1e-3, 0.0)
                upper = (10.0 * max(y_max, 1.0), t[-1], 100.0 * span, max(y_max, 1.0))
                # clip p0 into bounds
                p0 = tuple(min(max(p, lo), up) for p, lo, up in zip(p0, lower, upper))
                popt, pcov = curve_fit(
                    exp_decay_model, t, y, p0=p0,
                    bounds=(lower, upper), maxfev=20_000,
                )
            else:
                popt, pcov = curve_fit(
                    exp_decay_model, t, y, p0=p0, maxfev=20_000,
                )
            A, t_0, tau, C = popt
            errs = np.sqrt(np.diag(pcov)) if pcov is not None else [np.nan] * 4
            A_err, t_0_err, tau_err, C_err = errs
        elif fix_t_0 is not None and fix_C is not None:
            # 2-param fit: tylko A, tau (t_0 i C stałe). Najbezpieczniejsze
            # dla 3 punktów — prawdziwy least-squares zamiast exact fit.
            t0_fixed = float(fix_t_0)
            C_fixed = float(fix_C)

            def _model_AT(tt, A, tau):
                return A * np.exp(-(tt - t0_fixed) / tau) + C_fixed

            A0, _, tau0, _ = (p0 or _initial_guess(t, y))
            A0 = max(A0, 1e-6)
            tau0 = max(tau0, 1e-3)
            if use_bounds:
                lower = (0.0, 1e-3)
                upper = (10.0 * max(y_max, 1.0), 100.0 * span)
                p2 = (min(max(A0, lower[0]), upper[0]),
                      min(max(tau0, lower[1]), upper[1]))
                popt, pcov = curve_fit(
                    _model_AT, t, y, p0=p2,
                    bounds=(lower, upper), maxfev=20_000,
                )
            else:
                popt, pcov = curve_fit(
                    _model_AT, t, y, p0=(A0, tau0), maxfev=20_000,
                )
            A, tau = popt
            C = C_fixed
            t_0 = t0_fixed
            errs = np.sqrt(np.diag(pcov)) if pcov is not None else [np.nan] * 2
            A_err, tau_err = errs
            C_err = 0.0
            t_0_err = 0.0
        else:
            # 3-parameter fit z zafiksowanym t_0 (a wolnym C)
            t0_fixed = float(fix_t_0)

            def _model_fixed_t0(tt, A, tau, C):
                return A * np.exp(-(tt - t0_fixed) / tau) + C

            A0, _, tau0, C0 = (p0 or _initial_guess(t, y))
            if use_bounds:
                lower = (0.0, 1e-3, 0.0)
                upper = (10.0 * max(y_max, 1.0), 100.0 * span, max(y_max, 1.0))
                p3 = (
                    min(max(A0,   lower[0]), upper[0]),
                    min(max(tau0, lower[1]), upper[1]),
                    min(max(C0,   lower[2]), upper[2]),
                )
                popt, pcov = curve_fit(
                    _model_fixed_t0, t, y, p0=p3,
                    bounds=(lower, upper), maxfev=20_000,
                )
            else:
                popt, pcov = curve_fit(
                    _model_fixed_t0, t, y, p0=(A0, tau0, C0), maxfev=20_000,
                )
            A, tau, C = popt
            t_0 = t0_fixed
            errs = np.sqrt(np.diag(pcov)) if pcov is not None else [np.nan] * 3
            A_err, tau_err, C_err = errs
            t_0_err = 0.0

        return ExpDecayFit(
            A=float(A), t_0=float(t_0), tau=float(tau), C=float(C),
            A_err=float(A_err), t_0_err=float(t_0_err),
            tau_err=float(tau_err), C_err=float(C_err),
            n_points=n, success=True, message="ok",
        )
    except Exception as e:  # noqa: BLE001
        return ExpDecayFit.failed(f"fit failed: {type(e).__name__}: {e}")


def fit_discharge_two_strategies(
    trace: TimeTrace,
    discharge: Discharge,
    n_points: int = 3,
    fix_C_to_background: bool = True,
) -> tuple[ExpDecayFit, ExpDecayFit]:
    """Dopasuj eksponensę dla jednego discharge dwoma strategiami startu.

    Strategie
    ---------
    "first"  : fit od `start_frame` z `n_points` punktami. t_0 jest
               zafiksowany na `start_frame` jeśli n_points==3 (model ma 4
               parametry — z 3 punktami i 4 parametrami curve_fit zawiedzie;
               zafiksowanie t_0 daje 3-param fit, dokładnie wyznaczony).
               Dla n_points >= 4 robimy pełny 4-param fit.
    "second" : analogicznie, ale od `start_frame + 1`. Zwykle jest to
               właściwa strategia — pierwsza ramka discharge może być na
               zboczu wzrastającym injekcji, a drugi punkt jest bliżej
               prawdziwego maksimum.

    Parameters
    ----------
    fix_C_to_background : bool, default True
        Jeśli True i n_points==3, fixujemy C = mediana całego trace (poziom
        tła). To zamienia exact 3-param fit na 2-param least-squares (A, tau)
        — numerycznie znacznie stabilniejsze i fizycznie lepsze (tło jest
        cechą całego shotu, a nie 3 punktów).

    Returns
    -------
    (fit_from_first, fit_from_second)
    """
    fn = trace.frame_numbers
    v = trace.values

    try:
        start_i = int(np.where(fn == discharge.start_frame)[0][0])
    except IndexError:
        return (ExpDecayFit.failed("start_frame not in trace"),
                ExpDecayFit.failed("start_frame not in trace"))

    # poziom tła z całego trace (mediana — odporna na peaki)
    bg_level = float(np.median(v))

    def _fit_window(start_idx: int) -> ExpDecayFit:
        end_idx = min(start_idx + n_points, len(fn))
        n_avail = end_idx - start_idx
        if n_avail < 3:
            return ExpDecayFit.failed(
                f"too few points (n_avail={n_avail}, need >=3)"
            )
        t_w = fn[start_idx:end_idx].astype(float)
        y_w = v[start_idx:end_idx]
        if n_avail == 3:
            # 3 punkty: t_0 fix + C fix => 2 param fit (A, tau)
            if fix_C_to_background:
                return fit_exp_decay(
                    t_w, y_w,
                    fix_t_0=float(t_w[0]), fix_C=bg_level,
                )
            # awaryjnie: tylko fix t_0
            return fit_exp_decay(t_w, y_w, fix_t_0=float(t_w[0]))
        # 4+ punktów — pełny 4-param fit
        return fit_exp_decay(t_w, y_w)

    fit_a = _fit_window(start_i)        # od pierwszej ramki discharge
    fit_b = _fit_window(start_i + 1)    # od drugiej ramki discharge
    return fit_a, fit_b
