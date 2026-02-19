#!/usr/bin/env python3
import sys
import re
from pathlib import Path


def analyze_seo(file_path, keywords):
    path = Path(file_path)
    if not path.exists():
        return f"Error: {file_path} no encontrado."

    content = path.read_text(encoding="utf-8")

    # Analisis de encabezados
    h1 = len(re.findall(r"^# ", content, re.M))
    h2 = len(re.findall(r"^## ", content, re.M))

    # Analisis de keywords
    kw_report = {}
    for kw in keywords:
        count = len(re.findall(re.escape(kw), content, re.I))
        kw_report[kw] = count

    report = f"# SEO Analysis: {path.name}\n\n"
    report += f"- **H1 Tags**: {h1} (Recomendado: 1)\n"
    report += f"- **H2 Tags**: {h2}\n\n"
    report += "## Keyword Density\n"
    for kw, count in kw_report.items():
        report += f"- `{kw}`: {count} apariciones\n"

    return report


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Uso: python seo-checker.py <archivo> <keyword1,keyword2...>")
    else:
        file = sys.argv[1]
        kws = sys.argv[2].split(",")
        print(analyze_seo(file, kws))
