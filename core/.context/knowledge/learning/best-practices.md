# Mejores Prácticas

> Patrones probados que funcionan. Seguir estas prácticas asegura calidad.

## Release y Sincronización

### ✅ Crear versión CLEAN-PROD para archivos de configuración sensibles

**Cuándo aplicar**: Todo archivo de config que contenga:
- Credenciales o API keys
- URLs de repos privados
- Datos de desarrollo interno
- Información de máquina local

**Proceso**:
1. Crear `archivo.config.json.CLEAN-PROD` en BASE
2. Sanitizar: remover datos sensibles
3. Actualizar `sync-prealpha.py` para usar CLEAN-PROD en PROD
4. Agregar a PROD_ONLY_IGNORE_PATTERNS el archivo original

**Ejemplos**:
```
opencode.jsonc.CLEAN-PROD          → MCPs sin credenciales
vitals.config.json.CLEAN-PROD      → Sin remote_repo
```

**Validación**:
```bash
# En PROD después de sync:
grep -E "pk_|sk_|remote_repo|private" config/*.json && echo "❌ ERROR" || echo "✅ OK"
```

---

### ✅ Verificar links en AGENTS.md antes de release

**Problema**: Links a `../PRPs/` funcionan en BASE pero están rotos en PROD.

**Solución**: Usar `docs/core/PRP-XXX.md` para documentación pública.

**Checklist pre-release**:
```bash
# Verificar todos los links en AGENTS.md
grep -o '\[.*\](.*)' AGENTS.md | while read link; do
    path=$(echo $link | grep -o '(.*)' | tr -d '()')
    [ -f "$path" ] || echo "❌ Roto: $path"
done
```

**Estructura**:
```
BASE/PRPs/PRP-001-CORE-Framework-Validation.md          (completo, interno)
docs/core/PRP-001-CORE-Framework-Validation.md          (simplificado, público)
```

---

### ✅ Excluir archivos generados localmente de PROD

**Archivos que NUNCA deben ir a PROD**:
- `core/.context/vitals/vitals.manifest.json` (índice local)
- `core/.context/vitals/vitals.log` (logs locales)
- `core/.context/vitals/backups/` (backups locales)
- `core/.context/sessions/` (sesiones de usuario)
- `core/.context/codebase/` (datos de usuario)

**Configuración en sync-prealpha.py**:
```python
PROD_ONLY_IGNORE_PATTERNS = {
    "core/.context/vitals/vitals.manifest.json",
    "core/.context/vitals/vitals.log",
    "core/.context/vitals/backups/",
    # ...
}
```

---

### ✅ Validar instalación limpia antes de declarar release estable

**Proceso de validación**:
1. Clonar repo PROD en directorio limpio
2. Ejecutar `python core/scripts/session-start.py`
3. Verificar:
   - No hay errores de "archivos faltantes"
   - No hay credenciales expuestas
   - AGENTS.md tiene links válidos
   - opencode.jsonc es válido

**Comandos de validación**:
```bash
# Verificar credenciales
grep -r "pk_\|sk_\|api_key" . --include="*.json" --include="*.yaml"

# Verificar links rotos
find . -name "*.md" -exec grep -l "404\|Not Found" {} \;

# Verificar estructura
ls core/.context/vitals/vitals.manifest.json && echo "❌ No debe existir" || echo "✅ OK"
```

---

## Flujo de Sesión

### ✅ SIEMPRE ejecutar session-start.py al inicio

```bash
python core/scripts/session-start.py
```

**Beneficios**:
- Contexto cargado automáticamente
- Sesión del día creada
- Multi-CLI coordinado
- Pendientes heredados visibles

---

### ✅ SIEMPRE ejecutar session-end.py al cerrar

```bash
python core/scripts/session-end.py
```

**Beneficios**:
- time_end registrado
- Resumen generado
- Pendientes migrados
- Sesión indexada

---

### ✅ Verificar persistencia antes de salir

```markdown
Checklist:
- [ ] ¿Ejecuté session-end.py?
- [ ] ¿Mi sesión tiene time_end?
- [ ] ¿Mis pendientes están en recordatorios.md?
```

---

## Código y Desarrollo

### ✅ Clasificación de Scripts CORE vs INTERNOS

| Categoría | Criterio | Ejemplos |
|-----------|----------|----------|
| **CORE** | Usado por framework para funcionar | `pa.py`, `install.py`, `kb-init.py`, `multi_cli_coordinator.py` |
| **INTERNO** | Rutas hardcodeadas o uso específico del desarrollador | `sync-prealpha.py`, `recover-maaji.py`, `backup-critical.bat` |

**Detectores de scripts internos**:
```bash
grep -l "C:/ACTUAL/FreakingJSON" core/scripts/*.py
grep -l "Pa_Pre_alpha_Opus" core/scripts/*.py
grep -l "Maaji" core/scripts/*.py
```

**Importante**: `sync-context.py` es CORE (usado por install.py), NO confundir con `sync-prealpha.py` (interno).

*Migrado desde ideas.md - 2026-03-11*

---

### ✅ Consultar SKILLS.md antes de crear scripts

```
1. Leer: core/skills/SKILLS.md
2. Buscar skill apropiada
3. Si existe → usarla
4. Si no → crear script documentando por qué
```

---

### ✅ Usar importlib para scripts con guiones

```python
# Correcto
import importlib.util
spec = importlib.util.spec_from_file_location("name", "script-name.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

# Incorrecto
from script-name import X  # SyntaxError
```

---

### ✅ Leer archivo antes de editarlo

```python
# Siempre leer primero
content = file.read_text(encoding="utf-8")
# Luego editar
new_content = transform(content)
file.write_text(new_content, encoding="utf-8")
```

---

## Documentación

### ✅ Principio MVI (Minimal Viable Information)

- Máximo 1-3 oraciones por concepto
- 3-5 bullets por sección
- Ejemplo mínimo cuando aplique
- Referencia a docs completos, no duplicar

---

### ✅ Separar ejecutivo de descriptivo

| Archivo | Propósito |
|---------|-----------|
| `recordatorios.md` | Checklist ejecutivo |
| `PLAN-*.md` | Documento descriptivo |
| `sessions/*.md` | Log de sesión |

---

## Debugging

### ✅ Cuando hay error, ARREGLARLO

> "Si un error bloquea el avance, ARREGLALO. No lo reportes esperando respuesta."

1. Documentar el error
2. Investigar causa raíz
3. Implementar fix
4. Actualizar documentación
5. Crear playbook si es recurrente### 2026-03-11: [PENDIENTE VALIDACION] Se resolvio el problema de encoding usando: ```python import io sys.stdout = io.

> **Estado**: pending_validation
> **Extraido de**: session#L12
> **Deteccion**: automatica

**Contexto**: Auto-detected from Solucion section

**Practica**: Se resolvio el problema de encoding usando: ```python import io sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8') ``` Esto funciono correctamente. [OK]

**Beneficio**: Resolved an issue during session

---

### 2026-03-11: [PENDIENTE VALIDACION] Usar siempre `encoding='utf-8'` al leer archivos en Windows

> **Estado**: pending_validation
> **Extraido de**: session#L43
> **Deteccion**: tag #best-practice

**Contexto**:  ## Best Practice 

**Practica**: Usar siempre `encoding='utf-8'` al leer archivos en Windows

**Beneficio**: To be documented

---

### 2026-03-11: [PENDIENTE VALIDACION] Se resolvio el problema de encoding usando: ```python import io sys.stdout = io.

> **Estado**: pending_validation
> **Extraido de**: session#L12
> **Deteccion**: automatica

**Contexto**: Auto-detected from Solucion section

**Practica**: Se resolvio el problema de encoding usando: ```python import io sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8') ``` Esto funciono correctamente. [OK]

**Beneficio**: Resolved an issue during session

---

### 2026-03-11: [PENDIENTE VALIDACION] Usar siempre `encoding='utf-8'` al leer archivos en Windows

> **Estado**: pending_validation
> **Extraido de**: session#L43
> **Deteccion**: tag #best-practice

**Contexto**:  ## Best Practice 

**Practica**: Usar siempre `encoding='utf-8'` al leer archivos en Windows

**Beneficio**: To be documented

---

### 2026-03-11: [PENDIENTE VALIDACION] Se resolvio el problema de encoding usando: ```python import io sys.stdout = io.

> **Estado**: pending_validation
> **Extraido de**: session#L12
> **Deteccion**: automatica

**Contexto**: Auto-detected from Solucion section

**Practica**: Se resolvio el problema de encoding usando: ```python import io sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8') ``` Esto funciono correctamente. [OK]

**Beneficio**: Resolved an issue during session

---

### 2026-03-11: [PENDIENTE VALIDACION] Usar siempre `encoding='utf-8'` al leer archivos en Windows

> **Estado**: pending_validation
> **Extraido de**: session#L43
> **Deteccion**: tag #best-practice

**Contexto**:  ## Best Practice 

**Practica**: Usar siempre `encoding='utf-8'` al leer archivos en Windows

**Beneficio**: To be documented

---


## 2026-03-12: Sincronización PROD

### ✅ SIEMPRE verificar remoto después de push

**Problema**: Se asumió que el push fue correcto sin verificar el contenido real en GitHub.

**Práctica**: Después de cada push a PROD, ejecutar:

```bash
# Verificar VERSION
git show origin/main:VERSION

# Verificar README.md
git show origin/main:README.md | head -10

# Verificar AGENTS.md
git show origin/main:AGENTS.md | head -10

# Verificar que NO hay PRPs en root
git ls-tree origin/main PRPs && echo "ERROR" || echo "OK"
```

---

### ✅ SIEMPRE usar @context-scout antes de sync/release

**Problema**: Se ejecutó sync sin consultar el contexto de problemas previos.

**Práctica**: Antes de cualquier sync/release:

```markdown
1. Invocar @context-scout para descubrir:
   - Problemas previos documentados
   - Patrones establecidos
   - Checklist de validación

2. Revisar:
   - sessions/anteriores (problemas solucionados)
   - discoveries.md (patrones descubiertos)
   - best-practices.md (lo que funciona)
```

---

### ✅ Checklist Pre-Release Obligatorio

```markdown
## ANTES de sync-prealpha.py --mode=prod

- [ ] Ejecutar @context-scout
- [ ] Verificar README-simple.md actualizado
- [ ] Verificar VERSION correcto
- [ ] Verificar CHANGELOG actualizado

## DESPUÉS de sync

- [ ] framework-guardian.py --timing pre-release
- [ ] Manual check: VERSION, README.md, AGENTS.md
- [ ] No credentials: grep -E "pk_|sk_" opencode.jsonc
- [ ] No PRPs: ls PRPs/ → debe fallar

## DESPUÉS de push

- [ ] git show origin/main:VERSION
- [ ] git show origin/main:README.md | head
- [ ] git show origin/main:AGENTS.md | head
```

---

## 2026-03-12: Checklist Obligatorio Pre/Post Sync

### ANTES de `sync-prealpha.py --mode=prod`

```bash
# 1. Ejecutar tests de validación
python core/scripts/tests/test_sync_critical.py

# 2. Dry-run OBLIGATORIO
python core/scripts/sync-prealpha.py --mode=prod --dry-run

# 3. Verificar que NO hay eliminaciones de archivos críticos
# Si dry-run muestra "D:0" o solo eliminaciones correctas, continuar
```

### DESPUÉS de sync

```bash
# 1. Validación framework
python core/scripts/framework-guardian.py --timing pre-release

# 2. Verificar archivos críticos manualmente
ls AGENTS.md VERSION README.md docs/core/PRP-001*.md

# 3. Si todo OK, commit
git add -A && git commit -m "sync: descripción"

# 4. Push
git push origin main
```

### DESPUÉS de push - Verificación REMOTA

```bash
# Verificar que archivos existen en GitHub
git fetch origin
git show origin/main:VERSION
git show origin/main:AGENTS.md | head
git ls-tree origin/main docs/core --name-only
```

---

## 2026-03-12: Tests Automatizados en Framework

### Ubicación
`core/scripts/tests/test_sync_critical.py`

### Ejecución
```bash
python core/scripts/tests/test_sync_critical.py
```

### Tests incluidos
1. **test_path_normalization**: Verifica fix del bug "./"
2. **test_critical_files_list**: Verifica CRITICAL_PROD_FILES
3. **test_prod_local_only_patterns**: Verifica protecciones
4. **test_no_dot_slash_in_comparison**: Verifica comparación correcta

### Integración
- Ejecutar antes de cada sync a PROD
- Ejecutar en CI/CD si está configurado
- Incluir en `framework-guardian.py --timing pre-release`

---
