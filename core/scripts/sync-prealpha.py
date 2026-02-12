#!/usr/bin/env python3
"""
Sincronizador PreAlpha - PA Framework
=====================================

Sincroniza cambios desde el proyecto base hacia los repos locales PreAlpha.
NO realiza operaciones git (push/commit) - eso es responsabilidad del usuario post-validación.

Uso:
    python sync-prealpha.py --mode=prod --dry-run    # Preview producción
    python sync-prealpha.py --mode=prod              # Aplicar a producción
    python sync-prealpha.py --mode=dev --dry-run     # Preview desarrollo
    python sync-prealpha.py --mode=dev               # Aplicar a desarrollo
    python sync-prealpha.py --mode=all --dry-run     # Preview ambos
    python sync-prealpha.py --mode=all               # Aplicar a ambos

Rutas (configurables al inicio del script):
    BASE_DIR: Proyecto base con todo el contexto de desarrollo
    PREALPHA_DIR: Repo local para producción (usa opencode.jsonc.CLEAN-PROD)
    PREALPHA_DEV_DIR: Repo local para desarrollo/test (mantiene opencode.jsonc original)
"""

import os
import sys
import shutil
import fnmatch
import argparse
from pathlib import Path
from datetime import datetime
from typing import List, Set, Tuple, Optional

# =============================================================================
# CONFIGURACIÓN DE RUTAS - AJUSTAR SEGÚN TU ENTORNO
# =============================================================================

# Rutas fijas (absolutas) para este entorno
DEFAULT_BASE_DIR = Path(
    r"C:\ACTUAL\IA\TEST\1_tempo_feb2026\test-pa-gemini_Opus\Model-Agnostic-AI-Personal-Assistant-Framework"
)
DEFAULT_PREALPHA_DIR = Path(
    r"C:\ACTUAL\IA\TEST\1_tempo_feb2026\test-pa-gemini_Opus\Pa_Pre_alpha_Opus_4_6"
)
DEFAULT_PREALPHA_DEV_DIR = Path(
    r"C:\ACTUAL\IA\TEST\1_tempo_feb2026\test-pa-gemini_Opus\Pa_Pre_alpha_Opus_4_6_DEV"
)

# Archivo de configuración limpio para producción
CLEAN_CONFIG_NAME = "opencode.jsonc.CLEAN-PROD"
CONFIG_NAME = "opencode.jsonc"

# =============================================================================
# ARCHIVOS Y DIRECTORIOS A IGNORAR (adicionales a .gitignore)
# =============================================================================

ADDITIONAL_IGNORE_PATTERNS = {
    ".git",  # Repositorios git
    ".gitignore",  # Se maneja especialmente
    "__pycache__",  # Python cache
    "*.pyc",  # Python compiled
    ".ruff_cache",  # Ruff cache
    ".last_sync",  # Archivo de control
    "TEMPO",  # Directorio temporal
    "*.tmp",  # Archivos temporales
    "node_modules",  # Dependencias npm
}

# Archivos/directorios a ignorar SOLO en producción (pero sí en dev)
PROD_ONLY_IGNORE_PATTERNS = {
    "docs/backlog.md",
    "docs/backlog.view.md",
}

# =============================================================================
# CLASES Y FUNCIONES
# =============================================================================


class SyncReporter:
    """Genera reportes de sincronización"""

    def __init__(self):
        self.added: List[str] = []
        self.modified: List[str] = []
        self.deleted: List[str] = []
        self.ignored: List[str] = []
        self.errors: List[str] = []
        self.config_replaced: bool = False

    def add(self, path: str):
        self.added.append(path)

    def modify(self, path: str):
        self.modified.append(path)

    def delete(self, path: str):
        self.deleted.append(path)

    def ignore(self, path: str):
        self.ignored.append(path)

    def error(self, msg: str):
        self.errors.append(msg)

    def set_config_replaced(self):
        self.config_replaced = True

    def print_summary(self, dry_run: bool = False):
        mode = "[DRY-RUN] " if dry_run else ""
        print(f"\n{'=' * 70}")
        print(f"{mode}RESUMEN DE SINCRONIZACIÓN")
        print(f"{'=' * 70}")

        if self.config_replaced:
            print(f"\n[CFG] CONFIGURACION:")
            print(f"   > opencode.jsonc -> REEMPLAZADO por version CLEAN-PROD")

        if self.added:
            print(f"\n[+] ARCHIVOS NUEVOS ({len(self.added)}):")
            for f in sorted(self.added)[:10]:  # Limitar a 10
                print(f"   + {f}")
            if len(self.added) > 10:
                print(f"   ... y {len(self.added) - 10} más")

        if self.modified:
            print(f"\n[~] ARCHIVOS MODIFICADOS ({len(self.modified)}):")
            for f in sorted(self.modified)[:10]:
                print(f"   ~ {f}")
            if len(self.modified) > 10:
                print(f"   ... y {len(self.modified) - 10} más")

        if self.deleted:
            print(f"\n[-] ARCHIVOS ELIMINADOS ({len(self.deleted)}):")
            for f in sorted(self.deleted)[:10]:
                print(f"   - {f}")
            if len(self.deleted) > 10:
                print(f"   ... y {len(self.deleted) - 10} más")

        if self.ignored:
            print(f"\n[o] IGNORADOS ({len(self.ignored)}):")
            for f in sorted(self.ignored)[:5]:
                print(f"   o {f}")
            if len(self.ignored) > 5:
                print(f"   ... y {len(self.ignored) - 5} más")

        if self.errors:
            print(f"\n[X] ERRORES ({len(self.errors)}):")
            for e in self.errors:
                print(f"   x {e}")

        total_changes = len(self.added) + len(self.modified) + len(self.deleted)
        print(f"\n{'=' * 70}")
        print(
            f"Total cambios: {total_changes} (A:{len(self.added)} M:{len(self.modified)} D:{len(self.deleted)})"
        )

        if dry_run:
            print(f"\n[i] Modo dry-run: NO se aplicaron cambios")
            print(f"   Ejecuta sin --dry-run para aplicar")
        else:
            print(f"\n[OK] Sincronización completada")
            print(f"\n[!] IMPORTANTE: Revisa los cambios locales antes de hacer push:")
            print(f"   cd <directorio-destino>")
            print(f"   git status")
            print(f"   git diff")
            print(f"   git add . && git commit -m 'sync: actualización desde base'")
            print(f"   git push origin <branch>")


def load_gitignore_patterns(gitignore_path: Path) -> Set[str]:
    """Carga patrones de .gitignore"""
    patterns = set()

    if not gitignore_path.exists():
        return patterns

    try:
        with open(gitignore_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                # Ignorar comentarios y líneas vacías
                if line and not line.startswith("#"):
                    patterns.add(line)
    except Exception as e:
        print(f"[!] Advertencia: No se pudo leer .gitignore: {e}")

    return patterns


def should_ignore(file_path: str, patterns: Set[str]) -> bool:
    """Verifica si un archivo debe ser ignorado según patrones"""
    # Verificar patrones adicionales
    for pattern in ADDITIONAL_IGNORE_PATTERNS:
        if pattern in file_path:
            return True
        if fnmatch.fnmatch(os.path.basename(file_path), pattern):
            return True

    # Verificar patrones de .gitignore
    for pattern in patterns:
        # Manejar patrones con slash (directorios específicos)
        if "/" in pattern:
            if pattern.rstrip("/") in file_path:
                return True
        else:
            # Patrones simples (wildcards)
            if fnmatch.fnmatch(os.path.basename(file_path), pattern):
                return True
            if fnmatch.fnmatch(file_path, pattern):
                return True

    return False


def calculate_hash(filepath: Path) -> str:
    """Calcula hash simple de archivo para detectar cambios"""
    import hashlib

    try:
        with open(filepath, "rb") as f:
            return hashlib.md5(f.read()).hexdigest()
    except:
        return ""


def sync_directory(
    src_dir: Path,
    dest_dir: Path,
    gitignore_patterns: Set[str],
    reporter: SyncReporter,
    dry_run: bool = False,
    use_clean_config: bool = False,
    is_prod_mode: bool = False,
) -> bool:
    """
    Sincroniza directorio fuente a destino

    Args:
        src_dir: Directorio origen (proyecto base)
        dest_dir: Directorio destino (prealpha)
        gitignore_patterns: Patrones a ignorar
        reporter: Objeto para reportar cambios
        dry_run: Si True, solo reporta sin aplicar
        use_clean_config: Si True, reemplaza opencode.jsonc con CLEAN-PROD
        is_prod_mode: Si True, aplica exclusiones específicas de producción

    Returns:
        True si hubo éxito, False si hubo errores
    """
    success = True

    # Crear directorio destino si no existe
    if not dest_dir.exists() and not dry_run:
        dest_dir.mkdir(parents=True, exist_ok=True)

    # Coleccionar archivos en destino para detectar eliminados
    dest_files_before = set()
    if dest_dir.exists():
        for root, dirs, files in os.walk(dest_dir):
            # Filtrar directorios ignorados
            dirs[:] = [
                d
                for d in dirs
                if not should_ignore(os.path.join(root, d), gitignore_patterns)
            ]

            for file in files:
                full_path = Path(root) / file
                rel_path = full_path.relative_to(dest_dir)
                dest_files_before.add(str(rel_path).replace("\\", "/"))

    # Procesar archivos fuente
    src_files = set()

    for root, dirs, files in os.walk(src_dir):
        rel_root = Path(root).relative_to(src_dir)

        # Filtrar directorios ignorados
        dirs[:] = [
            d for d in dirs if not should_ignore(str(rel_root / d), gitignore_patterns)
        ]

        for file in files:
            src_file = Path(root) / file
            rel_path = str(rel_root / file).replace("\\", "/")

            # Saltar .gitignore (se maneja especialmente)
            if file == ".gitignore":
                continue

            # Verificar si debe ignorarse
            if should_ignore(rel_path, gitignore_patterns):
                reporter.ignore(rel_path)
                continue

            # Verificar exclusiones específicas de producción
            if is_prod_mode and rel_path in PROD_ONLY_IGNORE_PATTERNS:
                reporter.ignore(rel_path)
                continue

            src_files.add(rel_path)

            # Determinar archivo destino
            dest_file = dest_dir / rel_path

            # Caso especial: opencode.jsonc
            if file == CONFIG_NAME and use_clean_config:
                clean_config = src_dir / CLEAN_CONFIG_NAME
                if clean_config.exists():
                    src_file = clean_config
                    if not dry_run:
                        reporter.set_config_replaced()
                else:
                    reporter.error(f"No se encontró {CLEAN_CONFIG_NAME}")
                    success = False
                    continue

            # Verificar si necesita copiarse
            needs_copy = False

            if not dest_file.exists():
                needs_copy = True
                reporter.add(rel_path)
            else:
                # Comparar hashes
                src_hash = calculate_hash(src_file)
                dest_hash = calculate_hash(dest_file)
                if src_hash != dest_hash:
                    needs_copy = True
                    reporter.modify(rel_path)

            # Copiar archivo
            if needs_copy and not dry_run:
                try:
                    dest_file.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src_file, dest_file)
                except Exception as e:
                    reporter.error(f"Error copiando {rel_path}: {e}")
                    success = False

    # Detectar archivos eliminados
    deleted = dest_files_before - src_files
    for del_path in deleted:
        # No eliminar archivos ignorados
        if not should_ignore(del_path, gitignore_patterns):
            full_del_path = dest_dir / del_path
            if full_del_path.exists():
                reporter.delete(del_path)
                if not dry_run:
                    try:
                        if full_del_path.is_file():
                            full_del_path.unlink()
                        else:
                            shutil.rmtree(full_del_path)
                    except Exception as e:
                        reporter.error(f"Error eliminando {del_path}: {e}")
                        success = False

    # Copiar .gitignore (siempre se actualiza)
    src_gitignore = src_dir / ".gitignore"
    dest_gitignore = dest_dir / ".gitignore"

    if src_gitignore.exists():
        if not dest_gitignore.exists() or calculate_hash(
            src_gitignore
        ) != calculate_hash(dest_gitignore):
            reporter.modify(".gitignore")
            if not dry_run:
                try:
                    shutil.copy2(src_gitignore, dest_gitignore)
                except Exception as e:
                    reporter.error(f"Error copiando .gitignore: {e}")
                    success = False

    return success


def validate_paths(base_dir: Path, prealpha_dir: Path, prealpha_dev_dir: Path) -> bool:
    """Valida que las rutas existan"""
    valid = True

    if not base_dir.exists():
        print(f"[X] ERROR: Directorio base no existe: {base_dir}")
        valid = False
    else:
        print(f"[OK] Base: {base_dir}")

    if not prealpha_dir.exists():
        print(f"[X] ERROR: Directorio PreAlpha no existe: {prealpha_dir}")
        valid = False
    else:
        print(f"[OK] PreAlpha (prod): {prealpha_dir}")

    if not prealpha_dev_dir.exists():
        print(f"[X] ERROR: Directorio PreAlpha DEV no existe: {prealpha_dev_dir}")
        valid = False
    else:
        print(f"[OK] PreAlpha (dev): {prealpha_dev_dir}")

    return valid


def main():
    parser = argparse.ArgumentParser(
        description="Sincroniza PreAlpha desde proyecto base",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  # Preview de cambios en producción
  python sync-prealpha.py --mode=prod --dry-run
  
  # Aplicar cambios a producción
  python sync-prealpha.py --mode=prod
  
  # Preview de cambios en desarrollo
  python sync-prealpha.py --mode=dev --dry-run
  
  # Aplicar cambios a ambos
  python sync-prealpha.py --mode=all
        """,
    )

    parser.add_argument(
        "--mode",
        choices=["prod", "dev", "all"],
        default="all",
        help="Modo de sincronización (default: all)",
    )

    parser.add_argument(
        "--dry-run", action="store_true", help="Solo muestra cambios sin aplicarlos"
    )

    parser.add_argument(
        "--base-dir",
        type=Path,
        default=DEFAULT_BASE_DIR,
        help=f"Directorio base (default: {DEFAULT_BASE_DIR})",
    )

    parser.add_argument(
        "--prealpha-dir",
        type=Path,
        default=DEFAULT_PREALPHA_DIR,
        help=f"Directorio PreAlpha producción (default: {DEFAULT_PREALPHA_DIR})",
    )

    parser.add_argument(
        "--prealpha-dev-dir",
        type=Path,
        default=DEFAULT_PREALPHA_DEV_DIR,
        help=f"Directorio PreAlpha desarrollo (default: {DEFAULT_PREALPHA_DEV_DIR})",
    )

    args = parser.parse_args()

    # Header
    print(f"{'=' * 70}")
    print(f"PA Framework - Sincronizador PreAlpha")
    print(f"{'=' * 70}")
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Modo: {args.mode}")
    print(f"Dry-run: {'Sí' if args.dry_run else 'No'}")
    print(f"{'=' * 70}\n")

    # Validar rutas
    if not validate_paths(args.base_dir, args.prealpha_dir, args.prealpha_dev_dir):
        sys.exit(1)

    # Cargar .gitignore del base
    gitignore_path = args.base_dir / ".gitignore"
    gitignore_patterns = load_gitignore_patterns(gitignore_path)
    print(f"\n[i] Patrones .gitignore cargados: {len(gitignore_patterns)}")

    # Sincronizar según modo
    all_success = True

    if args.mode in ["prod", "all"]:
        print(f"\n{'=' * 70}")
        print(f">>> SINCRONIZANDO: Producción (usa CLEAN-PROD)")
        print(f"{'=' * 70}")

        reporter = SyncReporter()
        success = sync_directory(
            args.base_dir,
            args.prealpha_dir,
            gitignore_patterns,
            reporter,
            dry_run=args.dry_run,
            use_clean_config=True,
            is_prod_mode=True,
        )

        reporter.print_summary(dry_run=args.dry_run)
        all_success = all_success and success

    if args.mode in ["dev", "all"]:
        print(f"\n{'=' * 70}")
        print(f">>> SINCRONIZANDO: Desarrollo (mantiene config original)")
        print(f"{'=' * 70}")

        reporter = SyncReporter()
        success = sync_directory(
            args.base_dir,
            args.prealpha_dev_dir,
            gitignore_patterns,
            reporter,
            dry_run=args.dry_run,
            use_clean_config=False,
            is_prod_mode=False,
        )

        reporter.print_summary(dry_run=args.dry_run)
        all_success = all_success and success

    # Resultado final
    print(f"\n{'=' * 70}")
    if all_success:
        print("[OK] PROCESO COMPLETADO")
        if args.dry_run:
            print("\n[i] Para aplicar cambios, ejecuta sin --dry-run")
        else:
            print("[X] PROCESO COMPLETADO CON ERRORES")
        print("Revisa los mensajes de error arriba")
        sys.exit(1)
    print(f"{'=' * 70}\n")


if __name__ == "__main__":
    main()
