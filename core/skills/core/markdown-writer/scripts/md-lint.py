#!/usr/bin/env python3
"""
Markdown Linter - Valida archivos Markdown según estándares del framework FreakingJSON.

Uso:
    python md-lint.py <archivo.md> [--fix]

Ejemplo:
    python md-lint.py core/.context/sessions/2026-02-11.md
    python md-lint.py core/skills/core/pdf/SKILL.md --fix
"""

import argparse
import re
import sys
from pathlib import Path
from typing import List, Tuple


def check_yaml_frontmatter(content: str) -> Tuple[bool, List[str]]:
    """Valida YAML frontmatter si existe."""
    errors = []

    if not content.strip().startswith("---"):
        return True, []  # No requiere frontmatter

    lines = content.split("\n")
    end_idx = None

    for i, line in enumerate(lines[1:], 1):
        if line.strip() == "---":
            end_idx = i
            break

    if end_idx is None:
        errors.append("Frontmatter YAML no cerrado (falta '---' final)")
        return False, errors

    frontmatter = "\n".join(lines[1:end_idx])

    # Validar campos comunes
    if "date:" in frontmatter:
        date_match = re.search(r"date:\s*(\d{4}-\d{2}-\d{2})", frontmatter)
        if not date_match:
            errors.append("Campo 'date' no tiene formato YYYY-MM-DD")

    return len(errors) == 0, errors


def check_mvi_principle(content: str) -> Tuple[bool, List[str], List[str]]:
    """Valida principio MVI (Minimal Viable Information)."""
    errors = []
    warnings = []

    # Dividir en secciones
    sections = re.split(r"\n##+\s+", content)

    for section in sections[1:]:  # Skip title
        lines = section.split("\n")
        section_title = lines[0].strip()

        # Contar bullets
        bullets = [l for l in lines if l.strip().startswith(("- ", "* ", "+ "))]
        if len(bullets) > 7:
            warnings.append(
                f"Sección '{section_title}': {len(bullets)} bullets (recomendado: 3-5)"
            )

        # Contar palabras en párrafos
        paragraphs = "\n".join(lines).split("\n\n")
        for para in paragraphs:
            if para.strip() and not para.strip().startswith(
                ("- ", "* ", "+ ", "```", "|", "#")
            ):
                words = len(para.split())
                if words > 100:
                    warnings.append(
                        f"Sección '{section_title}': párrafo de {words} palabras (considerar dividir)"
                    )

    return len(errors) == 0, errors, warnings


def check_line_length(content: str) -> List[str]:
    """Verifica longitud de líneas."""
    warnings = []
    lines = content.split("\n")

    for i, line in enumerate(lines, 1):
        # Ignorar tablas, código y headers
        if line.strip().startswith(("```", "|", "#")):
            continue
        if len(line) > 100:
            warnings.append(f"Línea {i}: {len(line)} caracteres (máx recomendado: 100)")

    return warnings


def check_headers_hierarchy(content: str) -> Tuple[bool, List[str]]:
    """Valida jerarquía de headers."""
    errors = []

    headers = re.findall(r"^(#{1,6})\s+", content, re.MULTILINE)
    levels = [len(h) for h in headers]

    if not levels:
        return True, []

    # Verificar que empieza con H1
    if levels[0] != 1:
        errors.append("El documento debe comenzar con un header H1 (#)")

    # Verificar que no hay saltos mayores a 1 nivel
    for i in range(1, len(levels)):
        if levels[i] > levels[i - 1] + 1:
            errors.append(f"Salto de H{levels[i - 1]} a H{levels[i]} (máximo 1 nivel)")

    # Verificar que no usa H4+ excesivamente
    deep_headers = [l for l in levels if l >= 4]
    if len(deep_headers) > 3:
        errors.append(f"{len(deep_headers)} headers H4+ (considerar reestructurar)")

    return len(errors) == 0, errors


def check_links(content: str) -> Tuple[List[str], List[str]]:
    """Verifica enlaces."""
    errors = []
    warnings = []

    # Enlaces Markdown
    md_links = re.findall(r"\[([^\]]+)\]\(([^)]+)\)", content)

    for text, url in md_links:
        # Verificar URL vacía
        if not url.strip():
            errors.append(f"Enlace vacío: '[{text}]()'")

        # Verificar placeholder
        if url in ["https://example.com", "#TODO", "TODO"]:
            warnings.append(f"Enlace placeholder: '[{text}]({url})'")

        # Verificar enlaces locales
        if not url.startswith(("http://", "https://", "mailto:", "#")):
            # Es un enlace relativo
            path = Path(url.split("#")[0])
            if not path.exists() and not url.startswith("/"):
                warnings.append(f"Posible enlace roto: '[{text}]({url})'")

    return errors, warnings


def check_empty_sections(content: str) -> List[str]:
    """Detecta secciones vacías o con solo TODO."""
    warnings = []

    # Encontrar headers y su contenido
    pattern = r"^(#{2,})\s+(.+)\n(.*?)(?=\n#{1,}\s+|\Z)"
    sections = re.findall(pattern, content, re.MULTILINE | re.DOTALL)

    for level, title, content_section in sections:
        content_clean = content_section.strip()

        if not content_clean:
            warnings.append(f"Sección '{title}' está vacía")
        elif content_clean.lower() in ["todo", "todo -", "tbd", "pending"]:
            warnings.append(f"Sección '{title}' tiene solo placeholder")

    return warnings


def generate_report(file_path: str, results: dict) -> None:
    """Genera reporte de validación."""

    print("\n" + "=" * 60)
    print(f"Validación: {file_path}")
    print("=" * 60)

    total_errors = sum(len(v) for k, v in results.items() if k.endswith("_errors"))
    total_warnings = sum(len(v) for k, v in results.items() if k.endswith("_warnings"))

    # Frontmatter
    if "frontmatter_errors" in results:
        if results["frontmatter_errors"]:
            print("\n[ERROR] Frontmatter YAML:")
            for error in results["frontmatter_errors"]:
                print(f"   - {error}")
        else:
            print("\n[OK] Frontmatter YAML válido")

    # MVI
    if "mvi_errors" in results or "mvi_warnings" in results:
        if results.get("mvi_errors"):
            print("\n[ERROR] Principio MVI:")
            for error in results["mvi_errors"]:
                print(f"   - {error}")

        if results.get("mvi_warnings"):
            print("\n[WARN] Advertencias MVI:")
            for warning in results["mvi_warnings"][:5]:  # Limitar a 5
                print(f"   - {warning}")
            if len(results["mvi_warnings"]) > 5:
                print(f"   ... y {len(results['mvi_warnings']) - 5} más")

    # Headers
    if "header_errors" in results:
        if results["header_errors"]:
            print("\n[ERROR] Jerarquía de Headers:")
            for error in results["header_errors"]:
                print(f"   - {error}")
        else:
            print("\n[OK] Jerarquía de headers válida")

    # Longitud de líneas
    if results.get("line_warnings"):
        print("\n[WARN] Longitud de líneas:")
        for warning in results["line_warnings"][:3]:
            print(f"   - {warning}")
        if len(results["line_warnings"]) > 3:
            print(f"   ... y {len(results['line_warnings']) - 3} más")

    # Enlaces
    if results.get("link_errors") or results.get("link_warnings"):
        if results.get("link_errors"):
            print("\n[ERROR] Enlaces:")
            for error in results["link_errors"]:
                print(f"   - {error}")

        if results.get("link_warnings"):
            print("\n[WARN] Advertencias de enlaces:")
            for warning in results["link_warnings"][:5]:
                print(f"   - {warning}")

    # Secciones vacías
    if results.get("empty_warnings"):
        print("\n[WARN] Secciones:")
        for warning in results["empty_warnings"]:
            print(f"   - {warning}")

    # Resumen
    print("\n" + "=" * 60)
    print("RESUMEN")
    print("=" * 60)
    print(f"Errores:   {total_errors}")
    print(f"Advertencias: {total_warnings}")

    if total_errors == 0:
        print("\n[OK] Documento válido según estándares del framework")
    else:
        print(f"\n[ERROR] Se encontraron {total_errors} errores")

    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(
        description="Valida archivos Markdown según estándares FreakingJSON",
        epilog="Ejemplo: python md-lint.py documento.md",
    )

    parser.add_argument("file", help="Archivo Markdown a validar")
    parser.add_argument(
        "--fix", action="store_true", help="Intentar corregir problemas automáticamente"
    )

    args = parser.parse_args()

    # Leer archivo
    try:
        with open(args.file, "r", encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        print(f"Error: Archivo no encontrado: {args.file}")
        sys.exit(1)
    except Exception as e:
        print(f"Error leyendo archivo: {e}")
        sys.exit(1)

    # Ejecutar validaciones
    results = {}

    # Frontmatter
    valid, errors = check_yaml_frontmatter(content)
    results["frontmatter_valid"] = valid
    results["frontmatter_errors"] = errors

    # MVI
    valid, errors, warnings = check_mvi_principle(content)
    results["mvi_valid"] = valid
    results["mvi_errors"] = errors
    results["mvi_warnings"] = warnings

    # Headers
    valid, errors = check_headers_hierarchy(content)
    results["header_valid"] = valid
    results["header_errors"] = errors

    # Líneas
    results["line_warnings"] = check_line_length(content)

    # Enlaces
    errors, warnings = check_links(content)
    results["link_errors"] = errors
    results["link_warnings"] = warnings

    # Secciones vacías
    results["empty_warnings"] = check_empty_sections(content)

    # Generar reporte
    generate_report(args.file, results)

    # Exit code
    total_errors = (
        len(results.get("frontmatter_errors", []))
        + len(results.get("mvi_errors", []))
        + len(results.get("header_errors", []))
        + len(results.get("link_errors", []))
    )

    sys.exit(0 if total_errors == 0 else 1)


if __name__ == "__main__":
    main()
