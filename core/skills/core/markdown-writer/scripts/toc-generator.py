#!/usr/bin/env python3
"""
TOC Generator - Genera tabla de contenidos para archivos Markdown.

Uso:
    python toc-generator.py <archivo.md> [--output <archivo>] [--max-depth N]

Ejemplo:
    python toc-generator.py documento.md
    python toc-generator.py documento.md --output documento-con-toc.md
    python toc-generator.py documento.md --max-depth 3
"""

import argparse
import re
import sys
from pathlib import Path
from typing import List, Tuple


def extract_headers(content: str) -> List[Tuple[int, str, str]]:
    """
    Extrae headers del contenido Markdown.

    Returns:
        Lista de tuplas (nivel, texto, anchor)
    """
    headers = []

    # Patrón para headers Markdown
    pattern = r"^(#{1,6})\s+(.+)$"

    for match in re.finditer(pattern, content, re.MULTILINE):
        level = len(match.group(1))
        text = match.group(2).strip()

        # Generar anchor (similar a GitHub)
        anchor = text.lower()
        anchor = re.sub(r"[^\w\s-]", "", anchor)  # Remover caracteres especiales
        anchor = re.sub(r"\s+", "-", anchor)  # Espacios a guiones
        anchor = anchor.strip("-")  # Remover guiones extremos

        headers.append((level, text, anchor))

    return headers


def generate_toc(headers: List[Tuple[int, str, str]], max_depth: int = 3) -> str:
    """
    Genera tabla de contenidos en formato Markdown.

    Args:
        headers: Lista de (nivel, texto, anchor)
        max_depth: Profundidad máxima de headers a incluir

    Returns:
        String con TOC en formato Markdown
    """
    if not headers:
        return ""

    # Filtrar por profundidad máxima
    headers = [(l, t, a) for l, t, a in headers if l <= max_depth]

    if not headers:
        return ""

    # Encontrar nivel base (mínimo)
    min_level = min(h[0] for h in headers)

    lines = ["## Tabla de Contenidos", ""]

    for level, text, anchor in headers:
        # Calcular indentación (2 espacios por nivel debajo del mínimo)
        indent = "  " * (level - min_level)
        lines.append(f"{indent}- [{text}](#{anchor})")

    lines.append("")

    return "\n".join(lines)


def insert_toc(content: str, toc: str) -> str:
    """
    Inserta TOC después del primer H1 o frontmatter.

    Args:
        content: Contenido original
        toc: Tabla de contenidos generada

    Returns:
        Contenido con TOC insertada
    """
    lines = content.split("\n")

    # Buscar dónde insertar (después de H1 o después de frontmatter)
    insert_idx = 0
    in_frontmatter = False
    frontmatter_end = -1
    h1_idx = -1

    for i, line in enumerate(lines):
        # Detectar frontmatter
        if i == 0 and line.strip() == "---":
            in_frontmatter = True
            continue

        if in_frontmatter:
            if line.strip() == "---":
                frontmatter_end = i
                in_frontmatter = False
            continue

        # Detectar H1
        if line.startswith("# ") and h1_idx == -1:
            h1_idx = i
            break

    # Decidir dónde insertar
    if frontmatter_end != -1:
        insert_idx = frontmatter_end + 1
    elif h1_idx != -1:
        insert_idx = h1_idx + 1
    else:
        insert_idx = 0

    # Insertar TOC
    new_lines = lines[:insert_idx] + ["", toc] + lines[insert_idx:]

    return "\n".join(new_lines)


def has_toc(content: str) -> bool:
    """Verifica si el documento ya tiene TOC."""
    return "## Tabla de Contenidos" in content or "## Table of Contents" in content


def main():
    parser = argparse.ArgumentParser(
        description="Genera tabla de contenidos para archivos Markdown",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  python toc-generator.py documento.md
  python toc-generator.py documento.md --output doc-con-toc.md
  python toc-generator.py documento.md --max-depth 2
        """,
    )

    parser.add_argument("file", help="Archivo Markdown de entrada")
    parser.add_argument(
        "--output", "-o", help="Archivo de salida (default: sobrescribe entrada)"
    )
    parser.add_argument(
        "--max-depth",
        type=int,
        default=3,
        help="Profundidad máxima de headers (default: 3)",
    )
    parser.add_argument("--force", action="store_true", help="Reemplazar TOC existente")

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

    # Verificar si ya tiene TOC
    if has_toc(content) and not args.force:
        print(f"El archivo ya tiene una tabla de contenidos.")
        print("Usa --force para reemplazarla.")
        sys.exit(0)

    # Extraer headers
    headers = extract_headers(content)

    if len(headers) < 3:
        print(f"El documento tiene solo {len(headers)} headers. TOC no necesaria.")
        sys.exit(0)

    # Generar TOC
    toc = generate_toc(headers, args.max_depth)

    if not toc:
        print("No se pudo generar tabla de contenidos.")
        sys.exit(1)

    # Insertar TOC
    new_content = insert_toc(content, toc)

    # Determinar archivo de salida
    output_file = args.output or args.file

    # Guardar
    try:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(new_content)

        print(f"Tabla de contenidos generada exitosamente")
        print(f"Archivo: {output_file}")
        print(f"Headers encontrados: {len(headers)}")
        print(f"Profundidad máxima: {args.max_depth}")

    except Exception as e:
        print(f"Error guardando archivo: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
