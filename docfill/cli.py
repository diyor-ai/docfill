"""Command line: python -m docfill --pdf-dir samples/pdf --config config/invoice.yml ..."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .excel import write_summary
from .extract import load_rules, process_pdf
from .fill import fill_template


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="docfill", description=__doc__)
    p.add_argument("--pdf-dir", required=True, type=Path)
    p.add_argument("--config", required=True, type=Path, help="YAML field rules")
    p.add_argument("--template", required=True, type=Path, help=".docx with {{field}} placeholders")
    p.add_argument("--out", default=Path("out"), type=Path)
    p.add_argument("--strict", action="store_true", help="exit 1 if any required field is missing")
    args = p.parse_args(argv)

    rules = load_rules(args.config)
    pdfs = sorted(args.pdf_dir.glob("*.pdf"))
    if not pdfs:
        print(f"no PDFs found in {args.pdf_dir}", file=sys.stderr)
        return 2

    results, problems = [], 0
    for pdf in pdfs:
        res = process_pdf(pdf, rules)
        unknown = fill_template(args.template, res.values, args.out / f"{pdf.stem}.docx")
        status = "OK" if not res.missing else f"MISSING: {', '.join(res.missing)}"
        print(f"{pdf.name}: {status}")
        if unknown:
            print(f"  warning: template placeholders without rule: {', '.join(unknown)}")
        problems += bool(res.missing)
        results.append(res)

    write_summary(results, list(rules), args.out / "summary.xlsx")
    print(f"done: {len(results)} file(s), {problems} with missing fields -> {args.out}/")
    return 1 if (args.strict and problems) else 0


if __name__ == "__main__":
    raise SystemExit(main())
