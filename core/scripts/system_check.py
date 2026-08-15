#!/usr/bin/env python3
"""
PA Framework — System Health Check
====================================
Verifica el estado de todos los componentes críticos del framework.
Se ejecuta automáticamente al iniciar sesión o bajo demanda.

Uso:
    python core/scripts/system_check.py
    python core/scripts/system_check.py --fix        # Intenta reparar automáticamente
    python core/scripts/system_check.py --json        # Salida JSON
    python core/scripts/system_check.py --quick       # Solo checks críticos

Creator: FreakingJSON (instagram.com/freakingjson, freakingjson.com)
Version: 1.0.0
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
from concurrent.futures import ThreadPoolExecutor, as_completed
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

# --- PATHS ---
SCRIPT_DIR = Path(__file__).resolve().parent
CORE_DIR = SCRIPT_DIR.parent
REPO_ROOT = CORE_DIR.parent
CONTEXT_DIR = CORE_DIR / ".context"
KB_DIR = CONTEXT_DIR / "knowledge"
CONFIG_DIR = REPO_ROOT / "config"
DATA_DIR = REPO_ROOT / "data"

# --- COLORS ---
class Colors:
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    CYAN = "\033[96m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    END = "\033[0m"

def c(text, color):
    return f"{color}{text}{Colors.END}"

def print_ok(msg):
    print(f"  {c('[OK]', Colors.GREEN)} {msg}")

def print_warn(msg):
    print(f"  {c('[!]', Colors.YELLOW)} {msg}")

def print_error(msg):
    print(f"  {c('[X]', Colors.RED)} {msg}")

def print_info(msg):
    print(f"  {c('[i]', Colors.CYAN)} {msg}")

# --- CHECK REGISTRY ---
checks = []
results = []

def register(name, description, critical=True):
    def decorator(func):
        checks.append({
            "name": name,
            "description": description,
            "critical": critical,
            "func": func,
        })
        return func
    return decorator

# ===========================================================================
# CHECKS
# ===========================================================================

@register("python_version", "Python 3.11+")
def check_python():
    if sys.version_info >= (3, 11):
        return True, f"Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    return False, f"Python {sys.version_info.major}.{sys.version_info.minor} < 3.11"

@register("core_structure", "Estructura del framework")
def check_core_structure():
    required = [
        CONTEXT_DIR,
        CORE_DIR / "agents",
        CORE_DIR / "skills" / "core",
        SCRIPT_DIR,
        CONFIG_DIR,
        REPO_ROOT / "workspaces",
    ]
    missing = [d for d in required if not d.exists()]
    if not missing:
        return True, f"{len(required)} directorios OK"
    return False, f"Faltan: {', '.join(str(m) for m in missing)}"

@register("version", "Archivo VERSION")
def check_version():
    vf = REPO_ROOT / "VERSION"
    if not vf.exists():
        return False, "VERSION no existe"
    version = vf.read_text(encoding="utf-8").strip()
    return True, f"Framework v{version}"

@register("profile", "Perfil de instalacion")
def check_profile():
    pf = CONTEXT_DIR / "profile.md"
    if pf.exists():
        return True, "profile.md presente"
    return False, "profile.md no encontrado"

@register("master_context", "MASTER.md")
def check_master():
    mf = CONTEXT_DIR / "MASTER.md"
    if mf.exists():
        return True, "MASTER.md presente"
    return False, "MASTER.md no encontrado"

@register("navigation", "navigation.md")
def check_navigation():
    nf = CONTEXT_DIR / "navigation.md"
    if nf.exists():
        return True, "navigation.md presente"
    return False, "navigation.md no encontrado"

@register("quick_start", "quick-start.md")
def check_quickstart():
    qf = CONTEXT_DIR / "quick-start.md"
    if qf.exists():
        return True, "quick-start.md presente"
    return False, "quick-start.md no encontrado"

@register("python_scripts", "Scripts base en core/scripts")
def check_scripts():
    essential = [
        "pa.py", "install.py", "update.py", "session_start.py",
        "session_end.py", "migrate.py", "kb_init.py",
        "system_check.py", "version_updater.py",
        "persistent_storage_discover.py",
    ]
    missing = [s for s in essential if not (SCRIPT_DIR / s).exists()]
    if not missing:
        return True, f"{len(essential)} scripts OK"
    return False, f"Faltan: {', '.join(missing)}"

@register("sqlite", "SQLite (sessions.db)")
def check_sqlite():
    db = DATA_DIR / "sessions.db"
    if db.exists():
        size_kb = db.stat().st_size // 1024
        return True, f"OK ({size_kb} KB)"
    # No es crítico si no existe (se crea al usar el framework)
    return "warn", "No creado aun (se crea automaticamente)"

@register("sessions_md", "Sesiones MD")
def check_sessions_md():
    sd = CONTEXT_DIR / "sessions"
    if sd.exists():
        files = list(sd.glob("*.md"))
        return True, f"{len(files)} archivo(s)"
    return False, "Directorio sessions/ no existe"

@register("memory_md", "MD Memory")
def check_memory_md():
    md = CONTEXT_DIR / "memory"
    if md.exists():
        files = list(md.glob("**/*.md"))
        return True, f"{len(files)} archivo(s)"
    return False, "Directorio memory/ no existe"

@register("knowledge_base", "Knowledge Base")
def check_kb():
    kb_readme = KB_DIR / "README.md"
    sessions_index = KB_DIR / "sessions-index.json"
    if kb_readme.exists() and sessions_index.exists():
        return True, "KB inicializada"
    return "warn", "KB incompleta (ejecutar kb_init.py)"

@register("wiki", "Wiki (knowledge/wiki)")
def check_wiki():
    wk = KB_DIR / "wiki"
    has_files = False
    file_count = 0
    if wk.exists():
        md_files = list(wk.glob("**/*.md"))
        file_count = len(md_files)
        has_files = file_count > 0
    if has_files:
        return True, f"{file_count} archivo(s)"
    return "warn", "Wiki vacia o sin archivos .md"

@register("migrations", "Migraciones pendientes")
def check_migrations():
    migrate_script = SCRIPT_DIR / "migrate.py"
    if not migrate_script.exists():
        return "warn", "migrate.py no encontrado (opcional)"
    try:
        result = subprocess.run(
            [sys.executable, str(migrate_script), "--check"],
            capture_output=True, text=True, timeout=10, cwd=REPO_ROOT,
        )
        if result.returncode == 0:
            return True, "Al dia"
        return "warn", "Migraciones pendientes (ejecutar --apply)"
    except Exception as e:
        return "warn", f"No se pudo verificar: {e}"

@register("update_protected", "update-protected-paths.txt")
def check_update_protected():
    upf = CONFIG_DIR / "update-protected-paths.txt"
    if upf.exists():
        lines = [l.strip() for l in upf.read_text().splitlines() if l.strip() and not l.startswith("#")]
        return True, f"{len(lines)} paths protegidos"
    return "warn", "No encontrado (opcional)"

@register("opencode_config", "opencode.jsonc")
def check_opencode_config():
    oc = REPO_ROOT / "opencode.jsonc"
    if oc.exists():
        size_kb = oc.stat().st_size // 1024
        return True, f"OK ({size_kb} KB)"
    return "warn", "No encontrado (opcional)"

@register("opencode_dir", ".opencode/ directorio")
def check_opencode_dir():
    od = REPO_ROOT / ".opencode"
    if od.exists() and (od / "config.json").exists():
        return True, "Configurado"
    return "warn", "No configurado (opcional)"

@register("dashboard", "Dashboard HTML")
def check_dashboard():
    dh = REPO_ROOT / "dashboard.html"
    dj = REPO_ROOT / "dashboard-data.js"
    if dh.exists() and dj.exists():
        return True, f"dashboard.html + data.js OK"
    return "warn", "Dashboard no disponible"

@register("config_files", "Archivos de configuracion")
def check_config_files():
    configs = {
        "branding.txt": CONFIG_DIR / "branding.txt",
        "framework.yaml": CONFIG_DIR / "framework.yaml",
        "i18n.json": CONFIG_DIR / "i18n.json",
    }
    present = []
    missing = []
    for name, path in configs.items():
        if path.exists():
            present.append(name)
        else:
            missing.append(name)
    if not missing:
        return True, f"{len(present)} archivos OK"
    return "warn", f"Faltan: {', '.join(missing)}"

@register("pa_bat", "pa.bat (Windows)")
def check_pa_bat():
    if (REPO_ROOT / "pa.bat").exists():
        return True, "Disponible"
    return "warn", "No encontrado"

@register("pa_sh", "pa.sh (Linux/Mac)")
def check_pa_sh():
    if (REPO_ROOT / "pa.sh").exists():
        return True, "Disponible"
    return "warn", "No encontrado"

@register("agents_config", "Agentes del framework")
def check_agents():
    agents_dirs = [
        CORE_DIR / "agents" / "pa-assistant.md",
        CORE_DIR / "agents" / "AGENTS.md",
    ]
    missing = [str(a) for a in agents_dirs if not a.exists()]
    if not missing:
        return True, "Agentes OK"
    return "warn", f"Faltan: {', '.join(missing)}"

@register("skills", "Skills instaladas")
def check_skills():
    skills_dir = CORE_DIR / "skills" / "core"
    if skills_dir.exists():
        skill_count = len([d for d in skills_dir.iterdir() if d.is_dir()])
        return True, f"{skill_count} skills disponibles"
    return "warn", "Directorio skills/ no encontrado"

# ===========================================================================
# MAIN
# ===========================================================================

def run_all_checks(quick=False):
    """Run all registered checks in parallel (ThreadPool)."""
    start = time.time()
    results_data = []

    # Filter: quick mode solo critical checks
    active_checks = [c for c in checks if not quick or c["critical"]]

    with ThreadPoolExecutor(max_workers=8) as executor:
        future_map = {
            executor.submit(c["func"]): c for c in active_checks
        }
        for future in as_completed(future_map, timeout=30):
            check = future_map[future]
            try:
                result = future.result()
                if isinstance(result, tuple) and len(result) == 2:
                    status, detail = result
                else:
                    status, detail = result, ""
                results_data.append({
                    "name": check["name"],
                    "description": check["description"],
                    "status": status,
                    "detail": detail,
                    "critical": check["critical"],
                })
            except Exception as e:
                results_data.append({
                    "name": check["name"],
                    "description": check["description"],
                    "status": False,
                    "detail": f"Error: {e}",
                    "critical": check["critical"],
                })

    elapsed = time.time() - start
    return results_data, elapsed


def print_report(results_data, elapsed):
    """Print human-readable health report."""
    total = len(results_data)
    ok_count = sum(1 for r in results_data if r["status"] is True)
    warn_count = sum(1 for r in results_data if r["status"] == "warn")
    error_count = sum(1 for r in results_data if r["status"] is False)
    critical_errors = sum(1 for r in results_data if r["status"] is False and r["critical"])

    # Header
    version = "?"
    vf = REPO_ROOT / "VERSION"
    if vf.exists():
        version = vf.read_text(encoding="utf-8").strip()

    print()
    print("=" * 58)
    print(f"  PA Framework v{version} — System Health Check")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 58)
    print()

    # Results by category
    for r in results_data:
        if r["status"] is True:
            print_ok(f"{r['description']}: {r['detail']}")
        elif r["status"] == "warn":
            print_warn(f"{r['description']}: {r['detail']}")
        else:
            print_error(f"{r['description']}: {r['detail']}")

    # Summary
    print()
    print("-" * 58)
    print(f"  Resumen: {ok_count} OK | {warn_count} advertencias | {error_count} errores")
    if critical_errors > 0:
        print(f"  {c(f'[!] {critical_errors} error(es) critico(s) requieren atencion', Colors.RED)}")
    else:
        print(f"  {c('[OK] Sin errores criticos', Colors.GREEN)}")
    print(f"  Tiempo: {elapsed:.2f}s")
    print("-" * 58)
    print()

    return critical_errors == 0 and error_count == 0


def auto_fix():
    """Intenta reparar problemas detectables automaticamente."""
    print(c("\n  [FIX] Intentando reparaciones automaticas...\n", Colors.CYAN))

    fixed = 0
    failed = 0

    # 0. v0.3.9-alpha: crear MASTER.md y profile.md desde templates si faltan
    template_fixes = [
        (CONTEXT_DIR / "MASTER.template.md", CONTEXT_DIR / "MASTER.md", "MASTER.md (desde template)"),
        (CONTEXT_DIR / "profile.template.md", CONTEXT_DIR / "profile.md", "profile.md (desde template)"),
    ]
    for tpl, target, label in template_fixes:
        if not target.exists():
            if tpl.exists():
                try:
                    target.write_text(tpl.read_text(encoding="utf-8"), encoding="utf-8")
                    print_ok(f"Creado: {label}")
                    fixed += 1
                except Exception as e:
                    print_error(f"No se pudo crear {label}: {e}")
                    failed += 1
            else:
                try:
                    target.write_text(
                        "# Perfil de instalación\n\n"
                        "(Personaliza este archivo con tus datos — no se sube al repo público.)\n",
                        encoding="utf-8",
                    )
                    print_ok(f"Creado: {label} (mínimo)")
                    fixed += 1
                except Exception as e:
                    print_error(f"No se pudo crear {label}: {e}")
                    failed += 1

    # 0.5 v0.3.9-alpha: seed del backlog (backlog_manager depende de él)
    backlog = CONTEXT_DIR / "codebase" / "backlog.md"
    seed = CONTEXT_DIR / "codebase" / "backlog.seed.md"
    if not backlog.exists() and seed.exists():
        try:
            backlog.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(seed, backlog)
            print(f"  [OK] Creado: backlog.md (desde seed)")
            fixed += 1
        except Exception as e:
            print(f"  [!] No se pudo crear backlog.md: {e}")
            failed += 1

    # 1. Crear directorios faltantes del framework
    dirs_to_create = [
        CONTEXT_DIR / "sessions",
        CONTEXT_DIR / "memory",
        CONTEXT_DIR / "memory" / "summaries",
        CONTEXT_DIR / "memory" / "profile",
        CONTEXT_DIR / "knowledge" / "wiki",
        CONTEXT_DIR / "codebase",
        KB_DIR / "users" / "default",
        CORE_DIR / "agents" / "subagents",
        CORE_DIR / "skills" / "core",
        REPO_ROOT / "workspaces",
        REPO_ROOT / "config",
        REPO_ROOT / "docs",
        DATA_DIR,
    ]
    for d in dirs_to_create:
        try:
            d.mkdir(parents=True, exist_ok=True)
            print_ok(f"Directorio creado: {d.relative_to(REPO_ROOT)}")
            fixed += 1
        except Exception as e:
            print_error(f"No se pudo crear {d}: {e}")
            failed += 1

    # 2. Ejecutar kb_init.py si existe
    kb_init = SCRIPT_DIR / "kb_init.py"
    if kb_init.exists():
        try:
            subprocess.run(
                [sys.executable, str(kb_init), "--force"],
                capture_output=True, timeout=30, cwd=REPO_ROOT,
            )
            print_ok("kb_init.py ejecutado correctamente")
            fixed += 1
        except Exception as e:
            print_error(f"kb_init.py fallo: {e}")
            failed += 1

    # 3. Ejecutar migrate.py --apply si hay pendientes
    migrate = SCRIPT_DIR / "migrate.py"
    if migrate.exists():
        try:
            result = subprocess.run(
                [sys.executable, str(migrate), "--check"],
                capture_output=True, text=True, timeout=10, cwd=REPO_ROOT,
            )
            if result.returncode != 0:
                result2 = subprocess.run(
                    [sys.executable, str(migrate), "--apply"],
                    capture_output=True, timeout=60, cwd=REPO_ROOT,
                )
                if result2.returncode == 0:
                    print_ok("Migraciones aplicadas correctamente")
                    fixed += 1
                else:
                    print_error(f"Migraciones fallaron: {result2.stderr.decode()}")
                    failed += 1
            else:
                print_ok("Migraciones al dia (sin pendientes)")
        except Exception as e:
            print_error(f"Error en migraciones: {e}")
            failed += 1

    print()
    if failed == 0:
        print(c(f"  [FIX] {fixed} reparaciones exitosas, 0 fallos", Colors.GREEN))
    else:
        print(c(f"  [FIX] {fixed} exitosas, {failed} fallos", Colors.RED))
    print()


def main():
    parser = argparse.ArgumentParser(
        description="PA Framework — System Health Check",
    )
    parser.add_argument("--fix", action="store_true", help="Intentar reparar automaticamente")
    parser.add_argument("--quiet-first-run", action="store_true",
                        help="Modo silencioso para auto-heal de primer arranque (session_start)")
    parser.add_argument("--json", action="store_true", help="Salida JSON")
    parser.add_argument("--quick", action="store_true", help="Solo checks criticos")
    args = parser.parse_args()

    if args.fix:
        # quiet-first-run: solo imprimir lo creado (llamado por session_start)
        if args.quiet_first_run:
            import io
            import contextlib
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                auto_fix()
            created = [l for l in buf.getvalue().splitlines() if "Creado" in l or "creado" in l]
            for l in created:
                print(l)
        else:
            auto_fix()
        return 0

    results_data, elapsed = run_all_checks(quick=args.quick)

    if args.json:
        output = {
            "timestamp": datetime.now().isoformat(),
            "version": (REPO_ROOT / "VERSION").read_text(encoding="utf-8").strip() if (REPO_ROOT / "VERSION").exists() else "unknown",
            "elapsed_seconds": round(elapsed, 2),
            "checks": results_data,
            "summary": {
                "ok": sum(1 for r in results_data if r["status"] is True),
                "warnings": sum(1 for r in results_data if r["status"] == "warn"),
                "errors": sum(1 for r in results_data if r["status"] is False),
                "critical_errors": sum(1 for r in results_data if r["status"] is False and r["critical"]),
            },
        }
        print(json.dumps(output, indent=2, ensure_ascii=False))
    else:
        all_ok = print_report(results_data, elapsed)
        return 0 if all_ok else 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
