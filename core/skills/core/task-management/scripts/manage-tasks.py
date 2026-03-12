#!/usr/bin/env python3
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
WORKSPACES_ROOT = REPO_ROOT / "workspaces"
SESSION_FILE = REPO_ROOT / "sessions" / "SESSION.md"


def find_tasks_in_file(file_path, workspace_filter=None):
    if not file_path.exists():
        return []

    content = file_path.read_text(encoding="utf-8")
    tasks = []
    # Regex para capturar tareas: - [ ] algo @workspace #prioridad
    pattern = r"- \[[ x~]\] .*?(@\w+)?.*?(\#\w+)?"

    lines = content.splitlines()
    for line in lines:
        if line.strip().startswith("- ["):
            if workspace_filter:
                if f"@{workspace_filter}" in line:
                    tasks.append(line.strip())
            else:
                tasks.append(line.strip())
    return tasks


def list_all_tasks(workspace=None):
    all_tasks = []

    # Buscar en workspaces
    if WORKSPACES_ROOT.exists():
        for ws_dir in WORKSPACES_ROOT.iterdir():
            if ws_dir.is_dir():
                files_to_check = list(ws_dir.rglob("*.md"))
                for f in files_to_check:
                    all_tasks.extend(find_tasks_in_file(f, workspace))

    # Buscar en SESSION.md
    all_tasks.extend(find_tasks_in_file(SESSION_FILE, workspace))

    return list(set(all_tasks))  # Eliminar duplicados simples


if __name__ == "__main__":
    ws = sys.argv[1] if len(sys.argv) > 1 else None
    tasks = list_all_tasks(ws)

    if ws:
        print(f"--- Tareas para @{ws} ---")
    else:
        print("--- Todas las Tareas ---")

    if not tasks:
        print("No se encontraron tareas.")
    for t in tasks:
        print(t)
