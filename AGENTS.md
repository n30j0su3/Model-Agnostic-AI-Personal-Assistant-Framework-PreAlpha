# AGENTS — Framework Init Router

> **Version: v0.2.0-prealpha** | **Este archivo es el punto de entrada universal para cualquier CLI de IA.** Cuando un agente AI lee este archivo (Gemini, Claude, OpenCode, Codex), se activa el protocolo de inicialización del framework.

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

## ⚠️ ENFORCEMENT OBLIGATORIO

### ¿Qué es?

El **Framework Enforcement System** garantiza que cualquier IA que use el framework siga los principios CORE.

### Uso

**ANTES de acciones críticas** (commit, push, release), ejecutar:

```bash
python core/scripts/framework-guardian.py --timing pre-commit
python core/scripts/framework-guardian.py --timing pre-push
python core/scripts/framework-guardian.py --timing pre-release
```

### Validaciones por Timing

| Timing | Checks | Bloquea si falla |
|--------|--------|------------------|
| `pre-commit` | CORE-006, CORE-007 | warn |
| `pre-push` | CORE-006, CORE-007 | block |
| `pre-release` | CORE-001, CORE-006, CORE-007 | block |
| `session-end` | CORE-003, CORE-005 | warn |

### Checks Críticos (NO pueden desactivarse)

- `session_end_required` - Cerrar sesión correctamente
- `version_consistency` - Versión sincronizada en todos los archivos
- `no_credentials_prod` - Sin credenciales en repo público
- `no_prps_prod` - Sin PRPs en release público
- `critical_files_exist` - Archivos críticos presentes (AGENTS.md, VERSION, README.md, PRPs CORE)

### Ejemplo de Output

```
[CORE-006] Version Governance
  [✓] VERSION: 0.1.9-prealpha
  [✓] README.md: 0.1.9-prealpha
  [✓] AGENTS.md: 0.1.9-prealpha
  
[CORE-007] Release Sanitization
  [✓] No credentials found
  [✓] No PRPs in release target

PASSED: All checks passed
```

### Configuración

El usuario puede modificar `config/framework.yaml`:

```yaml
enforcement:
  level: warn  # warn | block | log
  timing:
    pre-commit: {enabled: false}
    pre-push: {enabled: false}
    pre-release: {enabled: true}
```

### Comando Rápido

| Comando | Acción |
|---------|--------|
| `/enforce` | Ejecutar validación pre-release |

---

## 🚦 CLOSING PROTOCOL

### Step Final: Cerrar Sesión (OBLIGATORIO)

**Antes de terminar cualquier sesión**, ejecutar:

```bash
python core/scripts/session-end.py
```

Esto asegura:
- ✅ Hora de cierre registrada
- ✅ Resumen automático generado
- ✅ Pendientes migrados a recordatorios.md
- ✅ Sesión indexada en Knowledge Base

### Fallback Manual (si script falla)

1. Actualizar `core/.context/sessions/YYYY-MM-DD.md`:
   - Agregar `time_end` en frontmatter
   - Agregar sección `## Cierre` con resumen
2. Mover pendientes nuevos a `core/.context/codebase/recordatorios.md`
3. Indexar: `python core/scripts/session-indexer.py --today`

### Cierre Automático (atexit)

El framework registra automáticamente el cierre via `atexit`.
Si la CLI termina inesperadamente, se intentará cierre limpio.

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

---

## 🧠 Procesos CORE

El framework implementa 8 procesos CORE que garantizan calidad y consistencia:

| CORE | Nombre | Principio | PRP |
|------|--------|-----------|-----|
| **001** | Framework-First Validation | SIEMPRE usar skills/agentes del framework | [PRP-001](docs/core/PRP-001-CORE-Framework-Validation.md) |
| **002** | Context-Aware Discovery | Validar archivos .md de contexto en directorio | [PRP-002](docs/core/PRP-002-CORE-Context-Aware.md) |
| **003** | Antifragile Error Recovery | Documentar errores, aprender, mejorar | [PRP-003](docs/core/PRP-003-CORE-Antifragile-Errors.md) |
| **004** | Self-Healing + MCP | Skills con lógica self-healing | [PRP-004](docs/core/PRP-004-CORE-Self-Healing-MCP.md) |
| **005** | Assembly Line | Delimitar → Mapear → Ejecutar → Validar | [PRP-005](docs/core/PRP-005-CORE-Assembly-Line.md) |
| **006** | Version Governance | Una versión, múltiples fuentes, sincronización automática | [PRP-008](docs/core/PRP-008-CORE-Version-Governance.md) |
| **007** | Release Sanitization & Data Protection | PROD público, DEV protegido, BASE completo | [PRP-009](docs/core/PRP-009-CORE-Release-Sanitization.md) |
| **008** | Knowledge Extraction Framework | Extracción automática de conocimiento | [PRP-011](docs/core/PRP-011-CORE-Knowledge-Extraction.md) |

### CORE-001: Framework-First Validation (CRÍTICO)

**Antes de cualquier acción**, verificar si existe una skill que resuelva el problema:

```
1. Consultar: core/skills/SKILLS.md
2. Identificar skill apropiada
3. Si existe → USARLA
4. Si no → Crear solución documentando por qué
```

### CORE-005: Assembly Line

Flujo de ejecución para tareas complejas:

| Fase | Acción | Output |
|------|--------|--------|
| **DELIMITAR** | Definir alcance, crear PRP | Blueprint |
| **MAPEAR** | Descubrir contexto con @context-scout | Archivos relevantes |
| **EJECUTAR** | Delegar a subagentes | Resultados |
| **VALIDAR** | Verificar con assertions | QA |
| **PRESERVAR** | Ejecutar session-end.py | Conocimiento guardado |

Ver documentación completa en `docs/ASSEMBLY-LINE.md`.

### CORE-006: Version Governance

**Antes de cualquier release**, verificar consistencia de versión:

```
1. Leer: cat VERSION
2. Ejecutar: python core/scripts/version-updater.py
3. Actualizar: CHANGELOG.md manualmente
4. Validar: sync-prealpha.py verifica consistencia
```

### CORE-007: Release Sanitization & Data Protection

**Antes de sincronizar a PROD**, verificar:

| Check | Acción |
|-------|--------|
| Sin credenciales | `grep -r "token\|password\|secret" .` |
| Sin PRPs en root | `ls PRPs/` debe dar error |
| Sin docs internos | `PROD_ONLY_IGNORE_PATTERNS` aplicado |
| DEV protegido | `PROTECTED_DIRS` con backup |