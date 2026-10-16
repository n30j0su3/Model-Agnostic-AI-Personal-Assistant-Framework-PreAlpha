#!/usr/bin/env python3
"""
PA Framework — Session Start with Multi-CLI Support
Secuencia de inicio rápido del día con soporte para múltiples CLIs.
v2.2.0: Lazy tier-based context loading via ContextLoader (ADR-001)

Uso:
    python core/scripts/session_start.py
    python core/scripts/session_start.py --skip-context

Multi-CLI:
    Este script detecta automáticamente otras instancias CLI activas
    y coordina el acceso a recursos compartidos para prevenir
    pérdida de datos.

Context Loading (ADR-001):
    Tier 0-1: Bootstrap + Essential — loaded immediately at startup
    Tier 2-4: Context + Reference + Historical — LAZY (deferred)

Autor: FreakingJSON-PA Framework
Versión: 2.2.0 (Context Loader Integration)
"""

import json
import os
import sys
import atexit
import subprocess
from datetime import datetime
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import hashlib

# --- CONTEXT LOADER (v2.2.0) ---
from context_loader import ContextLoader, TokenBudgetTracker, estimate_tokens

# --- PATHS (moved UP for imports) ---
SCRIPT_DIR = Path(__file__).resolve().parent
CORE_DIR = SCRIPT_DIR.parent
MEMORY_DIR = CORE_DIR / "memory"

# Add SCRIPT_DIR to sys.path FIRST (session_bridge.py is here!)
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import workspace_config as workspace_cfg  # noqa: E402

# Add memory to sys.path for session_memory imports
if str(MEMORY_DIR) not in sys.path:
    sys.path.insert(0, str(MEMORY_DIR))

# --- SESSION BRIDGE (v0.4.0) - MEMORY INTEGRATION ---
try:
    from session_bridge import SessionBridge
    MEMORY_BRIDGE_AVAILABLE = True
except ImportError:
    MEMORY_BRIDGE_AVAILABLE = False
    print("[MEMORY] Warning: SessionBridge not available, memory will not persist")

# Global bridge instance
_session_bridge = None

# Configurar UTF-8 para Windows, incluso con stdout/stderr redirigidos
if sys.platform == "win32":
    try:
        
        # v0.4.0-beta fix: reconfigure in-place (TextIOWrapper nuevo dejaba un wrapper
# huérfano que su GC cerraba → "I/O operation on closed file"/"lost sys.stderr" al salir)
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except (ValueError, AttributeError):
        pass

# --- PATHS (redefined for reference) ---
# NOTE: SCRIPT_DIR, CORE_DIR, MEMORY_DIR already defined above for imports
REPO_ROOT = CORE_DIR.parent
CONTEXT_DIR = CORE_DIR / ".context"
SESSIONS_DIR = CONTEXT_DIR / "sessions"
CODEBASE_DIR = CONTEXT_DIR / "codebase"
KNOWLEDGE_DIR = CONTEXT_DIR / "knowledge"

# Ensure critical directories exist (first-run safety)
SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
CODEBASE_DIR.mkdir(parents=True, exist_ok=True)
KNOWLEDGE_DIR.mkdir(parents=True, exist_ok=True)

# --- WARM START RECEIPT (v0.4.1-beta-r3) ---
CACHE_DIR = CONTEXT_DIR / ".cache"
WARM_CACHE_PATH = CACHE_DIR / "warm-start.json"
WARM_CACHE_TTL = 86400  # Hashes invalidate first; TTL is a 24h backstop.
WARM_RECEIPT_SCHEMA = "pa.warm-start/1"
STORAGE_RECEIPT_KEYS = (
    "sqlite_available",
    "wiki_available",
    "md_memory_available",
    "sessions_md_available",
    "all_available",
)
WARM_RECEIPT_INPUTS = (
    "VERSION",
    "AGENTS-lite.md",
    "AGENTS.md",
    ".opencode/agent/FreakingJSON.md",
    "core/.context/quick-start.md",
    "core/.context/MASTER.md",
    "core/.context/profile.md",
    "core/.context/knowledge/sessions-index.json",
    "config/workspaces.json",
    "data/user/workspaces.json",
)

# --- GLOBAL COORDINATOR (inicializado en main) ---
_coordinator = None


# --- MIGRATION CHECK (v0.2.0) ---
def check_pending_migrations():
    """Verifica si hay migraciones pendientes y las aplica automaticamente."""
    try:
        migrate_script = SCRIPT_DIR / "migrate.py"
        if migrate_script.exists():
            result = subprocess.run(
                [sys.executable, str(migrate_script), "--check"],
                capture_output=True,
                text=True,
                timeout=5,
                cwd=REPO_ROOT,
            )
            # Si hay migraciones pendientes, aplicarlas automaticamente
            if result.returncode != 0 or "0" not in result.stdout:
                print(c("\\n[MIGRATE] Aplicando migraciones pendientes...", Colors.CYAN))
                apply_result = subprocess.run(
                    [sys.executable, str(migrate_script), "--apply"],
                    capture_output=True,
                    text=True,
                    timeout=60,
                    cwd=REPO_ROOT,
                )
                if apply_result.returncode == 0:
                    print(c("  [OK] Migraciones aplicadas correctamente", Colors.GREEN))
                else:
                    print(c(f"  [WARN] Migraciones no se pudieron aplicar: {apply_result.stderr.strip()}", Colors.YELLOW))
                    print(c("  Ejecuta manualmente: python core/scripts/migrate.py --apply", Colors.CYAN))
    except Exception:
        pass  # No bloquear inicio si falla verificación


# --- SESSION SHUTDOWN (atexit) ---
def session_shutdown():
    """Cierre automático de sesión al terminar la CLI."""
    global _session_bridge
    
    # Close memory bridge session
    if _session_bridge and _session_bridge.current_session:
        try:
            _session_bridge.end_session(summary="Session ended via atexit")
            # Windows-safe print (stderr may be closed)
            try:
                print("[MEMORY] Session saved to SQLite")
            except (ValueError, OSError):
                pass  # I/O closed, ignore
        except Exception as e:
            # Windows I/O errors are common in atexit
            if not isinstance(e, (ValueError, OSError)):
                try:
                    print(f"[MEMORY] Error saving session: {e}")
                except (ValueError, OSError):
                    pass
    
    # --- SESSION AUTOSAVE (FASE 2) ---
    # Sync interactions log → session MD before closing
    try:
        autosave_script = SCRIPT_DIR / "session_autosave.py"
        if autosave_script.exists():
            subprocess.run(
                [sys.executable, str(autosave_script)],
                capture_output=True,
                timeout=10,
            )
    except (ValueError, OSError, subprocess.TimeoutExpired):
        pass  # Silencioso - no bloquear salida
    
    # --- SESSION END ---
    try:
        session_end_script = SCRIPT_DIR / "session_end.py"
        if session_end_script.exists():
            subprocess.run(
                [sys.executable, str(session_end_script), "--silent"],
                capture_output=True,
                timeout=10,
            )
    except (ValueError, OSError, subprocess.TimeoutExpired):
        pass  # Silencioso - no bloquear salida (Windows-safe)


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


# --- WORKSPACE SYNC (sesion 2026-03-09) ---
def sync_workspaces_status():
    """Renderiza en MASTER los workspaces configurados por el usuario."""
    ws_dir = REPO_ROOT / "workspaces"
    master_path = CONTEXT_DIR / "MASTER.md"

    if not master_path.exists():
        return

    status, entries = workspace_cfg.load_user_config(REPO_ROOT)
    if status == "missing":
        entries = {
            directory.name: {
                "dir": directory.name,
                "display": directory.name.capitalize(),
            }
            for directory in (ws_dir.iterdir() if ws_dir.is_dir() else [])
            if directory.is_dir() and directory.name != ".gitkeep"
        }
    content = master_path.read_text(encoding="utf-8")
    rendered = workspace_cfg.render_master_workspaces(content, entries)
    if rendered != content:
        master_path.write_text(rendered, encoding="utf-8", newline="")


# --- WARM START RECEIPT (v0.4.1-beta-r3) ---
def _relative_source(source: str | Path) -> str | None:
    """Return a safe repository-relative source path, never a local absolute path."""
    try:
        root = REPO_ROOT.resolve()
        path = Path(source)
        if not path.is_absolute():
            path = root / path
        resolved = path.resolve()
        if resolved != root and root not in resolved.parents:
            return None
        return resolved.relative_to(root).as_posix()
    except (OSError, ValueError):
        return None


def _source_sha256(relative: str) -> str | None:
    """Hash one regular in-repo file; missing/unsafe inputs are represented by null."""
    try:
        path = REPO_ROOT / relative
        if path.is_symlink() or not path.is_file():
            return None
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError:
        return None


def _receipt_source_paths(tier_0_data: dict, tier_1_data: dict) -> list[str]:
    paths: set[str] = set(WARM_RECEIPT_INPUTS)
    for tier in (tier_0_data, tier_1_data):
        for source in tier.get("sources", []):
            relative = _relative_source(source)
            if relative:
                paths.add(relative)
    return sorted(paths)


def _framework_version() -> str:
    try:
        return (REPO_ROOT / "VERSION").read_text(encoding="utf-8").strip()
    except OSError:
        return "unknown"


def check_warm_start_cache() -> dict | None:
    """Return a valid metadata-only receipt, or None for a deterministic cold start."""
    if not WARM_CACHE_PATH.exists():
        return None

    try:
        receipt = json.loads(WARM_CACHE_PATH.read_text(encoding="utf-8"))
        if receipt.get("schema") != WARM_RECEIPT_SCHEMA:
            return None
        if time.time() - float(receipt.get("timestamp", 0)) > WARM_CACHE_TTL:
            return None
        if receipt.get("framework_version") != _framework_version():
            return None

        tiers = receipt.get("tiers", {})
        if "tier_0" not in tiers or "tier_1" not in tiers:
            return None
        if any("content" in tier for tier in tiers.values() if isinstance(tier, dict)):
            return None

        source_hashes = receipt.get("source_hashes")
        if not isinstance(source_hashes, dict) or not source_hashes:
            return None
        for relative, expected in source_hashes.items():
            if not isinstance(relative, str) or Path(relative).is_absolute():
                return None
            if _source_sha256(relative) != expected:
                return None
        return receipt
    except (json.JSONDecodeError, KeyError, OSError, TypeError, ValueError):
        return None


def save_warm_cache(
    tier_0_data: dict,
    tier_1_data: dict,
    storage_status: dict | None = None,
) -> bool:
    """Atomically persist hashes and counters only; never cache context text."""
    try:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        source_paths = _receipt_source_paths(tier_0_data, tier_1_data)

        def tier_metadata(data: dict) -> dict:
            sources = []
            for source in data.get("sources", []):
                relative = _relative_source(source)
                if relative:
                    sources.append(relative)
            return {
                "tokens": int(data.get("tokens", 0) or 0),
                "sources": sorted(set(sources)),
            }

        receipt = {
            "schema": WARM_RECEIPT_SCHEMA,
            "timestamp": time.time(),
            "framework_version": _framework_version(),
            "status": "ready",
            "storage": {
                key: bool((storage_status or {}).get(key, False))
                for key in STORAGE_RECEIPT_KEYS
            },
            "tiers": {
                "tier_0": tier_metadata(tier_0_data),
                "tier_1": tier_metadata(tier_1_data),
            },
            "deferred_tiers": [2, 3, 4],
            "source_hashes": {
                relative: _source_sha256(relative) for relative in source_paths
            },
        }
        temp_path = WARM_CACHE_PATH.with_suffix(".json.tmp")
        temp_path.write_text(
            json.dumps(receipt, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        os.replace(temp_path, WARM_CACHE_PATH)
        return True
    except (OSError, TypeError, ValueError):
        return False


def defer_loading(context_loader: ContextLoader) -> dict:
    """
    Register deferred (lazy) tiers 2-4 per ADR-001 §4.
    
    These tiers are NOT loaded at startup. They are registered so that
    downstream consumers know they can be loaded on-demand via
    context_loader.load_tier(tier_num).
    
    Returns:
        Dict with deferred tier metadata.
    """
    deferred = {
        "deferred_tiers": [2, 3, 4],
        "descriptions": {
            2: "Context (PRPs, recent logs)",
            3: "Reference (templates, examples)",
            4: "Historical (archive, old sessions)",
        },
        "status": "deferred",
        "loader_available": context_loader is not None,
    }

    # Pre-register in the loader's cache as None (marks as known-but-unloaded)
    if context_loader:
        for tier in [2, 3, 4]:
            if context_loader._cache.get(tier) is None:
                context_loader._cache[tier] = None  # Explicit deferred marker

    return deferred


def extract_kb_summary_from_tier(tier_1_data: dict) -> dict:
    """
    Extract structured KB summary from ContextLoader tier 1 data.
    
    Replaces the standalone load_knowledge_base_summary() by parsing
    data that was already loaded via ContextLoader.load_tier(1).
    
    Args:
        tier_1_data: Result dict from ContextLoader.load_tier(1)
        
    Returns:
        Structured KB summary dict for display.
    """
    summary = {
        "total_sessions": 0,
        "last_session": None,
        "recent_topics": [],
        "available": False,
    }

    # Try to extract from sessions-index.json (loaded in tier 1)
    sessions_index = KNOWLEDGE_DIR / "sessions-index.json"
    if not sessions_index.exists():
        return summary

    summary["available"] = True

    try:
        with open(sessions_index, "r", encoding="utf-8") as f:
            data = json.load(f)

        sessions = data.get("sessions", []) if isinstance(data, dict) else []
        summary["total_sessions"] = data.get("total_sessions", len(sessions))

        if sessions:
            last = sessions[0]
            summary["last_session"] = {
                "id": last.get("id"),
                "title": last.get("title", "Sin título"),
                "topics": last.get("topics", [])[:3],
            }
            # Collect recent topics
            all_topics = []
            for s in sessions[:5]:
                all_topics.extend(s.get("topics", []))
            # Count frequency
            topic_counts = {}
            for t in all_topics:
                topic_counts[t] = topic_counts.get(t, 0) + 1
            summary["recent_topics"] = sorted(
                topic_counts.items(), key=lambda x: x[1], reverse=True
            )[:5]
    except (json.JSONDecodeError, IOError):
        pass

    return summary


def extract_last_session_from_tier(tier_1_data: dict) -> str:
    """
    Extract last session summary from tier 1 context data.
    
    Replaces get_last_session_summary() — uses sessions-index.json
    already loaded in tier 1 instead of reading full session .md files.
    Full session file reading is deferred to tier 2 (lazy).
    
    Args:
        tier_1_data: Result dict from ContextLoader.load_tier(1)
        
    Returns:
        Brief summary string of last session.
    """
    sessions_index = KNOWLEDGE_DIR / "sessions-index.json"
    if not sessions_index.exists():
        return "Sin sesión anterior"

    try:
        with open(sessions_index, "r", encoding="utf-8") as f:
            data = json.load(f)

        sessions = data.get("sessions", []) if isinstance(data, dict) else []
        if len(sessions) >= 2:
            # Second most recent = previous session
            prev = sessions[1]
            title = prev.get("title", prev.get("summary", ""))
            if title:
                return str(title)[:60]
        elif sessions:
            return sessions[0].get("summary", "Sesión anterior completada")[:60]
    except (json.JSONDecodeError, IOError):
        pass

    return "Sin sesión anterior"


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

    vitals_script = SCRIPT_DIR / "vitals_guardian.py"
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
        print(f"\n  Ejecuta: python core/scripts/vitals_guardian.py restore")
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
    """Mostrar warning si no está usando FreakingJSON-PA.

    v0.4.1-beta: nota interna — el agente instalado en .opencode/agent/ tiene
    id "FreakingJSON" (no "FreakingJSON-PA"). check_agent() lee el campo
    `agent` de .opencode/config.json; este repo lo escribe como "FreakingJSON",
    por lo que el warning legacy dispara siempre. Aceptamos ambos ids para
    dejar de mostrar un aviso stale.
    """
    if agent not in ("FreakingJSON-PA", "FreakingJSON"):
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


def load_knowledge_base_summary() -> dict:
    """Cargar resumen del Knowledge Base para contexto de sesión."""
    summary = {
        "total_sessions": 0,
        "last_session": None,
        "recent_topics": [],
        "available": False,
    }

    try:
        kb_readme = CONTEXT_DIR / "knowledge" / "README.md"
        sessions_index = CONTEXT_DIR / "knowledge" / "sessions-index.json"

        if not kb_readme.exists():
            return summary

        summary["available"] = True

        if sessions_index.exists():
            import json

            with open(sessions_index, "r", encoding="utf-8") as f:
                index = json.load(f)
                summary["total_sessions"] = index.get("total_sessions", 0)
                sessions = index.get("sessions", [])
                if sessions:
                    last = sessions[0]
                    summary["last_session"] = {
                        "id": last.get("id"),
                        "title": last.get("title", "Sin título"),
                        "topics": last.get("topics", [])[:3],
                    }
                    # Collect recent topics
                    all_topics = []
                    for s in sessions[:5]:
                        all_topics.extend(s.get("topics", []))
                    # Count frequency
                    topic_counts = {}
                    for t in all_topics:
                        topic_counts[t] = topic_counts.get(t, 0) + 1
                    summary["recent_topics"] = sorted(
                        topic_counts.items(), key=lambda x: x[1], reverse=True
                    )[:5]

    except Exception:
        pass

    return summary


# --- PARALLEL CHECKS (v2.2.0 — ContextLoader Integration) ---
def run_parallel_checks(coord=None, skip_context: bool = False) -> dict:
    """
    Ejecuta checks independientes en paralelo + carga context via ContextLoader.
    
    v2.2.0 changes:
    - ContextLoader.load_tier(0) + load_tier(1) replace manual context loading
    - Tier 2-4 are deferred (not loaded at startup)
    - Warm start cache check for faster re-starts
    - --skip-context skips ContextLoader entirely
    
    Returns dict con todos los datos pre-cargados.
    """
    results = {}
    start = time.time()
    
    # --- Context Loading via ContextLoader (v2.2.0) ---
    context_loader = None
    tier_0_data = None
    tier_1_data = None
    warm_start = False
    
    if not skip_context:
        # Check warm start cache first
        warm_cache = check_warm_start_cache()
        if warm_cache:
            warm_start = True
            tier_0_data = warm_cache["tiers"]["tier_0"]
            tier_1_data = warm_cache["tiers"]["tier_1"]
        else:
            # Cold start — load tiers 0-1 via ContextLoader
            try:
                context_loader = ContextLoader(repo_root=REPO_ROOT)
                tier_0_data = context_loader.load_tier(0)
                tier_1_data = context_loader.load_tier(1)
                
                # Save to warm cache for next startup
                save_warm_cache(tier_0_data, tier_1_data)
            except Exception:
                # ContextLoader failure should not block startup
                context_loader = None
                tier_0_data = None
                tier_1_data = None
    
    # Defer tiers 2-4 (lazy loading per ADR-001 §4)
    deferred = defer_loading(context_loader)
    
    # Extract structured data from loaded tiers (replaces standalone functions)
    if tier_1_data:
        kb_summary = extract_kb_summary_from_tier(tier_1_data)
        last_summary = extract_last_session_from_tier(tier_1_data)
    else:
        # Fallback to legacy functions if ContextLoader failed or was skipped
        kb_summary = load_knowledge_base_summary()
        last_summary = get_last_session_summary()
    
    # Define operational checks to run in parallel
    # (these are NOT context loading — they're system checks)
    checks = [
        ("cli_summary", get_active_clis_summary),
        ("all_skills", get_all_skills),
        ("pending_count", count_pending),
        ("vitals_status", lambda: check_vitals_integrity()),
        ("workspaces_sync", lambda: sync_workspaces_status()),
    ]
    
    # Execute in parallel with ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {
            executor.submit(check): name
            for name, check in checks
        }
        
        for future in as_completed(futures, timeout=30):
            name = futures[future]
            try:
                results[name] = future.result()
            except Exception:
                results[name] = None
    
    # Add context loading results
    elapsed = time.time() - start
    results["_parallel_time"] = elapsed
    results["_context_loaded"] = tier_0_data is not None
    results["_warm_start"] = warm_start
    results["_tier_0_tokens"] = tier_0_data.get("tokens", 0) if tier_0_data else 0
    results["_tier_1_tokens"] = tier_1_data.get("tokens", 0) if tier_1_data else 0
    results["_deferred"] = deferred
    results["_context_loader"] = context_loader
    
    # Use ContextLoader-derived data (or legacy fallback)
    results["kb_summary"] = kb_summary
    results["last_session"] = last_summary
    
    return results


# --- TEMPLATE DE INICIO (MODIFIED v2.2.0) ---
def print_session_start(parallel_data: dict = None):
    """Imprimir template fijo de inicio de sesión.
    
    Args:
        parallel_data: Dict con datos pre-cargados desde run_parallel_checks()
                       Si es None, ejecuta checks inline (fallback legacy)
    """
    # Use parallel data if provided, else run checks inline (legacy mode)
    if parallel_data:
        cli_count, cli_instances = parallel_data.get("cli_summary", (0, []))
        all_skills = parallel_data.get("all_skills", [])
        kb_summary = parallel_data.get("kb_summary", {"available": False})
        pending = parallel_data.get("pending_count", 0)
        last_summary = parallel_data.get("last_session", "Sin sesión anterior")
        parallel_time = parallel_data.get("_parallel_time", 0)
    else:
        # Legacy fallback - run inline
        cli_count, cli_instances = get_active_clis_summary()
        all_skills = get_all_skills()
        kb_summary = load_knowledge_base_summary()
        pending = count_pending()
        last_summary = get_last_session_summary()
        parallel_time = 0
    
    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%H:%M")

    # Header
    print(c("\n" + "=" * 60, Colors.HEADER))
    print(c("[LAUNCH] ¡SECUENCIA DE DÍA INICIADA!", Colors.BOLD + Colors.GREEN))
    print(c("=" * 60, Colors.HEADER))

    # Info básica
    print(f"\n  [DATE] {date_str} | [TIME] {time_str}")

    # Multi-CLI Status
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
    skills_count = len(all_skills)
    skills_preview = ", ".join(all_skills[:4])
    remaining = skills_count - 4
    if remaining > 0:
        skills_display = f"{skills_preview}... (+{remaining} más)"
    else:
        skills_display = skills_preview
    print(c("\n[SKILLS] Skills Disponibles:", Colors.BOLD + Colors.CYAN))
    print(f"   {skills_display}")

    # Knowledge Base
    if kb_summary["available"]:
        print(c("\n[KNOWLEDGE] Base de Conocimiento:", Colors.BOLD + Colors.CYAN))
        print(f"   {kb_summary['total_sessions']} sesiones indexadas")
        if kb_summary["last_session"]:
            last = kb_summary["last_session"]
            print(f"   Última: {last['title'][:50]}...")
        if kb_summary["recent_topics"]:
            topics_str = ", ".join([t[0] for t in kb_summary["recent_topics"][:3]])
            print(f"   Temas recientes: {topics_str}")
    else:
        print(c("\n[KNOWLEDGE] Base de Conocimiento:", Colors.BOLD + Colors.CYAN))
        print("   No inicializado (ejecutar: python core/scripts/kb-init.py)")

    # Pendientes
    print(c(f"\n[PENDING] Pendientes Heredados: ", Colors.BOLD + Colors.YELLOW), end="")
    print(c(f"[{pending}] tareas pendientes", Colors.YELLOW))

    # Logros sesión anterior
    print(c(f"\n[WINS] Logros Sesión Anterior:", Colors.BOLD + Colors.GREEN))
    safe_print(f"   {last_summary}")

    # Parallel optimization indicator + Context loader status (v2.2.0)
    if parallel_time > 0:
        context_loaded = parallel_data.get("_context_loaded", False) if parallel_data else False
        warm_start = parallel_data.get("_warm_start", False) if parallel_data else False
        tier_0_tokens = parallel_data.get("_tier_0_tokens", 0) if parallel_data else 0
        tier_1_tokens = parallel_data.get("_tier_1_tokens", 0) if parallel_data else 0
        deferred = parallel_data.get("_deferred", {}) if parallel_data else {}
        
        if context_loaded:
            cache_type = "warm cache" if warm_start else "cold start"
            total_tokens = tier_0_tokens + tier_1_tokens
            print(c(f"\n[CONTEXT] Tier 0-1 loaded ({cache_type}): {total_tokens} tokens", Colors.DIM))
            deferred_tiers = deferred.get("deferred_tiers", [2, 3, 4])
            print(c(f"[CONTEXT] Tiers {deferred_tiers} deferred (lazy)", Colors.DIM))
        print(c(f"[OPTIMIZED] Checks completed in {parallel_time:.1f}s", Colors.DIM))

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


# --- DETERMINISTIC BOOTSTRAP-ONLY PATH (v0.4.1-beta-r3) ---
def _refresh_bootstrap_indexes() -> bool:
    """Refresh dashboard indexes in-process; best-effort and process-free."""
    ok = True
    try:
        from skills_indexer import SkillsIndexer

        SkillsIndexer().index_all_skills()
    except Exception:
        ok = False
    try:
        from interaction_logger import InteractionLogger

        InteractionLogger().rebuild_interactions_index()
    except Exception:
        ok = False
    return ok


def _discover_storage_status() -> dict:
    """Return only non-sensitive storage availability booleans."""
    script = SCRIPT_DIR / "persistent_storage_discover.py"
    if not script.exists():
        return {key: False for key in STORAGE_RECEIPT_KEYS}
    try:
        result = subprocess.run(
            [sys.executable, str(script), "--integration"],
            capture_output=True,
            text=True,
            timeout=10,
            cwd=REPO_ROOT,
        )
        payload = json.loads(result.stdout) if result.returncode == 0 else {}
        if not isinstance(payload, dict):
            payload = {}
    except (OSError, subprocess.SubprocessError, json.JSONDecodeError):
        payload = {}
    return {key: bool(payload.get(key, False)) for key in STORAGE_RECEIPT_KEYS}


def _run_bootstrap_only() -> int:
    """Build or reuse the compact receipt without opening a user session."""
    _refresh_bootstrap_indexes()
    receipt = check_warm_start_cache()
    if receipt is not None:
        print(json.dumps({
            "schema": WARM_RECEIPT_SCHEMA,
            "status": "warm",
            "receipt": "core/.context/.cache/warm-start.json",
        }))
        return 0

    try:
        heal_script = SCRIPT_DIR / "system_check.py"
        if heal_script.exists():
            subprocess.run(
                [sys.executable, str(heal_script), "--fix", "--quiet-first-run"],
                capture_output=True,
                text=True,
                timeout=30,
                cwd=REPO_ROOT,
            )
    except (OSError, subprocess.SubprocessError):
        pass

    check_pending_migrations()
    storage_status = _discover_storage_status()
    try:
        loader = ContextLoader(repo_root=REPO_ROOT)
        tier_0_data = loader.load_tier(0)
        tier_1_data = loader.load_tier(1)
    except Exception:
        return 1

    if not save_warm_cache(tier_0_data, tier_1_data, storage_status=storage_status):
        return 1
    print(json.dumps({
        "schema": WARM_RECEIPT_SCHEMA,
        "status": "cold-refreshed",
        "receipt": "core/.context/.cache/warm-start.json",
    }))
    return 0


# --- MAIN (v2.2.0 — ContextLoader Integration) ---
def main():
    """Función principal de inicio rápido.
    
    v2.2.0:
    - ContextLoader.load_tier(0) + load_tier(1) for immediate context
    - Tier 2-4 deferred (lazy loading per ADR-001)
    - Warm start cache for faster re-starts (<2s target)
    - --skip-context flag to skip all context loading
    """
    import argparse

    parser = argparse.ArgumentParser(description="PA Framework - Session Start Script")
    parser.add_argument(
        "--skip-validation",
        action="store_true",
        help="Skip framework enforcement validation",
    )
    parser.add_argument(
        "--no-parallel",
        action="store_true",
        help="Disable parallel execution (legacy mode)",
    )
    parser.add_argument(
        "--skip-context",
        action="store_true",
        help="Skip context loading entirely (API-Contracts.md compatibility)",
    )
    parser.add_argument(
        "--bootstrap-only",
        action="store_true",
        help="Prepare/reuse the warm receipt without opening a CLI session",
    )
    args = parser.parse_args()

    if args.bootstrap_only:
        return _run_bootstrap_only()

    start_time = datetime.now()

    # 0. Auto-heal en primer arranque (v0.3.9-alpha): si faltan MASTER.md,
    #    profile.md o workspaces/, crearlos desde templates ANTES de validar.
    #    Fresh install pasa de 3 errores a 0 sin comandos extra.
    try:
        heal_script = SCRIPT_DIR / "system_check.py"
        if heal_script.exists():
            heal_result = subprocess.run(
                [sys.executable, str(heal_script), "--fix", "--quiet-first-run"],
                capture_output=True, text=True, timeout=30,
            )
            if heal_result.returncode == 0 and "creado" in (heal_result.stdout or "").lower():
                print("  [OK] Primer arranque: contexto base creado (MASTER.md, profile.md)")
    except Exception:
        pass  # nunca bloquear el arranque por el auto-heal

    # 0b. Verificar migraciones pendientes (v0.2.0)
    check_pending_migrations()

    # Detectar modelo
    model = detect_model_from_env()

    # 1. Auto-descubrimiento de sistemas de memoria (v0.3.7-alpha)
    # Ejecuta persistent_storage_discover.py para detectar SQLite, Wiki, MD Memory, Sessions MD
    # y mostrar el estado al agente
    try:
        discover_script = SCRIPT_DIR / "persistent_storage_discover.py"
        if discover_script.exists():
            discover_result = subprocess.run(
                [sys.executable, str(discover_script), "--integration"],
                capture_output=True,
                text=True,
                timeout=10,
                cwd=REPO_ROOT,
            )
            if discover_result.returncode == 0 and discover_result.stdout.strip():
                storage_status = discover_result.stdout.strip()
                print(c(f"[STORAGE] Sistemas de memoria descubiertos:", Colors.CYAN))
                # Parse JSON and display nicely
                try:
                    import json
                    status_data = json.loads(storage_status)
                    systems = []
                    if status_data.get("sqlite_available"):
                        systems.append("SQLite")
                    if status_data.get("wiki_available"):
                        systems.append("Wiki")
                    if status_data.get("md_memory_available"):
                        systems.append("MD Memory")
                    if status_data.get("sessions_md_available"):
                        systems.append("Sessions MD")
                    if systems:
                        print(c(f"  [OK] Disponible: {', '.join(systems)}", Colors.GREEN))
                    else:
                        print(c(f"  [i] Sin sistemas persistentes (primera ejecucion)", Colors.DIM))
                    if not status_data.get("all_available"):
                        missing = []
                        if not status_data.get("sqlite_available"): missing.append("SQLite")
                        if not status_data.get("wiki_available"): missing.append("Wiki")
                        if not status_data.get("md_memory_available"): missing.append("MD Memory")
                        if not status_data.get("sessions_md_available"): missing.append("Sessions MD")
                        print(c(f"  [i] Sistemas pendientes: {', '.join(missing)}", Colors.DIM))
                except json.JSONDecodeError:
                    print(c(f"  [OK] Descubrimiento completado", Colors.DIM))
    except Exception:
        pass  # No bloquear inicio si falla discovery

    # 2. Inicializar Multi-CLI Coordinator (PRIMERO)
    coord = init_multi_cli_coordinator(model)

    # 2. Validar agente (quick check)
    agent = check_agent()
    if agent and agent != "FreakingJSON-PA":
        show_agent_warning(agent)

    # === PARALLEL CHECKS + CONTEXT LOADING (v2.2.0) ===
    # ContextLoader loads Tier 0-1 immediately; Tier 2-4 deferred
    # Warm start cache is checked inside run_parallel_checks
    if not args.no_parallel:
        parallel_data = run_parallel_checks(coord, skip_context=args.skip_context)
    else:
        parallel_data = None  # Legacy mode

    # 3. Mostrar template de inicio (con datos pre-cargados)
    print_session_start(parallel_data)

    # 4. Verificar integridad de archivos vitales (ya ejecutado en parallel)
    # 4.5. Sincronizar estado de workspaces (ya ejecutado en parallel)
    # Si legacy mode, ejecutar ahora
    if args.no_parallel:
        show_vitals_status()
        sync_workspaces_status()

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

    # === MEMORY BRIDGE INIT (v0.4.0) - CRITICAL ===
    # Initialize SessionBridge and start SQLite session
    global _session_bridge
    if MEMORY_BRIDGE_AVAILABLE:
        try:
            _session_bridge = SessionBridge()
            session_id = _session_bridge.start_session(
                user_input=None,
                metadata={
                    "agent": "FreakingJSON-PA",
                    "multi_cli": len(coord.get_other_active_instances()) if coord else 0,
                    "warm_start": parallel_data.get("_warm_start", False) if parallel_data else False
                }
            )
            print(c(f"[MEMORY] Session started: {session_id}", Colors.CYAN))
            
            # Log todos heredados to memory
            if parallel_data and parallel_data.get("todos"):
                for todo in parallel_data.get("todos", [])[:10]:  # First 10
                    _session_bridge.add_message("system", f"TODO_HEREDADO: {todo}")
            
            # Show memory stats
            stats = _session_bridge.get_stats()
            print(c(f"[MEMORY] Sessions in SQLite: {stats.get('total_sessions', 0)}", Colors.DIM))
            
            # v0.3.7-alpha: Show user memory facts
            user_context = _session_bridge.get_user_context_summary()
            if user_context:
                safe_print(c(user_context, Colors.DIM))
            
            user_stats = _session_bridge.get_user_memory_stats()
            if user_stats.get("available"):
                print(c(f"[MEMORY] User facts: {user_stats.get('active_facts', 0)} active", Colors.DIM))
            
        except Exception as e:
            print(c(f"[MEMORY] Bridge init failed: {e}", Colors.YELLOW))
            _session_bridge = None

    # 6. Indexar sesión actual en KB (si no está indexada)
    try:
        import importlib.util

        indexer_path = SCRIPT_DIR / "session_indexer.py"
        spec = importlib.util.spec_from_file_location("session_indexer", indexer_path)
        if spec and spec.loader:
            session_indexer = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(session_indexer)
            SessionIndexer = session_indexer.SessionIndexer
            indexer = SessionIndexer()
            existing_ids = {s["id"] for s in indexer.index.get("sessions", [])}
            if today not in existing_ids:
                indexer.index_all_sessions()  # Indexar todas (incluye hoy)
    except Exception:
        pass  # No bloquear inicio si falla indexación

    # 7. Registrar cierre automático via atexit
    atexit.register(session_shutdown)

    # Calcular tiempo
    elapsed = (datetime.now() - start_time).total_seconds()
    
    # Context loading status
    if args.skip_context:
        print(c("  [CONTEXT] Skipped (--skip-context)", Colors.DIM))
    elif parallel_data and parallel_data.get("_warm_start"):
        print(c(f"  [OK] Sesión iniciada en {elapsed:.1f}s (warm start)", Colors.GREEN))
    else:
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

    # === OPTIONAL: Framework Enforcement Check ===
    if not args.skip_validation:
        try:
            from framework_guardian import FrameworkGuardian

            guardian = FrameworkGuardian()
            results = guardian.run_validation(timing="session-start")
            if any(not r.passed for r in results):
                safe_print(
                    c(
                        "[ENFORCEMENT] Some checks failed. Run: python framework_guardian.py --timing session-start",
                        Colors.YELLOW,
                    )
                )
        except ImportError:
            pass  # Guardian not available, continue

    return 0


if __name__ == "__main__":
    sys.exit(main())
