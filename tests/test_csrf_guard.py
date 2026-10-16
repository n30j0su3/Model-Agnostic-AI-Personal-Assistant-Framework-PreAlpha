"""Mutation guard tests for the local dashboard control plane."""

from __future__ import annotations

import json
import sys
import threading
import urllib.error
import urllib.request
from contextlib import contextmanager
from pathlib import Path


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


def post_config(port: int, headers: dict[str, str]) -> int:
    body = json.dumps({"file": "profile", "content": "PWNED"}).encode()
    request = urllib.request.Request(
        f"http://127.0.0.1:{port}/api/files/config",
        data=body,
        headers=headers,
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=5) as response:
            return response.status
    except urllib.error.HTTPError as error:
        return error.code


def test_cross_origin_write_is_rejected_without_touching_profile(tmp_path):
    with running_server(tmp_path) as (server, port):
        status = post_config(
            port,
            {
                "Origin": "https://evil.example",
                "Content-Type": "application/json",
                "X-PA-Token": server.current_token(),
            },
        )
    assert status == 403
    assert not (tmp_path / "core/.context/profile.md").exists()


def test_invalid_host_is_rejected(tmp_path):
    with running_server(tmp_path) as (server, port):
        status = post_config(
            port,
            {
                "Host": "evil.example",
                "Content-Type": "application/json",
                "X-PA-Token": server.current_token(),
            },
        )
    assert status == 403


def test_non_json_mutation_is_rejected(tmp_path):
    with running_server(tmp_path) as (server, port):
        status = post_config(
            port,
            {
                "Origin": f"http://127.0.0.1:{port}",
                "Content-Type": "text/plain",
                "X-PA-Token": server.current_token(),
            },
        )
    assert status == 415
    assert not (tmp_path / "core/.context/profile.md").exists()
