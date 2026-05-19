"""End-to-end demo na unitedc_62_239.txt.

Wczytuje shot, analizuje OSOBNO każdy kanał, zapisuje 2 osobne Parquet/CSV
i generuje diagnostyczne wykresy (overview + fit per discharge).
"""
import sys
from pathlib import Path

import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from pha_lib import io, pipeline, export, plotting
from pha_lib.timetrace import integrate_energy_window
from pha_lib.discharges import detect_discharges
from pha_lib.fit import fit_discharge

INPUT = Path("/home/user/workspace/unitedc_62_239.txt")
OUT = ROOT / "output"
PLOTS = ROOT / "output" / "plots"

LINE_E = 6660.0
HALF_W = 60.0
N_POINTS = 3


def main():
    print(f"Loading {INPUT.name}...")
    shot = io.load_united_txt(INPUT, shot_id="united_62_239")
    print(f"  {shot.meta['n_frames']} frames, {shot.meta['n_bins']} bins, "
          f"frame_dt = {shot.frame_dt_s} s\n")

    # === ANALIZA: dwa kanały, osobne DataFrame'y ===
    results = pipeline.analyze_shot(
        shot,
        line_energy_eV=LINE_E,
        half_width_eV=HALF_W,
        n_points=N_POINTS,
        channels=(1, 2),
    )

    for ch, df in results.items():
        print(f"--- Channel {ch}: {len(df)} discharges ---")
        if not df.empty:
            cols = ["discharge_no", "start_frame", "finish_frame",
                    "A_f", "t_0_f", "tau_f", "C_f",
                    "A",   "t_0",   "tau",   "C",
                    "fit_success"]
            print(df[cols].to_string(index=False))
        print()

    # === EXPORT ===
    paths = export.save_results_parquet(results, OUT, prefix="results", also_csv=True)
    for ch, p in paths.items():
        print(f"Saved channel {ch} -> {p}")

    # === WYKRESY DIAGNOSTYCZNE ===
    # Odtwarzamy TimeTrace + Discharge (te same parametry co w pipeline)
    # i rysujemy. Pipeline zwraca tylko DataFrame, więc dla wykresów liczymy
    # to ponownie (tani re-compute, te same wejścia => te same wyniki).
    PLOTS.mkdir(parents=True, exist_ok=True)

    for ch_id, channel in shot.channels.items():
        trace = integrate_energy_window(channel, LINE_E, HALF_W)
        discharges = detect_discharges(trace, LINE_E)

        # Overview: cały trace z zaznaczonymi discharges
        fig, ax = plt.subplots(figsize=(11, 4))
        plotting.plot_timetrace_with_discharges(trace, discharges, ax=ax)
        out_overview = PLOTS / f"overview_ch{ch_id}.png"
        fig.tight_layout()
        fig.savefig(out_overview, dpi=120)
        plt.close(fig)
        print(f"Saved {out_overview}")

        # Per-discharge: fit
        for d in discharges:
            fit = fit_discharge(trace, d, n_points=N_POINTS)
            fig, ax = plt.subplots(figsize=(7, 4.5))
            plotting.plot_discharge_fit(trace, d, fit,
                                        n_points=N_POINTS, ax=ax)
            out_fit = PLOTS / f"fit_ch{ch_id}_d{d.discharge_no}.png"
            fig.tight_layout()
            fig.savefig(out_fit, dpi=120)
            plt.close(fig)
            print(f"Saved {out_fit}")


if __name__ == "__main__":
    main()