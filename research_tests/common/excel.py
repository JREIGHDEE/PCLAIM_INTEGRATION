"""Results workbooks: a raw-data sheet plus summary sheets per test, styled
like the OCR comparison workbook (dark blue header) so the tables can be
copied into Chapter 5.

A sheet is a dict:
  {"name": "Summary", "title": "Table - ...", "headers": [...],
   "rows": [[...], ...], "notes": ["...", ...], "bold_last": False}

Every test also keeps its summary sheets as JSON (save_summary), and
results.py puts all of them into outputs/chapter5_results.xlsx.
"""
import json
from datetime import datetime

from openpyxl import Workbook, load_workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

HEADER_FILL = PatternFill("solid", fgColor="1E3A8A")
HEADER_FONT = Font(bold=True, color="FFFFFF")
TITLE_FONT = Font(bold=True, size=12)
NOTE_FONT = Font(italic=True, color="475569")
THIN = Side(style="thin", color="CBD5E1")
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)


def _cell_value(value):
    if isinstance(value, (list, tuple, set)):
        return ", ".join(str(v) for v in value)
    if isinstance(value, dict):
        return json.dumps(value, ensure_ascii=False)
    return value


def _write_sheet(ws, sheet):
    row = 1
    if sheet.get("title"):
        ws.cell(row=row, column=1, value=sheet["title"]).font = TITLE_FONT
        row += 2
    header_row = row
    headers = sheet.get("headers") or []
    for col, name in enumerate(headers, start=1):
        cell = ws.cell(row=row, column=col, value=name)
        cell.fill, cell.font, cell.border = HEADER_FILL, HEADER_FONT, BORDER
        cell.alignment = Alignment(wrap_text=True, vertical="center", horizontal="center")
    rows = sheet.get("rows") or []
    for r, values in enumerate(rows, start=row + 1):
        for col, value in enumerate(values, start=1):
            cell = ws.cell(row=r, column=col, value=_cell_value(value))
            cell.border = BORDER
            if isinstance(value, float):
                cell.number_format = "0.00" if abs(value) >= 1 or value == 0 else "0.0000"
        if sheet.get("bold_last") and r == row + len(rows):
            for col in range(1, len(values) + 1):
                ws.cell(row=r, column=col).font = Font(bold=True)
    row = row + len(rows) + 2
    for note in sheet.get("notes") or []:
        ws.cell(row=row, column=1, value=note).font = NOTE_FONT
        row += 1
    widths = sheet.get("widths")
    for col, name in enumerate(headers, start=1):
        longest = max([len(str(name))] + [len(str(_cell_value(v[col - 1]) or "")) for v in rows[:300]
                                          if col - 1 < len(v)])
        width = widths[col - 1] if widths and col - 1 < len(widths) else min(48, max(9, longest + 2))
        ws.column_dimensions[get_column_letter(col)].width = width
    ws.row_dimensions[header_row].height = 32
    if headers:
        ws.freeze_panes = ws.cell(row=header_row + 1, column=1)


def safe_name(name, taken=()):
    name = "".join(ch for ch in str(name) if ch not in '[]:*?/\\')[:31] or "Sheet"
    base, n = name, 2
    while name in taken:
        suffix = f" ({n})"
        name = base[:31 - len(suffix)] + suffix
        n += 1
    return name


def write_workbook(path, sheets):
    """Write the sheets (in order) to path, replacing the file."""
    wb = Workbook()
    wb.remove(wb.active)
    taken = set()
    for sheet in sheets:
        name = safe_name(sheet["name"], taken)
        taken.add(name)
        _write_sheet(wb.create_sheet(name), sheet)
    path.parent.mkdir(parents=True, exist_ok=True)
    wb.save(path)
    return path


def save_summary(folder, test_key, title, sheets, extra=None):
    """Keep this test's summary sheets for results.py (summary.json)."""
    record = {"test": test_key, "title": title, "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
              "sheets": sheets, **(extra or {})}
    path = folder / "summary.json"
    path.write_text(json.dumps(record, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    return path


def read_rows(path, sheet_name=None, header_row=None, formulas_as_text=False):
    """[{header: value}, ...] from a sheet. header_row: the row of the
    headers (found automatically when None: the first row with 2+ text
    cells). formulas_as_text: a cell Excel keeps as a formula (an OCR
    reading that began with "=") gives its text instead of its (missing)
    computed value."""
    wb = load_workbook(path, read_only=True, data_only=not formulas_as_text)
    ws = wb[sheet_name] if sheet_name else wb.worksheets[0]
    rows = list(ws.iter_rows(values_only=True))
    wb.close()
    if header_row is None:
        header_row = next((i for i, r in enumerate(rows)
                           if sum(isinstance(v, str) and v.strip() != "" for v in r) >= 2), 0)
    headers = [str(h).strip() if h is not None else "" for h in rows[header_row]] if rows else []
    out = []
    for r in rows[header_row + 1:]:
        if not any(v not in (None, "") for v in r):
            continue
        out.append({h: (r[i] if i < len(r) else None) for i, h in enumerate(headers) if h})
    return out
