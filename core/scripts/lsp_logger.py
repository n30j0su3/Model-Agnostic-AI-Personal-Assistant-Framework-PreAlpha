#!/usr/bin/env python3
"""
LSP Error Logger - PA Framework
===============================

Captura errores LSP/diagnósticos y los guarda en formato JSON Lines.
Permite análisis de errores frecuentes y seguimiento de calidad de código.

Uso:
    # Capturar errores desde salida de herramienta
    python core/scripts/lsp-logger.py --parse-string "$diagnostic_output"

    # Log manual de error
    python core/scripts/lsp-logger.py --file "script.py" --line 42 --error "Type mismatch"

    # Mostrar resumen de errores del día
    python core/scripts/lsp-logger.py --summary

Formato de salida (JSON Lines):
    logs/lsp/YYYY-MM-DD.jsonl

Integración:
    - Llamado automáticamente desde edit tools que retornan diagnósticos LSP
    - Actualiza sessions-index.json con conteo de errores
"""

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

# Paths
SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent.parent
LOGS_LSP_DIR = REPO_ROOT / "logs" / "lsp"
KNOWLEDGE_DIR = REPO_ROOT / "core" / ".context" / "knowledge"
SESSIONS_DIR = REPO_ROOT / "core" / ".context" / "sessions"

# Ensure directories exist
LOGS_LSP_DIR.mkdir(parents=True, exist_ok=True)


class LSPLogger:
    """Logger para errores LSP/diagnósticos."""

    def __init__(self, session_id: Optional[str] = None):
        self.session_id = session_id or datetime.now().strftime("%Y-%m-%d")
        self.log_file = LOGS_LSP_DIR / f"{self.session_id}.jsonl"

    def log_error(
        self,
        file: str,
        line: int,
        severity: str,
        message: str,
        tool: str = "lsp",
        context: Optional[str] = None,
    ) -> dict:
        """Log a single LSP error."""

        entry = {
            "timestamp": datetime.now().isoformat(),
            "session": self.session_id,
            "file": file,
            "line": line,
            "severity": severity,
            "message": message,
            "tool": tool,
            "context": context,
        }

        # Append to JSON Lines file
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

        return entry

    def parse_diagnostics(self, diagnostic_text: str, tool: str = "lsp") -> list:
        """Parse diagnostic output from LSP tools."""
        errors = []

        # Pattern 1: ERROR [line:col] message
        pattern1 = r"ERROR\s+\[(\d+):(\d+)\]\s*(.+?)(?=\n|$)"

        # Pattern 2: file.py:line:col - severity: message
        pattern2 = r"([^\s]+\.py):(\d+):(\d+):\s*(error|warning|info):\s*(.+)"

        # Pattern 3: Type error specific
        pattern3 = r'Type\s+"(.+?)"\s+is not assignable to return type\s+"(.+?)"'

        lines = diagnostic_text.split("\n")
        current_file = None

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Try pattern 1
            match1 = re.search(pattern1, line, re.IGNORECASE)
            if match1:
                line_num = int(match1.group(1))
                message = match1.group(3).strip()
                errors.append(
                    self.log_error(
                        file=current_file or "unknown",
                        line=line_num,
                        severity="error",
                        message=message,
                        tool=tool,
                    )
                )
                continue

            # Try pattern 2
            match2 = re.search(pattern2, line, re.IGNORECASE)
            if match2:
                current_file = match2.group(1)
                line_num = int(match2.group(2))
                severity = match2.group(4).lower()
                message = match2.group(5).strip()
                errors.append(
                    self.log_error(
                        file=current_file,
                        line=line_num,
                        severity=severity,
                        message=message,
                        tool=tool,
                    )
                )
                continue

            # Try pattern 3 (type errors)
            match3 = re.search(pattern3, line)
            if match3:
                actual_type = match3.group(1)
                expected_type = match3.group(2)
                errors.append(
                    self.log_error(
                        file=current_file or "unknown",
                        line=0,
                        severity="error",
                        message=f'Type "{actual_type}" not assignable to "{expected_type}"',
                        tool=tool,
                        context="type_check",
                    )
                )

        return errors

    def get_summary(self, date: Optional[str] = None) -> dict:
        """Get summary of errors for a date."""
        date = date or self.session_id
        log_file = LOGS_LSP_DIR / f"{date}.jsonl"

        if not log_file.exists():
            return {"total": 0, "by_severity": {}, "by_file": {}}

        summary = {"total": 0, "by_severity": {}, "by_file": {}, "by_tool": {}}

        with open(log_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                    summary["total"] += 1

                    # By severity
                    sev = entry.get("severity", "unknown")
                    summary["by_severity"][sev] = summary["by_severity"].get(sev, 0) + 1

                    # By file
                    file = entry.get("file", "unknown")
                    summary["by_file"][file] = summary["by_file"].get(file, 0) + 1

                    # By tool
                    tool = entry.get("tool", "unknown")
                    summary["by_tool"][tool] = summary["by_tool"].get(tool, 0) + 1

                except json.JSONDecodeError:
                    continue

        return summary

    def update_session_index(self) -> bool:
        """Update sessions-index.json with error count."""
        index_file = KNOWLEDGE_DIR / "sessions-index.json"

        if not index_file.exists():
            return False

        try:
            with open(index_file, "r", encoding="utf-8") as f:
                index = json.load(f)

            summary = self.get_summary()
            error_count = summary["total"]

            # Update current session
            for session in index.get("sessions", []):
                if session.get("id") == self.session_id:
                    session["stats"]["lsp_errors"] = error_count
                    break

            index["last_updated"] = datetime.now().isoformat()

            with open(index_file, "w", encoding="utf-8") as f:
                json.dump(index, f, indent=2, ensure_ascii=False)

            return True

        except Exception as e:
            print(f"[LSP Logger] Error updating index: {e}", file=sys.stderr)
            return False


def main():
    parser = argparse.ArgumentParser(description="LSP Error Logger")
    parser.add_argument("--parse-string", help="Parse diagnostic output string")
    parser.add_argument("--file", help="File path with error")
    parser.add_argument("--line", type=int, help="Line number")
    parser.add_argument("--severity", default="error", help="Error severity")
    parser.add_argument("--error", help="Error message")
    parser.add_argument("--tool", default="lsp", help="Tool name")
    parser.add_argument("--context", help="Additional context")
    parser.add_argument("--summary", action="store_true", help="Show summary")
    parser.add_argument("--session", help="Session ID (default: today)")

    args = parser.parse_args()

    logger = LSPLogger(session_id=args.session)

    if args.summary:
        summary = logger.get_summary()
        print(f"LSP Errors Summary for {logger.session_id}")
        print(f"Total: {summary['total']}")
        print(f"\nBy Severity:")
        for sev, count in summary["by_severity"].items():
            print(f"  {sev}: {count}")
        print(f"\nBy File:")
        for file, count in sorted(summary["by_file"].items(), key=lambda x: -x[1]):
            print(f"  {file}: {count}")
        return 0

    if args.parse_string:
        errors = logger.parse_diagnostics(args.parse_string, args.tool)
        logger.update_session_index()
        print(f"[LSP Logger] Captured {len(errors)} errors")
        return 0

    if args.file and args.error:
        logger.log_error(
            file=args.file,
            line=args.line or 0,
            severity=args.severity,
            message=args.error,
            tool=args.tool,
            context=args.context,
        )
        logger.update_session_index()
        print(f"[LSP Logger] Error logged: {args.file}:{args.line}")
        return 0

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
