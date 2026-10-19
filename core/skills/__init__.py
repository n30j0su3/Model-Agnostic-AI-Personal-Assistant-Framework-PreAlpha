"""
PA Framework — Skills layer (Markdown).

El sistema de skills del framework es **Markdown basado en archivos**:

    core/skills/core/<skill>/SKILL.md        definición de la skill (fuente canónica)
    core/skills/catalog.json                 índice canónico
    core/skills/SKILLS.md                    catálogo legible
    core/.context/knowledge/skills-index.json  índice generado (skills_indexer.py)

Este paquete (`core.skills`) es solo un marcador de namespace; no ejecuta skills.
El antiguo ejecutor TOML y su shim de re-export fueron eliminados (2026-10-18).
Histórico: `docs/legacy/`.
"""
