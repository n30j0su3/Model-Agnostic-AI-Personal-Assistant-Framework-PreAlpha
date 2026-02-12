#!/usr/bin/env python3
"""
Skill Initializer - Crea la estructura base para una nueva skill.

Uso:
    python init_skill.py <nombre-skill> [--path <directorio>]

Ejemplo:
    python init_skill.py pdf-editor --path core/skills/core/
"""

import argparse
import os
import sys
from datetime import datetime
from pathlib import Path


def create_skill_structure(skill_name: str, base_path: str) -> str:
    """
    Crea la estructura de directorios y archivos para una nueva skill.

    Args:
        skill_name: Nombre de la skill (ej: 'pdf-editor')
        base_path: Directorio base donde se creará la skill

    Returns:
        Ruta completa de la skill creada
    """
    # Normalizar nombre
    skill_name = skill_name.lower().strip().replace(" ", "-")

    # Crear ruta completa
    skill_path = Path(base_path) / skill_name

    if skill_path.exists():
        print(f"[ERROR] El directorio '{skill_path}' ya existe.")
        sys.exit(1)

    # Crear directorios
    directories = [
        skill_path,
        skill_path / "scripts",
        skill_path / "references",
        skill_path / "assets",
    ]

    for directory in directories:
        directory.mkdir(parents=True, exist_ok=False)
        print(f"[DIR] Creado: {directory}")

    return str(skill_path)


def create_skill_md(skill_path: str, skill_name: str) -> None:
    """Crea el archivo SKILL.md con template base."""

    skill_md_content = f"""---
name: {skill_name}
description: TODO - Describe qué hace esta skill y cuándo usarla. Sé específico. Esta skill debe usarse cuando...
license: MIT
metadata:
  author: TODO - Tu nombre
  version: "1.0"
  created: {datetime.now().strftime("%Y-%m-%d")}
compatibility: TODO - Requisitos específicos si los hay (ej: Python 3.8+, Node.js, etc.)
---

# {skill_name.replace("-", " ").title()}

TODO - Descripción breve del propósito de esta skill.

## Casos de Uso

1. **Caso 1**: TODO - Describe el primer caso de uso
2. **Caso 2**: TODO - Describe el segundo caso de uso  
3. **Caso 3**: TODO - Describe el tercer caso de uso

## Cuándo Usar Esta Skill

Esta skill debe usarse cuando el usuario necesite:
- TODO - Condición 1
- TODO - Condición 2
- TODO - Condición 3

## Instrucciones de Uso

### Paso 1: TODO - Primer paso
Descubre qué necesita el usuario exactamente. Pregunta si falta contexto.

### Paso 2: TODO - Segundo paso
Ejecuta la tarea siguiendo las mejores prácticas.

### Paso 3: TODO - Tercer paso
Valida el resultado antes de entregarlo.

## Ejemplos

### Ejemplo 1: TODO - Descripción
```python
# TODO - Código de ejemplo si aplica
```

### Ejemplo 2: TODO - Descripción
```bash
# TODO - Comando de ejemplo si aplica
```

## Recursos Disponibles

### Scripts (`scripts/`)
- `scripts/example.py` - TODO - Describe qué hace este script

### References (`references/`)
- `references/guide.md` - TODO - Documentación de referencia

### Assets (`assets/`)
- `assets/template.xyz` - TODO - Template o archivo de ejemplo

## Mejores Prácticas

1. TODO - Mejor práctica 1
2. TODO - Mejor práctica 2
3. TODO - Mejor práctica 3

## Notas

- TODO - Nota importante 1
- TODO - Nota importante 2
"""

    skill_md_path = Path(skill_path) / "SKILL.md"
    with open(skill_md_path, "w", encoding="utf-8") as f:
        f.write(skill_md_content)

    print(f"[FILE] Creado: {skill_md_path}")


def create_example_files(skill_path: str) -> None:
    """Crea archivos de ejemplo en cada directorio."""

    # Script de ejemplo
    script_content = '''#!/usr/bin/env python3
"""
Ejemplo de script para skill.

Este es un template que puedes personalizar o eliminar.
"""

import sys


def main():
    """Función principal del script."""
    print("¡Hola desde el script de ejemplo!")
    print("Argumentos recibidos:", sys.argv[1:])


if __name__ == "__main__":
    main()
'''

    script_path = Path(skill_path) / "scripts" / "example.py"
    with open(script_path, "w", encoding="utf-8") as f:
        f.write(script_content)
    print(f"[FILE] Creado: {script_path}")

    # Reference de ejemplo
    reference_content = """# Guía de Referencia

## Sección 1: TODO - Título

Información de referencia que el asistente puede consultar mientras trabaja.

### Subsección 1.1

- Punto 1
- Punto 2
- Punto 3

## Sección 2: TODO - Título

Más información de referencia...

## Esquemas/Formatos

```
TODO - Ejemplo de esquema o formato si aplica
```

## Enlaces Útiles

- [Documentación externa](https://example.com)
- [Recurso adicional](https://example.com/resource)
"""

    reference_path = Path(skill_path) / "references" / "guide.md"
    with open(reference_path, "w", encoding="utf-8") as f:
        f.write(reference_content)
    print(f"[FILE] Creado: {reference_path}")

    # Asset de ejemplo
    asset_content = """<!-- 
  Template de ejemplo para skill.
  
  Este archivo es un placeholder. Reemplázalo con assets reales
  como templates, imágenes, fuentes, etc.
-->

TEMPLATE_PLACEHOLDER

Instrucciones de uso:
1. TODO - Instrucción 1
2. TODO - Instrucción 2
3. TODO - Instrucción 3
"""

    asset_path = Path(skill_path) / "assets" / "template.txt"
    with open(asset_path, "w", encoding="utf-8") as f:
        f.write(asset_content)
    print(f"[FILE] Creado: {asset_path}")


def print_next_steps(skill_name: str, skill_path: str) -> None:
    """Imprime los siguientes pasos para el usuario."""

    print("\n" + "=" * 60)
    print(f"[OK] Skill '{skill_name}' inicializada exitosamente!")
    print("=" * 60)
    print(f"\n[PATH] Ubicación: {skill_path}")
    print("\n[NEXT] Siguientes pasos:")
    print("   1. Edita SKILL.md y completa los TODOs")
    print("   2. Personaliza o elimina los archivos de ejemplo")
    print("   3. Agrega scripts útiles en scripts/")
    print("   4. Agrega documentación en references/")
    print("   5. Agrega templates/assets en assets/")
    print("   6. Cuando esté lista, empaquétala con:")
    print(
        f"      python core/skills/core/skill-creator/scripts/package_skill.py {skill_path}"
    )
    print("\n[TIP] Sigue el principio MVI - Minimal Viable Information")
    print("   Documenta lo esencial, referencia el resto.")
    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(
        description="Inicializa una nueva skill en el framework FreakingJSON",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  python init_skill.py pdf-editor --path core/skills/core/
  python init_skill.py data-processor
  python init_skill.py api-client --path ./mis-skills/
        """,
    )

    parser.add_argument(
        "skill_name", help="Nombre de la skill (ej: pdf-editor, data-processor)"
    )

    parser.add_argument(
        "--path",
        default="core/skills/core/",
        help="Directorio donde se creará la skill (default: core/skills/core/)",
    )

    args = parser.parse_args()

    print(f"\n[INIT] Inicializando skill: {args.skill_name}")
    print(f"[PATH] Directorio base: {args.path}")
    print("-" * 60)

    # Crear estructura
    skill_path = create_skill_structure(args.skill_name, args.path)

    # Crear archivos
    create_skill_md(skill_path, args.skill_name)
    create_example_files(skill_path)

    # Mostrar siguientes pasos
    print_next_steps(args.skill_name, skill_path)


if __name__ == "__main__":
    main()
