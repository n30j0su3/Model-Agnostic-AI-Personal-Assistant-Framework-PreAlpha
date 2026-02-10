---
name: xlsx
description: Comprehensive spreadsheet creation, editing, and analysis with support for formulas, formatting, data analysis, and visualization. Use when working with .xlsx, .csv, .tsv files.
license: Apache-2.0
metadata:
  author: Agentman
  version: "1.0"
compatibility: Requires openpyxl, pandas, and LibreOffice (for recalculation).
---

# xlsx Skill

Comprehensive spreadsheet creation, editing, and analysis with support for formulas, formatting, data analysis, and visualization.

## When to use this skill
Use this skill when you need to work with spreadsheets (.xlsx, .xlsm, .csv, .tsv, etc) for:
1. Creating new spreadsheets with formulas and formatting.
2. Reading or analyzing data.
3. Modifying existing spreadsheets while preserving formulas.
4. Data analysis and visualization in spreadsheets.
5. Recalculating formulas.

## All Excel files

### Zero Formula Errors
- Every Excel model MUST be delivered with ZERO formula errors (#REF!, #DIV/0!, #VALUE!, #N/A, #NAME?)

### Preserve Existing Templates
- Study and EXACTLY match existing format, style, and conventions when modifying files.
- Existing template conventions ALWAYS override these guidelines.

## Financial models

### Color Coding Standards
- **Blue text (RGB: 0,0,255)**: Hardcoded inputs.
- **Black text (RGB: 0,0,0)**: ALL formulas and calculations.
- **Green text (RGB: 0,128,0)**: Links pulling from other worksheets within same workbook.
- **Red text (RGB: 255,0,0)**: External links to other files.
- **Yellow background (RGB: 255,255,0)**: Key assumptions.

## Excel File Workflows

### CRITICAL: Use Formulas, Not Hardcoded Values
**Always use Excel formulas instead of calculating values in Python and hardcoding them.** 

### Reading and analyzing data with pandas
```python
import pandas as pd
df = pd.read_excel('file.xlsx')
df.head()
df.to_excel('output.xlsx', index=False)
```

### Recalculating formulas
Excel files modified by openpyxl contain formulas as strings but not calculated values. Use `scripts/recalc.py` to recalculate formulas:

```bash
python scripts/recalc.py <excel_file> [timeout_seconds]
```

## Best Practices
- **pandas**: Best for data analysis and bulk operations.
- **openpyxl**: Best for complex formatting and formulas.
- Cell indices are 1-based (row=1, column=1 is A1).
- Use `data_only=True` in `load_workbook` to read values, but be careful as saving will lose formulas.
