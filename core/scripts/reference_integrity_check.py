#!/usr/bin/env python3
"""Reference integrity checker for framework docs, agents, skills, and configs."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PREFIXES = (
    "core/",
    "docs/",
    "config/",
    ".opencode/",
    "README",
    "AGENTS",
    "VERSION",
    "ROADMAP",
    "CHANGELOG",
    "workspaces/",
)


def load_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def iter_targets() -> list[Path]:
    targets = [
        ROOT / "AGENTS.md",
        ROOT / "core" / "INIT-PROTOCOL.md",
        ROOT / "core" / ".context" / "navigation.md",
        ROOT / "core" / "skills" / "SKILLS.md",
    ]
    targets.extend((ROOT / "docs" / "core").glob("PRP-*.md"))
    targets.extend((ROOT / "core" / "agents").glob("**/*.md"))
    return [p for p in targets if p.exists()]


def extract_backtick_paths(text: str) -> set[str]:
    paths = set()
    for match in re.findall(r"`([^`]+)`", text):
        if match.startswith(PREFIXES):
            paths.add(match)
    return paths


def check_backtick_paths(issues: list[str]) -> None:
    for path in iter_targets():
        text = load_text(path)
        for ref in sorted(extract_backtick_paths(text)):
            if ref.startswith("http"):
                continue
            if any(
                token in ref for token in ("YYYY-MM-DD", "{workspace}", "{project}")
            ):
                continue
            candidate = ROOT / ref
            if not candidate.exists():
                issues.append(
                    f"Missing referenced path: {path.relative_to(ROOT)} -> {ref}"
                )


def check_agent_dependencies(issues: list[str]) -> None:
    for path in (ROOT / "core" / "agents").glob("**/*.md"):
        text = load_text(path)
        for context_ref in re.findall(r"- context:([^\n]+)", text):
            ref = context_ref.strip()
            candidate = ROOT / ref
            if not candidate.exists():
                issues.append(
                    f"Missing agent context dependency: {path.relative_to(ROOT)} -> {ref}"
                )
        for skill_ref in re.findall(r"- skill:([^\n]+)", text):
            skill_name = skill_ref.strip()
            candidate = ROOT / "core" / "skills" / "core" / skill_name / "SKILL.md"
            if not candidate.exists():
                issues.append(
                    f"Missing agent skill dependency: {path.relative_to(ROOT)} -> {skill_name}"
                )
        for subagent_ref in re.findall(r"- subagent:([^\n]+)", text):
            subagent_name = subagent_ref.strip()
            candidate = ROOT / "core" / "agents" / "subagents" / f"{subagent_name}.md"
            if not candidate.exists():
                issues.append(
                    f"Missing subagent dependency: {path.relative_to(ROOT)} -> {subagent_name}"
                )


def check_catalog_paths(issues: list[str]) -> None:
    catalog_path = ROOT / "core" / "skills" / "catalog.json"
    if not catalog_path.exists():
        issues.append("Missing core/skills/catalog.json")
        return
    data = json.loads(load_text(catalog_path))
    for skill_name, info in data.get("skills", {}).items():
        ref = info.get("path", "")
        candidate = ROOT / ref / "SKILL.md"
        if not candidate.exists():
            issues.append(f"Missing catalog skill path: {skill_name} -> {ref}")


def check_guardian_timings(issues: list[str]) -> None:
    config_path = ROOT / "config" / "framework.yaml"
    guardian_path = ROOT / "core" / "scripts" / "framework-guardian.py"
    if not config_path.exists() or not guardian_path.exists():
        return
    config_text = load_text(config_path)
    guardian_text = load_text(guardian_path)
    timings = re.findall(r"^\s{4}([a-z-]+):\s*$", config_text, re.MULTILINE)
    for timing in timings:
        if timing in {"notifications", "critical_checks", "performance", "checks"}:
            continue
        if f'"{timing}"' not in guardian_text:
            issues.append(f"Guardian missing configured timing: {timing}")


def check_expected_paths(issues: list[str]) -> None:
    expected = [
        ROOT / "core" / ".context" / "codebase" / "backlog.md",
        ROOT / "core" / ".context" / "workspaces",
    ]
    for path in expected:
        if not path.exists():
            issues.append(f"Expected path missing: {path.relative_to(ROOT)}")


def main() -> int:
    issues: list[str] = []
    check_backtick_paths(issues)
    check_agent_dependencies(issues)
    check_catalog_paths(issues)
    check_guardian_timings(issues)
    check_expected_paths(issues)

    if issues:
        print("REFERENCE INTEGRITY CHECK FAILED")
        for issue in issues:
            print(f"- {issue}")
        return 1

    print("REFERENCE INTEGRITY CHECK PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
