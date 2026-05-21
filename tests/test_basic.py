"""Smoke tests — basic sanity checks for the library.

Run with: python -m pytest tests/   (or simply python tests/test_basic.py)
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np

from pha_lib import io, pipeline
from pha_lib.fit import exp_decay_model, fit_injection
from pha_lib.timetrace import integrate_energy_window
from pha_lib.discharges import detect_injections, InjectionDetectionConfig
from pha_lib.model import TimeTrace, Injection


UNITED_TXT = Path(__file__).resolve().parent.parent / "data" / "test" / "modified" / "unitedc_62_239.txt"


def test_load_united_txt():
    """File loads; frames and bins match the description."""
    discharge = io.load_united_txt(UNITED_TXT, discharge_id="t")
    assert set(discharge.channels.keys()) == {1, 2}
    assert discharge.meta["n_frames"] == 178   # 62..239 = 178 ramek
    assert discharge.meta["n_bins"] == 2047    # after removing trash footer
    ch1 = discharge.channels[1]
    assert ch1.spectra.shape == (178, 2047)
    assert ch1.frame_numbers[0] == 62
    assert ch1.frame_numbers[-1] == 239


def test_energy_axis_steps_10eV():
    discharge = io.load_united_txt(UNITED_TXT, discharge_id="t")
    e = discharge.channels[1].energy_eV
    np.testing.assert_allclose(np.diff(e), 10.0, rtol=1e-6)
    assert e[0] == 10.0


def test_integrate_window_matches_manual():
    """Manually check the sum for frame 102 ch2 — we know the expected value."""
    discharge = io.load_united_txt(UNITED_TXT, discharge_id="t")
    trace = integrate_energy_window(discharge.channels[2], 6660.0, 50.0)
    idx = int(np.where(trace.frame_numbers == 102)[0][0])
    # z peek_data.py wiemy: frame 102 ch2 = 1995
    assert trace.values[idx] == 1995


def test_detect_injections_finds_three():
    """This discharge should contain ~3-4 injections in channel 2."""
    discharge = io.load_united_txt(UNITED_TXT, discharge_id="t")
    trace = integrate_energy_window(discharge.channels[2], 6660.0, 50.0)
    injections = detect_injections(trace, 6660.0)
    starts = [d.start_frame for d in injections]
    # expect around 100, 147, 194 (these three are true injections)
    assert any(98 <= s <= 102 for s in starts), starts
    assert any(145 <= s <= 149 for s in starts), starts
    assert any(192 <= s <= 196 for s in starts), starts


def test_exp_decay_model_roundtrip():
    """Generate an ideal decay — fit must reproduce the same curve y(t).

    Physical note: parameters (A, t_0) are degenerate —
    A*exp(-(t-t_0)/tau) = (A*exp(t_0/tau)) * exp(-t/tau), so different pairs
    (A, t_0) produce the same curve. We therefore compare the curve, not
    individual A or t_0 values.
    """
    A_true, t0_true, tau_true, C_true = 1000.0, 100.0, 5.0, 50.0
    # create a longer trace with background C_true so median(trace.values)==C_true
    full_frames = np.arange(0, 300, dtype=int)
    values = np.full_like(full_frames, float(C_true), dtype=float)

    t = np.arange(100, 110, dtype=float)
    y = exp_decay_model(t, A_true, t0_true, tau_true, C_true)
    values[100:110] = y

    # fit_injection expects a TimeTrace and an Injection dataclass
    trace = TimeTrace(frame_numbers=full_frames, values=values, energy_window_eV=(6660.0, 6660.0), channel_id=2)
    # t_0 in fit_injection = start_frame + 1 -> to get t_0=100, start_frame must be 99
    inj = Injection(injection_no=1, channel_id=2, line_energy_eV=6660.0, start_frame=99, finish_frame=109, peak_frame=100)

    fit = fit_injection(trace, inj)
    assert fit.success
    assert abs(fit.tau - tau_true) < 0.05
    assert abs(fit.C - C_true) < 0.5
    y_fit = exp_decay_model(t, fit.A, fit.t_0, fit.tau, fit.C)
    np.testing.assert_allclose(y_fit, y, rtol=1e-3)


def test_pipeline_returns_dataframes():
    discharge = io.load_united_txt(UNITED_TXT, discharge_id="t")
    res = pipeline.analyze_discharge(discharge, line_energy_eV=6660.0)
    assert set(res.keys()) == {1, 2}
    df2 = res[2]
    expected_cols = ["injection_no", "discharge_E", "start_frame",
                     "finish_frame", "A_f", "t_0_f", "tau_f", "C_f",
                     "A", "t_0", "tau", "C"]
    for col in expected_cols:
        assert col in df2.columns, f"missing column: {col}"
    # at least 3 real injections in ch2
    assert len(df2) >= 3


if __name__ == "__main__":
    # uproszczony runner bez pytest
    failed = 0
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for tf in tests:
        try:
            tf()
            print(f"PASS  {tf.__name__}")
        except AssertionError as e:
            failed += 1
            print(f"FAIL  {tf.__name__}: {e}")
        except Exception as e:
            failed += 1
            print(f"ERROR {tf.__name__}: {type(e).__name__}: {e}")
    print(f"\n{len(tests) - failed}/{len(tests)} tests passed")
    sys.exit(1 if failed else 0)
