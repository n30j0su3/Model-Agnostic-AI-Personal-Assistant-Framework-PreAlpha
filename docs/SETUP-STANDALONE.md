# PA Framework — Standalone Setup Guide

> For users running PA Framework **without Hermes** (via OpenCode, Gemini CLI, or direct Python)

## Quick Start (3 Steps)

### Step 1: Clone & Install

```bash
git clone https://github.com/freakingjson/Model-Agnostic-AI-Personal-Assistant-Framework.git
cd Model-Agnostic-AI-Personal-Assistant-Framework/Model-Agnostic-AI-Personal-Assistant-Framework
```

**Dependencies**: Python 3.11+ (stdlib-only, no pip install required)

Optional for YAML config:
```bash
pip install pyyaml  # Only if using providers.yaml
```

### Step 2: Configure Providers (JSON)

Create `~/.pa-framework/providers.json`:

```json
{
  "providers": [
    {
      "name": "local",
      "type": "ollama",
      "base_url": "http://localhost:11434"
    },
    {
      "name": "opencode",
      "type": "openai_compat",
      "api_key": "${OPENCODE_API_KEY}",
      "base_url": "https://api.nanogpt.com/v1",
      "models": ["qwopus-9b-q4", "qwopus-9b-q8"]
    },
    {
      "name": "gemini",
      "type": "openai_compat",
      "api_key": "${GEMINI_API_KEY}",
      "base_url": "https://generativelanguage.googleapis.com/v1beta/openai",
      "models": ["gemini-2.0-flash", "gemini-2.5-pro-preview"]
    }
  ],
  "fallback_order": ["local", "opencode", "gemini", "mock"]
}
```

Set API keys as environment variables:
```bash
export OPENCODE_API_KEY="your-key-here"
export GEMINI_API_KEY="your-key-here"
```

### Step 3: Initialize Session

```bash
python core/scripts/session-start.py
```

Expected output:
- Framework init time: ~4.5s cold, <2s warm
- Multi-CLI coordination: Active
- Context loading: Tier 0-1 loaded, Tier 2-4 lazy

---

## Architecture (Standalone Mode)

| Component | Path | Standalone | Notes |
|-----------|------|------------|-------|
| SessionStore | `core/memory/session_memory.py` | ✅ Yes | SQLite `data/sessions.db` |
| SkillExecutor | `core/skills/skill_executor.py` | ✅ Yes | TOML skills in `skills/*.toml` |
| MultiEngine | `core/providers/multi_engine.py` | ✅ Yes | JSON/YAML config |
| ContextLoader | `core/scripts/context_loader.py` | ✅ Yes | Tier-based lazy loading |
| SessionStart | `core/scripts/session-start.py` | ✅ Yes | Bootstrap script |

---

## Using with OpenCode CLI

```bash
# OpenCode with PA Framework skills
opencode chat --skill-dir skills/ --skill greet_user.toml

# Or load PA Framework context
opencode chat --context core/.context/
```

---

## Using with Gemini CLI

```bash
# Gemini with PA Framework memory
gemini chat --memory ~/.pa-framework/memory/sessions.db
```

---

## Cross-Platform Compatibility

| Platform | Status | Notes |
|----------|--------|-------|
| Linux | ✅ Verified | Primary development platform |
| macOS | ✅ Verified | `Path.home()` works, SQLite standard |
| Windows | ✅ Verified | UTF-8 handling, `pathlib.Path` native |

---

## Testing Standalone

```bash
# Full test suite
pytest tests/ core/scripts/tests/ --ignore=obsolete --ignore=docs/archive

# Expected: 285 passed, 1 skipped
```

---

## Troubleshooting

### Issue: "No module named 'yaml'"
**Solution**: Use JSON config (`providers.json`) or install pyyaml:
```bash
pip install pyyaml
```

### Issue: "Permission denied ~/.pa-framework/"
**Solution**: Ensure directory exists:
```bash
mkdir -p ~/.pa-framework/memory
mkdir -p ~/.pa-framework/sessions
```

### Issue: "API key not found"
**Solution**: Export environment variables:
```bash
export NANOGPT_API_KEY="..."
export GEMINI_API_KEY="..."
```

---

## Version Info

- **Framework**: v0.2.2-prealpha
- **Phase**: 3 (wiki-cron integration)
- **Tests**: 285 passed, 1 skipped
- **Author**: FreakingJSON (instagram.com/freakingjson)

---

*"Calidad sobre velocidad. Estabilidad primero."*