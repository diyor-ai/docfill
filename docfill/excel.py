"""Write one summary row per processed PDF."""
from __future__ import annotations

from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill


def write_summary(results, field_names, out_path: Path) -> None:
    wb = Workbook()
    ws = wb.active
    ws.title = "summary"
    headers = ["source_file", *field_names, "missing_fields"]
    ws.append(headers)
    for cell in ws[1]:
        cell.font = Font(bold=True)
    flag = PatternFill("solid", fgColor="FFF2CC")
    for r in results:
        ws.append([r.source, *[r.values.get(n) for n in field_names], ", ".join(r.missing)])
        if r.missing:
            for cell in ws[ws.max_row]:
                cell.fill = flag
    for col in ws.columns:
        ws.column_dimensions[col[0].column_letter].width = max(len(str(c.value or "")) for c in col) + 2
    ws.freeze_panes = "A2"
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    wb.save(out_path)
