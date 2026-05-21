"""Save analysis results to disk.

Main format: Parquet (preserves types, fast, columnar — suitable
for analytical results). Optionally also save CSV for quick inspection.
"""
from __future__ import annotations
from pathlib import Path
from typing import Optional
import pandas as pd


def save_results_parquet(
    df_by_channel: dict[int, pd.DataFrame],
    out_dir: str | Path,
    prefix: str = "results",
    also_csv: bool = False,
) -> dict[int, Path]:
    """Write each DataFrame to a separate parquet file.

    Parameters
    ----------
    df_by_channel : dict[int, pd.DataFrame]
        Output from `pipeline.analyze_discharge()`.
    out_dir : path
        Directory to write results to (created if missing).
    prefix : str
        File name prefix, default "results".
    also_csv : bool
        If True, also write a CSV copy next to the parquet file.

    Returns
    -------
    dict[int, Path]
        Mapping channel_id -> path of the written parquet file.
    """
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    written: dict[int, Path] = {}
    for ch, df in df_by_channel.items():
        path_pq = out_dir / f"{prefix}_channel{ch}.parquet"
        df.to_parquet(path_pq, index=False)
        written[ch] = path_pq
        if also_csv:
            df.to_csv(out_dir / f"{prefix}_channel{ch}.csv", index=False)

    return written


def load_results_parquet(path: str | Path) -> pd.DataFrame:
    """Read a single parquet results file."""
    return pd.read_parquet(path)
