#!/usr/bin/env python3
"""
PA Framework - Migration System
Sistema de migracion automatica entre versiones del framework.

Uso:
    python core/scripts/migrate.py --check
    python core/scripts/migrate.py --apply
    python core/scripts/migrate.py --status
    python core/scripts/migrate.py --force-all

Autor: FreakingJSON-PA Framework
Version: 1.0.0
"""

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

if sys.platform == "win32" and sys.stdout.isatty():
    try:
        import io

        sys.stdout = io.TextIOWrapper(
            sys.stdout.buffer, encoding="utf-8", errors="replace"
        )
        sys.stderr = io.TextIOWrapper(
            sys.stderr.buffer, encoding="utf-8", errors="replace"
        )
    except (ValueError, AttributeError):
        pass

SCRIPT_DIR = Path(__file__).resolve().parent
CORE_DIR = SCRIPT_DIR.parent
REPO_ROOT = CORE_DIR.parent
CONTEXT_DIR = CORE_DIR / ".context"
MIGRATION_STATE_FILE = CONTEXT_DIR / ".migration_state.json"
VERSION_FILE = REPO_ROOT / "VERSION"

MIGRATIONS: Dict[str, Dict] = {
    "v0.1.0": {
        "name": "initial_structure",
        "description": "Estructura inicial del framework",
        "creates": ["core/.context/", "core/.context/sessions/"],
    },
    "v0.1.4": {
        "name": "vitals_system",
        "description": "Sistema de proteccion VITALS",
        "creates": ["core/.context/vitals/"],
    },
    "v0.1.7": {
        "name": "knowledge_base",
        "description": "Sistema de Knowledge Base",
        "creates": [
            "core/.context/knowledge/",
            "core/.context/knowledge/sessions-index.json",
            "core/.context/codebase/",
        ],
        "scripts": ["kb-init.py"],
    },
    "v0.2.0": {
        "name": "indexes_and_learning",
        "description": "Indices de skills/agents y estructuras de aprendizaje",
        "creates": [
            "core/.context/knowledge/skills-index.json",
            "core/.context/knowledge/agents-index.json",
            "core/.context/knowledge/learning/",
            "core/.context/knowledge/self-healing/",
            "core/.context/knowledge/prompts/",
            "core/.context/projects/",
        ],
        "scripts": ["skills-indexer.py", "agents-indexer.py"],
    },
}


class Colors:
    HEADER = "\033[95m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    END = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"


def c(text: str, color: str) -> str:
    return f"{color}{text}{Colors.END}"


def safe_print(text: str, **kwargs):
    try:
        print(text, **kwargs)
    except UnicodeEncodeError:
        encoding = sys.stdout.encoding or "utf-8"
        safe_text = text.encode(encoding, errors="replace").decode(encoding)
        print(safe_text, **kwargs)


def get_framework_version() -> str:
    try:
        if VERSION_FILE.exists():
            content = VERSION_FILE.read_text(encoding="utf-8").strip()
            return content
    except Exception:
        pass
    return "0.0.0"


def parse_version(version: str) -> Tuple[int, int, int]:
    clean = version.lstrip("v").split("-")[0].split("+")[0]
    parts = clean.split(".")
    major = int(parts[0]) if len(parts) > 0 else 0
    minor = int(parts[1]) if len(parts) > 1 else 0
    patch = int(parts[2]) if len(parts) > 2 else 0
    return (major, minor, patch)


def version_compare(v1: str, v2: str) -> int:
    p1 = parse_version(v1)
    p2 = parse_version(v2)
    if p1 < p2:
        return -1
    elif p1 > p2:
        return 1
    return 0


def load_migration_state() -> Dict:
    default_state = {
        "framework_version": get_framework_version(),
        "migrations_applied": [],
        "last_migration": None,
        "migrations_log": [],
    }

    if not MIGRATION_STATE_FILE.exists():
        return default_state

    try:
        content = MIGRATION_STATE_FILE.read_text(encoding="utf-8")
        state = json.loads(content)
        for key in default_state:
            if key not in state:
                state[key] = default_state[key]
        return state
    except Exception:
        return default_state


def save_migration_state(state: Dict) -> bool:
    try:
        MIGRATION_STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        content = json.dumps(state, indent=2, ensure_ascii=False)
        MIGRATION_STATE_FILE.write_text(content, encoding="utf-8")
        return True
    except Exception as e:
        safe_print(c(f"[ERROR] No se pudo guardar estado: {e}", Colors.RED))
        return False


def detect_missing_structures() -> Dict[str, List[str]]:
    missing = {}

    for version, migration in MIGRATIONS.items():
        version_missing = []

        for path in migration.get("creates", []):
            full_path = REPO_ROOT / path
            if path.endswith("/"):
                if not full_path.exists():
                    version_missing.append(path)
            else:
                if not full_path.exists():
                    version_missing.append(path)

        if version_missing:
            missing[version] = version_missing

    return missing


def get_pending_migrations() -> List[str]:
    state = load_migration_state()
    applied = set(state.get("migrations_applied", []))
    pending = []

    for version in MIGRATIONS.keys():
        if version not in applied:
            pending.append(version)

    return pending


def create_directory(path: Path) -> bool:
    try:
        path.mkdir(parents=True, exist_ok=True)
        gitkeep = path / ".gitkeep"
        if not gitkeep.exists():
            gitkeep.write_text("", encoding="utf-8")
        return True
    except Exception as e:
        safe_print(c(f"  [ERROR] Creando directorio {path}: {e}", Colors.RED))
        return False


def create_json_file(path: Path, initial_content: Dict = None) -> bool:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        if initial_content is None:
            initial_content = {}
        content = json.dumps(initial_content, indent=2, ensure_ascii=False)
        path.write_text(content, encoding="utf-8")
        return True
    except Exception as e:
        safe_print(c(f"  [ERROR] Creando archivo {path}: {e}", Colors.RED))
        return False


def run_migration_script(script_name: str) -> bool:
    script_path = SCRIPT_DIR / script_name
    if not script_path.exists():
        safe_print(c(f"  [SKIP] Script no encontrado: {script_name}", Colors.YELLOW))
        return True

    try:
        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True,
            timeout=60,
        )
        if result.returncode == 0:
            safe_print(c(f"  [OK] Script ejecutado: {script_name}", Colors.GREEN))
            return True
        else:
            safe_print(c(f"  [WARN] Script con errores: {script_name}", Colors.YELLOW))
            if result.stderr:
                safe_print(f"    {result.stderr[:200]}")
            return True
    except subprocess.TimeoutExpired:
        safe_print(c(f"  [WARN] Script timeout: {script_name}", Colors.YELLOW))
        return True
    except Exception as e:
        safe_print(c(f"  [ERROR] Ejecutando script {script_name}: {e}", Colors.RED))
        return False


def apply_migration(version: str, force: bool = False) -> bool:
    if version not in MIGRATIONS:
        safe_print(
            c(f"[ERROR] Version de migracion desconocida: {version}", Colors.RED)
        )
        return False

    migration = MIGRATIONS[version]
    name = migration.get("name", "unknown")
    description = migration.get("description", "")

    safe_print(
        c(f"\n[MIGRATE] Aplicando {version} - {name}", Colors.BOLD + Colors.CYAN)
    )
    safe_print(f"  {description}")

    state = load_migration_state()

    if not force and version in state.get("migrations_applied", []):
        safe_print(
            c(f"  [SKIP] Ya aplicada (use --force-all para forzar)", Colors.YELLOW)
        )
        return True

    errors = []

    for path in migration.get("creates", []):
        full_path = REPO_ROOT / path
        if path.endswith("/"):
            safe_print(f"  [DIR] Creando: {path}")
            if not create_directory(full_path):
                errors.append(f"dir:{path}")
        else:
            safe_print(f"  [FILE] Creando: {path}")
            initial = {}
            if "sessions-index.json" in path:
                initial = {"sessions": [], "total_sessions": 0, "last_updated": None}
            elif "skills-index.json" in path:
                initial = {"skills": [], "total_skills": 0, "last_updated": None}
            elif "agents-index.json" in path:
                initial = {"agents": [], "total_agents": 0, "last_updated": None}

            if not create_json_file(full_path, initial):
                errors.append(f"file:{path}")

    for script in migration.get("scripts", []):
        safe_print(f"  [SCRIPT] Ejecutando: {script}")
        if not run_migration_script(script):
            errors.append(f"script:{script}")

    if version not in state.get("migrations_applied", []):
        state["migrations_applied"].append(version)

    state["last_migration"] = datetime.now().isoformat()
    state["migrations_log"].append(
        {
            "version": version,
            "name": name,
            "timestamp": datetime.now().isoformat(),
            "errors": errors if errors else None,
            "success": len(errors) == 0,
        }
    )

    save_migration_state(state)

    if errors:
        safe_print(
            c(f"  [WARN] Migracion completada con errores: {errors}", Colors.YELLOW)
        )
        return False
    else:
        safe_print(c(f"  [OK] Migracion completada exitosamente", Colors.GREEN))
        return True


def run_all_pending(force: bool = False) -> Tuple[int, int]:
    pending = get_pending_migrations() if not force else list(MIGRATIONS.keys())

    if not pending:
        safe_print(c("\n[MIGRATE] No hay migraciones pendientes", Colors.GREEN))
        return 0, 0

    safe_print(
        c(
            f"\n[MIGRATE] Ejecutando {len(pending)} migracion(es)...",
            Colors.BOLD + Colors.CYAN,
        )
    )

    success = 0
    failed = 0

    for version in pending:
        if apply_migration(version, force=force):
            success += 1
        else:
            failed += 1

    return success, failed


def show_status():
    safe_print(c("\n" + "=" * 60, Colors.HEADER))
    safe_print(c("[STATUS] Estado de Migraciones", Colors.BOLD + Colors.CYAN))
    safe_print(c("=" * 60, Colors.HEADER))

    current_version = get_framework_version()
    state = load_migration_state()
    applied = set(state.get("migrations_applied", []))

    safe_print(f"\n  [VERSION] Framework: {current_version}")
    safe_print(f"  [VERSION] Ultima migracion: {state.get('last_migration', 'Nunca')}")

    safe_print(c("\n  [MIGRATIONS] Migraciones disponibles:", Colors.CYAN))

    for version, migration in MIGRATIONS.items():
        status = (
            c("[OK]", Colors.GREEN)
            if version in applied
            else c("[PENDING]", Colors.YELLOW)
        )
        name = migration.get("name", "unknown")
        desc = migration.get("description", "")[:40]
        safe_print(f"    {status} {version}: {name}")
        safe_print(f"        {desc}")

    pending = get_pending_migrations()
    if pending:
        safe_print(
            c(f"\n  [PENDING] {len(pending)} migracion(es) pendiente(s)", Colors.YELLOW)
        )
    else:
        safe_print(c("\n  [OK] Todas las migraciones aplicadas", Colors.GREEN))

    missing = detect_missing_structures()
    if missing:
        safe_print(c("\n  [WARN] Estructuras faltantes detectadas:", Colors.YELLOW))
        for ver, items in missing.items():
            safe_print(f"    {ver}:")
            for item in items:
                safe_print(f"      - {item}")
    else:
        safe_print(c("\n  [OK] Todas las estructuras estan presentes", Colors.GREEN))

    safe_print(c("\n" + "-" * 60, Colors.DIM))


def check_migrations():
    safe_print(c("\n" + "=" * 60, Colors.HEADER))
    safe_print(c("[CHECK] Verificacion de Migraciones", Colors.BOLD + Colors.CYAN))
    safe_print(c("=" * 60, Colors.HEADER))

    current_version = get_framework_version()
    state = load_migration_state()
    applied = set(state.get("migrations_applied", []))

    safe_print(f"\n  [VERSION] Framework actual: {current_version}")

    pending = get_pending_migrations()

    if pending:
        safe_print(
            c(f"\n  [PENDING] Migraciones pendientes: {len(pending)}", Colors.YELLOW)
        )
        for version in pending:
            migration = MIGRATIONS.get(version, {})
            safe_print(f"    - {version}: {migration.get('name', 'unknown')}")
        safe_print(
            c("\n  Ejecuta: python core/scripts/migrate.py --apply", Colors.CYAN)
        )
        return 1
    else:
        safe_print(c("\n  [OK] Todas las migraciones aplicadas", Colors.GREEN))

    missing = detect_missing_structures()
    if missing:
        safe_print(
            c(
                f"\n  [WARN] Estructuras faltantes detectadas en {len(missing)} version(es)",
                Colors.YELLOW,
            )
        )
        safe_print("  Ejecuta: python core/scripts/migrate.py --apply")
        return 1

    safe_print(c("\n  [OK] Framework en estado correcto", Colors.GREEN))
    return 0


def main():
    parser = argparse.ArgumentParser(
        description="PA Framework - Sistema de Migracion",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
    python core/scripts/migrate.py --check       Verificar migraciones pendientes
    python core/scripts/migrate.py --apply        Aplicar migraciones pendientes
    python core/scripts/migrate.py --status       Mostrar estado completo
    python core/scripts/migrate.py --force-all    Forzar todas las migraciones
        """,
    )

    parser.add_argument(
        "--check",
        action="store_true",
        help="Verificar migraciones pendientes",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Aplicar migraciones pendientes",
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Mostrar estado actual de migraciones",
    )
    parser.add_argument(
        "--force-all",
        action="store_true",
        help="Forzar todas las migraciones (re-aplicar)",
    )

    args = parser.parse_args()

    num_actions = sum([args.check, args.apply, args.status, args.force_all])

    if num_actions == 0:
        parser.print_help()
        return 0

    if num_actions > 1:
        safe_print(
            c("[ERROR] Solo se puede especificar una accion a la vez", Colors.RED)
        )
        return 1

    if args.check:
        return check_migrations()

    if args.status:
        show_status()
        return 0

    if args.apply:
        success, failed = run_all_pending(force=False)
        safe_print(
            c(f"\n[RESULT] Exitosas: {success}, Fallidas: {failed}", Colors.CYAN)
        )
        return 0 if failed == 0 else 1

    if args.force_all:
        safe_print(c("\n[WARN] Forzando todas las migraciones...", Colors.YELLOW))
        success, failed = run_all_pending(force=True)
        safe_print(
            c(f"\n[RESULT] Exitosas: {success}, Fallidas: {failed}", Colors.CYAN)
        )
        return 0 if failed == 0 else 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
