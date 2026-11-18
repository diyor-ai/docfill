"""PDF text extraction + rule-based field parsing.

Rules live in a YAML file, so a new document type needs no code change.
Each field has one or more regex patterns; the first that matches wins.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

import pdfplumber
import yaml

DATE_FORMATS = ("%Y-%m-%d", "%d %b %Y", "%d %B %Y", "%d.%m.%Y", "%m/%d/%Y")


@dataclass
class Result:
    source: str
    values: dict = field(default_factory=dict)
    missing: list = field(default_factory=list)


def read_pdf_text(path: Path) -> str:
    with pdfplumber.open(path) as pdf:
        return "\n".join((page.extract_text() or "") for page in pdf.pages)


def load_rules(path: Path) -> dict:
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict) or "fields" not in data:
        raise ValueError(f"{path}: config must contain a 'fields' mapping")
    return data["fields"]


def parse_money(raw: str) -> float:
    """'1,234.50' -> 1234.5 ; '1.234,50' -> 1234.5"""
    s = raw.strip().replace(" ", "")
    if "," in s and "." in s:
        if s.rfind(",") > s.rfind("."):
            s = s.replace(".", "").replace(",", ".")
        else:
            s = s.replace(",", "")
    elif "," in s:
        s = s.replace(",", ".") if re.search(r",\d{1,2}$", s) else s.replace(",", "")
    return float(s)


def parse_date(raw: str) -> str:
    raw = raw.strip()
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(raw, fmt).date().isoformat()
        except ValueError:
            continue
    raise ValueError(f"unrecognised date: {raw!r}")


CONVERTERS = {"str": str.strip, "money": parse_money, "date": parse_date}


def extract_fields(text: str, rules: dict) -> tuple[dict, list]:
    values, missing = {}, []
    for name, spec in rules.items():
        patterns = spec["patterns"] if isinstance(spec["patterns"], list) else [spec["patterns"]]
        convert = CONVERTERS[spec.get("type", "str")]
        for pat in patterns:
            m = re.search(pat, text, flags=re.IGNORECASE | re.MULTILINE)
            if m:
                try:
                    values[name] = convert(m.group("value"))
                    break
                except ValueError:
                    continue
        else:
            values[name] = None
            if spec.get("required", True):
                missing.append(name)
    return values, missing


def process_pdf(path: Path, rules: dict) -> Result:
    text = read_pdf_text(path)
    values, missing = extract_fields(text, rules)
    return Result(source=Path(path).name, values=values, missing=missing)
