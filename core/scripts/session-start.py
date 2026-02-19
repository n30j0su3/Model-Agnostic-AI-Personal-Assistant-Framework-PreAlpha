#!/usr/bin/env python3
"""
PA Framework — Session Start (Optimized <30s)
Secuencia de inicio rápido del día.

Uso:
    python core/scripts/session-start.py
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path

# --- PATHS ---
SCRIPT_DIR = Path(__file__).resolve().parent
CORE_DIR = SCRIPT_DIR.parent
REPO_ROOT = CORE_DIR.parent
CONTEXT_DIR = CORE_DIR / ".context"
SESSIONS_DIR = CONTEXT_DIR / "sessions"
CODEBASE_DIR = CONTEXT_DIR / "codebase"


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
                return line.strip("- #*✅ ")[:60]  # Truncar a 60 chars

        return "Sesión anterior completada"
    except:
        return "No hay datos previos"


def get_recent_skills() -> list:
    """Retornar skills más usadas o variadas si no hay uso."""
    # Por ahora, retornar un subset variado
    core_skills = [
        "skill-creator",
        "markdown-writer",
        "csv-processor",
        "python-standards",
        "xlsx",
        "pdf",
        "task-management",
    ]
    return core_skills


# --- TEMPLATE DE INICIO ---
def print_session_start():
    """Imprimir template fijo de inicio de sesión."""
    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%H:%M")

    # Header
    print(c("\n" + "=" * 60, Colors.HEADER))
    print(c("[LAUNCH] ¡SECUENCIA DE DÍA INICIADA!", Colors.BOLD + Colors.GREEN))
    print(c("=" * 60, Colors.HEADER))

    # Info básica
    print(f"\n  [DATE] {date_str} | [TIME] {time_str}")

    # Agentes
    print(c("\n[AGENTS] Agentes Disponibles:", Colors.BOLD + Colors.CYAN))
    print("   pa-assistant, context-scout, session-manager, doc-writer")

    # Skills (recientes/variadas)
    print(c("\n[SKILLS] Skills Disponibles:", Colors.BOLD + Colors.CYAN))
    skills = get_recent_skills()
    print(f"   {', '.join(skills[:4])}... (+11 más)")

    # Pendientes
    pending = count_pending()
    print(c(f"\n[PENDING] Pendientes Heredados: ", Colors.BOLD + Colors.YELLOW), end="")
    print(c(f"[{pending}] tareas pendientes", Colors.YELLOW))

    # Logros sesión anterior
    summary = get_last_session_summary()
    print(c(f"\n[WINS] Logros Sesión Anterior:", Colors.BOLD + Colors.GREEN))
    print(f"   {summary}")

    # Opciones
    print(c("\n[WHAT] ¿Qué necesitas hoy?", Colors.BOLD + Colors.CYAN))
    print("   [1] Continuar pendientes")
    print("   [2] Nueva tarea")
    print("   [3] Revisar estado (/status)")
    print("   [4] Configurar workspace")

    # Frase insignia
    print(c("\n" + "-" * 60, Colors.DIM))
    print(c('   "El conocimiento verdadero trasciende a lo publico."', Colors.HEADER))
    print(c("-" * 60 + "\n", Colors.DIM))


# --- MAIN ---
def main():
    """Función principal de inicio rápido."""
    start_time = datetime.now()

    # 1. Validar agente (2s)
    agent = check_agent()
    if agent and agent != "FreakingJSON-PA":
        show_agent_warning(agent)

    # 2. Mostrar template de inicio (3s)
    print_session_start()

    # 3. Crear sesión del día si no existe
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

## Log de Actividades


## Pendientes


## Resumen

"""
        session_file.write_text(session_content, encoding="utf-8")

    # Calcular tiempo
    elapsed = (datetime.now() - start_time).total_seconds()
    print(c(f"  [OK] Sesión iniciada en {elapsed:.1f}s", Colors.GREEN))

    return 0


if __name__ == "__main__":
    sys.exit(main())
