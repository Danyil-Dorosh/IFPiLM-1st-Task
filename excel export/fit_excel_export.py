"""
fit_excel_export.py
===================
Export sigma-clip fit results of injections into a coloured Excel sheet.

Design philosophy
-----------------
There is ONE public entry point (``export_fits_to_excel``), but internally the
work is split into small reusable "lego-block" helpers so each piece can be
tested and reused independently:

    _build_header_block()   -> systematic-configuration block (B2:I5)
    _build_table_headers()  -> main table column titles (row 8)
    _make_workbook()        -> fresh workbook + styled empty template

Stage B only exercises the empty template (titles/format), data + colours are
added in later stages.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from openpyxl import Workbook
from openpyxl.drawing.image import Image as XLImage
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import column_index_from_string
from openpyxl.worksheet.worksheet import Worksheet


# ===========================================================================
# Layout constants — single source of truth for where everything goes.
# ===========================================================================

# Main injections/fits table: ordered (column letter, header text).
TABLE_COLUMNS: list[tuple[str, str]] = [
    ("B", "Discharge"),
    ("C", "Inj #"),
    ("D", "A"),
    ("E", "tau"),
    ("F", "t_0"),
    ("G", "C_bg"),
    ("H", "A err"),
    ("I", "tau err"),
    ("J", "tau err rel [%]"),
    ("K", "red. chi2"),
    ("L", "pts used"),
    ("M", "Fit (log)"),
    ("N", "Fit (linear)"),
    ("O", "Start frame"),
    ("P", "Finish frame"),
]

HEADER_ROW = 8        # row that holds the main-table column titles
FIRST_DATA_ROW = 9    # first row where injection data begins

# Embedded fit-image size (pixels) and the matching row height (points).
IMG_W_PX = 260
IMG_H_PX = 170
IMG_ROW_HEIGHT_PT = IMG_H_PX * 0.75   # ~0.75 pt per pixel at 96 dpi

# tau_err_rel (%) -> fill colour for cells C..P of each injection row.
COLOR_GREEN = "C6EFCE"
COLOR_YELLOW = "FFEB9C"
COLOR_ORANGE = "FFD199"
COLOR_RED = "FFC7CE"

# Columns that get coloured per injection (C through P inclusive).
COLOR_COLUMNS = ["C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "P"]

# Reusable style objects.
_THIN = Side(style="thin", color="BFBFBF")
_BORDER = Border(left=_THIN, right=_THIN, top=_THIN, bottom=_THIN)
_TITLE_FONT = Font(bold=True, size=11)
_LABEL_FONT = Font(bold=True, size=9, color="404040")
_CENTER = Alignment(horizontal="center", vertical="center", wrap_text=True)
_HEADER_FILL = PatternFill("solid", fgColor="DDEBF7")   # light blue for table headers
_CONFIG_FILL = PatternFill("solid", fgColor="F2F2F2")   # light grey for config block


@dataclass
class SystematicConfig:
    """Values shown in the B2:I5 systematic-configuration block.

    Defaults mirror the constants used in the sigma-clip notebook and
    ``pha_lib.config.InjectionDetectionConfig``.
    """
    # Physics (B3:D5)
    line_e: float = 6660.0
    half_w: float = 60.0
    channel_id: int = 2
    # Injection detection (E3:F5)
    min_jump: float = 20.0
    threshold_factor: float = 3.0
    # Fit / sigma-clip (G3:I5)
    sigma_thresh: float = 1.0
    min_inliers: int = 4
    max_iter: int = 10


# ===========================================================================
# Lego-block helpers
# ===========================================================================

def _put(ws: Worksheet, coord: str, value, *, font=None, fill=None,
         align=_CENTER, border=_BORDER) -> None:
    """Write ``value`` into ``coord`` and apply the given styles in one shot."""
    cell = ws[coord]
    cell.value = value
    if font is not None:
        cell.font = font
    if fill is not None:
        cell.fill = fill
    if align is not None:
        cell.alignment = align
    if border is not None:
        cell.border = border


def _build_header_block(ws: Worksheet, cfg: SystematicConfig) -> None:
    """Write the systematic-configuration block into B2:I5.

    Row 2 = block title, row 3 = sub-section titles, row 4 = field labels,
    row 5 = values. Merged cells are intentionally NOT used.
    """
    # Block title spanning the top row of the block.
    _put(ws, "B2", "Systematic configuration", font=_TITLE_FONT, fill=_CONFIG_FILL)
    for col in "CDEFGHI":
        _put(ws, f"{col}2", None, fill=_CONFIG_FILL)

    # --- Physics sub-section (B3:D5) ---
    _put(ws, "B3", "Physics", font=_LABEL_FONT, fill=_CONFIG_FILL)
    _put(ws, "C3", None, fill=_CONFIG_FILL)
    _put(ws, "D3", None, fill=_CONFIG_FILL)
    _put(ws, "B4", "Line E [eV]", font=_LABEL_FONT)
    _put(ws, "C4", "Half-window [eV]", font=_LABEL_FONT)
    _put(ws, "D4", "Channel ID", font=_LABEL_FONT)
    _put(ws, "B5", cfg.line_e)
    _put(ws, "C5", cfg.half_w)
    _put(ws, "D5", cfg.channel_id)

    # --- Injection-detection sub-section (E3:F5) ---
    _put(ws, "E3", "Injection detection", font=_LABEL_FONT, fill=_CONFIG_FILL)
    _put(ws, "F3", None, fill=_CONFIG_FILL)
    _put(ws, "E4", "Min jump [eV]", font=_LABEL_FONT)
    _put(ws, "F4", "Threshold x median", font=_LABEL_FONT)
    _put(ws, "E5", cfg.min_jump)
    _put(ws, "F5", cfg.threshold_factor)

    # --- Fit / sigma-clip sub-section (G3:I5) ---
    _put(ws, "G3", "Fit (sigma-clip)", font=_LABEL_FONT, fill=_CONFIG_FILL)
    _put(ws, "H3", None, fill=_CONFIG_FILL)
    _put(ws, "I3", None, fill=_CONFIG_FILL)
    _put(ws, "G4", "Sigma thresh", font=_LABEL_FONT)
    _put(ws, "H4", "Min inliers", font=_LABEL_FONT)
    _put(ws, "I4", "Max iter", font=_LABEL_FONT)
    _put(ws, "G5", cfg.sigma_thresh)
    _put(ws, "H5", cfg.min_inliers)
    _put(ws, "I5", cfg.max_iter)


def _build_table_headers(ws: Worksheet) -> None:
    """Write the main-table column titles on ``HEADER_ROW``."""
    # Each column gets its title with the shared header style.
    for col_letter, title in TABLE_COLUMNS:
        _put(ws, f"{col_letter}{HEADER_ROW}", title,
             font=Font(bold=True, size=9), fill=_HEADER_FILL)


def _apply_column_widths(ws: Worksheet) -> None:
    """Set reasonable column widths so titles/values are readable."""
    # Widen the text-heavy columns; keep numeric ones compact.
    widths = {
        "B": 18, "C": 6, "D": 10, "E": 10, "F": 8, "G": 9, "H": 10,
        "I": 10, "J": 14, "K": 10, "L": 9, "M": 38, "N": 38, "O": 11, "P": 12,
    }
    for col, width in widths.items():
        ws.column_dimensions[col].width = width


# ===========================================================================
# Data-row lego-blocks (Stage C onward)
# ===========================================================================

def _save_ax_image(ax, yscale: str, path: Path) -> Path:
    """Render the user's ``ax`` to a PNG at the requested y-scale.

    The package "does nothing" with the plot except snapshot it, so we only
    toggle the y-scale, save, then restore the previous scale to avoid
    permanently mutating the caller's figure.
    """
    fig = ax.figure
    prev_scale = ax.get_yscale()          # remember so we can restore it
    ax.set_yscale(yscale)
    fig.savefig(path, dpi=80, bbox_inches="tight")
    ax.set_yscale(prev_scale)             # leave caller's ax untouched
    return path


def _embed_image(ws: Worksheet, cell: str, path: Path) -> None:
    """Anchor a fixed-size PNG at ``cell`` (top-left corner)."""
    img = XLImage(str(path))
    img.width = IMG_W_PX
    img.height = IMG_H_PX
    ws.add_image(img, cell)


def _fmt_num(value) -> object:
    """Return a finite float for Excel, or '' for NaN/None so cells stay clean."""
    if value is None:
        return ""
    try:
        f = float(value)
    except (TypeError, ValueError):
        return ""
    return f if f == f else ""   # f == f is False only for NaN


def _fill_for_tau_err_rel(rel_pct) -> PatternFill | None:
    """Pick the row fill from tau error (in %): green/yellow/orange/red.

    Thresholds (per spec): <7 green, (7,12] yellow, (12,25] orange, >25 red.
    Returns None for NaN/None so failed fits stay uncoloured.
    """
    # guard against missing or NaN values (e.g. fits where errors failed)
    if rel_pct is None:
        return None
    try:
        r = float(rel_pct)
    except (TypeError, ValueError):
        return None
    if r != r:                       # NaN check
        return None
    # apply the banded thresholds from low to high error
    if r < 7:
        color = COLOR_GREEN
    elif r <= 12:
        color = COLOR_YELLOW
    elif r <= 25:
        color = COLOR_ORANGE
    else:
        color = COLOR_RED
    return PatternFill("solid", fgColor=color)


def _write_injection_row(
    ws: Worksheet,
    row: int,
    discharge_id: str,
    injection,
    result: dict,
    img_dir: Path,
    colorize: bool = False,
) -> None:
    """Write one injection's data + fit images into ``row``.

    Column map (see TABLE_COLUMNS): B discharge, C inj#, D..K fit params,
    L pts used, M/N fit images (log/linear), O/P start/finish frame.
    """
    # --- identifiers ---
    _put(ws, f"B{row}", discharge_id, font=Font(size=9))
    _put(ws, f"C{row}", injection.injection_no, font=Font(size=9))

    # --- fit coefficients (D..K), order per documentation ---
    _put(ws, f"D{row}", _fmt_num(result.get("A")))
    _put(ws, f"E{row}", _fmt_num(result.get("tau")))
    _put(ws, f"F{row}", _fmt_num(result.get("t_0")))
    _put(ws, f"G{row}", _fmt_num(result.get("C_bg")))
    _put(ws, f"H{row}", _fmt_num(result.get("A_err")))
    _put(ws, f"I{row}", _fmt_num(result.get("tau_err")))
    # tau_err_rel stored as percent for readability
    rel = result.get("tau_err_rel")
    _put(ws, f"J{row}", _fmt_num(rel * 100 if rel is not None and rel == rel else rel))
    _put(ws, f"K{row}", _fmt_num(result.get("reduced_chi2")))

    # --- points used "inliers/total" ---
    n_in = result.get("n_inliers", "")
    n_tot = result.get("n_total", "")
    _put(ws, f"L{row}", f"{n_in}/{n_tot}")

    # --- frames (O/P) ---
    _put(ws, f"O{row}", injection.start_frame, font=Font(size=9))
    _put(ws, f"P{row}", injection.finish_frame, font=Font(size=9))

    # --- colour cells C..P by tau error (Stage F/G) ---
    if colorize:
        # tau_err_rel is a fraction in the result; convert to percent for banding
        fill = _fill_for_tau_err_rel(rel * 100 if rel is not None and rel == rel else None)
        if fill is not None:
            for col in COLOR_COLUMNS:
                ws[f"{col}{row}"].fill = fill

    # --- fit images (M log, N linear) ---
    # Only embed when the caller supplied an ax via result["_ax"].
    ax = result.get("_ax")
    if ax is not None:
        ws.row_dimensions[row].height = IMG_ROW_HEIGHT_PT
        log_png = _save_ax_image(ax, "log", img_dir / f"{discharge_id}_{injection.injection_no}_log.png")
        lin_png = _save_ax_image(ax, "linear", img_dir / f"{discharge_id}_{injection.injection_no}_lin.png")
        _embed_image(ws, f"M{row}", log_png)
        _embed_image(ws, f"N{row}", lin_png)


def _make_workbook(cfg: SystematicConfig) -> Workbook:
    """Build a fresh workbook with the header block and table titles only."""
    wb = Workbook()
    ws = wb.active
    ws.title = "Fits"
    _build_header_block(ws, cfg)
    _build_table_headers(ws)
    _apply_column_widths(ws)
    return wb


# ===========================================================================
# Public entry point
# ===========================================================================

def export_empty_template(
    out_dir: str | Path = "output/excel_export",
    *,
    filename: str = "fits_empty_template.xlsx",
    config: SystematicConfig | None = None,
) -> Path:
    """Stage B: write an EMPTY sheet (titles/format only) for layout review.

    Parameters
    ----------
    out_dir : output folder, created if missing.
    filename : output .xlsx file name.
    config : systematic-configuration values for the header block.

    Returns the path to the written file.
    """
    cfg = config or SystematicConfig()
    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)  # ensure folder exists
    wb = _make_workbook(cfg)
    file_path = out_path / filename
    wb.save(file_path)
    return file_path


def export_fits_to_excel(
    rows: list[dict],
    out_dir: str | Path = "output/excel_export",
    *,
    filename: str = "fits.xlsx",
    config: SystematicConfig | None = None,
    colorize: bool = False,
) -> Path:
    """Export injection fits to a coloured-ready Excel sheet (Stage C onward).

    Parameters
    ----------
    rows : list of per-injection dicts, each with keys:
        "discharge_id" : str               (or "discharge": Discharge object)
        "injection"    : Injection object  (.injection_no, .start_frame, .finish_frame)
        "result"       : dict returned by fit_sigma_clip
        "ax"           : matplotlib Axes to snapshot (optional)
        Rows are written top-to-bottom in the given order.
    out_dir : output folder (created if missing). Fit images go in a
        "_fit_images" sub-folder.
    filename : output .xlsx file name.
    config : systematic-configuration values for the header block.

    Returns the path to the written file.
    """
    cfg = config or SystematicConfig()
    out_path = Path(out_dir)
    img_dir = out_path / "_fit_images"
    out_path.mkdir(parents=True, exist_ok=True)
    img_dir.mkdir(parents=True, exist_ok=True)

    wb = _make_workbook(cfg)
    ws = wb.active

    # Write each injection on its own row, starting at FIRST_DATA_ROW.
    for offset, entry in enumerate(rows):
        excel_row = FIRST_DATA_ROW + offset
        # Resolve the discharge id from either an explicit string or a Discharge.
        discharge_id = entry.get("discharge_id")
        if discharge_id is None and entry.get("discharge") is not None:
            discharge_id = entry["discharge"].discharge_id

        # Pass the ax through the result dict so the row writer can snapshot it.
        result = dict(entry["result"])      # shallow copy; don't mutate caller's dict
        result["_ax"] = entry.get("ax")

        _write_injection_row(
            ws, excel_row, discharge_id, entry["injection"], result, img_dir,
            colorize=colorize,
        )

    file_path = out_path / filename
    wb.save(file_path)
    return file_path

