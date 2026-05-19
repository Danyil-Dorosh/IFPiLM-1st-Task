"""Smoke tests dla biblioteki pha_lib.

Uruchom: python tests/test_basic.py   (lub: python -m pytest tests/)
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np

from pha_lib import io, pipeline
from pha_lib.fit import exp_decay_model, fit_discharge
from pha_lib.timetrace import integrate_energy_window
from pha_lib.discharges import detect_discharges
from pha_lib.model import Discharge, TimeTrace


UNITED_TXT = Path("/home/user/workspace/unitedc_62_239.txt")


def test_load_united_txt():
    shot = io.load_united_txt(UNITED_TXT, shot_id="t")
    assert set(shot.channels.keys()) == {1, 2}
    assert shot.meta["n_frames"] == 178
    assert shot.meta["n_bins"] == 2047
    ch1 = shot.channels[1]
    assert ch1.spectra.shape == (178, 2047)
    assert ch1.frame_numbers[0] == 62
    assert ch1.frame_numbers[-1] == 239


def test_energy_axis_steps_10eV():
    shot = io.load_united_txt(UNITED_TXT, shot_id="t")
    e = shot.channels[1].energy_eV
    np.testing.assert_allclose(np.diff(e), 10.0, rtol=1e-6)
    assert e[0] == 10.0


def test_channels_independent():
    """Channel 1 i 2 maj\u0105 r\u00f3\u017cne dane \u2014 nie sumujemy ich."""
    shot = io.load_united_txt(UNITED_TXT, shot_id="t")
    tr1 = integrate_energy_window(shot.channels[1], 6660.0, 50.0)
    tr2 = integrate_energy_window(shot.channels[2], 6660.0, 50.0)
    assert tr1.channel_id == 1
    assert tr2.channel_id == 2
    assert not np.array_equal(tr1.values, tr2.values)


def test_integrate_window_no_subtraction():
    """Bez odejmowania continuum: frame 102 ch2 z oknem ±50 eV = suma 1995."""
    shot = io.load_united_txt(UNITED_TXT, shot_id="t")
    trace = integrate_energy_window(
        shot.channels[2], 6660.0, 50.0, subtract_continuum=False,
    )
    idx = int(np.where(trace.frame_numbers == 102)[0][0])
    assert trace.values[idx] == 1995


def test_integrate_window_with_continuum_subtraction():
    """Z odejmowaniem continuum trace ma sens: tło ~0, peak >> tło."""
    shot = io.load_united_txt(UNITED_TXT, shot_id="t")
    trace = integrate_energy_window(shot.channels[2], 6660.0, 70.0)
    quiet_idx = int(np.where(trace.frame_numbers == 80)[0][0])
    peak_idx = int(np.where(trace.frame_numbers == 102)[0][0])
    # tło blisko zera (parę dziesiątek z fluktuacji), peak ~1700
    assert abs(trace.values[quiet_idx]) < 100
    assert trace.values[peak_idx] > 1500


def test_detect_discharges_finds_three():
    shot = io.load_united_txt(UNITED_TXT, shot_id="t")
    trace = integrate_energy_window(shot.channels[2], 6660.0, 70.0)
    ds = detect_discharges(trace, 6660.0)
    starts = [d.start_frame for d in ds]
    assert any(98 <= s <= 102 for s in starts), starts
    assert any(145 <= s <= 149 for s in starts), starts
    assert any(192 <= s <= 196 for s in starts), starts


def test_fit_curve_recovers_synthetic():
    """Wygeneruj idealny zanik \u2014 fit musi odda\u0107 t\u0119 sam\u0105 krzyw\u0105."""
    A_true, t0_true, tau_true, C_true = 1000.0, 101.0, 5.0, 50.0
    fn = np.arange(95, 115)
    v = exp_decay_model(fn.astype(float), A_true, t0_true, tau_true, C_true)
    trace = TimeTrace(frame_numbers=fn, values=v,
                      energy_window_eV=(6610, 6710), channel_id=2)
    # Symuluj discharge: start_frame = t0 - 1 (bo t_0 = drugi frame burstu)
    d = Discharge(discharge_no=1, channel_id=2, line_energy_eV=6660.0,
                  start_frame=100, finish_frame=110, peak_frame=101)
    fit = fit_discharge(trace, d, n_points=3)
    assert fit.success, fit.message
    assert fit.t_0 == 101.0  # zafiksowany na drugim frame burstu
    # Krzywa powinna by\u0107 dok\u0142adnie odzyskana (3 punkty, 3 unknowns => exact)
    y_fit = exp_decay_model(fn[6:9].astype(float), fit.A, fit.t_0, fit.tau, fit.C)
    np.testing.assert_allclose(y_fit, v[6:9], rtol=1e-3)


def test_pipeline_returns_two_dataframes():
    shot = io.load_united_txt(UNITED_TXT, shot_id="t")
    res = pipeline.analyze_shot(shot, line_energy_eV=6660.0)
    assert set(res.keys()) == {1, 2}
    df2 = res[2]
    expected = ["discharge_no", "discharge_E", "start_frame", "finish_frame",
                "A_f", "t_0_f", "tau_f", "C_f",
                "A", "t_0", "tau", "C"]
    for col in expected:
        assert col in df2.columns, f"missing column: {col}"
    assert len(df2) >= 3


def test_seconds_columns_are_frames_times_dt():
    """Niezasuffix-owane kolumny czasowe = ramki * frame_dt_s."""
    shot = io.load_united_txt(UNITED_TXT, shot_id="t", frame_dt_s=0.05)
    df2 = pipeline.analyze_shot(shot)[2]
    ok_rows = df2[df2["fit_success"]]
    assert len(ok_rows) > 0
    for _, row in ok_rows.iterrows():
        np.testing.assert_allclose(row["t_0"], row["t_0_f"] * 0.05, rtol=1e-9)
        np.testing.assert_allclose(row["tau"], row["tau_f"] * 0.05, rtol=1e-9)
        # A i C nie zmieniaj\u0105 si\u0119
        assert row["A"] == row["A_f"]
        assert row["C"] == row["C_f"]


if __name__ == "__main__":
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
