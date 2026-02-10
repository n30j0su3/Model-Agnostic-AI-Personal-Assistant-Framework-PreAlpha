#!/usr/bin/env python3
"""
Instalador Pre-Alpha simplificado.
Crea estructura, configura perfil y sincroniza contexto.
"""

import os
import platform
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
CORE_DIR = SCRIPT_DIR.parent
REPO_ROOT = CORE_DIR.parent
CONTEXT_DIR = CORE_DIR / ".context"

CLI_COMMANDS = ["opencode", "claude", "gemini", "codex"]
LOCAL_CLI_COMMANDS = ["ollama", "lms"]
CLI_LABELS = {
    "opencode": "OpenCode",
    "claude": "Claude Code",
    "gemini": "Gemini CLI",
    "codex": "Codex",
}

# Exported for compatibility
LLM_CLI_COMMANDS = CLI_COMMANDS
LLM_ENV_VARS = ["OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GEMINI_API_KEY"]
MIN_PYTHON = (3, 11)


class Colors:
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    CYAN = "\033[96m"
    BOLD = "\033[1m"
    END = "\033[0m"
    HEADER = "\033[95m"


def print_ok(m): print(f"{Colors.GREEN}  ✓ {m}{Colors.END}")
def print_warn(m): print(f"{Colors.YELLOW}  ⚠ {m}{Colors.END}")
def print_error(m): print(f"{Colors.RED}  ✗ {m}{Colors.END}")
def print_info(m): print(f"{Colors.CYAN}  ℹ {m}{Colors.END}")


def prompt_yes_no(msg, default=False):
    suffix = "[S/n]" if default else "[s/N]"
    choice = input(f"  {msg} {suffix}: ").strip().lower()
    if not choice:
        return default
    return choice in {"s", "si", "y", "yes"}


def configure_preferences(repo_root):
    """Configure user preferences interactively."""
    master = CONTEXT_DIR / "MASTER.md"
    if not master.exists():
        print_warn("MASTER.md no encontrado.")
        return
    print_info("Configuración de preferencias (Enter para mantener valor actual)")
    lang = input("  Idioma principal [es]: ").strip() or "es"
    style = input("  Estilo de respuesta [Claro y conciso]: ").strip() or "Claro y conciso; ampliar cuando sea necesario."
    return lang, style


def main():
    print(f"\n{Colors.HEADER}{Colors.BOLD}  Personal Assistant Framework — Instalador Pre-Alpha{Colors.END}\n")
    print_info(f"Sistema: {platform.system()} {platform.release()}")
    print_info(f"Python: {platform.python_version()}")
    print_info(f"Directorio: {REPO_ROOT}\n")

    # Check Python version
    if sys.version_info < MIN_PYTHON:
        print_error(f"Python {'.'.join(str(v) for v in MIN_PYTHON)}+ requerido.")
        sys.exit(1)

    # Ensure directories
    dirs = [
        CONTEXT_DIR,
        CONTEXT_DIR / "sessions",
        CONTEXT_DIR / "codebase",
        CONTEXT_DIR / "backups",
        CORE_DIR / "agents" / "subagents",
        CORE_DIR / "skills" / "core",
        REPO_ROOT / "workspaces",
        REPO_ROOT / "docs",
        REPO_ROOT / "config",
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
    print_ok("Estructura de directorios verificada.")

    # Ensure MASTER.md
    master = CONTEXT_DIR / "MASTER.md"
    if not master.exists():
        template = CONTEXT_DIR / "MASTER.template.md"
        if template.exists():
            content = template.read_text(encoding="utf-8")
            master.write_text(content, encoding="utf-8")
            print_ok("MASTER.md restaurado desde template.")
        else:
            print_warn("MASTER.md no encontrado y sin template disponible.")

    # Detect CLIs
    found = []
    for cli in CLI_COMMANDS + LOCAL_CLI_COMMANDS:
        if shutil.which(cli):
            found.append(cli)
    if found:
        print_ok(f"CLIs detectados: {', '.join(found)}")
    else:
        print_warn("Ningún CLI de IA detectado. Instala: opencode, claude, gemini, o codex")

    # Choose default CLI
    default_cli = "opencode"
    if found:
        print("\n  Selecciona CLI por defecto:")
        for i, cli in enumerate(found, 1):
            print(f"    {i}. {CLI_LABELS.get(cli, cli)}")
        choice = input(f"  Selección [1]: ").strip()
        try:
            idx = int(choice) - 1
            default_cli = found[idx] if 0 <= idx < len(found) else found[0]
        except (ValueError, IndexError):
            default_cli = found[0] if found else "opencode"

    # Save profile
    version = "0.1.0-alpha"
    vf = REPO_ROOT / "VERSION"
    if vf.exists():
        version = vf.read_text(encoding="utf-8").strip()

    profile = CONTEXT_DIR / "profile.md"
    profile.write_text(
        f"# Perfil de Instalación\n\n"
        f"- **Framework Version**: {version}\n"
        f"- **Fecha**: {datetime.now().strftime('%Y-%m-%d')}\n"
        f"- **CLI default**: {default_cli}\n"
        f"- **Sistema Operativo**: {platform.system()} {platform.release()}\n",
        encoding="utf-8",
    )
    print_ok("Perfil guardado.")

    # Sync context
    sync_script = SCRIPT_DIR / "sync-context.py"
    if sync_script.exists():
        print_info("Sincronizando contexto...")
        subprocess.run([sys.executable, str(sync_script)], cwd=REPO_ROOT, check=False)

    # Done
    print(f"\n{Colors.GREEN}{Colors.BOLD}  {'=' * 50}{Colors.END}")
    print(f"{Colors.GREEN}{Colors.BOLD}  ✓ Instalación completada.{Colors.END}")
    print(f"{Colors.GREEN}{Colors.BOLD}  {'=' * 50}{Colors.END}")
    print(f"\n{Colors.CYAN}  Siguiente paso: ejecuta pa.bat para iniciar el framework.{Colors.END}\n")


if __name__ == "__main__":
    main()
