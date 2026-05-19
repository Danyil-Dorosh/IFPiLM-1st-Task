"""Zapis wynik\u00f3w do Parquet."""
from __future__ import annotations
from pathlib import Path
import pandas as pd


def save_results_parquet(
    df_by_channel: dict[int, pd.DataFrame],
    out_dir: str | Path,
    prefix: str = "results",
    also_csv: bool = False,
) -> dict[int, Path]:
    """Zapisz ka\u017cdy DataFrame do osobnego pliku parquet.

    Returns
    -------
    dict[int, Path]
        {channel_id -> \u015bcie\u017cka zapisanego pliku parquet}.
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
    """Odczyt pojedynczego pliku parquet z wynikami."""
    return pd.read_parquet(path)
