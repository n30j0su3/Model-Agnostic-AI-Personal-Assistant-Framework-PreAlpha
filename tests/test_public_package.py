"""Release ZIP must be deterministic, sanitized, and runnable after extraction."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
BUILD_SCRIPT = ROOT / "core" / "scripts" / "build_release.py"


def load_builder():
    spec = importlib.util.spec_from_file_location("build_release", BUILD_SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def initialize_fixture_repo(repo_extract: Path) -> Path:
    """Turn the extracted candidate into a standalone Git source tree."""
    subprocess.run(["git", "init", "-q"], cwd=repo_extract, check=True)
    subprocess.run(["git", "add", "-A"], cwd=repo_extract, check=True)
    subprocess.run(
        [
            "git",
            "-c",
            "user.name=PA Release Tests",
            "-c",
            "user.email=release-tests@example.invalid",
            "commit",
            "-qm",
            "release fixture",
        ],
        cwd=repo_extract,
        check=True,
    )
    return repo_extract


@pytest.fixture
def release_repo(repo_extract: Path) -> Path:
    return initialize_fixture_repo(repo_extract)


def test_release_zip_is_sanitized_and_hashed(tmp_path: Path, release_repo: Path):
    builder = load_builder()
    package = builder.build_release_zip(tmp_path / "dist", repo_root=release_repo)
    receipt = builder.verify_release_zip(package)

    assert receipt["version"] == "0.4.1-beta"
    assert receipt["files"] > 100
    assert len(receipt["sha256"]) == 64

    with zipfile.ZipFile(package) as archive:
        names = archive.namelist()
        manifest = json.loads(archive.read(builder.MANIFEST_NAME))
        assert "core/scripts/build_release.py" in names
        assert "tests/test_public_package.py" in names
        assert re.fullmatch(r"[0-9a-f]{40}", manifest["tree"])
        assert not any(
            part in {".git", ".pytest_cache", "__pycache__", "node_modules"}
            for name in names
            for part in Path(name).parts
        )
        assert all(
            name == builder.MANIFEST_NAME or not builder.is_denied_path(name)
            for name in names
        )
        assert names.count(builder.MANIFEST_NAME) == 1
        assert not any(".bak" in name.lower() for name in names)
        assert not any(name.startswith(("data/", "dist/", "build/", "backups/")) for name in names)
        local_user = b"freaking" + b"json"
        forbidden_paths = (
            b"/home/" + local_user,
            b"/Users/" + local_user,
            b"C:\\Users\\" + local_user,
        )
        for entry in manifest["files"]:
            payload = archive.read(entry["path"])
            assert entry["size"] == len(payload)
            assert entry["sha256"] == hashlib.sha256(payload).hexdigest()
            if builder.is_scannable_payload(entry["path"], payload):
                assert not any(needle in payload for needle in forbidden_paths)


def test_release_zip_is_byte_deterministic(tmp_path: Path, release_repo: Path):
    builder = load_builder()
    first = builder.build_release_zip(tmp_path / "first", repo_root=release_repo)
    second = builder.build_release_zip(tmp_path / "second", repo_root=release_repo)
    assert first.read_bytes() == second.read_bytes()


def test_repackaging_excludes_stale_source_manifest(tmp_path: Path, release_repo: Path):
    builder = load_builder()
    stale = release_repo / builder.MANIFEST_NAME
    stale.write_text('{"stale": true}\n', encoding="utf-8")
    subprocess.run(["git", "add", builder.MANIFEST_NAME], cwd=release_repo, check=True)
    subprocess.run(
        [
            "git",
            "-c",
            "user.name=PA Release Tests",
            "-c",
            "user.email=release-tests@example.invalid",
            "commit",
            "-qm",
            "stale manifest fixture",
        ],
        cwd=release_repo,
        check=True,
    )
    package = builder.build_release_zip(tmp_path / "dist", repo_root=release_repo)
    receipt = builder.verify_release_zip(package)
    with zipfile.ZipFile(package) as archive:
        assert archive.namelist().count(builder.MANIFEST_NAME) == 1
        assert json.loads(archive.read(builder.MANIFEST_NAME)).get("stale") is None
    assert receipt["files"] > 100


def test_sanitizer_rejects_private_payloads_and_paths():
    builder = load_builder()
    real_user = b"alice"
    with pytest.raises(builder.ReleaseBuildError, match="local path"):
        builder.assert_public_payload("README.md", b"workspace=/home/" + real_user + b"/private")
    private_key_marker = b"-----BEGIN OPENSSH " + b"PRIVATE KEY-----"
    with pytest.raises(builder.ReleaseBuildError, match="secret-like"):
        builder.assert_public_payload("config.txt", b"key=" + private_key_marker)
    with pytest.raises(builder.ReleaseBuildError, match="secret-like"):
        builder.assert_public_payload("opencode.jsonc", b"key=" + private_key_marker)
    for denied in (
        ".env",
        ".env.production",
        ".opencode/config.json.bak-20260815",
        "data/user.json",
        "nested/backups/.opencode/config.json",
        "nested/logs/runtime.txt",
        "core/.context/sessions/2026-10-16.json",
        "core/.context/.cache/context.json",
        "core/.context/knowledge/errors/error-log.md",
        "state.sqlite",
        "run.log",
    ):
        assert builder.is_denied_path(denied), denied
    for public in (
        ".opencode/config.json",
        ".opencode/agent/FreakingJSON.md",
        "core/skills/core/ui-ux-pro-max/data/colors.csv",
    ):
        assert not builder.is_denied_path(public), public


def test_extracted_package_installer_dry_run(tmp_path: Path, release_repo: Path):
    builder = load_builder()
    package = builder.build_release_zip(tmp_path / "dist", repo_root=release_repo)
    extracted = tmp_path / "candidate"
    with zipfile.ZipFile(package) as archive:
        archive.extractall(extracted)

    env = {**os.environ, "HOME": str(tmp_path / "home"), "USERPROFILE": str(tmp_path / "home")}
    result = subprocess.run(
        [
            sys.executable,
            "core/scripts/install.py",
            "--non-interactive",
            "--dry-run",
            "--json",
            "--no-browser",
        ],
        cwd=extracted,
        env=env,
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert result.returncode == 0, result.stderr or result.stdout
    report = json.loads(result.stdout)
    assert report["ok"] is True
    assert report["mode"] == "dry-run"
    assert report["writes"] == []
    assert report["version"] == "0.4.1-beta"


PUBLIC_CONTEXT_ALLOWLIST = (
    "core/.context/.gitkeep",
    "core/.context/MASTER.template.md",
    "core/.context/codebase/backlog.seed.md",
    "core/.context/knowledge/.gitkeep",
    "core/.context/knowledge/README.md",
    "core/.context/knowledge/agents-index.json",
    "core/.context/knowledge/learning/.gitkeep",
    "core/.context/knowledge/prompts/.gitkeep",
    "core/.context/knowledge/self-healing/.gitkeep",
    "core/.context/knowledge/skills-index.json",
    "core/.context/knowledge/wiki/README.md",
    "core/.context/knowledge/wiki/comparisons/.gitkeep",
    "core/.context/knowledge/wiki/concepts/.gitkeep",
    "core/.context/knowledge/wiki/entities/.gitkeep",
    "core/.context/knowledge/wiki/queries/.gitkeep",
    "core/.context/knowledge/wiki/raw/extracts/.gitkeep",
    "core/.context/knowledge/wiki/raw/inputs/.gitkeep",
    "core/.context/knowledge/wiki/raw/observations/.gitkeep",
    "core/.context/navigation.md",
    "core/.context/opencode-reference.md",
    "core/.context/profile.template.md",
    "core/.context/quick-start.md",
)


def context_members(names: list[str]) -> list[str]:
    return sorted(name for name in names if name.startswith("core/.context/"))


def test_context_ships_exact_public_allowlist(tmp_path: Path, release_repo: Path):
    builder = load_builder()
    package = builder.build_release_zip(tmp_path / "dist", repo_root=release_repo)
    with zipfile.ZipFile(package) as archive:
        assert context_members(archive.namelist()) == sorted(PUBLIC_CONTEXT_ALLOWLIST)
        for name in PUBLIC_CONTEXT_ALLOWLIST:
            assert name in archive.namelist(), name


def test_no_private_runtime_surface_is_tracked_or_packaged(release_repo: Path):
    builder = load_builder()
    files, _excluded = builder.archive_files(release_repo, "HEAD")
    for name in files:
        assert not builder.is_denied_context_path(name), name
        assert ".bak" not in Path(name).name.lower(), name
    with open(ROOT / ".gitignore", encoding="utf-8") as handle:
        gitignore = handle.read()
    assert "core/.context/memory/**" in gitignore
    assert "core/.context/knowledge/users/**" in gitignore
    assert "core/.context/knowledge/errors/**" in gitignore
    assert "core/.context/.migration_state.json" in gitignore
    assert "core/.context/knowledge_base.json" in gitignore
    assert "core/.context/knowledge/interactions-index.json" in gitignore
    assert "core/.context/knowledge/knowledge-index.json" in gitignore
    assert "core/.context/knowledge/last_mined.json" in gitignore
    assert "core/.context/knowledge/learning/best-practices.md" in gitignore
    assert "core/.context/knowledge/learning/discoveries.md" in gitignore
    assert "core/.context/knowledge/prompts/registry.json" in gitignore
    assert "core/.context/knowledge/sessions-index.json" in gitignore
    assert "core/.context/knowledge/insights/error-analysis.md" in gitignore
    assert ".opencode/*.bak*" in gitignore


def test_root_data_ignored_but_nested_skill_data_kept(tmp_path: Path, release_repo: Path):
    builder = load_builder()
    tracked_root = subprocess.run(
        ["git", "ls-files", "data/"],
        cwd=release_repo,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.splitlines()
    assert tracked_root == []
    nested_asset = "core/skills/core/ui-ux-pro-max/data/colors.csv"
    tracked_nested = subprocess.run(
        ["git", "ls-files", nested_asset],
        cwd=release_repo,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.splitlines()
    assert tracked_nested == [nested_asset]
    assert builder.is_denied_path("data/dashboard.token")
    assert not builder.is_denied_path(nested_asset)
    package = builder.build_release_zip(tmp_path / "dist", repo_root=release_repo)
    with zipfile.ZipFile(package) as archive:
        names = archive.namelist()
    assert not any(name == "data" or name.startswith("data/") for name in names)
    assert nested_asset in names


def test_public_source_omits_dangerous_deprecated_uninstaller(release_repo: Path):
    assert not (release_repo / "core/scripts/deprecated/uninstall.py").exists()


def test_accidentally_tracked_private_file_never_reaches_zip(
    tmp_path: Path, release_repo: Path
):
    builder = load_builder()
    leak = release_repo / "core/.context/memory/session.json"
    leak.parent.mkdir(parents=True, exist_ok=True)
    leak.write_text('{"secret": "local-only"}\n', encoding="utf-8")
    subprocess.run(["git", "add", "-f", "core/.context/memory/session.json"], cwd=release_repo, check=True)
    subprocess.run(
        [
            "git",
            "-c",
            "user.name=PA Release Tests",
            "-c",
            "user.email=release-tests@example.invalid",
            "commit",
            "-qm",
            "accidental private tracking fixture",
        ],
        cwd=release_repo,
        check=True,
    )
    package = builder.build_release_zip(tmp_path / "dist", repo_root=release_repo)
    with zipfile.ZipFile(package) as archive:
        names = archive.namelist()
        assert "core/.context/memory/session.json" not in names
        assert context_members(names) == sorted(PUBLIC_CONTEXT_ALLOWLIST)
        manifest = json.loads(archive.read(builder.MANIFEST_NAME))
    assert "core/.context/memory/session.json" in manifest["excluded"]


def test_fresh_extract_regenerates_local_runtime_state(tmp_path: Path, release_repo: Path):
    package = load_builder().build_release_zip(tmp_path / "dist", repo_root=release_repo)
    extracted = tmp_path / "candidate"
    with zipfile.ZipFile(package) as archive:
        archive.extractall(extracted)
    env = {
        **os.environ,
        "HOME": str(tmp_path / "home"),
        "USERPROFILE": str(tmp_path / "home"),
    }
    fixed = subprocess.run(
        [sys.executable, "core/scripts/system_check.py", "--fix", "--quiet-first-run"],
        cwd=extracted,
        env=env,
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert fixed.returncode == 0, fixed.stderr or fixed.stdout

    context = extracted / "core/.context"
    generated = [
        context / "MASTER.md",
        context / "profile.md",
        context / "codebase/backlog.md",
        context / "knowledge/sessions-index.json",
        context / "memory/context_injection.md",
    ]
    for path in generated:
        assert path.is_file(), path
    index = json.loads((context / "knowledge/sessions-index.json").read_text(encoding="utf-8"))
    assert index.get("total_sessions") == 0
    assert index.get("sessions") == []
    assert (context / "memory/context_injection.md").read_text(
        encoding="utf-8"
    ).startswith("# Context Injection")
    seeded_backlog = (context / "codebase/backlog.seed.md").read_text(encoding="utf-8")
    assert (context / "codebase/backlog.md").read_text(encoding="utf-8") == seeded_backlog


def test_workflow_declares_only_supported_blocking_lanes():
    workflow = (ROOT / ".github" / "workflows" / "release-gates.yml").read_text(encoding="utf-8")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    readme_plain = readme.replace("**", "")
    for label in ("Linux x64", "Windows x64", "macOS arm64"):
        assert label in workflow
        assert label in readme
    for unsupported in ("Windows arm64", "Linux arm64", "macOS Intel"):
        assert unsupported in readme
        assert f"{unsupported} — no soportado" in readme_plain
    assert workflow.count("python -m pip install -r requirements-dev.txt") == 3
    assert "python -m compileall -q core/scripts tests core/memory core/recovery" in workflow
    assert "python core/scripts/install.py --non-interactive --dry-run --json --no-browser" in workflow
    assert "pa.bat --help" in workflow
    assert "browser-gate:" in workflow
    assert workflow.count("macOS arm64") >= 2
    assert "python -m pytest tests core/scripts/tests -q" in workflow
    assert "tests/test_public_package.py" in workflow
    assert "dist/*.zip" in workflow

    release_gate = (ROOT / "tests" / "gates" / "release_gate.py").read_text(encoding="utf-8")
    assert "def fresh_extract_gate()" in release_gate
    assert '["git", "archive", tree]' in release_gate
    assert "receipts.append(fresh_extract_gate())" in release_gate
    assert "def migration_gate()" in release_gate
    assert '"v0.4.0-beta^{commit}"' in release_gate
    assert "receipts.append(migration_gate())" in release_gate
