# pha_lib — API reference

This document describes the public functions and modules inside the `pha_lib` package. Keep `pha_lib` focused on stable, well-tested library functions; project-level notes and testing data live in `AI/context.md`.

Modules and primary responsibilities:

- `pha_lib.model` — dataclasses and domain objects: `Discharge`, `EnergyChannelData`, `TimeTrace`, `Injection`, `FitResult`.
- `pha_lib.io` — input routines: `load_united_txt`, `load_test_folder`, and placeholders for `.pha` readers. These functions return `Discharge` objects.
- `pha_lib.timetrace` — time-trace helpers: `integrate_energy_window` and small utilities that compute per-frame counts for a given energy window.
- `pha_lib.discharges` — injection detection: `detect_injections` and `InjectionDetectionConfig` (returns `list[Injection]`).
- `pha_lib.fit` — fitting primitives: `fit_injection` which fits the exponential decay model and returns `FitResult`.
- `pha_lib.pipeline` — high-level API: `analyze_discharge` and `analyze_channel` that orchestrate the full workflow and return result `DataFrame`s (one per channel).
- `pha_lib.export` — output helpers: `save_results_parquet`, `load_results_parquet`.
- `pha_lib.plotting` — visualization: `plot_timetrace_with_injections`, `plot_injection_fit`.

Quick usage (library-focused):

```python
from pha_lib import io, pipeline, export

# 1. load a discharge (path can be any supported input)
discharge = io.load_united_txt("path/to/discharge_united.txt", discharge_id="XP_test")

# 2. analyze the discharge — returns a dict[channel, DataFrame]
results = pipeline.analyze_discharge(
    discharge,
    line_energy_eV=6660.0,
    half_width_eV=50.0,
    n_points=3,
    channels=(1, 2),
)

# 3. persist results
export.save_results_parquet(results, out_dir="output", also_csv=False)
```

Result `DataFrame` schema (per-channel):

- `injection_no` — sequential injection index
- `discharge_E` — analyzed line energy (eV)
- `start_frame`, `finish_frame` — injection interval (frame units)
- `A_f`, `t_0_f`, `tau_f`, `C_f` — fit parameters in frames
- `A`, `t_0`, `tau`, `C` — fit parameters converted to seconds (using `frame_dt_s`)
- `fit_success`, `fit_message` — diagnostics

Design notes:

- Keep `pha_lib` modules self-contained and stable.
- Move dataset-specific descriptions, test fixtures, and demo scripts out of this README and into `AI/context.md` or `scripts/`.

