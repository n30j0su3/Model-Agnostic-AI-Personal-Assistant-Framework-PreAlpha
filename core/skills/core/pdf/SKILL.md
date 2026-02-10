---
name: pdf
description: Comprehensive PDF manipulation toolkit for extracting text and tables, creating new PDFs, merging/splitting documents, and handling forms. Use when the user needs to process or generate PDF files.
license: Apache-2.0
metadata:
  author: Agentman
  version: "1.0"
compatibility: Requires pypdf, pdfplumber, reportlab, and poppler-utils.
---

# PDF Skill

Toolkit for advanced PDF processing operations using Python libraries and command-line tools.

## Use Cases
1. **Extraction**: Extract text, tables, and images from PDFs.
2. **Creation**: Generate professional PDFs from scratch.
3. **Manipulation**: Merge multiple PDFs, split pages, or rotate documents.
4. **Forms**: Fill in PDF forms programmatically.
5. **OCR**: Extract text from scanned documents (requires pytesseract).

## Python Operations

### Merge PDFs
```python
from pypdf import PdfWriter, PdfReader
writer = PdfWriter()
for f in ["1.pdf", "2.pdf"]:
    writer.add_page(PdfReader(f).pages[0])
with open("merged.pdf", "wb") as out:
    writer.write(out)
```

### Extract Tables (pdfplumber)
```python
import pdfplumber
with pdfplumber.open("doc.pdf") as pdf:
    table = pdf.pages[0].extract_table()
```

### Create PDF (reportlab)
```python
from reportlab.pdfgen import canvas
c = canvas.Canvas("hello.pdf")
c.drawString(100, 750, "Hello World")
c.save()
```

## CLI Tools
- `pdftotext`: `pdftotext input.pdf output.txt`
- `qpdf`: `qpdf --empty --pages f1.pdf f2.pdf -- merged.pdf`

## Best Practices
- Use `pypdf` for structure (merge/split).
- Use `pdfplumber` for content extraction (text/tables).
- Use `reportlab` for generation.
