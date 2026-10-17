"""Durable API/security contract for the local Dashboard Command Center."""
from __future__ import annotations

from contextlib import contextmanager
import http.client
import json
import os
from pathlib import Path
import re
import sys
import threading
from urllib.parse import urlencode

import pytest

from conftest import assert_private_file


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "core" / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import dashboard_server as ds  # noqa: E402
import version as framework_version  # noqa: E402


BRANDING = json.loads((ROOT / "config/branding.json").read_text(encoding="utf-8"))


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def seed_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    knowledge = repo / "core/.context/knowledge"
    for directory in (
        knowledge / "errors",
        repo / "config",
        repo / "docs",
        repo / "assets",
        repo / ".opencode/agent",
        repo / "core/agents/subagents",
    ):
        directory.mkdir(parents=True, exist_ok=True)

    _write_json(knowledge / "sessions-index.json", {
        "total_sessions": 2,
        "sessions": [
            {"id": "s1", "date": "2026-10-10", "title": "Alpha", "topics": ["x"],
             "summary": "SECRET-BODY", "file_path": "/tmp/secret/s1.md",
             "stats": {"messages": 3}, "highlights": ["secret"]},
            {"id": "s2", "date": "2026-10-11", "title": "Beta", "topics": ["y"],
             "summary": "beta body", "file_path": "data/sessions/s2.md"},
        ],
    })
    _write_json(knowledge / "skills-index.json", {
        "total_skills": 2,
        "skills": [
            {"id": "pa-assistant", "name": "PA Assistant", "category": "core",
             "location": "core/skills/core/pa-assistant/SKILL.md"},
            {"id": "doc-writer", "name": "Doc Writer", "category": "docs",
             "location": "core/skills/core/doc-writer/SKILL.md"},
        ],
    })
    _write_json(knowledge / "agents-index.json", {
        "total_agents": 3,
        "agents": [
            {"name": "pa-assistant", "type": "primary", "description": "d1",
             "purpose": "p", "location": ".opencode/agent/pa-assistant.md",
             "status": "active", "content": "SECRET-BODY"},
            {"name": "doc-writer", "type": "subagent", "description": "d2",
             "purpose": "p", "location": "core/agents/subagents/doc-writer.md",
             "status": "active"},
            {"name": "ghost", "type": "subagent", "description": "d3",
             "purpose": "p", "location": "core/agents/ghost.md", "status": "unknown"},
        ],
    })
    _write_json(knowledge / "interactions-index.json", {
        "total_events": 3,
        "interactions": [{"tool": "bash", "count": 2}, {"tool": "read", "count": 1}],
    })
    _write_json(knowledge / "errors/index.json", [
        {"id": "e1", "timestamp": "2026-10-12T10:00:00", "type": "runtime",
         "severity": "warn", "message": "SECRET-DETAIL"},
        {"id": "e2", "timestamp": "2026-10-12T11:00:00", "type": "network",
         "severity": "info"},
    ])
    _write_json(repo / "config/branding.json", BRANDING)
    (repo / "VERSION").write_text("0.4.1-beta\n", encoding="utf-8")
    (repo / "dashboard.html").write_text("<!doctype html><title>PA</title>", encoding="utf-8")
    (repo / ".opencode/agent/pa-assistant.md").write_text("v1\n", encoding="utf-8")
    (repo / "core/agents/subagents/doc-writer.md").write_text("doc\n", encoding="utf-8")
    (repo / "docs/note.md").write_text("# public doc\n", encoding="utf-8")
    (repo / "assets/app.css").write_text("body{}", encoding="utf-8")
    (repo / "core/.context/MASTER.md").write_text("MASTER-SECRET-BODY\n", encoding="utf-8")
    (repo / "assets/.env").write_text("SECRET=1\n", encoding="utf-8")
    (repo / ".hidden").write_text("hidden\n", encoding="utf-8")
    return repo


@contextmanager
def running_server(repo_root: Path):
    server, port = ds.make_server("127.0.0.1", 0, repo_root=repo_root, token_required=True)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield server, port, server.current_token()
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def request(
    repo: Path,
    method: str,
    path: str,
    body: object | None = None,
    *,
    token: bool = True,
    origin: str | None = None,
    host: str | None = None,
    content_type: str = "application/json",
) -> tuple[int, object]:
    with running_server(repo) as (_server, port, current_token):
        headers: dict[str, str] = {}
        if token:
            headers["X-PA-Token"] = current_token
        if content_type:
            headers["Content-Type"] = content_type
        if origin is not None:
            headers["Origin"] = origin.format(port=port)
        if host is not None:
            headers["Host"] = host.format(port=port)
        payload = None if body is None else json.dumps(body).encode("utf-8")
        connection = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
        connection.request(method, path, body=payload, headers=headers)
        response = connection.getresponse()
        raw = response.read()
        status = response.status
        content_type_header = response.getheader("Content-Type") or ""
        connection.close()
    if "json" in content_type_header:
        return status, json.loads(raw.decode("utf-8"))
    return status, raw.decode("utf-8", errors="replace")


def test_knowledge_summary_returns_whitelisted_metadata_and_honest_counts(tmp_path):
    repo = seed_repo(tmp_path)
    status, payload = request(repo, "GET", "/api/knowledge/summary")
    assert status == 200 and payload["ok"] is True
    assert payload["counts"] == {"sessions": 2, "interactions": 2, "skills": 2,
                                  "agents": 3, "errors": 2}
    assert payload["sessions"][0] == {"id": "s1", "date": "2026-10-10",
                                       "title": "Alpha", "topics": ["x"]}
    assert payload["interactions"] == [{"tool": "bash", "count": 2},
                                        {"tool": "read", "count": 1}]
    assert payload["skills"][0] == {"id": "pa-assistant", "name": "PA Assistant",
                                     "category": "core"}
    assert [item["name"] for item in payload["agents"]] == ["pa-assistant", "doc-writer", "ghost"]
    assert payload["agents"][0]["editable"] is True
    assert payload["agents"][2]["editable"] is False
    assert payload["errors"][0] == {"id": "e1", "timestamp": "2026-10-12T10:00:00",
                                     "type": "runtime", "severity": "warn"}


def test_knowledge_summary_redacts_bodies_paths_and_secrets(tmp_path):
    repo = seed_repo(tmp_path)
    status, payload = request(repo, "GET", "/api/knowledge/summary")
    text = json.dumps(payload)
    assert status == 200
    for secret in ("SECRET-BODY", "SECRET-DETAIL", "/tmp/secret", str(repo)):
        assert secret not in text
    assert set(payload["sessions"][0]) <= {"id", "date", "title", "topics"}


def test_knowledge_summary_with_missing_knowledge_dir_is_empty_but_ok(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "VERSION").write_text("0.4.1-beta\n", encoding="utf-8")
    status, payload = request(repo, "GET", "/api/knowledge/summary")
    assert status == 200 and payload["ok"] is True
    for key in ("sessions", "interactions", "skills", "agents", "errors"):
        assert payload[key] == []
    assert set(payload["counts"].values()) == {0}


def test_knowledge_summary_malformed_indexes_degrade_to_empty(tmp_path):
    repo = tmp_path / "repo"
    knowledge = repo / "core/.context/knowledge"
    (knowledge / "errors").mkdir(parents=True)
    (knowledge / "sessions-index.json").write_text("{not json", encoding="utf-8")
    (knowledge / "skills-index.json").write_text('["wrong", "shape"]', encoding="utf-8")
    (knowledge / "agents-index.json").write_text("17", encoding="utf-8")
    _write_json(knowledge / "interactions-index.json", {"total_events": "NaN"})
    (knowledge / "errors/index.json").write_text("[]", encoding="utf-8")
    (repo / "VERSION").write_text("0.4.1-beta\n", encoding="utf-8")
    status, payload = request(repo, "GET", "/api/knowledge/summary")
    assert status == 200
    assert set(payload["counts"].values()) == {0}


def test_status_reports_canonical_version_and_tracked_brand(tmp_path):
    repo = seed_repo(tmp_path)
    status, payload = request(repo, "GET", "/api/status")
    assert status == 200
    assert payload["framework"]["version"] == framework_version.canonical(repo)
    assert payload["framework"]["brand"] == BRANDING
    assert str(repo) not in json.dumps(payload)


def test_branding_json_is_tracked_with_expected_official_content():
    path = ROOT / "config/branding.json"
    assert path.exists(), "config/branding.json debe existir en el repo"
    assert json.loads(path.read_text(encoding="utf-8")) == BRANDING


def test_models_free_endpoint_uses_only_get_free_models(tmp_path, monkeypatch):
    repo = seed_repo(tmp_path)
    calls: list[int] = []
    monkeypatch.setattr(ds.sfm, "get_free_models", lambda port: calls.append(port) or [
        {"id": "opencode/qwen3-coder-free", "status": "anon"}
    ])
    monkeypatch.setattr(ds.sfm, "get_usable_models", lambda *a, **k: pytest.fail("paid catalog used"))
    status, payload = request(repo, "GET", "/api/models/free")
    assert status == 200 and calls
    assert payload == [{"id": "opencode/qwen3-coder-free", "status": "anon",
                        "badge": ds.oc_auth.provider_auth_badge("anon"), "free": True}]


def test_skills_toggle_requires_loopback_origin_token_and_json(tmp_path):
    repo = seed_repo(tmp_path)
    body = {"id": "pa-assistant", "enabled": False}
    assert request(repo, "POST", "/api/skills/toggle", body, token=False)[0] == 401
    assert request(repo, "POST", "/api/skills/toggle", body,
                   origin="https://evil.example")[0] == 403
    assert request(repo, "POST", "/api/skills/toggle", body,
                   content_type="text/plain")[0] == 415
    assert request(repo, "GET", "/api/skills/toggle")[0] == 405


def test_skills_toggle_validates_id_against_skills_index(tmp_path, monkeypatch):
    repo = seed_repo(tmp_path)
    home = tmp_path / "home"
    monkeypatch.setenv("HOME", str(home))
    config_path = home / ".pa-framework/config.json"
    assert request(repo, "POST", "/api/skills/toggle", {"id": "nope", "enabled": True})[0] == 404
    assert not config_path.exists()
    assert request(repo, "POST", "/api/skills/toggle",
                   {"id": "pa-assistant", "enabled": "yes"})[0] == 400
    status, payload = request(repo, "POST", "/api/skills/toggle",
                              {"id": "doc-writer", "enabled": True})
    assert status == 200 and payload["enabled_skills"] == ["doc-writer"]
    assert json.loads(config_path.read_text(encoding="utf-8"))["enabled_skills"] == ["doc-writer"]


def test_skills_toggle_preserves_unknown_keys_and_sets_private_mode(tmp_path, monkeypatch):
    repo = seed_repo(tmp_path)
    home = tmp_path / "home"
    monkeypatch.setenv("HOME", str(home))
    replacements: list[tuple[Path, Path]] = []
    real_replace = ds.os.replace
    monkeypatch.setattr(
        ds.os,
        "replace",
        lambda source, target: (
            replacements.append((Path(source), Path(target))),
            real_replace(source, target),
        )[1],
    )
    config_path = home / ".pa-framework/config.json"
    config_path.parent.mkdir(parents=True)
    _write_json(config_path, {"enabled_skills": ["pa-assistant"], "language": "es", "custom_key": "keep"})
    os.chmod(config_path, 0o644)
    status, _ = request(repo, "POST", "/api/skills/toggle",
                        {"id": "pa-assistant", "enabled": False})
    data = json.loads(config_path.read_text(encoding="utf-8"))
    assert status == 200
    assert data["enabled_skills"] == [] and data["language"] == "es" and data["custom_key"] == "keep"
    assert_private_file(config_path)
    assert any(target == config_path for _source, target in replacements)
    assert not list(config_path.parent.glob(".config.json.*.tmp"))


def test_skills_reindex_invokes_only_skills_indexer(tmp_path, monkeypatch):
    repo = seed_repo(tmp_path)
    calls = []
    monkeypatch.setattr(ds, "run_py", lambda script, *a, **k: calls.append(script) or {"ok": True})
    status, payload = request(repo, "POST", "/api/skills/reindex",
                              {"script": "os-system-evil", "cmd": "rm -rf /"})
    assert status == 200 and payload["ok"] is True
    assert calls == ["skills_indexer.py"]


def test_agents_list_reflects_real_index_with_editable_flags(tmp_path):
    repo = seed_repo(tmp_path)
    status, payload = request(repo, "GET", "/api/agents/list")
    assert status == 200
    names = {item["name"] for item in payload["agents"]}
    assert {"pa-assistant", "doc-writer", "ghost"} <= names
    first = next(item for item in payload["agents"] if item["name"] == "pa-assistant")
    ghost = next(item for item in payload["agents"] if item["name"] == "ghost")
    assert first["editable"] is True and first["status"] == "active"
    assert ghost["editable"] is False
    assert "SECRET-BODY" not in json.dumps(payload)


def test_agent_read_and_update_roundtrip_with_timestamped_backup(tmp_path):
    repo = seed_repo(tmp_path)
    doc = repo / ".opencode/agent/pa-assistant.md"
    r_status, read_payload = request(repo, "GET", "/api/agents/read?id=pa-assistant")
    u_status, update_payload = request(repo, "POST", "/api/agents/update",
                                       {"id": "pa-assistant", "content": "v2\n"})
    assert r_status == 200 and read_payload["content"] == "v1\n"
    assert read_payload["path"] == ".opencode/agent/pa-assistant.md"
    assert u_status == 200 and update_payload["ok"] is True
    assert doc.read_text(encoding="utf-8") == "v2\n"
    backups = list(doc.parent.glob("pa-assistant.md.bak-*"))
    assert len(backups) == 1
    assert re.fullmatch(r"pa-assistant\.md\.bak-\d{8}-\d{6}", backups[0].name)
    assert backups[0].read_text(encoding="utf-8") == "v1\n"


def test_agent_endpoints_require_token_for_reads_and_writes(tmp_path):
    repo = seed_repo(tmp_path)
    assert request(repo, "GET", "/api/agents/read?id=pa-assistant", token=False)[0] == 401
    assert request(repo, "POST", "/api/agents/update",
                   {"id": "pa-assistant", "content": "x"}, token=False)[0] == 401
    assert request(repo, "GET", "/api/agents/list")[0] == 200


def _append_agents(repo: Path, entries: list[dict]) -> None:
    path = repo / "core/.context/knowledge/agents-index.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    data["agents"].extend(entries)
    _write_json(path, data)


def test_agent_update_rejects_unindexed_weird_abs_poisoned_and_nonmd(tmp_path):
    repo = seed_repo(tmp_path)
    _append_agents(repo, [
        {"name": "abs-agent", "type": "subagent", "description": "d", "purpose": "p",
         "location": "/etc/passwd", "status": "active"},
        {"name": "trav-agent", "type": "subagent", "description": "d", "purpose": "p",
         "location": "../outside.md", "status": "active"},
        {"name": "txt-agent", "type": "subagent", "description": "d", "purpose": "p",
         "location": "core/agents/notes.txt", "status": "active"},
    ])
    cases = [
        ({"id": "../escape", "content": "x"}, 404),
        ({"id": "/etc/passwd", "content": "x"}, 404),
        ({"id": "ghost", "content": "x"}, 400),
        ({"id": "abs-agent", "content": "x"}, 400),
        ({"id": "trav-agent", "content": "x"}, 400),
        ({"id": "txt-agent", "content": "x"}, 400),
        ({"id": "pa-assistant", "content": 42}, 400),
    ]
    for payload, expected in cases:
        assert request(repo, "POST", "/api/agents/update", payload)[0] == expected


def test_agent_update_rejects_symlinked_document(tmp_path):
    repo = seed_repo(tmp_path)
    target = tmp_path / "outside-root/target.md"
    target.parent.mkdir()
    target.write_text("OUTSIDE\n", encoding="utf-8")
    link = repo / "core/agents/linked.md"
    link.symlink_to(target)
    _append_agents(repo, [{"name": "linked", "type": "subagent", "description": "d",
                           "purpose": "p", "location": "core/agents/linked.md", "status": "active"}])
    assert request(repo, "GET", "/api/agents/read?id=linked")[0] == 400
    assert request(repo, "POST", "/api/agents/update",
                   {"id": "linked", "content": "HACKED"})[0] == 400
    assert target.read_text(encoding="utf-8") == "OUTSIDE\n"


def test_agent_update_rejects_oversized_content(tmp_path):
    repo = seed_repo(tmp_path)
    doc = repo / ".opencode/agent/pa-assistant.md"
    status, _ = request(repo, "POST", "/api/agents/update",
                        {"id": "pa-assistant", "content": "a" * (512 * 1024 + 1)})
    assert status == 413
    assert doc.read_text(encoding="utf-8") == "v1\n"
    assert not list(doc.parent.glob("*.bak-*"))


def test_agent_endpoints_refuse_context_and_credential_files(tmp_path):
    repo = seed_repo(tmp_path)
    _append_agents(repo, [
        {"name": "master-edit", "type": "system", "description": "d", "purpose": "p",
         "location": "core/.context/MASTER.md", "status": "active"},
        {"name": "oc-auth", "type": "script", "description": "d", "purpose": "p",
         "location": "core/scripts/oc_auth.py", "status": "active"},
    ])
    l_status, listing = request(repo, "GET", "/api/agents/list")
    assert l_status == 200
    flagged = {a["name"]: a["editable"] for a in listing["agents"]}
    assert flagged["master-edit"] is False and flagged["oc-auth"] is False
    assert request(repo, "GET", "/api/agents/read?id=master-edit")[0] == 400
    assert request(repo, "POST", "/api/agents/update",
                   {"id": "master-edit", "content": "x"})[0] == 400
    assert request(repo, "GET", "/api/agents/read?id=oc-auth")[0] == 400
    assert "MASTER-SECRET-BODY" not in json.dumps(listing)


def test_static_keeps_serving_safe_public_files(tmp_path):
    repo = seed_repo(tmp_path)
    s1, body = request(repo, "GET", "/docs/note.md")
    s2, css = request(repo, "GET", "/assets/app.css")
    assert s1 == 200 and "# public doc" in body
    assert s2 == 200 and css == "body{}"


def test_static_denies_context_data_config_and_dotfiles(tmp_path):
    repo = seed_repo(tmp_path)
    for path in ("/core/.context/MASTER.md", "/core/.context/knowledge/sessions-index.json",
                 "/data/dashboard.token", "/config/branding.json", "/assets/.env", "/.hidden"):
        assert request(repo, "GET", path)[0] == 404


def test_static_denies_encoded_and_backslash_traversal(tmp_path):
    repo = seed_repo(tmp_path)
    for path in ("/%2e%2e/core/.context/MASTER.md",
                 "/core/%2e%2e/%2e%2e/core/.context/MASTER.md",
                 "/..%5ccore%5c.context%5cMASTER.md",
                 "/core/..%2f.context%2fMASTER.md"):
        assert request(repo, "GET", path)[0] == 404


def test_static_denies_symlinked_assets(tmp_path):
    repo = seed_repo(tmp_path)
    outside = tmp_path / "outside-root/secret.md"
    outside.parent.mkdir()
    outside.write_text("OUTSIDE-SECRET\n", encoding="utf-8")
    (repo / "core/public-link.md").symlink_to(outside)
    (repo / "assets/alias.md").symlink_to(repo / "docs/note.md")
    out_code, out_body = request(repo, "GET", "/core/public-link.md")
    alias_code, _ = request(repo, "GET", "/assets/alias.md")
    safe_code, safe_body = request(repo, "GET", "/docs/note.md")
    assert out_code == 404 and "OUTSIDE-SECRET" not in json.dumps(out_body)
    assert alias_code == 404
    assert safe_code == 200 and "# public doc" in safe_body


def test_sensitive_read_apis_reject_foreign_host_and_origin(tmp_path):
    repo = seed_repo(tmp_path)
    host_code, _ = request(repo, "GET", "/api/knowledge/summary", host="evil.example")
    origin_code, _ = request(repo, "GET", "/api/knowledge/summary",
                             origin="https://evil.example")
    assert host_code == 403 and origin_code == 403
