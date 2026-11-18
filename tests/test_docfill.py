import subprocess
import sys
from pathlib import Path

import pytest
from docx import Document

from docfill.extract import extract_fields, load_rules, parse_date, parse_money, process_pdf
from docfill.fill import fill_template

ROOT = Path(__file__).resolve().parents[1]
RULES = load_rules(ROOT / "config" / "invoice.yml")


@pytest.fixture(scope="session", autouse=True)
def samples():
    subprocess.run([sys.executable, str(ROOT / "samples" / "make_samples.py")], check=True)


@pytest.mark.parametrize("raw,expected", [
    ("1,234.50", 1234.5), ("1.234,50", 1234.5), ("595.00", 595.0), ("80,5", 80.5), ("1,200", 1200.0),
])
def test_parse_money(raw, expected):
    assert parse_money(raw) == expected


@pytest.mark.parametrize("raw,expected", [
    ("2026-11-02", "2026-11-02"), ("05 Nov 2026", "2026-11-05"), ("05.11.2026", "2026-11-05"),
])
def test_parse_date(raw, expected):
    assert parse_date(raw) == expected


def test_parse_date_rejects_garbage():
    with pytest.raises(ValueError):
        parse_date("next tuesday")


def test_two_layouts_extract_same_fields():
    a = process_pdf(ROOT / "samples/pdf/invoice_001.pdf", RULES)
    b = process_pdf(ROOT / "samples/pdf/invoice_002.pdf", RULES)
    assert a.missing == [] and b.missing == []
    assert a.values["total"] == 1200.0 and a.values["invoice_date"] == "2026-11-02"
    assert b.values["invoice_number"] == "B-778" and b.values["invoice_date"] == "2026-11-05"


def test_missing_required_field_is_reported_not_invented():
    r = process_pdf(ROOT / "samples/pdf/invoice_003_missing_buyer.pdf", RULES)
    assert r.missing == ["buyer"]
    assert r.values["buyer"] is None


def test_optional_field_not_reported_missing():
    values, missing = extract_fields("Invoice No: X-1\nTotal: 5.00", RULES)
    assert "tax" not in missing and values["tax"] is None


def test_fill_marks_missing_and_flags_unknown_placeholders(tmp_path):
    tpl = tmp_path / "t.docx"
    d = Document()
    d.add_paragraph("Buyer: {{buyer}} / {{nope}}")
    d.save(str(tpl))
    out = tmp_path / "o.docx"
    unknown = fill_template(tpl, {"buyer": None}, out)
    assert unknown == ["nope"]
    assert "[MISSING]" in Document(str(out)).paragraphs[0].text


def test_cli_strict_exit_code(tmp_path):
    cmd = [sys.executable, "-m", "docfill", "--pdf-dir", str(ROOT / "samples/pdf"),
           "--config", str(ROOT / "config/invoice.yml"),
           "--template", str(ROOT / "samples/template.docx"), "--out", str(tmp_path)]
    assert subprocess.run(cmd, cwd=ROOT).returncode == 0
    assert subprocess.run(cmd + ["--strict"], cwd=ROOT).returncode == 1
    assert (tmp_path / "summary.xlsx").exists()
