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
    r"C:\ACTUAL\FreakingJSON-pa\Model-Agnostic-AI-Personal-Assistant-Framework"
)
DEFAULT_PREALPHA_DIR = Path(r"C:\ACTUAL\FreakingJSON-pa\Pa_Pre_alpha_Opus_4_6")
DEFAULT_PREALPHA_DEV_DIR = Path(r"C:\ACTUAL\FreakingJSON-pa\Pa_Pre_alpha_Opus_4_6_DEV")

# Archivo de configuración limpio para producción
CLEAN_CONFIG_NAME = "opencode.jsonc.CLEAN-PROD"
CONFIG_NAME = "opencode.jsonc"

# Archivo de configuración de vitals limpio para producción
VITALS_CLEAN_CONFIG_NAME = "vitals.config.json.CLEAN-PROD"
VITALS_CONFIG_NAME = "vitals.config.json"

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
    "*.backup",  # [CRITICO] Backups de proteccion de sync
    "bk",  # [CRITICO] Directorio de backup externo
    "vitals",  # [CRITICO] Backups históricos y snapshots (solo local)
    "logs",  # [CRITICO] Logs internos (sesiones LSP, sistema)
    "docs/technical",  # [CRITICO] Documentación técnica avanzada (solo BASE)
    "workspaces",  # [CRITICO] Proyectos del usuario - SIEMPRE SIN CAMBIOS
    "RELEASE-STAGING",  # [CRITICO] Staging para validación - generado dinámicamente
    "OBSOLETE",  # [CRITICO] Archivos históricos/obsoletos (solo local)
    "Obsoleto",  # [CRITICO] Directorio obsoleto (solo local)
    "core/.context/backups",  # [CRITICO] Backups locales (solo local)
    "core/.context/vitals",  # [CRITICO] VITALS system (solo local)
    "core/.context/codebase/.sanitized",  # [CRITICO] Templates de saneado (solo BASE)
}

# Archivos/directorios a ignorar SOLO en producción (pero sí en dev)
# Estos son documentos de desarrollo interno que NO deben estar en PROD
PROD_ONLY_IGNORE_PATTERNS = {
    # Backlogs y planificación (desarrollo interno)
    "docs/backlog.md",
    "docs/backlog.view.md",
    # Configuración de agentes (interna)
    "docs/AGENT-CONFIGURATION.md",
    # Multi-CLI workflow (desarrollo)
    "docs/MULTI-CLI.md",
    # Procesos de release (interno)
    "docs/RELEASE-CHECKLIST.md",
    # VITALS - herramientas internas de desarrollo
    "docs/VITALS-GUARDIAN.md",
    "docs/VITALS-QUICKSTART.md",
    # Documentación técnica del workflow (AVAILABLE EN PROD - útil para usuarios)
    # docs/WORKFLOW-STANDARD.md - NO excluir, incluir en PROD
    # PRDs de desarrollo
    "docs/prd-*.md",
    # Ejemplos técnicos de desarrollo
    "docs/workflow-test-*.md",
    # Planes de desarrollo
    "docs/PLAN-*.md",
    "docs/SYNC-PROTOCOL.md",
    # PRPs - Planes de desarrollo (solo BASE)
    "PRPs",
    # .opencode/plans - Planes de desarrollo (solo BASE)
    ".opencode/plans",
    # Tests scripts (solo BASE)
    "core/scripts/test_*.py",
    # Backup files (solo BASE)
    "core/scripts/.backup-*",
    "*.backup-*",
    # Dashboard data files in wrong location
    "dashboard-data.js",
    "dashboard.html.backup-*",
    # Vitals - archivos de inventario/logs (solo BASE)
    "core/.context/vitals/vitals.manifest.json",
    "core/.context/vitals/vitals.log",
    "core/.context/vitals/*.log",
    "core/.context/vitals/backups/",
    "core/.context/vitals/remote-setup.log",
    "core/.context/vitals/safe-executor.log",
    # Development sync scripts (internal workflow only)
    "core/scripts/sync-base-to-dev.sh",
    "core/scripts/sync-base-to-prod.sh",
    "core/scripts/sync-dev-to-base.sh",
    # Archivos de estado de desarrollo (no son públicos)
    "core/.context/dev-resources-state.json",
    "core/.context/.migration_state.json",
    "core/.context/INITIALIZATION_STATUS.md",
    # Sesiones - solo template en PROD (sesiones reales son privadas)
    "core/.context/sessions/2026-",
    "core/.context/sessions/2025-",
    "core/.context/sessions/SESSION_RESUME_",
    "core/.context/sessions/verification_report_",
    # Knowledge con datos de usuario/interacciones
    "core/.context/knowledge/users/",
    "core/.context/knowledge/interactions/",
    "core/.context/knowledge/sessions-index.json",
    "core/.context/knowledge/search-index.db",
    "core/.context/knowledge/errors/",  # contiene logs reales
    # Config obsoleta (reemplazada por framework.yaml)
    "config/knowledge_base.json",
    "config/mcp.json",
    "config/quotas.json",
    # Docs con información interna
    "docs/README-TECNICO.md",  # contiene rutas internas de trabajo
    "docs/RELEASES/",  # desactualizado, revisar
}

# Archivos/directorios que EXISTEN en PROD pero NO en BASE
# Se usan para evitar eliminarlos durante el sync
PROD_LOCAL_ONLY_PATTERNS = {
    "Obsoleto",  # Archivos obsoletos (PRPs, docs viejos, etc.)
    # =====================================================================
    # ARCHIVOS CORE CRÍTICOS - NUNCA ELIMINAR (protección contra bug "./")
    # =====================================================================
    "AGENTS.md",
    "VERSION",
    "README.md",
    "README-simple.md",
    "README-technical.md",
    "README_en.md",
    "CHANGELOG.md",
    "ROADMAP.md",
    "LICENSE",
    "config/framework.yaml",
    # KB archivos críticos del framework
    "core/.context/knowledge/skills-index.json",
    "core/.context/knowledge/agents-index.json",
    "core/.context/knowledge/learning",
    "core/.context/knowledge/self-healing",
    "core/.context/knowledge/prompts",
    "core/.context/knowledge/insights",
    # Docs CORE públicos
    "docs/core",
    "docs/ASSEMBLY-LINE.md",
    "docs/PHILOSOPHY.md",
}

# =============================================================================
# ARCHIVOS CRÍTICOS PARA VALIDACIÓN POST-SYNC
# Si alguno falta después del sync, el proceso falla
# =============================================================================

CRITICAL_PROD_FILES = [
    # Archivos root críticos
    "AGENTS.md",
    "VERSION",
    "README.md",
    "CHANGELOG.md",
    # Docs CORE públicos (8 PRPs)
    "docs/core/PRP-001-CORE-Framework-Validation.md",
    "docs/core/PRP-002-CORE-Context-Aware.md",
    "docs/core/PRP-003-CORE-Antifragile-Errors.md",
    "docs/core/PRP-004-CORE-Self-Healing-MCP.md",
    "docs/core/PRP-005-CORE-Assembly-Line.md",
    "docs/core/PRP-008-CORE-Version-Governance.md",
    "docs/core/PRP-009-CORE-Release-Sanitization.md",
    "docs/core/PRP-011-CORE-Knowledge-Extraction.md",
    # KB índices del framework
    "core/.context/knowledge/skills-index.json",
    "core/.context/knowledge/agents-index.json",
    "core/.context/knowledge/knowledge-index.json",
    # KB aprendizaje del framework (crítico para usuarios)
    "core/.context/knowledge/learning/discoveries.md",
    "core/.context/knowledge/learning/best-practices.md",
    "core/.context/knowledge/learning/README.md",
    # Documentación workflow
    "docs/WORKFLOW-STANDARD.md",
    # OpenCode config (sanitizado - CLEAN-PROD ya en sync)
    ".opencode/config.json",
    ".opencode/package.json",
]

# Staging for release validation
STAGING_DIR = "RELEASE-STAGING"
STAGING_CHECKLIST = "VALIDATION-CHECKLIST.md"

# =============================================================================
# DIRECTORIOS PROTEGIDOS EN PreAlpha-DEV (nunca se sobrescriben)
# =============================================================================

PROTECTED_DIRS = {
    # Directorios de usuario (SIEMPRE proteger)
    "core/.context/sessions",  # Sesiones del usuario
    "core/.context/codebase",  # Conocimiento del usuario (recordatorios, ideas)
    "core/.context/workspaces",  # Contexto por workspace (configuración)
    "config",  # Configuraciones del usuario (branding, i18n)
    # NOTA: workspaces/ se ignora completamente (ver ADDITIONAL_IGNORE_PATTERNS)
    # Local/custom (SIEMPRE proteger)
    "core/agents/subagents/_local",
    "core/skills/_local",
    # DENTRO de knowledge - subdirectorios específicos del usuario
    # (NO proteger learning/, self-healing/, prompts/ - son del framework)
    "core/.context/knowledge/users",  # Preferencias de usuario
    "core/.context/knowledge/interactions",  # Log de interacciones del usuario
    "core/.context/knowledge/insights",  # Insights extraídos del usuario
    "core/.context/knowledge/projects",  # Proyectos registrados por el usuario
    # VITALS - configuración (proteger configs, pero permite sync de scripts)
    "core/.context/vitals/vitals.config.json",
    "core/.context/vitals/vitals.manifest.json",
    # NOTA: sessions-index.json, skills-index.json, agents-index.json
    # NO están protegidos para permitir sync de estructuras actualizadas.
    # Se regeneran con session-indexer.py --rebuild si es necesario.
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
        self.version: Optional[str] = None
        self.version_mismatch: bool = False
        self.staging_path: Optional[str] = None

    def add(self, path: str):
        self.added.append(path)

    def modify(self, path: str):
        self.modified.append(path)

    def delete(self, path: str):
        self.deleted.append(path)

    def ignore(self, path: str):
        self.ignored.append(path)

    def sanitize(self, path: str):
        """Registra que un archivo fue sanitizado (contenido interno reemplazado por template)"""
        self.modified.append(f"{path} [SANITIZED]")

    def error(self, msg: str):
        self.errors.append(msg)

    def set_config_replaced(self):
        self.config_replaced = True

    def set_version(self, version: str):
        self.version = version

    def set_version_mismatch(self):
        self.version_mismatch = True

    def set_staging(self, path: str):
        self.staging_path = path

    def print_summary(self, dry_run: bool = False):
        mode = "[DRY-RUN] " if dry_run else ""
        print(f"\n{'=' * 70}")
        print(f"{mode}RESUMEN DE SINCRONIZACIÓN")
        print(f"{'=' * 70}")

        if self.config_replaced:
            print(f"\n[CFG] CONFIGURACION:")
            print(f"   > opencode.jsonc -> REEMPLAZADO por version CLEAN-PROD")

        if self.version:
            prefix = "[!]" if self.version_mismatch else "[V]"
            status = "mismatch" if self.version_mismatch else ""
            print(
                f"\n{prefix} VERSION: {self.version}{f' ({status})' if status else ''}"
            )

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

        if self.staging_path:
            print(f"\n[STAGING] Release staging generated:")
            print(f"   Location: {self.staging_path}")
            print(f"   Checklist: {self.staging_path}/{STAGING_CHECKLIST}")
            print(f"\n[!] IMPORTANTE: Valida el staging antes de push remoto!")


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


def should_ignore_prod_only(file_path: str, patterns: Set[str]) -> bool:
    """
    Verifica si un archivo debe ser ignorado según PROD_ONLY_IGNORE_PATTERNS.
    Soporta:
    - Coincidencia exacta
    - Directorios (ej: "PRPs" coincide con "PRPs/file.md")
    - Wildcards (ej: "docs/prd-*.md")
    """
    for pattern in patterns:
        # Coincidencia exacta
        if file_path == pattern:
            return True
        # Directorio (pattern sin wildcard)
        if not "*" in pattern and not "/" in pattern:
            # Es un nombre de directorio
            if file_path.startswith(pattern + "/") or file_path.startswith(
                pattern + "\\"
            ):
                return True
        # Wildcard pattern
        if "*" in pattern:
            if fnmatch.fnmatch(file_path, pattern):
                return True
            if fnmatch.fnmatch(os.path.basename(file_path), pattern):
                return True
        # Path pattern con /
        if "/" in pattern and pattern.rstrip("/") in file_path:
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


def restore_protected_dirs(dest_dir: Path, backups: dict, reporter: SyncReporter):
    """
    Restaura directorios protegidos después del sync.
    """
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


def generate_validation_checklist(staging_path: Path, version: str) -> None:
    """
    Generates validation checklist markdown file in staging folder.
    """
    checklist_content = f"""# Release Validation Checklist / Checklist de Validación de Release

> **Version**: {version}
> **Generated**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
> **Status**: PENDING VALIDATION

---

## Security Checks / Verificaciones de Seguridad

- [ ] No credentials/tokens in any file
- [ ] No internal PRPs in root (should be in Obsoleto/)
- [ ] No .opencode/plans/ in root
- [ ] No test_*.py scripts
- [ ] No internal docs (backlog, AGENT-CONFIGURATION, etc.)
- [ ] README.md is user-facing (not technical)

**Verify with**:
```bash
grep -r "token|password|secret|api_key" . --include="*.py" --include="*.json" --include="*.yaml"
ls PRPs/ 2>/dev/null || echo "OK: No PRPs in root"
```

---

## Functionality Checks / Verificaciones de Funcionalidad

- [ ] `python core/scripts/session-start.py` runs without errors
- [ ] `python core/scripts/session-end.py --summary` shows correct version
- [ ] `dashboard.html` opens correctly in browser
- [ ] All core skills are present in `core/skills/core/`

**Quick test**:
```bash
python core/scripts/session-start.py
python core/scripts/version-updater.py --dry-run
```

---

## Documentation Checks / Verificaciones de Documentación

- [ ] VERSION file matches CHANGELOG.md
- [ ] README.md has correct version badge
- [ ] AGENTS.md has correct version
- [ ] CHANGELOG.md has entry for this version

---

## Ready for Push / Listo para Push

- [ ] All security checks passed
- [ ] All functionality checks passed
- [ ] All documentation checks passed
- [ ] User has reviewed staging folder

**If all checks pass**:
```bash
cd ..
git add .
git commit -m "release: v{version}"
git push origin main
```

---

_Validated by_: ________________
_Date_: ________________
"""
    checklist_path = staging_path / STAGING_CHECKLIST
    checklist_path.write_text(checklist_content, encoding="utf-8")


def archive_staging(dest_dir: Path, staging_path: Path, reporter: SyncReporter) -> None:
    """
    Archives existing staging folder before creating new one.
    Moves to staging_path/.archive/v{version}-{timestamp}/
    """
    version_file = staging_path / "VERSION"
    if version_file.exists():
        version = version_file.read_text(encoding="utf-8").strip()
    else:
        version = "unknown"

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    archive_name = f"v{version}-{timestamp}"

    archive_dir = staging_path / ".archive"
    archive_dir.mkdir(parents=True, exist_ok=True)

    archive_path = archive_dir / archive_name

    archive_path.mkdir(parents=True, exist_ok=True)

    for item in staging_path.iterdir():
        if item.name != ".archive":
            shutil.move(str(item), str(archive_path / item.name))

    reporter.ignore(f"[ARCHIVED] Previous staging: {archive_name}")


def generate_staging(dest_dir: Path, version: str, reporter: SyncReporter) -> bool:
    """
    Generates a staging copy of PROD for validation before remote push.
    Creates RELEASE-STAGING/ with exact copy of PROD clean + validation checklist.
    """
    staging_path = dest_dir / STAGING_DIR

    print(f"\n[STAGING] Generating release staging...")

    if staging_path.exists():
        print(f"[STAGING] Archiving previous staging...")
        archive_staging(dest_dir, staging_path, reporter)
        if staging_path.exists():
            shutil.rmtree(staging_path)

    staging_path.mkdir(parents=True, exist_ok=True)

    exclude_patterns = {
        ".git",
        "__pycache__",
        "*.pyc",
        ".ruff_cache",
        "Obsoleto",
        ".archive",
        STAGING_DIR,
    }

    for item in dest_dir.iterdir():
        if item.name in exclude_patterns:
            continue
        if item.name.startswith("."):
            continue

        dest_item = staging_path / item.name
        try:
            if item.is_dir():
                shutil.copytree(item, dest_item)
            else:
                shutil.copy2(item, dest_item)
        except Exception as e:
            reporter.error(f"Error copying to staging: {item.name}: {e}")

    generate_validation_checklist(staging_path, version)

    reporter.set_staging(str(staging_path))
    print(f"[STAGING] Created: {staging_path}")
    print(f"[STAGING] Checklist: {staging_path / STAGING_CHECKLIST}")

    return True


def validate_version_consistency(
    src_dir: Path, dest_dir: Path, reporter: SyncReporter
) -> bool:
    """
    Validates that VERSION file is consistent between source and destination.
    Returns True if consistent or VERSION doesn't exist in dest.
    """
    src_version_file = src_dir / "VERSION"
    dest_version_file = dest_dir / "VERSION"

    if not src_version_file.exists():
        return True

    src_version = src_version_file.read_text().strip()
    reporter.set_version(src_version)

    if dest_version_file.exists():
        dest_version = dest_version_file.read_text().strip()
        if src_version != dest_version:
            reporter.error(f"VERSION mismatch: BASE={src_version}, DEST={dest_version}")
            reporter.set_version_mismatch()
            return False

    return True


def sync_directory(
    src_dir: Path,
    dest_dir: Path,
    gitignore_patterns: Set[str],
    reporter: SyncReporter,
    dry_run: bool = False,
    use_clean_config: bool = False,
    is_prod_mode: bool = False,
    protect_dirs: bool = False,
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
        protect_dirs: Si True, protege directorios personales (sessions, codebase, workspaces)

    Returns:
        True si hubo éxito, False si hubo errores
    """
    success = True
    protected_backups = {}

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

            # FIX CRÍTICO: Normalizar path "./" para archivos en directorio raíz
            # Path.relative_to() retorna "." para archivos en root, causando que
            # se marquen como eliminados durante el sync (bug documentado en sesión 2026-03-11)
            if rel_path.startswith("./"):
                rel_path = rel_path[2:]

            # Saltar .gitignore (se maneja especialmente)
            if file == ".gitignore":
                continue

            # Verificar si debe ignorarse
            if should_ignore(rel_path, gitignore_patterns):
                reporter.ignore(rel_path)
                continue

            # Verificar exclusiones específicas de producción
            if is_prod_mode and should_ignore_prod_only(
                rel_path, PROD_ONLY_IGNORE_PATTERNS
            ):
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
            src_for_hash = src_file  # Valor por defecto

            if not dest_file.exists():
                needs_copy = True
                reporter.add(rel_path)
            else:
                # SANEADO: En PROD, siempre sanitizar archivos codebase/
                # Forzar copia aunque hash coincida (para asegurar sanitizacion)
                # Normalizar path para comparacion (soporta Windows y Unix)
                normalized_src = str(src_file).replace("\\", "/")
                if is_prod_mode and "core/.context/codebase/" in normalized_src:
                    sanitized_template = src_file.parent / ".sanitized" / file
                    if sanitized_template.exists():
                        src_for_hash = sanitized_template
                        needs_copy = True  # Forzar copia para sanitizar
                        reporter.sanitize(rel_path)
                    # Si no existe template, usar original

                # Comparar hashes solo si no forzamos copia por sanitizacion
                if not needs_copy:
                    src_hash = calculate_hash(src_for_hash)
                    dest_hash = calculate_hash(dest_file)
                    if src_hash != dest_hash:
                        needs_copy = True
                    reporter.modify(rel_path)

            # Copiar archivo
            if needs_copy and not dry_run:
                try:
                    dest_file.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src_for_hash, dest_file)
                except Exception as e:
                    reporter.error(f"Error copiando {rel_path}: {e}")
                    success = False

    # Detectar archivos eliminados
    deleted = dest_files_before - src_files
    for del_path in deleted:
        # No eliminar archivos ignorados
        if not should_ignore(del_path, gitignore_patterns):
            # [PROTECCION] No eliminar si está en directorio protegido
            if protect_dirs and any(
                del_path.startswith(protected) or protected in del_path
                for protected in PROTECTED_DIRS
            ):
                reporter.ignore(f"[PROTEGIDO] {del_path}")
                continue

            # [PROTECCION PROD] No eliminar archivos que solo existen en PROD
            if is_prod_mode and any(
                del_path.startswith(pattern) or pattern in del_path
                for pattern in PROD_LOCAL_ONLY_PATTERNS
            ):
                reporter.ignore(f"[PROD-LOCAL] {del_path}")
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
                try:
                    shutil.copy2(src_gitignore, dest_gitignore)
                except Exception as e:
                    reporter.error(f"Error copiando .gitignore: {e}")
                    success = False

    # Validar consistencia de VERSION (warning si mismatch)
    validate_version_consistency(src_dir, dest_dir, reporter)

    # Restaurar directorios protegidos después del sync
    if protect_dirs and not dry_run and protected_backups:
        restore_protected_dirs(dest_dir, protected_backups, reporter)

    # =============================================================================
    # POST-PROCESAMIENTO PARA PRODUCCIÓN
    # =============================================================================
    if is_prod_mode and not dry_run:
        # 1. README-simple.md -> README.md (sobrescribir)
        readme_simple = src_dir / "README-simple.md"
        readme_dest = dest_dir / "README.md"
        if readme_simple.exists():
            try:
                shutil.copy2(readme_simple, readme_dest)
                if "README.md" not in reporter.modified:
                    reporter.modify("README.md (from README-simple.md)")
            except Exception as e:
                reporter.error(f"Error copiando README-simple.md a README.md: {e}")
                success = False

        # 2. Eliminar opencode.jsonc.CLEAN-PROD del destino (solo debe estar en BASE)
        clean_prod_dest = dest_dir / CLEAN_CONFIG_NAME
        if clean_prod_dest.exists():
            try:
                clean_prod_dest.unlink()
                reporter.delete(CLEAN_CONFIG_NAME)
            except Exception as e:
                reporter.error(f"Error eliminando {CLEAN_CONFIG_NAME}: {e}")

        # 2.5. Copiar vitals.config.json.CLEAN-PROD -> vitals.config.json
        vitals_clean_src = (
            src_dir / "core" / ".context" / "vitals" / VITALS_CLEAN_CONFIG_NAME
        )
        vitals_config_dest = (
            dest_dir / "core" / ".context" / "vitals" / VITALS_CONFIG_NAME
        )
        if vitals_clean_src.exists():
            try:
                vitals_config_dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(vitals_clean_src, vitals_config_dest)
                reporter.modify(
                    f"core/.context/vitals/{VITALS_CONFIG_NAME} (from {VITALS_CLEAN_CONFIG_NAME})"
                )
            except Exception as e:
                reporter.error(f"Error copiando vitals.config.json.CLEAN-PROD: {e}")
                success = False

        # 2.6. Eliminar vitals.config.json.CLEAN-PROD del destino
        vitals_clean_dest = (
            dest_dir / "core" / ".context" / "vitals" / VITALS_CLEAN_CONFIG_NAME
        )
        if vitals_clean_dest.exists():
            try:
                vitals_clean_dest.unlink()
                reporter.delete(f"core/.context/vitals/{VITALS_CLEAN_CONFIG_NAME}")
            except Exception as e:
                reporter.error(f"Error eliminando vitals.config.json.CLEAN-PROD: {e}")

        # 3. Eliminar vitals/ del destino si existe (solo local, nunca en PROD)
        vitals_dest = dest_dir / "vitals"
        if vitals_dest.exists():
            try:
                shutil.rmtree(vitals_dest)
                reporter.delete("vitals/")
            except Exception as e:
                reporter.error(f"Error eliminando vitals/: {e}")

        # 4. [PROD] Eliminar directorios con datos de usuario/interacciones
        # Estos directorios contienen información privada y no deben estar en PROD
        # EXCEPCION: sessions/ debe tener el template
        dirs_to_clean_prod = [
            "logs",
            "core/.context/knowledge/users",
            "core/.context/knowledge/interactions",
            "core/.context/knowledge/errors",  # Contiene logs reales
            "core/.context/knowledge/search-index.db",
            "config/knowledge_base.json",
            "config/mcp.json",
            "config/quotas.json",
        ]
        for clean_path in dirs_to_clean_prod:
            clean_full = dest_dir / clean_path
            if clean_full.exists():
                try:
                    if clean_full.is_file():
                        clean_full.unlink()
                    else:
                        shutil.rmtree(clean_full)
                    reporter.delete(clean_path)
                except Exception as e:
                    reporter.error(f"Error eliminando {clean_path}: {e}")

        # 4.5 [PROD] Reemplazar sessions/ con template (sesiones reales son privadas)
        sessions_dest = dest_dir / "core/.context/sessions"
        session_template_src = src_dir / "core/.context/sessions/SESSION_TEMPLATE.md"

        # Eliminar sesiones existentes
        if sessions_dest.exists():
            try:
                shutil.rmtree(sessions_dest)
                reporter.delete("core/.context/sessions/ (all)")
            except Exception as e:
                reporter.error(f"Error eliminando sessions/: {e}")

        # Crear directorio y copiar template
        if session_template_src.exists():
            try:
                sessions_dest.mkdir(parents=True, exist_ok=True)
                shutil.copy2(
                    session_template_src, sessions_dest / "SESSION_TEMPLATE.md"
                )
                reporter.add("core/.context/sessions/SESSION_TEMPLATE.md")
            except Exception as e:
                reporter.error(f"Error copiando SESSION_TEMPLATE.md: {e}")

        # Generate staging for validation (PROD mode only)
        version = ""
        version_file = src_dir / "VERSION"
        if version_file.exists():
            version = version_file.read_text(encoding="utf-8").strip()
        generate_staging(dest_dir, version, reporter)

        # ================================================================
        # VALIDACIÓN DE STAGING (CORE-007: Release Sanitization)
        # ================================================================
        # El staging ha sido generado en RELEASE-STAGING/
        # El usuario DEBE validar antes de hacer push a remoto
        #
        # Para validar manualmente:
        #   1. Revisar RELEASE-STAGING/CHECKLIST.md
        #   2. Verificar archivos críticos presentes
        #   3. Ejecutar: python core/scripts/framework-guardian.py --timing pre-release
        #   4. Solo después de validación, hacer push manualmente
        # ================================================================
        if is_prod_mode and not dry_run:
            print(f"\n{'=' * 70}")
            print(f"[!] VALIDACION DE STAGING REQUERIDA ANTES DE PUSH")
            print(f"{'=' * 70}")
            print(f"\n[PASOS OBLIGATORIOS ANTES DE PUSH A REMOTO:]")
            print(f"  1. Revisa RELEASE-STAGING/CHECKLIST.md")
            print(f"  2. Verifica archivos criticos en staging")
            print(
                f"  3. Ejecuta: python core/scripts/framework-guardian.py --timing pre-release"
            )
            print(f"  4. Confirma que todo esta OK")
            print(f"  5. Haz push manualmente: git push origin main")
            print(f"\n{'=' * 70}")
            print(f"[!] NO HACER PUSH SIN VALIDAR EL STAGING PRIMERO")
            print(f"{'=' * 70}\n")

        # 4. VALIDACIÓN DE ARCHIVOS CRÍTICOS POST-SYNC
        # Verifica que archivos esenciales del framework no se perdieron
        for critical_file in CRITICAL_PROD_FILES:
            critical_path = dest_dir / critical_file
            if not critical_path.exists():
                reporter.error(f"CRITICAL FILE MISSING: {critical_file}")
                reporter.error(
                    "SYNC FAILED: Critical framework files were lost during sync!"
                )
                reporter.error(
                    "This indicates the './' path bug or incorrect exclusions."
                )
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
    # NOTA: NO usamos .gitignore para decidir qué copiar al framework
    # El .gitignore es para CONTROL DE VERSIONES (datos locales privados)
    # Para SYNC usamos: ADDITIONAL_IGNORE_PATTERNS + PROD_ONLY_IGNORE_PATTERNS
    # Esto asegura que TODO el framework (incluyendo knowledge/) llegue a PROD
    gitignore_path = args.base_dir / ".gitignore"
    gitignore_patterns = set()  # VACÍO - No usar .gitignore para sync
    print(f"\n[i] .gitignore NO usado para sync (solo patrones explícitos)")

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
            protect_dirs=False,  # PROD: sincronización limpia
        )

        reporter.print_summary(dry_run=args.dry_run)
        all_success = all_success and success

    if args.mode in ["dev", "all"]:
        print(f"\n{'=' * 70}")
        print(
            f">>> SINCRONIZANDO: Desarrollo (mantiene config original + protege datos)"
        )
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
            protect_dirs=True,  # DEV: protege directorios personales
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
