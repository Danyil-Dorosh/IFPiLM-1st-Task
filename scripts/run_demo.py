"""End-to-end demo using unitedc_62_239.txt.

Loads a discharge, analyzes each channel SEPARATELY, writes two Parquet/CSV
files and generates diagnostic plots (overview + per-injection fits).
"""
import sys
from pathlib import Path

import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from pha_lib import io, pipeline, export, plotting
from pha_lib.timetrace import integrate_energy_window
from pha_lib.discharges import detect_injections
from pha_lib.fit import fit_injection

INPUT = Path("data\\test\\modified\\unitedc_62_239.txt")
OUT = ROOT / "output"
PLOTS = ROOT / "output" / "plots"

LINE_E = 6660.0
HALF_W = 60.0
N_POINTS = 3


def main():
    print(f"Loading {INPUT.name}...")
    discharge = io.load_united_txt(INPUT, discharge_id="united_62_239")
    print(f"  {discharge.meta['n_frames']} frames, {discharge.meta['n_bins']} bins, "
        f"frame_dt = {discharge.frame_dt_s} s\n")

    # === ANALYSIS: two channels, separate DataFrames ===
    results = pipeline.analyze_discharge(
        discharge,
        line_energy_eV=LINE_E,
        half_width_eV=HALF_W,
        n_points=N_POINTS,
        channels=(1, 2),
    )

    for ch, df in results.items():
        print(f"--- Channel {ch}: {len(df)} injections ---")
        if not df.empty:
            cols = ["injection_no", "start_frame", "finish_frame",
                    "A_f", "t_0_f", "tau_f", "C_f",
                    "A",   "t_0",   "tau",   "C",
                    "fit_success"]
            print(df[cols].to_string(index=False))
        print()

    # === EXPORT ===
    paths = export.save_results_parquet(results, OUT, prefix="results", also_csv=True)
    for ch, p in paths.items():
        print(f"Saved channel {ch} -> {p}")

    # === DIAGNOSTIC PLOTS ===
    # Recompute TimeTrace + Injections (same parameters as in pipeline)
    # and plot. The pipeline returns only DataFrames, so we recompute traces
    # for plotting (cheap recompute, same inputs => same outputs).
    PLOTS.mkdir(parents=True, exist_ok=True)

    for ch_id, channel in discharge.channels.items():
        trace = integrate_energy_window(channel, LINE_E, HALF_W)
        injections = detect_injections(trace, LINE_E)

        # Overview: full trace with highlighted injections
        fig, ax = plt.subplots(figsize=(11, 4))
        plotting.plot_timetrace_with_injections(trace, injections, ax=ax)
        out_overview = PLOTS / f"overview_ch{ch_id}.png"
        fig.tight_layout()
        fig.savefig(out_overview, dpi=120)
        plt.close(fig)
        print(f"Saved {out_overview}")

        # Per-injection: fit
        for d in injections:
            fit = fit_injection(trace, d, n_points=N_POINTS)
            fig, ax = plt.subplots(figsize=(7, 4.5))
            plotting.plot_injection_fit(trace, d, fit,
                                        n_points=N_POINTS, ax=ax)
            out_fit = PLOTS / f"fit_ch{ch_id}_d{d.injection_no}.png"
            fig.tight_layout()
            fig.savefig(out_fit, dpi=120)
            plt.close(fig)
            print(f"Saved {out_fit}")


if __name__ == "__main__":
    main()