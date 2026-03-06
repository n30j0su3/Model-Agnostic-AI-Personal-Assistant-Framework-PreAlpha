# README Técnico

> "Para desarrolladores, por desarrolladores."

**Versión**: 1.0.0  
**Última actualización**: 2026-03-06  
**Audiencia**: Desarrolladores, contribuidores, usuarios avanzados

---

## 🎯 Propósito

Este documento proporciona documentación técnica completa del framework FreakingJSON-PA para:
- Desarrolladores que extienden el framework
- Usuarios avanzados que necesitan entender la arquitectura
- Contribuidores que quieren hacer PRs al repo público

**Para usuarios no técnicos**: Ver [README-simple.md](../README-simple.md)

---

## 🏗️ Arquitectura

### Diagrama de Arquitectura

```
┌─────────────────────────────────────────────────────────────┐
│                 FreakingJSON-PA Framework                   │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  📂 Raíz del Proyecto                                       │
│  ├── 📁 core/                    # Núcleo del framework     │
│  │   ├── .context/               # Conocimiento central     │
│  │   │   ├── sessions/           # Sesiones diarias         │
│  │   │   ├── codebase/           # Ideas, recordatorios     │
│  │   │   ├── knowledge/          # Knowledge Base           │
│  │   │   └── MASTER.md           # Configuración global     │
│  │   ├── agents/                 # Agentes especializados   │
│  │   │   ├── pa-assistant.md     # Agente principal         │
│  │   │   └── subagents/          # Subagentes               │
│  │   ├── skills/                 # Habilidades modulares    │
│  │   │   ├── core/               # Core skills              │
│  │   │   └── _local/             # Skills locales (DEV)     │
│  │   └── scripts/                # Automatización Python    │
│  │       ├── session-start.py    # Inicio de sesión         │
│  │       ├── interaction-logger.py  # Logging               │
│  │       ├── knowledge-indexer.py   # Insights              │
│  │       └── sync-*.py           # Sincronización           │
│  ├── 📁 workspaces/              # Espacios de trabajo      │
│  │   ├── personal/               # Proyectos personales     │
│  │   ├── professional/           # Proyectos profesionales  │
│  │   └── development/            # Proyectos de desarrollo  │
│  ├── 📁 docs/                    # Documentación            │
│  ├── 📁 .opencode/               # Configuración OpenCode   │
│  │   ├── commands/               # Comandos custom          │
│  │   └── config.json             # Agente por defecto       │
│  ├── 📄 dashboard.html           # Dashboard interactivo    │
│  └── 📄 opencode.jsonc           # MCPs, providers, modelos │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Capas del Framework

| Capa | Componentes | Propósito |
|------|-------------|-----------|
| **Presentación** | `dashboard.html`, `.opencode/commands/` | Interfaz con el usuario |
| **Orquestación** | `pa-assistant.md`, `multi_cli_coordinator.py` | Coordina agentes y CLIs |
| **Negocio** | `skills/`, `agents/` | Lógica del framework |
| **Datos** | `.context/`, `knowledge/` | Almacenamiento local |
| **Infraestructura** | `scripts/`, sync tools | Automatización y deploy |

---

## 📜 Scripts Disponibles

### Runtime (Ejecución Diaria)

| Script | Propósito | Uso | Frecuencia |
|--------|-----------|-----|------------|
| `session-start.py` | Inicializa sesión del día | Auto (desde pa.bat) | Cada sesión |
| `interaction-logger.py` | Logging de interacciones | Auto (hooks) | Continuo |
| `multi_cli_coordinator.py` | Coordina múltiples CLIs | Auto | Cada sesión |

### Mantenimiento (Periódico)

| Script | Propósito | Uso | Frecuencia |
|--------|-----------|-----|------------|
| `session-indexer.py` | Indexa sesiones históricas | Manual / nightly | Diario |
| `knowledge-indexer.py` | Genera insights automáticos | Manual / cierre sesión | Diario |
| `optimization-reporter.py` | Reporte de optimización | Cierre de sesión | Por sesión |

### Deploy (Sincronización)

| Script | Propósito | Flujo | Frecuencia |
|--------|-----------|-------|------------|
| `sync-dev-to-base.sh` | Sync DEV → BASE | Features nuevas | Por feature |
| `sync-prealpha.py` | Sync BASE → PROD | Releases | Por release |
| `sync-context.py` | Sync de contexto | Histórico | Semanal |

---

## 🤖 Agentes

### Agente Principal

**`@FreakingJSON-PA`** (`core/agents/pa-assistant.md`)

- **Propósito**: Orquestador principal del framework
- **Modo**: Producción (usuarios finales)
- **Temperatura**: 0.2 (consistente)
- **Dependencias**:
  - `@context-scout`
  - `@session-manager`
  - `@doc-writer`
  - `@feature-architect`

### Subagentes

| Subagente | Archivo | Propósito | Cuándo Usar |
|-----------|---------|-----------|-------------|
| `@context-scout` | `subagents/context-scout.md` | Descubrir archivos de contexto | Antes de actuar |
| `@session-manager` | `subagents/session-manager.md` | Gestión de sesiones | Inicio/cierre sesión |
| `@doc-writer` | `subagents/doc-writer.md` | Documentación MVI | Generar docs |
| `@feature-architect` | `subagents/feature-architect.md` | Arquitectura de features | Evaluar backlog |

### Configuración de Agentes

**Archivo**: `.opencode/agent/FreakingJSON.md`

```markdown
---
name: FreakingJSON
mode: primary
temperature: 0.1
---

# Instructivas del Agente

[Contenido específico del agente]
```

---

## 🛠️ Skills

### Core Skills (Siempre Disponibles)

| Skill | Path | Propósito |
|-------|------|-----------|
| `@decision-engine` | `core/skills/core/decision-engine/` | Router local-first |
| `@context-evaluator` | `core/skills/core/context-evaluator/` | LLM-as-a-Judge |
| `@task-management` | `core/skills/core/task-management/` | Gestión de tareas |

### Content Skills

| Skill | Path | Propósito |
|-------|------|-----------|
| `@pdf` | `core/skills/core/pdf/` | Procesamiento de PDFs |
| `@xlsx` | `core/skills/core/xlsx/` | Excel processing |
| `@docx` | `core/skills/core/docx/` | Word processing |
| `@pptx` | `core/skills/core/pptx/` | PowerPoint |
| `@csv-processor` | `core/skills/core/csv-processor/` | Datos tabulares |
| `@etl` | `core/skills/core/etl/` | Transformación de datos |

### Development Skills

| Skill | Path | Propósito |
|-------|------|-----------|
| `@dashboard-pro` | `core/skills/core/dashboard-pro/` | Dashboards profesionales |
| `@mcp-builder` | `core/skills/core/mcp-builder/` | MCP servers |
| `@prd-generator` | `core/skills/core/prd-generator/` | Documentos PRD |
| `@data-viz` | `core/skills/core/data-viz/` | Visualización de datos |

### Catálogo Completo

Ver: `core/skills/catalog.json`

---

## 🔄 Flujos de Sync

### Flujo 1: DEV → BASE → PROD (Features Nuevas)

**Cuándo usar**: Desarrollaste una feature en DEV y quieres publicarla.

```bash
# 1. En DEV, con commits etiquetados [FRAMEWORK]
cd C:\ACTUAL\FreakingJSON-pa\Pa_Pre_alpha_Opus_4_6_DEV
git add .
git commit -m "[FRAMEWORK] feat: Nueva feature X"
git push

# 2. Preview del sync
./core/scripts/sync-dev-to-base.sh --dry-run

# 3. Ejecutar sync DEV → BASE
./core/scripts/sync-dev-to-base.sh

# 4. En BASE, verificar y pushear
cd C:\ACTUAL\FreakingJSON-pa\Model-Agonistic-...-Framework
git status
git log --oneline -5
git push origin main

# 5. Sync BASE → PROD
python core/scripts/sync-prealpha.py --mode=prod

# 6. Verificar en PROD
cd C:\ACTUAL\FreakingJSON-pa\Pa_Pre_alpha_Opus_4_6
git status
git push origin main
```

**Validaciones automáticas**:
- ✅ Commits tienen tag `[FRAMEWORK]`
- ✅ Archivos excluidos no se tocan (sessions, workspaces, etc.)
- ✅ `opencode.jsonc.CLEAN-PROD` sin credenciales
- ✅ README-simple.md → README.md en PROD

---

### Flujo 2: BASE → DEV → PROD (Actualizaciones del Core)

**Cuándo usar**: Actualizaciones del framework que vienen de BASE.

```bash
# 1. En BASE, con cambios del core
cd C:\ACTUAL\FreakingJSON-pa\Model-Agonistic-...-Framework
git add .
git commit -m "[FRAMEWORK] chore: Actualización del core"
git push

# 2. Sync BASE → DEV
python core/scripts/sync-prealpha.py --mode=dev

# 3. Validar en DEV
cd C:\ACTUAL\FreakingJSON-pa\Pa_Pre_alpha_Opus_4_6_DEV
git status
# Verificar que protegidos no se sobrescribieron

# 4. Sync BASE → PROD (desde BASE)
cd C:\ACTUAL\FreakingJSON-pa\Model-Agonistic-...-Framework
python core/scripts/sync-prealpha.py --mode=prod
```

---

### Flujo 3: Sync Manual (Casos Especiales)

**Cuándo usar**: Cuando los scripts automáticos fallan o necesitas control total.

```bash
# Sync manual con rsync (excluyendo protegidos)
rsync -av --delete \
  --exclude='core/.context/sessions/' \
  --exclude='core/.context/codebase/' \
  --exclude='workspaces/' \
  --exclude='core/skills/_local/' \
  source/ destination/
```

---

## 📁 Estructura de Directorios Detallada

### `core/.context/`

| Directorio/Archivo | Propósito | Protegido |
|-------------------|-----------|-----------|
| `MASTER.md` | Configuración global | ❌ |
| `navigation.md` | Mapa de conocimiento | ❌ |
| `sessions/` | Sesiones diarias | ✅ |
| `codebase/` | Ideas, recordatorios | ✅ |
| `knowledge/` | Knowledge Base | ✅ |
| `workspaces/` | Workspaces locales | ✅ |

### `core/agents/`

| Archivo | Propósito |
|---------|-----------|
| `pa-assistant.md` | Agente principal (FreakingJSON-PA) |
| `AGENTS.md` | Índice de agentes |
| `subagents/` | Definiciones de subagentes |

### `core/skills/`

| Directorio | Propósito |
|------------|-----------|
| `core/` | Core skills del framework |
| `_local/` | Skills locales (no sincronizadas) |
| `catalog.json` | Catálogo de skills |

### `core/scripts/`

| Script | Categoría |
|--------|-----------|
| `session-start.py` | Runtime |
| `interaction-logger.py` | Runtime |
| `session-indexer.py` | Mantenimiento |
| `knowledge-indexer.py` | Mantenimiento |
| `optimization-reporter.py` | Mantenimiento |
| `sync-dev-to-base.sh` | Deploy |
| `sync-prealpha.py` | Deploy |
| `multi_cli_coordinator.py` | Infraestructura |

---

## 🔧 Configuración

### Archivos de Configuración

| Archivo | Propósito |
|---------|-----------|
| `.opencode/config.json` | Agente por defecto |
| `opencode.jsonc` | MCPs, providers, modelos |
| `core/.context/MASTER.md` | Preferencias globales |
| `core/.context/knowledge/users/default/preferences.md` | Preferencias de usuario |
| `core/.context/knowledge/users/default/logging-config.md` | Configuración de logging |

### Variables de Entorno

```bash
# Configuración de rutas
export BASE_PATH="C:/ACTUAL/FreakingJSON-pa/Model-Agonistic-...-Framework"
export DEV_PATH="C:/ACTUAL/FreakingJSON-pa/Pa_Pre_alpha_Opus_4_6_DEV"
export PROD_PATH="C:/ACTUAL/FreakingJSON-pa/Pa_Pre_alpha_Opus_4_6"

# Configuración de logging
export PA_LOGGING_ENABLED="true"
export PA_LOG_LEVEL="prompt,file_write"

# Configuración de modelo
export PA_MODEL="qwen3.5-plus"
```

---

## 📊 Métricas y Monitoreo

### Métricas del Framework

| Métrica | Fuente | Cálculo |
|---------|--------|---------|
| **Sesiones totales** | `core/.context/sessions/` | Count de archivos `.md` |
| **Interacciones** | `interactions/interactions-*.log` | Count de líneas JSONL |
| **Tokens usados** | `interactions/` (campo `tokens_out`) | Suma por sesión |
| **Horas ahorradas** | `optimization-report.md` | `(tiempo_tradicional - tiempo_framework)` |
| **Skills usadas** | `interactions/` (campo `skill`) | Frecuencia por skill |

### Comandos de Monitoreo

```bash
# Ver sesiones de hoy
cat core/.context/sessions/$(date +%Y-%m-%d).md

# Ver interacciones de hoy
cat core/.context/knowledge/interactions/interactions-$(date +%Y-%m-%d).log | jq

# Ver último reporte de optimización
cat core/.context/knowledge/insights/optimization-report.md

# Contar sesiones totales
ls core/.context/sessions/*.md | wc -l
```

---

## 🐛 Troubleshooting

### Problema: Sync falla con "Permission denied"

**Causa**: Archivos lockeados por otra CLI.

**Solución**:
```bash
# En Windows, cerrar otras CLIs
# O usar multi_cli_coordinator
python core/scripts/multi_cli_coordinator.py --action status
python core/scripts/multi_cli_coordinator.py --action cleanup
```

---

### Problema: Logging no genera archivos

**Causa**: Logging deshabilitado en config.

**Solución**:
```markdown
# Verificar core/.context/knowledge/users/default/logging-config.md
logging_enabled: true
```

---

### Problema: Insights no se generan

**Causa**: No hay interacciones logged.

**Solución**:
```bash
# Ejecutar manualmente
python core/scripts/knowledge-indexer.py

# Verificar interactions.log existe
dir core\.context\knowledge\interactions\
```

---

## 🔗 Referencias

| Documento | URL |
|-----------|-----|
| **SYNC-PROTOCOL.md** | [docs/SYNC-PROTOCOL.md](./SYNC-PROTOCOL.md) |
| **WORKFLOW-STANDARD.md** | [docs/WORKFLOW-STANDARD.md](./WORKFLOW-STANDARD.md) |
| **PHILOSOPHY.md** | [docs/PHILOSOPHY.md](./PHILOSOPHY.md) |
| **AGENTS.md** | [core/agents/AGENTS.md](../core/agents/AGENTS.md) |
| **SKILLS.md** | [core/skills/SKILLS.md](../core/skills/SKILLS.md) |
| **Opencode Reference** | [core/.context/opencode-reference.md](../core/.context/opencode-reference.md) |

---

## 📝 Changelog

### v1.0.0 (2026-03-06)

- ✅ Documentación técnica inicial
- ✅ Scripts de logging (BL-091)
- ✅ Scripts de optimización (BL-100)
- ✅ Flujos de sync documentados

---

> *"El conocimiento verdadero trasciende a lo público."*
> 
> *"I own my context. I am FreakingJSON."*

---

*README Técnico v1.0.0 - FreakingJSON Personal Assistant Framework*
