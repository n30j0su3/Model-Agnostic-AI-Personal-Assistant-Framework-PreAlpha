#!/usr/bin/env python3
"""
Script Checker - Valida scripts Python contra estándares cross-platform.

Uso:
    python check_script.py <archivo.py> [--fix-suggestions]

Ejemplos:
    python check_script.py ../csv-processor/scripts/csv_processor.py
    python check_script.py ../../scripts/pa.py --fix-suggestions
    python check_script.py . --recursive  # Todos los .py en directorio
"""

import argparse
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple


class Issue:
    """Representa un problema encontrado en el código."""

    def __init__(self, line: int, col: int, severity: str, code: str, message: str):
        self.line = line
        self.col = col
        self.severity = severity  # 'ERROR', 'WARNING', 'INFO'
        self.code = code
        self.message = message

    def __str__(self) -> str:
        return f"{self.severity}: Line {self.line}, Col {self.col} - {self.code}: {self.message}"


class ScriptChecker:
    """Validador de scripts Python para estándares cross-platform."""

    # Emojis comunes que causan problemas en Windows
    EMOJI_PATTERN = re.compile(
        r"[\U0001F600-\U0001F64F"  # Emoticons
        r"\U0001F300-\U0001F5FF"  # Misc symbols
        r"\U0001F680-\U0001F6FF"  # Transport/map
        r"\U0001F1E0-\U0001F1FF"  # Flags
        r"\U00002702-\U000027B0"  # Dingbats
        r"\U000024C2-\U0001F251"  # Enclosed chars
        r"]+",
        re.UNICODE,
    )

    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        self.issues: List[Issue] = []
        self.lines: List[str] = []
        self.content: str = ""

        # Leer archivo
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                self.content = f.read()
                self.lines = self.content.split("\n")
        except Exception as e:
            self.issues.append(
                Issue(0, 0, "ERROR", "READ_ERROR", f"Error leyendo archivo: {e}")
            )

    def check_all(self) -> List[Issue]:
        """Ejecuta todas las validaciones."""
        self.check_shebang()
        self.check_encoding_in_open()
        self.check_emojis_in_prints()
        self.check_emojis_in_strings()
        self.check_path_concatenation()
        self.check_import_order()
        self.check_line_endings()

        return self.issues

    def check_shebang(self) -> None:
        """Verifica que el archivo tenga shebang correcto."""
        if not self.lines:
            return

        first_line = self.lines[0] if self.lines else ""

        # Verificar si es un script ejecutable (no módulo)
        if first_line.startswith("#!"):
            if "python" not in first_line.lower():
                self.issues.append(
                    Issue(
                        1,
                        0,
                        "WARNING",
                        "BAD_SHEBANG",
                        f"Shebang no estándar: {first_line}",
                    )
                )
            elif "env" not in first_line:
                self.issues.append(
                    Issue(
                        1,
                        0,
                        "INFO",
                        "SHEBANG_STYLE",
                        "Usar '#!/usr/bin/env python3' para mejor portabilidad",
                    )
                )
        elif self.file_path.name != "__init__.py":
            # No es obligatorio para módulos, pero sí para scripts
            self.issues.append(
                Issue(
                    1,
                    0,
                    "INFO",
                    "MISSING_SHEBANG",
                    "Considerar agregar shebang '#!/usr/bin/env python3' para scripts ejecutables",
                )
            )

    def check_encoding_in_open(self) -> None:
        """Verifica que open() tenga encoding='utf-8'."""
        open_pattern = re.compile(
            r'open\s*\(\s*[^,]+(?:,\s*[\'"]r[\'"])?\s*\)', re.MULTILINE
        )

        for i, line in enumerate(self.lines, 1):
            if "open(" in line and "encoding" not in line:
                # Verificar que no sea un comentario
                if not line.strip().startswith("#"):
                    self.issues.append(
                        Issue(
                            i,
                            line.find("open("),
                            "WARNING",
                            "MISSING_ENCODING",
                            "open() sin encoding='utf-8'. Usar: open(file, encoding='utf-8')",
                        )
                    )

    def check_emojis_in_prints(self) -> None:
        """Verifica emojis en statements de print."""
        print_pattern = re.compile(r"print\s*\((.*)\)")

        for i, line in enumerate(self.lines, 1):
            match = print_pattern.search(line)
            if match:
                content = match.group(1)
                if self.EMOJI_PATTERN.search(content):
                    self.issues.append(
                        Issue(
                            i,
                            match.start(),
                            "ERROR",
                            "EMOJI_IN_PRINT",
                            "Emoji detectado en print(). Usar prefijos ASCII: [OK], [ERROR], [WARN], [INFO]",
                        )
                    )

    def check_emojis_in_strings(self) -> None:
        """Verifica emojis en strings que podrían ir a consola."""
        # Buscar emojis en cualquier string
        for i, line in enumerate(self.lines, 1):
            # Ignorar comentarios
            code = line.split("#")[0]

            # Buscar emojis
            if self.EMOJI_PATTERN.search(code):
                # Verificar si es un raise, logging, o mensaje de error
                if any(
                    kw in code.lower()
                    for kw in ["raise", "exception", "error", "warn", "log"]
                ):
                    self.issues.append(
                        Issue(
                            i,
                            self.EMOJI_PATTERN.search(code).start(),
                            "WARNING",
                            "EMOJI_IN_MESSAGE",
                            "Emoji en mensaje de error/warning. Considerar usar ASCII para compatibilidad",
                        )
                    )

    def check_path_concatenation(self) -> None:
        """Verifica concatenación de paths con strings."""
        # Buscar patrones como "path/" + file o "path\\" + file
        path_patterns = [
            (re.compile(r'[\'"][^\'"]*[/\\][\'"]\s*\+'), "STRING_PATH_CONCAT"),
            (re.compile(r"\.format\s*\([^)]*[/\\]"), "FORMAT_PATH"),
            (re.compile(r'f[\'"][^\'"]*\{[^}]*\}[^\'"]*[/\\]'), "FSTRING_PATH"),
        ]

        for i, line in enumerate(self.lines, 1):
            for pattern, code in path_patterns:
                if pattern.search(line) and "pathlib" not in line.lower():
                    self.issues.append(
                        Issue(
                            i,
                            0,
                            "INFO",
                            code,
                            "Considerar usar pathlib.Path en lugar de concatenación de strings para paths",
                        )
                    )

    def check_import_order(self) -> None:
        """Verifica orden de imports (stdlib, third-party, local)."""
        # Simplificación: detectar imports locales mezclados con stdlib
        local_imports = []
        stdlib_imports = []

        stdlib_modules = {
            "os",
            "sys",
            "re",
            "json",
            "pathlib",
            "typing",
            "argparse",
            "datetime",
            "collections",
            "functools",
            "itertools",
            "math",
            "random",
            "string",
            "hashlib",
            "base64",
            "urllib",
            "http",
            "socket",
            "subprocess",
            "tempfile",
            "shutil",
            "glob",
            "csv",
        }

        for i, line in enumerate(self.lines, 1):
            if line.strip().startswith("import ") or line.strip().startswith("from "):
                module = line.strip().split()[1].split(".")[0]

                if module in stdlib_modules:
                    stdlib_imports.append((i, module))
                elif not module.startswith("."):
                    local_imports.append((i, module))

        # Si hay imports locales antes de stdlib completo, warning
        if local_imports and stdlib_imports:
            first_local = min(line for line, _ in local_imports)
            last_stdlib = max(line for line, _ in stdlib_imports)

            if first_local < last_stdlib:
                self.issues.append(
                    Issue(
                        first_local,
                        0,
                        "INFO",
                        "IMPORT_ORDER",
                        "Imports locales/third-party mezclados con stdlib. Orden recomendado: stdlib → third-party → local",
                    )
                )

    def check_line_endings(self) -> None:
        """Verifica que no haya line endings mixtos."""
        if "\r\n" in self.content and "\n" in self.content.replace("\r\n", ""):
            self.issues.append(
                Issue(
                    0,
                    0,
                    "WARNING",
                    "MIXED_LINE_ENDINGS",
                    "Archivo tiene line endings mixtos (CRLF y LF). Normalizar a LF.",
                )
            )

    def get_summary(self) -> Dict[str, int]:
        """Retorna resumen de issues encontradas."""
        summary = {"ERROR": 0, "WARNING": 0, "INFO": 0}
        for issue in self.issues:
            summary[issue.severity] += 1
        return summary

    def generate_fix_suggestions(self) -> List[Tuple[int, str, str]]:
        """Genera sugerencias de corrección (línea, original, sugerencia)."""
        suggestions = []

        for issue in self.issues:
            if issue.line == 0:
                continue

            original_line = self.lines[issue.line - 1]

            if issue.code == "EMOJI_IN_PRINT":
                # Reemplazar emojis comunes
                fixed = original_line
                replacements = {
                    "✅": "[OK]",
                    "❌": "[ERROR]",
                    "⚠️": "[WARN]",
                    "ℹ️": "[INFO]",
                    "➜": "->",
                    "•": "-",
                    "✓": "[X]",
                    "✗": "[ ]",
                }
                for emoji, ascii in replacements.items():
                    fixed = fixed.replace(emoji, ascii)
                suggestions.append((issue.line, original_line, fixed))

            elif issue.code == "MISSING_ENCODING":
                # Agregar encoding='utf-8'
                if "open(" in original_line and "encoding" not in original_line:
                    # Buscar el cierre del paréntesis
                    if original_line.rstrip().endswith(")"):
                        fixed = original_line.rstrip()[:-1] + ", encoding='utf-8')"
                        suggestions.append((issue.line, original_line, fixed))

        return suggestions


def check_file(file_path: str, fix_suggestions: bool = False) -> bool:
    """Chequea un archivo y muestra resultados."""
    print(f"\n{'=' * 60}")
    print(f"Checking: {file_path}")
    print("=" * 60)

    checker = ScriptChecker(file_path)
    issues = checker.check_all()
    summary = checker.get_summary()

    if not issues:
        print("[OK] No issues found! Script follows cross-platform standards.")
        return True

    # Mostrar issues agrupadas por severidad
    for severity in ["ERROR", "WARNING", "INFO"]:
        severity_issues = [i for i in issues if i.severity == severity]
        if severity_issues:
            print(f"\n{severity}s ({len(severity_issues)}):")
            for issue in severity_issues:
                print(f"  Line {issue.line:4d}: {issue.message}")

    # Resumen
    print(f"\n{'-' * 60}")
    print(
        f"Summary: {summary['ERROR']} errors, {summary['WARNING']} warnings, {summary['INFO']} info"
    )

    # Sugerencias de fixes
    if fix_suggestions and summary["ERROR"] + summary["WARNING"] > 0:
        suggestions = checker.generate_fix_suggestions()
        if suggestions:
            print(f"\nSuggested fixes:")
            for line, original, fixed in suggestions:
                print(f"  Line {line}:")
                print(f"    - {original.strip()}")
                print(f"    + {fixed.strip()}")

    return summary["ERROR"] == 0


def main():
    parser = argparse.ArgumentParser(
        description="Valida scripts Python contra estándares cross-platform",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  python check_script.py mi_script.py
  python check_script.py mi_script.py --fix-suggestions
  python check_script.py . --recursive
  python check_script.py ../../scripts/pa.py
        """,
    )

    parser.add_argument("path", help="Archivo o directorio a validar")
    parser.add_argument(
        "--fix-suggestions",
        action="store_true",
        help="Muestra sugerencias de corrección",
    )
    parser.add_argument(
        "--recursive",
        "-r",
        action="store_true",
        help="Busca recursivamente en directorios",
    )

    args = parser.parse_args()

    path = Path(args.path)

    if path.is_file():
        # Validar archivo individual
        success = check_file(str(path), args.fix_suggestions)
        sys.exit(0 if success else 1)

    elif path.is_dir():
        # Validar todos los .py en el directorio
        if args.recursive:
            files = list(path.rglob("*.py"))
        else:
            files = list(path.glob("*.py"))

        if not files:
            print(f"[WARN] No Python files found in {path}")
            sys.exit(0)

        all_success = True
        for file in sorted(files):
            if not check_file(str(file), args.fix_suggestions):
                all_success = False

        print(f"\n{'=' * 60}")
        print(f"Checked {len(files)} files")
        print("=" * 60)

        sys.exit(0 if all_success else 1)

    else:
        print(f"[ERROR] Path not found: {path}")
        sys.exit(1)


if __name__ == "__main__":
    main()
