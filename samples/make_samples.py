"""Generate synthetic sample PDFs and the Word template (no real data)."""
from pathlib import Path

from docx import Document
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

HERE = Path(__file__).parent

INVOICES = [
    # layout A
    dict(file="invoice_001.pdf", lines=[
        "INVOICE", "Invoice No: INV-2026-001", "Invoice Date: 2026-11-02",
        "From: Northwind Demo Ltd", "Bill To: Contoso Sample LLC",
        "Consulting services      USD 1,000.00", "VAT 20%: USD 200.00", "Total Due: USD 1,200.00"]),
    # layout B: different labels and date format
    dict(file="invoice_002.pdf", lines=[
        "Invoice # B-778", "Date: 05 Nov 2026",
        "From: Acme Example GmbH", "Bill To: Globex Test Inc",
        "Hosting", "VAT 19%: EUR 95.00", "Total Amount: EUR 595.00"]),
    # layout C: required field (buyer) deliberately absent, to show missing detection
    dict(file="invoice_003_missing_buyer.pdf", lines=[
        "Invoice No: C-9001", "Invoice Date: 2026-11-10",
        "From: Initech Demo", "Total: USD 80.50"]),
]


def make_pdf(path: Path, lines):
    c = canvas.Canvas(str(path), pagesize=A4)
    y = 800
    for line in lines:
        c.drawString(60, y, line)
        y -= 22
    c.save()


def make_template(path: Path):
    doc = Document()
    doc.add_heading("Invoice Summary", level=1)
    doc.add_paragraph("Invoice {{invoice_number}} dated {{invoice_date}}.")
    doc.add_paragraph("Seller: {{seller}}")
    doc.add_paragraph("Buyer: {{buyer}}")
    t = doc.add_table(rows=2, cols=2)
    t.style = "Table Grid"
    t.cell(0, 0).text, t.cell(0, 1).text = "Tax", "Total"
    t.cell(1, 0).text, t.cell(1, 1).text = "{{tax}}", "{{total}}"
    doc.save(str(path))


if __name__ == "__main__":
    pdf_dir = HERE / "pdf"
    pdf_dir.mkdir(exist_ok=True)
    for inv in INVOICES:
        make_pdf(pdf_dir / inv["file"], inv["lines"])
    make_template(HERE / "template.docx")
    print("samples written")
