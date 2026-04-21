#!/usr/bin/env python3
"""
PA Framework — Memory Pipeline
================================
Orquestador central para el sistema de memoria persistente.
Combina 3 modos de ejecución:

  MODE A: Session Start   - Cargar contexto al iniciar
  MODE B: Interval Timer - Ejecutar cada N minutos (configurable)
  MODE C: Session End    - Guardar estado completo al cerrar

Usage:
    # MODE A: Cargar contexto (para session_start.py)
    python memory_pipeline.py --load-context

    # MODE B: Ejecutar en intervalo (background)
    python memory_pipeline.py --watch --interval 15

    # MODE C: Ejecutar ciclo completo (para session_end.py)
    python memory_pipeline.py --full-cycle

    # Estado actual
    python memory_pipeline.py --status

    # Configurar intervalo
    python memory_pipeline.py --set-interval 30

Version: 1.1.0
Autor: PA Framework
"""

import argparse
import json
import os
import sys
import time
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

# Paths
SCRIPT_DIR = Path(__file__).resolve().parent
CORE_DIR = SCRIPT_DIR.parent
REPO_ROOT = CORE_DIR.parent
CONTEXT_DIR = CORE_DIR / ".context"
SESSIONS_DIR = CONTEXT_DIR / "sessions"
MEMORY_DIR = CONTEXT_DIR / "memory"
CHECKPOINTS_DIR = CONTEXT_DIR / "checkpoints"
KNOWLEDGE_DIR = CONTEXT_DIR / "knowledge"

# Config file
CONFIG_FILE = REPO_ROOT / "config" / "framework.yaml"


class Colors:
    """Windows-safe ASCII markers."""

    GREEN = "[+]"
    RED = "[-]"
    YELLOW = "[!]"
    BLUE = "[*]"
    CYAN = "[=]"
    RESET = ""


def log(msg: str, color: Optional[str] = None) -> None:
    """Print with color support."""
    if color:
        print(f"{color}{msg}{Colors.RESET}")
    else:
        print(msg)


def log_header(msg: str) -> None:
    """Print section header."""
    log(f"\n{'=' * 60}", Colors.CYAN)
    log(f"  {msg}", Colors.CYAN)
    log(f"{'=' * 60}\n", Colors.CYAN)


# =============================================================================
# CONFIGURATION
# =============================================================================


def get_config() -> Dict[str, Any]:
    """Load framework configuration."""
    default_config = {
        "memory_pipeline": {
            "enabled": True,
            "interval_minutes": 15,
            "modes": {
                "session_start": True,
                "interval": True,
                "session_end": True,
            },
            "memory_dir": "core/.context/memory",
            "max_sessions_in_context": 3,
            "max_context_length": 2000,
        }
    }

    if not CONFIG_FILE.exists():
        return default_config

    try:
        import yaml

        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f) or {}
        return {**default_config, **config}
    except ImportError:
        return default_config


def save_config(config: Dict[str, Any]) -> bool:
    """Save framework configuration."""
    try:
        CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
        import yaml

        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
        return True
    except Exception as e:
        log(f"Error saving config: {e}", Colors.RED)
        return False


def get_interval() -> int:
    """Get configured interval in minutes."""
    config = get_config()
    return config.get("memory_pipeline", {}).get("interval_minutes", 15)


def set_interval(minutes: int) -> bool:
    """Set interval in minutes."""
    config = get_config()
    if "memory_pipeline" not in config:
        config["memory_pipeline"] = {}
    config["memory_pipeline"]["interval_minutes"] = minutes
    log(f"Interval set to {minutes} minutes", Colors.GREEN)
    return save_config(config)


# =============================================================================
# MEMORY DIRECTORY
# =============================================================================


def ensure_memory_dir() -> Path:
    """Ensure memory directory exists."""
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)

    # Create subdirectories
    (MEMORY_DIR / "summaries").mkdir(exist_ok=True)
    (MEMORY_DIR / "context").mkdir(exist_ok=True)
    (MEMORY_DIR / "profile").mkdir(exist_ok=True)

    return MEMORY_DIR


def get_memory_file(name: str) -> Path:
    """Get path to memory file."""
    ensure_memory_dir()
    return MEMORY_DIR / name


# =============================================================================
# EXISTING SCRIPTS WRAPPERS
# =============================================================================


def run_session_saver() -> bool:
    """Run session saver for checkpoint."""
    try:
        result = os.system(f'"{sys.executable}" "{SCRIPT_DIR / "session_saver.py"}"')
        return result == 0
    except Exception as e:
        log(f"[WARN] Session saver failed: {e}", Colors.YELLOW)
        return False


def run_knowledge_miner() -> bool:
    """Run knowledge miner."""
    try:
        result = os.system(
            f'"{sys.executable}" "{SCRIPT_DIR / "knowledge_miner.py"}" --quiet'
        )
        return result == 0
    except Exception as e:
        log(f"[WARN] Knowledge miner failed: {e}", Colors.YELLOW)
        return False


def run_knowledge_extractor() -> bool:
    """Run knowledge extractor."""
    try:
        result = os.system(
            f'"{sys.executable}" "{SCRIPT_DIR / "knowledge_extractor.py"}"'
        )
        return result == 0
    except Exception as e:
        log(f"[WARN] Knowledge extractor failed: {e}", Colors.YELLOW)
        return False


def run_wiki_autopopulate() -> bool:
    """Run wiki autopopulate."""
    try:
        result = os.system(
            f'"{sys.executable}" "{SCRIPT_DIR / "wiki_autopopulate.py"}"'
        )
        return result == 0
    except Exception as e:
        log(f"[WARN] Wiki autopopulate failed: {e}", Colors.YELLOW)
        return False


def run_kb_updater() -> bool:
    """Run knowledge base updater (relationships + indexes)."""
    try:
        result = os.system(f'"{sys.executable}" "{SCRIPT_DIR / "kb_updater.py"}"')
        return result == 0
    except Exception as e:
        log(f"[WARN] KB updater failed: {e}", Colors.YELLOW)
        return False


def run_memory_sync() -> bool:
    """Run memory/wiki structural sync and validation."""
    try:
        result = os.system(f'"{sys.executable}" "{SCRIPT_DIR / "memory_sync.py"}"')
        return result == 0
    except Exception as e:
        log(f"[WARN] Memory sync failed: {e}", Colors.YELLOW)
        return False


def run_context_loader_tier(tier: int = 1) -> bool:
    """Initialize context loader tiers."""
    try:
        # Just ensure context is ready
        return True
    except Exception as e:
        log(f"[WARN] Context loader failed: {e}", Colors.YELLOW)
        return False


# =============================================================================
# PIPELINE CORE
# =============================================================================


def load_session_state() -> Dict[str, Any]:
    """Load last session state from memory."""
    state_file = get_memory_file("session.json")

    if not state_file.exists():
        return {
            "has_previous_session": False,
            "last_session_date": None,
            "context": None,
        }

    try:
        with open(state_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {
            "has_previous_session": False,
            "last_session_date": None,
            "context": None,
        }


def save_session_state(state: Dict[str, Any]) -> bool:
    """Save session state to memory."""
    state_file = get_memory_file("session.json")

    try:
        with open(state_file, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        log(f"[ERROR] Failed to save session state: {e}", Colors.RED)
        return False


def generate_context_injection() -> str:
    """Generate context injection text for next session."""
    state = load_session_state()

    if not state.get("has_previous_session"):
        return ""

    context_parts = []

    # Last session info
    if state.get("last_session_date"):
        context_parts.append(f"Última sesión: {state['last_session_date']}")

    # Topics
    topics = state.get("topics", [])
    if topics:
        context_parts.append(f"Temas activos: {', '.join(topics)}")

    # Decisions
    decisions = state.get("decisions", [])
    if decisions:
        lines = ["Decisiones tomadas:"]
        for d in decisions[-3:]:  # Last 3
            lines.append(f"  - {d}")
        context_parts.append("\n".join(lines))

    # Pending tasks
    pending = state.get("pending_tasks", [])
    if pending:
        lines = ["Tareas pendientes:"]
        for p in pending:
            lines.append(f"  - {p}")
        context_parts.append("\n".join(lines))

    if not context_parts:
        return ""

    return "\n\n".join(context_parts)


def save_context_injection() -> bool:
    """Save context injection to file."""
    context_file = MEMORY_DIR / "context_injection.md"
    content = generate_context_injection()

    try:
        if content:
            context_file.write_text(content, encoding="utf-8")
            log(f"Context injection saved: {context_file.name}", Colors.GREEN)
        else:
            # Empty but exists
            context_file.write_text("", encoding="utf-8")
        return True
    except Exception as e:
        log(f"[ERROR] Failed to save context injection: {e}", Colors.RED)
        return False


def generate_session_summary(session_file: Path) -> str:
    """Generate session summary."""
    if not session_file.exists():
        return ""

    try:
        content = session_file.read_text(encoding="utf-8")

        # Extract key info (simplified)
        lines = content.split("\n")

        summary = {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "time_start": "",
            "time_end": "",
            "topics": [],
            "decisions": [],
            "pending": [],
            "file": str(session_file.name),
        }

        # Parse content for key sections
        in_topics = False
        in_decisions = False
        in_pending = False

        for line in lines:
            line = line.strip()

            if line.startswith("## "):
                in_topics = "Tema" in line or "Topics" in line
                in_decisions = "Decisión" in line or "Decision" in line
                in_pending = "Pendiente" in line or "Pending" in line
                continue

            if in_topics and line.startswith("-"):
                summary["topics"].append(line[1:].strip())
            elif in_decisions and line.startswith("-"):
                summary["decisions"].append(line[1:].strip())
            elif in_pending and line.startswith("-"):
                summary["pending"].append(line[1:].strip())

        return json.dumps(summary, ensure_ascii=False, indent=2)
    except Exception:
        return "{}"


def save_session_summary() -> bool:
    """Save current session summary."""
    today = datetime.now().strftime("%Y-%m-%d")
    session_file = SESSIONS_DIR / f"{today}.md"

    summary = generate_session_summary(session_file)
    summary_file = MEMORY_DIR / "summaries" / f"{today}-summary.md"

    try:
        summary_file.write_text(summary, encoding="utf-8")
        return True
    except Exception as e:
        log(f"[ERROR] Failed to save session summary: {e}", Colors.RED)
        return False


def extract_current_knowledge() -> Dict[str, Any]:
    """Extract knowledge from current session."""
    today = datetime.now().strftime("%Y-%m-%d")
    session_file = SESSIONS_DIR / f"{today}.md"

    knowledge = {
        "topics": [],
        "decisions": [],
        "insights": [],
    }

    if not session_file.exists():
        return knowledge

    try:
        content = session_file.read_text(encoding="utf-8")

        # Simple tag-based extraction
        for line in content.split("\n"):
            line = line.strip()

            # Topics (#discovery, #idea)
            if "#discovery" in line.lower() or "#idea" in line.lower():
                knowledge["topics"].append(line)

            # Decisions
            if "-decisión" in line.lower() or "- decisión" in line.lower():
                knowledge["decisions"].append(line)

            # Insights
            if "#insight" in line.lower():
                knowledge["insights"].append(line)

        return knowledge
    except Exception:
        return knowledge


def update_profile(knowledge: Dict[str, Any]) -> bool:
    """Update user profile with extracted knowledge."""
    profile_file = MEMORY_DIR / "profile" / "user.md"

    profile_lines = [
        "# User Profile",
        "",
        f"## Last Updated",
        f"- {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "",
        f"## Topics",
    ]

    for topic in knowledge.get("topics", [])[:10]:
        profile_lines.append(f"- {topic}")

    profile_lines.extend(["", "## Decisions", ""])
    for decision in knowledge.get("decisions", [])[:5]:
        profile_lines.append(f"- {decision}")

    try:
        ensure_memory_dir()
        profile_file.write_text("\n".join(profile_lines), encoding="utf-8")
        return True
    except Exception as e:
        log(f"[ERROR] Failed to update profile: {e}", Colors.RED)
        return False


# =============================================================================
# PIPELINE MODES
# =============================================================================


def run_mode_a_session_start() -> str:
    """
    MODE A: Session Start
    Cargar contexto de sesiones anteriores.
    """
    log_header("Memory Pipeline - MODE A: Session Start")

    context_file = MEMORY_DIR / "context_injection.md"

    if not context_file.exists():
        log("No previous context found", Colors.YELLOW)
        return ""

    try:
        content = context_file.read_text(encoding="utf-8")
        if content:
            log(f"Context loaded: {len(content)} chars", Colors.GREEN)
            return content
        else:
            log("Context is empty", Colors.YELLOW)
            return ""
    except Exception as e:
        log(f"[ERROR] Failed to load context: {e}", Colors.RED)
        return ""


def run_mode_b_interval() -> bool:
    """
    MODE B: Interval Timer
    Ejecutar ciclo integral de memoria cada N minutos.
    """
    log_header("Memory Pipeline - MODE B: Interval")

    # Integral 4-layer cycle (persist + structure + relational sync)
    results = {
        "checkpoint": run_session_saver(),            # .md/session checkpoint
        "knowledge": run_knowledge_miner(),           # mined artifacts
        "extractor": run_knowledge_extractor(),       # memory/intermediate extraction
        "wiki": run_wiki_autopopulate(),              # wiki pages
        "kb": run_kb_updater(),                       # relationships + indexes
        "sync": run_memory_sync(),                    # schema/structure validation
    }

    # Save current state
    knowledge = extract_current_knowledge()
    state = {
        "has_previous_session": True,
        "last_session_date": datetime.now().strftime("%Y-%m-%d"),
        "topics": knowledge.get("topics", []),
        "decisions": knowledge.get("decisions", []),
        "pending_tasks": knowledge.get("insights", []),
    }
    save_session_state(state)

    # Update profile
    update_profile(knowledge)

    successful = sum(1 for v in results.values() if v)
    total_steps = len(results)
    log(
        f"Integral interval cycle complete: {successful}/{total_steps} steps",
        Colors.GREEN if successful == total_steps else Colors.YELLOW,
    )

    return successful > 0


def run_mode_c_session_end() -> bool:
    """
    MODE C: Session End
    Ejecutar consolidación integral y preparar próxima sesión.
    """
    log_header("Memory Pipeline - MODE C: Session End")

    # Integral close cycle
    results = {
        "checkpoint": run_session_saver(),
        "knowledge": run_knowledge_miner(),
        "extractor": run_knowledge_extractor(),
        "wiki": run_wiki_autopopulate(),
        "kb": run_kb_updater(),
        "sync": run_memory_sync(),
    }

    # Extract knowledge
    knowledge = extract_current_knowledge()

    # Update state
    state = {
        "has_previous_session": True,
        "last_session_date": datetime.now().strftime("%Y-%m-%d"),
        "topics": knowledge.get("topics", []),
        "decisions": knowledge.get("decisions", []),
        "pending_tasks": knowledge.get("insights", []),
        "completed": True,
    }
    save_session_state(state)

    # Generate outputs
    save_session_summary()
    save_context_injection()
    update_profile(knowledge)

    successful = sum(1 for v in results.values() if v)
    total_steps = len(results)
    log(
        f"Integral session-end cycle complete: {successful}/{total_steps} steps",
        Colors.GREEN if successful == total_steps else Colors.YELLOW,
    )

    return successful > 0


def run_full_cycle() -> bool:
    """Run full memory pipeline cycle."""
    return run_mode_c_session_end()


# =============================================================================
# WATCH MODE (BACKGROUND)
# =============================================================================


def run_watch_mode(interval_minutes: int = 15) -> None:
    """Run pipeline in watch mode (background timer)."""
    log_header(f"Memory Pipeline - Watch Mode")
    log(f"Interval: {interval_minutes} minutes")
    log("Press Ctrl+C to stop")

    session_active = True

    def signal_handler():
        nonlocal session_active
        session_active = False

    try:
        import signal

        signal.signal(signal.SIGINT, signal_handler)
    except Exception:
        pass

    while session_active:
        try:
            log(f"[{datetime.now().strftime('%H:%M:%S')}] Running interval cycle...")
            run_mode_b_interval()
            log("Sleeping...", Colors.CYAN)
            time.sleep(interval_minutes * 60)
        except KeyboardInterrupt:
            log("\n[INFO] Stopping watch mode", Colors.YELLOW)
            break
        except Exception as e:
            log(f"[ERROR] Watch loop error: {e}", Colors.RED)
            time.sleep(60)


# =============================================================================
# STATUS
# =============================================================================


def show_status() -> None:
    """Show memory pipeline status."""
    log_header("Memory Pipeline Status")

    config = get_config()
    mp_config = config.get("memory_pipeline", {})

    log(f"Enabled: {mp_config.get('enabled', True)}", Colors.GREEN)
    log(f"Interval: {mp_config.get('interval_minutes', 15)} min")

    # 4-layer health snapshot
    sessions_path = SESSIONS_DIR
    sqlite_path = REPO_ROOT / "data" / "sessions.db"
    memory_path = MEMORY_DIR
    wiki_path = CORE_DIR / ".context" / "knowledge" / "wiki"

    log(f"Layer sessions_md: {'OK' if sessions_path.exists() else 'MISSING'} ({sessions_path})")
    log(f"Layer sqlite: {'OK' if sqlite_path.exists() else 'MISSING'} ({sqlite_path})")
    log(f"Layer memory_md: {'OK' if memory_path.exists() else 'MISSING'} ({memory_path})")
    log(f"Layer wiki: {'OK' if wiki_path.exists() else 'MISSING'} ({wiki_path})")

    # Check memory directory
    if MEMORY_DIR.exists():
        files = list(MEMORY_DIR.rglob("*"))
        log(f"Memory files: {len([f for f in files if f.is_file()])}")
    else:
        log("Memory directory: Not created", Colors.YELLOW)

    # Check context injection
    context_file = MEMORY_DIR / "context_injection.md"
    if context_file.exists():
        content = context_file.read_text(encoding="utf-8")
        log(
            f"Context injection: {len(content)} chars",
            Colors.GREEN if content else Colors.YELLOW,
        )
    else:
        log("Context injection: Not found", Colors.YELLOW)

    # Last session
    state = load_session_state()
    if state.get("has_previous_session"):
        log(f"Last session: {state.get('last_session_date')}", Colors.GREEN)
    else:
        log("Previous session: None", Colors.YELLOW)

    # Profile
    profile_file = MEMORY_DIR / "profile" / "user.md"
    if profile_file.exists():
        log("User profile: Updated", Colors.GREEN)
    else:
        log("User profile: Not created", Colors.YELLOW)


# =============================================================================
# MAIN
# =============================================================================


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="PA Framework Memory Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Load context for session start
  python memory_pipeline.py --load-context

  # Run full cycle (session end)
  python memory_pipeline.py --full-cycle

  # Run in watch mode (every 15 min)
  python memory_pipeline.py --watch

  # Custom interval
  python memory_pipeline.py --watch --interval 30

  # Show status
  python memory_pipeline.py --status

  # Set interval
  python memory_pipeline.py --set-interval 20
        """,
    )

    parser.add_argument(
        "--load-context",
        action="store_true",
        help="Load context for session start (MODE A)",
    )
    parser.add_argument(
        "--full-cycle",
        action="store_true",
        help="Run full cycle (MODE C - session end)",
    )
    parser.add_argument(
        "--watch", action="store_true", help="Run in watch mode (MODE B - interval)"
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=15,
        help="Interval in minutes for watch mode (default: 15)",
    )
    parser.add_argument("--status", action="store_true", help="Show pipeline status")
    parser.add_argument(
        "--set-interval", type=int, metavar="MINUTES", help="Set interval configuration"
    )
    parser.add_argument("--quiet", action="store_true", help="Silence output")

    args = parser.parse_args()

    if args.quiet:
        # Redirect to null
        sys.stdout = open(os.devnull, "w")

    # Handle arguments
    if args.status:
        show_status()
        return 0

    if args.set_interval is not None:
        set_interval(args.set_interval)
        return 0

    if args.load_context:
        result = run_mode_a_session_start()
        if result:
            print(result)
        return 0

    if args.full_cycle:
        run_full_cycle()
        return 0

    if args.watch:
        run_watch_mode(args.interval)
        return 0

    # Default: show help
    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
