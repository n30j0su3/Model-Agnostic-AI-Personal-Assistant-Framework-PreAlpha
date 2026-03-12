#!/usr/bin/env python3
"""
Detecta workspace, proyecto y modo activo basado en cwd y señales.

Uso:
    python detect-workspace.py [--json] [--verbose]

Salida (JSON):
    {
        "workspace": {
            "name": "professional",
            "path": "workspaces/professional",
            "detected_by": "cwd",
            "confidence": 1.0
        },
        "project": {
            "name": "MyApp",
            "path": "workspaces/professional/projects/MyApp",
            "detected_by": "cwd",
            "confidence": 1.0,
            "is_new": false,
            "has_context_file": true
        },
        "mode": {
            "available": ["BASE", "DEV", "PROD"],
            "active": null,
            "user_specified": false
        }
    }
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any, List


# Configuración
FRAMEWORK_ROOT = Path(__file__).resolve().parents[2]  # core/scripts/ -> core/ -> root/
WORKSPACES_DIR = FRAMEWORK_ROOT / "workspaces"
CONTEXT_DIR = FRAMEWORK_ROOT / "core" / ".context"
PROJECTS_REGISTRY = CONTEXT_DIR / "projects" / "_registry.md"


def parse_args():
    parser = argparse.ArgumentParser(description="Detecta workspace y proyecto activo")
    parser.add_argument("--json", action="store_true", help="Output en formato JSON")
    parser.add_argument(
        "--verbose",
        "-v",
        choices=["silent", "minimal", "normal", "debug"],
        default="normal",
        help="Nivel de verbosidad",
    )
    return parser.parse_args()


def get_cwd() -> Path:
    """Obtiene el directorio de trabajo actual."""
    return Path.cwd().resolve()


def detect_workspace(cwd: Path, verbose: str) -> Optional[Dict[str, Any]]:
    """
    Detecta el workspace basado en cwd.

    Busca si cwd está dentro de workspaces/{workspace}/
    """
    if verbose == "debug":
        print(f"[DEBUG] CWD: {cwd}", file=sys.stderr)

    # Normalizar path
    cwd_str = str(cwd)
    workspaces_str = str(WORKSPACES_DIR)

    if verbose == "debug":
        print(f"[DEBUG] Workspaces dir: {workspaces_str}", file=sys.stderr)

    # Verificar si estamos dentro de workspaces/
    if workspaces_str not in cwd_str:
        if verbose in ["normal", "debug"]:
            print(f"[INFO] No estás dentro de {workspaces_str}", file=sys.stderr)
        return None

    # Extraer nombre del workspace
    relative = cwd.relative_to(WORKSPACES_DIR)
    parts = relative.parts

    if len(parts) == 0:
        if verbose == "debug":
            print(
                f"[DEBUG] Estás en workspaces/ pero sin subdirectorio", file=sys.stderr
            )
        return None

    workspace_name = parts[0]
    workspace_path = WORKSPACES_DIR / workspace_name

    if not workspace_path.exists():
        if verbose == "debug":
            print(f"[DEBUG] Workspace no existe: {workspace_path}", file=sys.stderr)
        return None

    return {
        "name": workspace_name,
        "path": str(workspace_path.relative_to(FRAMEWORK_ROOT)),
        "detected_by": "cwd",
        "confidence": 1.0,
    }


def detect_project(
    cwd: Path, workspace: Dict[str, Any], verbose: str
) -> Optional[Dict[str, Any]]:
    """
    Detecta el proyecto basado en cwd.

    Busca si cwd está dentro de workspaces/{workspace}/projects/{project}/
    """
    if verbose == "debug":
        print(
            f"[DEBUG] Detectando proyecto en workspace: {workspace['name']}",
            file=sys.stderr,
        )

    workspace_path = WORKSPACES_DIR / workspace["name"]
    projects_dir = workspace_path / "projects"

    if not projects_dir.exists():
        if verbose == "debug":
            print(
                f"[DEBUG] No hay directorio projects/ en {workspace_path}",
                file=sys.stderr,
            )
        return None

    # Verificar si estamos dentro de projects/
    cwd_str = str(cwd)
    projects_str = str(projects_dir)

    if projects_str not in cwd_str:
        if verbose == "debug":
            print(f"[DEBUG] No estás dentro de {projects_str}", file=sys.stderr)
        return None

    # Extraer nombre del proyecto
    try:
        relative = cwd.relative_to(projects_dir)
        parts = relative.parts

        if len(parts) == 0:
            if verbose == "debug":
                print(
                    f"[DEBUG] Estás en projects/ pero sin subdirectorio",
                    file=sys.stderr,
                )
            return None

        project_name = parts[0]
        project_path = projects_dir / project_name

        # Verificar si tiene .context/project.md
        context_file = project_path / ".context" / "project.md"
        has_context = context_file.exists()

        # Verificar si está registrado
        is_new = not is_project_registered(project_name, workspace["name"])

        return {
            "name": project_name,
            "path": str(project_path.relative_to(FRAMEWORK_ROOT)),
            "detected_by": "cwd",
            "confidence": 1.0,
            "is_new": is_new,
            "has_context_file": has_context,
        }

    except ValueError:
        if verbose == "debug":
            print(f"[DEBUG] Error calculando relative path", file=sys.stderr)
        return None


def detect_modes(project_path: Path, verbose: str) -> List[str]:
    """
    Detecta modos disponibles (BASE, DEV, PROD) escaneando directorios.
    """
    modes = []
    mode_dirs = ["BASE", "DEV", "PROD"]

    for mode in mode_dirs:
        mode_path = project_path / mode
        if mode_path.exists() and mode_path.is_dir():
            modes.append(mode)

    if verbose == "debug":
        print(f"[DEBUG] Modos detectados: {modes}", file=sys.stderr)

    return modes


def is_project_registered(project_name: str, workspace_name: str) -> bool:
    """
    Verifica si un proyecto está registrado en _registry.md
    """
    if not PROJECTS_REGISTRY.exists():
        return False

    try:
        content = PROJECTS_REGISTRY.read_text(encoding="utf-8")
        # Buscar línea con proyecto y workspace
        search_term = f"| {project_name} | {workspace_name} |"
        return search_term in content
    except Exception:
        return False


def register_project(project: Dict[str, Any], workspace: Dict[str, Any]) -> bool:
    """
    Registra un proyecto nuevo en _registry.md
    """
    try:
        PROJECTS_REGISTRY.parent.mkdir(parents=True, exist_ok=True)

        from datetime import datetime

        today = datetime.now().strftime("%Y-%m-%d")

        line = f"| {project['name']} | {workspace['name']} | {project['path']} | {today} | {today} |\n"

        if not PROJECTS_REGISTRY.exists():
            # Crear archivo con header
            header = "# Registro de Proyectos\n\n"
            header += "| Proyecto | Workspace | Ruta | Detectado | Último Uso |\n"
            header += "|----------|-----------|------|-----------|------------|\n"
            PROJECTS_REGISTRY.write_text(header + line, encoding="utf-8")
        else:
            # Agregar línea
            with open(PROJECTS_REGISTRY, "a", encoding="utf-8") as f:
                f.write(line)

        return True
    except Exception as e:
        print(f"[WARNING] No se pudo registrar proyecto: {e}", file=sys.stderr)
        return False


def main():
    args = parse_args()
    verbose = args.verbose

    if verbose == "debug":
        print(f"[DEBUG] Framework root: {FRAMEWORK_ROOT}", file=sys.stderr)
        print(f"[DEBUG] Workspaces dir: {WORKSPACES_DIR}", file=sys.stderr)

    cwd = get_cwd()

    # Detectar workspace
    workspace = detect_workspace(cwd, verbose)

    # Detectar proyecto (solo si hay workspace)
    project = None
    if workspace:
        project = detect_project(cwd, workspace, verbose)

        # Registrar proyecto si es nuevo
        if project and project["is_new"]:
            if verbose in ["normal", "debug"]:
                print(
                    f"[INFO] Registrando proyecto nuevo: {project['name']}",
                    file=sys.stderr,
                )
            register_project(project, workspace)

    # Detectar modos (solo si hay proyecto)
    modes = {"available": [], "active": None, "user_specified": False}
    if project:
        project_path = FRAMEWORK_ROOT / project["path"]
        modes["available"] = detect_modes(project_path, verbose)

    # Construir resultado
    result = {
        "workspace": workspace,
        "project": project,
        "mode": modes,
        "framework_root": str(FRAMEWORK_ROOT),
        "cwd": str(cwd),
    }

    # Output
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        # Formato legible
        print("=" * 60)
        print("DETECCIÓN DE CONTEXTO")
        print("=" * 60)

        if workspace:
            print(f"Workspace: {workspace['name']}")
            print(f"  Ruta: {workspace['path']}")
            print(f"  Confianza: {workspace['confidence']}")
        else:
            print("Workspace: No detectado")

        print()

        if project:
            print(f"Proyecto: {project['name']}")
            print(f"  Ruta: {project['path']}")
            if project["is_new"]:
                print(f"  Estado: Nuevo (registrado)")
            else:
                print(f"  Estado: Existente")
            if not project["has_context_file"]:
                print(f"  Aviso: No tiene .context/project.md")
        else:
            print("Proyecto: No detectado")

        print()

        if modes["available"]:
            print(f"Modos disponibles: {', '.join(modes['available'])}")
            print(f"Modo activo: {modes['active'] or 'Ninguno (especifica con /mode)'}")
        else:
            print("Modos: No detectados (sin carpetas BASE/DEV/PROD)")

        print("=" * 60)

    return 0 if workspace else 1


if __name__ == "__main__":
    sys.exit(main())
