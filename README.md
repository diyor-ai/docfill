

https://github.com/user-attachments/assets/e450066a-bc0d-41ea-8551-7728d45255fd

# docfill

Extract fields from text-based PDFs, fill a Word (.docx) template, and collect every
document into one Excel summary. Rules are plain YAML, so a new document type needs
no code change.

```
PDF files ──> extract (regex rules in YAML) ──> fill {{placeholders}} in .docx ──> summary.xlsx
```

Demo data is synthetic (invoices). Nothing here uses real customer data.

## Quick start

```bash
pip install -r requirements.txt
python samples/make_samples.py          # makes samples/pdf/*.pdf and samples/template.docx
python -m docfill --pdf-dir samples/pdf --config config/invoice.yml \
                  --template samples/template.docx --out out
python -m pytest -q
```

Output in `out/`: one filled `.docx` per PDF and `summary.xlsx` (rows with missing
required fields are highlighted).

Example run:

```
invoice_001.pdf: OK
invoice_002.pdf: OK
invoice_003_missing_buyer.pdf: MISSING: buyer
done: 3 file(s), 1 with missing fields -> out/
```

## Use it on your own documents

1. Copy `config/invoice.yml`, and for each field write one or more regexes with a named
   group `(?P<value>...)`. Types: `str`, `money` (handles `1,234.50` and `1.234,50`), `date`.
   Add `required: false` for optional fields.
2. In your Word template, write `{{field_name}}` where a value should go
   (paragraphs, tables, headers and footers are supported).
3. Run the command above with `--strict` to exit with code 1 if any required field is missing
   (useful in a pipeline).

## Behaviour you can rely on

- A field that cannot be found is **never guessed**: it is written as `[MISSING]` in the
  Word file, left empty in Excel, and listed in `missing_fields`.
- Placeholders in the template that have no rule are reported as warnings.
- Two label styles in the sample set (`Invoice No:` / `Invoice #`, ISO date / `05 Nov 2026`)
  are handled by listing several patterns per field.

## Limits (honest)

- Works on PDFs that contain selectable text. Scanned PDFs need OCR first (not included).
- Rule-based, not an LLM. This keeps results deterministic and free to run; an LLM step
  can be added for messy layouts, with the same `[MISSING]` rule for low-confidence values.
- When a paragraph has mixed formatting, the replaced paragraph keeps the first run's formatting.

## Layout

```
docfill/        extract.py (PDF + rules), fill.py (Word), excel.py, cli.py
config/         invoice.yml (example rules)
samples/        make_samples.py (synthetic PDFs + template)
tests/          pytest suite (parsers, both layouts, missing field, CLI exit code)
.github/        ci.yml (runs tests on every push)
```
