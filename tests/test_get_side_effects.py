"""HTTP method and side-effect contracts for dashboard GET routes."""

from __future__ import annotations

import json
import sys
import threading
import urllib.error
import urllib.request
from contextlib import contextmanager
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "core" / "scripts"
sys.path.insert(0, str(SCRIPTS))

import dashboard_server  # noqa: E402


@contextmanager
def running_server(repo_root: Path):
    server, port = dashboard_server.make_server(
        repo_root=repo_root, token_required=True
    )
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield server, port
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def request_status(url: str, *, method: str = "GET", body: bytes | None = None,
                   headers: dict[str, str] | None = None) -> tuple[int, Any]:
    request = urllib.request.Request(
        url, data=body, headers=headers or {}, method=method
    )
    try:
        with urllib.request.urlopen(request, timeout=5) as response:
            payload = json.loads(response.read().decode("utf-8"))
            return response.status, payload
    except urllib.error.HTTPError as error:
        payload = json.loads(error.read().decode("utf-8"))
        return error.code, payload


def mutation_headers(server, port: int) -> dict[str, str]:
    return {
        "Origin": f"http://127.0.0.1:{port}",
        "Content-Type": "application/json",
        "X-PA-Token": server.current_token(),
    }


def test_get_models_is_read_only(tmp_path, monkeypatch):
    monkeypatch.setattr(
        dashboard_server,
        "opencode_ensure",
        lambda: (_ for _ in ()).throw(AssertionError("GET spawned runtime")),
    )
    monkeypatch.setattr(
        dashboard_server.sfm, "get_usable_models", lambda _port: []
    )
    with running_server(tmp_path) as (_, port):
        status, payload = request_status(
            f"http://127.0.0.1:{port}/api/models/free"
        )
    assert status == 200
    assert payload == []


def test_get_process_routes_are_method_not_allowed(tmp_path, monkeypatch):
    monkeypatch.setattr(
        dashboard_server,
        "run_py",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            AssertionError("GET executed subprocess")
        ),
    )
    monkeypatch.setattr(
        dashboard_server,
        "opencode_ensure",
        lambda: (_ for _ in ()).throw(AssertionError("GET spawned runtime")),
    )
    with running_server(tmp_path) as (_, port):
        base = f"http://127.0.0.1:{port}"
        for path in (
            "/api/framework/bootstrap",
            "/api/framework/check",
            "/api/models/test?model=opencode/test-free",
        ):
            status, _ = request_status(base + path)
            assert status == 405, path


def test_security_bootstrap_is_same_origin(tmp_path):
    with running_server(tmp_path) as (server, port):
        base = f"http://127.0.0.1:{port}"
        status, payload = request_status(base + "/api/security/token")
        assert status == 200
        assert payload["token"] == server.current_token()

        status, _ = request_status(
            base + "/api/security/token",
            headers={"Origin": "https://evil.example"},
        )
        assert status == 403


def test_sensitive_gets_reject_foreign_origin_before_reading(tmp_path, monkeypatch):
    forbidden = lambda *args, **kwargs: (_ for _ in ()).throw(
        AssertionError("foreign origin reached sensitive read")
    )
    with running_server(tmp_path) as (_, port):
        monkeypatch.setattr(dashboard_server.sfm, "get_free_models", forbidden)
        monkeypatch.setattr(dashboard_server.sfm, "load_selection", forbidden)
        base = f"http://127.0.0.1:{port}"
        for path in (
            "/api/files/config",
            "/api/models/free",
            "/api/config/model",
        ):
            status, payload = request_status(
                base + path,
                headers={"Origin": "https://evil.example"},
            )
            assert status == 403, path
            assert payload["error"] == "invalid origin"


def test_sensitive_gets_remain_available_on_loopback(tmp_path, monkeypatch):
    monkeypatch.setattr(dashboard_server.sfm, "get_free_models", lambda _port: [])
    monkeypatch.setattr(
        dashboard_server.sfm,
        "load_selection",
        lambda _root: {"model": "opencode/test-free", "agent": "FreakingJSON"},
    )

    with running_server(tmp_path) as (_, port):
        base = f"http://127.0.0.1:{port}"
        for path in (
            "/api/files/config",
            "/api/models/free",
            "/api/config/model",
        ):
            status, _ = request_status(base + path)
            assert status == 200, path


def test_runtime_ensure_via_guarded_post(tmp_path, monkeypatch):
    calls = []

    def fake_ensure():
        calls.append("ensure")
        return {"ok": True, "already": True, "port": 47371}

    monkeypatch.setattr(dashboard_server, "opencode_ensure", fake_ensure)
    with running_server(tmp_path) as (server, port):
        base = f"http://127.0.0.1:{port}"
        status, payload = request_status(
            base + "/api/runtime/ensure",
            method="POST",
            body=b"{}",
            headers=mutation_headers(server, port),
        )
        legacy_status, _ = request_status(
            base + "/api/opencode/ensure",
            method="POST",
            body=b"{}",
            headers=mutation_headers(server, port),
        )
    assert status == 200
    assert payload["ok"] is True
    assert legacy_status == 404
    assert calls == ["ensure"]


def test_chat_and_model_test_never_start_runtime(tmp_path, monkeypatch):
    monkeypatch.setattr(
        dashboard_server,
        "opencode_ensure",
        lambda: (_ for _ in ()).throw(AssertionError("implicit runtime start")),
    )
    monkeypatch.setattr(dashboard_server, "opencode_serving", lambda: False)
    with running_server(tmp_path) as (server, port):
        base = f"http://127.0.0.1:{port}"
        headers = mutation_headers(server, port)
        chat_status, _ = request_status(
            base + "/api/opencode/chat",
            method="POST",
            body=json.dumps({"message": "hola"}).encode(),
            headers=headers,
        )
        model_status, _ = request_status(
            base + "/api/models/test",
            method="POST",
            body=json.dumps({"model": "opencode/test-free"}).encode(),
            headers=headers,
        )
    assert chat_status == 503
    assert model_status == 503


def test_frontend_uses_in_memory_token_and_explicit_post_routes():
    html = (ROOT / "dashboard.html").read_text(encoding="utf-8")
    assert "X-PA-Token" in html
    assert "this.token = payload.token" in html
    assert "this.api('/api/framework/bootstrap', 'POST', {})" in html
    assert "paConsole.api('/api/runtime/ensure', 'POST', {})" in html
    assert "paConsole.api('/api/models/test', 'POST', {model})" in html
    assert "/api/opencode/ensure" not in html
