"""RC5 active documentation and metadata truth contracts."""
from __future__ import annotations

import ast
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_active_agent_docs_do_not_link_missing_agents_full():
    active = (
        ROOT / "AGENTS-lite.md",
        ROOT / "AGENTS.md",
        ROOT / "docs" / "api" / "README.md",
    )

    offenders = [
        path.relative_to(ROOT).as_posix()
        for path in active
        if "AGENTS-full.md" in path.read_text(encoding="utf-8")
    ]

    assert offenders == []


def test_update_guide_exists_with_current_safety_contract():
    guide = ROOT / "docs" / "UPDATE-GUIDE.md"

    assert guide.is_file()
    content = guide.read_text(encoding="utf-8")
    for required in (
        "python core/scripts/update.py --check",
        "data/user",
        "data/sessions.db",
        "data/user_memory.db",
        "data/backups/pre-migration-",
        "python core/scripts/rollback.py --snapshot",
    ):
        assert required in content


def test_active_documentation_relative_links_resolve():
    active = (
        ROOT / "AGENTS-lite.md",
        ROOT / "AGENTS.md",
        ROOT / "README_en.md",
        ROOT / "docs" / "api" / "README.md",
        ROOT / "docs" / "technical" / "README-FULL.md",
        ROOT / "docs" / "WINDOWS-CHECKLIST.md",
        ROOT / "docs" / "UPDATE-GUIDE.md",
    )
    broken: list[str] = []

    for path in active:
        content = path.read_text(encoding="utf-8")
        for target in re.findall(r"\[[^]]+\]\(([^)]+)\)", content):
            target = target.split("#", 1)[0]
            if not target or "://" in target or target.startswith("mailto:"):
                continue
            if not (path.parent / target).resolve().exists():
                broken.append(f"{path.relative_to(ROOT).as_posix()} -> {target}")

    assert broken == []


def test_current_kb_init_commands_use_canonical_script_name():
    active = (
        ROOT / "README_en.md",
        ROOT / "docs" / "technical" / "README-FULL.md",
        ROOT / "core" / "scripts" / "session_start.py",
        ROOT / "core" / "scripts" / "kb_init.py",
    )

    offenders = [
        path.relative_to(ROOT).as_posix()
        for path in active
        if "kb-init.py" in path.read_text(encoding="utf-8")
    ]

    assert offenders == []


def test_windows_checklist_uses_directory_snapshot_contract():
    checklist = (ROOT / "docs" / "WINDOWS-CHECKLIST.md").read_text(encoding="utf-8")

    assert "data\\rollback" not in checklist
    assert "data\\backups\\pre-migration-<timestamp>" in checklist
    assert ".tar.gz" not in checklist


def test_control_panel_module_docstring_does_not_embed_release_version():
    source = (ROOT / "core" / "scripts" / "pa.py").read_text(encoding="utf-8")
    docstring = ast.get_docstring(ast.parse(source)) or ""

    assert "Control Panel" in docstring
    assert re.search(r"\bv\d+\.\d+\.\d+", docstring) is None
