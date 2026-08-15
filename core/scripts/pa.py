#!/usr/bin/env python3
"""
FreakingJSON PA Framework — Control Panel v0.4.0-beta
Menú reorganizado según N30's spec: 7 opciones principales.

Creator: FreakingJSON (instagram.com/freakingjson, freakingjson.com)
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path


# --- Windows console compatibility (v0.4.0-beta) -----------------------------
# Consolas legacy (cmd.exe / cp1252) no pueden imprimir Unicode (✓, →, ó).
# Re-ensoblamos stdout/stderr con 'replace' para no crashear; el texto
# legible sobrevive. No-op en UTF-8 (Linux/macOS/Windows Terminal).
def _console_safe_streams():
    import sys
    for name in ("stdout", "stderr"):
        stream = getattr(sys, name, None)
        if stream is None or stream.encoding is None:
            continue
        try:
            stream.encoding.lower().encode("\u2192")
        except (LookupError, UnicodeEncodeError):
            import io, os
            enc = stream.encoding
            setattr(sys, name, io.TextIOWrapper(
                stream.buffer, encoding=enc, errors="replace",
                line_buffering=stream.line_buffering if hasattr(stream, "line_buffering") else False,
            ))

_console_safe_streams()
# ----------------------------------------------------------------------------
# Windows UTF-8 encoding fix (evita acentos corruptos)
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


# --- RESOLVE PATHS ---
SCRIPT_DIR = Path(__file__).resolve().parent  # core/scripts/
CORE_DIR = SCRIPT_DIR.parent  # core/
REPO_ROOT = CORE_DIR.parent  # /PA-Pre-Alpha/
CONTEXT_DIR = CORE_DIR / ".context"
SESSIONS_DIR = CONTEXT_DIR / "sessions"
CODEBASE_DIR = CONTEXT_DIR / "codebase"

# Standalone config directory
STANDALONE_CONFIG_DIR = Path.home() / ".pa-framework"
CONFIG_FILE = STANDALONE_CONFIG_DIR / "config.json"

# Default config structure
DEFAULT_CONFIG = {
    "wiki_path": "",
    "memory_path": str(STANDALONE_CONFIG_DIR / "memory"),
    "auto_sync": False,
    "sync_interval": 30,
    "enabled_skills": [],
    "default_cli": "opencode",
    "language": "es"
}

# Ensure critical dirs exist
SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
CODEBASE_DIR.mkdir(parents=True, exist_ok=True)

# Add scripts dir to path for local imports
sys.path.insert(0, str(SCRIPT_DIR))

# Optional memory bridge (best-effort)
try:
    from session_bridge import SessionBridge
    MEMORY_BRIDGE_AVAILABLE = True
except Exception:
    SessionBridge = None
    MEMORY_BRIDGE_AVAILABLE = False

_session_bridge = None


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
    print(c(f"  [OK] {msg}", Colors.GREEN))


def print_warn(msg: str):
    print(c(f"  [WARN] {msg}", Colors.YELLOW))


def print_error(msg: str):
    print(c(f"  [ERROR] {msg}", Colors.RED))


def print_info(msg: str):
    print(c(f"  [INFO] {msg}", Colors.CYAN))


# --- MEMORY PERSISTENCE (CLI DIRECT MODE) ---
def _init_cli_memory_bridge(cli_name: str, magic_prompt: str) -> None:
    """Initialize SQLite session for --cli mode so memory does not get lost."""
    global _session_bridge
    if not MEMORY_BRIDGE_AVAILABLE:
        return
    try:
        _session_bridge = SessionBridge()
        _session_bridge.start_session(
            user_input=magic_prompt,
            metadata={"entrypoint": "pa.py", "mode": "--cli", "cli": cli_name},
        )
        _session_bridge.add_message("system", f"CLI_LAUNCH: {cli_name}")
    except Exception:
        _session_bridge = None


def _close_cli_memory_bridge(summary: str = "CLI session ended") -> None:
    """Close SQLite session gracefully in --cli mode."""
    global _session_bridge
    if not _session_bridge:
        return
    try:
        _session_bridge.end_session(summary=summary)
    except Exception:
        pass
    finally:
        _session_bridge = None


# --- CONFIG.JSON MANAGER ---
def get_config_path() -> Path:
    """Get the path to config.json, creating directory if needed."""
    STANDALONE_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    return CONFIG_FILE


def load_config() -> dict:
    """Load config.json, returning defaults if not exists."""
    config_path = get_config_path()
    if config_path.exists():
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            # Merge with defaults for any missing keys
            merged = DEFAULT_CONFIG.copy()
            merged.update(config)
            return merged
        except (json.JSONDecodeError, Exception):
            return DEFAULT_CONFIG.copy()
    return DEFAULT_CONFIG.copy()


def save_config(config: dict):
    """Save config to config.json."""
    config_path = get_config_path()
    STANDALONE_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)


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
    print(
        c(
            "╔═══════════════════════════════════════════════════════╗",
            f"{Colors.HEADER}{Colors.BOLD}",
        )
    )
    print(
        c(
           "║   FreakingJSON PA Framework — v0.4.0-beta          ║",
            f"{Colors.HEADER}{Colors.BOLD}",
        )
    )
    print(
        c(
            "╚═══════════════════════════════════════════════════════╝",
            f"{Colors.HEADER}{Colors.BOLD}",
        )
    )


def pause(msg: str = ""):
    try:
        input(f"\n  {msg or 'Presiona Enter para continuar...'}")
    except (EOFError, KeyboardInterrupt):
        # Non-interactive shells (CI/tests) or interrupted input
        return


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

# CLI-specific prompt injection methods
# Each CLI has different ways to accept initial prompts
CLI_PROMPT_ARGS = {
    "opencode": ["--prompt"],      # opencode --prompt "message"
    "claude": ["--print"],         # claude --print "message" (prints and exits, not ideal)
    "gemini": [],                  # gemini interactive mode (stdin or just launch)
    "codex": [],                   # codex interactive mode
    "ollama": [],                  # ollama run model (stdin)
    "lms": [],                     # lm studio (no CLI prompt injection)
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


def get_magic_prompt() -> str:
    """Get the magic prompt for session initialization."""
    return "Lee 'core/.context/quick-start.md' para iniciar. Este archivo contiene todo lo necesario para comenzar."


def build_cli_command(cli: str, prompt: str, workdir: Path) -> tuple[list[str], bool]:
    """
    Build CLI command with prompt injection.
    
    Returns:
        tuple: (command_list, can_auto_inject)
        - command_list: The command to run
        - can_auto_inject: Whether prompt can be auto-injected
    """
    # CLIs that support direct prompt injection
    if cli == "opencode":
        # OpenCode supports --prompt flag for initial message
        return [cli, "--prompt", prompt], True
    
    elif cli == "claude":
        # Claude Code: try with prompt via stdin or just launch
        # Note: claude --print is non-interactive, so we just launch normally
        # and let user paste the prompt
        return [cli], False
    
    elif cli == "gemini":
        # Gemini CLI: prompt can be passed as argument or via stdin
        return [cli], False
    
    elif cli == "codex":
        # Codex: similar to others
        return [cli], False
    
    else:
        # Default: just launch the CLI
        return [cli], False


def try_auto_launch_cli(cli: str, prompt: str, workdir: Path) -> bool:
    """
    Attempt to auto-launch CLI with prompt injected.
    
    Returns:
        bool: True if auto-launch succeeded, False if fallback needed
    """
    command, can_auto_inject = build_cli_command(cli, prompt, workdir)
    
    if not can_auto_inject:
        return False
    
    # Verify CLI exists in PATH before attempting to run
    cli_path = shutil.which(cli)
    if not cli_path:
        print_warn(f"CLI '{CLI_LABELS.get(cli, cli)}' no está disponible en PATH.")
        print_info("Usando modo manual (fallback): se mostrará el prompt para copiar.")
        return False

    try:
        print_info(f"Auto-iniciando {CLI_LABELS.get(cli, cli)} con prompt...")
        print_info("Presiona Ctrl+C para salir del CLI y volver al menú.\n")
        subprocess.run(command, cwd=workdir, check=False)
        return True
    except FileNotFoundError:
        print_info(f"Auto-launch no disponible para {CLI_LABELS.get(cli, cli)}. Cambiando a modo manual...")
        return False
    except Exception as e:
        print_warn(f"Auto-launch falló: {e}. Cambiando a modo manual...")
        return False


# --- SYNC ---
def run_sync_context() -> bool:
    """Synchronize MASTER.md to tool-specific context files."""
    sync_script = SCRIPT_DIR / "sync_context.py"
    if not sync_script.exists():
        print_error("No se encontró sync_context.py")
        return False
    result = subprocess.run(
        [get_python(), str(sync_script)],
        cwd=REPO_ROOT,
        capture_output=False,
        check=False,
    )
    return result.returncode == 0


def menu_sync():
    """Option 5: Sync Context submenu with manual/auto toggle."""
    while True:
        config = load_config()
        clear_screen()
        print(c("\n  [SYNC] Sincronización de Contexto\n", f"{Colors.BOLD}{Colors.CYAN}"))
        
        # Show current status
        auto_sync = config.get("auto_sync", False)
        sync_interval = config.get("sync_interval", 30)
        
        mode_str = c("Automático", Colors.GREEN) if auto_sync else c("Manual", Colors.YELLOW)
        print(f"  Modo actual: {mode_str}")
        if auto_sync:
            print(f"  Intervalo: cada {sync_interval} minutos")
        print()
        
        print(f"    {c('1', Colors.CYAN)}. [SYNC] Sincronizar ahora (manual)")
        print(f"    {c('2', Colors.CYAN)}. [TOGGLE] Cambiar modo ({'Manual' if auto_sync else 'Auto'})")
        if auto_sync:
            print(f"    {c('3', Colors.CYAN)}. [CONFIG] Cambiar intervalo (actual: {sync_interval} min)")
        print(f"    {c('0', Colors.RED)}. ↩  Volver\n")
        
        valid_choices = {"0", "1", "2"}
        if auto_sync:
            valid_choices.add("3")
        
        choice = prompt_choice("  Selecciona: ", valid_choices)
        
        if choice == "0":
            return
        elif choice == "1":
            print(c("\n  [SYNC] Sincronizando contexto...\n", Colors.CYAN))
            if run_sync_context():
                print_ok("Contexto sincronizado correctamente.")
            else:
                print_error("Falló la sincronización de contexto.")
            pause()
        elif choice == "2":
            config["auto_sync"] = not auto_sync
            save_config(config)
            status = "automático" if config["auto_sync"] else "manual"
            print_ok(f"Modo de sync cambiado a: {status}")
            pause()
        elif choice == "3" and auto_sync:
            new_interval = input(f"  Nuevo intervalo en minutos [{sync_interval}]: ").strip()
            if new_interval:
                try:
                    interval = int(new_interval)
                    if interval >= 1:
                        config["sync_interval"] = interval
                        save_config(config)
                        print_ok(f"Intervalo actualizado a {interval} minutos.")
                    else:
                        print_error("El intervalo debe ser al menos 1 minuto.")
                except ValueError:
                    print_error("Por favor ingresa un número válido.")
            pause()


# --- LAUNCH AI SESSION ---
def menu_launch_ai(cli_override: str = None):
    """Option 2: Launch AI Session with auto-inject or fallback to manual prompt."""
    print(c("\n  [LAUNCH] Iniciar Sesión AI\n", f"{Colors.BOLD}{Colors.CYAN}"))

    available = detect_clis()
    default_cli = get_default_cli()

    # If CLI override provided via --cli flag, use it
    if cli_override:
        if cli_override in available:
            selected = cli_override
            print_info(f"Usando CLI especificado: {CLI_LABELS.get(selected, selected)}")
        else:
            print_warn(f"CLI '{cli_override}' no disponible. Seleccionando de la lista...")
            cli_override = None
    
    if not cli_override:
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

    # Get magic prompt
    magic = get_magic_prompt()

    # Initialize persistence bridge BEFORE launching any CLI path.
    # This ensures both auto-inject and manual fallback sessions are persisted.
    _init_cli_memory_bridge(selected, magic)

    # Try auto-launch first (for CLIs that support it)
    auto_launched = try_auto_launch_cli(selected, magic, REPO_ROOT)

    if auto_launched:
        _close_cli_memory_bridge(summary=f"CLI session finished ({selected})")
        pause()
        return
    
    # Fallback: Show manual prompt for CLIs that don't support auto-inject
    print(
        c(
            f"\n  ╔══ MAGIC PROMPT ════════════════════════════════════╗",
            f"{Colors.GREEN}{Colors.BOLD}",
        )
    )
    print(c(f"  ║ {magic}", Colors.CYAN))
    print(
        c(
            f"  ╚════════════════════════════════════════════════════╝\n",
            f"{Colors.GREEN}{Colors.BOLD}",
        )
    )

    pause("Presiona Enter después de copiar el prompt para iniciar la CLI...")

    print_info(f"Iniciando {CLI_LABELS.get(selected, selected)}...")
    print_info("Presiona Ctrl+C para salir del CLI y volver al menú.\n")

    try:
        subprocess.run(selected, cwd=REPO_ROOT, shell=True, check=False)
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print_error(f"No se pudo iniciar el CLI: {e}")
        _close_cli_memory_bridge(summary=f"CLI launch error ({selected}): {e}")
        pause()
        return

    _close_cli_memory_bridge(summary=f"CLI session finished ({selected})")

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
    """Configuration submenu - now redirect to main menu items."""
    # This is now just an alias - configuration is handled in main menu
    # Kept for backward compatibility
    pass


# --- SUBMENU: WORKSPACES ---
def submenu_workspaces():
    """Option 1: Workspace Management."""
    print(c("\n  [CONFIG] Gestión de Workspaces\n", f"{Colors.BOLD}{Colors.CYAN}"))
    ws_dir = REPO_ROOT / "workspaces"
    ws_dir.mkdir(exist_ok=True)

    # List existing
    existing = [d.name for d in ws_dir.iterdir() if d.is_dir() and d.name != ".gitkeep"]
    if existing:
        print("  Workspaces actuales:")
        for ws in sorted(existing):
            print(f"    [DIR] {ws}")
    else:
        print("  (Sin workspaces configurados)")

    defaults = [
        "personal",
        "professional",
        "research",
        "content",
        "development",
        "homelab",
    ]
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
            update_master_workspace_status(name, configured=True)
            print_ok(f"Workspace '{name}' creado.")
    elif choice == "2":
        for ws in defaults:
            d = ws_dir / ws
            d.mkdir(exist_ok=True)
            (d / "notes").mkdir(exist_ok=True)
            (d / "projects").mkdir(exist_ok=True)
            update_master_workspace_status(ws, configured=True)
        print_ok(f"Workspaces por defecto restablecidos: {', '.join(defaults)}")

    pause()


# --- SUBMENU: MEMORIA/WIKI ---
def submenu_memoria_wiki():
    """Option 2: Memory/Wiki configuration."""
    while True:
        config = load_config()
        clear_screen()
        print(c("\n  [CONFIG] Memoria/Wiki\n", f"{Colors.BOLD}{Colors.CYAN}"))
        
        # Show current settings
        wiki_path = config.get("wiki_path", "")
        memory_path = config.get("memory_path", str(STANDALONE_CONFIG_DIR / "memory"))
        auto_sync = config.get("auto_sync", False)
        sync_interval = config.get("sync_interval", 30)
        
        # Display current values
        wiki_display = c(wiki_path if wiki_path else "(no configurado)", Colors.YELLOW if not wiki_path else Colors.GREEN)
        memory_display = c(memory_path, Colors.GREEN)
        auto_display = c("Sí" if auto_sync else "No", Colors.GREEN if auto_sync else Colors.YELLOW)
        
        print(f"  Wiki Path:     {wiki_display}")
        print(f"  Memory Path:   {memory_display}")
        print(f"  Auto-sync:     {auto_display}")
        if auto_sync:
            print(f"  Sync Interval: {sync_interval} minutos")
        print()
        
        print(f"    {c('1', Colors.CYAN)}. [SET] Configurar Wiki Path")
        print(f"    {c('2', Colors.CYAN)}. [SET] Configurar Memory Path")
        print(f"    {c('3', Colors.CYAN)}. [TOGGLE] Auto-sync: {'Desactivar' if auto_sync else 'Activar'}")
        print(f"    {c('4', Colors.CYAN)}. [CONFIG] Cambiar intervalo de sync")
        print(f"    {c('0', Colors.RED)}. ↩  Volver\n")
        
        choice = prompt_choice("  Selecciona: ", {"0", "1", "2", "3", "4"})
        
        if choice == "0":
            return
        elif choice == "1":
            # Set wiki path
            default_wiki = str(Path.home() / "wiki")
            new_path = input(f"  Wiki path [{default_wiki}]: ").strip()
            if not new_path:
                new_path = default_wiki
            
            wiki_dir = Path(new_path).expanduser()
            if wiki_dir.exists():
                config["wiki_path"] = str(wiki_dir)
                save_config(config)
                print_ok(f"Wiki path configurado: {wiki_dir}")
            else:
                create = prompt_yes_no(f"El directorio {wiki_dir} no existe. ¿Crear?", default=True)
                if create:
                    try:
                        wiki_dir.mkdir(parents=True, exist_ok=True)
                        config["wiki_path"] = str(wiki_dir)
                        save_config(config)
                        print_ok(f"Wiki path creado y configurado: {wiki_dir}")
                    except Exception as e:
                        print_error(f"No se pudo crear el directorio: {e}")
                else:
                    print_info("Operación cancelada.")
            pause()
            
        elif choice == "2":
            # Set memory path
            new_path = input(f"  Memory path [{memory_path}]: ").strip()
            if not new_path:
                print_info("Se mantiene el path actual.")
                pause()
                continue
            
            memory_dir = Path(new_path).expanduser()
            if memory_dir.exists():
                config["memory_path"] = str(memory_dir)
                save_config(config)
                print_ok(f"Memory path configurado: {memory_dir}")
            else:
                create = prompt_yes_no(f"El directorio {memory_dir} no existe. ¿Crear?", default=True)
                if create:
                    try:
                        memory_dir.mkdir(parents=True, exist_ok=True)
                        config["memory_path"] = str(memory_dir)
                        save_config(config)
                        print_ok(f"Memory path creado y configurado: {memory_dir}")
                    except Exception as e:
                        print_error(f"No se pudo crear el directorio: {e}")
                else:
                    print_info("Operación cancelada.")
            pause()
            
        elif choice == "3":
            # Toggle auto-sync
            config["auto_sync"] = not auto_sync
            save_config(config)
            status = "activado" if config["auto_sync"] else "desactivado"
            print_ok(f"Auto-sync {status}.")
            pause()
            
        elif choice == "4":
            # Set sync interval
            new_interval = input(f"  Intervalo en minutos [{sync_interval}]: ").strip()
            if new_interval:
                try:
                    interval = int(new_interval)
                    if interval >= 1:
                        config["sync_interval"] = interval
                        save_config(config)
                        print_ok(f"Intervalo actualizado a {interval} minutos.")
                    else:
                        print_error("El intervalo debe ser al menos 1 minuto.")
                except ValueError:
                    print_error("Por favor ingresa un número válido.")
            pause()


# --- SUBMENU: COMPORTAMIENTO AGENTE ---
def submenu_comportamiento_agente():
    """Option 3: Configure Agent Behavior (formerly Profile)."""
    print(c("\n  [CONFIG] Comportamiento del Agente\n", f"{Colors.BOLD}{Colors.CYAN}"))
    
    # Load current config
    config = load_config()
    
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
    cur_lang = _extract(lines, "- **Primary Language**") or config.get("language", "es")
    cur_style = _extract(lines, "- Response style")
    cur_cli = config.get("default_cli", get_default_cli())

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

    content = re.sub(
        r"- \*\*Primary Language\*\*: .*", f"- **Primary Language**: {lang}", content
    )
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

    # Save to config.json
    config["language"] = lang
    config["default_cli"] = new_cli
    save_config(config)
    
    # Also save to profile.md for backward compatibility
    _save_profile(lang, new_cli)
    print_ok("Configuración del agente actualizada.")
    pause()


# --- SUBMENU: SKILLS ---
def get_skills_directories() -> list[Path]:
    """Get list of skills directories (repo and standalone)."""
    dirs = []
    # Repo skills directory
    repo_skills = REPO_ROOT / "skills"
    if repo_skills.exists():
        dirs.append(repo_skills)
    # Standalone skills directory
    standalone_skills = STANDALONE_CONFIG_DIR / "skills"
    if standalone_skills.exists():
        dirs.append(standalone_skills)
    return dirs


def list_available_skills() -> dict[str, Path]:
    """List all available skills from all directories.
    
    Returns:
        dict mapping skill_name -> skill_file_path
    """
    skills = {}
    for skills_dir in get_skills_directories():
        for toml_file in skills_dir.glob("*.toml"):
            skill_name = toml_file.stem
            if skill_name not in skills:  # First found takes precedence
                skills[skill_name] = toml_file
    return skills


def submenu_skills():
    """Option 4: Skills management."""
    while True:
        config = load_config()
        clear_screen()
        print(c("\n  [CONFIG] Skills\n", f"{Colors.BOLD}{Colors.CYAN}"))
        
        # Get skills info
        all_skills = list_available_skills()
        enabled_skills = config.get("enabled_skills", [])
        
        # Count enabled/available
        enabled_count = len([s for s in enabled_skills if s in all_skills])
        total_count = len(all_skills)
        
        print(f"  Skills disponibles: {total_count}")
        print(f"  Skills habilitados: {enabled_count}")
        print()
        
        print(f"    {c('1', Colors.CYAN)}. [LIST] Listar todos los skills")
        print(f"    {c('2', Colors.CYAN)}. [ENABLE] Habilitar skill")
        print(f"    {c('3', Colors.CYAN)}. [DISABLE] Deshabilitar skill")
        print(f"    {c('4', Colors.CYAN)}. [IMPORT] Importar skill desde path")
        print(f"    {c('0', Colors.RED)}. ↩  Volver\n")
        
        choice = prompt_choice("  Selecciona: ", {"0", "1", "2", "3", "4"})
        
        if choice == "0":
            return
        elif choice == "1":
            # List all skills
            _list_skills(all_skills, enabled_skills)
            pause()
        elif choice == "2":
            # Enable skill
            _enable_skill(all_skills, enabled_skills, config)
        elif choice == "3":
            # Disable skill
            _disable_skill(enabled_skills, config)
        elif choice == "4":
            # Import skill
            _import_skill()


def _list_skills(all_skills: dict, enabled_skills: list):
    """Display all available skills with their status."""
    print(c("\n  ─── Skills Disponibles ───\n", Colors.BOLD))
    
    if not all_skills:
        print_warn("  No se encontraron skills.")
        print_info("  Coloca archivos .toml en:")
        print_info(f"    - {REPO_ROOT / 'skills'}")
        print_info(f"    - {STANDALONE_CONFIG_DIR / 'skills'}")
        return
    
    # Sort: enabled first, then alphabetically
    sorted_skills = sorted(all_skills.items(), key=lambda x: (x[0] not in enabled_skills, x[0]))
    
    for skill_name, skill_path in sorted_skills:
        is_enabled = skill_name in enabled_skills
        status = c("[✓]", Colors.GREEN) if is_enabled else c("[ ]", Colors.DIM)
        location = "repo" if REPO_ROOT in skill_path.parents else "standalone"
        print(f"    {status} {c(skill_name, Colors.CYAN)} ({location})")
        # Try to read description from TOML
        try:
            content = skill_path.read_text(encoding="utf-8")
            for line in content.splitlines():
                if line.startswith("description"):
                    desc = line.split("=", 1)[1].strip().strip('"\'')
                    print(f"        {c(desc, Colors.DIM)}")
                    break
        except Exception:
            pass


def _enable_skill(all_skills: dict, enabled_skills: list, config: dict):
    """Enable a skill."""
    if not all_skills:
        print_warn("\n  No hay skills disponibles para habilitar.")
        pause()
        return
    
    print(c("\n  ─── Habilitar Skill ───\n", Colors.BOLD))
    
    # Show disabled skills
    disabled = {k: v for k, v in all_skills.items() if k not in enabled_skills}
    if not disabled:
        print_info("  Todos los skills disponibles ya están habilitados.")
        pause()
        return
    
    skill_list = sorted(disabled.keys())
    for i, skill_name in enumerate(skill_list, 1):
        print(f"    {c(str(i), Colors.CYAN)}. {skill_name}")
    print(f"    {c('0', Colors.RED)}. Cancelar\n")
    
    choice = input("  Selecciona skill a habilitar: ").strip()
    try:
        idx = int(choice) - 1
        if 0 <= idx < len(skill_list):
            skill_name = skill_list[idx]
            if skill_name not in enabled_skills:
                enabled_skills.append(skill_name)
                config["enabled_skills"] = enabled_skills
                save_config(config)
                print_ok(f"Skill '{skill_name}' habilitado.")
            else:
                print_info(f"Skill '{skill_name}' ya estaba habilitado.")
        elif choice == "0":
            return
        else:
            print_warn("Opción inválida.")
    except ValueError:
        print_warn("Por favor ingresa un número.")
    pause()


def _disable_skill(enabled_skills: list, config: dict):
    """Disable a skill."""
    if not enabled_skills:
        print_info("\n  No hay skills habilitados.")
        pause()
        return
    
    print(c("\n  ─── Deshabilitar Skill ───\n", Colors.BOLD))
    
    for i, skill_name in enumerate(enabled_skills, 1):
        print(f"    {c(str(i), Colors.CYAN)}. {skill_name}")
    print(f"    {c('0', Colors.RED)}. Cancelar\n")
    
    choice = input("  Selecciona skill a deshabilitar: ").strip()
    try:
        idx = int(choice) - 1
        if 0 <= idx < len(enabled_skills):
            skill_name = enabled_skills.pop(idx)
            config["enabled_skills"] = enabled_skills
            save_config(config)
            print_ok(f"Skill '{skill_name}' deshabilitado.")
        elif choice == "0":
            return
        else:
            print_warn("Opción inválida.")
    except ValueError:
        print_warn("Por favor ingresa un número.")
    pause()


def _import_skill():
    """Import a skill from an external path."""
    print(c("\n  ─── Importar Skill ───\n", Colors.BOLD))
    print_info("Ingresa la ruta a un archivo .toml de skill.")
    print_info("El archivo será copiado al directorio de skills standalone.\n")
    
    src_path = input("  Ruta del skill: ").strip()
    if not src_path:
        print_info("Operación cancelada.")
        pause()
        return
    
    src = Path(src_path).expanduser()
    if not src.exists():
        print_error(f"El archivo no existe: {src}")
        pause()
        return
    
    if not src.suffix == ".toml":
        print_warn("El archivo no tiene extensión .toml. ¿Continuar?")
        if not prompt_yes_no("", default=False):
            pause()
            return
    
    # Create standalone skills dir
    skills_dir = STANDALONE_CONFIG_DIR / "skills"
    skills_dir.mkdir(parents=True, exist_ok=True)
    
    dest = skills_dir / src.name
    
    if dest.exists():
        if not prompt_yes_no(f"El skill {src.name} ya existe. ¿Sobrescribir?", default=False):
            print_info("Operación cancelada.")
            pause()
            return
    
    try:
        import shutil as shutil_module
        shutil_module.copy2(src, dest)
        print_ok(f"Skill importado: {dest}")
        
        # Ask to enable
        skill_name = src.stem
        if prompt_yes_no(f"¿Habilitar skill '{skill_name}'?", default=True):
            config = load_config()
            enabled = config.get("enabled_skills", [])
            if skill_name not in enabled:
                enabled.append(skill_name)
                config["enabled_skills"] = enabled
                save_config(config)
                print_ok(f"Skill '{skill_name}' habilitado.")
    except Exception as e:
        print_error(f"Error al importar: {e}")
    
    pause()


def submenu_system_status():
    """3.1: System Status with option to install missing components."""
    print(c("\n  [STATUS] Estado del Sistema\n", f"{Colors.BOLD}{Colors.CYAN}"))

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
        r = subprocess.run(
            ["git", "--version"], capture_output=True, text=True, check=False
        )
        if r.returncode == 0:
            print_ok(f"Git: {r.stdout.strip()}")
            checks_ok += 1
        else:
            print_warn("Git: no detectado (opcional)")
    except Exception:
        print_warn("Git: no detectado (opcional)")

    # 3. Framework structure
    checks_total += 1
    required = [
        "core/.context",
        "core/agents",
        "core/skills",
        "core/scripts",
        "workspaces",
    ]
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
        print(c(f"    [MISSING] {CLI_LABELS.get(cli, cli)} (no instalado)", Colors.DIM))
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
            days = (
                datetime.now() - datetime.fromtimestamp(last_sync.stat().st_mtime)
            ).days
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
        print(c(summary + " — Sistema saludable [OK]", Colors.GREEN))
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
        print_error(
            "No se pudo instalar. Intenta manualmente: npm install -g opencode-ai"
        )


def _save_profile(lang: str = "es", default_cli: str = "opencode"):
    """Save profile.md with current settings."""
    import platform as plat

    version = "0.4.0-beta"
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


def update_master_workspace_status(workspace_name: str, configured: bool = True):
    """Actualiza estado de workspace en MASTER.md."""
    master_path = CONTEXT_DIR / "MASTER.md"
    if not master_path.exists():
        return

    content = master_path.read_text(encoding="utf-8")

    ws_name_cap = workspace_name.capitalize()
    if configured:
        old = f"- [ ] {ws_name_cap}: No configurado."
        new = f"- [x] {ws_name_cap}: Configurado."
    else:
        old = f"- [x] {ws_name_cap}: Configurado."
        new = f"- [ ] {ws_name_cap}: No configurado."

    if old in content:
        content = content.replace(old, new)
        master_path.write_text(content, encoding="utf-8")


def sync_workspaces_status():
    """Sincroniza estado de workspaces en MASTER.md con directorios existentes."""
    ws_dir = REPO_ROOT / "workspaces"
    if not ws_dir.exists():
        return

    existing = [d.name for d in ws_dir.iterdir() if d.is_dir() and d.name != ".gitkeep"]

    defaults = [
        "personal",
        "professional",
        "research",
        "content",
        "development",
        "homelab",
    ]

    # Marcar como configurados los que existen
    for ws in existing:
        update_master_workspace_status(ws, configured=True)

    # Marcar como no configurados los defaults que no existen
    for ws in defaults:
        if ws not in existing:
            update_master_workspace_status(ws, configured=False)


# --- HELP SYSTEM ---
def show_help():
    """Display comprehensive help information."""
    print_banner()
    print(c("\n  ═════════════════ AYUDA / HELP ═════════════════\n", f"{Colors.BOLD}{Colors.HEADER}"))
    
    # Menu commands
    print(c("  ─── COMANDOS DEL MENÚ ───\n", f"{Colors.BOLD}{Colors.CYAN}"))
    print(f"    {c('1', Colors.GREEN)}. [CONFIG]   Workspaces — Gestión de directorios de trabajo")
    print(f"    {c('2', Colors.GREEN)}. [CONFIG]   Memoria/Wiki — Configurar paths y auto-sync")
    print(f"    {c('3', Colors.GREEN)}. [CONFIG]   Comportamiento Agente — Idioma, CLI default")
    print(f"    {c('4', Colors.GREEN)}. [CONFIG]   Skills — Habilitar/deshabilitar/importar skills")
    print(f"    {c('5', Colors.GREEN)}. [SYNC]     Contexto — Sincronizar (manual/auto)")
    print(f"    {c('6', Colors.GREEN)}. [LAUNCH]   Iniciar sesión con AI CLI")
    print(f"    {c('7', Colors.GREEN)}. [UPDATE]   Buscar actualizaciones del framework")
    print(f"    {c('8', Colors.GREEN)}. [HELP]     Ayuda")
    print(f"    {c('0', Colors.RED)}. [EXIT]     Salir del menú\n")
    
    # Submenus
    print(c("  ─── SUBMENÚS ───\n", f"{Colors.BOLD}{Colors.CYAN}"))
    print(f"    Memoria/Wiki:")
    print(f"      [1] Configurar Wiki Path, [2] Memory Path, [3] Toggle auto-sync, [4] Intervalo")
    print(f"    Skills:")
    print(f"      [1] Listar skills, [2] Habilitar, [3] Deshabilitar, [4] Importar")
    print(f"    Sync:")
    print(f"      [1] Sync ahora, [2] Toggle modo, [3] Cambiar intervalo\n")
    
    # CLI flags
    print(c("  ─── BANDERAS CLI / CLI FLAGS ───\n", f"{Colors.BOLD}{Colors.CYAN}"))
    print(f"    {c('--help', Colors.YELLOW)}, {c('-h', Colors.YELLOW)}      Muestra esta ayuda")
    print(f"    {c('--sync', Colors.YELLOW)}           Sincroniza contexto y sale")
    print(f"    {c('--version', Colors.YELLOW)}       Muestra versión del framework")
    print(f"    {c('--cli NAME', Colors.YELLOW)}     Inicia CLI directamente (opencode, claude, gemini, codex)\n")
    
    # Skills available
    print(c("  ─── SKILLS DISPONIBLES ───\n", f"{Colors.BOLD}{Colors.CYAN}"))
    print(c("    Invoca con @nombre en tu sesión AI\n", Colors.DIM))
    
    print(f"    {c('📄 Documentos:', Colors.BOLD)}")
    print(f"      @pdf, @docx, @pptx, @markdown-writer, @paper-summarizer")
    print(f"    {c('📊 Datos:', Colors.BOLD)}")
    print(f"      @xlsx, @csv-processor, @etl, @data-viz")
    print(f"    {c('🛠️ Desarrollo:', Colors.BOLD)}")
    print(f"      @skill-creator, @skill-discovery, @python-standards, @mcp-builder")
    print(f"    {c('✨ Productividad:', Colors.BOLD)}")
    print(f"      @task-management, @prompt-improvement, @prd-generator, @content-optimizer")
    print(f"    {c('🎨 Diseño:', Colors.BOLD)}")
    print(f"      @ui-ux-pro-max, @dashboard-pro")
    print(f"    {c('🧠 Sistema:', Colors.BOLD)}")
    print(f"      @decision-engine, @error-recovery, @context-evaluator, @json-prompt-generator\n")
    
    # Agents
    print(c("  ─── AGENTES ───\n", f"{Colors.BOLD}{Colors.CYAN}"))
    print(c("    Delega tareas automáticamente\n", Colors.DIM))
    print(f"    {c('@FreakingJSON-PA', Colors.GREEN)}  → Agente principal (orquestación)")
    print(f"    {c('@context-scout', Colors.GREEN)}   → Descubrimiento de contexto")
    print(f"    {c('@skill-finder', Colors.GREEN)}    → Ruteo de capabilities")
    print(f"    {c('@session-manager', Colors.GREEN)} → Gestión de sesiones diarias")
    print(f"    {c('@doc-writer', Colors.GREEN)}       → Documentación automática")
    print(f"    {c('@feature-architect', Colors.GREEN)}→ Arquitecto de producto (dev-only)")
    print(f"    {c('@skill-finder', Colors.GREEN)}  → Discovery de skills\n")
    
    # Config file
    print(c("  ─── CONFIG.JSON ───\n", f"{Colors.BOLD}{Colors.CYAN}"))
    print(f"    ~/.pa-framework/config.json")
    print(f"    wiki_path, memory_path, auto_sync, sync_interval, enabled_skills, default_cli, language\n")
    
    # Key files
    print(c("  ─── ARCHIVOS CLAVE ───\n", f"{Colors.BOLD}{Colors.CYAN}"))
    print(f"    core/.context/MASTER.md      → Contexto maestro")
    print(f"    core/.context/quick-start.md → Inicio rápido (<500 tokens)")
    print(f"    core/skills/SKILLS.md        → Catálogo completo de skills")
    print(f"    core/agents/AGENTS.md        → Índice de agentes")
    print(f"    core/.context/sessions/      → Sesiones diarias")
    print(f"    workspaces/                   → Directorios de trabajo\n")
    
    print(f"  {'─' * 48}")
    print(c("  Documentación completa: README.md, GEMINI.md, CLAUDE.md", Colors.DIM))
    print()


def show_cli_help():
    """Display CLI help and exit."""
    version = "0.4.0-beta"
    vf = REPO_ROOT / "VERSION"
    if vf.exists():
        version = vf.read_text(encoding="utf-8").strip()
    
    print(f"""
{c('PA Framework Control Panel', Colors.BOLD)} v{version}

{c('USO:', Colors.BOLD)}
  ./pa.sh [OPCIONES]
  python core/scripts/pa.py [OPCIONES]

{c('OPCIONES:', Colors.BOLD)}
  -h, --help      Muestra esta ayuda y sale
  --sync          Sincroniza contexto (MASTER.md → tool-specific) y sale
  --version       Muestra la versión y sale
  --cli NAME      Inicia CLI directamente sin menú (opencode, claude, gemini, codex)

{c('MENÚ INTERACTIVO (N30 Spec):', Colors.BOLD)}
  Sin opciones, abre el menú interactivo:
    1. [CONFIG] Workspaces
    2. [CONFIG] Memoria/Wiki
    3. [CONFIG] Comportamiento Agente
    4. [CONFIG] Skills
    5. [SYNC] Contexto (manual/auto)
    6. [LAUNCH] Iniciar Sesión IA
    7. [UPDATE] Actualizar Framework
    8. [HELP] Ayuda
    0. Salir

{c('CONFIG.JSON (~/.pa-framework/config.json):', Colors.BOLD)}
  wiki_path: Path to wiki directory
  memory_path: Path to memory directory
  auto_sync: bool (default: False)
  sync_interval: int minutes (default: 30)
  enabled_skills: list of skill names
  default_cli: "opencode" | "claude" | "gemini" | "codex"
  language: "es" | "en"

{c('EJEMPLOS --cli:', Colors.BOLD)}
  ./pa.sh --cli opencode    # Inicia OpenCode con prompt automático
  ./pa.sh --cli claude      # Inicia Claude Code (fallback a manual)
  ./pa.sh --cli gemini      # Inicia Gemini CLI (fallback a manual)

{c('SKILLS DISPONIBLES:', Colors.BOLD)}
  @pdf, @xlsx, @csv-processor, @docx, @pptx, @data-viz
  @task-management, @skill-discovery, @prompt-improvement
  @prd-generator, @etl, @error-recovery, @decision-engine
  @ui-ux-pro-max, @dashboard-pro, @skill-creator, @mcp-builder

{c('AGENTES:', Colors.BOLD)}
  @FreakingJSON-PA (principal), @context-scout, @skill-finder
  @session-manager, @doc-writer, @feature-architect, @skill-finder

{c('ARCHIVOS CLAVE:', Colors.BOLD)}
  core/.context/quick-start.md  → Guía de inicio rápido
  core/skills/SKILLS.md          → Catálogo de skills
  core/agents/AGENTS.md          → Índice de agentes
  ~/.pa-framework/config.json    → Configuración del usuario

{c('EJEMPLOS:', Colors.BOLD)}
  ./pa.sh                  # Menú interactivo
  ./pa.sh --sync           # Sincronizar y salir
  ./pa.sh --cli opencode   # Iniciar OpenCode con prompt
  ./pa.sh --help           # Esta ayuda

{c('DOCUMENTACIÓN:', Colors.BOLD)}
  README.md, GEMINI.md, CLAUDE.md
""")


# --- UPDATE CHECK ---
def menu_updates():
    """Option 4: Check for updates."""
    print(c("\n  [SYNC] Buscando actualizaciones...\n", Colors.CYAN))

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
            print_info(
                "No se pudo verificar (git no disponible o no es un repositorio)."
            )

    pause()


# --- MAIN MENU ---
def menu_help():
    """Show help information."""
    show_help()
    pause()


def main_menu():
    """Main control panel with 7 options (N30's spec)."""
    while True:
        clear_screen()
        print_banner()
        
        # Load config to show current state indicators
        config = load_config()
        auto_sync = config.get("auto_sync", False)
        enabled_skills = len(config.get("enabled_skills", []))
        sync_mode = "Auto" if auto_sync else "Manual"
        
        print()
        print(f"    {c('1', Colors.CYAN)}. [CONFIG] Workspaces")
        print(f"    {c('2', Colors.CYAN)}. [CONFIG] Memoria/Wiki")
        print(f"    {c('3', Colors.CYAN)}. [CONFIG] Comportamiento Agente")
        print(f"    {c('4', Colors.CYAN)}. [SYNC] Contexto {c('(' + sync_mode + ')', Colors.DIM)}")
        print(f"    {c('5', Colors.CYAN)}. [LAUNCH] {c('Iniciar Sesión IA', Colors.BOLD)}")
        print(f"    {c('6', Colors.CYAN)}. [UPDATE] Actualizar Framework")
        print(f"    {c('7', Colors.CYAN)}. [HELP] {c('Ayuda', Colors.YELLOW)}")
        print(f"    {c('0', Colors.RED)}. [EXIT] Salir")
        print()

        choice = input(f"  {c('Selecciona una opción', Colors.BOLD)}: ").strip()

        if choice == "0":
            print(c("\n  ¡Hasta luego! [BYE]\n", Colors.CYAN))
            return
        elif choice == "1":
            submenu_workspaces()
        elif choice == "2":
            submenu_memoria_wiki()
        elif choice == "3":
            submenu_comportamiento_agente()
        elif choice == "4":
            menu_sync()
        elif choice == "5":
            menu_launch_ai()
        elif choice == "6":
            menu_updates()
        elif choice == "7":
            menu_help()
        elif choice.lower() in {"h", "/help", "-h", "--help"}:
            menu_help()
        else:
            print_warn("Opción inválida.")
            time.sleep(0.5)


# --- ENTRY POINT ---
def main():
    parser = argparse.ArgumentParser(
        description="FreakingJSON PA Framework Control Panel v0.4.0-beta",
        add_help=False,  # Custom help handler
    )
    parser.add_argument("--sync", action="store_true", help="Run sync and exit")
    parser.add_argument("--version", action="store_true", help="Show version and exit")
    parser.add_argument("-h", "--help", action="store_true", help="Show help and exit")
    parser.add_argument(
        "--cli", 
        type=str, 
        metavar="NAME",
        choices=CLI_COMMANDS,
        help="Launch specific AI CLI directly (opencode, claude, gemini, codex)"
    )
    args = parser.parse_args()

    # Handle --version
    if args.version:
        version = "0.4.0-beta"
        vf = REPO_ROOT / "VERSION"
        if vf.exists():
            version = vf.read_text(encoding="utf-8").strip()
        print(f"FreakingJSON PA Framework v{version}")
        sys.exit(0)

    # Handle --help
    if args.help:
        show_cli_help()
        sys.exit(0)

    # Setup
    os.chdir(REPO_ROOT)
    for stream in (sys.stdout, sys.stderr):
        rec = getattr(stream, "reconfigure", None)
        if rec:
            try:
                rec(encoding="utf-8")
            except Exception:
                pass

    set_title("FreakingJSON PA Framework")

    if args.sync:
        sys.exit(0 if run_sync_context() else 1)

    # Handle --cli flag: auto-launch and exit
    if args.cli:
        # First-time setup if needed
        if not (CONTEXT_DIR / "profile.md").exists():
            install_script = SCRIPT_DIR / "install.py"
            if install_script.exists():
                print_info("Primera ejecución detectada. Iniciando instalador...")
                result = subprocess.run(
                    [get_python(), str(install_script)], cwd=REPO_ROOT, check=False
                )
                if not (CONTEXT_DIR / "profile.md").exists():
                    print_error("La instalación no se completó correctamente.")
                    sys.exit(1)
        
        # Ensure session file exists
        _ensure_session_file()
        
        # Get magic prompt and try auto-launch
        magic = get_magic_prompt()
        _init_cli_memory_bridge(args.cli, magic)
        auto_launched = try_auto_launch_cli(args.cli, magic, REPO_ROOT)
        
        if not auto_launched:
            # Fallback: show prompt and launch CLI manually
            print(
                c(
                    f"\n  ╔══ MAGIC PROMPT ════════════════════════════════════╗",
                    f"{Colors.GREEN}{Colors.BOLD}",
                )
            )
            print(c(f"  ║ {magic}", Colors.CYAN))
            print(
                c(
                    f"  ╚════════════════════════════════════════════════════╝\n",
                    f"{Colors.GREEN}{Colors.BOLD}",
                )
            )
            pause("Presiona Enter para iniciar la CLI...")
            
            print_info(f"Iniciando {CLI_LABELS.get(args.cli, args.cli)}...")
            try:
                subprocess.run(args.cli, cwd=REPO_ROOT, shell=True, check=False)
            except KeyboardInterrupt:
                pass
            except Exception as e:
                print_error(f"No se pudo iniciar el CLI: {e}")
                _close_cli_memory_bridge(summary=f"CLI launch error ({args.cli}): {e}")
                sys.exit(1)
        _close_cli_memory_bridge(summary=f"CLI session finished ({args.cli})")
        sys.exit(0)

    # Auto-install check
    if not (CONTEXT_DIR / "profile.md").exists():
        install_script = SCRIPT_DIR / "install.py"
        if install_script.exists():
            print_info("Primera ejecución detectada. Iniciando instalador...")
            result = subprocess.run(
                [get_python(), str(install_script)], cwd=REPO_ROOT, check=False
            )
            # Verificar que la instalación fue exitosa
            if not (CONTEXT_DIR / "profile.md").exists():
                print_error("La instalación no se completó correctamente.")
                print_info(
                    "Verifica los mensajes de error arriba e intenta nuevamente."
                )
                sys.exit(1)

    main_menu()


if __name__ == "__main__":
    main()
