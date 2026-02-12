#!/usr/bin/env python3
"""
Framework Test Suite - Validación de scripts y skills

Uso:
    python test_framework.py              # Test completo
    python test_framework.py --quick      # Test rápido (scripts core)
    python test_framework.py --skills     # Solo skills
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path


def find_repo_root():
    """Encuentra la raíz del repo."""
    script_path = Path(__file__).resolve()
    for candidate in [script_path.parent] + list(script_path.parents):
        if (candidate / "core" / ".context").exists():
            return candidate
    return None


def test_script_syntax(script_path):
    """Testea sintaxis de un script Python."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "py_compile", str(script_path)],
            capture_output=True,
            text=True,
            timeout=10,
        )
        return result.returncode == 0, result.stderr
    except Exception as e:
        return False, str(e)


def test_cross_platform(script_path):
    """Verifica que no haya emojis en el script."""
    content = script_path.read_text(encoding="utf-8")
    emojis_found = []

    # Caracteres comunes de emojis (simplificado)
    for char in content:
        if ord(char) > 127 and not char.isalpha() and not char.isdigit():
            if char not in [
                "\n",
                "\r",
                "\t",
                " ",
                '"',
                "'",
                "(",
                ")",
                "[",
                "]",
                "{",
                "}",
                ":",
                ";",
                ",",
                ".",
                "+",
                "-",
                "*",
                "/",
                "=",
                "<",
                ">",
                "!",
                "?",
                "@",
                "#",
                "$",
                "%",
                "^",
                "&",
                "|",
                "~",
                "`",
                "_",
                "\\",
            ]:
                emojis_found.append(char)

    # Limitar a los primeros 10 para no saturar
    emojis_found = list(set(emojis_found))[:10]
    return len(emojis_found) == 0, emojis_found


def discover_scripts(repo_root):
    """Descubre todos los scripts Python del framework."""
    scripts = {"core": [], "skills": []}

    core_scripts_dir = repo_root / "core" / "scripts"
    skills_dir = repo_root / "core" / "skills"

    # Scripts core
    if core_scripts_dir.exists():
        for script in core_scripts_dir.glob("*.py"):
            scripts["core"].append(script)

    # Scripts de skills
    if skills_dir.exists():
        for script in skills_dir.rglob("scripts/*.py"):
            scripts["skills"].append(script)

    return scripts


def run_tests(repo_root, quick=False, skills_only=False):
    """Ejecuta tests."""
    print("=" * 70)
    print("FRAMEWORK TEST SUITE")
    print("=" * 70)
    print(f"Repo: {repo_root}")
    print(f"Mode: {'Quick' if quick else 'Full'}")
    print("=" * 70)

    scripts = discover_scripts(repo_root)

    if quick:
        # Solo scripts core
        test_scripts = scripts["core"]
    elif skills_only:
        # Solo skills
        test_scripts = scripts["skills"]
    else:
        # Todos
        test_scripts = scripts["core"] + scripts["skills"]

    results = {"passed": 0, "failed": 0, "emoji_issues": 0, "errors": []}

    print(f"\n[TEST] Validando {len(test_scripts)} scripts...\n")

    for script in sorted(test_scripts):
        rel_path = script.relative_to(repo_root)
        print(f"Testing: {rel_path}", end=" ")

        # Test de sintaxis
        syntax_ok, syntax_err = test_script_syntax(script)

        # Test cross-platform (emojis)
        cross_ok, emojis = test_cross_platform(script)

        if syntax_ok and cross_ok:
            print("[OK]")
            results["passed"] += 1
        else:
            print("[FAIL]")
            results["failed"] += 1

            if not syntax_ok:
                results["errors"].append(f"{rel_path}: Syntax error - {syntax_err}")

            if not cross_ok:
                results["emoji_issues"] += 1
                results["errors"].append(f"{rel_path}: Emoji found - {emojis}")

    # Resumen
    print("\n" + "=" * 70)
    print("RESUMEN")
    print("=" * 70)
    print(f"Total scripts: {len(test_scripts)}")
    print(f"Passed: {results['passed']}")
    print(f"Failed: {results['failed']}")
    print(f"Emoji issues: {results['emoji_issues']}")

    if results["errors"]:
        print("\n[ERRORES]")
        for error in results["errors"][:10]:
            print(f"  - {error}")
        if len(results["errors"]) > 10:
            print(f"  ... y {len(results['errors']) - 10} más")

    print("=" * 70)

    return results["failed"] == 0


def main():
    parser = argparse.ArgumentParser(description="Framework Test Suite")
    parser.add_argument("--quick", action="store_true", help="Test rápido (solo core)")
    parser.add_argument("--skills", action="store_true", help="Solo skills")
    args = parser.parse_args()

    repo_root = find_repo_root()
    if not repo_root:
        print("[ERROR] No se encontró la raíz del repositorio")
        sys.exit(1)

    success = run_tests(repo_root, quick=args.quick, skills_only=args.skills)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
