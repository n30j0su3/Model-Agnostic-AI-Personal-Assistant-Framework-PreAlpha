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

FORBIDDEN_DOC_GLOBS = [
    "docs/WORKFLOW-STANDARD.md",
    "docs/ASSEMBLY-LINE.md",
    "docs/PHILOSOPHY.md",
    "docs/core/PRP-*.md",
    "config/protected-dev-paths.txt",
    "README-technical.md",
    "GEMINI.md",
    "core/.context/navigation.md",
    "core/.context/knowledge/learning/*",
    "core/.context/knowledge/insights/*",
    "core/.context/knowledge/playbooks/*",
    "core/.context/knowledge/agents/*",
    "core/.context/backups/*",
    "core/.context/dev-todo/*",
    "core/.context/codebase/*",
    "core/.context/knowledge_base.json",
    "core/.context/projects/*",
    "core/.context/vitals/*",
    "core/.context/knowledge/self-healing/*",
    "core/.context/knowledge/prompts/*",
    "docs/propagation/*",
    ".opencode/commands/*",
    ".opencode/agent/pa-assistant.md",
    ".opencode/bun.lock",
    ".opencode/node_modules/*",
    "core/agents/subagents/sync-propagator.md",
]

FORBIDDEN_SCRIPTS = [
    "core/scripts/sync-prealpha.py",
    "core/scripts/assembly-line-enforcer.py",
    "core/scripts/propagate-framework-updates.py",
    "core/scripts/reference-integrity-check.py",
    "core/scripts/sync-auditor.py",
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
    "docs/FRAMEWORK-PROPAGATION-PROTOCOL.md",
    "docs/workflow-test-example.md",
]

FORBIDDEN_README_PATTERNS = [
    "repositorio de desarrollo",
    "github.com/n30j0su3/Model-Agnostic-AI-Personal-Assistant-Framework/tree/main",
]

FORBIDDEN_CONTENT_PATTERNS = [
    r"\bMaaji\b",
    r"WORKFLOW-STANDARD",
    r"Workflow Standard",
    r"ASSEMBLY-LINE",
    r"Assembly Line",
    r"SYNC-PROTOCOL",
    r"\bPRP-\d{3}\b",
    r"protected-dev-paths",
    r"Model-Agnostic-AI-Personal-Assistant-Framework-dev",
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
    print(f"{Colors.GREEN}[OK]{Colors.RESET} {msg}")


def print_err(msg: str):
    print(f"{Colors.RED}[X]{Colors.RESET} {msg}")


def print_warn(msg: str):
    print(f"{Colors.YELLOW}[!]{Colors.RESET} {msg}")


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


def check_forbidden_globs(root: Path, globs: list[str], label: str) -> int:
    errors = 0
    for pattern in globs:
        matches = list(root.glob(pattern))
        if matches:
            for match in matches[:10]:
                print_err(f"{label} prohibido existe: {match.relative_to(root)}")
            errors += len(matches)
        else:
            print_ok(f"{label} OK: {pattern}")
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


def check_forbidden_content(root: Path) -> int:
    errors = 0
    scan_suffixes = {".md", ".txt", ".json", ".yaml", ".yml"}
    excluded_parts = {".git", "Obsoleto", "__pycache__"}

    for file_path in root.rglob("*"):
        if not file_path.is_file():
            continue
        if file_path.suffix.lower() not in scan_suffixes:
            continue
        relative_parts = file_path.relative_to(root).parts
        if any(part in excluded_parts for part in relative_parts):
            continue

        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue

        for pattern in FORBIDDEN_CONTENT_PATTERNS:
            if re.search(pattern, content, re.IGNORECASE):
                print_err(
                    f"Contenido prohibido '{pattern}' en {file_path.relative_to(root)}"
                )
                errors += 1
                break

    if errors == 0:
        print_ok("Sin referencias internas prohibidas en contenido textual")
    return errors


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
    parser.add_argument(
        "--root", type=str, help="Ruta explícita a validar en lugar del repo del script"
    )
    args = parser.parse_args()

    if args.no_color or not sys.stdout.isatty():
        Colors.disable()

    root = (
        Path(args.root).resolve()
        if args.root
        else Path(__file__).resolve().parent.parent.parent
    )
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

    print("\n[2.5/5] Patrones glob de documentos internos")
    errors = check_forbidden_globs(root, FORBIDDEN_DOC_GLOBS, "Glob")
    total_errors += errors
    if errors:
        issues.append(
            "Eliminar workflow docs, PRP docs y KB interna del release público"
        )

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

    print("\n[5.5/5] Contenido textual prohibido")
    errors = check_forbidden_content(root)
    total_errors += errors
    if errors:
        issues.append(
            "Eliminar menciones internas (workflow, PRP, Maaji, rutas/proyectos internos)"
        )

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
