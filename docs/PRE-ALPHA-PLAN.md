# Pre-Alpha Framework — Plan de Implementación

> **Fecha**: 2026-02-09  
> **Versión objetivo**: 0.1.0-alpha  
> **Referencia**: OpenAgentsControl 0.7.1

---

## Estructura Final Pre-Alpha

```
/PA-Pre-Alpha/
├── core/                          # Núcleo central del framework
│   ├── .context/                  # Conocimiento central
│   │   ├── MASTER.md              # Fuente de verdad (template limpio)
│   │   ├── MASTER.template.md     # Template para restaurar
│   │   ├── navigation.md          # Mapa de navegación token-eficiente
│   │   ├── sessions/              # Logs diarios y trazabilidad
│   │   │   └── .gitkeep
│   │   └── codebase/              # Knowledge base personal
│   │       ├── .gitkeep
│   │       ├── recordatorios.md   # Template vacío
│   │       └── ideas.md           # Template vacío
│   ├── agents/                    # Agentes AI especializados (.md)
│   │   ├── AGENTS.md              # Índice y Router principal
│   │   ├── pa-assistant.md        # Agente principal (inspirado en eval-runner)
│   │   └── subagents/             # Subagentes auto-delegados
│   │       ├── context-scout.md   # Descubrimiento de contexto
│   │       ├── session-manager.md # Gestión de sesiones
│   │       └── doc-writer.md      # Documentación
│   ├── skills/                    # Habilidades modulares
│   │   ├── SKILLS.md              # Catálogo
│   │   └── core/                  # Skills incluidos
│   │       ├── task-management/
│   │       ├── pdf/
│   │       ├── xlsx/
│   │       └── prompt-improvement/
│   └── scripts/                   # Automatización Python
│       ├── pa.py                  # Control panel (menú simplificado)
│       ├── install.py             # Instalador
│       ├── sync-context.py        # Sincronización
│       ├── utils.py               # Utilidades
│       └── i18n.py                # Internacionalización
├── workspaces/                    # Espacios aislados por disciplina
│   └── .gitkeep
├── docs/                          # Documentación sencilla
│   ├── README.md                  # Quick-start
│   └── quickstart.md              # Guía rápida
├── config/                        # Configuración del framework
│   ├── branding.txt               # Banner ASCII
│   └── i18n.json                  # Traducciones
├── pa.bat                         # Entry point Windows
├── pa.sh                          # Entry point macOS/Linux
├── Agents.md                      # Router para /init (Gemini, Claude, etc.)
├── GEMINI.md                      # Contexto exclusivo Gemini CLI
├── opencode.jsonc                 # Config OpenCode (template limpio)
├── VERSION                        # Versión del framework
└── .gitignore
```

---

## Fases de Implementación

### Fase 1 — Reestructuración de Directorio
Crear `core/` y mover `.context/`, `agents/`, `skills/`, `scripts/` dentro. Crear subdirectorios nuevos: `sessions/`, `codebase/`.

### Fase 2 — Menú Simplificado (pa.py)
Menú de 4 opciones:
1. 🔄 Sincronizar Contexto
2. 🚀 Iniciar Sesión AI
3. ⚙️ Configuración (submenu: Estado, Perfil, Workspaces)
4. 🔄 Buscar Actualizaciones
0. 🚪 Salir

### Fase 3 — Sistema de Agentes (Inspirado en OpenAgentsControl)
- `pa-assistant.md` → Agente principal con YAML frontmatter + dependencias de subagentes
- `context-scout.md` → Descubrimiento de contexto (read-only)
- `session-manager.md` → Gestión de sesiones diarias
- `doc-writer.md` → Documentación automática

### Fase 4 — Contexto y Navegación MVI
- `navigation.md` → Mapa token-eficiente (~200-300 tokens)
- `codebase/` → Templates para conocimiento local persistente
- Principio MVI: máximo 1-3 oraciones por concepto, 3-5 bullets, ejemplo mínimo

### Fase 5 — Framework-Agnostic Init
`Agents.md` en raíz como router universal. Cualquier CLI (Gemini, Claude, OpenCode) puede leer este archivo y bootstrapear el framework.

### Fase 6 — Sanitización
- Limpiar tokens, URLs personales, sesiones
- VERSION → `0.1.0-alpha`
- MASTER.md → template limpio

### Fase 7 — Verificación
- Test `pa.bat` → menú funcional
- Test estructura de directorios
- Agent configs bien formados
