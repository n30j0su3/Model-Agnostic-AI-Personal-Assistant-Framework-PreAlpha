# Quick-Start — PA Framework

> **Version**: 0.4.1-beta | Referencia MVI para inicio ligero

## Contrato de inicio

El launcher completa el bootstrap determinístico antes de abrir la CLI. El estado verificable queda en `core/.context/.cache/warm-start.json`; no repitas discovery, migraciones ni carga de sesión desde el LLM.

## Contexto bajo demanda

- OpenCode carga las reglas de `AGENTS.md` y el agente `FreakingJSON`.
- Consulta `core/.context/MASTER.md`, perfil, sesiones o preferencias solo cuando la tarea lo requiera.
- Usa los índices de `core/.context/knowledge/` antes de recorrer archivos completos.
- Carga tiers 2–4 únicamente por necesidad; no en la secuencia inicial.
- Antes de crear scripts, revisa las skills disponibles y reutiliza una existente.

## Rutas clave

- Sesiones: `core/.context/sessions/`
- Pendientes: `core/.context/codebase/recordatorios.md`
- Ideas: `core/.context/codebase/ideas.md`
- Skills: `core/skills/SKILLS.md`
- Agentes: `core/agents/AGENTS.md`
- Navegación completa: `core/.context/navigation.md`

**MVI:** carga solo la información necesaria para la tarea actual.
