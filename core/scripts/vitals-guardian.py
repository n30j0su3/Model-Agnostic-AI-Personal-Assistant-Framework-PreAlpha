#!/usr/bin/env python3
"""
Vitals Guardian - Sistema de Protección de Datos Críticos
============================================================

Protege archivos vitales del framework contra pérdida accidental.
Este script es parte del sistema de protección de datos del framework
FreakingJSON y DEBE ejecutarse en modo base y dev.

Uso:
    python core/scripts/vitals-guardian.py check          # Verificar integridad
    python core/scripts/vitals-guardian.py snapshot       # Crear snapshot manual
    python core/scripts/vitals-guardian.py snapshot --reason "antes_de_cambio"
    python core/scripts/vitals-guardian.py restore        # Restaurar desde backup
    python core/scripts/vitals-guardian.py list           # Listar backups disponibles
    python core/scripts/vitals-guardian.py sync           # Sincronizar con repo externo

Configuración:
    El archivo vitals.config.json permite personalizar rutas protegidas
    y el repositorio externo para backups remotos.
"""

import argparse
import hashlib
import json
import logging
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Set

# =============================================================================
# CONFIGURACIÓN POR DEFECTO
# =============================================================================

REPO_ROOT = Path(__file__).resolve().parents[2]
CONTEXT_DIR = REPO_ROOT / "core" / ".context"
VITALS_DIR = CONTEXT_DIR / "vitals"
BACKUP_DIR = VITALS_DIR / "backups"
MANIFEST_PATH = VITALS_DIR / "vitals.manifest.json"
CONFIG_PATH = VITALS_DIR / "vitals.config.json"
LOG_PATH = VITALS_DIR / "vitals.log"

# Archivos y directorios vitales por defecto
DEFAULT_VITALS = [
    # Configuración
    "opencode.jsonc",
    # Contexto central
    "core/.context/MASTER.md",
    "core/.context/navigation.md",
    "core/.context/claude.md",
    "core/.context/gemini.md",
    "core/.context/opencode.md",
    "core/.context/profile.md",
    # Backlog y conocimiento
    "core/.context/codebase/backlog.md",
    "core/.context/codebase/recordatorios.md",
    "core/.context/codebase/ideas.md",
    "core/.context/codebase/workflow-metodologia.md",
    "core/.context/codebase/INITIALIZATION_STATUS.md",
    # Dev To-do (prealpha-dev)
    "core/.context/dev-todo/",
    # Sesiones
    "core/.context/sessions/",
    # Backups existentes
    "core/.context/backups/",
    # Workspaces
    "workspaces/",
    # Configuración
    "config/",
    # Agentes personalizados
    "core/agents/",
    # Skills personalizadas
    "core/skills/custom/",
    # Histórico OBSOLETE
    "**/OBSOLETE*/",
    "**/*_OBSOLETE*/",
    "**/*_OBSOLETE.*",
]

DEFAULT_REMOTE_REPO = (
    "https://github.com/n30j0su3/Model-Agnostic-AI-Personal-Assistant-Framework-dev.git"
)

# =============================================================================
# CONFIGURACIÓN DE LOGGING
# =============================================================================


def setup_logging():
    """Configura el sistema de logging."""
    VITALS_DIR.mkdir(parents=True, exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(LOG_PATH, encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )
    return logging.getLogger(__name__)


logger = setup_logging()

# =============================================================================
# CLASE PRINCIPAL
# =============================================================================


class VitalsGuardian:
    """
    Guardian de archivos vitales del framework.

    Responsabilidades:
    - Mantener registro (manifest) de archivos vitales con hashes
    - Crear snapshots de respaldo automáticos
    - Detectar anomalías (archivos faltantes, modificados, corruptos)
    - Restaurar archivos desde backups
    - Sincronizar backups con repositorio externo
    """

    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path or CONFIG_PATH
        self.config = self._load_config()
        self.vitals = self._expand_vitals_list(
            self.config.get("vitals", DEFAULT_VITALS)
        )
        self.remote_repo = self.config.get("remote_repo", DEFAULT_REMOTE_REPO)
        self.backup_retention_days = self.config.get("backup_retention_days", 30)
        self.max_backups = self.config.get("max_backups", 50)

        # Asegurar directorios existen
        VITALS_DIR.mkdir(parents=True, exist_ok=True)
        BACKUP_DIR.mkdir(parents=True, exist_ok=True)

    def _load_config(self) -> dict:
        """Carga configuración desde archivo o crea default."""
        if self.config_path.exists():
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Error cargando config: {e}. Usando default.")

        # Crear config default
        default_config = {
            "vitals": DEFAULT_VITALS,
            "remote_repo": DEFAULT_REMOTE_REPO,
            "backup_retention_days": 30,
            "max_backups": 50,
            "auto_backup_on_destructive": True,
            "check_integrity_on_startup": True,
            "sync_to_remote": False,  # Requiere configuración manual
        }
        self._save_config(default_config)
        return default_config

    def _save_config(self, config: dict):
        """Guarda configuración a archivo."""
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)

    def _expand_vitals_list(self, vitals: List[str]) -> List[Path]:
        """Expande patrones glob en lista de rutas concretas."""
        expanded = []
        for pattern in vitals:
            if "*" in pattern:
                # Es un patrón glob
                matches = list(REPO_ROOT.glob(pattern))
                expanded.extend(matches)
            else:
                # Ruta específica
                expanded.append(REPO_ROOT / pattern)

        # Filtrar solo existentes y eliminar duplicados
        return list(set(p for p in expanded if p.exists()))

    def _compute_hash(self, file_path: Path) -> str:
        """Calcula SHA-256 de un archivo."""
        sha256 = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(8192), b""):
                    sha256.update(chunk)
            return sha256.hexdigest()
        except Exception as e:
            logger.error(f"Error calculando hash de {file_path}: {e}")
            return "ERROR"

    def _get_file_info(self, file_path: Path) -> dict:
        """Obtiene información de un archivo."""
        stat = file_path.stat()
        return {
            "path": str(file_path.relative_to(REPO_ROOT)),
            "hash": self._compute_hash(file_path),
            "size": stat.st_size,
            "mtime": stat.st_mtime,
            "is_dir": file_path.is_dir(),
        }

    def create_manifest(self) -> dict:
        """Crea un nuevo manifest con el estado actual de archivos vitales."""
        logger.info("Creando manifest de archivos vitales...")

        manifest = {
            "created_at": datetime.now().isoformat(),
            "version": "1.0",
            "total_files": 0,
            "total_dirs": 0,
            "files": {},
        }

        for vital_path in self.vitals:
            if vital_path.is_dir():
                manifest["total_dirs"] += 1
                # Procesar recursivamente
                for file_path in vital_path.rglob("*"):
                    if file_path.is_file():
                        rel_path = str(file_path.relative_to(REPO_ROOT))
                        manifest["files"][rel_path] = self._get_file_info(file_path)
                        manifest["total_files"] += 1
            else:
                if vital_path.is_file():
                    rel_path = str(vital_path.relative_to(REPO_ROOT))
                    manifest["files"][rel_path] = self._get_file_info(vital_path)
                    manifest["total_files"] += 1

        logger.info(
            f"Manifest creado: {manifest['total_files']} archivos, {manifest['total_dirs']} directorios"
        )
        return manifest

    def save_manifest(self, manifest: dict):
        """Guarda el manifest a disco."""
        with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)
        logger.info(f"Manifest guardado en {MANIFEST_PATH}")

    def load_manifest(self) -> Optional[dict]:
        """Carga el manifest desde disco."""
        if not MANIFEST_PATH.exists():
            logger.warning("No existe manifest previo. Creando nuevo...")
            return None

        try:
            with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error cargando manifest: {e}")
            return None

    def check_integrity(self) -> Tuple[bool, List[dict]]:
        """
        Verifica integridad de archivos vitales.

        Returns:
            (bool: todo_ok, List[dict]: lista de issues)
        """
        logger.info("Verificando integridad de archivos vitales...")

        current_manifest = self.create_manifest()
        saved_manifest = self.load_manifest()

        if saved_manifest is None:
            logger.warning(
                "No hay manifest previo para comparar. Guardando manifest actual."
            )
            self.save_manifest(current_manifest)
            return True, []

        issues = []
        saved_files = saved_manifest.get("files", {})
        current_files = current_manifest.get("files", {})

        # Detectar archivos faltantes
        for rel_path in saved_files:
            if rel_path not in current_files:
                issues.append(
                    {
                        "type": "missing",
                        "path": rel_path,
                        "severity": "critical",
                        "message": f"Archivo vital faltante: {rel_path}",
                    }
                )

        # Detectar archivos nuevos
        for rel_path in current_files:
            if rel_path not in saved_files:
                issues.append(
                    {
                        "type": "new",
                        "path": rel_path,
                        "severity": "info",
                        "message": f"Nuevo archivo vital detectado: {rel_path}",
                    }
                )

        # Detectar archivos modificados
        for rel_path in current_files:
            if rel_path in saved_files:
                current_hash = current_files[rel_path].get("hash")
                saved_hash = saved_files[rel_path].get("hash")
                if current_hash != saved_hash:
                    issues.append(
                        {
                            "type": "modified",
                            "path": rel_path,
                            "severity": "warning",
                            "message": f"Archivo modificado: {rel_path}",
                        }
                    )

        # Actualizar manifest con estado actual
        self.save_manifest(current_manifest)

        all_ok = len([i for i in issues if i["severity"] == "critical"]) == 0

        if all_ok:
            logger.info(
                "[OK] Integridad verificada: No hay archivos criticos faltantes"
            )
        else:
            critical_count = len([i for i in issues if i["severity"] == "critical"])
            logger.warning(
                f"[!] Detectados {critical_count} archivos criticos faltantes"
            )

        return all_ok, issues

    def create_snapshot(self, reason: str = "manual") -> Path:
        """
        Crea un snapshot de archivos vitales.

        Args:
            reason: Razón del snapshot (ej: "manual", "predestructive", "scheduled")

        Returns:
            Path al directorio del snapshot
        """
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        snapshot_name = f"{timestamp}_{reason}"
        snapshot_dir = BACKUP_DIR / snapshot_name

        logger.info(f"Creando snapshot: {snapshot_name}")
        snapshot_dir.mkdir(parents=True, exist_ok=True)

        files_backed = 0
        dirs_backed = 0
        errors = []

        for vital_path in self.vitals:
            try:
                rel_path = vital_path.relative_to(REPO_ROOT)
                dest_path = snapshot_dir / rel_path

                if vital_path.is_dir():
                    if vital_path.exists():
                        shutil.copytree(vital_path, dest_path, dirs_exist_ok=True)
                        dirs_backed += 1
                else:
                    if vital_path.exists():
                        dest_path.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(vital_path, dest_path)
                        files_backed += 1
            except Exception as e:
                error_msg = f"Error copiando {vital_path}: {e}"
                logger.error(error_msg)
                errors.append(error_msg)

        # Guardar metadata del snapshot
        metadata = {
            "created_at": timestamp,
            "reason": reason,
            "files_backed": files_backed,
            "dirs_backed": dirs_backed,
            "errors": errors,
        }

        with open(snapshot_dir / "snapshot.json", "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)

        logger.info(
            f"[OK] Snapshot creado: {files_backed} archivos, {dirs_backed} dirs en {snapshot_dir}"
        )

        # Limpiar backups antiguos
        self._cleanup_old_backups()

        return snapshot_dir

    def _cleanup_old_backups(self):
        """Elimina backups antiguos según política de retención."""
        if not BACKUP_DIR.exists():
            return

        backups = sorted(
            BACKUP_DIR.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True
        )

        # Mantener solo max_backups
        if len(backups) > self.max_backups:
            for old_backup in backups[self.max_backups :]:
                try:
                    if old_backup.is_dir():
                        shutil.rmtree(old_backup)
                    else:
                        old_backup.unlink()
                    logger.info(f"Backup antiguo eliminado: {old_backup.name}")
                except Exception as e:
                    logger.error(f"Error eliminando backup antiguo {old_backup}: {e}")

    def list_backups(self) -> List[dict]:
        """Lista todos los backups disponibles."""
        if not BACKUP_DIR.exists():
            return []

        backups = []
        for backup_dir in BACKUP_DIR.iterdir():
            if backup_dir.is_dir():
                metadata_path = backup_dir / "snapshot.json"
                metadata = {}
                if metadata_path.exists():
                    try:
                        with open(metadata_path, "r", encoding="utf-8") as f:
                            metadata = json.load(f)
                    except:
                        pass

                stat = backup_dir.stat()
                backups.append(
                    {
                        "name": backup_dir.name,
                        "path": str(backup_dir),
                        "created_at": metadata.get(
                            "created_at",
                            datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        ),
                        "reason": metadata.get("reason", "unknown"),
                        "files_backed": metadata.get("files_backed", 0),
                        "size_mb": sum(
                            f.stat().st_size
                            for f in backup_dir.rglob("*")
                            if f.is_file()
                        )
                        / (1024 * 1024),
                    }
                )

        return sorted(backups, key=lambda x: x["created_at"], reverse=True)

    def restore_from_backup(
        self, backup_name: str, files_to_restore: Optional[List[str]] = None
    ):
        """
        Restaura archivos desde un backup.

        Args:
            backup_name: Nombre del backup (ej: "2026-02-19_10-30-15_manual")
            files_to_restore: Lista específica de archivos a restaurar, o None para todo
        """
        backup_dir = BACKUP_DIR / backup_name

        if not backup_dir.exists():
            logger.error(f"Backup no encontrado: {backup_name}")
            return False

        logger.info(f"Restaurando desde backup: {backup_name}")

        # Crear backup de seguridad antes de restaurar (por si acaso)
        safety_backup = self.create_snapshot(reason="prerestore_safety")
        logger.info(f"Backup de seguridad creado: {safety_backup.name}")

        restored = 0
        errors = []

        # Si no se especifican archivos, restaurar todo
        if files_to_restore is None:
            for item in backup_dir.iterdir():
                if item.name == "snapshot.json":
                    continue

                dest_path = REPO_ROOT / item.name
                try:
                    if item.is_dir():
                        if dest_path.exists():
                            shutil.rmtree(dest_path)
                        shutil.copytree(item, dest_path)
                    else:
                        shutil.copy2(item, dest_path)
                    restored += 1
                except Exception as e:
                    errors.append(f"Error restaurando {item}: {e}")
        else:
            # Restaurar archivos específicos
            for rel_path in files_to_restore:
                src_path = backup_dir / rel_path
                dest_path = REPO_ROOT / rel_path

                if not src_path.exists():
                    errors.append(f"Archivo no existe en backup: {rel_path}")
                    continue

                try:
                    dest_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src_path, dest_path)
                    restored += 1
                except Exception as e:
                    errors.append(f"Error restaurando {rel_path}: {e}")

        # Actualizar manifest después de restaurar
        self.save_manifest(self.create_manifest())

        if errors:
            logger.warning(f"Restauración completada con {len(errors)} errores:")
            for err in errors:
                logger.warning(f"  - {err}")
        else:
            logger.info(
                f"[OK] Restauracion completada: {restored} elementos restaurados"
            )

        return len(errors) == 0

    def sync_to_remote(self) -> bool:
        """
        Sincroniza backups con repositorio externo.

        NOTA: Requiere configuración manual de credenciales Git.
        """
        logger.info(f"Sincronizando con repositorio remoto: {self.remote_repo}")

        # Verificar que git está disponible
        if not shutil.which("git"):
            logger.error("Git no está disponible. No se puede sincronizar con remoto.")
            return False

        # Crear directorio temporal para clonar
        import tempfile

        with tempfile.TemporaryDirectory() as tmp_dir:
            remote_dir = Path(tmp_dir) / "remote_backup"

            try:
                # Clonar repo remoto
                result = subprocess.run(
                    ["git", "clone", "--depth", "1", self.remote_repo, str(remote_dir)],
                    capture_output=True,
                    text=True,
                )

                if result.returncode != 0:
                    logger.error(f"Error clonando repo remoto: {result.stderr}")
                    return False

                # Copiar backups locales al repo remoto
                vitals_remote_dir = remote_dir / "vitals"
                vitals_remote_dir.mkdir(exist_ok=True)

                # Copiar manifest y últimos 10 backups
                backups = self.list_backups()[:10]

                for backup in backups:
                    src = Path(backup["path"])
                    dst = vitals_remote_dir / backup["name"]
                    if src.exists():
                        shutil.copytree(src, dst, dirs_exist_ok=True)

                # Copiar manifest
                if MANIFEST_PATH.exists():
                    shutil.copy2(
                        MANIFEST_PATH, vitals_remote_dir / "vitals.manifest.json"
                    )

                # Commit y push
                subprocess.run(
                    ["git", "config", "user.email", "vitals@freakingjson.local"],
                    cwd=remote_dir,
                )
                subprocess.run(
                    ["git", "config", "user.name", "Vitals Guardian"], cwd=remote_dir
                )
                subprocess.run(["git", "add", "."], cwd=remote_dir)

                commit_result = subprocess.run(
                    [
                        "git",
                        "commit",
                        "-m",
                        f"Vitals sync: {datetime.now().isoformat()}",
                    ],
                    cwd=remote_dir,
                    capture_output=True,
                )

                if commit_result.returncode == 0:
                    push_result = subprocess.run(
                        ["git", "push"], cwd=remote_dir, capture_output=True, text=True
                    )

                    if push_result.returncode == 0:
                        logger.info("[OK] Sincronizacion con remoto completada")
                        return True
                    else:
                        logger.error(f"Error en push: {push_result.stderr}")
                        return False
                else:
                    logger.info("No hay cambios para sincronizar")
                    return True

            except Exception as e:
                logger.error(f"Error sincronizando con remoto: {e}")
                return False


# =============================================================================
# FUNCIONES DE INTERFAZ DE USUARIO
# =============================================================================


def cmd_check(args):
    """Comando: verificar integridad."""
    guardian = VitalsGuardian()
    all_ok, issues = guardian.check_integrity()

    print(f"\n{'=' * 60}")
    print("RESULTADO DE VERIFICACIÓN DE INTEGRIDAD")
    print("=" * 60)

    if not issues:
        print("\n[OK] Todos los archivos vitales estan intactos")
        return 0

    critical = [i for i in issues if i["severity"] == "critical"]
    warnings = [i for i in issues if i["severity"] == "warning"]
    info = [i for i in issues if i["severity"] == "info"]

    if critical:
        print(f"\n[!] ARCHIVOS CRITICOS FALTANTES ({len(critical)}):")
        for issue in critical:
            print(f"   [X] {issue['path']}")

    if warnings:
        print(f"\n[~] Archivos modificados ({len(warnings)}):")
        for issue in warnings:
            print(f"   [~] {issue['path']}")

    if info:
        print(f"\n[+] Nuevos archivos ({len(info)}):")
        for issue in info:
            print(f"   [+] {issue['path']}")

    if critical and input("\n¿Deseas restaurar desde backup? [s/N]: ").lower() in (
        "s",
        "si",
        "y",
        "yes",
    ):
        cmd_restore(args)

    return 1 if critical else 0


def cmd_snapshot(args):
    """Comando: crear snapshot."""
    guardian = VitalsGuardian()
    reason = args.reason if hasattr(args, "reason") and args.reason else "manual"
    snapshot_path = guardian.create_snapshot(reason)
    print(f"\n[OK] Snapshot creado: {snapshot_path.name}")
    return 0


def cmd_list(args):
    """Comando: listar backups."""
    guardian = VitalsGuardian()
    backups = guardian.list_backups()

    print(f"\n{'=' * 60}")
    print("BACKUPS DISPONIBLES")
    print("=" * 60)

    if not backups:
        print("\nNo hay backups disponibles")
        return 0

    print(f"\n{'Nombre':<40} {'Razón':<15} {'Archivos':<10} {'Tamaño (MB)':<12}")
    print("-" * 80)

    for backup in backups:
        name = backup["name"][:38]
        reason = backup["reason"][:13]
        files = backup["files_backed"]
        size = f"{backup['size_mb']:.2f}"
        print(f"{name:<40} {reason:<15} {files:<10} {size:<12}")

    print(f"\nTotal: {len(backups)} backups")
    return 0


def cmd_restore(args):
    """Comando: restaurar desde backup."""
    guardian = VitalsGuardian()
    backups = guardian.list_backups()

    if not backups:
        print("\nNo hay backups disponibles para restaurar")
        return 1

    print(f"\n{'=' * 60}")
    print("RESTAURAR DESDE BACKUP")
    print("=" * 60)
    print("\nBackups disponibles:")

    for i, backup in enumerate(backups[:10], 1):
        print(f"  {i}. {backup['name']} ({backup['reason']})")

    try:
        choice = input("\nSelecciona el número del backup (o 'cancelar'): ").strip()
        if choice.lower() in ("cancelar", "cancel", "c", "n", "no"):
            print("Operación cancelada")
            return 0

        idx = int(choice) - 1
        if idx < 0 or idx >= len(backups):
            print("Selección inválida")
            return 1

        selected_backup = backups[idx]
        print(f"\nSeleccionado: {selected_backup['name']}")

        if input(
            "¿Confirmar restauración? Los archivos actuales serán reemplazados. [s/N]: "
        ).lower() not in ("s", "si", "y", "yes"):
            print("Operación cancelada")
            return 0

        guardian.restore_from_backup(selected_backup["name"])
        return 0

    except ValueError:
        print("Entrada inválida")
        return 1


def cmd_sync(args):
    """Comando: sincronizar con remoto."""
    print("\nSincronizando con repositorio externo...")
    print("NOTA: Esto requiere credenciales Git configuradas.")

    guardian = VitalsGuardian()
    success = guardian.sync_to_remote()

    if success:
        print("\n[OK] Sincronizacion completada")
        return 0
    else:
        print("\n[ERROR] Error en sincronizacion")
        print("Verifica que tienes acceso al repositorio y credenciales configuradas.")
        return 1


# =============================================================================
# MAIN
# =============================================================================


def main():
    parser = argparse.ArgumentParser(
        description="Vitals Guardian - Protección de datos críticos del framework",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
    python vitals-guardian.py check                    # Verificar integridad
    python vitals-guardian.py snapshot                 # Crear snapshot
    python vitals-guardian.py snapshot --reason antes_cambio
    python vitals-guardian.py list                     # Listar backups
    python vitals-guardian.py restore                  # Restaurar desde backup
    python vitals-guardian.py sync                     # Sincronizar con remoto
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Comandos disponibles")

    # check
    check_parser = subparsers.add_parser(
        "check", help="Verificar integridad de archivos vitales"
    )

    # snapshot
    snapshot_parser = subparsers.add_parser(
        "snapshot", help="Crear snapshot de archivos vitales"
    )
    snapshot_parser.add_argument(
        "--reason", help="Razón del snapshot (ej: manual, predestructive)"
    )

    # list
    list_parser = subparsers.add_parser("list", help="Listar backups disponibles")

    # restore
    restore_parser = subparsers.add_parser(
        "restore", help="Restaurar archivos desde backup"
    )

    # sync
    sync_parser = subparsers.add_parser(
        "sync", help="Sincronizar backups con repositorio remoto"
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 0

    commands = {
        "check": cmd_check,
        "snapshot": cmd_snapshot,
        "list": cmd_list,
        "restore": cmd_restore,
        "sync": cmd_sync,
    }

    return commands[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
