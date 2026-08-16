#!/usr/bin/env python3
"""v0.4.0-beta: Desinstalador del PA Framework + dependencias opencode."""
import os, sys, shutil, subprocess, json
from pathlib import Path

def confirm(msg):
    print(f"\n{msg} [y/N]: ", end="", flush=True)
    try:
        resp = input().strip().lower()
    except EOFError:
        resp = ""
    return resp in ("y", "yes", "si", "sí")

def main():
    REPO_ROOT = Path(__file__).resolve().parent.parent
    print("=" * 60)
    print("PA Framework - Desinstalador v0.4.0-beta")
    print("=" * 60)
    
    # 1) Datos personales (opcional preservar)
    context_dir = REPO_ROOT / "core" / ".context"
    if context_dir.exists():
        print(f"\nSe encontraron datos en {context_dir}")
        print("  - MASTER.md: config global")
        print("  - sessions/: historial de sesiones")
        print("  - knowledge/: conocimiento extraído")
        if confirm("¿Eliminar datos personales? (NO = se preservan)"):
            shutil.rmtree(context_dir)
            print("✓ Datos eliminados")
        else:
            print("✓ Datos preservados")
    
    # 2) Cache
    cache_dir = REPO_ROOT / "core" / ".context" / ".cache"
    if cache_dir.exists():
        shutil.rmtree(cache_dir)
        print("✓ Cache eliminado")
    
    # 3) SQLite de sesiones
    db_path = REPO_ROOT / "data" / "sessions.db"
    if db_path.exists():
        if confirm("¿Eliminar SQLite de sesiones?"):
            db_path.unlink()
            print("✓ SQLite eliminado")
        else:
            print("✓ SQLite preservado")
    
    # 4) opencode (opcional, es global)
    oc_dirs = [
        Path.home() / ".opencode",
        Path.home() / ".nvm" / "versions" / "node" / "v24.14.1" / "lib" / "node_modules" / "opencode-ai"
    ]
    for oc in oc_dirs:
        if oc.exists() and confirm(f"¿Desinstalar opencode de {oc}? (esto afecta otros proyectos)"):
            shutil.rmtree(oc)
            print(f"✓ {oc} eliminado")
    
    # 5) Scripts del framework (opcional)
    if confirm("¿Eliminar scripts del framework? (deja solo el repo git)"):
        scripts = list((REPO_ROOT / "core" / "scripts").glob("*.py"))
        for s in scripts:
            if s.name not in ["__init__.py"]:
                s.unlink()
        print("✓ Scripts eliminados")
    
    print("\n" + "=" * 60)
    print("Desinstalación completada.")
    print("Para eliminar el repo completamente: `rm -rf {REPO_ROOT}`")
    print("=" * 60)
    return 0

if __name__ == "__main__":
    sys.exit(main())
