"""Headless smoke test for the PA dashboard bridge."""

from __future__ import annotations

import sys
import threading
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "core" / "scripts"
sys.path.insert(0, str(SCRIPTS))

import dashboard_server  # noqa: E402


def test_make_server_serves_dashboard_on_ephemeral_port():
    server, port = dashboard_server.make_server(
        host="127.0.0.1", port=0, repo_root=ROOT
    )
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        assert port > 0
        assert server.server_address[1] == port
        assert server.repo_root == ROOT
        with urllib.request.urlopen(
            f"http://127.0.0.1:{port}/", timeout=5
        ) as response:
            body = response.read().decode("utf-8")
            assert response.status == 200
        assert "<!DOCTYPE html>" in body
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
        assert not thread.is_alive()
