#!/usr/bin/env python3
"""Utilidades multiplataforma — Pre-Alpha."""

import os
import sys
import subprocess
from pathlib import Path


class PlatformHelper:
    @staticmethod
    def clear_screen():
        if sys.stdout.isatty():
            os.system("cls" if os.name == "nt" else "clear")

    @staticmethod
    def set_terminal_title(title: str):
        if os.name == "nt":
            os.system(f"title {title}")
        else:
            sys.stdout.write(f"\x1b]2;{title}\x07")
            sys.stdout.flush()

    @staticmethod
    def get_python_executable() -> str:
        return sys.executable

    @staticmethod
    def run_command(command_list, cwd=None, capture_output=True):
        try:
            return subprocess.run(
                command_list, cwd=cwd, capture_output=capture_output,
                text=True, check=False,
            )
        except FileNotFoundError as e:
            return subprocess.CompletedProcess(
                args=command_list, returncode=1, stderr=f"Not found: {e}"
            )


def get_repo_root() -> Path:
    """Return the repository root (2 levels up from core/scripts/)."""
    return Path(__file__).resolve().parents[2]
