#!/usr/bin/env python3
"""
FreakingJSON Personal Assistant Framework — Instalador v0.3.0-alpha

Crea estructura, configura perfil y sincroniza contexto.
Framework multi-IA standalone — OpenCode, Claude, Gemini, Codex, Ollama.

Creator: FreakingJSON (instagram.com/freakingjson, freakingjson.com)
"""

import argparse
import os
import platform
import shutil
import subprocess
import sys
import webbrowser
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


def print_ok(m):
    print(f"{Colors.GREEN}  [OK] {m}{Colors.END}")


def print_warn(m):
    print(f"{Colors.YELLOW}  [WARN] {m}{Colors.END}")


def print_error(m):
    print(f"{Colors.RED}  [ERROR] {m}{Colors.END}")


def print_info(m):
    print(f"{Colors.CYAN}  [INFO] {m}{Colors.END}")


def prompt_yes_no(msg, default=False):
    suffix = "[S/n]" if default else "[s/N]"
    choice = input(f"  {msg} {suffix}: ").strip().lower()
    if not choice:
        return default
    return choice in {"s", "si", "y", "yes"}


def check_optional_dependencies():
    """Check for optional dependencies and offer to install them."""
    print_info("Verificando dependencias opcionales...")
    
    # Check for pyyaml (optional - JSON is the primary config format)
    try:
        import yaml
        print_ok("pyyaml disponible (soporte YAML para configuración).")
        return True
    except ImportError:
        print_warn("pyyaml no está instalado (opcional - JSON es el formato primario).")
        print_info("El soporte YAML es opcional. El framework funciona con JSON (stdlib).")
        
        if prompt_yes_no("¿Instalar pyyaml via pip?", default=True):
            print_info("Instalando pyyaml...")
            try:
                result = subprocess.run(
                    [sys.executable, "-m", "pip", "install", "pyyaml"],
                    capture_output=True,
                    text=True,
                    timeout=120
                )
                if result.returncode == 0:
                    print_ok("pyyaml instalado correctamente.")
                    return True
                else:
                    print_error(f"Error al instalar pyyaml: {result.stderr.strip()}")
                    print_info(f"Instalación manual: https://pyyaml.org/wiki/PyYAMLDocumentation")
                    return False
            except subprocess.TimeoutExpired:
                print_error("Timeout durante la instalación de pyyaml.")
                print_info(f"Instalación manual: https://pyyaml.org/wiki/PyYAMLDocumentation")
                return False
            except Exception as e:
                print_error(f"Error inesperado: {e}")
                print_info(f"Instalación manual: https://pyyaml.org/wiki/PyYAMLDocumentation")
                return False
        else:
            print_info("Continuando sin pyyaml. Solo configuración JSON disponible.")
            print_info(f"Para instalar manualmente: pip install pyyaml")
            print_info(f"Documentación: https://pyyaml.org/wiki/PyYAMLDocumentation")
            return False


def configure_preferences(repo_root):
    """Configure user preferences interactively."""
    master = CONTEXT_DIR / "MASTER.md"
    if not master.exists():
        print_warn("MASTER.md no encontrado.")
        return
    print_info("Configuración de preferencias (Enter para mantener valor actual)")
    lang = input("  Idioma principal [es]: ").strip() or "es"
    style = (
        input("  Estilo de respuesta [Claro y conciso]: ").strip()
        or "Claro y conciso; ampliar cuando sea necesario."
    )
    return lang, style


def main():
    # Parse arguments
    parser = argparse.ArgumentParser(description="FreakingJSON PA Framework Installer")
    parser.add_argument(
        "--no-browser",
        action="store_true",
        help="Skip auto-opening dashboard in browser (for headless installs)",
    )
    args = parser.parse_args()

    print(
        f"\n{Colors.HEADER}{Colors.BOLD}  ╔══════════════════════════════════════════════════════════╗\n"
        f"  ║   FreakingJSON Personal Assistant Framework v0.3.0-alpha    ║\n"
        f"  ║   I own my context. I am FreakingJSON.                      ║\n"
        f"  ╚══════════════════════════════════════════════════════════╝{Colors.END}\n"
    )
    print_info(f"Sistema: {platform.system()} {platform.release()}")
    print_info(f"Python: {platform.python_version()}")
    print_info(f"Directorio: {REPO_ROOT}\n")

    # Check Python version
    if sys.version_info < MIN_PYTHON:
        print_error(f"Python {'.'.join(str(v) for v in MIN_PYTHON)}+ requerido.")
        sys.exit(1)

    # Check optional dependencies
    check_optional_dependencies()

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
            # Fallback: crear contenido por defecto si no hay template
            default_content = """# MASTER CONTEXT

## Localization
- **Primary Language**: es
- **Secondary Language**: en

## Active Workspaces
- [ ] Personal: No configurado.
- [ ] Professional: No configurado.
- [ ] Research: No configurado.
- [ ] Content: No configurado.
- [ ] Development: No configurado.
- [ ] Homelab: No configurado.

## Current Focus
Bienvenida. Este framework actúa como asistente personal para tareas diarias, investigación y productividad.

## Preferences
- Response style: Claro y conciso; ampliar cuando sea necesario.
- Decision making: Presenta opciones con pros y contras cuando aplique.
- Proactivity: Sugiere mejoras cuando agreguen valor.
- Clarification: Pregunta si falta información crítica.

## Key Files Reference
- Navigation: core/.context/navigation.md
- Sessions: core/.context/sessions/
- Codebase: core/.context/codebase/
- Agents: core/agents/AGENTS.md
- Skills: core/skills/SKILLS.md

## Rules
1. Prioriza el objetivo del usuario final y su experiencia.
2. Pregunta si falta información crítica o contexto.
3. Mantén respuestas accionables y seguras.
4. Guarda SIEMPRE el contexto relevante en archivos .md locales (sesiones, ideas, prompts).
5. Evita exponer credenciales o datos sensibles.
6. Usa el principio MVI (Minimal Viable Information): solo lo esencial, referencia el resto.
"""
            master.write_text(default_content, encoding="utf-8")
            print_ok("MASTER.md creado con configuración por defecto.")

    # Detect CLIs
    found = []
    for cli in CLI_COMMANDS + LOCAL_CLI_COMMANDS:
        if shutil.which(cli):
            found.append(cli)
    if found:
        print_ok(f"CLIs detectados: {', '.join(found)}")
    else:
        print_warn(
            "Ningún CLI de IA detectado. Instala: opencode, claude, gemini, o codex"
        )

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
    sync_script = SCRIPT_DIR / "sync_context.py"
    if sync_script.exists():
        print_info("Sincronizando contexto...")
        subprocess.run([sys.executable, str(sync_script)], cwd=REPO_ROOT, check=False)

    # Initialize Knowledge Base (sesion 2026-03-09)
    kb_init_script = SCRIPT_DIR / "kb_init.py"
    if kb_init_script.exists():
        print_info("Inicializando Knowledge Base...")
        subprocess.run(
            [sys.executable, str(kb_init_script), "--force"], cwd=REPO_ROOT, check=False
        )

    # Done - Mensaje según sistema operativo
    system_name = platform.system()
    if system_name == "Windows":
        next_step = "pa.bat"
    else:
        next_step = "./pa.sh"

    print(f"\n{Colors.GREEN}{Colors.BOLD}  {'=' * 60}{Colors.END}")
    print(f"{Colors.GREEN}{Colors.BOLD}  ✓ INSTALACIÓN COMPLETADA EXITOSAMENTE{Colors.END}")
    print(f"{Colors.GREEN}{Colors.BOLD}  {'=' * 60}{Colors.END}")
    
    # What's Next guidance
    print(f"\n{Colors.BOLD}{Colors.CYAN}  📋 ¿QUÉ SIGUE? — WHAT'S NEXT{Colors.END}")
    print(f"  {Colors.CYAN}{'─' * 50}{Colors.END}")
    print(f"\n  {Colors.YELLOW}1.{Colors.END} Inicia el framework:")
    print(f"     {Colors.BOLD}{next_step}{Colors.END}")
    print(f"\n  {Colors.YELLOW}2.{Colors.END} Configura tus API keys en:")
    print(f"     core/.context/MASTER.md")
    print(f"\n  {Colors.YELLOW}3.{Colors.END} Revisa la documentación:")
    print(f"     docs/ y AGENTS.md")
    print(f"\n  {Colors.YELLOW}4.{Colors.END} Explora los ejemplos en:")
    print(f"     examples/")
    print(f"\n  {Colors.CYAN}{'─' * 50}{Colors.END}")
    
    # Dashboard path
    dashboard_path = REPO_ROOT / "dashboard.html"
    
    # Auto-open dashboard in browser (unless --no-browser flag)
    if not args.no_browser and dashboard_path.exists():
        print(f"\n{Colors.CYAN}  🌐 Abriendo dashboard en navegador...{Colors.END}")
        try:
            webbrowser.open(f"file://{dashboard_path}")
            print_ok("Dashboard abierto en tu navegador.")
        except Exception as e:
            print_warn(f"No se pudo abrir el navegador: {e}")
            print_info(f"Puedes abrir manualmente: {dashboard_path}")
    elif args.no_browser:
        print_info(f"Modo headless: dashboard no abierto (--no-browser)")
        if dashboard_path.exists():
            print_info(f"Dashboard disponible en: {dashboard_path}")
    else:
        print_warn(f"Dashboard no encontrado: {dashboard_path}")
    
    print(f"\n{Colors.GREEN}{Colors.BOLD}  ¡Gracias por instalar FreakingJSON PA Framework!{Colors.END}")
    print(f"{Colors.CYAN}  ─────────────────────────────────────────────────{Colors.END}")
    print(f"{Colors.CYAN}  📸 Instagram: @freakingjson{Colors.END}")
    print(f"{Colors.CYAN}  🌐 Linktree:  linktr.ee/freakingjson{Colors.END}")
    print(f"{Colors.CYAN}  📝 Blog:      freakingjson.com{Colors.END}")
    print(f"{Colors.CYAN}  ☕ Support:   buymeacoffee.com/freakingjson{Colors.END}")
    print(f"{Colors.CYAN}  ─────────────────────────────────────────────────{Colors.END}")
    print(f"{Colors.BOLD}{Colors.HEADER}  \"I own my context. I am FreakingJSON.\"{Colors.END}\n")


if __name__ == "__main__":
    main()
