#!/usr/bin/env python3
"""
Validador de Sanitización Pre-Release
Verifica que el repo público esté correctamente sanitizado.

Uso:
    python core/scripts/validate-public-release.py
    python core/scripts/validate-public-release.py --fix  # Sugiere correcciones

Autor: FreakingJSON-PA Framework
Versión: 1.0.0
"""

import argparse
import re
import sys
from pathlib import Path

FORBIDDEN_SCRIPTS = [
    "core/scripts/sync-prealpha.py",
    "core/scripts/sync-prealpha-optimized.py",
    "core/scripts/sync-base-to-dev.sh",
    "core/scripts/sync-base-to-prod.sh",
    "core/scripts/sync-dev-to-base.sh",
    "core/scripts/sync-dev-safe.bat",
    "core/scripts/sync-menu.bat",
    "core/scripts/backup-critical.bat",
    "core/scripts/restore-from-backup.py",
    "core/scripts/restore-dev-resources.py",
    "core/scripts/recover-maaji.py",
    "core/scripts/validate-dev-resources.py",
    "core/scripts/vitals-remote-setup.py",
    "core/scripts/test_framework.py",
    "core/scripts/test_sync_prealpha_optimized.py",
]

FORBIDDEN_DOCS = [
    "docs/RELEASE-CHECKLIST.md",
    "docs/backlog.md",
    "docs/backlog.view.md",
    "docs/AGENT-CONFIGURATION.md",
    "docs/SYNC-PROTOCOL.md",
    "docs/workflow-test-example.md",
]

FORBIDDEN_README_PATTERNS = [
    "repositorio de desarrollo",
    "github.com/n30j0su3/Model-Agnostic-AI-Personal-Assistant-Framework/tree/main",
]

VERSION_PATTERN = re.compile(r"^\d+\.\d+\.\d+(-[a-zA-Z0-9.]+)?$")


class Colors:
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    RESET = "\033[0m"
    BOLD = "\033[1m"

    @classmethod
    def disable(cls):
        cls.GREEN = ""
        cls.RED = ""
        cls.YELLOW = ""
        cls.RESET = ""
        cls.BOLD = ""


def print_ok(msg: str):
    print(f"{Colors.GREEN}✓{Colors.RESET} {msg}")


def print_err(msg: str):
    print(f"{Colors.RED}✗{Colors.RESET} {msg}")


def print_warn(msg: str):
    print(f"{Colors.YELLOW}!{Colors.RESET} {msg}")


def print_header(msg: str):
    print(f"\n{Colors.BOLD}{'=' * 60}{Colors.RESET}")
    print(f"{Colors.BOLD}{msg}{Colors.RESET}")
    print(f"{Colors.BOLD}{'=' * 60}{Colors.RESET}")


def check_forbidden_files(root: Path, files: list[str], label: str) -> int:
    errors = 0
    for f in files:
        path = root / f
        if path.exists():
            print_err(f"{label} prohibido existe: {f}")
            errors += 1
        else:
            print_ok(f"{label} OK: {f}")
    return errors


def check_readme_patterns(root: Path) -> int:
    readme_path = root / "README.md"
    if not readme_path.exists():
        print_err("README.md no existe")
        return 1

    content = readme_path.read_text(encoding="utf-8").lower()
    errors = 0
    for pattern in FORBIDDEN_README_PATTERNS:
        if pattern.lower() in content:
            print_err(f"Patrón prohibido en README: '{pattern}'")
            errors += 1
        else:
            print_ok(f"README sin patrón: '{pattern[:30]}...'")
    return errors


def check_version_file(root: Path) -> tuple[int, str | None]:
    version_path = root / "VERSION"
    if not version_path.exists():
        print_err("VERSION no existe")
        return 1, None

    version = version_path.read_text(encoding="utf-8").strip()
    if not VERSION_PATTERN.match(version):
        print_err(f"VERSION formato inválido: '{version}' (esperado: X.Y.Z)")
        return 1, None

    print_ok(f"VERSION válido: {version}")
    return 0, version


def check_changelog(root: Path, version: str) -> int:
    changelog_path = root / "CHANGELOG.md"
    if not changelog_path.exists():
        print_err("CHANGELOG.md no existe")
        return 1

    content = changelog_path.read_text(encoding="utf-8")
    version_pattern = re.compile(rf"^##\s+\[?{re.escape(version)}\]?", re.MULTILINE)

    if version_pattern.search(content):
        print_ok(f"CHANGELOG tiene entrada para v{version}")
        return 0
    else:
        print_err(f"CHANGELOG falta entrada para v{version}")
        return 1


def suggest_fixes(issues: list[str]):
    print_header("SUGERENCIAS DE CORRECCIÓN")
    for issue in issues:
        print(f"  • {issue}")


def main():
    parser = argparse.ArgumentParser(
        description="Valida sanitización del repo público antes de releases"
    )
    parser.add_argument(
        "--fix", action="store_true", help="Sugiere correcciones para problemas"
    )
    parser.add_argument(
        "--no-color", action="store_true", help="Desactiva colores en output"
    )
    args = parser.parse_args()

    if args.no_color or not sys.stdout.isatty():
        Colors.disable()

    root = Path(__file__).resolve().parent.parent.parent
    total_errors = 0
    issues = []

    print_header("VALIDACIÓN PRE-RELEASE")

    print("\n[1/5] Scripts internos prohibidos")
    errors = check_forbidden_files(root, FORBIDDEN_SCRIPTS, "Script")
    total_errors += errors
    if errors:
        issues.append("Eliminar scripts de sincronización interna prohibidos")

    print("\n[2/5] Documentos internos prohibidos")
    errors = check_forbidden_files(root, FORBIDDEN_DOCS, "Doc")
    total_errors += errors
    if errors:
        issues.append("Eliminar documentos internos prohibidos")

    print("\n[3/5] Patrones en README.md")
    errors = check_readme_patterns(root)
    total_errors += errors
    if errors:
        issues.append("Actualizar README.md para público (sin referencias a repo dev)")

    print("\n[4/5] Archivo VERSION")
    errors, version = check_version_file(root)
    total_errors += errors
    if errors:
        issues.append("Crear VERSION con formato semántico (X.Y.Z)")

    print("\n[5/5] CHANGELOG.md")
    if version:
        errors = check_changelog(root, version)
        total_errors += errors
        if errors:
            issues.append(f"Añadir entrada en CHANGELOG.md para v{version}")

    print_header("RESULTADO")

    if total_errors == 0:
        print_ok(f"Repo sanitizado correctamente - listo para release")
        return 0
    else:
        print_err(f"{total_errors} problema(s) encontrado(s)")
        if args.fix and issues:
            suggest_fixes(issues)
        return 1


if __name__ == "__main__":
    sys.exit(main())
