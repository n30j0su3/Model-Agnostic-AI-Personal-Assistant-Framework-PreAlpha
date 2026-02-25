#!/usr/bin/env python3
"""
Sincronizador PreAlpha - PA Framework (OPTIMIZADO)
==================================================

Sincroniza cambios desde el proyecto base hacia los repos locales PreAlpha.
Versión optimizada con protección _local/, validación pre-sync, y modo skill-only.

Uso:
    python sync-prealpha-optimized.py --mode=prod --dry-run    # Preview producción
    python sync-prealpha-optimized.py --mode=prod              # Aplicar a producción
    python sync-prealpha-optimized.py --mode=dev --dry-run     # Preview desarrollo
    python sync-prealpha-optimized.py --mode=dev               # Aplicar a desarrollo
    python sync-prealpha-optimized.py --mode=all --dry-run     # Preview ambos
    python sync-prealpha-optimized.py --mode=all               # Aplicar a ambos
    python sync-prealpha-optimized.py --mode=dev --skill=dashboard-pro  # Solo una skill

Rutas (configurables al inicio del script):
    BASE_DIR: Proyecto base con todo el contexto de desarrollo
    PREALPHA_DIR: Repo local para producción (usa opencode.jsonc.CLEAN-PROD)
    PREALPHA_DEV_DIR: Repo local para desarrollo/test (mantiene opencode.jsonc original)
"""

from __future__ import annotations

import os
import sys
import shutil
import fnmatch
import argparse
import time
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Set, Tuple, Optional, Dict, Callable
from dataclasses import dataclass, field
from enum import Enum

# =============================================================================
# CONFIGURACIÓN DE RUTAS - AJUSTAR SEGÚN TU ENTORNO
# =============================================================================

# Rutas fijas (absolutas) para este entorno
DEFAULT_BASE_DIR = Path(
    r"C:\ACTUAL\FreakingJSON-pa\Model-Agnostic-AI-Personal-Assistant-Framework"
)
DEFAULT_PREALPHA_DIR = Path(r"C:\ACTUAL\FreakingJSON-pa\Pa_Pre_alpha_Opus_4_6")
DEFAULT_PREALPHA_DEV_DIR = Path(r"C:\ACTUAL\FreakingJSON-pa\Pa_Pre_alpha_Opus_4_6_DEV")

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
# DIRECTORIOS PROTEGIDOS EN PreAlpha-DEV (nunca se sobrescriben)
# =============================================================================

# [OPTIMIZACIÓN 1] Directorios protegidos extendidos con _local/
PROTECTED_DIRS = {
    "core/.context/sessions",
    "core/.context/codebase",
    "core/.context/workspaces",  # NUEVO: workspaces locales
    "core/agents/subagents/_local",  # NUEVO: agentes locales de DEV
    "core/skills/_local",  # NUEVO: skills locales de DEV
    "workspaces",
}

# Recursos críticos que deben existir en DEV antes de sincronizar
CRITICAL_RESOURCES = [
    "core/.context/MASTER.md",
    "core/.context/navigation.md",
    "core/agents/pa-assistant.md",
]

# =============================================================================
# ENUMERACIONES Y DATACLASSES
# =============================================================================


class FileCategory(Enum):
    """Categorías de archivos para reporte"""

    SKILL = "skills"
    AGENT = "agentes"
    DOCS = "docs"
    CONFIG = "config"
    SCRIPT = "scripts"
    CONTEXT = "context"
    OTHER = "otros"


@dataclass
class FileOperation:
    """Representa una operación de archivo"""

    path: str
    category: FileCategory
    operation: str  # 'add', 'modify', 'delete'
    size_bytes: int = 0


@dataclass
class CopyResult:
    """Resultado de una operación de copia"""

    success: bool
    bytes_copied: int = 0
    error_message: str = ""
    time_elapsed: float = 0.0


# =============================================================================
# CLASES OPTIMIZADAS
# =============================================================================


class ProgressTracker:
    """Tracking de progreso con estimación de tiempo"""

    def __init__(self, total_items: int = 0):
        self.total_items = total_items
        self.processed_items = 0
        self.total_bytes = 0
        self.start_time = time.time()
        self.item_times: List[float] = []

    def update(self, bytes_processed: int = 0):
        """Actualiza el progreso"""
        current_time = time.time()
        if self.processed_items > 0:
            item_time: float = (
                current_time - self.start_time - float(sum(self.item_times))
            )
            self.item_times.append(item_time)
            # Mantener solo últimos 10 para promedio
            self.item_times = self.item_times[-10:]

        self.processed_items += 1
        self.total_bytes += bytes_processed

    def get_eta(self) -> Optional[str]:
        """Calcula tiempo estimado restante"""
        if self.total_items == 0 or len(self.item_times) == 0:
            return None

        avg_time = sum(self.item_times) / len(self.item_times)
        remaining = self.total_items - self.processed_items
        eta_seconds = avg_time * remaining

        if eta_seconds < 60:
            return f"{int(eta_seconds)}s"
        elif eta_seconds < 3600:
            return f"{int(eta_seconds / 60)}m {int(eta_seconds % 60)}s"
        else:
            return f"{int(eta_seconds / 3600)}h {int((eta_seconds % 3600) / 60)}m"

    def get_progress_percentage(self) -> float:
        """Porcentaje de progreso"""
        if self.total_items == 0:
            return 0.0
        return (self.processed_items / self.total_items) * 100

    def format_bytes(self) -> str:
        """Formatea bytes a unidades legibles"""
        bytes_val = self.total_bytes
        for unit in ["B", "KB", "MB", "GB"]:
            if bytes_val < 1024.0:
                return f"{bytes_val:.1f} {unit}"
            bytes_val /= 1024.0
        return f"{bytes_val:.1f} TB"


class FileCopyManager:
    """Gestiona copia de archivos con manejo de errores granular"""

    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.stats = {"successful": 0, "failed": 0, "total_bytes": 0, "errors": []}

    def copy_file(
        self, src: Path, dest: Path, preserve_metadata: bool = True
    ) -> CopyResult:
        """
        Copia un archivo con manejo de errores y preservación de metadatos.

        Args:
            src: Ruta origen
            dest: Ruta destino
            preserve_metadata: Si True, usa copy2 para preservar metadatos

        Returns:
            CopyResult con resultado de la operación
        """
        start_time = time.time()

        try:
            # Crear directorio destino si no existe
            dest.parent.mkdir(parents=True, exist_ok=True)

            # Obtener tamaño antes de copiar
            file_size = src.stat().st_size

            # Copiar con preservación de metadatos
            if preserve_metadata:
                shutil.copy2(src, dest)
            else:
                shutil.copy(src, dest)

            elapsed = time.time() - start_time

            if self.verbose:
                print(f"  [COPY] {src.name} ({file_size} bytes) en {elapsed:.2f}s")

            self.stats["successful"] += 1
            self.stats["total_bytes"] += file_size

            return CopyResult(
                success=True, bytes_copied=file_size, time_elapsed=elapsed
            )

        except PermissionError as e:
            error_msg = f"Sin permisos para copiar {src}: {e}"
            self.stats["failed"] += 1
            self.stats["errors"].append(error_msg)
            return CopyResult(success=False, error_message=error_msg)

        except FileNotFoundError as e:
            error_msg = f"Archivo no encontrado {src}: {e}"
            self.stats["failed"] += 1
            self.stats["errors"].append(error_msg)
            return CopyResult(success=False, error_message=error_msg)

        except shutil.Error as e:
            error_msg = f"Error de shutil copiando {src}: {e}"
            self.stats["failed"] += 1
            self.stats["errors"].append(error_msg)
            return CopyResult(success=False, error_message=error_msg)

        except Exception as e:
            error_msg = f"Error inesperado copiando {src}: {e}"
            self.stats["failed"] += 1
            self.stats["errors"].append(error_msg)
            return CopyResult(success=False, error_message=error_msg)

    def get_stats(self) -> Dict:
        """Retorna estadísticas de copia"""
        return self.stats.copy()


class ExtendedSyncReporter:
    """Genera reportes de sincronización con categorización"""

    def __init__(self):
        self.added: List[FileOperation] = []
        self.modified: List[FileOperation] = []
        self.deleted: List[FileOperation] = []
        self.ignored: List[str] = []
        self.errors: List[str] = []
        self.config_replaced: bool = False
        self.total_bytes_transferred: int = 0
        self.start_time: float = time.time()

    @staticmethod
    def get_file_category(file_path: str) -> FileCategory:
        """Categoriza un archivo según su ruta"""
        path_lower = file_path.lower()

        if "/skills/" in path_lower or "skills/" in path_lower:
            return FileCategory.SKILL
        elif "/agents/" in path_lower or "agents/" in path_lower:
            return FileCategory.AGENT
        elif (
            "/docs/" in path_lower or "docs/" in path_lower or file_path.endswith(".md")
        ):
            return FileCategory.DOCS
        elif "/scripts/" in path_lower or file_path.endswith(".py"):
            return FileCategory.SCRIPT
        elif "/.context/" in path_lower or "context" in path_lower:
            return FileCategory.CONTEXT
        elif any(
            file_path.endswith(ext)
            for ext in [".json", ".jsonc", ".yaml", ".yml", ".toml"]
        ):
            return FileCategory.CONFIG
        else:
            return FileCategory.OTHER

    def add(self, path: str, size_bytes: int = 0):
        category = self.get_file_category(path)
        self.added.append(FileOperation(path, category, "add", size_bytes))
        self.total_bytes_transferred += size_bytes

    def modify(self, path: str, size_bytes: int = 0):
        category = self.get_file_category(path)
        self.modified.append(FileOperation(path, category, "modify", size_bytes))
        self.total_bytes_transferred += size_bytes

    def delete(self, path: str):
        category = self.get_file_category(path)
        self.deleted.append(FileOperation(path, category, "delete"))

    def ignore(self, path: str):
        self.ignored.append(path)

    def error(self, msg: str):
        self.errors.append(msg)

    def set_config_replaced(self):
        self.config_replaced = True

    def format_bytes(self, bytes_val: float) -> str:
        """Formatea bytes a unidades legibles"""
        value = float(bytes_val)
        for unit in ["B", "KB", "MB", "GB"]:
            if value < 1024.0:
                return f"{value:.1f} {unit}"
            value /= 1024.0
        return f"{value:.1f} TB"

    def get_elapsed_time(self) -> str:
        """Retorna tiempo transcurrido formateado"""
        elapsed = time.time() - self.start_time
        if elapsed < 60:
            return f"{int(elapsed)}s"
        elif elapsed < 3600:
            return f"{int(elapsed / 60)}m {int(elapsed % 60)}s"
        else:
            return f"{int(elapsed / 3600)}h {int((elapsed % 3600) / 60)}m"

    def _print_categorized(self, operations: List[FileOperation], title: str):
        """Imprime operaciones categorizadas"""
        if not operations:
            return

        # Agrupar por categoría
        by_category: Dict[FileCategory, List[FileOperation]] = {}
        for op in operations:
            if op.category not in by_category:
                by_category[op.category] = []
            by_category[op.category].append(op)

        print(f"\n[{title}] Total: {len(operations)}")

        for category in FileCategory:
            if category in by_category:
                items = by_category[category]
                print(f"\n  [{category.value.upper()}] ({len(items)}):")
                for op in sorted(items, key=lambda x: x.path)[:5]:
                    size_str = (
                        f" ({self.format_bytes(op.size_bytes)})"
                        if op.size_bytes > 0
                        else ""
                    )
                    print(f"    {op.path}{size_str}")
                if len(items) > 5:
                    print(f"    ... y {len(items) - 5} más")

    def print_summary(self, dry_run: bool = False):
        mode = "[DRY-RUN] " if dry_run else ""
        print(f"\n{'=' * 70}")
        print(f"{mode}RESUMEN DE SINCRONIZACIÓN")
        print(f"{'=' * 70}")
        print(f"Tiempo transcurrido: {self.get_elapsed_time()}")

        if self.total_bytes_transferred > 0:
            print(
                f"Bytes transferidos: {self.format_bytes(self.total_bytes_transferred)}"
            )

        if self.config_replaced:
            print(f"\n[CFG] CONFIGURACION:")
            print(f"   > opencode.jsonc -> REEMPLAZADO por version CLEAN-PROD")

        # [OPTIMIZACIÓN 4] Mostrar cambios categorizados
        self._print_categorized(self.added, "+ ARCHIVOS NUEVOS")
        self._print_categorized(self.modified, "~ ARCHIVOS MODIFICADOS")
        self._print_categorized(self.deleted, "- ARCHIVOS ELIMINADOS")

        if self.ignored:
            print(f"\n[o] IGNORADOS ({len(self.ignored)}):")
            for f in sorted(self.ignored)[:5]:
                print(f"   o {f}")
            if len(self.ignored) > 5:
                print(f"   ... y {len(self.ignored) - 5} más")

        if self.errors:
            print(f"\n[X] ERRORES ({len(self.errors)}):")
            for e in self.errors[:10]:
                print(f"   x {e}")
            if len(self.errors) > 10:
                print(f"   ... y {len(self.errors) - 10} más")

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


# =============================================================================
# FUNCIONES DE UTILIDAD
# =============================================================================


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


# [OPTIMIZACIÓN 2] Validación de recursos críticos pre-sync
def validate_critical_resources(dest_dir: Path, reporter: ExtendedSyncReporter) -> bool:
    """
    Verifica que existan recursos críticos en el destino antes de sincronizar.
    Alerta si faltan recursos protegidos.

    Args:
        dest_dir: Directorio destino a validar
        reporter: Reporter para registrar advertencias

    Returns:
        True si todos los recursos críticos existen, False si falta alguno
    """
    print(f"\n[i] Validando recursos críticos en {dest_dir.name}...")

    all_exist = True
    missing_resources = []

    for resource in CRITICAL_RESOURCES:
        resource_path = dest_dir / resource
        if resource_path.exists():
            print(f"  [OK] {resource}")
        else:
            print(f"  [ALERTA] Falta recurso crítico: {resource}")
            missing_resources.append(resource)
            all_exist = False

    # Validar directorios protegidos
    for protected_dir in PROTECTED_DIRS:
        protected_path = dest_dir / protected_dir
        if protected_path.exists():
            print(f"  [OK] Directorio protegido: {protected_dir}")
        else:
            print(
                f"  [INFO] Directorio protegido no existe (se creará): {protected_dir}"
            )

    if missing_resources:
        reporter.error(f"Recursos críticos faltantes: {', '.join(missing_resources)}")
        print(f"\n[!] ADVERTENCIA: Faltan {len(missing_resources)} recursos críticos")
        print("    La sincronización continuará, pero verifica el destino.")
    else:
        print(f"\n[OK] Todos los recursos críticos verificados")

    return all_exist


def backup_protected_dirs(dest_dir: Path, protected: set) -> dict:
    """
    Hace backup de directorios protegidos antes del sync.
    Retorna dict con {nombre_dir: ruta_backup}
    """
    backups = {}
    for protected_dir in protected:
        src_path = dest_dir / protected_dir
        if src_path.exists():
            backup_path = dest_dir / f"{protected_dir}.backup"
            # Eliminar backup anterior si existe
            if backup_path.exists():
                if backup_path.is_dir():
                    shutil.rmtree(backup_path)
                else:
                    backup_path.unlink()
            # Mover directorio actual a backup
            shutil.move(str(src_path), str(backup_path))
            backups[protected_dir] = backup_path
    return backups


def restore_protected_dirs(
    dest_dir: Path, backups: dict, reporter: ExtendedSyncReporter
):
    """Restaura directorios protegidos después del sync."""
    for protected_dir, backup_path in backups.items():
        target_path = dest_dir / protected_dir
        # Eliminar versión sincronizada si existe
        if target_path.exists():
            if target_path.is_dir():
                shutil.rmtree(target_path)
            else:
                target_path.unlink()
        # Restaurar desde backup
        shutil.move(str(backup_path), str(target_path))
        reporter.ignore(f"[PROTEGIDO] {protected_dir}")


# [OPTIMIZACIÓN 5] Filtrado por skill específico
def should_include_for_skill(file_path: str, skill_name: str) -> bool:
    """
    Verifica si un archivo pertenece a una skill específica.

    Args:
        file_path: Ruta del archivo a verificar
        skill_name: Nombre de la skill a filtrar

    Returns:
        True si el archivo debe incluirse para la skill especificada
    """
    path_lower = file_path.lower()
    skill_lower = skill_name.lower()

    # Si es un archivo de la skill específica
    if f"/skills/{skill_lower}/" in path_lower:
        return True
    if path_lower.startswith(f"skills/{skill_lower}/"):
        return True

    # Si es un archivo relacionado con la skill (con el nombre en el path)
    if skill_lower in path_lower:
        return True

    # Archivos de configuración y core siempre se incluyen
    if file_path.endswith((".json", ".jsonc", ".md", ".txt")):
        if "core" in path_lower or "config" in path_lower:
            return True

    return False


def sync_directory(
    src_dir: Path,
    dest_dir: Path,
    gitignore_patterns: Set[str],
    reporter: ExtendedSyncReporter,
    dry_run: bool = False,
    use_clean_config: bool = False,
    is_prod_mode: bool = False,
    protect_dirs: bool = False,
    skill_filter: Optional[str] = None,
    verbose: bool = False,
) -> bool:
    """
    Sincroniza directorio fuente a destino (VERSIÓN OPTIMIZADA)

    Args:
        src_dir: Directorio origen (proyecto base)
        dest_dir: Directorio destino (prealpha)
        gitignore_patterns: Patrones a ignorar
        reporter: Objeto para reportar cambios
        dry_run: Si True, solo reporta sin aplicar
        use_clean_config: Si True, reemplaza opencode.jsonc con CLEAN-PROD
        is_prod_mode: Si True, aplica exclusiones específicas de producción
        protect_dirs: Si True, protege directorios personales
        skill_filter: Si se especifica, solo sincroniza archivos de esa skill
        verbose: Si True, muestra logging detallado

    Returns:
        True si hubo éxito, False si hubo errores
    """
    success = True
    protected_backups = {}

    # Inicializar gestor de copias
    copy_manager = FileCopyManager(verbose=verbose)
    progress = ProgressTracker()

    # [OPTIMIZACIÓN 2] Validar recursos críticos antes de sync en modo DEV
    if protect_dirs and not dry_run:
        validate_critical_resources(dest_dir, reporter)

    # Hacer backup de directorios protegidos antes de sync (solo en modo protegido y no dry-run)
    if protect_dirs and not dry_run:
        protected_backups = backup_protected_dirs(dest_dir, PROTECTED_DIRS)

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
                rel_path = str(full_path.relative_to(dest_dir)).replace("\\", "/")
                dest_files_before.add(rel_path)

    # Procesar archivos fuente
    src_files = set()

    # Contar total de archivos para progreso
    total_files = 0
    for root, dirs, files in os.walk(src_dir):
        for _ in files:
            total_files += 1

    progress.total_items = total_files

    print(f"\n[i] Procesando {total_files} archivos...")

    for root, dirs, files in os.walk(src_dir):
        rel_root = Path(root).relative_to(src_dir)

        # Filtrar directorios ignorados
        dirs[:] = [
            d for d in dirs if not should_ignore(str(rel_root / d), gitignore_patterns)
        ]

        for file in files:
            src_file = Path(root) / file
            rel_path = str(rel_root / file).replace("\\", "/")

            progress.update()

            # Mostrar progreso cada 100 archivos
            if progress.processed_items % 100 == 0:
                eta = progress.get_eta()
                eta_str = f" (ETA: {eta})" if eta else ""
                print(f"  Progreso: {progress.get_progress_percentage():.1f}%{eta_str}")

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

            # [OPTIMIZACIÓN 5] Filtrar por skill si se especificó
            if skill_filter and not should_include_for_skill(rel_path, skill_filter):
                if verbose:
                    print(
                        f"  [SKIP] {rel_path} (no pertenece a skill '{skill_filter}')"
                    )
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
            file_size = src_file.stat().st_size if src_file.exists() else 0

            if not dest_file.exists():
                needs_copy = True
                reporter.add(rel_path, file_size)
            else:
                # Comparar hashes
                src_hash = calculate_hash(src_file)
                dest_hash = calculate_hash(dest_file)
                if src_hash != dest_hash:
                    needs_copy = True
                    reporter.modify(rel_path, file_size)

            # [OPTIMIZACIÓN 3] Copiar archivo con manejo optimizado de errores
            if needs_copy and not dry_run:
                result = copy_manager.copy_file(
                    src_file, dest_file, preserve_metadata=True
                )

                if not result.success:
                    reporter.error(result.error_message)
                    success = False

    # Detectar archivos eliminados
    deleted = dest_files_before - src_files
    for del_path in deleted:
        # No eliminar archivos ignorados
        if not should_ignore(del_path, gitignore_patterns):
            # [OPTIMIZACIÓN 5] No eliminar si estamos en modo skill-only
            if skill_filter:
                continue

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
                result = copy_manager.copy_file(src_gitignore, dest_gitignore)
                if not result.success:
                    reporter.error(f"Error copiando .gitignore: {result.error_message}")
                    success = False

    # Restaurar directorios protegidos después del sync
    if protect_dirs and not dry_run and protected_backups:
        restore_protected_dirs(dest_dir, protected_backups, reporter)

    # [OPTIMIZACIÓN 3] Reportar estadísticas de copia
    copy_stats = copy_manager.get_stats()
    if copy_stats["successful"] > 0 or copy_stats["failed"] > 0:
        print(f"\n[i] Estadísticas de copia:")
        print(f"    Exitosas: {copy_stats['successful']}")
        print(f"    Fallidas: {copy_stats['failed']}")
        print(
            f"    Total transferido: {reporter.format_bytes(copy_stats['total_bytes'])}"
        )

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
        description="Sincroniza PreAlpha desde proyecto base (VERSIÓN OPTIMIZADA)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  # Preview de cambios en producción
  python sync-prealpha-optimized.py --mode=prod --dry-run
  
  # Aplicar cambios a producción
  python sync-prealpha-optimized.py --mode=prod
  
  # Preview de cambios en desarrollo
  python sync-prealpha-optimized.py --mode=dev --dry-run
  
  # Sincronizar solo una skill específica
  python sync-prealpha-optimized.py --mode=dev --skill=dashboard-pro
  
  # Aplicar cambios a ambos con verbose
  python sync-prealpha-optimized.py --mode=all --verbose
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

    # [OPTIMIZACIÓN 5] Nuevo argumento para modo skill-only
    parser.add_argument(
        "--skill",
        type=str,
        default=None,
        help="Sincronizar solo archivos relacionados con una skill específica (ej: dashboard-pro)",
    )

    # [OPTIMIZACIÓN 3] Nuevo argumento para verbose
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Muestra logging detallado de operaciones",
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
    print(f"PA Framework - Sincronizador PreAlpha (OPTIMIZADO)")
    print(f"{'=' * 70}")
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Modo: {args.mode}")
    print(f"Dry-run: {'Sí' if args.dry_run else 'No'}")
    if args.skill:
        print(f"Skill filter: {args.skill}")
    print(f"Verbose: {'Sí' if args.verbose else 'No'}")
    print(f"{'=' * 70}\n")

    # Validar rutas
    if not validate_paths(args.base_dir, args.prealpha_dir, args.prealpha_dev_dir):
        sys.exit(1)

    # Cargar .gitignore del base
    gitignore_path = args.base_dir / ".gitignore"
    gitignore_patterns = load_gitignore_patterns(gitignore_path)
    print(f"\n[i] Patrones .gitignore cargados: {len(gitignore_patterns)}")

    # Mostrar directorios protegidos
    print(f"[i] Directorios protegidos ({len(PROTECTED_DIRS)}):")
    for d in sorted(PROTECTED_DIRS):
        print(f"     - {d}")

    # Sincronizar según modo
    all_success = True

    if args.mode in ["prod", "all"]:
        print(f"\n{'=' * 70}")
        print(f">>> SINCRONIZANDO: Producción (usa CLEAN-PROD)")
        print(f"{'=' * 70}")

        reporter = ExtendedSyncReporter()
        success = sync_directory(
            args.base_dir,
            args.prealpha_dir,
            gitignore_patterns,
            reporter,
            dry_run=args.dry_run,
            use_clean_config=True,
            is_prod_mode=True,
            protect_dirs=False,  # PROD: sincronización limpia
            skill_filter=args.skill,
            verbose=args.verbose,
        )

        reporter.print_summary(dry_run=args.dry_run)
        all_success = all_success and success

    if args.mode in ["dev", "all"]:
        print(f"\n{'=' * 70}")
        print(
            f">>> SINCRONIZANDO: Desarrollo (mantiene config original + protege datos)"
        )
        print(f"{'=' * 70}")

        reporter = ExtendedSyncReporter()
        success = sync_directory(
            args.base_dir,
            args.prealpha_dev_dir,
            gitignore_patterns,
            reporter,
            dry_run=args.dry_run,
            use_clean_config=False,
            is_prod_mode=False,
            protect_dirs=True,  # DEV: protege directorios personales
            skill_filter=args.skill,
            verbose=args.verbose,
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
