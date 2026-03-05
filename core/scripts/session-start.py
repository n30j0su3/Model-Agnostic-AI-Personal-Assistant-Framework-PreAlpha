#!/usr/bin/env python3
"""
PA Framework — Session Start with Multi-CLI Support
Secuencia de inicio rápido del día con soporte para múltiples CLIs.

Uso:
    python core/scripts/session-start.py

Multi-CLI:
    Este script detecta automáticamente otras instancias CLI activas
    y coordina el acceso a recursos compartidos para prevenir
    pérdida de datos.

Autor: FreakingJSON-PA Framework
Versión: 2.0.0 (Multi-CLI)
"""

import json
import os
import sys
import atexit
from datetime import datetime
from pathlib import Path

# Configurar UTF-8 para Windows (solo si es un terminal interactivo)
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

# --- PATHS ---
SCRIPT_DIR = Path(__file__).resolve().parent
CORE_DIR = SCRIPT_DIR.parent
REPO_ROOT = CORE_DIR.parent
CONTEXT_DIR = CORE_DIR / ".context"
SESSIONS_DIR = CONTEXT_DIR / "sessions"
CODEBASE_DIR = CONTEXT_DIR / "codebase"

# --- GLOBAL COORDINATOR (inicializado en main) ---
_coordinator = None


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


def safe_print(text: str, **kwargs):
    """Print con manejo seguro de Unicode para Windows."""
    try:
        print(text, **kwargs)
    except UnicodeEncodeError:
        # Fallback: encode con reemplazo de caracteres no soportados
        encoding = sys.stdout.encoding or "utf-8"
        safe_text = text.encode(encoding, errors="replace").decode(encoding)
        print(safe_text, **kwargs)


# --- MULTI-CLI COORDINATION ---
def init_multi_cli_coordinator(model: str = "unknown"):
    """Inicializa el coordinador Multi-CLI."""
    global _coordinator

    try:
        sys.path.insert(0, str(SCRIPT_DIR))
        from multi_cli_coordinator import MultiCLICoordinator

        _coordinator = MultiCLICoordinator(model=model)
        _coordinator.start()

        # Registrar shutdown
        atexit.register(shutdown_coordinator)

        return _coordinator
    except Exception as e:
        print(
            c(
                f"[Multi-CLI] Warning: No se pudo iniciar coordinador ({e})",
                Colors.YELLOW,
            )
        )
        return None


def shutdown_coordinator():
    """Limpieza al salir."""
    global _coordinator
    if _coordinator:
        try:
            _coordinator.shutdown()
        except:
            pass


def get_active_clis_summary() -> tuple:
    """
    Obtiene resumen de CLIs activas.

    Returns:
        (count, list of instance info)
    """
    global _coordinator

    if not _coordinator:
        return 0, []

    try:
        instances = _coordinator.get_other_active_instances()
        return len(instances), instances
    except:
        return 0, []


# --- VERIFICACIÓN DE VITALS ---
def check_vitals_integrity():
    """Verificar integridad de archivos vitales (solo en base/dev)."""
    import subprocess

    vitals_script = SCRIPT_DIR / "vitals-guardian.py"
    if not vitals_script.exists():
        return True, []

    try:
        # Ejecutar check sin output para ser rápido
        result = subprocess.run(
            [sys.executable, str(vitals_script), "check"],
            capture_output=True,
            text=True,
            timeout=5,  # Máximo 5 segundos
        )

        if result.returncode != 0:
            # Hay problemas - extraer información clave
            output = result.stdout + result.stderr
            issues = []
            for line in output.split("\n"):
                if "[X]" in line or "[!]" in line:
                    issues.append(line.strip())
            return False, issues[:5]  # Máximo 5 issues

        return True, []
    except:
        return True, []  # Si falla, no bloquear inicio


def show_vitals_status():
    """Mostrar estado de archivos vitales."""
    all_ok, issues = check_vitals_integrity()

    if not all_ok and issues:
        print(c("\n[VITALS] Estado de archivos protegidos:", Colors.BOLD + Colors.RED))
        print(c("  [!] Se detectaron anomalías en archivos vitales", Colors.RED))
        for issue in issues:
            print(f"    {issue}")
        print(f"\n  Ejecuta: python core/scripts/vitals-guardian.py restore")
        return False

    return True


# --- VALIDACIÓN DE AGENTE ---
def check_agent():
    """Verificar si el agente activo es FreakingJSON-PA en OpenCode."""
    opencode_config = REPO_ROOT / ".opencode" / "config.json"

    if not opencode_config.exists():
        return None

    try:
        config = json.loads(opencode_config.read_text(encoding="utf-8"))
        agent = config.get("agent", "")
        return agent
    except:
        return None


def show_agent_warning(agent: str):
    """Mostrar warning si no está usando FreakingJSON-PA."""
    if agent != "FreakingJSON-PA":
        print(c("\n  [TIP] ", Colors.YELLOW), end="")
        print(c(f"Presiona TAB para cambiar a modo 'FreakingJSON-PA'", Colors.CYAN))
        print(c(f"     Agente actual: {agent or 'default'}\n", Colors.DIM))


# --- CARGA MÍNIMA DE DATOS ---
def count_pending() -> int:
    """Contar pendientes en recordatorios.md (solo líneas con - [ ])."""
    recordatorios = CODEBASE_DIR / "recordatorios.md"
    if not recordatorios.exists():
        return 0

    try:
        content = recordatorios.read_text(encoding="utf-8")
        return content.count("- [ ]")
    except:
        return 0


def get_last_session_summary() -> str:
    """Obtener resumen de la última sesión (solo primera línea de resumen)."""
    # Buscar archivos de sesión
    try:
        session_files = sorted(SESSIONS_DIR.glob("*.md"), reverse=True)
        if len(session_files) < 2:  # Necesitamos al menos 2 (hoy y ayer)
            return "Primera sesión"

        # La segunda más reciente es la anterior
        last_session = session_files[1]
        content = last_session.read_text(encoding="utf-8")

        # Buscar línea con "Resumen" o "Logros"
        for line in content.split("\n"):
            if any(x in line for x in ["✅", "completad", "logro", "Listo"]):
                return line.strip("- #*[OK] ")[:60]  # Truncar a 60 chars

        return "Sesión anterior completada"
    except:
        return "No hay datos previos"


def get_all_skills() -> list:
    """Escanea core/skills/core/ y retorna todas las skills disponibles."""
    skills_dir = CORE_DIR / "skills" / "core"
    if not skills_dir.exists():
        return []

    skills = []
    for item in skills_dir.iterdir():
        if item.is_dir() and (item / "SKILL.md").exists():
            skills.append(item.name)

    return sorted(skills)


def get_recent_skills() -> list:
    """Retorna todas las skills disponibles (escaneo real)."""
    return get_all_skills()


def detect_model_from_env() -> str:
    """Detecta el modelo desde variables de entorno o contexto."""
    # Intentar detectar modelo desde entorno o configuración
    model = "unknown"

    # Variable de entorno (puede ser seteada por el wrapper de la CLI)
    if os.environ.get("PA_MODEL"):
        model = os.environ.get("PA_MODEL")

    # Intentar detectar desde opencode config
    try:
        opencode_config = REPO_ROOT / ".opencode" / "config.json"
        if opencode_config.exists():
            config = json.loads(opencode_config.read_text(encoding="utf-8"))
            # Buscar modelo activo
            if "providers" in config:
                for provider, pdata in config["providers"].items():
                    if pdata.get("enabled") and pdata.get("model"):
                        model = pdata.get("model", model)
                        break
    except:
        pass

    return model


# --- TEMPLATE DE INICIO ---
def print_session_start():
    """Imprimir template fijo de inicio de sesión."""
    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("H:%M")

    # Header
    print(c("\n" + "=" * 60, Colors.HEADER))
    print(c("[LAUNCH] ¡SECUENCIA DE DÍA INICIADA!", Colors.BOLD + Colors.GREEN))
    print(c("=" * 60, Colors.HEADER))

    # Info básica
    print(f"\n  [DATE] {date_str} | [TIME] {time_str}")

    # Multi-CLI Status
    cli_count, cli_instances = get_active_clis_summary()
    if cli_count > 0:
        print(
            c("\n[Multi-CLI] [ACTIVE] Instancias Activas:", Colors.BOLD + Colors.CYAN)
        )
        for inst in cli_instances[:3]:  # Mostrar máximo 3
            model = inst.get("model", "unknown")
            inst_id = inst.get("instance_id", "unknown")[:12]
            print(f"   • {inst_id}... ({model})")
        if cli_count > 3:
            print(f"   ... y {cli_count - 3} más")
    else:
        print(c("\n[Multi-CLI] [LAUNCH] Primera instancia del día", Colors.DIM))

    # Agentes
    print(c("\n[AGENTS] Agentes Disponibles:", Colors.BOLD + Colors.CYAN))
    print("   FreakingJSON-PA, context-scout, session-manager, doc-writer")

    # Skills (todas disponibles - escaneo real)
    all_skills = get_all_skills()
    skills_count = len(all_skills)
    skills_preview = ", ".join(all_skills[:4])
    remaining = skills_count - 4
    if remaining > 0:
        skills_display = f"{skills_preview}... (+{remaining} más)"
    else:
        skills_display = skills_preview
    print(c("\n[SKILLS] Skills Disponibles:", Colors.BOLD + Colors.CYAN))
    print(f"   {skills_display}")

    # Pendientes
    pending = count_pending()
    print(c(f"\n[PENDING] Pendientes Heredados: ", Colors.BOLD + Colors.YELLOW), end="")
    print(c(f"[{pending}] tareas pendientes", Colors.YELLOW))

    # Logros sesión anterior
    summary = get_last_session_summary()
    print(c(f"\n[WINS] Logros Sesión Anterior:", Colors.BOLD + Colors.GREEN))
    safe_print(f"   {summary}")

    # Opciones
    print(c("\n[WHAT] ¿Qué necesitas hoy?", Colors.BOLD + Colors.CYAN))
    print("   [1] Continuar pendientes")
    print("   [2] Nueva tarea")
    print("   [3] Revisar estado (/status)")
    print("   [4] Configurar workspace")

    # Multi-CLI hint
    if cli_count > 0:
        print(
            c(
                "\n[Multi-CLI] Tip: Otras CLIs pueden modificar archivos compartidos.",
                Colors.DIM,
            )
        )
        print(
            c("            Los cambios se sincronizarán automáticamente.", Colors.DIM)
        )

    # Frase insignia
    print(c("\n" + "-" * 60, Colors.DIM))
    print(c('   "El conocimiento verdadero trasciende a lo publico."', Colors.HEADER))
    print(c("-" * 60 + "\n", Colors.DIM))


# --- MAIN ---
def main():
    """Función principal de inicio rápido."""
    start_time = datetime.now()

    # Detectar modelo
    model = detect_model_from_env()

    # 1. Inicializar Multi-CLI Coordinator (PRIMERO)
    # Esto permite detectar otras instancias antes de mostrar el banner
    coord = init_multi_cli_coordinator(model)

    # 2. Validar agente (2s)
    agent = check_agent()
    if agent and agent != "FreakingJSON-PA":
        show_agent_warning(agent)

    # 3. Mostrar template de inicio (3s)
    print_session_start()

    # 4. Verificar integridad de archivos vitales (solo base/dev)
    show_vitals_status()

    # 5. Crear sesión del día si no existe
    today = datetime.now().strftime("%Y-%m-%d")
    session_file = SESSIONS_DIR / f"{today}.md"

    if not session_file.exists():
        # Crear sesión mínima
        session_content = f"""---
# Session Log - {today}
id: session-{today}
date: {today}
agent: FreakingJSON
status: active
---

# Sesión {today}

## Inicio
- **Hora**: {datetime.now().strftime("%H:%M")}
- **Agente**: @FreakingJSON
- **Multi-CLI**: {"Activo (" + str(len(coord.get_other_active_instances()) if coord else 0) + " otras instancias)" if coord else "No disponible"}

## Log de Actividades


## Pendientes


## Resumen

"""
        session_file.write_text(session_content, encoding="utf-8")

    # Calcular tiempo
    elapsed = (datetime.now() - start_time).total_seconds()
    print(c(f"  [OK] Sesión iniciada en {elapsed:.1f}s", Colors.GREEN))

    # Mensaje final Multi-CLI
    if coord:
        cli_count = len(coord.get_other_active_instances())
        if cli_count > 0:
            print(
                c(
                    f"  [Multi-CLI] Coordinando con {cli_count} otra(s) instancia(s)",
                    Colors.CYAN,
                )
            )

    return 0


if __name__ == "__main__":
    sys.exit(main())
