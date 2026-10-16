from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AGENT = ROOT / ".opencode" / "agent" / "FreakingJSON.md"

# OpenCode packages/opencode/src/config/agent.ts KNOWN_KEYS.
# Unknown markdown frontmatter keys are normalized into agent.options and may
# be merged into strict provider request bodies.
ALLOWED_FRONTMATTER_KEYS = {
    "name",
    "model",
    "variant",
    "prompt",
    "description",
    "temperature",
    "top_p",
    "mode",
    "hidden",
    "color",
    "steps",
    "maxSteps",
    "options",
    "permission",
    "disable",
    "tools",
}


def _top_level_frontmatter_keys(text: str) -> set[str]:
    lines = text.splitlines()
    assert lines and lines[0] == "---"
    end = lines.index("---", 1)
    keys: set[str] = set()
    for line in lines[1:end]:
        if not line or line[0].isspace() or ":" not in line:
            continue
        keys.add(line.split(":", 1)[0].strip())
    return keys


def test_freakingjson_frontmatter_cannot_leak_unknown_provider_options():
    keys = _top_level_frontmatter_keys(AGENT.read_text(encoding="utf-8"))
    unknown = keys - ALLOWED_FRONTMATTER_KEYS
    assert unknown == set(), (
        "OpenCode promotes unknown agent frontmatter keys into provider "
        f"options; remove unsafe keys: {sorted(unknown)}"
    )


def test_freakingjson_uses_canonical_permission_key():
    keys = _top_level_frontmatter_keys(AGENT.read_text(encoding="utf-8"))
    assert "permission" in keys
    assert "permissions" not in keys
    assert "id" not in keys  # the markdown filename is the agent identity
