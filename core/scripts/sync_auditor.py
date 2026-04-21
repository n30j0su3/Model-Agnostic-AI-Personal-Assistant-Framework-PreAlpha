#!/usr/bin/env python3
"""
Sync Auditor - PA Framework
============================

Verifica que archivos excluidos NO existan en el repositorio remoto.
Ayuda a detectar problemas antes de hacer push.

Uso:
    python core/scripts/sync-auditor.py              # Verifica remote por defecto
    python core/scripts/sync-auditor.py --local      # Verifica directorio local
    python core/scripts/sync-auditor.py --check-remote  # Verifica remoto
    python core/scripts/sync-auditor.py --fix        # Fija problemas encontrados
"""

import os
import sys
import subprocess
from pathlib import Path

# Archivos/directorios que NO deben estar en PROD
EXCLUDED_PATTERNS = {
    # Config obsoleta
    "config/knowledge_base.json",
    "config/mcp.json",
    "config/quotas.json",
    # Logs
    "logs/",
    # Datos de usuario/interacciones
    "core/.context/knowledge/users/",
    "core/.context/knowledge/interactions/",
    "core/.context/knowledge/errors/",
    # Sesiones reales (solo template)
    "core/.context/sessions/2026-",
    "core/.context/sessions/2025-",
}


def get_remote_files(remote="origin/main"):
    """Obtiene lista de archivos en el remote."""
    try:
        result = subprocess.run(
            ["git", "ls-tree", "-r", "--name-only", remote],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip().split("\n")
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] No se pudo obtener archivos del remote: {e}")
        return []


def get_local_files(base_dir="."):
    """Obtiene lista de archivos locales."""
    files = []
    base = Path(base_dir)
    for root, dirs, filenames in os.walk(base):
        for f in filenames:
            rel_path = Path(root).relative_to(base)
            files.append(str(rel_path / f).replace("\\", "/"))
    return files


def check_pattern(file_path, pattern):
    """Verifica si un archivo coincide con un patrón de exclusión."""
    pattern = pattern.rstrip("/")
    if pattern.endswith("*"):
        # Wildcard
        prefix = pattern[:-1]
        return file_path.startswith(prefix)
    elif "/" in pattern:
        # Directorio o path exacto
        return file_path.startswith(pattern) or file_path == pattern
    else:
        # Nombre de archivo
        return file_path.endswith("/" + pattern) or file_path == pattern


def verify_exclusions(files, patterns):
    """Verifica archivos excluidos."""
    found_excluded = []
    for f in files:
        for pattern in patterns:
            if check_pattern(f, pattern):
                found_excluded.append((f, pattern))
                break
    return found_excluded


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Audit sync exclusions")
    parser.add_argument(
        "--local", action="store_true", help="Verificar directorio local"
    )
    parser.add_argument("--check-remote", action="store_true", help="Verificar remote")
    parser.add_argument("--remote", default="origin/main", help="Remote a verificar")
    parser.add_argument(
        "--fix", action="store_true", help="Eliminar archivos encontrados"
    )
    parser.add_argument("--base-dir", default=".", help="Directorio base")

    args = parser.parse_args()

    print("=" * 70)
    print("SYNC AUDITOR - Verificación de Exclusiones PROD")
    print("=" * 70)

    if args.local or (not args.check_remote):
        print("\n[LOCAL] Verificando directorio local...")
        files = get_local_files(args.base_dir)
        found = verify_exclusions(files, EXCLUDED_PATTERNS)

        if found:
            print(f"\n[!] ENCONTRADOS {len(found)} ARCHIVOS EXCLUIDOS EN LOCAL:")
            for f, p in found:
                print(f"   - {f} (patron: {p})")

            if args.fix:
                print("\n[FIX] Eliminando archivos...")
                base = Path(args.base_dir)
                for f, p in found:
                    file_path = base / f
                    if file_path.exists():
                        if file_path.is_dir():
                            import shutil

                            shutil.rmtree(file_path)
                        else:
                            file_path.unlink()
                        print(f"   [ELIMINADO] {f}")
                print("\n[OK] Archivos eliminados. Ejecuta git add -A && commit")
        else:
            print("\n[OK] No se encontraron archivos excluidos en local")

    if args.check_remote:
        print(f"\n[REMOTE] Verificando {args.remote}...")
        try:
            files = get_remote_files(args.remote)
            found = verify_exclusions(files, EXCLUDED_PATTERNS)

            if found:
                print(f"\n[!] ENCONTRADOS {len(found)} ARCHIVOS EXCLUIDOS EN REMOTO:")
                for f, p in found:
                    print(f"   - {f} (patron: {p})")
                print("\n[ACCION REQUERIDA]")
                print("   1. Ejecuta sync-prealpha.py para actualizar local")
                print("   2. Elimina archivos problemáticos manualmente")
                print(
                    "   3. Commit y push: git add -A && git commit -m 'fix: cleanup' && git push"
                )
                return 1
            else:
                print("\n[OK] No se encontraron archivos excluidos en remoto")
        except Exception as e:
            print(f"\n[ERROR] {e}")
            return 1

    print("\n" + "=" * 70)
    print("AUDITORÍA COMPLETADA")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    sys.exit(main())
