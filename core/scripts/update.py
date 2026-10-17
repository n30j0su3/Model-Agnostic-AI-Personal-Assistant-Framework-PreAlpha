#!/usr/bin/env python3
"""Framework updater with user-state preservation and post-update migrations."""

import argparse
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import urllib.request
import zipfile
from datetime import datetime
from pathlib import Path, PurePosixPath


REPO_ROOT = Path(__file__).resolve().parents[2]
CORE_DIR = REPO_ROOT / "core"
DEFAULT_REPO = "https://github.com/n30j0su3/Model-Agnostic-AI-Personal-Assistant-Framework-PreAlpha"
VERSION_PATH = REPO_ROOT / "VERSION"
UPDATE_PROTECTED_PATHS_FILE = REPO_ROOT / "config" / "update-protected-paths.txt"
BACKUP_BASE_DIR = REPO_ROOT / ".update-preservation"
EXCLUDE_ROOTS = {".context", "sessions", "workspaces", "logs"}
EXCLUDE_SUBPATHS = {
    ("agents", "custom"),
    ("skills", "custom"),
    ("core", "agents", "custom"),
    ("core", "skills", "custom"),
}

STATUS_OK = 0
STATUS_ERROR = 1
STATUS_UPDATE_AVAILABLE = 2

SEMVER_RE = re.compile(r"^v?(\d+)\.(\d+)\.(\d+)(?:-([0-9A-Za-z.-]+))?$")


def parse_version(version_text):
    cleaned = version_text.strip().lstrip("v")
    match = SEMVER_RE.match(cleaned)
    if not match:
        return cleaned, ()

    major, minor, patch, prerelease = match.groups()
    base = (int(major), int(minor), int(patch))

    if prerelease is None:
        return cleaned, base + (1, ())

    prerelease_parts = []
    for part in prerelease.split("."):
        if part.isdigit():
            prerelease_parts.append((0, int(part)))
        else:
            prerelease_parts.append((1, part))

    return cleaned, base + (0, tuple(prerelease_parts))


def read_local_version():
    if not VERSION_PATH.exists():
        return "", ()
    return parse_version(VERSION_PATH.read_text(encoding="utf-8"))


def normalize_repo_url(url):
    if not url:
        return DEFAULT_REPO
    if url.endswith(".git"):
        url = url[: -len(".git")]
    if url.startswith("git@"):
        try:
            host_repo = url.split("@", 1)[1]
            host, repo = host_repo.split(":", 1)
            return f"https://{host}/{repo}"
        except ValueError:
            return DEFAULT_REPO
    if url.startswith("https://") or url.startswith("http://"):
        return url
    return DEFAULT_REPO


def detect_repo_url():
    if (REPO_ROOT / ".git").exists() and shutil.which("git"):
        try:
            result = subprocess.run(
                ["git", "config", "--get", "remote.origin.url"],
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode == 0:
                return normalize_repo_url(result.stdout.strip())
        except Exception:
            return DEFAULT_REPO
    return DEFAULT_REPO


def build_raw_version_url(repo_url):
    if repo_url.startswith("https://github.com/"):
        path = repo_url.split("https://github.com/", 1)[1].strip("/")
        return f"https://raw.githubusercontent.com/{path}/main/VERSION"
    return f"{repo_url.rstrip('/')}/raw/main/VERSION"


def build_zip_url(repo_url):
    return f"{repo_url.rstrip('/')}/archive/refs/heads/main.zip"


def fetch_remote_version(url):
    """Fetch version from URL with fallback to default repo."""
    try:
        with urllib.request.urlopen(url, timeout=15) as response:
            data = response.read().decode("utf-8").strip()
        return parse_version(data)
    except Exception as exc:
        # Try fallback to default public repo
        if url != build_raw_version_url(DEFAULT_REPO):
            print(f"[WARN] No se pudo obtener version desde {url}: {exc}")
            print(f"[INFO] Intentando con repositorio publico por defecto...")
            try:
                fallback_url = build_raw_version_url(DEFAULT_REPO)
                with urllib.request.urlopen(fallback_url, timeout=15) as response:
                    data = response.read().decode("utf-8").strip()
                return parse_version(data)
            except Exception as fallback_exc:
                print(f"[ERROR] No se pudo obtener la version remota: {fallback_exc}")
                return "", ()
        else:
            print(f"[ERROR] No se pudo obtener la version remota: {exc}")
            return "", ()


def fetch_remote_version_via_git(remote="origin", branch="main"):
    if not (REPO_ROOT / ".git").exists() or not shutil.which("git"):
        return "", ()

    try:
        subprocess.run(
            ["git", "fetch", remote, branch, "--quiet"],
            cwd=REPO_ROOT,
            capture_output=True,
            check=False,
        )
        show_result = subprocess.run(
            ["git", "show", f"{remote}/{branch}:VERSION"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        if show_result.returncode == 0:
            return parse_version(show_result.stdout.strip())
    except Exception as exc:
        print(f"[WARN] No se pudo leer VERSION remota via git: {exc}")

    return "", ()


def is_update_available(local_tuple, remote_tuple):
    if not local_tuple or not remote_tuple:
        return False
    return remote_tuple > local_tuple


def prompt_yes_no(message, default=False):
    suffix = "[s/N]" if not default else "[S/n]"
    choice = input(f"{message} {suffix}: ").strip().lower()
    if not choice:
        return default
    return choice in {"s", "si", "y", "yes"}


def create_snapshot() -> Path | None:
    """Create one rollback-compatible snapshot before any update write."""
    try:
        from migrate import create_pre_migration_snapshot

        snapshot = create_pre_migration_snapshot(REPO_ROOT)
        manifest_path = snapshot / "manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if manifest.get("schema") != 1 or not isinstance(manifest.get("roots"), list):
            raise ValueError("snapshot manifest invalido")
        print(f"[INFO] Snapshot pre-update creado en: {snapshot}")
        return snapshot
    except Exception as exc:
        print(f"[ERROR] No se pudo crear snapshot: {exc}")
        return None


def load_update_protected_paths() -> list[str]:
    defaults = [
        "workspaces",
        "data/user",
        "data/sessions.db",
        "data/user_memory.db",
        "core/.context/MASTER.md",
        "core/.context/profile.md",
        "core/.context/opencode.md",
        "core/.context/claude.md",
        "core/.context/gemini.md",
        "core/.context/sessions",
        "core/.context/codebase",
        "core/.context/backups",
        "core/.context/projects",
        "core/.context/vitals",
        "core/.context/knowledge/insights",
        "core/.context/knowledge/learning",
        "core/.context/knowledge/self-healing",
        "core/.context/knowledge/prompts",
        "config/mcp.json",
        "config/quotas.json",
        "opencode.jsonc",
        ".opencode/config.json",
    ]
    if not UPDATE_PROTECTED_PATHS_FILE.exists():
        return defaults
    lines = [
        line.strip().rstrip("/")
        for line in UPDATE_PROTECTED_PATHS_FILE.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]
    return lines or defaults


def is_protected_update_path(rel_path: Path, protected_paths: list[str]) -> bool:
    normalized = rel_path.as_posix().rstrip("/")
    for protected in protected_paths:
        protected_norm = protected.replace("\\", "/").rstrip("/")
        if normalized == protected_norm or normalized.startswith(protected_norm + "/"):
            return True
    return False


def backup_protected_update_paths(protected_paths: list[str]) -> Path:
    backup_dir = BACKUP_BASE_DIR / datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_dir.mkdir(parents=True, exist_ok=True)
    manifest = {"created_at": datetime.now().isoformat(), "paths": []}

    for rel in protected_paths:
        src = REPO_ROOT / rel
        if not src.exists():
            continue
        dst = backup_dir / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        if src.is_dir():
            shutil.copytree(src, dst, dirs_exist_ok=True)
        else:
            shutil.copy2(src, dst)
        manifest["paths"].append(rel)

    (backup_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return backup_dir


def restore_protected_update_paths(backup_dir: Path) -> bool:
    if not backup_dir.exists():
        return True
    manifest_path = backup_dir / "manifest.json"
    if not manifest_path.exists():
        return False
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    for rel in manifest.get("paths", []):
        src = backup_dir / rel
        dst = REPO_ROOT / rel
        if not src.exists():
            continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        if src.is_dir():
            shutil.copytree(src, dst, dirs_exist_ok=True)
        else:
            shutil.copy2(src, dst)
    return True


def reset_tracked_protected_paths_for_git(protected_paths: list[str]) -> bool:
    if not shutil.which("git"):
        return True

    ok = True
    for rel in protected_paths:
        tracked = subprocess.run(
            ["git", "ls-files", "--error-unmatch", rel],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        if tracked.returncode != 0:
            continue

        checkout = subprocess.run(
            ["git", "checkout", "--", rel],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        if checkout.returncode != 0:
            print(
                f"[WARN] No se pudo limpiar temporalmente el path protegido para git pull: {rel}"
            )
            ok = False
    return ok


def run_migrations() -> bool:
    script_path = CORE_DIR / "scripts" / "migrate.py"
    if not script_path.exists():
        print("[ERROR] Script requerido no encontrado: core/scripts/migrate.py")
        return False
    result = subprocess.run(
        [sys.executable, str(script_path), "--apply"], cwd=REPO_ROOT
    )
    return result.returncode == 0


def run_kb_init() -> bool:
    script_path = CORE_DIR / "scripts" / "kb_init.py"
    if not script_path.exists():
        print("[ERROR] Script requerido no encontrado: core/scripts/kb_init.py")
        return False
    result = subprocess.run(
        [sys.executable, str(script_path), "--force"], cwd=REPO_ROOT
    )
    return result.returncode == 0


def should_skip(rel_path, protected_paths=None):
    if not rel_path.parts:
        return False
    if rel_path.parts[0] in EXCLUDE_ROOTS:
        return True
    if protected_paths and is_protected_update_path(rel_path, protected_paths):
        return True
    for excluded in EXCLUDE_SUBPATHS:
        length = len(excluded)
        if len(rel_path.parts) >= length and rel_path.parts[:length] == excluded:
            return True
    return False


def copy_tree(source_root, target_root, protected_paths=None):
    for root, dirs, files in os.walk(source_root):
        rel_root = Path(root).relative_to(source_root)
        if should_skip(rel_root, protected_paths):
            dirs[:] = []
            continue
        for dirname in list(dirs):
            if should_skip(rel_root / dirname, protected_paths):
                dirs.remove(dirname)
        for filename in files:
            rel_file = rel_root / filename
            if should_skip(rel_file, protected_paths):
                continue
            source_file = Path(root) / filename
            target_file = target_root / rel_file
            target_file.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source_file, target_file)


def update_with_git(protected_paths):
    reset_tracked_protected_paths_for_git(protected_paths)
    result = subprocess.run(["git", "pull", "--ff-only"], cwd=REPO_ROOT)
    if result.returncode != 0:
        print("[ERROR] Git pull fallo. Revisa tu repositorio.")
        return False
    return True


def try_requests_download(zip_url, zip_path):
    """Intenta descargar con requests library (opcional)."""
    try:
        import requests

        print("[INFO] Intentando con requests library...")
        response = requests.get(zip_url, timeout=30)
        response.raise_for_status()
        zip_path.write_bytes(response.content)
        return True
    except ImportError:
        print("[INFO] requests no instalado (opcional)")
        return False
    except Exception as e:
        print(f"[INFO] requests fallo: {e}")
        return False


def try_urllib_download(zip_url, zip_path):
    """Download using urllib with normal certificate verification."""
    try:
        import urllib.request

        print("[INFO] Intentando con urllib (SSL=ON)...")
        with urllib.request.urlopen(zip_url, timeout=30) as response:
            zip_path.write_bytes(response.read())

        return True

    except Exception as e:
        print(f"[INFO] urllib fallo: {e}")
        return False


def _extract_validated_zip(zip_path: Path, destination: Path) -> Path:
    """Validate every archive member before extracting one rooted tree."""
    destination.mkdir(parents=True, exist_ok=True)
    destination_resolved = destination.resolve()
    top_levels = set()
    with zipfile.ZipFile(zip_path) as archive:
        infos = archive.infolist()
        if not infos:
            raise ValueError("ZIP vacio")
        for info in infos:
            normalized = info.filename.replace("\\", "/")
            relative = PurePosixPath(normalized)
            parts = relative.parts
            if (
                not parts
                or relative.is_absolute()
                or any(part in {".", ".."} for part in parts)
                or (len(parts[0]) >= 2 and parts[0][1] == ":")
            ):
                raise ValueError(f"ruta ZIP insegura: {info.filename!r}")
            mode = info.external_attr >> 16
            if stat.S_ISLNK(mode):
                raise ValueError(f"symlink ZIP no permitido: {info.filename!r}")
            target = (destination / Path(*parts)).resolve()
            if target != destination_resolved and destination_resolved not in target.parents:
                raise ValueError(f"ruta ZIP fuera de staging: {info.filename!r}")
            top_levels.add(parts[0])
        bad_member = archive.testzip()
        if bad_member is not None:
            raise ValueError(f"CRC ZIP invalido: {bad_member!r}")
        if len(top_levels) != 1:
            raise ValueError("ZIP debe contener un unico directorio raiz")
        archive.extractall(destination)

    source_root = destination / next(iter(top_levels))
    if not source_root.is_dir():
        raise ValueError("directorio raiz ZIP inexistente")
    return source_root


def update_with_zip(zip_url, protected_paths):
    """Download over verified TLS, validate, and apply one rooted ZIP."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        zip_path = tmp_path / "update.zip"

        # MÉTODO 1: Intentar con requests (si esta disponible)
        if try_requests_download(zip_url, zip_path):
            print("[OK] Descarga completada con requests")
        # MÉTODO 2: Intentar con urllib estandar
        elif try_urllib_download(zip_url, zip_path):
            print("[OK] Descarga completada con verificacion SSL")
        else:
            print("[ERROR] Descarga cancelada: no hay conexion TLS verificada.")
            print(f"[INFO] Descarga manualmente y verifica el release oficial: {zip_url}")
            return False

        try:
            source_root = _extract_validated_zip(zip_path, tmp_path / "extracted")
        except Exception as exc:
            print(f"[ERROR] No se pudo extraer el zip: {exc}")
            return False
        copy_tree(source_root, REPO_ROOT, protected_paths)
    return True


def run_update(force=False, check_only=False):
    repo_url = detect_repo_url()
    raw_url = build_raw_version_url(repo_url)
    zip_url = build_zip_url(repo_url)
    local_text, local_tuple = read_local_version()
    remote_text, remote_tuple = fetch_remote_version_via_git()
    remote_source = "git origin/main"
    if not remote_text:
        remote_text, remote_tuple = fetch_remote_version(raw_url)
        remote_source = raw_url

    if not remote_text:
        return STATUS_ERROR

    print(f"[INFO] Version local: {local_text or 'N/D'}")
    print(f"[INFO] Version remota: {remote_text}")
    print(f"[INFO] Fuente remota: {remote_source}")

    if not local_tuple:
        print("[WARN] VERSION local no valido o inexistente.")
    if not remote_tuple:
        print("[WARN] VERSION remota no valida.")
        if check_only:
            return STATUS_ERROR

    update_available = is_update_available(local_tuple, remote_tuple)

    # Modo check-only: solo verificar sin aplicar
    if check_only:
        if update_available:
            print("[INFO] Hay una nueva version disponible.")
            return STATUS_UPDATE_AVAILABLE
        else:
            print("[OK] Framework actualizado.")
            return STATUS_OK

    if not update_available and not force:
        print("[OK] Framework actualizado.")
        return STATUS_OK

    if update_available:
        print("[INFO] Hay una nueva version disponible.")
    if not force and not prompt_yes_no("Actualizar ahora?", default=False):
        print("[INFO] Actualizacion cancelada.")
        return STATUS_OK

    if not create_snapshot():
        print("[ERROR] Actualizacion cancelada: snapshot requerido.")
        return STATUS_ERROR

    protected_paths = load_update_protected_paths()
    backup_dir = backup_protected_update_paths(protected_paths)
    print(f"[INFO] Backup de preservacion creado en: {backup_dir}")

    if (REPO_ROOT / ".git").exists() and shutil.which("git"):
        print("[INFO] Metodo de actualizacion: Git")
        success = update_with_git(protected_paths)
        if success:
            if not restore_protected_update_paths(backup_dir):
                print("[ERROR] No se pudo restaurar el estado protegido del usuario.")
                return STATUS_ERROR
            if not run_migrations():
                print("[ERROR] Las migraciones post-update fallaron.")
                return STATUS_ERROR
            if not run_kb_init():
                print(
                    "[ERROR] La inicializacion de Knowledge Base fallo tras la actualizacion."
                )
                return STATUS_ERROR
            return STATUS_OK
        restore_protected_update_paths(backup_dir)
        return STATUS_ERROR

    print("[INFO] Metodo de actualizacion: Descarga directa")
    success = update_with_zip(zip_url, protected_paths)
    if success:
        if not restore_protected_update_paths(backup_dir):
            print("[ERROR] No se pudo restaurar el estado protegido del usuario.")
            return STATUS_ERROR
        if not run_migrations():
            print("[ERROR] Las migraciones post-update fallaron.")
            return STATUS_ERROR
        if not run_kb_init():
            print(
                "[ERROR] La inicializacion de Knowledge Base fallo tras la actualizacion."
            )
            return STATUS_ERROR
        return STATUS_OK
    restore_protected_update_paths(backup_dir)
    return STATUS_ERROR


def main():
    parser = argparse.ArgumentParser(description="Actualizador del framework")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Forzar actualizacion aunque versiones coincidan",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Solo verificar si hay actualizaciones disponibles sin aplicarlas",
    )
    args = parser.parse_args()
    status = run_update(force=args.force, check_only=args.check)
    sys.exit(status)


if __name__ == "__main__":
    main()
