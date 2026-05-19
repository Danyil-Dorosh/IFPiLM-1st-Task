"""I/O \u2014 czytanie wej\u015bciowych plik\u00f3w tekstowych do obiektu Shot."""
from __future__ import annotations
from pathlib import Path
from typing import Iterable, Optional
import re
import numpy as np

from .model import Shot, EnergyChannelData


DEFAULT_CHANNELS = (1, 2)


# ---------- united training file --------------------------------------------

_FRAME_MARKER = re.compile(r"^(\d+)-\s*$")
_HEADER_PREFIX = ("E1[eV]", "E1")


def load_united_txt(
    path: str | Path,
    shot_id: str = "unknown",
    channels: Iterable[int] = DEFAULT_CHANNELS,
    frame_dt_s: float = 0.05,
) -> Shot:
    """Za\u0142aduj zunifikowany plik treningowy z wieloma ramkami.

    Format:
        62-
        E1[eV] Events1 E2[eV] Events2
        10.000 0 10.000 0
        ...
        63-
        E1[eV] Events1 E2[eV] Events2
        ...
    """
    path = Path(path)
    frames_data: dict[int, np.ndarray] = {}
    current_frame: Optional[int] = None
    current_rows: list[list[float]] = []

    def _flush():
        if current_frame is not None and current_rows:
            frames_data[current_frame] = np.asarray(current_rows, dtype=float)

    with path.open() as f:
        for raw in f:
            s = raw.strip()
            if not s:
                continue
            m = _FRAME_MARKER.match(s)
            if m:
                _flush()
                current_frame = int(m.group(1))
                current_rows = []
                continue
            if s.startswith(_HEADER_PREFIX):
                continue
            parts = s.split()
            if len(parts) < 4:
                continue
            try:
                current_rows.append([float(p) for p in parts[:4]])
            except ValueError:
                continue
    _flush()

    if not frames_data:
        raise ValueError(f"No frames parsed from {path}")

    return _build_shot_from_frame_dict(
        frames_data, shot_id=shot_id, channels=channels,
        frame_dt_s=frame_dt_s, source=str(path),
    )


# ---------- folder test_<n>.txt (orig 9-column format) ----------------------

_TEST_FILE_RE = re.compile(r"test_(\d+).*\.txt$", re.IGNORECASE)


def load_test_folder(
    folder: str | Path,
    shot_id: str = "unknown",
    channels: Iterable[int] = DEFAULT_CHANNELS,
    frame_dt_s: float = 0.05,
) -> Shot:
    """Za\u0142aduj folder z plikami test_<frame_no>.txt (orig 9-kol format).

    Plik test_<n>.txt:
        Channel E1[eV] Events1 E2[eV] Events2 E3[eV] Events3 E4[eV] Events4
        0 10.000 0 10.000 0 10.000 0 10.000 0
        ...
    """
    folder = Path(folder)
    files = sorted(folder.glob("test_*.txt"))
    if not files:
        raise FileNotFoundError(f"No test_<n>.txt files in {folder}")

    frames_data: dict[int, np.ndarray] = {}
    for fp in files:
        m = _TEST_FILE_RE.search(fp.name)
        if not m:
            continue
        frame_no = int(m.group(1))
        rows: list[list[float]] = []
        with fp.open() as f:
            for raw in f:
                s = raw.strip()
                if not s or s.startswith("Channel"):
                    continue
                parts = s.split()
                if len(parts) < 5:
                    continue
                try:
                    rows.append([float(parts[1]), float(parts[2]),
                                 float(parts[3]), float(parts[4])])
                except ValueError:
                    continue
        if rows:
            frames_data[frame_no] = np.asarray(rows, dtype=float)

    return _build_shot_from_frame_dict(
        frames_data, shot_id=shot_id, channels=channels,
        frame_dt_s=frame_dt_s, source=str(folder),
    )


# ---------- placeholder for binary .pha -------------------------------------

def load_pha(path: str | Path, shot_id: str = "unknown") -> Shot:  # pragma: no cover
    """Placeholder for binary .pha loader (final production format).

    When the format spec is available, this is the only function we add.
    The rest of the pipeline is unchanged.
    """
    raise NotImplementedError("Binary .pha loader not implemented yet.")


# ---------- shared helper ---------------------------------------------------

def _build_shot_from_frame_dict(
    frames_data: dict[int, np.ndarray],
    shot_id: str,
    channels: Iterable[int],
    frame_dt_s: float,
    source: str,
) -> Shot:
    frame_numbers = np.array(sorted(frames_data.keys()), dtype=int)
    sample = frames_data[int(frame_numbers[0])]
    n_bins = sample.shape[0]

    for fn in frame_numbers:
        if frames_data[int(fn)].shape[0] != n_bins:
            raise ValueError(
                f"Frame {fn} has {frames_data[int(fn)].shape[0]} bins, "
                f"expected {n_bins}."
            )

    energy_eV = sample[:, 0].copy()

    channels_data: dict[int, EnergyChannelData] = {}
    for ch in channels:
        if ch == 1:
            counts_col = 1
        elif ch == 2:
            counts_col = 3
        else:
            raise ValueError(
                f"Channel {ch} not in this file format. "
                f"Currently only channels 1 and 2 are supported."
            )
        spectra = np.empty((len(frame_numbers), n_bins), dtype=float)
        for i, fn in enumerate(frame_numbers):
            spectra[i] = frames_data[int(fn)][:, counts_col]
        channels_data[ch] = EnergyChannelData(
            channel_id=ch,
            frame_numbers=frame_numbers,
            energy_eV=energy_eV,
            spectra=spectra,
        )

    return Shot(
        shot_id=shot_id,
        channels=channels_data,
        frame_dt_s=frame_dt_s,
        meta={"source": source, "n_frames": len(frame_numbers), "n_bins": n_bins},
    )
