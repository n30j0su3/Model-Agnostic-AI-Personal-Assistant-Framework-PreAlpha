---
description: Muestra ayuda del framework FreakingJSON-PA (NO es /help de OpenCode)
agent: FreakingJSON
---

# Ayuda del Framework FreakingJSON-PA

**Propósito**: Mostrar ayuda específica del framework (diferente a `/help` de OpenCode CLI).

## Comandos Disponibles

| Comando | Propósito | Agente |
|---------|-----------|--------|
| `/pa-status` | Estado del framework (KPIs, métricas) | FreakingJSON |
| `/session` | Gestión de sesiones diarias (.md) | session-manager |
| `/save` | Guardado de contexto actual | doc-writer |
| `/ideas` | Gestión de ideas y hallazgos | FreakingJSON |
| `/pending` | Gestión de pendientes | task-management |
| `/pa-help` | Esta ayuda | FreakingJSON |

**NOTA**: Evitamos `/status` y `/help` porque causan overlap con OpenCode CLI.

## Subagentes Disponibles

| Subagente | Propósito | Cuándo Usar |
|-----------|-----------|-------------|
| `@context-scout` | Descubrir archivos de contexto | Antes de actuar, buscar información relevante |
| `@session-manager` | Gestión de sesiones diarias | Crear, cerrar, resumir sesiones |
| `@doc-writer` | Documentación MVI | Generar docs de sesiones y hallazgos |
| `@feature-architect` | Arquitectura de features | Evaluar y ejecutar features del backlog |

## Skills Destacadas

**Core Skills** (siempre disponibles):
- `@decision-engine` → Router local-first
- `@context-evaluator` → LLM-as-a-Judge
- `@task-management` → Gestión de tareas

**Content Skills**:
- `@pdf`, `@xlsx`, `@docx`, `@pptx` → Procesamiento de archivos
- `@csv-processor` → Datos tabulares
- `@etl` → Transformación de datos

**Development Skills**:
- `@dashboard-pro` → Dashboards profesionales
- `@mcp-builder` → MCP servers
- `@prd-generator` → Documentos PRD

**Ver completo**: `core/skills/catalog.json`

## Documentación del Framework

| Archivo | Propósito |
|---------|-----------|
| `README.md` | Inicio rápido y características |
| `docs/README.md` | Documentación completa |
| `docs/WORKFLOW-STANDARD.md` | Workflow de 7 pasos |
| `docs/PHILOSOPHY.md` | Filosofía y principios |
| `core/agents/AGENTS.md` | Catálogo de agentes |
| `core/skills/SKILLS.md` | Catálogo de skills |

## Documentación de OpenCode (Referencia)

**URL Oficial**: https://opencode.ai/docs/

| Recurso | URL |
|---------|-----|
| Homepage | https://opencode.ai/docs/ |
| Comandos | https://opencode.ai/docs/commands/ |
| Agentes | https://opencode.ai/docs/agents/ |
| Models | https://opencode.ai/docs/models/ |
| MCP Servers | https://opencode.ai/docs/mcp-servers/ |
| Skills | https://opencode.ai/docs/skills/ |
| CLI | https://opencode.ai/docs/cli/ |
| TUI | https://opencode.ai/docs/tui/ |

**Nota**: Nuestros comandos custom (`/pa-status`, `/session`, etc.) se almacenan en `.opencode/commands/*.md` según el estándar oficial de OpenCode.

## Comandos de Productividad

| Comando | Acción |
|---------|--------|
| `/status` | ❌ OVERLAP con OpenCode - Usar `/pa-status` |
| `/save` | Fuerza guardado de contexto |
| `/session` | Muestra/crea sesión del día |
| `/ideas` | Abre codebase/ideas.md |
| `/pending` | Muestra recordatorios |
| `/pa-help` | Esta ayuda |

## Filosofía

> *"El conocimiento verdadero trasciende a lo público."*
> 
> *"I own my context. I am FreakingJSON."*

**Principios**:
1. **Local-First**: Todo en archivos locales que controlas
2. **User Sovereignty**: Tú decides, el framework nunca decide por ti
3. **Vendor-Agnostic**: Funciona con cualquier LLM/CLI
4. **MVI**: Minimal Viable Information - solo lo esencial
5. **Privacy-First**: Sin exposición de credenciales o datos sensibles

---

*Para más detalles: `core/.context/opencode-reference.md`*
