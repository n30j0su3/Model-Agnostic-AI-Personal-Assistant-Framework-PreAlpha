---
name: pptx
description: Presentation creation, editing, and analysis with support for layouts, notes, and design. Use when working with PowerPoint files (.pptx).
license: Apache-2.0
metadata:
  author: Agentman
  version: "1.0"
compatibility: Requires python-pptx, markitdown, and LibreOffice.
---

# PPTX Skill

Toolkit for handling PowerPoint presentations professionally.

## Use Cases
1. **Analysis**: Extract text, speaker notes, and layout info.
2. **Creation**: Create presentations from HTML templates (html2pptx) or scratch.
3. **Editing**: Modify slides by manipulating OOXML.
4. **Visuals**: Generate thumbnail grids for slide overview.

## Workflows

### Text Extraction
```bash
python -m markitdown presentation.pptx > content.md
```

### Visual Thumbnails
```bash
python scripts/thumbnail.py presentation.pptx ./output
```

### Creation from Template
1. Extract template inventory.
2. Map content to best-fit slide layouts.
3. Replace placeholders using JSON data.

## Design Principles
- **Hierarchy**: Use size and color for clear structure.
- **Readability**: High contrast and web-safe fonts.
- **Consistency**: Repeat patterns across the deck.

## Technical Details
- Unpack/Pack OOXML for deep editing.
- Slide indices are 0-based.
- Master slides are in `ppt/slideMasters/`.
