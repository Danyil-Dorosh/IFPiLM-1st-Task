"""End-to-end demo na unitedc_62_239.txt.

Robi:
1. Wczytaj united .txt -> Shot.
2. Uruchom analyze_shot dla obu kanałów.
3. Zapisz wyniki do Parquet (+ CSV podgląd).
4. Zrób wykresy diagnostyczne.
"""
import sys
from pathlib import Path

# add project root to path so `import pha_lib` works
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import matplotlib
matplotlib.use("Agg")  # non-interactive backend
import matplotlib.pyplot as plt
import numpy as np

from pha_lib import io, pipeline, export
from pha_lib.timetrace import integrate_energy_window
from pha_lib.discharges import detect_discharges
from pha_lib.fit import fit_discharge_two_strategies
from pha_lib.plotting import (
    plot_timetrace_with_discharges,
    plot_discharge_fit,
)

INPUT = Path("/home/user/workspace/unitedc_62_239.txt")
OUT_DIR = ROOT / "output"
OUT_DIR.mkdir(exist_ok=True)


def main():
    print(f"Loading {INPUT.name}...")
    shot = io.load_united_txt(INPUT, shot_id="united_62_239")
    print(f"  Shot has {len(shot.channels)} channels, "
          f"{shot.meta['n_frames']} frames, {shot.meta['n_bins']} energy bins")

    # 1) full pipeline -> dataframes
    LINE_E = 6660.0
    HALF = 50.0
    N_PTS = 3
    print(f"\nAnalyzing line {LINE_E} eV (+/- {HALF} eV), n_points={N_PTS}...")
    results = pipeline.analyze_shot(
        shot,
        line_energy_eV=LINE_E,
        half_width_eV=HALF,
        n_points=N_PTS,
        channels=(1, 2),
    )

    for ch, df in results.items():
        print(f"\n--- Channel {ch}: found {len(df)} discharges ---")
        if not df.empty:
            shown = ["discharge_no", "start_frame", "finish_frame",
                     "A_f", "tau_f", "C_f",
                     "A", "tau", "C",
                     "fit_first_success", "fit_second_success"]
            print(df[shown].to_string(index=False))

    # 2) save parquet + csv
    paths = export.save_results_parquet(results, OUT_DIR, prefix="results",
                                         also_csv=True)
    for ch, p in paths.items():
        print(f"\nSaved channel {ch} -> {p}")

    # 3) diagnostic plots
    print("\nPlotting diagnostics...")
    fig, axes = plt.subplots(2, 1, figsize=(11, 7), sharex=True)
    for ax, ch in zip(axes, (1, 2)):
        channel = shot.channels[ch]
        trace = integrate_energy_window(channel, center_eV=LINE_E,
                                         half_width_eV=HALF,
                                         label=f"line {LINE_E} eV")
        discharges = detect_discharges(trace, line_energy_eV=LINE_E)
        plot_timetrace_with_discharges(trace, discharges, ax=ax)
    fig.suptitle(f"unitedc_62_239 — sum of events in {LINE_E} +/- {HALF} eV")
    fig.tight_layout()
    overview_path = OUT_DIR / "overview_timetrace.png"
    fig.savefig(overview_path, dpi=130)
    print(f"  saved {overview_path}")
    plt.close(fig)

    # per-discharge fit plots (channel 2 only — najsilniejszy sygnał)
    channel2 = shot.channels[2]
    trace2 = integrate_energy_window(channel2, center_eV=LINE_E,
                                      half_width_eV=HALF)
    discharges2 = detect_discharges(trace2, line_energy_eV=LINE_E)
    if discharges2:
        ncols = min(3, len(discharges2))
        nrows = (len(discharges2) + ncols - 1) // ncols
        fig, axes = plt.subplots(nrows, ncols, figsize=(6 * ncols, 4 * nrows),
                                 squeeze=False)
        for idx, d in enumerate(discharges2):
            ax = axes[idx // ncols][idx % ncols]
            fa, fb = fit_discharge_two_strategies(trace2, d, n_points=N_PTS)
            plot_discharge_fit(trace2, d, fa, fb, n_points=N_PTS, ax=ax)
        # hide unused
        for j in range(len(discharges2), nrows * ncols):
            axes[j // ncols][j % ncols].axis("off")
        fig.suptitle(f"Channel 2 — per-discharge fits @ {LINE_E} eV")
        fig.tight_layout()
        fits_path = OUT_DIR / "fits_channel2.png"
        fig.savefig(fits_path, dpi=130)
        print(f"  saved {fits_path}")
        plt.close(fig)

    print("\nDone.")


if __name__ == "__main__":
    main()
