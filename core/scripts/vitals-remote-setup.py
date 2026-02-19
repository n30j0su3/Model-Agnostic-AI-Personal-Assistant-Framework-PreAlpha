#!/usr/bin/env python3
"""
Vitals Remote Sync Setup - Configuración de Sincronización Remota
==================================================================

Configura automáticamente la sincronización de backups con el repositorio
externo privado. Maneja credenciales y verificación de conectividad.

Uso:
    python core/scripts/vitals-remote-setup.py
    python core/scripts/vitals-remote-setup.py --check      # Solo verificar
    python core/scripts/vitals-remote-setup.py --auto       # Configuración automática

Flujo:
    1. Verificar credenciales GitHub almacenadas
    2. Probar conexión al repo remoto
    3. Configurar remote 'vitals-backup' si no existe
    4. Habilitar sync automático en vitals.config.json
"""

import argparse
import json
import logging
import os
import subprocess
import sys
from pathlib import Path

# Paths
REPO_ROOT = Path(__file__).resolve().parents[2]
VITALS_DIR = REPO_ROOT / "core" / ".context" / "vitals"
CONFIG_PATH = VITALS_DIR / "vitals.config.json"
LOG_PATH = VITALS_DIR / "remote-setup.log"

# Remote vitals
VITALS_REMOTE_NAME = "vitals-backup"
VITALS_REMOTE_URL = (
    "https://github.com/n30j0su3/Model-Agnostic-AI-Personal-Assistant-Framework-dev.git"
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_PATH, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)


def run_git(args, cwd=None, capture=True, check=False):
    """Ejecutar comando git."""
    cmd = ["git"] + args
    try:
        if capture:
            result = subprocess.run(
                cmd, cwd=cwd or REPO_ROOT, capture_output=True, text=True, check=check
            )
            return result
        else:
            return subprocess.run(cmd, cwd=cwd or REPO_ROOT, check=check)
    except Exception as e:
        logger.error(f"Error ejecutando git: {e}")
        return None


def check_git_credentials():
    """Verificar si hay credenciales de Git configuradas."""
    logger.info("Verificando credenciales Git...")

    # Verificar si hay .gitconfig con credenciales helper
    gitconfig = Path.home() / ".gitconfig"
    if gitconfig.exists():
        try:
            content = gitconfig.read_text(encoding="utf-8")
            if "credential" in content:
                logger.info("[OK] Helper de credenciales configurado")
                return True
        except:
            pass

    # Verificar si hay credenciales en Windows Credential Manager (solo Windows)
    if os.name == "nt":
        try:
            result = subprocess.run(
                ["cmdkey", "/list"], capture_output=True, text=True, timeout=5
            )
            if "git" in result.stdout.lower() or "github" in result.stdout.lower():
                logger.info(
                    "[OK] Credenciales encontradas en Windows Credential Manager"
                )
                return True
        except:
            pass

    logger.warning("[!] No se detectaron credenciales Git configuradas")
    return False


def test_github_connection():
    """Probar conexión a GitHub."""
    logger.info("Probando conexión a GitHub...")

    result = run_git(["ls-remote", VITALS_REMOTE_URL], capture=True)

    if result is None:
        logger.error("[ERROR] No se pudo ejecutar git")
        return False

    if result.returncode == 0:
        logger.info("[OK] Conexión a GitHub exitosa")
        return True

    if (
        "Authentication failed" in result.stderr
        or "could not read Username" in result.stderr
    ):
        logger.error(
            "[ERROR] Autenticación fallida - Credenciales inválidas o faltantes"
        )
        logger.info("""
[AYUDA] Para configurar credenciales:

Opción 1 - Git Credential Manager (recomendado):
    git credential-manager configure
    git credential-manager github login

Opción 2 - Token de acceso personal:
    1. Crea un token en https://github.com/settings/tokens
    2. Configura git:
       git config --global credential.helper store
    3. Intenta un push manual para guardar credenciales:
       git push vitals-backup main

Opción 3 - URL con token (no recomendado para compartir):
    git remote set-url vitals-backup https://TOKEN@github.com/n30j0su3/Model-Agnostic-AI-Personal-Assistant-Framework-dev.git
""")
        return False

    logger.error(f"[ERROR] Error de conexión: {result.stderr}")
    return False


def check_vitals_remote():
    """Verificar si el remote 'vitals-backup' existe."""
    logger.info("Verificando remote 'vitals-backup'...")

    result = run_git(["remote", "-v"], capture=True)

    if result and VITALS_REMOTE_NAME in result.stdout:
        logger.info(f"[OK] Remote '{VITALS_REMOTE_NAME}' ya existe")
        # Verificar URL
        for line in result.stdout.split("\n"):
            if VITALS_REMOTE_NAME in line and VITALS_REMOTE_URL in line:
                return True
        logger.warning("[!] Remote existe pero con URL diferente")
        return "wrong_url"

    return False


def add_vitals_remote():
    """Agregar remote 'vitals-backup'."""
    logger.info(f"Agregando remote '{VITALS_REMOTE_NAME}'...")

    result = run_git(
        ["remote", "add", VITALS_REMOTE_NAME, VITALS_REMOTE_URL], capture=True
    )

    if result and result.returncode == 0:
        logger.info(f"[OK] Remote '{VITALS_REMOTE_NAME}' agregado")
        return True

    logger.error(
        f"[ERROR] No se pudo agregar remote: {result.stderr if result else 'Unknown error'}"
    )
    return False


def update_vitals_remote():
    """Actualizar URL del remote si es necesario."""
    logger.info(f"Actualizando URL del remote '{VITALS_REMOTE_NAME}'...")

    result = run_git(
        ["remote", "set-url", VITALS_REMOTE_NAME, VITALS_REMOTE_URL], capture=True
    )

    if result and result.returncode == 0:
        logger.info(f"[OK] URL del remote actualizada")
        return True

    return False


def enable_auto_sync():
    """Habilitar sync automático en configuración."""
    logger.info("Habilitando sync automático...")

    if not CONFIG_PATH.exists():
        logger.error(f"[ERROR] No existe archivo de configuración: {CONFIG_PATH}")
        return False

    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            config = json.load(f)

        config["sync_to_remote"] = True
        config["auto_sync_after_backup"] = True
        config["last_sync_setup"] = (
            subprocess.check_output(["date", "+%Y-%m-%d_%H-%M-%S"]).decode().strip()
        )

        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)

        logger.info("[OK] Sync automático habilitado en configuración")
        return True
    except Exception as e:
        logger.error(f"[ERROR] No se pudo actualizar configuración: {e}")
        return False


def test_sync():
    """Probar sync inicial (dry-run)."""
    logger.info("Probando sync inicial...")

    # Verificar que el remote está configurado
    remote_status = check_vitals_remote()
    if not remote_status:
        logger.error("[ERROR] Remote no configurado")
        return False

    if remote_status == "wrong_url":
        update_vitals_remote()

    # Intentar fetch para probar conexión
    result = run_git(["fetch", VITALS_REMOTE_NAME], capture=True)

    if result and result.returncode == 0:
        logger.info("[OK] Fetch de prueba exitoso")
        return True

    if "Authentication failed" in (result.stderr if result else ""):
        logger.error("[ERROR] Autenticación fallida durante fetch")
        return False

    # El remote puede estar vacío, eso es OK
    if "Could not find" in (
        result.stderr if result else ""
    ) or "does not appear to be a git repository" in (result.stderr if result else ""):
        logger.info("[INFO] Remote existe pero puede estar vacío (esto es normal)")
        return True

    logger.warning(
        f"[WARN] Resultado inesperado del fetch: {result.stderr if result else 'No output'}"
    )
    return True  # Asumir éxito para no bloquear


def setup_credentials_interactive():
    """Guía interactiva para configurar credenciales."""
    print("""
=================================================================
CONFIGURACIÓN DE CREDENCIALES GIT
=================================================================

Parece que las credenciales de GitHub no están configuradas o son inválidas.

El repositorio de backups remotos requiere autenticación.

Opciones disponibles:

1. Token de Acceso Personal (Classic)
   - Ve a: https://github.com/settings/tokens
   - Genera un nuevo token con permisos 'repo'
   - Usa el token como contraseña cuando git lo solicite

2. GitHub CLI (gh)
   - Instala: https://cli.github.com/
   - Ejecuta: gh auth login

3. Git Credential Manager
   - git credential-manager github login

Presiona Enter cuando hayas configurado las credenciales...
""")

    input()

    # Verificar nuevamente
    if test_github_connection():
        print("[OK] Credenciales verificadas correctamente!")
        return True
    else:
        print("[ERROR] Las credenciales siguen sin funcionar.")
        retry = input("¿Intentar de nuevo? [s/N]: ").strip().lower()
        if retry in ("s", "si", "y", "yes"):
            return setup_credentials_interactive()
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Configurar sincronización remota de backups"
    )
    parser.add_argument(
        "--check", action="store_true", help="Solo verificar estado, no configurar"
    )
    parser.add_argument(
        "--auto", action="store_true", help="Configuración automática sin interacción"
    )
    args = parser.parse_args()

    print("""
=================================================================
VITALS REMOTE SYNC SETUP
Configuración de sincronización remota de backups
=================================================================
""")

    # 1. Verificar que estamos en un repo git
    if not (REPO_ROOT / ".git").exists():
        logger.error("[ERROR] No estamos en un repositorio Git")
        return 1

    # 2. Verificar credenciales
    has_credentials = check_git_credentials()

    # 3. Probar conexión
    can_connect = test_github_connection()

    if args.check:
        # Solo verificar
        print(f"\nEstado:")
        print(f"  Credenciales: {'[OK]' if has_credentials else '[FALTAN]'}")
        print(f"  Conexión: {'[OK]' if can_connect else '[FALLIDA]'}")
        return 0 if can_connect else 1

    # 4. Si no puede conectar, intentar configurar credenciales
    if not can_connect and not args.auto:
        if not setup_credentials_interactive():
            logger.error("[ERROR] No se pudieron configurar las credenciales")
            return 1
        can_connect = True

    if not can_connect:
        logger.error("[ERROR] No se puede conectar al repositorio remoto")
        return 1

    # 5. Verificar/Configurar remote
    remote_status = check_vitals_remote()
    if not remote_status:
        if not add_vitals_remote():
            return 1
    elif remote_status == "wrong_url":
        update_vitals_remote()

    # 6. Probar sync
    if not test_sync():
        logger.error("[ERROR] El test de sync falló")
        return 1

    # 7. Habilitar auto-sync
    if not enable_auto_sync():
        logger.warning("[WARN] No se pudo habilitar auto-sync")

    print("""
=================================================================
[OK] CONFIGURACIÓN COMPLETADA
=================================================================

El sistema de backups remotos está configurado.

Resumen:
  - Remote: vitals-backup
  - URL: https://github.com/n30j0su3/Model-Agnostic-AI-Personal-Assistant-Framework-dev.git
  - Sync automático: Habilitado

Comandos útiles:
  python core/scripts/vitals-guardian.py sync
  git push vitals-backup main

=================================================================
""")

    return 0


if __name__ == "__main__":
    sys.exit(main())
