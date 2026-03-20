# Update Guide

## Safe Update for Common Users

Use the official updater:

```bash
python core/scripts/update.py --check
python core/scripts/update.py
```

On Windows you can run the same command from PowerShell inside the framework folder.

## What the updater does

1. Checks whether a newer framework version is available.
2. Creates a preservation backup before changing files.
3. Updates framework files from the official public source.
4. Restores user-owned files and context.
5. Runs migrations and knowledge base initialization for compatibility.

## What is preserved automatically

The official updater preserves user-owned data such as:

- `workspaces/`
- `core/.context/MASTER.md`
- `core/.context/profile.md`
- `core/.context/opencode.md`
- `core/.context/claude.md`
- `core/.context/gemini.md`
- `core/.context/sessions/`
- `core/.context/codebase/`
- `core/.context/projects/`
- mutable knowledge / KB files
- `config/mcp.json`
- `config/quotas.json`
- `opencode.jsonc`
- `.opencode/config.json`

This means updates are designed to integrate framework improvements without overwriting your personal context, knowledge, or workspace data.

## If something goes wrong

The updater stores a preservation backup in:

```text
.update-preservation/
```

If an update is interrupted, this backup is the first place to review.

## Important Rule

For the preservation guarantee to apply, use the official updater:

```bash
python core/scripts/update.py
```

Avoid replacing files manually unless you know exactly which user-owned paths must be restored.
