"""Canonical version contract for public PA Framework surfaces."""

from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
from pathlib import Path

from conftest import subprocess_text_encoding


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "core" / "scripts"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {name}")
    module = importlib.util.module_from_spec(spec)
    previous = sys.modules.get(name)
    sys.modules[name] = module
    try:
        spec.loader.exec_module(module)
    except BaseException:
        if previous is None:
            sys.modules.pop(name, None)
        else:
            sys.modules[name] = previous
        raise
    return module


def test_version_file_is_canonical_and_render_is_surface_specific(tmp_path):
    version_file = tmp_path / "VERSION"
    version_file.write_text("v0.4.1-beta\n", encoding="utf-8")
    version = load_module("version", SCRIPTS / "version.py")

    canonical = version.canonical(tmp_path)

    assert canonical == "0.4.1-beta"
    assert version.render(canonical, "plain") == "0.4.1-beta"
    assert version.render(canonical, "badge") == "v0.4.1-beta"
    assert (ROOT / "VERSION").read_text(encoding="utf-8").strip() == "0.4.1-beta"


def test_cli_and_fallback_banner_never_render_double_v(tmp_path, monkeypatch, capsys):
    expected = "v0.4.1-beta"
    for flag in ("--help", "--version"):
        result = subprocess.run(
            [sys.executable, str(SCRIPTS / "pa.py"), flag],
            cwd=ROOT,
            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
            capture_output=True,
            text=True,
            encoding=subprocess_text_encoding(),
            check=False,
        )
        assert result.returncode == 0, result.stderr
        assert "vv" not in result.stdout
        assert expected in result.stdout

    pa = load_module("pa", SCRIPTS / "pa.py")
    isolated_root = tmp_path / "repo"
    isolated_root.mkdir()
    (isolated_root / "VERSION").write_text("v0.4.1-beta\n", encoding="utf-8")
    monkeypatch.setattr(pa, "REPO_ROOT", isolated_root)
    pa.print_banner()
    output = capsys.readouterr().out
    assert "vv" not in output
    assert expected in output

    system_check = load_module("system_check", SCRIPTS / "system_check.py")
    monkeypatch.setattr(system_check, "REPO_ROOT", isolated_root)
    ok, detail = system_check.check_version()
    assert ok is True
    assert detail == f"Framework {expected}"


def test_badge_css_class_is_not_parsed_as_a_version():
    updater = load_module("version_updater", SCRIPTS / "version_updater.py")

    assert updater.parse_version_from_text("badge-version-v0.4.0--beta-lime") is None
    assert updater.parse_version_from_text("v0.4.1-beta") == "0.4.1-beta"


def test_version_updater_targets_exist():
    updater = load_module("version_updater", SCRIPTS / "version_updater.py")

    missing = [relative for relative in updater.TARGETS if not (ROOT / relative).is_file()]
    assert missing == []


def test_version_updater_targets_only_real_static_tokens():
    updater = load_module("version_updater_targets", SCRIPTS / "version_updater.py")
    expected = {
        "README.md",
        "AGENTS.md",
        "AGENTS-lite.md",
        "config/framework.yaml",
        "ROADMAP.md",
    }
    assert set(updater.TARGETS) == expected

    detected = updater.detect_version_in_files()
    assert set(detected) == expected
    assert {info["detected"] for info in detected.values()} == {"0.4.1-beta"}


def test_roadmap_markdown_line_break_is_detected(tmp_path, monkeypatch):
    updater = load_module("version_updater", SCRIPTS / "version_updater.py")
    roadmap = tmp_path / "ROADMAP.md"
    roadmap.write_text(
        "**Versión actual**: v0.4.1-beta  \n",
        encoding="utf-8",
    )
    monkeypatch.setattr(updater, "get_root_dir", lambda: tmp_path)

    detected = updater.detect_version_in_files()

    assert detected["ROADMAP.md"]["detected"] == "0.4.1-beta"


def test_yaml_update_changes_only_top_level_version_key(tmp_path, monkeypatch):
    updater = load_module("version_updater", SCRIPTS / "version_updater.py")
    config = tmp_path / "config" / "framework.yaml"
    config.parent.mkdir(parents=True)
    config.write_text(
        "version: 0.4.0-beta\n"
        "note: preserve v9.9.9\n"
        "# Version: v0.4.0-beta documentation only\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(updater, "get_root_dir", lambda: tmp_path)

    updated = updater.apply_changes(
        [("config/framework.yaml", "0.4.0-beta", "0.4.1-beta")],
        "0.4.1-beta",
    )

    content = config.read_text(encoding="utf-8")
    assert updated == 1
    assert content.splitlines()[0] == "version: 0.4.1-beta"
    assert "note: preserve v9.9.9" in content
    assert "# Version: v0.4.0-beta documentation only" in content
