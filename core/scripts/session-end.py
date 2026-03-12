#!/usr/bin/env python3
"""
PA Framework — Session End with Multi-CLI Support
Secuencia de cierre ordenado de sesión con soporte para múltiples CLIs.

Uso:
    python core/scripts/session-end.py
    python core/scripts/session-end.py --summary
    python core/scripts/session-end.py --force
    python core/scripts/session-end.py --rebuild-index
    python core/scripts/session-end.py --skip-error-recovery

Multi-CLI:
    Este script coordina el cierre de sesión con otras instancias CLI
    activas, liberando locks y sincronizando cambios pendientes.

Error Recovery (PRP-007):
    Integra el sistema de recuperación de errores, migrando errores
    no resueltos a recordatorios.md y actualizando el análisis de tendencias.

Autor: FreakingJSON-PA Framework
Version: 1.1.0 (Multi-CLI + Error Recovery)
"""

import argparse
import json
import os
import re
import sys
import atexit
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
SESSIONS_DIR = CONTEXT_DIR / "sessions"
CODEBASE_DIR = CONTEXT_DIR / "codebase"
KNOWLEDGE_DIR = CONTEXT_DIR / "knowledge"

_coordinator = None
_silent_mode = False
_error_recovery_available = False

get_unresolved_errors = None
resolve_error = None
generate_trend_report = None

try:
    sys.path.insert(0, str(SCRIPT_DIR))
    from error_logger import get_unresolved_errors as _get_unresolved_errors
    from error_logger import resolve_error as _resolve_error
    from pattern_analyzer import generate_trend_report as _generate_trend_report

    get_unresolved_errors = _get_unresolved_errors
    resolve_error = _resolve_error
    generate_trend_report = _generate_trend_report
    _error_recovery_available = True
except ImportError:
    pass

_knowledge_extraction_available = False
try:
    from knowledge_extractor import extract_all_knowledge as _extract_all_knowledge

    _knowledge_extraction_available = True
except ImportError:
    pass

_enforcement_available = False
try:
    from framework_guardian import FrameworkGuardian as _FrameworkGuardian

    _enforcement_available = True
except ImportError:
    pass


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


def init_multi_cli_coordinator(model: str = "unknown"):
    global _coordinator
    try:
        sys.path.insert(0, str(SCRIPT_DIR))
        from multi_cli_coordinator import MultiCLICoordinator

        _coordinator = MultiCLICoordinator(model=model)
        return _coordinator
    except Exception:
        return None


def shutdown_coordinator():
    global _coordinator
    if _coordinator:
        try:
            _coordinator.shutdown()
        except Exception:
            pass


# --- BACKUP SYSTEM (v0.2.0) ---
def backup_critical_files() -> bool:
    """Crea backup de archivos críticos antes de modificar."""
    import shutil

    backup_dir = CONTEXT_DIR / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    critical_files = [
        CODEBASE_DIR / "recordatorios.md",
        CODEBASE_DIR / "ideas.md",
        KNOWLEDGE_DIR / "sessions-index.json",
    ]

    backed_up = 0
    for file_path in critical_files:
        if file_path.exists():
            backup_name = f"{file_path.stem}_{timestamp}{file_path.suffix}"
            backup_path = backup_dir / backup_name
            try:
                shutil.copy2(file_path, backup_path)
                backed_up += 1
            except Exception:
                pass

    # Limpiar backups antiguos (>7 días)
    try:
        import time

        for old_backup in backup_dir.glob("*"):
            if old_backup.stat().st_mtime < time.time() - 7 * 24 * 3600:
                old_backup.unlink()
    except Exception:
        pass

    return backed_up > 0


def get_today_session_file() -> Optional[Path]:
    today = datetime.now().strftime("%Y-%m-%d")
    session_file = SESSIONS_DIR / f"{today}.md"
    if session_file.exists():
        return session_file
    return None


def update_end_time(session_file: Path) -> bool:
    try:
        content = session_file.read_text(encoding="utf-8")
        now = datetime.now()
        time_str = now.strftime("%H:%M")

        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                frontmatter = parts[1]
                if "time_end:" in frontmatter:
                    frontmatter = re.sub(
                        r"time_end:\s*.*", f"time_end: {time_str}", frontmatter
                    )
                else:
                    frontmatter += f"\ntime_end: {time_str}"
                content = "---" + frontmatter + "\n---" + parts[2]
        else:
            if "## Inicio" in content:
                inicio_match = re.search(
                    r"(##\s+Inicio.*?)(##\s+Log)", content, re.DOTALL
                )
                if inicio_match:
                    inicio_section = inicio_match.group(1)
                    if "**Hora**:" in inicio_section:
                        inicio_section = re.sub(
                            r"(\*\*Hora\*\*:\s*\d+:\d+)",
                            f"\\1 - **Fin**: {time_str}",
                            inicio_section,
                        )
                        content = content.replace(inicio_match.group(1), inicio_section)

        if "status: active" in content:
            content = content.replace("status: active", "status: completed")

        session_file.write_text(content, encoding="utf-8")
        return True
    except Exception as e:
        if not _silent_mode:
            safe_print(c(f"[WARN] Error actualizando time_end: {e}", Colors.YELLOW))
        return False


def generate_summary(session_file: Path) -> Dict:
    summary = {
        "topics": [],
        "decisions": [],
        "pendientes": [],
        "files_modified": [],
        "interactions": 0,
        "title": "",
        "duration": "",
    }

    try:
        content = session_file.read_text(encoding="utf-8")

        title_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
        if title_match:
            summary["title"] = title_match.group(1).strip()

        time_start = None
        time_end = None
        start_match = re.search(r"\*\*Hora\*\*:\s*(\d+:\d+)", content)
        if start_match:
            time_start = start_match.group(1)
        end_match = re.search(r"\*\*Fin\*\*:\s*(\d+:\d+)", content)
        if end_match:
            time_end = end_match.group(1)
        if time_start:
            summary["duration"] = f"{time_start} - {time_end or 'ahora'}"

        topics_match = re.search(
            r"##\s+Temas\s*Tratados.*?\n(.+?)(?=\n##|\Z)", content, re.DOTALL
        )
        if topics_match:
            bullets = re.findall(r"[-*]\s*(.+?)(?:\n|$)", topics_match.group(1))
            summary["topics"] = [b.strip() for b in bullets if b.strip()][:5]

        decisions_match = re.search(
            r"##\s+Decisiones.*?\n(.+?)(?=\n##|\Z)", content, re.DOTALL
        )
        if decisions_match:
            items = re.findall(
                r"(?:\d+\.|[-*])\s*(.+?)(?:\n|$)", decisions_match.group(1)
            )
            summary["decisions"] = [i.strip() for i in items if i.strip()][:5]

        pendientes_match = re.search(
            r"##\s+Pendientes.*?\n(.+?)(?=\n##|\Z)", content, re.DOTALL
        )
        if pendientes_match:
            # Solo extraer pendientes NO completados (- [ ] no - [x])
            items = re.findall(
                r"[-*]\s*\[\s*\]\s*(.+?)(?:\n|$)", pendientes_match.group(1)
            )
            summary["pendientes"] = [i.strip() for i in items if i.strip()][:10]

        file_patterns = [
            r"`([^`]+\.(?:py|md|json|js|html|css|sh|bat|yaml|yml))`",
            r"(?:archivo|file|modificado)\s*:?\s*`?([^`\n]+\.(?:py|md|json|js|html|css|sh|bat))`?",
        ]
        files = set()
        for pattern in file_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            files.update(matches)
        summary["files_modified"] = list(files)[:10]

        interactions = len(re.findall(r"^[-*]\s+", content, re.MULTILINE))
        summary["interactions"] = interactions

    except Exception as e:
        if not _silent_mode:
            safe_print(c(f"[WARN] Error generando resumen: {e}", Colors.YELLOW))

    return summary


def migrate_pendientes(pendientes: List[str]) -> bool:
    if not pendientes:
        return True

    recordatorios_file = CODEBASE_DIR / "recordatorios.md"
    if not recordatorios_file.exists():
        return False

    try:
        content = recordatorios_file.read_text(encoding="utf-8")

        pendientes_section_match = re.search(
            r"(##\s+Pendientes.*?\n)", content, re.DOTALL
        )
        if not pendientes_section_match:
            pendientes_insert = "\n## Pendientes\n\n"
            insert_pos = content.find("\n## Completados")
            if insert_pos == -1:
                insert_pos = len(content)
            content = content[:insert_pos] + pendientes_insert + content[insert_pos:]

        today = datetime.now().strftime("%Y-%m-%d")
        new_items = []
        for p in pendientes:
            if p and f"- [ ] {p}" not in content:
                new_items.append(f"- [ ] [{today}] {p}")

        if new_items:
            pendientes_section_match = re.search(
                r"(##\s+Pendientes.*?\n(?:.*?\n)*)", content, re.DOTALL
            )
            if pendientes_section_match:
                insert_point = pendientes_section_match.end()
                new_block = "\n### Sesion " + today + "\n" + "\n".join(new_items) + "\n"
                content = content[:insert_point] + new_block + content[insert_point:]

        recordatorios_file.write_text(content, encoding="utf-8")
        return True
    except Exception as e:
        if not _silent_mode:
            safe_print(c(f"[WARN] Error migrando pendientes: {e}", Colors.YELLOW))
        return False


def migrate_unresolved_errors() -> Tuple[bool, int]:
    if not _error_recovery_available or get_unresolved_errors is None:
        return True, 0

    try:
        unresolved = get_unresolved_errors()
        if not unresolved:
            return True, 0

        recordatorios_file = CODEBASE_DIR / "recordatorios.md"
        if not recordatorios_file.exists():
            return False, 0

        content = recordatorios_file.read_text(encoding="utf-8")

        if "## Errores Pendientes" not in content:
            insert_pos = content.find("\n## Completados")
            if insert_pos == -1:
                insert_pos = content.find("\n## Ideas")
            if insert_pos == -1:
                insert_pos = len(content)
            error_section = "\n## Errores Pendientes\n\n> Errores no resueltos migrados desde sessions.\n\n"
            content = content[:insert_pos] + error_section + content[insert_pos:]

        today = datetime.now().strftime("%Y-%m-%d")
        new_items = []
        for error in unresolved[:10]:
            error_id = error.get("id", "Unknown")
            error_type = error.get("type", "Unknown")
            error_msg = error.get("message", "")[:80]
            playbook = error.get("playbook_suggestion", "")
            playbook_hint = f" [{playbook}]" if playbook else ""
            item = f"- [ ] [{today}] **{error_id}** ({error_type}){playbook_hint}: {error_msg}"
            if item not in content:
                new_items.append(item)

        if new_items:
            errors_section_match = re.search(
                r"(##\s+Errores\s+Pendientes.*?\n(?:.*?\n)*)", content, re.DOTALL
            )
            if errors_section_match:
                insert_point = errors_section_match.end()
                new_block = (
                    "\n### Session " + today + "\n" + "\n".join(new_items) + "\n"
                )
                content = content[:insert_point] + new_block + content[insert_point:]
                recordatorios_file.write_text(content, encoding="utf-8")

        return True, len(new_items)
    except Exception as e:
        if not _silent_mode:
            safe_print(
                c(f"[WARN] Error migrando errores no resueltos: {e}", Colors.YELLOW)
            )
        return False, 0


def get_error_stats() -> Dict:
    if not _error_recovery_available or get_unresolved_errors is None:
        return {"total": 0, "unresolved": 0, "available": False}

    try:
        errors = get_unresolved_errors()
        return {
            "total": len(errors),
            "unresolved": len(errors),
            "available": True,
        }
    except Exception:
        return {"total": 0, "unresolved": 0, "available": False}


def run_knowledge_extraction(session_file: Path) -> Dict:
    """
    Run knowledge extraction from session file.
    Returns stats about extracted items.
    """
    if not _knowledge_extraction_available:
        return {"available": False}

    try:
        return _extract_all_knowledge(session_file)
    except Exception as e:
        if not _silent_mode:
            safe_print(c(f"[WARN] Knowledge extraction failed: {e}", Colors.YELLOW))
        return {"available": False, "error": str(e)}


def index_session(rebuild: bool = False) -> bool:
    try:
        import importlib.util

        indexer_path = SCRIPT_DIR / "session-indexer.py"
        spec = importlib.util.spec_from_file_location("session_indexer", indexer_path)
        if spec is None or spec.loader is None:
            return False
        session_indexer = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(session_indexer)
        SessionIndexer = session_indexer.SessionIndexer

        indexer = SessionIndexer()

        if rebuild:
            indexer.index["sessions"] = []
            indexer.index_all_sessions()
        else:
            today = datetime.now().strftime("%Y-%m-%d")
            today_file = SESSIONS_DIR / f"{today}.md"
            if today_file.exists():
                session = indexer.parse_session_file(today_file)
                if session:
                    existing_ids = {s["id"] for s in indexer.index["sessions"]}
                    if session["id"] in existing_ids:
                        for i, existing in enumerate(indexer.index["sessions"]):
                            if existing["id"] == session["id"]:
                                indexer.index["sessions"][i] = session
                                break
                    else:
                        indexer.index["sessions"].append(session)

                    indexer.index["sessions"].sort(key=lambda x: x["id"], reverse=True)
                    indexer.index["total_sessions"] = len(indexer.index["sessions"])
                    indexer.index["last_updated"] = datetime.now().isoformat()
                    indexer._update_filters()
                    indexer._save_index()

        return True
    except Exception as e:
        if not _silent_mode:
            safe_print(c(f"[WARN] Error indexando sesion: {e}", Colors.YELLOW))
        return False


def print_summary(summary: Dict):
    if _silent_mode:
        return

    print(c("\n" + "=" * 50, Colors.HEADER))
    print(c("[SUMMARY] Resumen de Sesion", Colors.BOLD + Colors.CYAN))
    print(c("=" * 50, Colors.HEADER))

    if summary["title"]:
        safe_print(f"\n  [TITLE] {summary['title']}")

    if summary["duration"]:
        safe_print(f"  [TIME] {summary['duration']}")

    if summary["topics"]:
        print(c("\n  [TOPICS] Temas Tratados:", Colors.CYAN))
        for topic in summary["topics"][:5]:
            # Remover emojis para compatibilidad Windows
            clean_topic = (
                topic.replace("✅", "[OK]").replace("❌", "[X]").replace("⚠️", "[!]")
            )
            safe_print(f"    - {clean_topic}")

    if summary["decisions"]:
        print(c("\n  [DECISIONS] Decisiones:", Colors.GREEN))
        for decision in summary["decisions"][:3]:
            clean_decision = (
                decision.replace("✅", "[OK]").replace("❌", "[X]").replace("⚠️", "[!]")
            )
            safe_print(f"    - {clean_decision}")

    if summary["pendientes"]:
        print(
            c(
                f"\n  [PENDING] Pendientes: {len(summary['pendientes'])} items",
                Colors.YELLOW,
            )
        )

    if summary["files_modified"]:
        print(
            c(
                f"\n  [FILES] Archivos modificados: {len(summary['files_modified'])}",
                Colors.DIM,
            )
        )

    if summary.get("knowledge_extraction", {}).get("available"):
        ke = summary["knowledge_extraction"]
        items = []
        if ke.get("discoveries", 0) > 0:
            items.append(f"{ke['discoveries']} discoveries")
        if ke.get("prompts", 0) > 0:
            items.append(f"{ke['prompts']} prompts")
        if ke.get("ideas", 0) > 0:
            items.append(f"{ke['ideas']} ideas")
        if ke.get("best_practices", 0) > 0:
            items.append(f"{ke['best_practices']} best practices")

        if items:
            print(c(f"\n  [KNOWLEDGE] Extraido: {', '.join(items)}", Colors.CYAN))
            print(c("  [INFO] Pendiente validacion en knowledge/", Colors.DIM))

    print(c("\n" + "-" * 50, Colors.DIM))


def close(
    force: bool = False,
    summary_only: bool = False,
    rebuild_index: bool = False,
    skip_error_recovery: bool = False,
) -> int:
    global _silent_mode

    session_file = get_today_session_file()

    if not session_file:
        if not _silent_mode:
            safe_print(c("[WARN] No hay sesion activa para cerrar", Colors.YELLOW))
        return 0

    if summary_only:
        summary = generate_summary(session_file)
        print_summary(summary)
        return 0

    backup_critical_files()

    errors = []

    if not force:
        summary = generate_summary(session_file)
    else:
        summary = {
            "topics": [],
            "decisions": [],
            "pendientes": [],
            "files_modified": [],
            "interactions": 0,
            "title": "",
            "duration": "",
        }

    if not update_end_time(session_file):
        errors.append("update_end_time")

    if not force:
        summary = generate_summary(session_file)

    if summary["pendientes"]:
        if not migrate_pendientes(summary["pendientes"]):
            errors.append("migrate_pendientes")

    error_stats = {"total": 0, "unresolved": 0, "available": False}
    errors_migrated = 0

    if not skip_error_recovery and _error_recovery_available:
        error_stats = get_error_stats()
        if error_stats["unresolved"] > 0:
            migrated, errors_migrated = migrate_unresolved_errors()
            if not migrated:
                errors.append("migrate_unresolved_errors")

        if generate_trend_report is not None:
            try:
                generate_trend_report()
            except Exception as e:
                if not _silent_mode:
                    safe_print(
                        c(f"[WARN] Error generando trend report: {e}", Colors.YELLOW)
                    )

    # === FRAMEWORK ENFORCEMENT CHECK ===
    if _enforcement_available and not skip_error_recovery:
        try:
            from framework_guardian import FrameworkGuardian

            guardian = FrameworkGuardian()
            results = guardian.run_validation(timing="session-end")
            failed = [r for r in results if not r.passed]
            if failed:
                safe_print(
                    c(f"\n[ENFORCEMENT] {len(failed)} check(s) failed:", Colors.YELLOW)
                )
                for r in failed:
                    safe_print(c(f"  - {r.check_id}: {r.message}", Colors.YELLOW))
                    if r.fix_suggestion:
                        safe_print(c(f"    Fix: {r.fix_suggestion}", Colors.DIM))
        except ImportError:
            pass

    knowledge_stats = {"available": False}

    if not skip_error_recovery and _knowledge_extraction_available:
        knowledge_stats = run_knowledge_extraction(session_file)
        if knowledge_stats.get("available"):
            summary["knowledge_extraction"] = knowledge_stats

    if not index_session(rebuild=rebuild_index):
        errors.append("index_session")

    shutdown_coordinator()

    if _silent_mode:
        safe_print(c("[OK] Sesion cerrada", Colors.GREEN))
    else:
        print(c("\n" + "=" * 50, Colors.HEADER))
        print(c("[CLOSE] Sesion cerrada correctamente", Colors.BOLD + Colors.GREEN))
        print(c("=" * 50, Colors.HEADER))
        print_summary(summary)

        if error_stats.get("available") and error_stats["unresolved"] > 0:
            print(
                c(
                    f"\n  [ERRORS] Errores no resueltos: {error_stats['unresolved']} (migrados: {errors_migrated})",
                    Colors.YELLOW,
                )
            )

        if knowledge_stats.get("available"):
            ke = knowledge_stats
            total = sum(
                [
                    ke.get("discoveries", 0),
                    ke.get("prompts", 0),
                    ke.get("ideas", 0),
                    ke.get("best_practices", 0),
                ]
            )
            if total > 0:
                print(
                    c(
                        f"\n  [KNOWLEDGE] Extraidos {total} items para validacion",
                        Colors.CYAN,
                    )
                )

        if errors:
            safe_print(
                c(
                    f"\n[WARN] Algunos pasos fallaron: {', '.join(errors)}",
                    Colors.YELLOW,
                )
            )

    return 1 if errors else 0


def silent_close():
    global _silent_mode
    _silent_mode = True
    try:
        close(force=True)
    except Exception:
        pass


def main():
    parser = argparse.ArgumentParser(description="PA Framework - Session End Script")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Forzar cierre sin validaciones",
    )
    parser.add_argument(
        "--summary",
        action="store_true",
        help="Solo mostrar resumen sin cerrar",
    )
    parser.add_argument(
        "--rebuild-index",
        action="store_true",
        help="Reconstruir indice completo",
    )
    parser.add_argument(
        "--silent",
        action="store_true",
        help="Modo silencioso (para atexit)",
    )

    args = parser.parse_args()

    global _silent_mode
    _silent_mode = args.silent

    if _silent_mode:
        atexit.register(silent_close)
        return 0

    model = os.environ.get("PA_MODEL", "unknown")
    init_multi_cli_coordinator(model)

    return close(
        force=args.force, summary_only=args.summary, rebuild_index=args.rebuild_index
    )


if __name__ == "__main__":
    sys.exit(main())
