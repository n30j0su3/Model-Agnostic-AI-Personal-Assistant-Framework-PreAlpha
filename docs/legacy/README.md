# Legacy — Sistema de skills TOML (eliminado)

> El **sistema de skills TOML** (v0.4.0-beta) fue sustituido por el sistema **Markdown**. El código del sistema TOML **fue eliminado** el **2026-10-18**; aquí solo se conserva su documentación histórica.

## Sistema activo (Markdown)

| Artefacto | Ruta |
|-----------|------|
| Definición de skill | `core/skills/core/<skill>/SKILL.md` |
| Índice canónico | `core/skills/catalog.json` |
| Catálogo legible | `core/skills/SKILLS.md` |
| Índice generado | `core/.context/knowledge/skills-index.json` |
| Indexador | `core/scripts/skills_indexer.py` |

## Artefactos eliminados (2026-10-18)

| Artefacto | Estado | Nota |
|-----------|--------|------|
| `core/skills/skill_executor.py` | **ELIMINADO** | Ejecutor TOML; `discover_skills()` encontraba 0 skills (no existían `.toml`) |
| `core/scripts/skill_creator.py` | **ELIMINADO** | CLI que generaba `core/skills/<name>.toml` |
| `core/skills/__init__.py` (shim) | **REESCRITO** | Ya no re-exporta el ejecutor; es solo un marcador de namespace |
| `core/scripts/pa.py` (submenú Skills) | **ELIMINADO** | Código muerto que hacía glob de `*.toml` (nunca se invocaba) |

## Artefacto conservado (solo documentación)

| Artefacto | Nota |
|-----------|------|
| `docs/legacy/skill-creator-toml.md` | Documentación original del toolchain TOML, conservada como referencia histórica |

## No es legacy

- `core/skills/core/dashboard-pro/skill.yaml` — **manifiesto extendido activo** (modos, inputs/outputs, workflow, style presets). La fuente canónica sigue siendo su `SKILL.md`.
