"""End-to-end demo na unitedc_62_239.txt.

Wczytuje shot, analizuje OSOBNO ka\u017cdy kana\u0142, zapisuje 2 osobne Parquet'y.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from pha_lib import io, pipeline, export

INPUT = Path("/home/user/workspace/unitedc_62_239.txt")
OUT = ROOT / "output"


def main():
    print(f"Loading {INPUT.name}...")
    shot = io.load_united_txt(INPUT, shot_id="united_62_239")
    print(f"  {shot.meta['n_frames']} frames, {shot.meta['n_bins']} bins, "
          f"frame_dt = {shot.frame_dt_s} s\n")

    results = pipeline.analyze_shot(
        shot, line_energy_eV=6660.0, half_width_eV=50.0, n_points=3,
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

    paths = export.save_results_parquet(results, OUT, prefix="results", also_csv=True)
    for ch, p in paths.items():
        print(f"Saved channel {ch} -> {p}")


if __name__ == "__main__":
    main()
