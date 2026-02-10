---
name: docx
description: Comprehensive document creation, editing, and analysis with support for tracked changes, formatting preservation, and text extraction. Use when working with Word documents (.docx).
license: Apache-2.0
metadata:
  author: Agentman
  version: "1.0"
compatibility: Requires pandoc, python-docx, and LibreOffice.
---

# DOCX Skill

Toolkit for creating, editing, and analyzing Word documents.

## Use Cases
1. **Reading**: Extract text and structure using Pandoc or XML access.
2. **Editing**: Modify existing documents while preserving formatting.
3. **Creation**: Generate documents using `docx-js` or `python-docx`.
4. **Review**: Implement tracked changes (redlining) and comments.

## Workflows

### Text Extraction (Pandoc)
```bash
pandoc --track-changes=all document.docx -o output.md
```

### Unpacking (Raw XML Access)
DOCX files are ZIP archives. Unpack to access `word/document.xml`.
```bash
python scripts/unpack.py document.docx ./unpacked
```

### Redlining (Tracked Changes)
1. Unpack document.
2. Edit XML using `<w:ins>` and `<w:del>` tags.
3. Pack document.

## Best Practices
- **Minimal Edits**: Only mark the text that actually changes in XML.
- **RSID**: Preserve original Relationship IDs for unchanged runs.
- **Conversion**: Convert to PDF for visual analysis if needed.

## Dependencies
- `pandoc`: Text extraction.
- `LibreOffice`: PDF conversion.
- `defusedxml`: Secure XML parsing.
