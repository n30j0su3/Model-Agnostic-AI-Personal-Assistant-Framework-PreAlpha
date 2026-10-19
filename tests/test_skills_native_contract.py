"""Contract tests for native Markdown skills and their OpenCode integration.

These tests guard the skills layer that replaced the old TOML executor:
- every SKILL.md has valid, portable frontmatter;
- catalog, skill folders and SKILLS.md stay aligned;
- OpenCode loads the framework path and the local plugin from its canonical
  auto-load directory;
- the retired TOML system is gone and does not reappear in user-facing help.
"""
from __future__ import annotations

import importlib.util
import json
import re
from pathlib import Path

try:  # optional: full YAML validation when PyYAML is available
    import yaml
except ImportError:  # pragma: no cover - CI keeps requirements-dev minimal
    yaml = None

ROOT = Path(__file__).resolve().parents[1]
SKILLS_DIR = ROOT / "core" / "skills" / "core"
CATALOG = ROOT / "core" / "skills" / "catalog.json"
SKILLS_MD = ROOT / "core" / "skills" / "SKILLS.md"
CONFIG = ROOT / "opencode.jsonc"
PLUGIN = ROOT / ".opencode" / "plugins" / "freakingjson-framework.ts"

SLUG_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


def _minimal_frontmatter(text: str) -> dict:
    """Small fallback parser for the simple frontmatter used by SKILL.md."""
    data: dict = {}
    section: str | None = None
    for raw in text.splitlines():
        line = raw.rstrip()
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if line.startswith((" ", "\t")):
            if section is None or ":" not in line:
                continue
            key, value = line.strip().split(":", 1)
            data.setdefault(section, {})[key.strip()] = value.strip().strip("\"'")
            continue
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        key, value = key.strip(), value.strip()
        if value:
            data[key] = value.strip("\"'")
        else:
            section = key
            data[key] = {}
    return data


def _frontmatter(path: Path) -> dict:
    text = path.read_text(encoding="utf-8-sig")
    assert text.startswith("---"), f"{path}: must start with frontmatter"
    parts = text.split("---", 2)
    assert len(parts) == 3, f"{path}: unterminated frontmatter"
    if yaml is not None:
        data = getattr(yaml, "safe_load")(parts[1])
    else:
        data = _minimal_frontmatter(parts[1])
    assert isinstance(data, dict), f"{path}: frontmatter is not a mapping"
    return data


def _strip_jsonc(text: str) -> str:
    """Remove // and /* */ comments without touching strings."""
    out: list[str] = []
    in_str = False
    escaped = False
    i = 0
    while i < len(text):
        ch = text[i]
        if in_str:
            out.append(ch)
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == '"':
                in_str = False
            i += 1
            continue
        if ch == '"':
            in_str = True
            out.append(ch)
            i += 1
            continue
        if ch == "/" and i + 1 < len(text) and text[i + 1] == "/":
            i += 2
            while i < len(text) and text[i] not in "\r\n":
                i += 1
            continue
        if ch == "/" and i + 1 < len(text) and text[i + 1] == "*":
            i += 2
            while i + 1 < len(text) and not (text[i] == "*" and text[i + 1] == "/"):
                i += 1
            i += 2
            continue
        out.append(ch)
        i += 1
    return "".join(out)


def test_all_skill_directories_have_valid_portable_frontmatter():
    skill_dirs = sorted(p for p in SKILLS_DIR.iterdir() if p.is_dir())
    assert len(skill_dirs) == 23

    for skill_dir in skill_dirs:
        skill_md = skill_dir / "SKILL.md"
        assert skill_md.is_file(), f"missing {skill_md}"
        fm = _frontmatter(skill_md)
        assert fm.get("name") == skill_dir.name, f"{skill_dir.name}: name mismatch"
        assert SLUG_RE.fullmatch(skill_dir.name), f"{skill_dir.name}: invalid slug"
        description = fm.get("description")
        assert isinstance(description, str) and 1 <= len(description) <= 1024
        assert fm.get("license"), f"{skill_dir.name}: missing license"
        assert isinstance(fm.get("metadata", {}), dict)


def test_catalog_and_skills_md_cover_the_same_23_skills():
    skill_names = {p.name for p in SKILLS_DIR.iterdir() if p.is_dir()}
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    catalog_names = set(catalog.get("skills", {}))
    assert catalog_names == skill_names
    assert len(catalog_names) == 23

    table_names = set(
        re.findall(r"^\| \*\*@([a-z0-9-]+)\*\*", SKILLS_MD.read_text(encoding="utf-8"), re.M)
    )
    assert table_names == skill_names


def test_opencode_registers_skills_and_canonical_plugin():
    config = json.loads(_strip_jsonc(CONFIG.read_text(encoding="utf-8")))
    paths = config.get("skills", {}).get("paths", [])
    assert "core/skills/core" in paths
    assert config.get("default_agent") == "FreakingJSON"
    assert PLUGIN.is_file(), "plugin must live in .opencode/plugins/ for auto-load"
    assert not (ROOT / ".opencode" / "plugin").exists()
    plugin_text = PLUGIN.read_text(encoding="utf-8")
    assert "experimental.chat.system.transform" in plugin_text
    assert "config.skills" in plugin_text
    # `plugin` is for npm packages; local files are auto-loaded from the directory.
    for entry in config.get("plugin", []):
        assert not str(entry).startswith((".", "/")), (
            "local plugin paths must not be declared as npm plugins"
        )


def test_retired_toml_system_is_absent_and_help_is_consistent():
    assert not (ROOT / "core" / "skills" / "skill_executor.py").exists()
    assert not (ROOT / "core" / "scripts" / "skill_creator.py").exists()
    assert not (ROOT / "core" / "skills" / "skill-creator.md").exists()

    init_text = (ROOT / "core" / "skills" / "__init__.py").read_text(encoding="utf-8")
    assert "skill_executor" not in init_text

    pa_text = (ROOT / "core" / "scripts" / "pa.py").read_text(encoding="utf-8")
    assert "[CONFIG]   Skills" not in pa_text
    assert "Listar skills, [2] Habilitar" not in pa_text

    dashboard_text = (ROOT / "dashboard.html").read_text(encoding="utf-8")
    assert "SkillExecutor" not in dashboard_text
    assert "skill_executor.py" not in dashboard_text
    assert "skills/*.toml" not in dashboard_text


def _load_indexer():
    path = ROOT / "core" / "scripts" / "skills_indexer.py"
    spec = importlib.util.spec_from_file_location("skills_indexer_contract", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_indexer_prunes_legacy_ids_and_uses_catalog_category(tmp_path, monkeypatch):
    skills_dir = tmp_path / "core" / "skills" / "core"
    skills_dir.mkdir(parents=True)
    for name in ("alpha", "beta"):
        skill_dir = skills_dir / name
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(
            "---\n"
            f"name: {name}\n"
            f"description: {name} skill\n"
            "license: MIT\n"
            "---\n",
            encoding="utf-8",
        )
    catalog = tmp_path / "core" / "skills" / "catalog.json"
    catalog.write_text(
        json.dumps(
            {
                "skills": {
                    "alpha": {"category": "Development"},
                    "beta": {"category": "Content"},
                }
            }
        ),
        encoding="utf-8",
    )
    index_file = tmp_path / "core" / ".context" / "knowledge" / "skills-index.json"
    index_file.parent.mkdir(parents=True)
    index_file.write_text(
        json.dumps(
            {
                "skills": [
                    {"id": "Old Name", "name": "@Old Name"},
                    {"id": "alpha", "name": "@alpha", "category": "core"},
                ],
                "categories": {},
                "total_skills": 2,
                "last_updated": "2026-01-01",
            }
        ),
        encoding="utf-8",
    )

    module = _load_indexer()
    monkeypatch.setattr(module, "SKILLS_DIR", skills_dir)
    monkeypatch.setattr(module, "CATALOG_FILE", catalog)
    monkeypatch.setattr(module, "INDEX_FILE", index_file)
    module.SkillsIndexer().index_all_skills()

    index = json.loads(index_file.read_text(encoding="utf-8"))
    assert [s["id"] for s in index["skills"]] == ["alpha", "beta"]
    assert index["total_skills"] == 2
    assert {s["category"] for s in index["skills"]} == {"Development", "Content"}
