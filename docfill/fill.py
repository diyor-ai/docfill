"""Fill a .docx template: replaces {{field}} placeholders in paragraphs and tables."""
from __future__ import annotations

import re
from pathlib import Path

from docx import Document

PLACEHOLDER = re.compile(r"\{\{\s*(\w+)\s*\}\}")


def _fmt(value) -> str:
    if value is None:
        return "[MISSING]"
    if isinstance(value, float):
        return f"{value:,.2f}"
    return str(value)


def _fill_paragraph(par, values: dict) -> None:
    text = par.text
    if "{{" not in text:
        return
    new = PLACEHOLDER.sub(lambda m: _fmt(values.get(m.group(1))), text)
    if new == text:
        return
    # Placeholders can be split across runs by Word; rebuild text in the first run.
    # Formatting of the first run is kept; mixed formatting inside one paragraph is not.
    if par.runs:
        par.runs[0].text = new
        for run in par.runs[1:]:
            run.text = ""
    else:
        par.add_run(new)


def _iter_paragraphs(doc):
    yield from doc.paragraphs
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                yield from cell.paragraphs
    for section in doc.sections:
        yield from section.header.paragraphs
        yield from section.footer.paragraphs


def fill_template(template: Path, values: dict, out_path: Path) -> list:
    """Fill and save. Returns placeholders in the template with no matching field."""
    doc = Document(str(template))
    unknown = set()
    for par in _iter_paragraphs(doc):
        for m in PLACEHOLDER.finditer(par.text):
            if m.group(1) not in values:
                unknown.add(m.group(1))
        _fill_paragraph(par, values)
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(out_path))
    return sorted(unknown)
