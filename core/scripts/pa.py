#!/usr/bin/env python3
"""
PA Framework — Control Panel (Pre-Alpha 0.1.0)
Menú simplificado de 4 opciones + submenu de configuración.
"""

import argparse
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path


# --- RESOLVE PATHS ---
SCRIPT_DIR = Path(__file__).resolve().parent          # core/scripts/
CORE_DIR = SCRIPT_DIR.parent                          # core/
REPO_ROOT = CORE_DIR.parent                           # /PA-Pre-Alpha/
CONTEXT_DIR = CORE_DIR / ".context"
SESSIONS_DIR = CONTEXT_DIR / "sessions"
CODEBASE_DIR = CONTEXT_DIR / "codebase"

# Ensure critical dirs exist
SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
CODEBASE_DIR.mkdir(parents=True, exist_ok=True)

# Add scripts dir to path for local imports
sys.path.insert(0, str(SCRIPT_DIR))


# --- COLORS ---
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


def print_ok(msg: str):
    print(c(f"  ✓ {msg}", Colors.GREEN))


def print_warn(msg: str):
    print(c(f"  ⚠ {msg}", Colors.YELLOW))


def print_error(msg: str):
    print(c(f"  ✗ {msg}", Colors.RED))


def print_info(msg: str):
    print(c(f"  ℹ {msg}", Colors.CYAN))


# --- PLATFORM ---
def clear_screen():
    if sys.stdout.isatty():
        os.system("cls" if os.name == "nt" else "clear")


def get_python() -> str:
    return sys.executable


def set_title(title: str):
    if os.name == "nt":
        os.system(f"title {title}")
    else:
        sys.stdout.write(f"\x1b]2;{title}\x07")
        sys.stdout.flush()


# --- UI ---
def print_banner():
    branding_file = REPO_ROOT / "config" / "branding.txt"
    if branding_file.exists():
        try:
            print(c(branding_file.read_text(encoding="utf-8"), Colors.HEADER))
            return
        except Exception:
            pass
    print(c("╔═══════════════════════════════════════════════════════╗", f"{Colors.HEADER}{Colors.BOLD}"))
    print(c("║   Personal Assistant Framework — Pre-Alpha 0.1.0     ║", f"{Colors.HEADER}{Colors.BOLD}"))
    print(c("╚═══════════════════════════════════════════════════════╝", f"{Colors.HEADER}{Colors.BOLD}"))


def pause(msg: str = ""):
    input(f"\n  {msg or 'Presiona Enter para continuar...'}")


def prompt_choice(prompt: str, valid: set[str]) -> str:
    while True:
        choice = input(prompt).strip()
        if choice in valid:
            return choice
        print_warn("Opción inválida. Intenta de nuevo.")


def prompt_yes_no(msg: str, default: bool = False) -> bool:
    suffix = "[S/n]" if default else "[s/N]"
    choice = input(f"  {msg} {suffix}: ").strip().lower()
    if not choice:
        return default
    return choice in {"s", "si", "y", "yes"}


# --- CLI DETECTION ---
CLI_COMMANDS = ["opencode", "claude", "gemini", "codex"]
LOCAL_CLI_COMMANDS = ["ollama", "lms"]
CLI_LABELS = {
    "opencode": "OpenCode",
    "claude": "Claude Code",
    "gemini": "Gemini CLI",
    "codex": "Codex",
    "ollama": "Ollama",
    "lms": "LM Studio",
}


def detect_clis() -> list[str]:
    """Detect available AI CLIs in PATH."""
    available = []
    for cli in CLI_COMMANDS + LOCAL_CLI_COMMANDS:
        if shutil.which(cli):
            available.append(cli)
    return available


def get_default_cli() -> str:
    """Read default CLI from profile."""
    profile = CONTEXT_DIR / "profile.md"
    if profile.exists():
        for line in profile.read_text(encoding="utf-8").splitlines():
            if "cli default" in line.lower():
                for cli in CLI_COMMANDS:
                    if cli in line.lower():
                        return cli
    return "opencode"


# --- SYNC ---
def run_sync_context() -> bool:
    """Synchronize MASTER.md to tool-specific context files."""
    sync_script = SCRIPT_DIR / "sync-context.py"
    if not sync_script.exists():
        print_error("No se encontró sync-context.py")
        return False
    result = subprocess.run(
        [get_python(), str(sync_script)],
        cwd=REPO_ROOT,
        capture_output=False,
        check=False,
    )
    return result.returncode == 0


def menu_sync():
    """Option 1: Sync Context."""
    print(c("\n  🔄 Sincronizando contexto...\n", Colors.CYAN))
    if run_sync_context():
        print_ok("Contexto sincronizado correctamente.")
    else:
        print_error("Falló la sincronización de contexto.")
    pause()


# --- LAUNCH AI SESSION ---
def menu_launch_ai():
    """Option 2: Launch AI Session."""
    print(c("\n  🚀 Iniciar Sesión AI\n", f"{Colors.BOLD}{Colors.CYAN}"))

    available = detect_clis()
    default_cli = get_default_cli()

    if not available:
        print_error("No se detectaron CLIs de IA instalados.")
        print_info("Instala al menos uno: opencode, claude, gemini, o codex")
        print_info("Usa opción 3 → Estado del Sistema para más detalles.")
        pause()
        return

    print("  CLIs disponibles:\n")
    for i, cli in enumerate(available, 1):
        marker = c(" (default)", Colors.GREEN) if cli == default_cli else ""
        print(f"    {c(str(i), Colors.CYAN)}. {CLI_LABELS.get(cli, cli)}{marker}")
    print(f"    {c('0', Colors.RED)}. Volver\n")

    choice = input(f"  Selecciona CLI [1-{len(available)}]: ").strip()
    if choice == "0":
        return

    try:
        idx = int(choice) - 1
        selected = available[idx] if 0 <= idx < len(available) else default_cli
    except ValueError:
        selected = default_cli

    # Ensure today's session exists
    _ensure_session_file()

    # Magic prompt
    context_file = f"core/.context/MASTER.md"
    magic = f"Lee el archivo '{context_file}' y el archivo 'core/agents/pa-assistant.md' para iniciar la sesión de hoy."

    print(c(f"\n  ╔══ MAGIC PROMPT ════════════════════════════════════╗", f"{Colors.GREEN}{Colors.BOLD}"))
    print(c(f"  ║ {magic}", Colors.CYAN))
    print(c(f"  ╚════════════════════════════════════════════════════╝\n", f"{Colors.GREEN}{Colors.BOLD}"))

    pause("Presiona Enter después de copiar el prompt para iniciar la CLI...")

    print_info(f"Iniciando {CLI_LABELS.get(selected, selected)}...")
    print_info("Presiona Ctrl+C para salir del CLI y volver al menú.\n")

    try:
        subprocess.run(selected, cwd=REPO_ROOT, shell=True, check=False)
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print_error(f"No se pudo iniciar el CLI: {e}")

    pause()


def _ensure_session_file():
    """Create today's session file if it doesn't exist."""
    today = datetime.now().strftime("%Y-%m-%d")
    session_file = SESSIONS_DIR / f"{today}.md"
    if not session_file.exists():
        hora = datetime.now().strftime("%H:%M")
        content = (
            f"# Sesión {today}\n\n"
            f"## Inicio\n"
            f"- **Hora**: {hora}\n"
            f"- **CLI**: (auto-detectado al iniciar)\n\n"
            f"## Temas Tratados\n\n\n"
            f"## Decisiones\n\n\n"
            f"## Pendientes Generados\n\n\n"
            f"## Resumen\n\n"
        )
        session_file.write_text(content, encoding="utf-8")
        print_ok(f"Sesión del día creada: sessions/{today}.md")


# --- CONFIGURATION SUBMENU ---
def menu_config():
    """Option 3: Configuration submenu."""
    while True:
        clear_screen()
        print(c("\n  ⚙️  Configuración\n", f"{Colors.BOLD}{Colors.CYAN}"))
        print(f"    {c('1', Colors.CYAN)}. 📊 Estado del Sistema")
        print(f"    {c('2', Colors.CYAN)}. ⚙️  Configurar Perfil")
        print(f"    {c('3', Colors.CYAN)}. 🏢 Workspaces")
        print(f"    {c('0', Colors.RED)}. ↩  Volver\n")

        choice = prompt_choice("  Selecciona: ", {"0", "1", "2", "3"})

        if choice == "0":
            return
        elif choice == "1":
            submenu_system_status()
        elif choice == "2":
            submenu_profile()
        elif choice == "3":
            submenu_workspaces()


def submenu_system_status():
    """3.1: System Status with option to install missing components."""
    print(c("\n  📊 Estado del Sistema\n", f"{Colors.BOLD}{Colors.CYAN}"))

    checks_ok = 0
    checks_total = 0
    installable = []

    # 1. Python
    checks_total += 1
    import platform as plat
    py_ver = plat.python_version()
    print_ok(f"Python: {py_ver}")
    checks_ok += 1

    # 2. Git
    checks_total += 1
    try:
        r = subprocess.run(["git", "--version"], capture_output=True, text=True, check=False)
        if r.returncode == 0:
            print_ok(f"Git: {r.stdout.strip()}")
            checks_ok += 1
        else:
            print_warn("Git: no detectado (opcional)")
    except Exception:
        print_warn("Git: no detectado (opcional)")

    # 3. Framework structure
    checks_total += 1
    required = ["core/.context", "core/agents", "core/skills", "core/scripts", "workspaces"]
    missing_dirs = [d for d in required if not (REPO_ROOT / d).exists()]
    if not missing_dirs:
        print_ok("Estructura del framework: completa")
        checks_ok += 1
    else:
        print_warn(f"Estructura: faltan {', '.join(missing_dirs)}")

    # 4. AI CLIs
    checks_total += 1
    found = detect_clis()
    not_found = [c for c in CLI_COMMANDS if c not in found]
    if found:
        print_ok(f"CLIs AI: {', '.join(CLI_LABELS.get(c, c) for c in found)}")
        checks_ok += 1
    else:
        print_warn("CLIs AI: ninguno detectado")

    for cli in not_found:
        print(c(f"    ✗ {CLI_LABELS.get(cli, cli)} (no instalado)", Colors.DIM))
        if cli == "opencode":
            installable.append(cli)

    # 5. Profile
    checks_total += 1
    if (CONTEXT_DIR / "profile.md").exists():
        print_ok("Perfil: configurado")
        checks_ok += 1
    else:
        print_warn("Perfil: no configurado (ejecutar Configurar Perfil)")

    # 6. Last sync
    checks_total += 1
    last_sync = REPO_ROOT / ".last_sync"
    if last_sync.exists():
        try:
            days = (datetime.now() - datetime.fromtimestamp(last_sync.stat().st_mtime)).days
            if days == 0:
                print_ok("Última sync: hoy")
            elif days <= 3:
                print_ok(f"Última sync: hace {days} día(s)")
            else:
                print_warn(f"Última sync: hace {days} días")
            checks_ok += 1
        except Exception:
            print_warn("Última sync: no disponible")
    else:
        print_warn("Sin registro de sincronización")

    # Summary
    print(f"\n  {'─' * 45}")
    ratio = checks_ok / checks_total if checks_total else 0
    summary = f"  {checks_ok}/{checks_total} verificaciones OK"
    if ratio >= 1:
        print(c(summary + " — Sistema saludable ✓", Colors.GREEN))
    elif ratio >= 0.7:
        print(c(summary + " — Funcional con advertencias", Colors.YELLOW))
    else:
        print(c(summary + " — Se recomienda revisar", Colors.RED))

    # Option to install missing
    if installable:
        print()
        if prompt_yes_no("¿Instalar componentes faltantes (OpenCode)?", default=False):
            _install_opencode()

    pause()


def _install_opencode():
    """Attempt to install OpenCode via npm."""
    if not shutil.which("npm"):
        print_error("npm no detectado. Instala Node.js primero: https://nodejs.org")
        return
    print_info("Instalando OpenCode...")
    cmd = ["npm", "install", "-g", "opencode-ai"]
    if os.name == "nt":
        npm = shutil.which("npm") or shutil.which("npm.cmd")
        if npm:
            cmd[0] = npm
    result = subprocess.run(cmd, check=False)
    if result.returncode == 0:
        print_ok("OpenCode instalado correctamente.")
    else:
        print_error("No se pudo instalar. Intenta manualmente: npm install -g opencode-ai")


def submenu_profile():
    """3.2: Configure Profile."""
    print(c("\n  ⚙️  Configurar Perfil\n", f"{Colors.BOLD}{Colors.CYAN}"))

    master = CONTEXT_DIR / "MASTER.md"
    if not master.exists():
        print_error("No se encontró MASTER.md. Ejecuta 'Sincronizar Contexto' primero.")
        pause()
        return

    content = master.read_text(encoding="utf-8")

    # Extract current values
    def _extract(lines, prefix):
        for l in lines:
            if l.strip().startswith(prefix):
                return l.split(":", 1)[1].strip() if ":" in l else ""
        return ""

    lines = content.splitlines()
    cur_lang = _extract(lines, "- **Primary Language**")
    cur_style = _extract(lines, "- Response style")
    cur_cli = get_default_cli()

    print(f"  (Enter para mantener valor actual)\n")

    lang = input(f"  Idioma principal [{cur_lang}]: ").strip() or cur_lang
    style = input(f"  Estilo de respuesta [{cur_style}]: ").strip() or cur_style
    focus = input(f"  Enfoque actual [libre]: ").strip()

    # CLI default
    print(f"\n  CLI por defecto actual: {CLI_LABELS.get(cur_cli, cur_cli)}")
    available = detect_clis()
    if available:
        for i, cli in enumerate(available, 1):
            print(f"    {i}. {CLI_LABELS.get(cli, cli)}")
        cli_choice = input(f"  Nuevo CLI default [{cur_cli}]: ").strip()
        try:
            idx = int(cli_choice) - 1
            new_cli = available[idx] if 0 <= idx < len(available) else cur_cli
        except (ValueError, IndexError):
            new_cli = cur_cli
    else:
        new_cli = cur_cli

    # Update MASTER.md
    import re
    content = re.sub(r"- \*\*Primary Language\*\*: .*", f"- **Primary Language**: {lang}", content)
    content = re.sub(r"- Response style: .*", f"- Response style: {style}", content)

    if focus:
        lines = content.splitlines()
        for i, l in enumerate(lines):
            if l.strip() == "## Current Focus":
                # Replace the line after the heading
                if i + 1 < len(lines):
                    lines[i + 1] = focus
                break
        content = "\n".join(lines)

    master.write_text(content.rstrip() + "\n", encoding="utf-8")

    # Save profile
    _save_profile(lang, new_cli)
    print_ok("Perfil actualizado.")
    pause()


def _save_profile(lang: str = "es", default_cli: str = "opencode"):
    """Save profile.md with current settings."""
    import platform as plat
    version = "0.1.0-alpha"
    vf = REPO_ROOT / "VERSION"
    if vf.exists():
        version = vf.read_text(encoding="utf-8").strip()

    profile = CONTEXT_DIR / "profile.md"
    profile.write_text(
        f"# Perfil de Instalación\n\n"
        f"- **Framework Version**: {version}\n"
        f"- **Fecha**: {datetime.now().strftime('%Y-%m-%d')}\n"
        f"- **Idioma**: {lang}\n"
        f"- **CLI default**: {default_cli}\n"
        f"- **Sistema Operativo**: {plat.system()} {plat.release()}\n",
        encoding="utf-8",
    )


def submenu_workspaces():
    """3.3: Workspace Management."""
    print(c("\n  🏢 Gestión de Workspaces\n", f"{Colors.BOLD}{Colors.CYAN}"))
    ws_dir = REPO_ROOT / "workspaces"
    ws_dir.mkdir(exist_ok=True)

    # List existing
    existing = [d.name for d in ws_dir.iterdir() if d.is_dir() and d.name != ".gitkeep"]
    if existing:
        print("  Workspaces actuales:")
        for ws in sorted(existing):
            print(f"    📁 {ws}")
    else:
        print("  (Sin workspaces configurados)")

    defaults = ["personal", "professional", "research", "content", "development", "homelab"]
    print(f"\n    {c('1', Colors.CYAN)}. Crear nuevo workspace")
    print(f"    {c('2', Colors.CYAN)}. Restablecer por defecto ({', '.join(defaults)})")
    print(f"    {c('0', Colors.RED)}. Volver\n")

    choice = prompt_choice("  Selecciona: ", {"0", "1", "2"})

    if choice == "1":
        name = input("  Nombre del workspace (sin espacios): ").strip().lower()
        if name:
            new_ws = ws_dir / name
            new_ws.mkdir(exist_ok=True)
            (new_ws / "notes").mkdir(exist_ok=True)
            (new_ws / "projects").mkdir(exist_ok=True)
            print_ok(f"Workspace '{name}' creado.")
    elif choice == "2":
        for ws in defaults:
            d = ws_dir / ws
            d.mkdir(exist_ok=True)
            (d / "notes").mkdir(exist_ok=True)
            (d / "projects").mkdir(exist_ok=True)
        print_ok(f"Workspaces por defecto restablecidos: {', '.join(defaults)}")

    pause()


# --- UPDATE CHECK ---
def menu_updates():
    """Option 4: Check for updates."""
    print(c("\n  🔄 Buscando actualizaciones...\n", Colors.CYAN))

    update_script = SCRIPT_DIR / "update.py"
    if update_script.exists():
        result = subprocess.run(
            [get_python(), str(update_script), "--check"],
            cwd=REPO_ROOT,
            capture_output=False,
            check=False,
        )
        if result.returncode == 0:
            print_ok("El framework está actualizado.")
        else:
            print_warn("Hay actualizaciones disponibles.")
            if prompt_yes_no("¿Actualizar ahora?", default=False):
                subprocess.run(
                    [get_python(), str(update_script)],
                    cwd=REPO_ROOT,
                    capture_output=False,
                    check=False,
                )
    else:
        # Simple git-based check
        try:
            r = subprocess.run(
                ["git", "fetch", "--dry-run"],
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            if r.stderr.strip():
                print_warn("Posibles actualizaciones disponibles. Ejecuta 'git pull'.")
            else:
                print_ok("Sin actualizaciones detectadas.")
        except Exception:
            print_info("No se pudo verificar (git no disponible o no es un repositorio).")

    pause()


# --- MAIN MENU ---
def main_menu():
    """Main control panel with 4 options."""
    while True:
        clear_screen()
        print_banner()
        print()

        print(f"    {c('1', Colors.CYAN)}. 🔄 Sincronizar Contexto")
        print(f"    {c('2', Colors.CYAN)}. 🚀 {c('Iniciar Sesión AI', Colors.BOLD)}")
        print(f"    {c('3', Colors.CYAN)}. ⚙️  Configuración")
        print(f"    {c('4', Colors.CYAN)}. 🔄 Buscar Actualizaciones")
        print(f"    {c('0', Colors.RED)}. 🚪 Salir")
        print()

        choice = input(f"  {c('Selecciona una opción', Colors.BOLD)}: ").strip()

        if choice == "0":
            print(c("\n  ¡Hasta luego! 👋\n", Colors.CYAN))
            return
        elif choice == "1":
            menu_sync()
        elif choice == "2":
            menu_launch_ai()
        elif choice == "3":
            menu_config()
        elif choice == "4":
            menu_updates()
        else:
            print_warn("Opción inválida.")
            time.sleep(0.5)


# --- ENTRY POINT ---
def main():
    parser = argparse.ArgumentParser(description="PA Framework Control Panel (Pre-Alpha)")
    parser.add_argument("--sync", action="store_true", help="Run sync and exit")
    args = parser.parse_args()

    # Setup
    os.chdir(REPO_ROOT)
    for stream in (sys.stdout, sys.stderr):
        rec = getattr(stream, "reconfigure", None)
        if rec:
            try:
                rec(encoding="utf-8")
            except Exception:
                pass

    set_title("PA Framework")

    if args.sync:
        sys.exit(0 if run_sync_context() else 1)

    # Auto-install check
    if not (CONTEXT_DIR / "profile.md").exists():
        install_script = SCRIPT_DIR / "install.py"
        if install_script.exists():
            print_info("Primera ejecución detectada. Iniciando instalador...")
            subprocess.run([get_python(), str(install_script)], cwd=REPO_ROOT, check=False)

    main_menu()


if __name__ == "__main__":
    main()
