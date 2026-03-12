#!/usr/bin/env python3
import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.request
import zipfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
CORE_DIR = REPO_ROOT / "core"
DEFAULT_REPO = "https://github.com/n30j0su3/Model-Agnostic-AI-Personal-Assistant-Framework-PreAlpha"
VERSION_PATH = REPO_ROOT / "VERSION"
EXCLUDE_ROOTS = {".context", "sessions", "workspaces", "config", "logs"}
EXCLUDE_SUBPATHS = {
    ("agents", "custom"),
    ("skills", "custom"),
    ("core", ".context"),
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


def create_snapshot():
    script_path = CORE_DIR / "scripts" / "context-version.py"
    if not script_path.exists():
        return True
    try:
        result = subprocess.run(
            [sys.executable, str(script_path), "snapshot"], cwd=REPO_ROOT
        )
        return result.returncode == 0
    except Exception as exc:
        print(f"[WARN] No se pudo crear snapshot: {exc}")
        return False


def should_skip(rel_path):
    if not rel_path.parts:
        return False
    if rel_path.parts[0] in EXCLUDE_ROOTS:
        return True
    for excluded in EXCLUDE_SUBPATHS:
        length = len(excluded)
        if len(rel_path.parts) >= length and rel_path.parts[:length] == excluded:
            return True
    return False


def copy_tree(source_root, target_root):
    for root, dirs, files in os.walk(source_root):
        rel_root = Path(root).relative_to(source_root)
        if should_skip(rel_root):
            dirs[:] = []
            continue
        for dirname in list(dirs):
            if should_skip(rel_root / dirname):
                dirs.remove(dirname)
        for filename in files:
            rel_file = rel_root / filename
            if should_skip(rel_file):
                continue
            source_file = Path(root) / filename
            target_file = target_root / rel_file
            target_file.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source_file, target_file)


def update_with_git():
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


def try_urllib_download(zip_url, zip_path, verify_ssl=True):
    """Intenta descargar con urllib, con o sin SSL."""
    try:
        import ssl
        import urllib.request

        print(f"[INFO] Intentando con urllib (SSL={'ON' if verify_ssl else 'OFF'})...")

        if verify_ssl:
            # SSL normal
            with urllib.request.urlopen(zip_url, timeout=30) as response:
                zip_path.write_bytes(response.read())
        else:
            # SSL desactivado (fallback)
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE

            req = urllib.request.Request(zip_url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(
                req, timeout=30, context=ssl_context
            ) as response:
                zip_path.write_bytes(response.read())

        return True

    except Exception as e:
        print(f"[INFO] urllib fallo: {e}")
        return False


def install_certifi():
    """Intenta instalar certificados SSL."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "--upgrade", "certifi"],
            capture_output=True,
            text=True,
            timeout=60,
        )
        if result.returncode == 0:
            print("[OK] certifi instalado correctamente")
            return True
        else:
            print(f"[ERROR] pip fallo: {result.stderr}")
            return False
    except Exception as e:
        print(f"[ERROR] No se pudo ejecutar pip: {e}")
        return False


def update_with_zip(zip_url):
    """Descarga y aplica actualizacion desde ZIP con opciones de usuario."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        zip_path = tmp_path / "update.zip"

        # MÉTODO 1: Intentar con requests (si esta disponible)
        if try_requests_download(zip_url, zip_path):
            print("[OK] Descarga completada con requests")
        # MÉTODO 2: Intentar con urllib estandar
        elif try_urllib_download(zip_url, zip_path, verify_ssl=True):
            print("[OK] Descarga completada con verificacion SSL")
        # MÉTODO 3: Preguntar al usuario sobre opciones SSL
        else:
            print("\n" + "=" * 60)
            print("[INFO] No se pudo descargar con verificacion SSL.")
            print("Esto es comun en Windows con Python recien instalado.")
            print("=" * 60 + "\n")

            print("El usuario SIEMPRE tiene el control.")
            print("El framework NUNCA decide por ti. TU eliges como proceder.\n")

            print("Opciones disponibles:")
            print("  [1] Intentar sin verificacion SSL (funciona inmediatamente)")
            print("        - Menos seguro pero descarga desde GitHub igual")
            print("  [2] Instalar certificados SSL (solucion permanente)")
            print("        - Ejecuta: pip install --upgrade certifi")
            print("        - Luego reintenta la actualizacion")
            print("  [3] Descargar manualmente")
            print("        - Abre el navegador con el enlace del ZIP")
            print("        - Extrae manualmente en la carpeta del framework")
            print("  [c] Cancelar y salir")
            print()

            choice = input("Elige una opcion [1/2/3/c]: ").strip().lower()

            if choice == "1":
                print("[INFO] Intentando descarga sin verificacion SSL...")
                if try_urllib_download(zip_url, zip_path, verify_ssl=False):
                    print("[OK] Descarga completada (modo compatibilidad)")
                    print("[WARN] Recuerda: Esto es seguro para GitHub, pero")
                    print("        considera instalar certificados SSL despues.")
                else:
                    print("[ERROR] Aun fallo. Intenta opcion 2 o 3.")
                    return False

            elif choice == "2":
                print("[INFO] Instalando certificados SSL...")
                if install_certifi():
                    print("[OK] Certificados instalados. Reintentando...")
                    # Recursivo - vuelve a intentar todo
                    return update_with_zip(zip_url)
                else:
                    print("[ERROR] No se pudieron instalar certificados.")
                    retry = input("¿Intentar sin verificacion SSL? [s/N]: ")
                    if retry.lower() in ("s", "si", "y", "yes"):
                        return try_urllib_download(zip_url, zip_path, verify_ssl=False)
                    return False

            elif choice == "3":
                print(f"\n[INFO] Abriendo navegador con: {zip_url}")
                print("[INFO] Despues de descargar, extrae el ZIP manualmente")
                print("       en: {}".format(REPO_ROOT))
                import webbrowser

                webbrowser.open(zip_url)
                return False  # No automatico, usuario continua manual

            else:
                print("[INFO] Actualizacion cancelada.")
                return False

        try:
            with zipfile.ZipFile(zip_path) as zip_ref:
                zip_ref.extractall(tmp_path)
        except Exception as exc:
            print(f"[ERROR] No se pudo extraer el zip: {exc}")
            return False

        extracted_dirs = [path for path in tmp_path.iterdir() if path.is_dir()]
        if not extracted_dirs:
            print("[ERROR] Zip sin contenido valido.")
            return False
        source_root = extracted_dirs[0]
        copy_tree(source_root, REPO_ROOT)
    return True


def run_vendor_assets():
    script_path = CORE_DIR / "scripts" / "vendor_assets.py"
    if not script_path.exists():
        return True
    result = subprocess.run([sys.executable, str(script_path)], cwd=REPO_ROOT)
    if result.returncode != 0:
        print(
            "[WARN] Descarga de assets fallida. Ejecuta core/scripts/vendor_assets.py manualmente."
        )
        return False
    return True


def run_docs_manifest():
    script_path = CORE_DIR / "scripts" / "generate_docs_index.py"
    if not script_path.exists():
        return True
    result = subprocess.run([sys.executable, str(script_path)], cwd=REPO_ROOT)
    if result.returncode != 0:
        print("[WARN] Generacion de docs_manifest fallida.")
        return False
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
        run_vendor_assets()
        run_docs_manifest()
        return STATUS_OK

    if update_available:
        print("[INFO] Hay una nueva version disponible.")
    if not force and not prompt_yes_no("Actualizar ahora?", default=False):
        print("[INFO] Actualizacion cancelada.")
        return STATUS_OK

    if not create_snapshot():
        if force:
            print("[WARN] No se pudo crear snapshot. Continuando por --force.")
        elif not prompt_yes_no("Continuar sin snapshot?", default=False):
            print("[INFO] Actualizacion cancelada.")
            return STATUS_OK

    if (REPO_ROOT / ".git").exists() and shutil.which("git"):
        print("[INFO] Metodo de actualizacion: Git")
        success = update_with_git()
        if success:
            run_vendor_assets()
            run_docs_manifest()
            return STATUS_OK
        return STATUS_ERROR

    print("[INFO] Metodo de actualizacion: Descarga directa")
    success = update_with_zip(zip_url)
    if success:
        run_vendor_assets()
        run_docs_manifest()
        # Initialize Knowledge Base after update (sesion 2026-03-09)
        kb_init = CORE_DIR / "scripts" / "kb-init.py"
        if kb_init.exists():
            print("[INFO] Inicializando Knowledge Base...")
            subprocess.run(
                [sys.executable, str(kb_init), "--force"], cwd=REPO_ROOT, check=False
            )
        return STATUS_OK
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
