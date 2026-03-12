#!/usr/bin/env python3
"""
Backlog Manager - CRUD para el backlog y dev-todo del framework
Gestiona items en:
  - core/.context/codebase/backlog.md (features del framework)
  - core/.context/dev-todo/todo.md (pendientes de desarrollo - prealpha-dev only)

Uso:
    python core/scripts/backlog-manager.py list
    python core/scripts/backlog-manager.py list --type todo --status "Pendiente"
    python core/scripts/backlog-manager.py get BL-120
    python core/scripts/backlog-manager.py add --item "Nueva feature" --priority "Alta" --criteria "Content"
    python core/scripts/backlog-manager.py add --type todo --item "Fix bug" --priority "Alta" --tags "bug" --criteria "Criterio"
    python core/scripts/backlog-manager.py update BL-120 --status "En Progreso"
    python core/scripts/backlog-manager.py next-id
    python core/scripts/backlog-manager.py audit
"""

import argparse
import datetime
import json
import re
import sys
from pathlib import Path


def find_repo_root(start_path):
    """Encuentra la raíz del repo buscando el backlog o todo."""
    start = Path(start_path).resolve()
    for candidate in [start] + list(start.parents):
        # Check for backlog
        if (candidate / "core" / ".context" / "codebase" / "backlog.md").exists():
            return candidate
        # Check for todo
        if (candidate / "core" / ".context" / "dev-todo" / "todo.md").exists():
            return candidate
    return None


def get_backlog_path(repo_root, backlog_type="backlog"):
    """Retorna la ruta al archivo según el tipo."""
    root = Path(repo_root)
    if backlog_type == "todo":
        return root / "core" / ".context" / "dev-todo" / "todo.md"
    return root / "core" / ".context" / "codebase" / "backlog.md"


def get_id_prefix(backlog_type="backlog"):
    """Retorna el prefijo de ID según el tipo."""
    return "TD" if backlog_type == "todo" else "BL"


def get_table_columns(backlog_type="backlog"):
    """Retorna el número de columnas según el tipo."""
    return 6 if backlog_type == "todo" else 5  # todo tiene columna Tags extra


def load_lines(path):
    return path.read_text(encoding="utf-8").splitlines()


def save_lines(path, lines):
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def find_table_header(lines):
    for idx, line in enumerate(lines):
        if line.strip().startswith("| ID |"):
            return idx
    return -1


def parse_row(line, backlog_type="backlog"):
    parts = [p.strip() for p in line.strip().strip("|").split("|")]
    if backlog_type == "todo":
        if len(parts) < 6:
            return None
        if len(parts) > 6:
            parts = parts[:5] + [" | ".join(parts[5:]).strip()]
        return {
            "id": parts[0],
            "item": parts[1],
            "priority": parts[2],
            "status": parts[3],
            "tags": parts[4],
            "criteria": parts[5],
        }
    else:
        if len(parts) < 5:
            return None
        if len(parts) > 5:
            parts = parts[:4] + [" | ".join(parts[4:]).strip()]
        return {
            "id": parts[0],
            "item": parts[1],
            "priority": parts[2],
            "status": parts[3],
            "criteria": parts[4],
        }


def format_row(row, backlog_type="backlog"):
    if backlog_type == "todo":
        return f"| {row['id']} | {row['item']} | {row['priority']} | {row['status']} | {row['tags']} | {row['criteria']} |"
    return f"| {row['id']} | {row['item']} | {row['priority']} | {row['status']} | {row['criteria']} |"


def parse_table(lines, backlog_type="backlog"):
    header_idx = find_table_header(lines)
    if header_idx == -1:
        raise ValueError("Table header not found")
    data_start = header_idx + 2
    data_end = data_start
    rows = []
    while data_end < len(lines):
        line = lines[data_end]
        if not line.strip().startswith("|"):
            break
        row = parse_row(line, backlog_type)
        if row:
            rows.append(row)
        data_end += 1
    return header_idx, data_start, data_end, rows


def update_last_updated(lines, date_str):
    for idx, line in enumerate(lines):
        if line.startswith("Ultima actualizacion:"):
            lines[idx] = f"Ultima actualizacion: {date_str}"
            return


def add_history(lines, message):
    history_idx = -1
    for idx, line in enumerate(lines):
        if line.strip() == "## Historial de cambios":
            history_idx = idx
            break
    if history_idx == -1:
        raise ValueError("Historial section not found")

    table_idx = find_table_header(lines)
    if table_idx == -1:
        raise ValueError("Table header not found")

    last_entry_idx = None
    for idx in range(history_idx + 1, table_idx):
        if lines[idx].strip().startswith("- "):
            last_entry_idx = idx
    insert_at = (
        (last_entry_idx + 1) if last_entry_idx is not None else (history_idx + 1)
    )
    date_str = datetime.date.today().isoformat()
    lines.insert(insert_at, f"- {date_str}: {message}")

    table_idx = find_table_header(lines)
    if table_idx > 0 and lines[table_idx - 1].strip() != "":
        lines.insert(table_idx, "")


def next_id(rows, backlog_type="backlog"):
    prefix = get_id_prefix(backlog_type)
    max_num = 0
    pattern = rf"{prefix}-(\d+)"
    for row in rows:
        match = re.match(pattern, row["id"])
        if match:
            max_num = max(max_num, int(match.group(1)))
    return f"{prefix}-{max_num + 1:03d}"


def output(data, as_json, backlog_type="backlog"):
    if as_json:
        print(json.dumps(data, ensure_ascii=True, indent=2))
        return
    if isinstance(data, list):
        for row in data:
            if backlog_type == "todo" and "tags" in row:
                print(
                    f"{row['id']} | {row['priority']} | {row['status']} | {row['tags']} | {row['item']}"
                )
            else:
                print(
                    f"{row['id']} | {row['priority']} | {row['status']} | {row['item']}"
                )
        return
    if isinstance(data, dict):
        for key, value in data.items():
            print(f"{key}: {value}")
        return
    print(data)


def cmd_list(lines, args):
    _, _, _, rows = parse_table(lines, args.type)
    status_filter = args.status.lower() if args.status else None
    priority_filter = args.priority.lower() if args.priority else None
    tags_filter = args.tags.lower() if hasattr(args, "tags") and args.tags else None
    filtered = []
    for row in rows:
        if status_filter and row["status"].lower() != status_filter:
            continue
        if priority_filter and row["priority"].lower() != priority_filter:
            continue
        if tags_filter and hasattr(args, "type") and args.type == "todo":
            if tags_filter not in row.get("tags", "").lower():
                continue
        filtered.append(row)
    output(filtered, args.json, args.type)


def cmd_get(lines, args):
    _, _, _, rows = parse_table(lines, args.type)
    for row in rows:
        if row["id"] == args.id:
            output(row, args.json, args.type)
            return
    print(f"ERROR: ID not found: {args.id}")
    sys.exit(1)


def cmd_next_id(lines, args):
    _, _, _, rows = parse_table(lines, args.type)
    output({"next_id": next_id(rows, args.type)}, args.json, args.type)


def cmd_add(lines, args, backlog_path):
    header_idx, data_start, data_end, rows = parse_table(lines, args.type)
    new_id = next_id(rows, args.type)
    if args.type == "todo":
        row = {
            "id": new_id,
            "item": args.item,
            "priority": args.priority,
            "status": args.status,
            "tags": args.tags if hasattr(args, "tags") and args.tags else "misc",
            "criteria": args.criteria,
        }
    else:
        row = {
            "id": new_id,
            "item": args.item,
            "priority": args.priority,
            "status": args.status,
            "criteria": args.criteria,
        }
    rows.append(row)
    new_lines = (
        lines[:data_start] + [format_row(r, args.type) for r in rows] + lines[data_end:]
    )
    update_last_updated(new_lines, datetime.date.today().isoformat())
    if args.history:
        add_history(new_lines, args.history)
    save_lines(backlog_path, new_lines)
    output({"ok": True, "id": new_id}, args.json, args.type)


def cmd_update(lines, args, backlog_path):
    header_idx, data_start, data_end, rows = parse_table(lines, args.type)
    updated = False
    for row in rows:
        if row["id"] != args.id:
            continue
        if args.status:
            row["status"] = args.status
        if args.item:
            row["item"] = args.item
        if args.priority:
            row["priority"] = args.priority
        if hasattr(args, "tags") and args.tags:
            row["tags"] = args.tags
        if args.criteria:
            row["criteria"] = args.criteria
        updated = True
        break
    if not updated:
        print(f"ERROR: ID not found: {args.id}")
        sys.exit(1)
    new_lines = (
        lines[:data_start] + [format_row(r, args.type) for r in rows] + lines[data_end:]
    )
    update_last_updated(new_lines, datetime.date.today().isoformat())
    if args.history:
        add_history(new_lines, args.history)
    elif args.status:
        add_history(new_lines, f"Se actualizo {args.id} a estado {args.status}.")
    save_lines(backlog_path, new_lines)
    output({"ok": True, "id": args.id}, args.json, args.type)


def cmd_history(lines, args, backlog_path):
    add_history(lines, args.message)
    update_last_updated(lines, datetime.date.today().isoformat())
    save_lines(backlog_path, lines)
    output({"ok": True}, args.json, args.type)


def cmd_audit(lines, args):
    _, _, _, rows = parse_table(lines, args.type)
    prefix = get_id_prefix(args.type)
    pattern = rf"{prefix}-\d{{3}}$"
    issues = []
    seen = set()
    for row in rows:
        rid = row["id"]
        if rid in seen:
            issues.append(f"Duplicate ID: {rid}")
        seen.add(rid)
        if not re.match(pattern, rid):
            issues.append(f"Invalid ID format: {rid}")
        if not row["item"]:
            issues.append(f"Empty item for {rid}")
        if not row["priority"]:
            issues.append(f"Empty priority for {rid}")
        if not row["status"]:
            issues.append(f"Empty status for {rid}")
    output({"ok": len(issues) == 0, "issues": issues}, args.json, args.type)


def build_parser():
    parser = argparse.ArgumentParser(
        description="Backlog manager para core/.context/codebase/backlog.md y core/.context/dev-todo/todo.md"
    )
    parser.add_argument("--json", action="store_true", help="Output JSON")
    parser.add_argument(
        "--type",
        choices=["backlog", "todo"],
        default="backlog",
        help="Tipo de lista a gestionar (backlog=todo framework, todo=dev-todo prealpha-dev only)",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    list_cmd = sub.add_parser("list", help="Listar items")
    list_cmd.add_argument("--status", help="Filtrar por estado")
    list_cmd.add_argument("--priority", help="Filtrar por prioridad")
    list_cmd.add_argument("--tags", help="Filtrar por tags (solo todo)")

    get_cmd = sub.add_parser("get", help="Obtener item por ID")
    get_cmd.add_argument("id", help="ID (ej: BL-120 o TD-001)")

    next_cmd = sub.add_parser("next-id", help="Obtener siguiente ID disponible")

    add_cmd = sub.add_parser("add", help="Agregar item")
    add_cmd.add_argument("--item", required=True, help="Descripción del item")
    add_cmd.add_argument(
        "--priority", required=True, help="Prioridad (Alta/Media/Baja)"
    )
    add_cmd.add_argument("--criteria", required=True, help="Criterios de aceptación")
    add_cmd.add_argument("--status", default="Pendiente", help="Estado")
    add_cmd.add_argument("--tags", help="Tags separados por coma (ej: bug,urgente)")
    add_cmd.add_argument("--history", help="Mensaje para historial")

    update_cmd = sub.add_parser("update", help="Actualizar item")
    update_cmd.add_argument("id", help="ID (ej: BL-120 o TD-001)")
    update_cmd.add_argument("--status", help="Estado")
    update_cmd.add_argument("--item", help="Descripción")
    update_cmd.add_argument("--priority", help="Prioridad")
    update_cmd.add_argument("--criteria", help="Criterios")
    update_cmd.add_argument("--tags", help="Tags (solo todo)")
    update_cmd.add_argument("--history", help="Mensaje para historial")

    history_cmd = sub.add_parser("history", help="Agregar entrada al historial")
    history_cmd.add_argument("message", help="Mensaje de historial")

    audit_cmd = sub.add_parser("audit", help="Auditar integridad")

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    repo_root = find_repo_root(__file__)
    if not repo_root:
        print("ERROR: No se encontró la raíz del repositorio")
        print(
            "Buscando: core/.context/codebase/backlog.md o core/.context/dev-todo/todo.md"
        )
        sys.exit(1)

    # Determinar ruta según tipo
    backlog_path = get_backlog_path(repo_root, args.type)

    if not backlog_path.exists():
        print(f"ERROR: No se encontró el archivo en: {backlog_path}")
        print(f"Tipo seleccionado: {args.type}")
        sys.exit(1)

    lines = load_lines(backlog_path)

    if args.command == "list":
        cmd_list(lines, args)
        return
    if args.command == "get":
        cmd_get(lines, args)
        return
    if args.command == "next-id":
        cmd_next_id(lines, args)
        return
    if args.command == "add":
        cmd_add(lines, args, backlog_path)
        return
    if args.command == "update":
        cmd_update(lines, args, backlog_path)
        return
    if args.command == "history":
        cmd_history(lines, args, backlog_path)
        return
    if args.command == "audit":
        cmd_audit(lines, args)
        return


if __name__ == "__main__":
    main()
