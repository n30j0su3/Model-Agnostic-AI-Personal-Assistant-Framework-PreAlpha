"""Security tests for the per-install dashboard token."""

from __future__ import annotations

import os
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "core" / "scripts"
sys.path.insert(0, str(SCRIPTS))

import dashboard_server  # noqa: E402


def test_token_is_created_with_private_permissions(tmp_path):
    server, _ = dashboard_server.make_server(repo_root=tmp_path)
    try:
        token_file = tmp_path / "data" / "dashboard.token"
        assert token_file.is_file()
        assert token_file.stat().st_mode & 0o777 == 0o600
        token = token_file.read_text(encoding="utf-8").strip()
        assert len(token) >= 32
        assert server.current_token() == token
    finally:
        server.server_close()


def test_rotate_token_changes_value_and_revokes_cached_token(tmp_path):
    server, _ = dashboard_server.make_server(repo_root=tmp_path)
    try:
        token_file = tmp_path / "data" / "dashboard.token"
        first = token_file.read_text(encoding="utf-8").strip()
        second = server.rotate_token()
        assert second != first
        assert token_file.read_text(encoding="utf-8").strip() == second
        assert server.current_token() == second
    finally:
        server.server_close()


def test_external_token_change_is_reloaded(tmp_path):
    server, _ = dashboard_server.make_server(repo_root=tmp_path)
    try:
        token_file = tmp_path / "data" / "dashboard.token"
        assert server.current_token()
        replacement = "replacement-token-with-at-least-32-bytes"
        token_file.write_text(replacement + "\n", encoding="utf-8")
        os.chmod(token_file, 0o600)
        current = token_file.stat().st_mtime_ns
        os.utime(token_file, ns=(current + 1, current + 1))
        assert server.current_token() == replacement
    finally:
        server.server_close()
