# AGENTS — Framework Init Router

> **Este archivo es el punto de entrada universal para cualquier CLI de IA.** Cuando un agente AI lee este archivo (Gemini, Claude, OpenCode, Codex), se activa el protocolo de inicialización del framework.

---

## 🚦 INITIALIZATION PROTOCOL

### Step 1: Detect This Framework

Si estás leyendo este archivo, has encontrado un proyecto que utiliza el **Personal Assistant Framework**. Este framework gestiona asistentes AI personales con contexto local.

### Step 2: Fast Start (<30s) ⚡

```
📂 ACCIÓN OBLIGATORIA - Ejecutar script de inicio rápido:
   python core/scripts/session-start.py

Este script:
- Crea/verifica sesión del día
- Muestra conteos (pendientes, logros, skills)
- No carga contenido completo = RÁPIDO
- Target: <30 segundos
```

### Step 3: Fallback Manual (si script falla)

```
📂 Archivos a leer SOLO si session-start.py no está disponible:
1. core/.context/MASTER.md         → Configuración global y preferencias
2. core/agents/pa-assistant.md     → Agente principal FreakingJSON-PA (modo producción)
3. core/.context/navigation.md     → Mapa de todo el conocimiento disponible
4. core/skills/SKILLS.md           → Skills disponibles (OBLIGATORIO)
```

> **⚠️ CRÍTICO**: Siempre consultar `core/skills/SKILLS.md` antes de crear scripts.
> El framework tiene skills especializadas (@csv-processor, @xlsx, @etl) que deben
> usarse preferentemente sobre soluciones ad-hoc.

### Step 4: Session Ready

1. Sesión creada en `core/.context/sessions/YYYY-MM-DD.md`
2. **Sigue el workflow** definido en `pa-assistant.md` (agente FreakingJSON-PA):
   - Inicialización → Comprensión → Ejecución → Preservación

---

## Agentes Disponibles

| Agente | Propósito | Archivo |
|--------|-----------|---------|
| **@FreakingJSON-PA** | Agente principal (producción), orquestación | `core/agents/pa-assistant.md` |
| **@context-scout** | Descubrimiento de contexto | `core/agents/subagents/context-scout.md` |
| **@session-manager** | Gestión de sesiones diarias | `core/agents/subagents/session-manager.md` |
| **@doc-writer** | Documentación MVI | `core/agents/subagents/doc-writer.md` |

---

## Comandos Rápidos

| Comando | Acción |
|---------|--------|
| `/init` | Inicia el framework (lee este archivo) |
| `/status` | Estado actual: sesión, pendientes, workspace |
| `/save` | Guarda contexto actual en archivos .md |
| `/session` | Muestra/crea la sesión del día |
| `/help` | Lista comandos disponibles |

---

## Estructura del Proyecto

```
├── core/                  # Núcleo del framework
│   ├── .context/          # Conocimiento central (MASTER.md, sessions, codebase)
│   ├── agents/            # Agentes AI (.md con YAML frontmatter)
│   ├── skills/            # Habilidades modulares (@pdf, @xlsx, etc.)
│   └── scripts/           # Automatización Python (pa.py, install, sync)
├── workspaces/            # Espacios aislados por disciplina
├── docs/                  # Documentación
├── config/                # Configuración (branding, i18n)
├── pa.bat / pa.sh         # Entry points (Windows / macOS-Linux)
└── Agents.md              # Este archivo — router de inicialización
```

---

## Reglas Globales

1. **Contexto local**: TODO el conocimiento se almacena en archivos `.md` bajo control del usuario.
2. **Privacy-first**: NUNCA exponer credenciales, tokens o datos sensibles.
3. **Preservar conocimiento**: Al finalizar una sesión, SIEMPRE guardar sesión, decisiones y pendientes.
4. **MVI**: Minimal Viable Information — documentar lo esencial, no duplicar.
5. **Framework-agnostic**: Funciona con cualquier CLI de IA (OpenCode, Gemini, Claude, Codex).