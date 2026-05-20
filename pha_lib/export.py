"""Zapis wyników na dysk.

Główny format: Parquet (zachowuje typy, jest szybki, kolumnowy — idealny
do wyników analitycznych). Dodatkowo opcjonalnie CSV (dla podglądu w Excelu).
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
    """Zapisz każdy DataFrame do osobnego pliku parquet.

    Parameters
    ----------
    df_by_channel : dict[int, pd.DataFrame]
        Output z `pipeline.analyze_discharge()`.
    out_dir : path
        Folder na wyniki (zostanie utworzony jeśli nie istnieje).
    prefix : str
        Prefix nazwy pliku, domyślnie "results".
    also_csv : bool
        Jeśli True, zapisuj też wersję CSV obok parquet.

    Returns
    -------
    dict[int, Path]
        Mapowanie channel_id -> ścieżka zapisanego pliku parquet.
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
