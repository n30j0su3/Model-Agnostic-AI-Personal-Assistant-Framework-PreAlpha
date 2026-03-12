# Context Navigation

**Purpose**: Mapa central del conocimiento del framework. Punto de entrada para agentes AI.

---

## Structure (v0.2.0-prealpha)

```
core/.context/
├── MASTER.md              # Fuente de verdad (configuración global)
├── navigation.md         # Este archivo — mapa de navegación
├── sessions/              # Sesiones diarias (YYYY-MM-DD.md)
├── knowledge/             # Knowledge Base Central (CORE VITALS)
│   ├── README.md          # Guía central del conocimiento
│   ├── sessions-index.json# Índice de sesiones
│   ├── skills-index.json # Índice de skills disponibles
│   ├── agents-index.json # Índice de agentes
│   ├── knowledge-index.json
│   ├── interactions/     # BL-086: Historial de interacciones (JSON Lines)
│   ├── insights/         # Patrones y decisiones extraídas
│   │   ├── decisions.md
│   │   ├── error-analysis.md
│   │   └── patterns.md
│   ├── learning/         # Aprendizaje continuo
│   │   ├── discoveries.md   # Hallazgos significativos
│   │   ├── anti-patterns.md # Lo que NO funciona
│   │   ├── best-practices.md# Lo que SÍ funciona
│   │   └── README.md
│   ├── self-healing/     # Recovery system
│   │   ├── error-log.jsonl
│   │   ├── playbooks/
│   │   │   ├── index.json
│   │   │   ├── PB-001-encoding-errors.md
│   │   │   ├── PB-002-file-not-found.md
│   │   │   └── PB-003-json-parsing.md
│   │   └── README.md
│   └── prompts/          # Prompts exitosos
│       ├── registry.json
│       └── README.md
├── codebase/             # Conocimiento persistente del usuario
│   ├── recordatorios.md # Tareas y recordatorios
│   └── ideas.md         # Ideas, enlaces, notas
├── workspaces/           # Configuraciones de workspaces
└── vitals/              # VITALS - Sistema de respaldo y backup (LOCAL ONLY)
```

---

## Quick Routes

| Tarea | Ruta |
|-------|------|
| **Ver configuración global** | `MASTER.md` |
| **Dashboard SPA** | `dashboard.html` |
| **Sesión de hoy** | `sessions/YYYY-MM-DD.md` |
| **Knowledge Base Central** | `knowledge/README.md` |
| **Índice de sesiones** | `knowledge/sessions-index.json` |
| **Índice de skills** | `knowledge/skills-index.json` |
| **Índice de agentes** | `knowledge/agents-index.json` |
| **Índice de conocimiento** | `knowledge/knowledge-index.json` |
| **Historial de interacciones** | `knowledge/interactions/` |
| **Decisiones arquitectónicas** | `knowledge/insights/decisions.md` |
| **Análisis de errores** | `knowledge/insights/error-analysis.md` |
| **Patrones de uso** | `knowledge/insights/patterns.md` |
| **Descubrimientos** | `knowledge/learning/discoveries.md` |
| **Anti-patrones** | `knowledge/learning/anti-patterns.md` |
| **Mejores prácticas** | `knowledge/learning/best-practices.md` |
| **Error log** | `knowledge/self-healing/error-log.jsonl` |
| **Recovery playbooks** | `knowledge/self-healing/playbooks/` |
| **Prompts exitosos** | `knowledge/prompts/registry.json` |
| **Recordatorios** | `codebase/recordatorios.md` |
| **Ideas y notas** | `codebase/ideas.md` |
| **Agentes disponibles** | `core/agents/AGENTS.md` |
| **Skills disponibles** | `core/skills/SKILLS.md` |
| **Docs CORE (PRPs)** | `docs/core/PRP-*.md` |
| **Workflow Standard** | `docs/WORKFLOW-STANDARD.md` |
| **Assembly Line** | `docs/ASSEMBLY-LINE.md` |

---

## By Category

**MASTER.md** — Configuración global, idioma, workspaces, preferencias
**sessions/** — Historial diario, logs de sesiones AI, trazabilidad
**knowledge/** — Knowledge Base Central (CORE VITALS)
- `sessions-index.json` — Índice Dashboard SPA-compatible
- `skills-index.json` — Catálogo de skills del framework
- `agents-index.json` — Catálogo de agentes
- `knowledge-index.json` — Índice general
- `interactions/` — Log de interacciones (JSON Lines)
- `insights/` — Patrones y decisiones extraídas
- `learning/` — Aprendizaje continuo (discoveries, anti-patterns, best-practices)
- `self-healing/` — Sistema de recuperación (error-log, playbooks)
- `prompts/` — Prompts exitosos reutilizables
**codebase/** — Base de conocimiento personal (persistente entre sesiones)
**../agents/** — Definiciones de agentes y subagentes
**../skills/** — Habilidades modulares invocables
**docs/** — Documentación del framework
- `core/PRP-*.md` — Documentación CORE (8 PRPs públicos)
- `WORKFLOW-STANDARD.md` — Proceso de trabajo estándar
- `ASSEMBLY-LINE.md` — Proceso de Assembly Line

---

## Framework Structure (Archivos Root)

```
/                           # Raíz del proyecto
├── AGENTS.md              # Punto de entrada universal (cualquier CLI AI)
├── VERSION                # v0.2.0-prealpha
├── README.md              # Documentación usuario
├── README-simple.md       # Documentación simplificada
├── README-technical.md    # Documentación técnica
├── README_en.md          # English version
├── CHANGELOG.md          # Registro de cambios
├── ROADMAP.md            # Roadmap del proyecto
├── GEMINI.md             # Guía para Gemini CLI
├── LICENSE               # MIT License
├── config/               # Configuraciones del framework
│   ├── framework.yaml    # Configuración CORE
│   ├── branding.txt      # Personalización
│   ├── i18n.json         # Internacionalización
│   ├── mcp.json         # MCP servers config
│   ├── quotas.json      # Cuotas y límites
│   └── workflow-config.yaml
├── core/                  # Núcleo del framework
│   ├── agents/            # Agentes AI
│   │   ├── AGENTS.md
│   │   ├── pa-assistant.md
│   │   └── subagents/
│   ├── skills/           # Skills modulares
│   │   ├── SKILLS.md
│   │   ├── catalog.json
│   │   └── core/         # Skills del framework
│   ├── scripts/          # Scripts de automatización
│   │   ├── sync-prealpha.py
│   │   ├── session-start.py
│   │   ├── session-end.py
│   │   ├── framework-guardian.py
│   │   └── ...
│   └── .context/        # Contexto y conocimiento
├── docs/                  # Documentación
│   ├── core/            # Documentación CORE (8 PRPs)
│   ├── ASSEMBLY-LINE.md
│   ├── WORKFLOW-STANDARD.md
│   └── RELEASES/        # Notas de release
├── .opencode/            # Configuración OpenCode
│   ├── config.json      # Configuración sanitizada
│   ├── commands/        # Comandos custom
│   ├── agent/           # Agentes custom
│   └── package.json
└── workspaces/           # Workspaces de usuario (NO se sincroniza)
```

---

## Version

**v0.2.0-prealpha** - Framework Enforcement System
