# Protocolo de Inicialización del Framework

> **Aplicable a**: TODOS los agentes, modelos, entry points y modos de uso del framework.

---

## Propósito

Garantizar que **cualquier interacción** con el framework (independientemente del agente, modelo o punto de entrada) tenga acceso completo al contexto relevante: workspaces, proyectos y modos de trabajo.

---

## Secuencia Obligatoria de Inicialización

### Paso 1: Session Start (Siempre)

```bash
python core/scripts/session_start.py
```

**Qué hace**:
- Crea o verifica sesión del día (`core/.context/sessions/YYYY-MM-DD.md`)
- Muestra estado del framework (pendientes, logros, skills activos)
- Tiempo: <2 segundos

**Cuándo**: Al inicio de CADA sesión.

---

### Paso 2: Bootstrap canónico (Tier 0)

**LEER ESTE ARCHIVO PRIMERO**:
```bash
# Leer AGENTS-lite.md — punto de entrada canónico (<500 tokens)
cat AGENTS-lite.md
```

**Qué contiene**:
- Bootstrap mínimo del framework
- Router de agentes y tiers de referencia
- Entry point de `session_start.py`
- Paths críticos de inicialización
- Recordatorio del principio MVI

**Por qué**: `AGENTS-lite.md` es el Tier 0 consumido por `core/scripts/context_loader.py`, evitando cargar documentación completa antes de que el usuario escriba nada.

**Cuándo**: Al inicio de CADA sesión.

**Fallback**: Si `AGENTS-lite.md` no está disponible, usar `session_start.py` y luego `AGENTS.md` como router de respaldo.

---

### Paso 3: Detección de Contexto (Siempre)

Delegar a `@context-scout`:

```yaml
detect_workspace: true    # Detectar workspace actual
detect_project: true      # Detectar proyecto activo
detect_mode: true         # Detectar modos disponibles (no activar)
verbose: normal           # Nivel de output: silent|minimal|normal|debug
```

**Qué hace**:
- Analiza cwd (current working directory)
- Detecta workspace, proyecto y modo
- Registra proyectos nuevos automáticamente
- Reporta hallazgos

**Output esperado**:
```json
{
  "workspace": "professional",
  "project": "MyApp",
  "mode": {
    "available": ["BASE", "DEV", "PROD"],
    "active": null
  },
  "context_loaded": true
}
```

---

### Paso 4: Carga de Contexto (Condicional)

`session_start.py` usa `core/scripts/context_loader.py` para cargar Tier 0-1 inmediatamente y dejar Tier 2-4 en lazy loading.

Cargar automáticamente:

1. **Workspace**: Siempre (si detectado)
   - Archivo: `core/.context/workspaces/{workspace}.md`
   
2. **Proyecto**: Si proyecto detectado
   - Archivo: `workspaces/{workspace}/projects/{project}/.context/project.md`
   - Registra en: `core/.context/projects/_registry.md`
   
3. **Modo**: Solo si usuario especificó
   - Comando: `/mode DEV` (o BASE, PROD)
   - Contexto específico del modo (automatizaciones, configs)

### Paso 5: Workflow Gate (Tareas Complejas)

Antes de PRDs, roadmap, arquitectura, auditorías amplias o cambios multi-módulo:

```bash
python core/scripts/framework_guardian.py \
  --timing pre-execution \
  --task "Descripcion de la tarea" \
  --task-type prd|roadmap|architecture|audit|feature
```

**Obligatorio además**:
- usar `@context-scout` antes de exploración amplia
- validar skills en `core/skills/SKILLS.md`
- usar `@prd-generator` para PRDs / feature-definition
- si falla el guardrail, volver a DELIMITAR/MAPEAR

---

## Configuración de Verbosidad

Usuario puede configurar en `core/.context/MASTER.md`:

```yaml
framework:
  initialization:
    verbose: normal  # Opciones: silent, minimal, normal, debug
```

### Niveles:

| Nivel | Output | Uso recomendado |
|-------|--------|-----------------|
| `silent` | Solo errores críticos | CI/CD, scripts automatizados |
| `minimal` | Resultado final + warnings | Usuarios experimentados |
| `normal` | Progreso completo | **Default**, usuarios estándar |
| `debug` | Todo el detalle | Debugging, desarrollo |

### Cambio temporal:

```bash
# Vía comando
/init --verbose=debug

# O al iniciar sesión
python core/scripts/session_start.py
```

---

## Comandos Post-Inicialización

Una vez inicializado, estos comandos están disponibles:

| Comando | Descripción | Ejemplo |
|---------|-------------|---------|
| `/status` | Muestra contexto cargado | `/status` |
| `/context` | Detalle completo de contexto | `/context` |
| `/reload` | Recarga contexto desde disco | `/reload` |
| `/workspaces` | Lista workspaces disponibles | `/workspaces` |
| `/projects` | Lista proyectos en workspace | `/projects` |
| `/workspace {name}` | Cambia workspace | `/workspace personal` |
| `/project {name}` | Cambia proyecto | `/project Blog` |
| `/mode {BASE\|DEV\|PROD}` | Establece modo | `/mode DEV` |

---

## Entry Points Soportados

### 1. pa-assistant.md (Agente Principal)

```yaml
# En pa-assistant.md
init_sequence:
  mandatory:
    - step: "session_start"
      command: "python core/scripts/session_start.py"
      critical: true
    
    - step: "context_detection"
      delegate: "@context-scout"
      params:
        detect_workspace: true
        detect_project: true
        detect_mode: true
        verbose: "{{user.preference.verbose|default('normal')}}"
      critical: true
```

**Comportamiento**: Auto-ejecuta protocolo al iniciar sesión.

---

### 2. Otros Agentes (No pa-assistant)

Para agentes que usen el framework pero no sean pa-assistant:

**Requisito**: Incluir en system prompt o instrucciones iniciales:

```
[INSTRUCCIÓN OBLIGATORIA - INICIO DE SESIÓN]

Antes de cualquier acción:

1. Ejecutar: python core/scripts/session_start.py
2. Delegar a @context-scout para detección de contexto
3. Cargar contexto detectado
4. Reportar contexto activo al usuario

Referencia completa: core/INIT-PROTOCOL.md
```

---

### 3. pa.bat / pa.sh (Entry Point Principal)

```bash
#!/bin/bash
# PA Framework Entry Point

echo "[PA Framework] Inicializando..."

# 1. Session Start
python core/scripts/session_start.py

# 2. Detect Context
DETECTED=$(python core/scripts/detect-workspace.py --json)
echo "[PA Framework] Contexto detectado:"
echo "$DETECTED" | jq -r '
  "  Workspace: \(.workspace.name)",
  "  Proyecto:  \(.project.name // "N/A")",
  "  Modos:     \(.mode.available | join(", "))"
'

# 3. Exportar para CLI
export PA_CONTEXT="$DETECTED"

echo "[PA Framework] Listo. Usa /status para ver detalles."
echo ""

# 4. Iniciar CLI
opencode
```

---

### 4. Inicialización Manual (Init Sequence)

Para usuarios que inician sesión manualmente:

```bash
# 1. Navegar al directorio del framework
cd /ruta/al/pa-framework

# 2. Ejecutar protocolo
python core/scripts/session_start.py
python core/scripts/detect-workspace.py

# 3. Verificar contexto
# (La salida muestra workspace, proyecto y modo detectados)
```

**Documentado en**: `AGENTS.md` (Step 3: Fallback Manual)

---

## Detección de Cambio de Contexto

Si durante la sesión el usuario cambia de workspace/proyecto:

```
[DETECTADO] Cambio de contexto:
  Anterior: professional/MyApp
  Actual:   personal/BlogProject

¿Deseas cargar el nuevo contexto? (s/n): s

[Cargando contexto personal/BlogProject...]
[OK] Contexto actualizado. Usa /status para verificar.
```

**Implementado por**: `@context-scout` con `track_changes: true`

---

## Estructura de Contexto

### Contexto de Workspace

Ubicación: `core/.context/workspaces/{workspace-name}.md`

Contenido típico:
```yaml
---
workspace: personal
description: "Proyectos personales y de aprendizaje"
created: 2026-01-15
---

# Workspace: Personal

## Proyectos Activos
- Blog
- Portfolio
- Learning/Rust

## Configuración Específica
- verbose: debug
- default_mode: DEV
```

### Contexto de Proyecto

Ubicación: `workspaces/{workspace}/projects/{project}/.context/project.md`

Creado automáticamente si no existe.

Contenido típico:
```yaml
---
project: Blog
created: 2026-02-20
workspace: personal
modes_available: ["BASE", "DEV"]
---

# Proyecto: Blog

## Descripción
Blog personal técnico.

## Automatizaciones
- (pendiente configurar)

## Recursos
- Repo: github.com/user/blog
- Deploy: Vercel
```

---

## Registro de Proyectos

Ubicación: `core/.context/projects/_registry.md`

Actualizado automáticamente por `@context-scout`:

```markdown
# Registro de Proyectos

| Proyecto | Workspace | Ruta | Detectado | Último Uso |
|----------|-----------|------|-----------|------------|
| MyApp    | professional | workspaces/professional/projects/MyApp/ | 2026-02-25 | 2026-02-26 |
| Blog     | personal     | workspaces/personal/projects/Blog/      | 2026-02-26 | 2026-02-26 |
```

---

## Troubleshooting

### "No se detectó workspace"

**Causa**: cwd no está dentro de `workspaces/`
**Solución**: 
```bash
cd workspaces/{workspace}/  # Navegar a workspace
# O
/workspace {nombre}         # Especificar manualmente
```

### "Proyecto no aparece en /projects"

**Causa**: Carpeta no está en `workspaces/{workspace}/projects/`
**Solución**:
```bash
# Mover proyecto a ubicación correcta
mv /ruta/proyecto workspaces/professional/projects/

# O registrar manualmente
/project register /ruta/al/proyecto
```

### "Modo no cambia con /mode"

**Causa**: No existen carpetas BASE/DEV/PROD en el proyecto
**Solución**:
```bash
# Crear estructura de modos
mkdir -p workspaces/{workspace}/projects/{proyecto}/{BASE,DEV,PROD}
```

---

## Unified Memory System (Integral, Persistent, Lossless)

El framework usa un workflow de memoria **integral**: las 4 capas persisten en paralelo y se sincronizan continuamente. No son rutas excluyentes por tipo de tarea.

### Definición de las 4 Capas

| Sistema | ¿Para qué? | Persistencia |
|---------|------------|--------------|
| `.md` (Sessions) | Memoria simple/rápida (log cronológico universal) | `core/.context/sessions/YYYY-MM-DD.md` |
| `Memory MD` | Memoria intermedia (síntesis, patrones, decisiones reutilizables) | `core/.context/memory/` |
| `SQLite` | Memoria permanente estructurada (TODOs, sesiones completas, mensajes + metadata) | `data/sessions.db` |
| `Wiki (MkDocs)` | Segundo cerebro relacional (contexto + relaciones/grafos) | `core/.context/knowledge/wiki/` + `docs/` |

### Política de Persistencia Integral

| Principio | Garantía |
|------|--------|
| Captura continua | Cada interacción relevante se preserva en sesión y capa estructurada |
| No pérdida de detalle | SQLite conserva detalle completo e histórico ilimitado |
| No pérdida de patrones | Extracción periódica a Memory MD |
| No pérdida de relaciones | Wiki + KB updater mantienen relacionamiento semántico |
| Cierre robusto | `session_end.py` + `memory_pipeline.py --full-cycle` consolidan todo |

### Triggers Automáticos

| Trigger | Acción automática |
|---------|-------------------|
| Nueva interacción | Captura en `.md` + SQLite (hook/bridge) |
| Decisión/patrón nuevo | Actualización de Memory MD |
| Consolidación por intervalo | `memory_pipeline --watch` ejecuta ciclo integral |
| Relacionamiento de conocimiento | `wiki_autopopulate.py` + `kb_updater.py` |
| Fin de sesión o cierre inesperado | Full-cycle + indexación final |

### Comandos de Verificación Rápida

```bash
# Estado integral de memoria persistente (4 capas)
python core/scripts/memory_pipeline.py --status

# Búsqueda cross-session estructurada
python core/scripts/session_search.py --limit 5

# Health check estructural de memoria/wiki
python core/scripts/memory_sync.py
```

> Referencia extendida: `docs/MEMORY-ARCHITECTURE.md`

---

## Versión y Actualizaciones

| Versión | Fecha | Cambios |
|---------|-------|---------|
| 1.0.0 | 2026-02-26 | Creación inicial del protocolo |
| 1.1.0 | 2026-04-15 | Unified Memory System (LLM-Wiki + Engram) |
| 1.2.0 | 2026-04-21 | Workflow integral 4 capas (persistencia completa + relacional) |

---

*Framework PA - Context-Aware Initialization Protocol v1.2*

