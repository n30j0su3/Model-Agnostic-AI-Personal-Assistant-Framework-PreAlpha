#!/usr/bin/env python3
"""
Skill Packager - Valida y empaqueta una skill en formato ZIP distribuible.

Uso:
    python package_skill.py <ruta/a/skill-folder> [directorio-salida]

Ejemplo:
    python package_skill.py core/skills/core/pdf-editor ./dist
"""

import argparse
import json
import os
import re
import sys
import zipfile
from pathlib import Path
from typing import List, Tuple


def validate_yaml_frontmatter(skill_md_content: str) -> Tuple[bool, List[str]]:
    """
    Valida que el contenido tenga YAML frontmatter válido.

    Returns:
        Tuple de (es_válido, lista_de_errores)
    """
    errors = []

    # Verificar que comience con ---
    if not skill_md_content.strip().startswith("---"):
        errors.append("El archivo debe comenzar con '---' para el frontmatter YAML")
        return False, errors

    # Extraer frontmatter
    lines = skill_md_content.split("\n")
    if len(lines) < 3:
        errors.append("El archivo es demasiado corto")
        return False, errors

    # Encontrar cierre del frontmatter
    end_idx = None
    for i, line in enumerate(lines[1:], 1):
        if line.strip() == "---":
            end_idx = i
            break

    if end_idx is None:
        errors.append("No se encontró cierre del frontmatter YAML ('---')")
        return False, errors

    frontmatter = "\n".join(lines[1:end_idx])

    # Validar campos requeridos
    required_fields = ["name:", "description:"]
    for field in required_fields:
        if field not in frontmatter:
            errors.append(f"Campo requerido '{field}' no encontrado en frontmatter")

    # Validar formato de campos
    name_match = re.search(r"^name:\s*(.+)$", frontmatter, re.MULTILINE)
    if name_match:
        name = name_match.group(1).strip()
        if not name:
            errors.append("El campo 'name' está vacío")
        elif " " in name:
            errors.append(f"El campo 'name' no debe contener espacios: '{name}'")
        elif not re.match(r"^[a-z0-9-]+$", name):
            errors.append(
                f"El campo 'name' debe ser kebab-case (minúsculas y guiones): '{name}'"
            )

    desc_match = re.search(r"^description:\s*(.+)$", frontmatter, re.MULTILINE)
    if desc_match:
        description = desc_match.group(1).strip()
        if len(description) < 20:
            errors.append(
                f"La descripción es muy corta ({len(description)} chars). Mínimo 20 caracteres."
            )

    return len(errors) == 0, errors


def validate_directory_structure(skill_path: str) -> Tuple[bool, List[str]]:
    """
    Valida la estructura de directorios de una skill.

    Returns:
        Tuple de (es_válido, lista_de_errores)
    """
    errors = []
    path = Path(skill_path)

    # Verificar que existe
    if not path.exists():
        errors.append(f"El directorio no existe: {skill_path}")
        return False, errors

    # Verificar que es directorio
    if not path.is_dir():
        errors.append(f"La ruta no es un directorio: {skill_path}")
        return False, errors

    # Verificar SKILL.md
    skill_md = path / "SKILL.md"
    if not skill_md.exists():
        errors.append(f"No se encontró SKILL.md en: {skill_path}")
    else:
        # Leer y validar frontmatter
        try:
            with open(skill_md, "r", encoding="utf-8") as f:
                content = f.read()
            is_valid, yaml_errors = validate_yaml_frontmatter(content)
            errors.extend(yaml_errors)
        except Exception as e:
            errors.append(f"Error leyendo SKILL.md: {e}")

    # Verificar nombre del directorio vs nombre en SKILL.md
    dir_name = path.name
    if skill_md.exists():
        try:
            with open(skill_md, "r", encoding="utf-8") as f:
                content = f.read()
            name_match = re.search(r"^name:\s*(.+)$", content, re.MULTILINE)
            if name_match:
                skill_name = name_match.group(1).strip()
                if skill_name != dir_name:
                    errors.append(
                        f"Nombre mismatch: directorio='{dir_name}' vs SKILL.md name='{skill_name}'"
                    )
        except:
            pass

    return len(errors) == 0, errors


def check_references(skill_path: str) -> List[str]:
    """
    Verifica que las referencias en SKILL.md existan.

    Returns:
        Lista de advertencias
    """
    warnings = []
    path = Path(skill_path)
    skill_md = path / "SKILL.md"

    if not skill_md.exists():
        return warnings

    try:
        with open(skill_md, "r", encoding="utf-8") as f:
            content = f.read()

        # Buscar referencias a archivos
        ref_patterns = [
            r"references/([\w\-./]+)",
            r"scripts/([\w\-./]+)",
            r"assets/([\w\-./]+)",
        ]

        referenced_files = set()
        for pattern in ref_patterns:
            matches = re.findall(pattern, content)
            referenced_files.update(matches)

        # Verificar existencia
        for ref in referenced_files:
            # Limpiar extensión si se incluyó
            ref_clean = ref.split(".")[0] if "." in ref else ref

            # Buscar archivo
            found = False
            for subdir in ["references", "scripts", "assets"]:
                full_path = path / subdir / ref
                if full_path.exists():
                    found = True
                    break
                # Intentar con extensiones comunes
                for ext in [".md", ".py", ".js", ".sh", ".txt", ".json"]:
                    if (path / subdir / f"{ref}{ext}").exists():
                        found = True
                        break

            if not found:
                warnings.append(f"Referencia no encontrada: '{ref}' (en SKILL.md)")

    except Exception as e:
        warnings.append(f"Error verificando referencias: {e}")

    return warnings


def create_zip(skill_path: str, output_dir: str) -> str:
    """
    Crea un archivo ZIP de la skill.

    Returns:
        Ruta al archivo ZIP creado
    """
    path = Path(skill_path)
    skill_name = path.name

    # Crear directorio de salida si no existe
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Nombre del ZIP
    zip_name = f"{skill_name}.zip"
    zip_path = output_path / zip_name

    # Crear ZIP
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for file_path in path.rglob("*"):
            if file_path.is_file():
                # Calcular ruta relativa
                arcname = file_path.relative_to(path.parent)
                zipf.write(file_path, arcname)

    return str(zip_path)


def get_skill_info(skill_path: str) -> dict:
    """Extrae información de la skill desde SKILL.md."""
    info = {"name": "", "description": "", "version": "1.0", "files": 0, "size_kb": 0}

    path = Path(skill_path)
    skill_md = path / "SKILL.md"

    if skill_md.exists():
        try:
            with open(skill_md, "r", encoding="utf-8") as f:
                content = f.read()

            # Extraer campos
            name_match = re.search(r"^name:\s*(.+)$", content, re.MULTILINE)
            if name_match:
                info["name"] = name_match.group(1).strip()

            desc_match = re.search(r"^description:\s*(.+)$", content, re.MULTILINE)
            if desc_match:
                info["description"] = desc_match.group(1).strip()

            version_match = re.search(
                r'version:\s*["\']?([\d.]+)["\']?', content, re.MULTILINE
            )
            if version_match:
                info["version"] = version_match.group(1)
        except:
            pass

    # Contar archivos y tamaño
    total_size = 0
    file_count = 0
    for file_path in path.rglob("*"):
        if file_path.is_file():
            file_count += 1
            total_size += file_path.stat().st_size

    info["files"] = file_count
    info["size_kb"] = round(total_size / 1024, 2)

    return info


def main():
    parser = argparse.ArgumentParser(
        description="Valida y empaqueta una skill para distribución",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  python package_skill.py core/skills/core/pdf-editor
  python package_skill.py core/skills/core/data-processor ./dist
  python package_skill.py ./mi-skill ../packages/
        """,
    )

    parser.add_argument("skill_path", help="Ruta al directorio de la skill")

    parser.add_argument(
        "output_dir",
        nargs="?",
        default=".",
        help="Directorio de salida para el ZIP (default: directorio actual)",
    )

    args = parser.parse_args()

    skill_path = os.path.abspath(args.skill_path)
    output_dir = os.path.abspath(args.output_dir)

    print("\n[PACK] Skill Packager")
    print("=" * 60)
    print(f"Skill: {skill_path}")
    print(f"Output: {output_dir}")
    print("-" * 60)

    # Validar estructura
    print("\n[VALID] Validando estructura...")
    is_valid, errors = validate_directory_structure(skill_path)

    if errors:
        print("[ERROR] Errores encontrados:")
        for error in errors:
            print(f"   - {error}")

    if not is_valid:
        print("\n[FAIL] Validación fallida. Corrige los errores antes de empaquetar.")
        sys.exit(1)

    print("[OK] Estructura válida")

    # Verificar referencias
    print("\n[CHECK] Verificando referencias...")
    warnings = check_references(skill_path)
    if warnings:
        print("[WARN] Advertencias:")
        for warning in warnings:
            print(f"   - {warning}")
    else:
        print("[OK] Todas las referencias son válidas")

    # Obtener info
    info = get_skill_info(skill_path)

    # Crear ZIP
    print("\n[PACK] Empaquetando...")
    try:
        zip_path = create_zip(skill_path, output_dir)
        zip_size = os.path.getsize(zip_path) / 1024

        print(f"[OK] ZIP creado: {zip_path}")
        print(f"[INFO] Tamaño: {zip_size:.2f} KB")

    except Exception as e:
        print(f"[ERROR] Error creando ZIP: {e}")
        sys.exit(1)

    # Resumen
    print("\n" + "=" * 60)
    print("[SUMMARY] Resumen de la Skill")
    print("=" * 60)
    print(f"Nombre:        {info['name']}")
    print(f"Versión:       {info['version']}")
    print(f"Archivos:      {info['files']}")
    print(f"Tamaño:        {info['size_kb']} KB")
    print(f"Descripción:   {info['description'][:60]}...")
    print("=" * 60)
    print(f"\n[OK] Skill empaquetada exitosamente: {zip_path}")

    # Sugerir siguiente paso
    print("\n[TIP] Siguiente paso:")
    print(f"   El ZIP está listo para distribuirse o instalarse en otro sistema.")
    print("=" * 60)


if __name__ == "__main__":
    main()
