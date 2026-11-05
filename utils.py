"""utils.py - HTML helpers, Excel/CSV export and Excel upload parsing."""
from __future__ import annotations

import html
import io
import inspect
import re

import numpy as np
import pandas as pd

import data as D
from calculations import METRICS, REQUIRED_KEYS, fmt_value, validate_raw


# --------------------------------------------------------------------------- #
# Streamlit version compatibility
# --------------------------------------------------------------------------- #
def stretch_kwargs(fn) -> dict:
    """Return the 'full width' kwargs supported by this Streamlit version.

    Newer Streamlit uses width="stretch"; older uses use_container_width=True.
    """
    try:
        params = inspect.signature(fn).parameters
    except (TypeError, ValueError):
        return {"use_container_width": True}
    return {"width": "stretch"} if "width" in params else {"use_container_width": True}


# --------------------------------------------------------------------------- #
# HTML building blocks
# --------------------------------------------------------------------------- #
def kpi_card(label: str, value: str, delta: str = "", direction: str = "flat", sub: str = "", tip: str = "", arrow: str = "") -> str:
    """direction = colour tone (up=green, down=red, flat=grey); arrow = glyph for the sign of the change."""
    arrow = {"up": "\u25b2 ", "down": "\u25bc ", "": ""}[arrow]
    delta_html = f'<div class="kpi-delta {direction}">{arrow}{html.escape(delta)}</div>' if delta else '<div class="kpi-delta flat">&nbsp;</div>'
    return (f'<div class="kpi" title="{html.escape(tip, quote=True)}"><div class="kpi-label">{html.escape(label)}</div>'
            f'<div class="kpi-value">{html.escape(value)}</div>{delta_html}'
            f'<div class="kpi-sub">{html.escape(sub)}</div></div>')


def html_table(df: pd.DataFrame, link_cols: tuple[str, ...] = (), max_height: int | None = None) -> str:
    """Render a DataFrame of strings as a themed HTML table (index is shown as first column)."""
    head = "".join(f"<th>{html.escape(str(c))}</th>" for c in [df.index.name or ""] + list(df.columns))
    body = []
    for idx, row in df.iterrows():
        cells = [f"<td>{html.escape(str(idx))}</td>"]
        for c, v in row.items():
            s = "" if v is None else str(v)
            if c in link_cols and s.startswith("http"):
                cells.append(f'<td><a href="{html.escape(s)}" target="_blank" rel="noopener">open</a></td>')
                continue
            cls = "na" if s == "n/a" else ("neg" if s.startswith("-") or s.startswith("\u20b9-") else "")
            cells.append(f'<td class="{cls}">{html.escape(s)}</td>')
        body.append("<tr>" + "".join(cells) + "</tr>")
    style = f' style="max-height:{max_height}px;overflow-y:auto"' if max_height else ""
    return f'<div class="tbl-wrap"{style}><table class="fin"><thead><tr>{head}</tr></thead><tbody>{"".join(body)}</tbody></table></div>'


def metrics_table(d: pd.DataFrame, keys: list[str]) -> pd.DataFrame:
    """Rows = metrics, columns = FY, values formatted with units."""
    out = pd.DataFrame({fy: [fmt_value(d.loc[fy, k], METRICS[k].unit, 2 if METRICS[k].unit != "cr" else 0) for k in keys] for fy in d.index},
                       index=[METRICS[k].label for k in keys])
    out.index.name = "Metric"
    return out


# --------------------------------------------------------------------------- #
# Export
# --------------------------------------------------------------------------- #
def metrics_long(frames_metrics: dict[str, pd.DataFrame]) -> pd.DataFrame:
    rows = []
    for basis, d in frames_metrics.items():
        for k, m in METRICS.items():
            for fy in d.index:
                v = d.loc[fy, k]
                rows.append({"basis": basis, "fy": fy, "metric_key": k, "metric": m.label, "unit": {"cr": "INR crore", "%": "%", "x": "x", "INR": "INR"}[m.unit],
                             "value": None if pd.isna(v) else round(float(v), 4), "formula": m.formula,
                             "status": "missing" if pd.isna(v) else "ok"})
    return pd.DataFrame(rows)


def raw_sheet(df: pd.DataFrame) -> pd.DataFrame:
    """Raw frame -> upload-template layout (line_item, description, unit, FY columns)."""
    t = df.T.copy()
    t.insert(0, "unit", [D.LINE_ITEMS.get(k, ("", "", ""))[2] for k in t.index])
    t.insert(0, "description", [D.LINE_ITEMS.get(k, (k, "", ""))[0] for k in t.index])
    t.index.name = "line_item"
    return t.reset_index()


def _autowidth(ws):
    for col in ws.columns:
        width = max((len(str(c.value)) for c in col if c.value is not None), default=8)
        ws.column_dimensions[col[0].column_letter].width = min(max(10, width + 2), 70)


def build_excel(raw: dict[str, pd.DataFrame], metrics: dict[str, pd.DataFrame], sources: pd.DataFrame,
                fys: list[str] | None = None) -> bytes:
    """Multi-sheet workbook: metrics, raw line items (re-uploadable), sources, definitions."""
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as xw:
        pd.DataFrame({"Britannia Industries Ltd. - five-year financial dataset": [
            "Units: INR crore unless stated.", "Sheets 'Raw_<basis>' use the same layout accepted by the dashboard's Excel upload.",
            "Missing values are blank (shown as n/a in the dashboard).", "Consolidated = Britannia + subsidiaries, associates & JV; Standalone = Britannia Industries Ltd. only."]}).to_excel(xw, sheet_name="README", index=False)
        for basis, d in metrics.items():
            dd = d if not fys else d.loc[[f for f in d.index if f in fys]]
            t = dd[list(METRICS)].T
            t.insert(0, "formula", [METRICS[k].formula for k in t.index])
            t.insert(0, "unit", [METRICS[k].unit for k in t.index])
            t.insert(0, "metric", [METRICS[k].label for k in t.index])
            t.index.name = "key"
            t.reset_index().to_excel(xw, sheet_name=f"Metrics_{basis}", index=False)
        for basis, df in raw.items():
            dd = df if not fys else df.loc[[f for f in df.index if f in fys]]
            raw_sheet(dd).to_excel(xw, sheet_name=f"Raw_{basis}", index=False)
        sources.to_excel(xw, sheet_name="Sources", index=False)
        pd.DataFrame([{"metric": m.label, "unit": m.unit, "category": m.category, "formula": m.formula, "note": m.note} for m in METRICS.values()]
                     ).to_excel(xw, sheet_name="Definitions", index=False)
        for ws in xw.book.worksheets:
            _autowidth(ws)
            ws.freeze_panes = "B2"
    return buf.getvalue()


# --------------------------------------------------------------------------- #
# Upload
# --------------------------------------------------------------------------- #
def _norm_fy(c) -> str | None:
    m = re.search(r"(\d{4})", str(c))
    return f"FY{m.group(1)}" if m and 1990 < int(m.group(1)) < 2100 else None


def parse_upload(file) -> tuple[dict[str, pd.DataFrame], list[str]]:
    """Parse an uploaded workbook (same layout as the export). Raises ValueError on unusable files."""
    try:
        sheets = pd.read_excel(file, sheet_name=None, engine="openpyxl")
    except Exception as exc:                       # corrupt / wrong format
        raise ValueError(f"Could not read the Excel file: {exc}") from exc
    frames, notes = {}, []
    for name, df in sheets.items():
        low = name.lower()
        basis = "Consolidated" if "consol" in low else "Standalone" if "standalone" in low else None
        if basis is None or low.startswith("metrics"):
            continue
        df.columns = [str(c).strip() for c in df.columns]
        key_col = next((c for c in df.columns if c.lower() in ("line_item", "key")), None)
        if key_col is None:
            raise ValueError(f"Sheet '{name}' needs a 'line_item' column.")
        fy_cols = {c: _norm_fy(c) for c in df.columns if _norm_fy(c)}
        if not fy_cols:
            raise ValueError(f"Sheet '{name}' has no FY columns such as 'FY2026'.")
        body = df.set_index(df[key_col].astype(str).str.strip())[list(fy_cols)].apply(pd.to_numeric, errors="coerce")
        body.columns = list(fy_cols.values())
        t = body.T.sort_index()
        for k in D.LINE_ITEMS:
            if k not in t:
                t[k] = np.nan
                notes.append(f"{basis}: '{k}' not supplied - marked missing.")
        t = t[[k for k in D.LINE_ITEMS]]
        t.index.name = "FY"
        if t[[k for k in REQUIRED_KEYS]].isna().all(axis=None):
            raise ValueError(f"Sheet '{name}' contains none of the required items: {', '.join(REQUIRED_KEYS)}.")
        frames[basis] = t
        notes += [f"{basis}: {w}" for w in validate_raw(t)]
    if not frames:
        raise ValueError("No sheet named 'Consolidated' or 'Standalone' was found.")
    return frames, notes
