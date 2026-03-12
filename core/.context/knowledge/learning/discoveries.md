# Descubrimientos

> Hallazgos significativos identificados durante el uso del framework.

---

## 2026-03-11: Tarde - CRITICAL FIX Session

### Descubrimiento 1: PRPs Referencias Rotas en PROD

**Contexto**: Durante prueba de instalación limpia desde PROD remoto, se detectó que AGENTS.md tenía links rotos a `../PRPs/`

**Descubrimiento**: Los PRPs son documentación interna (excluida por CORE-007), pero AGENTS.md en PROD referenciaba paths que no existen.

**Impacto**: Los 7 procesos CORE documentados en AGENTS.md tenían links 404 para usuarios del repo público.

**Solución Aplicada**:
1. Crear `docs/core/` con versiones simplificadas de PRPs
2. Actualizar AGENTS.md para apuntar a `docs/core/PRP-XXX.md`
3. Sanitizar contenido (eliminar datos dev interno)

**Pattern establecido**: Todo archivo .md que referencie PRPs debe usar `docs/core/` en lugar de `../PRPs/`

---

### Descubrimiento 2: Bug Path "./" en sync-prealpha.py

**Contexto**: AGENTS.md desaparecía misteriosamente durante sync a PROD.

**Descubrimiento**: `Path.relative_to()` retorna "." para archivos en directorio raíz, causando que `rel_path` sea "./AGENTS.md" en lugar de "AGENTS.md".

**Problema**:
```python
# Origen: "./AGENTS.md"
# Destino: "AGENTS.md"
# Comparación: "./AGENTS.md" != "AGENTS.md" → Se marca para ELIMINACIÓN
```

**Solución**:
```python
rel_path = str(rel_root / file).replace("\\", "/")
if rel_path.startswith("./"):
    rel_path = rel_path[2:]  # Normalizar paths
```

**Impacto**: Este bug afectaba TODOS los archivos en root del proyecto.

---

### Descubrimiento 3: Patrón CLEAN-PROD es Esencial

**Contexto**: vitals.config.json contenía `remote_repo` apuntando a repo privado en PROD.

**Descubrimiento**: Cualquier archivo de configuración con datos sensibles/credenciales/info interna DEBE tener versión .CLEAN-PROD.

**Patrón Establecido**:
| Archivo Original | Versión CLEAN-PROD | Propósito |
|-----------------|-------------------|-----------|
| opencode.jsonc | opencode.jsonc.CLEAN-PROD | MCPs sin credenciales |
| vitals.config.json | vitals.config.json.CLEAN-PROD | Config sin remote_repo |

**Implementación en sync-prealpha.py**:
1. Detectar si existe versión CLEAN-PROD
2. Copiar CLEAN-PROD como archivo final
3. Eliminar CLEAN-PROD del destino (solo debe estar en BASE)

---

### Descubrimiento 4: vitals.manifest.json NO debe estar en PROD

**Contexto**: Instalación limpia reportaba "13,643 archivos críticos faltantes"

**Descubrimiento**: vitals.manifest.json es un índice generado localmente con rutas absolutas de la máquina de desarrollo.

**Impacto**: En instalación limpia, el 99% de las rutas no existen, causando falsos errores críticos.

**Solución**: Agregar a `PROD_ONLY_IGNORE_PATTERNS`:
- `core/.context/vitals/vitals.manifest.json`
- `core/.context/vitals/vitals.log`
- `core/.context/vitals/*.log`
- `core/.context/vitals/backups/`

**Nota**: vitals.manifest.json se regenera automáticamente en primera ejecución local.

---

## 2026-03

### 2026-03-11: Import dinámico para scripts con guiones

**Contexto**: `session-indexer.py` tiene guión en el nombre, pero Python no permite imports con guiones.

**Descubrimiento**: Usar `importlib.util.spec_from_file_location()` para cargar módulos dinámicamente.

```python
import importlib.util
spec = importlib.util.spec_from_file_location("session_indexer", "session-indexer.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
```

**Impacto**: Permite mantener convención de nombres con guiones mientras el código funciona correctamente.

---

### 2026-03-11: Flujo de sesión es crítico para persistencia

**Contexto**: El framework no tenía session-end.py, causando pérdida de contexto entre sesiones.

**Descubrimiento**: El flujo de cierre es TAN importante como el de inicio. Sin cierre ordenado:
- sessions-index.json se desactualiza
- Sesiones quedan en "active" para siempre
- Pendientes no se migran

**Solución implementada**: 
- `session-end.py` con atexit
- Closing Protocol en AGENTS.md
- Comandos ejecutables en session-manager.md

---

---

### 2026-03-09: Patrones de Sincronización Multi-Entorno

**Contexto**: Sincronización entre BASE/DEV/PROD con repos remotos públicos y privados.

**Patrones descubiertos**:

1. **Repos duales para desarrollo**:
   - `origin` = repo privado (BASE/DEV)
   - `upstream` = repo público (PreAlpha)
   - Permite mantener scripts internos en privados mientras el público está sanitized

2. **PROTECTED_DIRS dinámico**:
   - Lista base en sync-prealpha.py
   - Agregar según se detectan nuevos directorios de usuario
   - Validar con `ls -la` en DEV antes de sync

3. **Hotfix de emergencia**:
   - Cuando no hay acceso a BASE, aplicar fixes directamente en upstream
   - Documentar en CHANGELOG inmediatamente
   - Sincronizar de vuelta al volver al entorno habitual

4. **KB initialization automática**:
   - `install.py` y `update.py` deben llamar `kb-init.py`
   - Previene errores de "directorio no existe"

**Referencia**: `docs/SYNC-PROTOCOL.md` sección Hotfix de Emergencia

*Migrado desde ideas.md - 2026-03-11*

---

### 2026-03-09: MASTER.md Dinámico para Workspaces

**Contexto**: Discrepancia entre estado reportado y estado real de workspaces.

**Patrón**:
- MASTER.md tenía texto estático "No configurado"
- Los directorios físicos existían pero no se reflejaban

**Solución implementada**:
1. Función `update_master_workspace_status()` en pa.py
2. Función `sync_workspaces_status()` en session-start.py
3. Actualizar MASTER.md al crear workspaces
4. Sincronizar al inicio de cada sesión

**Patrón generalizable**:
- Cualquier archivo de estado en MASTER.md debería validarse contra filesystem
- Evita inconsistencia entre "lo que dice" y "lo que existe"

*Migrado desde ideas.md - 2026-03-11*

---

## Pendientes de Investigación

- [ ] ¿Cómo detectar automáticamente prompts exitosos?
- [ ] ¿Cómo extraer patrones de uso de interactions/*.jsonl?
- [ ] ¿Cómo medir efectividad de skills?### 2026-03-11: [PENDIENTE VALIDACION] Descubrimiento: El nuevo patron de error handling funciona mejor

> **Estado**: pendiente_validacion
> **Extraido de**: sessions/unknown#L9
> **Deteccion**: automatica

**Contexto**: Auto-detected from session

**Descubrimiento**: Descubrimiento: El nuevo patron de error handling funciona mejor

**Impacto**: To be evaluated

---

### 2026-03-11: [PENDIENTE VALIDACION] El modulo de extraction puede ser reutilizado #discovery

> **Estado**: pendiente_validacion
> **Extraido de**: sessions/unknown#L44
> **Deteccion**: automatica

**Contexto**: Auto-detected from session

**Descubrimiento**: El modulo de extraction puede ser reutilizado #discovery

**Impacto**: To be evaluated

---

### 2026-03-11: [PENDIENTE VALIDACION] El nuevo patron de error handling funciona mejor

> **Estado**: pendiente_validacion
> **Extraido de**: sessions/unknown#L9
> **Deteccion**: automatica

**Contexto**: Auto-detected from inline text

**Descubrimiento**: El nuevo patron de error handling funciona mejor

**Impacto**: To be evaluated

---

### 2026-03-11: [PENDIENTE VALIDACION] - El modulo de extraction puede ser reutilizado

> **Estado**: pendiente_validacion
> **Extraido de**: sessions/unknown#L10
> **Deteccion**: tag #discovery

**Contexto**: ## Hallazgos  - Descubrimiento: El nuevo patron de error handling funciona mejor

**Descubrimiento**: - El modulo de extraction puede ser reutilizado

**Impacto**: To be evaluated

---

### 2026-03-11: [PENDIENTE VALIDACION] Descubrimiento: El nuevo patron de error handling funciona mejor

> **Estado**: pendiente_validacion
> **Extraido de**: sessions/test_session.md#L9
> **Deteccion**: automatica

**Contexto**: Auto-detected from session

**Descubrimiento**: Descubrimiento: El nuevo patron de error handling funciona mejor

**Impacto**: To be evaluated

---

### 2026-03-11: [PENDIENTE VALIDACION] El modulo de extraction puede ser reutilizado #discovery

> **Estado**: pendiente_validacion
> **Extraido de**: sessions/test_session.md#L44
> **Deteccion**: automatica

**Contexto**: Auto-detected from session

**Descubrimiento**: El modulo de extraction puede ser reutilizado #discovery

**Impacto**: To be evaluated

---

### 2026-03-11: [PENDIENTE VALIDACION] El nuevo patron de error handling funciona mejor

> **Estado**: pendiente_validacion
> **Extraido de**: sessions/test_session.md#L9
> **Deteccion**: automatica

**Contexto**: Auto-detected from inline text

**Descubrimiento**: El nuevo patron de error handling funciona mejor

**Impacto**: To be evaluated

---

### 2026-03-11: [PENDIENTE VALIDACION] - El modulo de extraction puede ser reutilizado

> **Estado**: pendiente_validacion
> **Extraido de**: sessions/test_session.md#L10
> **Deteccion**: tag #discovery

**Contexto**: ## Hallazgos  - Descubrimiento: El nuevo patron de error handling funciona mejor

**Descubrimiento**: - El modulo de extraction puede ser reutilizado

**Impacto**: To be evaluated

---

### 2026-03-11: [PENDIENTE VALIDACION] Descubrimiento: El nuevo patron de error handling funciona mejor

> **Estado**: pendiente_validacion
> **Extraido de**: sessions/test_session.md#L9
> **Deteccion**: automatica

**Contexto**: Auto-detected from session

**Descubrimiento**: Descubrimiento: El nuevo patron de error handling funciona mejor

**Impacto**: To be evaluated

---

### 2026-03-11: [PENDIENTE VALIDACION] El modulo de extraction puede ser reutilizado #discovery

> **Estado**: pendiente_validacion
> **Extraido de**: sessions/test_session.md#L44
> **Deteccion**: automatica

**Contexto**: Auto-detected from session

**Descubrimiento**: El modulo de extraction puede ser reutilizado #discovery

**Impacto**: To be evaluated

---

### 2026-03-11: [PENDIENTE VALIDACION] El nuevo patron de error handling funciona mejor

> **Estado**: pendiente_validacion
> **Extraido de**: sessions/test_session.md#L9
> **Deteccion**: automatica

**Contexto**: Auto-detected from inline text

**Descubrimiento**: El nuevo patron de error handling funciona mejor

**Impacto**: To be evaluated

---

### 2026-03-11: [PENDIENTE VALIDACION] - El modulo de extraction puede ser reutilizado

> **Estado**: pendiente_validacion
> **Extraido de**: sessions/test_session.md#L10
> **Deteccion**: tag #discovery

**Contexto**: ## Hallazgos  - Descubrimiento: El nuevo patron de error handling funciona mejor

**Descubrimiento**: - El modulo de extraction puede ser reutilizado

**Impacto**: To be evaluated

---


## 2026-03-12: Sincronización BASE→DEV Multi-Entorno

### #discovery Patrón de Sincronización Selectiva

**Contexto**: DEV necesitaba actualización con features de BASE (FrameworkGuardian, docs/core/).

**Descubrimiento**: El patrón de sincronización BASE→DEV es diferente de BASE→PROD:

| Dirección | Consideraciones |
|-----------|-----------------|
| BASE→PROD | Sanitización obligatoria (CLEAN-PROD), excluir docs internos |
| BASE→DEV | Copia directa, preservar scripts internos únicos de DEV |

**Patrón establecido**:
1. Identificar archivos que necesitan sync (diff -rq)
2. Identificar archivos únicos de DEV que NO se deben sobrescribir
3. Copiar selectivamente solo archivos core del framework
4. Validar con diff que los archivos son idénticos
5. Commit con mensaje descriptivo de la fuente

**Archivos preservados en DEV** (no copiar desde BASE):
- `sync-*.sh`, `sync-*.bat` (scripts de sincronización específicos de DEV)
- `recover-maaji.py`, `restore-*.py` (scripts de recuperación específicos)
- `docs/PLAN-v0.2.0.md` (documentación de planificación)

**Impacto**: Este patrón permite mantener DEV sincronizado con mejoras de BASE sin perder sus herramientas específicas de desarrollo.

---

### #discovery Validación Post-Sync con diff

**Contexto**: Necesidad de verificar que los archivos copiados son idénticos.

**Descubrimiento**: `diff -rq` es más eficiente que `diff` individual para validar directorios completos.

```bash
# Validar directorio completo
diff -rq "DEV/docs/core" "BASE/docs/core" && echo "IDENTICAL"

# Validar archivo individual
diff "DEV/file.py" "BASE/file.py" && echo "IDENTICAL"
```

**Beneficio**: Confirmación visual de que la sincronización fue exitosa antes del commit.

---

### #discovery AGENTS.md puede eliminarse del remoto por sync incorrecto

**Contexto**: Durante push a PROD, se detectó que AGENTS.md no existía en el remoto.

**Descubrimiento**: Un sync mal ejecutado puede eliminar archivos críticos del framework en el remoto.

**Causa probable**:
- `sync-prealpha.py` con `--delete` activado
- Commit directo en el remoto sin archivos del framework

**Solución aplicada**:
1. Verificar siempre que archivos críticos existen en remoto: `git show origin/main:AGENTS.md`
2. Si falta, usar `--force-with-lease` para restaurar
3. Documentar en sesión para trazabilidad

**Prevención**: Siempre validar con `framework-guardian.py --timing pre-release` antes de push.

---

## 2026-03-12: Fix README.md Desactualizado en PROD Remoto

### #discovery README-simple.md es la fuente de README.md en PROD

**Contexto**: PROD remoto tenía README.md con v0.1.7 en lugar de v0.2.0-prealpha.

**Descubrimiento**: Según CORE-007, `README-simple.md` en BASE se convierte en `README.md` en PROD. Si README-simple.md no se actualiza, PROD queda desactualizado.

**Causa raíz**:
1. README-simple.md no estaba en version-updater.py
2. Se actualizó README.md pero no README-simple.md
3. sync-prealpha.py copió el archivo desactualizado

**Solución aplicada**:
1. Actualizar README-simple.md en BASE manualmente
2. Ejecutar sync-prealpha.py --mode=prod
3. Validar con framework-guardian --timing pre-release
4. Verificar en remoto: `git show origin/main:README.md`

**Prevención**: Agregar README-simple.md a version-updater.py.

---

### #discovery Case Sensitivity Windows vs Git

**Contexto**: sync-prealpha.py detectaba que eliminaría AGENTS.md y agregaría Agents.md.

**Descubrimiento**: Windows es case-insensitive, Git es case-sensitive. `Agents.md` y `AGENTS.md` son el mismo archivo en Windows pero diferentes en Git.

**Impacto**: El sync detecta esto como:
- Eliminar: AGENTS.md (existe en PROD)
- Agregar: Agents.md (existe en BASE)

**Solución**: Usar `git mv Agents.md AGENTS.md` para renombrar correctamente.

**Validación**: `git status` debe mostrar `R Agents.md -> AGENTS.md` (rename).

---

### #discovery El flujo sync-prealpha.py --dry-run es OBLIGATORIO

**Contexto**: Se ejecutó sync-prealpha.py --mode=prod directamente en intento anterior.

**Descubrimiento**: El dry-run revela:
1. Archivos que se eliminarán (validar que son correctos)
2. Archivos que se modificarán (validar cambios)
3. Problemas de case sensitivity
4. Archivos nuevos que se agregarán

**Patrón establecido**:
```bash
# SIEMPRE primero:
python core/scripts/sync-prealpha.py --mode=prod --dry-run

# Revisar output cuidadosamente
# Luego ejecutar:
python core/scripts/sync-prealpha.py --mode=prod
```

**Excepción**: NUNCA omitir dry-run, incluso si se tiene "confianza" en los cambios.

---

## 2026-03-12: FIX CRÍTICO DEFINITIVO - Bug "./"

### #critical #bug #sync Bug del Path "./" - SOLUCIONADO DEFINITIVAMENTE

**Contexto**: Durante sync a PROD, archivos en directorio raíz se eliminaban incorrectamente.

**Causa raíz** (`sync-prealpha.py:655`):
```python
# BUG:
rel_root = Path(root).relative_to(src_dir)  # Retorna "." para root
rel_path = str(rel_root / file)  # Retorna "./AGENTS.md"

# dest_files_before tiene: {"AGENTS.md"}
# src_files tiene: {"./AGENTS.md"}
# deleted = dest_files_before - src_files = {"AGENTS.md"} → ELIMINADO!
```

**Fix aplicado** (`sync-prealpha.py:660-664`):
```python
rel_path = str(rel_root / file).replace("\\", "/")
# FIX CRÍTICO: Normalizar path "./" para archivos en directorio raíz
if rel_path.startswith("./"):
    rel_path = rel_path[2:]
```

**Protecciones adicionales**:
1. `CRITICAL_PROD_FILES`: 17 archivos validados post-sync
2. `PROD_LOCAL_ONLY_PATTERNS`: 30+ patrones protegidos
3. Validación falla si archivos críticos faltan
4. Test automatizado: `core/scripts/tests/test_sync_critical.py`

**Commit**: `ebd6b74` (BASE), `3113de9` (PROD)

**Impacto**: Este bug NO volverá a causar pérdida de archivos en PROD.

---

### #discovery Badge README sin color se rompe

**Contexto**: Badge `[![Release](https://img.shields.io/badge/release-v0.2.0--prealpha)]` no se renderizaba.

**Descubrimiento**: Shields.io requiere color al final del badge.

**Fix**: `[![Release](https://img.shields.io/badge/release-v0.2.0--prealpha-blue)]`

**Prevención**: Agregar README-simple.md a version-updater.py.

---

### #discovery Link docs/technical no existe en PROD

**Contexto**: README.md link a `docs/technical` pero ese directorio está en `.gitignore`.

**Descubrimiento**: El link causaba 404 en README público.

**Fix**: Cambiar link a `./README-technical.md` que sí existe en PROD.

---
