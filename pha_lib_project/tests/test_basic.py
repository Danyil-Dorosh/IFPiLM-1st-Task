"""Smoke tests \u2014 podstawowe sanity checks dla biblioteki.

Uruchom: python -m pytest tests/   (lub po prostu python tests/test_basic.py)
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np

from pha_lib import io, pipeline
from pha_lib.fit import exp_decay_model, fit_exp_decay
from pha_lib.timetrace import integrate_energy_window
from pha_lib.discharges import detect_discharges, DischargeDetectionConfig


UNITED_TXT = Path("/home/user/workspace/unitedc_62_239.txt")


def test_load_united_txt():
    """Plik wczytuje si\u0119, ramki i biny zgadzaj\u0105 si\u0119 z opisem."""
    shot = io.load_united_txt(UNITED_TXT, shot_id="t")
    assert set(shot.channels.keys()) == {1, 2}
    assert shot.meta["n_frames"] == 178   # 62..239 = 178 ramek
    assert shot.meta["n_bins"] == 2047    # po usuni\u0119ciu trash footer
    ch1 = shot.channels[1]
    assert ch1.spectra.shape == (178, 2047)
    assert ch1.frame_numbers[0] == 62
    assert ch1.frame_numbers[-1] == 239


def test_energy_axis_steps_10eV():
    shot = io.load_united_txt(UNITED_TXT, shot_id="t")
    e = shot.channels[1].energy_eV
    np.testing.assert_allclose(np.diff(e), 10.0, rtol=1e-6)
    assert e[0] == 10.0


def test_integrate_window_matches_manual():
    """Sprawd\u017a r\u0119cznie sum\u0119 dla ramki 102 ch2 \u2014 znamy oczekiwan\u0105 warto\u015b\u0107."""
    shot = io.load_united_txt(UNITED_TXT, shot_id="t")
    trace = integrate_energy_window(shot.channels[2], 6660.0, 50.0)
    idx = int(np.where(trace.frame_numbers == 102)[0][0])
    # z peek_data.py wiemy: frame 102 ch2 = 1995
    assert trace.values[idx] == 1995


def test_detect_discharges_finds_three():
    """W tym shocie powinny si\u0119 pojawi\u0107 ~3-4 discharges w channel 2."""
    shot = io.load_united_txt(UNITED_TXT, shot_id="t")
    trace = integrate_energy_window(shot.channels[2], 6660.0, 50.0)
    ds = detect_discharges(trace, 6660.0)
    starts = [d.start_frame for d in ds]
    # oczekujemy okolic 100, 147, 194 (te trzy s\u0105 prawdziwe injekcje)
    assert any(98 <= s <= 102 for s in starts), starts
    assert any(145 <= s <= 149 for s in starts), starts
    assert any(192 <= s <= 196 for s in starts), starts


def test_exp_decay_model_roundtrip():
    """Wygeneruj idealny zanik — fit musi oddać tę samą krzywą y(t).

    Uwaga fizyczna: parametry (A, t_0) są zdegenerowane —
    A*exp(-(t-t_0)/tau) = (A*exp(t_0/tau)) * exp(-t/tau), więc różne pary
    (A, t_0) dają tę samą krzywą. Porównujemy więc krzywą, nie poszczególne A, t_0.
    """
    A_true, t0_true, tau_true, C_true = 1000.0, 100.0, 5.0, 50.0
    t = np.arange(100, 110, dtype=float)
    y = exp_decay_model(t, A_true, t0_true, tau_true, C_true)
    fit = fit_exp_decay(t, y)
    assert fit.success
    assert abs(fit.tau - tau_true) < 0.05
    assert abs(fit.C - C_true) < 0.5
    y_fit = exp_decay_model(t, fit.A, fit.t_0, fit.tau, fit.C)
    np.testing.assert_allclose(y_fit, y, rtol=1e-3)


def test_pipeline_returns_dataframes():
    shot = io.load_united_txt(UNITED_TXT, shot_id="t")
    res = pipeline.analyze_shot(shot, line_energy_eV=6660.0)
    assert set(res.keys()) == {1, 2}
    df2 = res[2]
    expected_cols = ["discharge_no", "discharge_E", "start_frame",
                     "finish_frame", "A_f", "t_0_f", "tau_f", "C_f",
                     "A", "t_0", "tau", "C"]
    for col in expected_cols:
        assert col in df2.columns, f"missing column: {col}"
    # przynajmniej 3 prawdziwe discharges w ch2
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
