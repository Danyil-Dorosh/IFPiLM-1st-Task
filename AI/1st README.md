# pha_lib — library for analysing PHA data from W7-X

Modular Python library to automate pulse-height analysis (PHA). The library
detects injections in a shot from the W7-X stellarator, fits an exponential
decay
\( y(t) = A \cdot \exp\!\left(-\dfrac{t-t_0}{\tau}\right) + C \)
to each injection, and saves results as two DataFrames (one per energy channel).

## Project structure

```
pha_lib_project/
├── pha_lib/             ← main library (each file implements one pipeline step)
│   ├── __init__.py
│   ├── model.py         # dataclasses: Discharge, EnergyChannelData, TimeTrace, Injection, FitResult
│   ├── io.py            # load_united_txt, load_test_folder, (placeholder load_pha)
│   ├── timetrace.py     # integrate_energy_window — sum counts in an energy window
│   ├── discharges.py    # detect_injections — find start/finish frames
│   ├── fit.py           # exp decay fitting helpers
│   ├── pipeline.py      # analyze_discharge, analyze_channel — high-level API
│   ├── export.py        # save_results_parquet
│   └── plotting.py      # plotting helpers
├── tests/test_basic.py  # smoke tests (6/6 PASS on test data)
├── scripts/
│   ├── peek_data.py     # exploration: count events in window per frame
   │   └── run_demo.py      # end-to-end demo using unitedc_62_239.txt
├── output/              # results: results_channel{1,2}.parquet + .csv + diagnostic PNGs
└── README.md
```

## Modularity philosophy

Each module implements **one responsibility**, which makes testing and
replacement straightforward:

| Step | Input | Output | Module |
|---|---|---|---|
| 1. Load input | `.txt` (unified or folder) | `Discharge` | `io` |
| 2. Sum energy window | `EnergyChannelData` | `TimeTrace` | `timetrace` |
| 3. Detect injections | `TimeTrace` | `list[Injection]` | `discharges` |
| 4. Fit exponential | `TimeTrace + Injection` | `FitResult` | `fit` |
| 5. Combine into table | previous results | `pd.DataFrame` | `pipeline` |
| 6. Save results | `dict[ch, DataFrame]` | `.parquet` (+ `.csv`) | `export` |
| 7. Plot | `TimeTrace` / `Injection` | `matplotlib.Axes` | `plotting` |

Future work: implement `load_pha()` (binary format), alternative detection
strategies, different fit models, additional lines, and more channels.

## Quick start

```python
from pha_lib import io, pipeline, export

# 1. load shot
shot = io.load_united_txt("unitedc_62_239.txt", shot_id="united_62_239")

# 2. analyze the whole shot — returns {1: df, 2: df}
results = pipeline.analyze_shot(
   shot,
   line_energy_eV=6660.0,   # line center (Fe XXV)
   half_width_eV=50.0,      # +- 50 eV window
   n_points=3,              # number of frames to fit (spec: 3)
   channels=(1, 2),
)

# 3. save Parquet
export.save_results_parquet(results, out_dir="output", also_csv=True)
```

Demo end-to-end: `python scripts/run_demo.py`

## Output format

Each DataFrame contains one row per injection and the following columns:

| column | meaning |
|---|---|
| `injection_no` | sequential injection number in the shot |
| `discharge_E` | line energy (eV), e.g. 6660.0 |
| `start_frame` | first frame of the injection |
| `finish_frame` | last frame (return to background) |
| `A_f, t_0_f, tau_f, C_f` | fit parameters in frame units (`_f` suffix)
| `A, t_0, tau, C` | fit parameters converted to seconds |
| `fit_success` | whether the fit succeeded |
| `fit_message` | diagnostic message from the fit |
| `A_err, tau_err` | uncertainties (from covariance diag) |

> **Note on naming:** the `_f` suffix means "for frames" (parameters given in frame units).

## Fitting strategies

"first" — fit starts at the detected start frame.

"second" — fit starts at the second frame of the injection. This is often
better because the first frame may be on the rising edge; the actual peak
is frequently in the second frame (see example frames 100–102: 1270 → 1995 → 1642).

Diagnostic plots show both fits for comparison.

## Injection detection

The algorithm in `discharges.py`:

1. Background and noise: median (`bg`) + 1.4826·MAD (`scale`) — robust to spikes.
2. Start: first frame with signal > `bg + 3·scale` and jump from previous frame > `min_jump`.
3. Finish: signal below `bg + 1.5·scale` for `min_quiet_frames=2` frames.
4. Filters: minimum separation 3 frames, maximum injection length 25 frames.

All thresholds configurable via `DischargeDetectionConfig`.

## Fit stability — numerical note

With 3 points and 4 parameters `curve_fit` would fail. For `n_points=3` the library:

- fixes `t_0` to the chosen start frame,
- fixes `C` to the trace median (background),
- fits (A, tau) with a 2-parameter least-squares — numerically stable.

For `n_points >= 4` a full 4-parameter fit with bounds is used.

## Results on test data (`unitedc_62_239.txt`)

| Channel | # injections | Notes |
|---|---:|---|
| 1 | 2 | weak signal (max ~3.8σ above background) — channel 1 not optimized for 6660 eV |
| 2 | 4 | 3 clear injections (frames ~100, ~147, ~194) + 1 ramp-down around 64 |

See `output/overview_timetrace.png` and `output/fits_channel2.png`.

Example τ (channel 2, "second" strategy):
- frame ~100: τ ≈ 13.8 frames ≈ 0.69 s (frame_dt=50 ms)
- frame ~146: τ ≈ 5.6 frames ≈ 0.28 s
- frame ~194: τ hit upper bound — weak injection, fit uncertain

## Physical context — short notes

- **6660 eV line** likely corresponds to the Fe XXV resonance line (helium-like iron).
- **τ (decay time)** is the e-folding time of the impurity emission; it relates to
   particle confinement and recycling.
- **Channel 1 vs 2**: different filters lead to different sensitivity at 6660 eV.
   In our shot channel 2 sees the line more clearly than channel 1.
- **Doppler broadening** — the ±50 eV window (10 bins) covers expected Doppler
   widths for Fe XXV at typical ion temperatures.

## Roadmap

1. Implement `io.load_pha()` for binary `.pha` files when the format is available.
2. Automatic line identification and window centering (peak finding).
3. Per-injection background subtraction.
4. Multi-line analysis (compare τ across different impurity lines).
5. Improved uncertainty estimation for τ (bootstrap and covariance propagation).
6. YAML configuration for thresholds and windows.

## Requirements

```
numpy, scipy, pandas, matplotlib, pyarrow
```

## Tests

Run `python tests/test_basic.py` — 6 tests (parser, energy axis, window integration,
injection detection, fit roundtrip, full pipeline). All should pass.
