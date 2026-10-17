"""Durable core tests for the semantic workspace configuration authority.

Covers the W1 contract for ``core/scripts/workspace_config.py``:

- canonical six semantic keys with no user data (tracked config file);
- safe directory-name validation across Windows/Linux/macOS;
- load/save of the per-install selection (atomic, 0600, exact statuses
  ``missing`` / ``empty`` / ``present``; corrupt counts as empty, no fallback);
- key alias and custom safe-key normalization;
- resolver precedence: configured cwd > explicit key > legacy ``content``
  fallback ONLY when the user config file is missing; present configs fail
  closed; sibling ``workspaces-extra`` never matches;
- all path math honors the passed ``repo_root`` (never a module global) and
  containment fails closed instead of silently normalizing traversal;
- MASTER ``## Active Workspaces`` rendering for LF and CRLF with configured
  display names;
- agent rules containing all six semantic examples and no unconditional
  content routing.

Run with: python3.11 -m pytest tests/test_workspace_config_core.py -q
"""

from __future__ import annotations

import importlib.util
import json
import re
import sys
from pathlib import Path

import pytest

from conftest import assert_private_file

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "core" / "scripts" / "workspace_config.py"


def _load_module():
    spec = importlib.util.spec_from_file_location(
        "workspace_config_core_test", MODULE_PATH
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


workspace_config = _load_module()

ENTRIES = {"professional": {"dir": "Trabajo", "display": "Trabajo"}}

SIX_KEYS = {
    "personal",
    "professional",
    "research",
    "content",
    "development",
    "homelab",
}


@pytest.fixture
def repo(tmp_path) -> Path:
    """A throwaway install root with a configured workspace and a sibling."""
    root = tmp_path.resolve() / "repo"
    (root / "workspaces" / "Trabajo" / "projects").mkdir(parents=True)
    (root / "workspaces-extra" / "x").mkdir(parents=True)
    return root


# ---------------------------------------------------------------------------
# Canonical definitions: six semantic keys, no user data
# ---------------------------------------------------------------------------


def test_semantic_keys_are_exactly_the_six_canonical_keys():
    assert set(workspace_config.SEMANTIC_KEYS) == SIX_KEYS


def test_tracked_canonical_config_has_six_keys_and_no_user_data():
    raw = json.loads(
        (ROOT / "config" / "workspaces.json").read_text(encoding="utf-8")
    )
    workspace_keys = {key for key in raw if not key.startswith("_")}
    assert workspace_keys == SIX_KEYS
    for key, value in raw.items():
        if key.startswith("_"):
            assert isinstance(value, str)  # comments only, never user data
        else:
            assert isinstance(value, dict)
            assert set(value) == {"display"}
            assert isinstance(value["display"], str)
            assert value["display"]  # non-empty display name


def test_load_canonical_definitions_returns_six_entries_with_display_only():
    definitions = workspace_config.load_canonical_definitions()
    assert set(definitions) == SIX_KEYS
    for key, entry in definitions.items():
        assert set(entry) == {"display"}
        assert entry["display"]


def test_load_canonical_definitions_custom_path_filters_unknown_and_meta(tmp_path):
    source = tmp_path / "workspaces.json"
    source.write_text(
        json.dumps(
            {
                "_comment": "meta only",
                "personal": {"display": "Personal"},
                "bogus": {"display": "Bogus"},
                "research": {"display": "Investigación"},
                "development": {"display": "../escape"},
            }
        ),
        encoding="utf-8",
    )
    definitions = workspace_config.load_canonical_definitions(source)
    assert set(definitions) == {"personal", "research", "development"}
    assert definitions["research"] == {"display": "Investigación"}
    # Unsafe display falls back to the capitalized semantic key.
    assert definitions["development"] == {"display": "Development"}


def test_canonical_display_uses_tracked_config():
    assert workspace_config.canonical_display("research") == "Research"
    # Unknown keys fall back to the capitalize() convention.
    key = "nonexistent-key"
    assert workspace_config.canonical_display(key) == key.capitalize()


def test_default_paths_are_repo_anchored():
    assert workspace_config.ROOT == ROOT
    assert workspace_config.CANONICAL_DEFINITIONS_PATH == ROOT / "config" / "workspaces.json"
    assert workspace_config.USER_CONFIG_PATH == ROOT / "data" / "user" / "workspaces.json"


# ---------------------------------------------------------------------------
# safe_name: cross-platform directory-name validation
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "value",
    ["Personal", "Trabajo", "Work", "my-lab", "Investigación", "a" * 100],
)
def test_safe_name_accepts(value):
    assert workspace_config.safe_name(value) == value


@pytest.mark.parametrize(
    "value",
    [
        "",  # empty
        "   ",  # whitespace only
        ".",  # current dir
        "..",  # parent dir
        ".hidden",  # hidden name
        "../x",  # traversal
        "x/y",  # separator
        "/abs",  # absolute POSIX
        "/tmp/x",  # absolute POSIX deep
        "C:",  # drive form
        "C:/x",  # drive + path
        "c:\\temp",  # lowercase drive + backslash
        "\\\\server\\share",  # UNC
        "\\\\?\\C:\\x",  # extended-length UNC
        "name\x01",  # control char
        "na\tme",  # internal tab
        "name\n",  # trailing newline (control char)
        "CON",
        "con",
        "Con.txt",
        "CON.TXT",
        "PRN",
        "prn",
        "AUX",
        "aux",
        "NUL",
        "nul",
        *tuple(f"COM{i}" for i in range(1, 10)),
        *tuple(f"LPT{i}" for i in range(1, 10)),
        "COM1.txt",
        "LPT9.log",
        "Trabajo ",  # trailing literal space (must NOT be silently trimmed)
        "name ",
        "name.",  # trailing literal dot
        "a" * 101,  # over max length
        None,  # non-strings
        42,
        3.14,
        [],
        {},
    ],
)
def test_safe_name_rejects(value):
    assert workspace_config.safe_name(value) is None


# ---------------------------------------------------------------------------
# User config: load statuses, normalization, atomic save
# ---------------------------------------------------------------------------


def _write_user_config(repo: Path, text: str) -> None:
    (repo / "data" / "user").mkdir(parents=True, exist_ok=True)
    (repo / "data" / "user" / "workspaces.json").write_text(text, encoding="utf-8")


def test_config_status_values_are_exactly_missing_empty_present(repo):
    assert workspace_config.config_status(repo) == "missing"

    _write_user_config(repo, "{}")
    assert workspace_config.config_status(repo) == "empty"

    _write_user_config(repo, '{"workspaces": {}}')
    assert workspace_config.config_status(repo) == "empty"

    _write_user_config(repo, "{ this is not json ")
    assert workspace_config.config_status(repo) == "empty"

    _write_user_config(
        repo, '{"schema": 1, "workspaces": {"professional": "Trabajo"}}'
    )
    assert workspace_config.config_status(repo) == "present"


def test_load_user_config_missing(repo):
    status, entries = workspace_config.load_user_config(repo)
    assert status == "missing"
    assert entries == {}


def test_load_user_config_present_normalizes_entries(repo):
    _write_user_config(
        repo,
        json.dumps(
            {
                "schema": 1,
                "workspaces": {"professional": {"dir": "Trabajo", "display": "Trabajo"}},
            }
        ),
    )
    status, entries = workspace_config.load_user_config(repo)
    assert status == "present"
    assert entries == {"professional": {"dir": "Trabajo", "display": "Trabajo"}}


def test_load_user_config_display_defaults_to_dir(repo):
    _write_user_config(repo, '{"workspaces": {"research": "Investigación"}}')
    status, entries = workspace_config.load_user_config(repo)
    assert status == "present"
    assert entries == {
        "research": {"dir": "Investigación", "display": "Investigación"}
    }


def test_load_user_config_drops_unsafe_entries_and_counts_empty(repo):
    _write_user_config(repo, '{"workspaces": {"professional": "../escape"}}')
    status, entries = workspace_config.load_user_config(repo)
    assert status == "empty"
    assert entries == {}


def test_load_user_config_alias_normalization(repo):
    _write_user_config(
        repo,
        json.dumps({"workspaces": {"trabajo": "Trabajo", "dev": {"dir": "Dev"}}}),
    )
    status, entries = workspace_config.load_user_config(repo)
    assert status == "present"
    assert set(entries) == {"professional", "development"}
    assert entries["professional"]["dir"] == "Trabajo"
    assert entries["development"]["dir"] == "Dev"


def test_load_user_config_custom_safe_key_preserved(repo):
    _write_user_config(repo, json.dumps({"workspaces": {"my-lab": "my-lab"}}))
    status, entries = workspace_config.load_user_config(repo)
    assert status == "present"
    assert entries == {"my-lab": {"dir": "my-lab", "display": "my-lab"}}


def test_load_user_config_corrupt_is_empty_not_missing(repo):
    _write_user_config(repo, "]]]corrupt{{{")
    status, entries = workspace_config.load_user_config(repo)
    assert status == "empty"
    assert entries == {}


def test_normalize_key_aliases_and_passthrough():
    normalize = workspace_config.normalize_key
    assert normalize("Work") == "professional"
    assert normalize("TRABAJO") == "professional"
    assert normalize("job") == "professional"
    assert normalize("Dev") == "development"
    assert normalize("lab") == "homelab"
    assert normalize("casa") == "homelab"
    assert normalize("contenido") == "content"
    assert normalize("Personal") == "personal"
    assert normalize("my-lab") == "my-lab"  # custom key passes through
    assert normalize("") == ""


def test_is_semantic_key():
    assert workspace_config.is_semantic_key("work")
    assert workspace_config.is_semantic_key("homelab")
    assert not workspace_config.is_semantic_key("my-lab")
    assert not workspace_config.is_semantic_key("")


def test_save_user_config_atomic_0600_and_roundtrip(repo):
    returned = workspace_config.save_user_config({"Work": "Trabajo"}, repo_root=repo)
    assert returned == {"professional": {"dir": "Trabajo", "display": "Trabajo"}}

    destination = repo / "data" / "user" / "workspaces.json"
    assert_private_file(destination)

    # Atomic write: no temporary siblings left behind.
    siblings = sorted(p.name for p in destination.parent.iterdir())
    assert siblings == ["workspaces.json"]

    payload = json.loads(destination.read_text(encoding="utf-8"))
    assert payload["workspaces"] == {
        "professional": {"dir": "Trabajo", "display": "Trabajo"}
    }

    status, entries = workspace_config.load_user_config(repo)
    assert status == "present"
    assert entries == returned


def test_save_user_config_rejects_invalid_input(repo):
    with pytest.raises(ValueError):
        workspace_config.save_user_config({}, repo_root=repo)
    with pytest.raises(ValueError):
        workspace_config.save_user_config({"professional": "../escape"}, repo_root=repo)
    with pytest.raises(ValueError):
        workspace_config.save_user_config({"../x": "ok"}, repo_root=repo)
    with pytest.raises(ValueError):
        workspace_config.save_user_config("not-a-mapping", repo_root=repo)


# ---------------------------------------------------------------------------
# Path calculation honors repo_root (never the module global)
# ---------------------------------------------------------------------------


def test_workspace_dir_for_honors_passed_repo_root(repo):
    result = workspace_config.workspace_dir_for(
        ENTRIES, "professional", repo_root=repo
    )
    assert result == repo / "workspaces" / "Trabajo"


def test_workspace_dir_for_unknown_key_raises(repo):
    with pytest.raises(KeyError):
        workspace_config.workspace_dir_for(ENTRIES, "homelab", repo_root=repo)


def test_project_dir_for_honors_passed_repo_root(repo):
    result = workspace_config.project_dir_for(ENTRIES, "professional", repo_root=repo)
    assert result == repo / "workspaces" / "Trabajo" / "projects"


# ---------------------------------------------------------------------------
# Resolver precedence and fail-closed behavior
# ---------------------------------------------------------------------------


def test_resolver_cwd_inside_configured_workspace_wins(repo):
    deep = repo / "workspaces" / "Trabajo" / "projects" / "deep"
    result = workspace_config.resolve_workspace(ENTRIES, cwd=deep, repo_root=repo)
    assert result["ok"] is True
    assert result["source"] == "cwd"
    assert result["key"] == "professional"
    assert result["dir"] == "Trabajo"
    assert result["name"] == "Trabajo"


def test_resolver_cwd_exact_workspace_root_matches(repo):
    result = workspace_config.resolve_workspace(
        ENTRIES, cwd=repo / "workspaces" / "Trabajo", repo_root=repo
    )
    assert result["ok"] is True
    assert result["source"] == "cwd"


def test_resolver_cwd_in_unconfigured_workspace_dir_fails_closed(repo):
    result = workspace_config.resolve_workspace(
        ENTRIES, cwd=repo / "workspaces" / "Otro", repo_root=repo
    )
    assert result["ok"] is False


def test_resolver_sibling_workspaces_extra_never_matches(repo):
    result = workspace_config.resolve_workspace(
        ENTRIES, cwd=repo / "workspaces-extra" / "x", repo_root=repo
    )
    assert result["ok"] is False
    assert result["reason"] == "workspaces-not-selected"


def test_resolver_sibling_with_explicit_key_still_resolves(repo):
    result = workspace_config.resolve_workspace(
        ENTRIES,
        cwd=repo / "workspaces-extra" / "x",
        explicit_key="professional",
        repo_root=repo,
    )
    assert result["ok"] is True
    assert result["source"] == "explicit-key"
    assert result["dir"] == "Trabajo"


def test_resolver_cwd_beats_explicit_key(repo):
    inside = repo / "workspaces" / "Trabajo" / "projects"
    result = workspace_config.resolve_workspace(
        ENTRIES, cwd=inside, explicit_key="lab", repo_root=repo
    )
    assert result["ok"] is True
    assert result["source"] == "cwd"
    assert result["key"] == "professional"


def test_resolver_explicit_key_with_alias(repo):
    result = workspace_config.resolve_workspace(
        ENTRIES, explicit_key="Work", repo_root=repo
    )
    assert result["ok"] is True
    assert result["source"] == "explicit-key"
    assert result["key"] == "professional"
    assert result["dir"] == "Trabajo"
    assert result["name"] == "Trabajo"


def test_resolver_explicit_key_content_is_not_special(repo):
    entries = {"content": {"dir": "content", "display": "Content"}}
    result = workspace_config.resolve_workspace(entries, explicit_key="content")
    assert result["ok"] is True
    assert result["source"] == "explicit-key"


def test_resolver_explicit_key_not_configured_fails_closed(repo):
    result = workspace_config.resolve_workspace(
        ENTRIES, explicit_key="lab", repo_root=repo
    )
    assert result["ok"] is False
    assert result["reason"] == "workspace-not-configured"


def test_resolver_present_without_key_fails_closed(repo):
    result = workspace_config.resolve_workspace(ENTRIES, repo_root=repo)
    assert result["ok"] is False
    assert result["reason"] == "workspaces-not-selected"


def test_resolver_present_empty_fails_closed():
    result = workspace_config.resolve_workspace({}, status="empty")
    assert result["ok"] is False


def test_resolver_empty_entries_inferred_fail_closed():
    result = workspace_config.resolve_workspace({})
    assert result["ok"] is False


def test_resolver_missing_config_legacy_content_fallback():
    result = workspace_config.resolve_workspace({}, status="missing")
    assert result["ok"] is True
    assert result["key"] == "content"
    assert result["dir"] == "content"
    assert result["name"] == "Content"
    assert result["source"] == "fallback"


def test_corrupt_config_counts_as_empty_and_never_falls_back(repo):
    _write_user_config(repo, "not json at all {")
    status, entries = workspace_config.load_user_config(repo)
    assert status == "empty"
    result = workspace_config.resolve_workspace(entries, status=status, repo_root=repo)
    assert result["ok"] is False  # no legacy content fallback


# ---------------------------------------------------------------------------
# Project paths: containment fail-closed
# ---------------------------------------------------------------------------


def test_project_path_under_renamed_workspace(repo):
    result = workspace_config.project_path(
        ENTRIES, "professional", "informe-q3", repo_root=repo
    )
    expected = (repo / "workspaces" / "Trabajo" / "projects" / "informe-q3").resolve()
    assert result == expected


def test_project_path_containment_holds(repo):
    result = workspace_config.project_path(
        ENTRIES, "professional", "informe-q3", repo_root=repo
    )
    projects_root = (repo / "workspaces" / "Trabajo" / "projects").resolve()
    assert result.is_relative_to(projects_root)


@pytest.mark.parametrize(
    "workdir",
    [
        "../escape",
        "/etc/passwd",
        "..\\escape",
        "C:\\evil",
        "Trabajo/projects/x",
        "",
        ".",
        "..",
        ".hidden",
        "informe.",
        "informe ",
        "name\x01",
        None,
        42,
    ],
)
def test_project_path_fails_closed_on_unsafe_input(repo, workdir):
    with pytest.raises(ValueError):
        workspace_config.project_path(
            ENTRIES, "professional", workdir, repo_root=repo
        )


def test_project_path_unknown_key_raises(repo):
    with pytest.raises(KeyError):
        workspace_config.project_path(ENTRIES, "homelab", "lab-notebook", repo_root=repo)


# ---------------------------------------------------------------------------
# MASTER section rendering
# ---------------------------------------------------------------------------


def test_master_active_workspaces_block_uses_configured_display_names():
    block = workspace_config.master_active_workspaces_block(ENTRIES)
    assert block == "- [ ] Trabajo (`workspaces/Trabajo`)"


def test_master_active_workspaces_block_sorted_by_key():
    entries = {
        "personal": {"dir": "Personal", "display": "Personal"},
        "development": {"dir": "Dev", "display": "Dev"},
    }
    block = workspace_config.master_active_workspaces_block(entries)
    assert block == (
        "- [ ] Dev (`workspaces/Dev`)\n- [ ] Personal (`workspaces/Personal`)"
    )


def test_render_master_workspaces_lf():
    master = (
        "# MASTER\n\n## Active Workspaces\n\n"
        "- [ ] Viejo (`workspaces/Viejo`)\n\n"
        "## Next\n\nbody\n"
    )
    entries = {"professional": {"dir": "Trabajo", "display": "Trabajo"}}
    rendered = workspace_config.render_master_workspaces(master, entries)
    assert rendered == (
        "# MASTER\n\n## Active Workspaces\n\n"
        "- [ ] Trabajo (`workspaces/Trabajo`)\n\n"
        "## Next\n\nbody\n"
    )
    assert "Viejo" not in rendered


def test_render_master_workspaces_crlf():
    master = (
        "# MASTER\r\n\r\n## Active Workspaces\r\n\r\n"
        "- [ ] Viejo (`workspaces/Viejo`)\r\n\r\n"
        "## Next\r\n\r\nbody\r\n"
    )
    entries = {"professional": {"dir": "Trabajo", "display": "Trabajo"}}
    rendered = workspace_config.render_master_workspaces(master, entries)
    assert rendered == (
        "# MASTER\r\n\r\n## Active Workspaces\r\n\r\n"
        "- [ ] Trabajo (`workspaces/Trabajo`)\r\n\r\n"
        "## Next\r\n\r\nbody\r\n"
    )
    assert "Viejo" not in rendered


def test_render_master_workspaces_section_at_end():
    master = "# MASTER\n\n## Active Workspaces\n\n- [ ] Viejo (`workspaces/Viejo`)\n"
    entries = {"research": {"dir": "Research", "display": "Research"}}
    rendered = workspace_config.render_master_workspaces(master, entries)
    assert rendered == (
        "# MASTER\n\n## Active Workspaces\n\n- [ ] Research (`workspaces/Research`)\n"
    )


def test_render_master_workspaces_without_heading_is_identity():
    master = "# MASTER\n\nno section here\n"
    assert workspace_config.render_master_workspaces(master, ENTRIES) == master


def test_render_master_workspaces_empty_entries_placeholder():
    master = "## Active Workspaces\n\n- [ ] Viejo (`workspaces/Viejo`)\n"
    rendered = workspace_config.render_master_workspaces(master, {})
    assert rendered == (
        "## Active Workspaces\n\n- (sin workspaces configurados)\n"
    )


# ---------------------------------------------------------------------------
# Agent rules: six examples, no unconditional content routing
# ---------------------------------------------------------------------------


def test_agent_rules_contain_all_six_examples():
    text = workspace_config.agent_workspace_rules(ENTRIES)
    for key in SIX_KEYS:
        assert key in text
    # The six examples are conditional domain mappings (arrow targets).
    assert text.count("→") >= 6


def test_agent_rules_have_no_unconditional_content_routing():
    text = workspace_config.agent_workspace_rules(ENTRIES)
    # The legacy content path must never be hard-routed in agent rules.
    assert "workspaces/content" not in text
    assert not re.search(r"(?i)\bdefault\b[^\n]*\bcontent\b", text)
    assert not re.search(r"(?i)\bcontent\b[^\n]*\bdefault\b", text)
    assert not re.search(r"(?i)por defecto[^\n]*\bcontent\b", text)
    assert not re.search(r"(?i)\bcontent\b[^\n]*por defecto", text)


def test_agent_rules_surface_configured_entries():
    text = workspace_config.agent_workspace_rules(ENTRIES)
    assert "Configured: Trabajo (Trabajo)" in text


def test_agent_rules_empty_entries_still_list_examples():
    text = workspace_config.agent_workspace_rules({})
    for key in SIX_KEYS:
        assert key in text
    assert "No workspaces configured yet." in text
