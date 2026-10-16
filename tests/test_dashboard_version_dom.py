"""Dashboard version must come only from the local status API."""

from __future__ import annotations

import importlib.util
import json
import sys
import threading
import urllib.request
from contextlib import contextmanager
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "core" / "scripts" / "dashboard_server.py"

spec = importlib.util.spec_from_file_location("dashboard_server_version_test", MODULE_PATH)
if spec is None or spec.loader is None:
    raise ImportError("cannot load dashboard_server")
dashboard_server = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = dashboard_server
spec.loader.exec_module(dashboard_server)


@contextmanager
def running_server(tmp_path: Path):
    (tmp_path / "dashboard.html").write_text(
        (ROOT / "dashboard.html").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    (tmp_path / "VERSION").write_text("0.4.1-beta\n", encoding="utf-8")
    server, port = dashboard_server.make_server(repo_root=tmp_path)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield port
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=3)


def get_text(url: str) -> str:
    with urllib.request.urlopen(url, timeout=3) as response:
        assert response.status == 200
        return response.read().decode("utf-8")


def test_no_dashboard_data_js_request(tmp_path):
    with running_server(tmp_path) as port:
        html = get_text(f"http://127.0.0.1:{port}/")

    assert "dashboard-data.js" not in html


def test_version_is_provided_by_api_only(tmp_path, monkeypatch):
    monkeypatch.setattr(dashboard_server, "opencode_installed", lambda: None)
    monkeypatch.setattr(dashboard_server, "opencode_serving", lambda: False)

    with running_server(tmp_path) as port:
        html = get_text(f"http://127.0.0.1:{port}/")
        status = json.loads(get_text(f"http://127.0.0.1:{port}/api/status"))

    assert "v0.4.1" not in html
    assert "fetch('/api/status'" in html
    for element_id in (
        "header-framework-version",
        "home-framework-version",
        "workflow-framework-version",
        "footer-framework-version",
    ):
        assert f'id="{element_id}"' in html
    assert status["framework"]["version"] == "0.4.1-beta"
