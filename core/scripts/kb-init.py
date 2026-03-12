#!/usr/bin/env python3
"""
KB Init - Knowledge Base Initialization
========================================

Inicializa la estructura de la Knowledge Base del framework.
Crea los archivos necesarios si no existen.

Uso:
    python core/scripts/kb-init.py
    python core/scripts/kb-init.py --check    # Solo verificar estado
    python core/scripts/kb-init.py --force     # Forzar recrear estructura

Autor: FreakingJSON-PA Framework
Version: 1.0.0
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

# Paths
SCRIPT_DIR = Path(__file__).resolve().parent
CORE_DIR = SCRIPT_DIR.parent
REPO_ROOT = CORE_DIR.parent
CONTEXT_DIR = CORE_DIR / ".context"
KB_DIR = CONTEXT_DIR / "knowledge"
CODEBASE_DIR = CONTEXT_DIR / "codebase"


# Colors
class Colors:
    HEADER = "\033[95m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    END = "\033[0m"
    BOLD = "\033[1m"


def c(text: str, color: str) -> str:
    return f"{color}{text}{Colors.END}"


def check_kb_structure() -> dict:
    """Verificar estructura de KB y retornar estado."""
    status = {
        "kb_readme": KB_DIR / "README.md",
        "sessions_index": KB_DIR / "sessions-index.json",
        "preferences": KB_DIR / "users" / "default" / "preferences.md",
        "logging_config": KB_DIR / "users" / "default" / "logging-config.md",
        "codebase_recordatorios": CODEBASE_DIR / "recordatorios.md",
        "codebase_ideas": CODEBASE_DIR / "ideas.md",
    }

    result = {}
    for name, path in status.items():
        result[name] = {
            "exists": path.exists(),
            "path": str(path),
        }

    return result


def create_default_files():
    """Crear archivos por defecto si no existen."""
    created = []

    # FIX: Crear directorios padres primero (sesion 2026-03-09)
    KB_DIR.mkdir(parents=True, exist_ok=True)
    CODEBASE_DIR.mkdir(parents=True, exist_ok=True)

    # KB README
    if not (KB_DIR / "README.md").exists():
        (KB_DIR / "README.md").write_text(
            """# Knowledge Base

Sistema centralizado de almacenamiento y conocimiento del asistente personal.

## Estructura

- sessions-index.json: Indice de sesiones
- users/default/: Configuracion de usuario

**Ultima actualizacion**: """,
            encoding="utf-8",
        )
        created.append("README.md")

    # Sessions index
    if not (KB_DIR / "sessions-index.json").exists():
        index = {
            "version": "1.0.0",
            "total_sessions": 0,
            "last_updated": datetime.now().strftime("%Y-%m-%d"),
            "sessions": [],
        }
        (KB_DIR / "sessions-index.json").write_text(
            json.dumps(index, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        created.append("sessions-index.json")

    # Preferences
    prefs_dir = KB_DIR / "users" / "default"
    prefs_dir.mkdir(parents=True, exist_ok=True)
    if not (prefs_dir / "preferences.md").exists():
        (prefs_dir / "preferences.md").write_text(
            """# Preferencias del Usuario

## Idioma
- Principal: Espanol
- Secundario: English

## Estilo
- Claro y conciso
""",
            encoding="utf-8",
        )
        created.append("preferences.md")

    # Logging config
    if not (prefs_dir / "logging-config.md").exists():
        (prefs_dir / "logging-config.md").write_text(
            """# Configuracion de Logging

## Estado
- Habilitado: Si
- Nivel: Info
""",
            encoding="utf-8",
        )
        created.append("logging-config.md")

    # Codebase - recordatorios
    CODEBASE_DIR.mkdir(parents=True, exist_ok=True)
    if not (CODEBASE_DIR / "recordatorios.md").exists():
        (CODEBASE_DIR / "recordatorios.md").write_text(
            """# Pendientes

## Alta Prioridad
- [ ] Ejemplo de tarea

## Media Prioridad

## Baja Prioridad
""",
            encoding="utf-8",
        )
        created.append("recordatorios.md")

    # Codebase - ideas
    if not (CODEBASE_DIR / "ideas.md").exists():
        (CODEBASE_DIR / "ideas.md").write_text(
            """# Ideas y Descubrimientos

## Ideas Recientes

## Recursos Utiles
""",
            encoding="utf-8",
        )
        created.append("ideas.md")

    return created


def print_status(status: dict):
    """Imprimir estado de la KB."""
    print(c("\n[KB] Estado de Knowledge Base:", Colors.BOLD + Colors.CYAN))

    all_ok = True
    for name, info in status.items():
        icon = c("[OK]", Colors.GREEN) if info["exists"] else c("[FALTA]", Colors.RED)
        print(f"  {icon} {name}")
        if not info["exists"]:
            all_ok = False

    if all_ok:
        print(c("\n[KB] Knowledge Base completamente inicializada", Colors.GREEN))
    else:
        print(
            c("\n[KB] Ejecuta: python core/scripts/kb-init.py --force", Colors.YELLOW)
        )

    return all_ok


def main():
    parser = argparse.ArgumentParser(description="Inicializar Knowledge Base")
    parser.add_argument("--check", action="store_true", help="Solo verificar estado")
    parser.add_argument(
        "--force", action="store_true", help="Forzar recrear estructura"
    )
    args = parser.parse_args()

    print(c("\n" + "=" * 50, Colors.HEADER))
    print(c("[KB] Knowledge Base Initialization", Colors.BOLD + Colors.GREEN))
    print(c("=" * 50, Colors.HEADER))

    # Check current status
    status = check_kb_structure()
    print_status(status)

    if args.check:
        return 0 if all(s["exists"] for s in status.values()) else 1

    if args.force or not all(s["exists"] for s in status.values()):
        print(c("\n[KB] Creando archivos faltantes...", Colors.YELLOW))
        created = create_default_files()
        print(c(f"[KB] Archivos creados: {len(created)}", Colors.GREEN))
        for f in created:
            print(f"  - {f}")

        # Verify again
        status = check_kb_structure()
        print_status(status)

    print(c("\n[KB] Listo.", Colors.GREEN))
    return 0


if __name__ == "__main__":
    sys.exit(main())
