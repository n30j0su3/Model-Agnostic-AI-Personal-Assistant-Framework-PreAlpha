#!/usr/bin/env python3
"""
Safe Executor - Ejecutor Seguro con Protección de Datos Vitales
================================================================

Wrapper que intercepta comandos potencialmente destructivos y protege
archivos vitales del framework. Parte del sistema Vitals Guardian.

Modo de operación: PERMISIVO con detección para volverse RESTRICTIVO ante la duda.

Uso directo:
    python safe-executor.py -- rm -rf workspaces/
    python safe-executor.py -- del /f /q archivo.txt
    python safe-executor.py -- python script_que_borra.py

Uso como módulo:
    from safe_executor import SafeExecutor
    executor = SafeExecutor()
    executor.execute("rm -rf workspaces/")

Protección automática:
    - Detecta operaciones destructivas
    - Crea backup automático antes de ejecutar
    - Solicita confirmación si afecta archivos vitales
    - Modo restrictivo automático ante situaciones de riesgo
"""

import argparse
import fnmatch
import logging
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

# Importar Vitals Guardian
sys.path.insert(0, str(Path(__file__).parent))
try:
    from vitals_guardian import VitalsGuardian
except ImportError:
    # Si no se puede importar, ejecutar como subprocess
    import subprocess
    import json

    class VitalsGuardian:
        """Stub minimal para cuando no se puede importar."""

        def __init__(self):
            self.vitals = self._load_vitals()

        def _load_vitals(self):
            # Cargar desde config
            config_path = (
                REPO_ROOT / "core" / ".context" / "vitals" / "vitals.config.json"
            )
            if config_path.exists():
                with open(config_path, "r", encoding="utf-8") as f:
                    config = json.load(f)
                    return [REPO_ROOT / v for v in config.get("vitals", [])]
            return []

        def create_snapshot(self, reason="manual"):
            # Crear snapshot via subprocess
            result = subprocess.run(
                [
                    sys.executable,
                    str(Path(__file__).parent / "vitals-guardian.py"),
                    "snapshot",
                    "--reason",
                    reason,
                ],
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                # Extraer nombre del backup de la salida
                for line in result.stdout.split("\n"):
                    if "Snapshot creado:" in line or "[OK] Snapshot creado:" in line:
                        parts = line.split(":")
                        if len(parts) > 1:
                            return Path(line.split(":")[-1].strip())
            return None

        def check_integrity(self):
            result = subprocess.run(
                [
                    sys.executable,
                    str(Path(__file__).parent / "vitals-guardian.py"),
                    "check",
                ],
                capture_output=True,
                text=True,
            )
            return result.returncode == 0, []

        def restore_from_backup(self, backup_name):
            result = subprocess.run(
                [
                    sys.executable,
                    str(Path(__file__).parent / "vitals-guardian.py"),
                    "restore",
                ],
                input=backup_name + "\n",
                capture_output=True,
                text=True,
            )
            return result.returncode == 0

# =============================================================================
# CONFIGURACIÓN
# =============================================================================

REPO_ROOT = Path(__file__).resolve().parents[2]
VITALS_DIR = REPO_ROOT / "core" / ".context" / "vitals"
LOG_PATH = VITALS_DIR / "safe-executor.log"

# Patrones de comandos destructivos
DESTRUCTIVE_PATTERNS = {
    # Unix/Linux/Mac
    "rm": [
        r"^rm\s+-[rf]*[rf]",  # rm -rf, rm -r, rm -f
        r"^rm\s+.*\*",  # rm con wildcards
        r"^rm\s+-rf\s+\.",  # rm -rf . (peligroso!)
    ],
    "rmdir": [
        r"^rmdir\s+-p",  # rmdir -p
        r"^rmdir\s+.*\*",  # rmdir con wildcards
    ],
    # Windows
    "del": [
        r"^del\s+/[fq]",  # del /f /q
        r"^del\s+.*\*",  # del con wildcards
    ],
    "rmdir_win": [
        r"^rmdir\s+/[sq]",  # rmdir /s /q
    ],
    "erase": [
        r"^erase\s+/[fq]",  # erase /f /q
    ],
    # PowerShell
    "powershell": [
        r"Remove-Item.*-Recurse",
        r"Remove-Item.*-Force",
        r"ri\s+.*-r",  # ri (alias) -Recurse
        r"del\s+.*-r",  # del -Recurse
    ],
    # Python/shutil
    "python_code": [
        r"shutil\.rmtree",
        r"os\.rmdir\s*\(",
        r"os\.remove\s*\(",
        r"os\.unlink\s*\(",
        r"Path\(.*\)\.rmdir\s*\(",
        r"Path\(.*\)\.unlink\s*\(",
    ],
    # Redirecciones destructivas
    "redirect": [
        r">\s*/dev/null",  # redirigir a /dev/null
        r">\s*[a-zA-Z]:",  # redirigir a archivo en Windows
    ],
}

# Umbrales para modo restrictivo
RISK_THRESHOLDS = {
    "vital_files_affected": 1,  # Si afecta 1+ archivos vitales
    "files_affected": 10,  # Si afecta 10+ archivos
    "directories_affected": 1,  # Si afecta 1+ directorios
    "wildcard_scope_large": 50,  # Si wildcard match > 50 archivos
    "recursive_delete": True,  # Si es borrado recursivo
}

# =============================================================================
# LOGGING
# =============================================================================


def setup_logging():
    """Configura logging para el safe executor."""
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


class SafeExecutor:
    """
    Ejecutor seguro que protege archivos vitales.

    Filosofía: Permisivo con detección, restrictivo ante la duda.
    """

    def __init__(self, auto_backup: bool = True, strict_mode: bool = False):
        self.guardian = VitalsGuardian()
        self.vitals = self.guardian.vitals
        self.auto_backup = auto_backup
        self.strict_mode = strict_mode
        self.execution_log: List[Dict] = []

    def analyze_command(self, command: str) -> Dict:
        """
        Analiza un comando para detectar operaciones destructivas.

        Returns:
            Dict con análisis de riesgo
        """
        result = {
            "command": command,
            "is_destructive": False,
            "risk_level": "low",  # low, medium, high, critical
            "patterns_matched": [],
            "affected_vitals": [],
            "affected_files": [],
            "affected_dirs": [],
            "estimated_files": 0,
            "requires_confirmation": False,
            "reasons": [],
        }

        # Verificar contra patrones destructivos
        for category, patterns in DESTRUCTIVE_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, command, re.IGNORECASE):
                    result["is_destructive"] = True
                    result["patterns_matched"].append(f"{category}:{pattern}")
                    result["reasons"].append(
                        f"Patrón destructivo detectado: {category}"
                    )

        if not result["is_destructive"]:
            return result

        # Analizar archivos/directorios afectados
        affected = self._extract_affected_paths(command)
        result["affected_files"] = affected["files"]
        result["affected_dirs"] = affected["dirs"]
        result["estimated_files"] = affected["estimated_count"]

        # Detectar archivos vitales afectados
        for vital in self.vitals:
            vital_str = str(vital)
            for path in affected["files"] + affected["dirs"]:
                if self._path_matches(path, vital_str):
                    result["affected_vitals"].append(
                        str(vital.relative_to(REPO_ROOT))
                        if vital.is_relative_to(REPO_ROOT)
                        else str(vital)
                    )

        # Calcular nivel de riesgo
        result["risk_level"] = self._calculate_risk_level(result)
        result["requires_confirmation"] = self._requires_confirmation(result)

        return result

    def _extract_affected_paths(self, command: str) -> Dict:
        """Extrae rutas de archivos/directorios afectados por el comando."""
        result = {"files": [], "dirs": [], "estimated_count": 0}

        # Tokenizar comando
        tokens = command.split()

        for i, token in enumerate(tokens):
            # Saltar flags y opciones
            if token.startswith("-") or token.startswith("/"):
                continue

            # Saltar comando mismo
            if i == 0:
                continue

            # Procesar como posible ruta
            path = Path(token)

            # Expandir wildcards si los hay
            if "*" in token or "?" in token:
                matches = list(REPO_ROOT.glob(token))
                result["estimated_count"] += len(matches)
                for match in matches:
                    if match.is_file():
                        result["files"].append(str(match))
                    elif match.is_dir():
                        result["dirs"].append(str(match))
            else:
                # Ruta específica
                full_path = REPO_ROOT / path if not path.is_absolute() else path
                if full_path.exists():
                    result["estimated_count"] += 1
                    if full_path.is_file():
                        result["files"].append(str(full_path))
                    elif full_path.is_dir():
                        result["dirs"].append(str(full_path))
                        # Estimar archivos dentro del directorio
                        try:
                            result["estimated_count"] += len(list(full_path.rglob("*")))
                        except:
                            pass

        return result

    def _path_matches(self, path1: str, path2: str) -> bool:
        """Verifica si dos rutas coinciden o una contiene a la otra."""
        p1 = Path(path1).resolve()
        p2 = Path(path2).resolve()

        # Coincidencia exacta
        if p1 == p2:
            return True

        # Una contiene a la otra
        try:
            p1.relative_to(p2)
            return True
        except ValueError:
            pass

        try:
            p2.relative_to(p1)
            return True
        except ValueError:
            pass

        return False

    def _calculate_risk_level(self, analysis: Dict) -> str:
        """Calcula el nivel de riesgo basado en el análisis."""
        score = 0

        # Archivos vitales afectados
        if analysis["affected_vitals"]:
            score += len(analysis["affected_vitals"]) * 10

        # Cantidad de archivos
        if analysis["estimated_files"] > RISK_THRESHOLDS["wildcard_scope_large"]:
            score += 5
        elif analysis["estimated_files"] > RISK_THRESHOLDS["files_affected"]:
            score += 3

        # Directorios afectados
        if len(analysis["affected_dirs"]) > RISK_THRESHOLDS["directories_affected"]:
            score += 4

        # Patrones peligrosos específicos
        for pattern in analysis["patterns_matched"]:
            if r"rm.*-rf.*\." in pattern or r"rmdir.*-r.*-f" in pattern:
                score += 10  # rm -rf . es extremadamente peligroso
            if "recursive" in pattern.lower():
                score += 3

        # Determinar nivel
        if score >= 10:
            return "critical"
        elif score >= 7:
            return "high"
        elif score >= 3:
            return "medium"
        else:
            return "low"

    def _requires_confirmation(self, analysis: Dict) -> bool:
        """Determina si se requiere confirmación del usuario."""
        # Siempre confirmar si hay archivos vitales
        if analysis["affected_vitals"]:
            return True

        # Confirmar en modo estricto para cualquier operación destructiva
        if self.strict_mode and analysis["is_destructive"]:
            return True

        # Confirmar para riesgo alto o crítico
        if analysis["risk_level"] in ("high", "critical"):
            return True

        # Confirmar si afecta muchos archivos
        if analysis["estimated_files"] > RISK_THRESHOLDS["files_affected"]:
            return True

        return False

    def execute(self, command: str, force: bool = False, dry_run: bool = False) -> bool:
        """
        Ejecuta un comando con protección.

        Args:
            command: Comando a ejecutar
            force: Forzar ejecución sin confirmación
            dry_run: Solo mostrar qué se haría, no ejecutar

        Returns:
            True si se ejecutó correctamente, False si se canceló o falló
        """
        logger.info(f"Analizando comando: {command}")

        # Analizar comando
        analysis = self.analyze_command(command)

        # Si no es destructivo, ejecutar directamente
        if not analysis["is_destructive"]:
            logger.info("Comando no destructivo. Ejecutando...")
            if dry_run:
                print(f"[DRY-RUN] Se ejecutaría: {command}")
                return True
            return self._run_command(command)

        # Es destructivo, mostrar análisis
        self._print_analysis(analysis)

        # Crear backup automático si está habilitado
        backup_path = None
        if self.auto_backup and not dry_run:
            affected_vitals = analysis["affected_vitals"]
            if affected_vitals:
                logger.info("Creando backup de seguridad de archivos vitales...")
                backup_path = self.guardian.create_snapshot(reason="predestructive")
                print(f"[BACKUP] Creado: {backup_path.name}")

        # Verificar si requiere confirmación
        if analysis["requires_confirmation"] and not force:
            if not self._prompt_confirmation(analysis, backup_path):
                logger.info("Ejecución cancelada por el usuario")
                print("[CANCELADO] Operación abortada")
                return False

        # Ejecutar (o simular)
        if dry_run:
            print(f"\n[DRY-RUN] Se ejecutaría: {command}")
            return True

        logger.info(f"Ejecutando comando: {command}")
        success = self._run_command(command)

        if success:
            logger.info("Comando ejecutado exitosamente")
            # Verificar integridad después de operación destructiva
            if analysis["affected_vitals"]:
                print("\n[VERIFICACION] Comprobando integridad de archivos vitales...")
                all_ok, issues = self.guardian.check_integrity()
                if not all_ok:
                    print(
                        "[!] ALERTA: Se detectaron archivos vitales faltantes después de la operación"
                    )
                    if backup_path and input(
                        "¿Restaurar desde backup de seguridad? [s/N]: "
                    ).lower() in ("s", "si"):
                        self.guardian.restore_from_backup(backup_path.name)
        else:
            logger.error("El comando falló")

        return success

    def _print_analysis(self, analysis: Dict):
        """Imprime el análisis de riesgo."""
        print(f"\n{'=' * 60}")
        print("ANALISIS DE SEGURIDAD - OPERACION DESTRUCTIVA DETECTADA")
        print("=" * 60)
        print(f"\nComando: {analysis['command']}")
        print(f"Nivel de riesgo: {analysis['risk_level'].upper()}")

        if analysis["reasons"]:
            print("\nRazones:")
            for reason in analysis["reasons"]:
                print(f"  - {reason}")

        if analysis["affected_vitals"]:
            print(
                f"\n[!] ARCHIVOS VITALES AFECTADOS ({len(analysis['affected_vitals'])}):"
            )
            for vital in analysis["affected_vitals"][:10]:
                print(f"    * {vital}")
            if len(analysis["affected_vitals"]) > 10:
                print(f"    ... y {len(analysis['affected_vitals']) - 10} más")

        if analysis["estimated_files"] > 0:
            print(f"\nArchivos estimados afectados: {analysis['estimated_files']}")

        if analysis["affected_dirs"]:
            print(f"Directorios afectados: {len(analysis['affected_dirs'])}")

    def _prompt_confirmation(self, analysis: Dict, backup_path: Optional[Path]) -> bool:
        """Solicita confirmación al usuario."""
        print("\n" + "-" * 60)

        if analysis["risk_level"] == "critical":
            print(
                "[!] ALERTA CRITICA: Esta operación puede causar pérdida de datos irreversible"
            )

        print("\n¿Deseas continuar con esta operación destructiva?")

        if backup_path:
            print(f"[INFO] Se ha creado un backup de seguridad: {backup_path.name}")

        response = input(
            "\nConfirmar [escribe 'SI' para confirmar / N para cancelar]: "
        ).strip()

        # Para operaciones críticas, requerir confirmación explícita
        if analysis["risk_level"] == "critical":
            return response == "SI"

        return response.lower() in ("s", "si", "y", "yes", "SI")

    def _run_command(self, command: str) -> bool:
        """Ejecuta el comando real."""
        try:
            result = subprocess.run(
                command, shell=True, capture_output=False, text=True
            )
            return result.returncode == 0
        except Exception as e:
            logger.error(f"Error ejecutando comando: {e}")
            return False

    def wrap_python_execution(
        self, python_code: str, globals_dict=None, locals_dict=None
    ):
        """
        Wrapper para ejecutar código Python de forma segura.

        Intercepta llamadas a shutil.rmtree, os.remove, etc.
        """
        # Analizar código por operaciones destructivas
        destructive_found = []
        for category, patterns in DESTRUCTIVE_PATTERNS.items():
            if category == "python_code":
                for pattern in patterns:
                    if re.search(pattern, python_code):
                        destructive_found.append(pattern)

        if destructive_found:
            print("[!] Código Python con operaciones destructivas detectado:")
            for d in destructive_found:
                print(f"    - {d}")

            if input("¿Continuar? [s/N]: ").lower() not in ("s", "si", "y", "yes"):
                print("[CANCELADO]")
                return None

        # Ejecutar código
        if globals_dict is None:
            globals_dict = globals()
        if locals_dict is None:
            locals_dict = locals()

        return exec(python_code, globals_dict, locals_dict)


# =============================================================================
# FUNCIONES DE UTILIDAD
# =============================================================================


def safe_remove(path: str, recursive: bool = False, force: bool = False) -> bool:
    """
    Función segura para eliminar archivos/directorios.

    Siempre verifica contra archivos vitales antes de eliminar.
    """
    executor = SafeExecutor()

    full_path = REPO_ROOT / path if not Path(path).is_absolute() else Path(path)

    # Verificar si es vital
    is_vital = False
    for vital in executor.vitals:
        try:
            full_path.relative_to(vital)
            is_vital = True
            break
        except ValueError:
            pass
        try:
            vital.relative_to(full_path)
            is_vital = True
            break
        except ValueError:
            pass

    if is_vital and not force:
        print(f"[!] ADVERTENCIA: {path} está protegido como archivo vital")
        print("    Usa --force para forzar la eliminación (no recomendado)")
        return False

    # Crear backup si es vital
    if is_vital:
        backup = executor.guardian.create_snapshot(reason="predelete_vital")
        print(f"[BACKUP] Creado antes de eliminar: {backup.name}")

    # Eliminar
    try:
        if full_path.is_dir():
            if recursive:
                shutil.rmtree(full_path)
            else:
                full_path.rmdir()
        else:
            full_path.unlink()
        print(f"[OK] Eliminado: {path}")
        return True
    except Exception as e:
        print(f"[ERROR] No se pudo eliminar {path}: {e}")
        return False


# =============================================================================
# MAIN
# =============================================================================


def main():
    parser = argparse.ArgumentParser(
        description="Safe Executor - Ejecutor seguro con protección de datos vitales",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
    safe-executor.py -- rm -rf workspaces/           # Intercepta y protege
    safe-executor.py --force -- rm -rf temp/        # Forzar ejecución
    safe-executor.py --dry-run -- del *.tmp         # Simular sin ejecutar
    safe-executor.py --strict -- comando            # Modo estricto
        """,
    )

    parser.add_argument(
        "command",
        nargs="?",
        help="Comando a ejecutar (usa -- para separar flags del comando)",
    )
    parser.add_argument(
        "--force", action="store_true", help="Forzar ejecución sin confirmación"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Simular sin ejecutar realmente"
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Modo estricto (requiere confirmación para todo)",
    )
    parser.add_argument(
        "--no-backup", action="store_true", help="No crear backup automático"
    )

    # Parsear argumentos
    args, remaining = parser.parse_known_args()

    # Reconstruir comando
    if remaining:
        command = " ".join(remaining)
    elif args.command:
        command = args.command
    else:
        parser.print_help()
        return 0

    # Crear executor
    executor = SafeExecutor(auto_backup=not args.no_backup, strict_mode=args.strict)

    # Ejecutar
    success = executor.execute(command, force=args.force, dry_run=args.dry_run)

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
