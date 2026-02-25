#!/usr/bin/env python3
"""
Script de optimización de templates @dashboard-pro
Minifica y comprime templates HTML, CSS, TypeScript y TSX
"""

import os
import re
import sys
from pathlib import Path
from typing import Tuple

# Configuración
SKILL_DIR = Path(__file__).parent.parent
MODES_DIR = SKILL_DIR / "modes"

# Patrones de minificación
HTML_PATTERNS = [
    (r">\s+<", "><"),  # Eliminar espacios entre tags
    (r"\s+", " "),  # Múltiples espacios a uno
    (r"<!--.*?-->", ""),  # Eliminar comentarios HTML
    (r"\s+\n", "\n"),  # Espacios al final de línea
    (r"\n+", ""),  # Eliminar saltos de línea
]

CSS_PATTERNS = [
    (r"\s*{\s*", "{"),  # Espacios antes/después de {
    (r"\s*}\s*", "}"),  # Espacios antes/después de }
    (r"\s*;\s*", ";"),  # Espacios alrededor de ;
    (r"\s*:\s*", ":"),  # Espacios alrededor de :
    (r",\s*", ","),  # Espacios después de ,
    (r"/\*.*?\*/", ""),  # Comentarios CSS
    (r"\n+", ""),  # Eliminar saltos de línea
]

JS_PATTERNS = [
    (r"\s+", " "),  # Múltiples espacios a uno
    (r"/\*.*?\*/", ""),  # Comentarios multilinea
    (r"//.*?\n", ""),  # Comentarios de línea
    (r"\s*\n\s*", ""),  # Líneas vacías
    (r";\s*\n", ";"),  # Saltos después de ;
]


def minify_html(content: str) -> str:
    """Minifica contenido HTML preservando variables {{}}"""
    # Preservar variables Handlebars temporalmente
    placeholders = {}
    counter = 0

    def preserve_handlebars(match):
        nonlocal counter
        key = f"___HB_{counter}___"
        placeholders[key] = match.group(0)
        counter += 1
        return key

    # Preservar {{...}} y {{{...}}}
    content = re.sub(r"\{\{\{?.*?\}?\}\}", preserve_handlebars, content)

    # Aplicar minificación HTML
    for pattern, replacement in HTML_PATTERNS:
        content = re.sub(pattern, replacement, content)

    # Restaurar variables Handlebars
    for key, value in placeholders.items():
        content = content.replace(key, value)

    return content.strip()


def minify_css(content: str) -> str:
    """Minifica contenido CSS preservando variables {{}}"""
    placeholders = {}
    counter = 0

    def preserve_handlebars(match):
        nonlocal counter
        key = f"___HB_{counter}___"
        placeholders[key] = match.group(0)
        counter += 1
        return key

    content = re.sub(r"\{\{\{?.*?\}?\}\}", preserve_handlebars, content)

    for pattern, replacement in CSS_PATTERNS:
        content = re.sub(pattern, replacement, content)

    for key, value in placeholders.items():
        content = content.replace(key, value)

    return content.strip()


def minify_typescript(content: str, is_tsx: bool = False) -> str:
    """Minifica TypeScript/TSX preservando tipos y JSX"""
    placeholders = {}
    counter = 0

    def preserve_handlebars(match):
        nonlocal counter
        key = f"___HB_{counter}___"
        placeholders[key] = match.group(0)
        counter += 1
        return key

    def preserve_strings(match):
        nonlocal counter
        key = f"___STR_{counter}___"
        placeholders[key] = match.group(0)
        counter += 1
        return key

    def preserve_jsx(match):
        nonlocal counter
        key = f"___JSX_{counter}___"
        placeholders[key] = match.group(0)
        counter += 1
        return key

    # Preservar strings, JSX y Handlebars
    content = re.sub(r'["\'](?:[^"\']|\\["\'])*["\']', preserve_strings, content)
    content = re.sub(r"\{\{.*?\}\}", preserve_handlebars, content)
    if is_tsx:
        content = re.sub(r"<[^>]+>", preserve_jsx, content)

    # Aplicar minificación
    content = re.sub(r"/\*.*?\*/", "", content, flags=re.DOTALL)
    content = re.sub(r"//.*?$", "", content, flags=re.MULTILINE)
    content = re.sub(r"\n\s*\n", "\n", content)
    content = re.sub(r" +", " ", content)
    content = re.sub(r";\s*\n", ";", content)
    content = re.sub(r",\s+", ",", content)
    content = re.sub(r"\{\s+", "{", content)
    content = re.sub(r"\s+\}", "}", content)
    content = re.sub(r"\(\s+", "(", content)
    content = re.sub(r"\s+\)", ")", content)
    content = re.sub(r"\s*=\s*>\s*", "=>", content)
    content = re.sub(r"\n+", "", content)

    # Restaurar placeholders
    def extract_number(s):
        match = re.search(r"\d+", s)
        return int(match.group()) if match else 0

    for key in sorted(placeholders.keys(), key=extract_number, reverse=True):
        content = content.replace(key, placeholders[key])

    return content.strip()


def get_file_size(path: Path) -> int:
    """Obtiene el tamaño de un archivo en bytes"""
    return path.stat().st_size


def format_size(size: int) -> str:
    """Formatea tamaño en bytes a string legible"""
    if size < 1024:
        return f"{size} B"
    elif size < 1024 * 1024:
        return f"{size / 1024:.1f} KB"
    else:
        return f"{size / (1024 * 1024):.1f} MB"


def optimize_file(source: Path, dest: Path) -> Tuple[int, int]:
    """Optimiza un archivo y retorna (tamaño_original, tamaño_optimizado)"""
    content = source.read_text(encoding="utf-8")
    original_size = len(content.encode("utf-8"))

    # Seleccionar minificador según extensión
    ext = source.suffix.lower()

    if ext == ".html":
        minified = minify_html(content)
    elif ext == ".css":
        minified = minify_css(content)
    elif ext == ".ts":
        minified = minify_typescript(content, is_tsx=False)
    elif ext == ".tsx":
        minified = minify_typescript(content, is_tsx=True)
    elif ext == ".js":
        minified = minify_typescript(content, is_tsx=False)
    else:
        minified = content  # No minificar otros tipos

    # Crear directorio destino si no existe
    dest.parent.mkdir(parents=True, exist_ok=True)

    # Guardar archivo optimizado
    dest.write_text(minified, encoding="utf-8")

    optimized_size = len(minified.encode("utf-8"))
    return original_size, optimized_size


def process_directory(source_dir: Path, dest_dir: Path) -> list:
    """Procesa un directorio de templates y retorna estadísticas"""
    stats = []

    if not source_dir.exists():
        return stats

    for source_file in source_dir.rglob("*"):
        # Skip .optimized directories to avoid recursion
        if ".optimized" in str(source_file):
            continue
        if source_file.is_file() and source_file.suffix in [
            ".html",
            ".css",
            ".ts",
            ".tsx",
            ".js",
        ]:
            # Calcular ruta relativa y destino
            rel_path = source_file.relative_to(source_dir)
            dest_file = dest_dir / rel_path

            try:
                original, optimized = optimize_file(source_file, dest_file)
                reduction = original - optimized
                percent = (reduction / original * 100) if original > 0 else 0

                stats.append(
                    {
                        "file": str(rel_path),
                        "original": original,
                        "optimized": optimized,
                        "reduction": reduction,
                        "percent": percent,
                    }
                )

                print(
                    f"  [OK] {rel_path}: {format_size(original)} -> {format_size(optimized)} (-{percent:.1f}%)"
                )

            except Exception as e:
                print(f"  [ERR] Error procesando {rel_path}: {e}")

    return stats


def main():
    """Función principal del script"""
    print("=" * 60)
    print("Optimizador de Templates @dashboard-pro")
    print("=" * 60)
    print()

    all_stats = []

    # Procesar template HTML
    print("Procesando template HTML (sin-dependencias)...")
    html_source = MODES_DIR / "sin-dependencias/templates/chart-js"
    html_dest = html_source / ".optimized"

    if html_source.exists():
        stats = process_directory(html_source, html_dest)
        all_stats.extend(stats)
    else:
        print("  [!] Directorio no encontrado")

    print()

    # Procesar templates Next.js
    print("Procesando templates Next.js (con-dependencias)...")
    nextjs_source = MODES_DIR / "con-dependencias/templates/nextjs-dashboard"
    nextjs_dest = nextjs_source / ".optimized"

    if nextjs_source.exists():
        # Excluir package.json y otros no-código
        stats = process_directory(nextjs_source, nextjs_dest)
        all_stats.extend(stats)
    else:
        print("  [!] Directorio no encontrado")

    print()
    print("=" * 60)
    print("Resumen de Optimizacion")
    print("=" * 60)

    if all_stats:
        total_original = sum(s["original"] for s in all_stats)
        total_optimized = sum(s["optimized"] for s in all_stats)
        total_reduction = total_original - total_optimized
        avg_percent = (
            (total_reduction / total_original * 100) if total_original > 0 else 0
        )

        print(f"\nArchivos procesados: {len(all_stats)}")
        print(f"Tamaño original:     {format_size(total_original)}")
        print(f"Tamaño optimizado:   {format_size(total_optimized)}")
        print(
            f"Reducción total:     {format_size(total_reduction)} ({avg_percent:.1f}%)"
        )
        print()
        print("[OK] Optimizacion completada exitosamente!")
        print()
        print("Los templates optimizados estan en:")
        print(f"  - {html_dest}")
        print(f"  - {nextjs_dest}")
    else:
        print("\n[!] No se procesaron archivos")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
