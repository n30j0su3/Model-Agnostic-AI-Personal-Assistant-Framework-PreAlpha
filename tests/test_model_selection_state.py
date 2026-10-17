"""User model selection belongs under ignored data/, never tracked config."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

from conftest import assert_private_file


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


def init_git(root: Path) -> None:
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    subprocess.run(["git", "add", "-A"], cwd=root, check=True)
    subprocess.run(
        [
            "git",
            "-c",
            "user.name=PA Test",
            "-c",
            "user.email=pa-test@example.invalid",
            "commit",
            "-qm",
            "fixture",
        ],
        cwd=root,
        check=True,
    )


def git_status(root: Path) -> str:
    return subprocess.run(
        ["git", "status", "--porcelain", "--untracked-files=all"],
        cwd=root,
        capture_output=True,
        text=True,
        check=True,
    ).stdout


def test_save_selection_does_not_touch_tracked_files(repo_extract):
    init_git(repo_extract)
    config = repo_extract / ".opencode/config.json"
    before_config = config.read_bytes()
    before_status = git_status(repo_extract)
    module = load_module(
        "select_free_model_state_test",
        repo_extract / "core/scripts/select_free_model.py",
    )

    state = module.save_selection("opencode/test-free", repo_root=repo_extract)

    selection = repo_extract / "data/user/model-selection.json"
    assert state["model"] == "opencode/test-free"
    assert json.loads(selection.read_text(encoding="utf-8"))["model"] == "opencode/test-free"
    assert_private_file(selection)
    assert config.read_bytes() == before_config
    assert git_status(repo_extract) == before_status


def test_selection_preserves_unknown_keys(repo_extract):
    module = load_module(
        "select_free_model_unknown_test",
        repo_extract / "core/scripts/select_free_model.py",
    )
    path = repo_extract / "data/user/model-selection.json"
    path.parent.mkdir(parents=True)
    path.write_text(
        json.dumps({"model": "old/model", "future": {"keep": True}}),
        encoding="utf-8",
    )

    module.save_selection("opencode/new-free", repo_root=repo_extract)

    state = json.loads(path.read_text(encoding="utf-8"))
    assert state == {"model": "opencode/new-free", "future": {"keep": True}}


def test_migration_from_opencode_config_is_one_time(repo_extract):
    config = repo_extract / ".opencode/config.json"
    original = json.loads(config.read_text(encoding="utf-8"))
    original["model"] = "opencode/legacy-free"
    original["unknown"] = "preserve-in-opencode"
    config.write_text(json.dumps(original, indent=2), encoding="utf-8")
    module = load_module(
        "select_free_model_migration_test",
        repo_extract / "core/scripts/select_free_model.py",
    )

    first = module.load_selection(repo_root=repo_extract)
    original["model"] = "opencode/changed-later"
    config.write_text(json.dumps(original, indent=2), encoding="utf-8")
    second = module.load_selection(repo_root=repo_extract)

    assert first["model"] == "opencode/legacy-free"
    assert second["model"] == "opencode/legacy-free"
    assert json.loads(config.read_text(encoding="utf-8"))["unknown"] == "preserve-in-opencode"


def test_ensure_data_dirs_creates_user_and_wizard(repo_extract):
    module = load_module(
        "ensure_data_dirs_test",
        repo_extract / "core/scripts/ensure_data_dirs.py",
    )

    paths = module.ensure_data_dirs(repo_extract)

    assert paths["user"] == repo_extract / "data/user"
    assert paths["wizard"] == repo_extract / "data/wizard"
    assert all(path.is_dir() for path in paths.values())
