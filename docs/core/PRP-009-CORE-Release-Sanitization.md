---
title: "CORE-007: Release Sanitization & Data Protection"
version: "0.2.0-prealpha"
type: "process"
scope: "public"
prp: "PRP-009"
---

# CORE-007: Release Sanitization & Data Protection

## Principio Fundamental

**PROD es público (solo archivos autorizados), DEV es protegido (preserva datos/credenciales), BASE es completo (todo el contexto de desarrollo).**

## Descripción

El proceso CORE-007 establece tres entornos con niveles de acceso diferenciados, asegurando que el código público (PROD) esté sanitizado de datos sensibles, credenciales y documentación interna, mientras que el entorno de desarrollo (DEV) preserva el contexto completo del usuario.

Este principio garantiza:
- Seguridad en releases públicos
- Privacidad de datos de usuario
- Separación clara de responsabilidades
- Flujo de sincronización controlado

## Los Tres Entornos

| Entorno | Privacidad | Propósito | Contenido |
|---------|-----------|-----------|-----------|
| **BASE** | 🔒 Privado | Código fuente framework | Todo el contexto de desarrollo |
| **DEV** | 🔒 Privado | Testing interno | PROD-Ready + datos/credenciales usuario |
| **PROD** | 🌍 Público | Release público | Solo archivos autorizados/saneados |

### BASE (Código Fuente Completo)

**Ubicación**: `Model-Agnostic-AI-Personal-Assistant-Framework`

**Contiene**:
- ✅ Todo el código fuente
- ✅ `opencode.jsonc` completo (con credenciales)
- ✅ `opencode.jsonc.CLEAN-PROD` (versión saneada)
- ✅ Backlog y docs internos
- ✅ Scripts de sync y automatización
- ✅ PRPs (Planes de desarrollo)
- ✅ Workspaces (estructura base)

### DEV (Testing Interno)

**Ubicación**: `Pa_Pre_alpha_Opus_4_6_DEV`

**Contiene**:
- ✅ Todo lo de BASE (sincronizado)
- ✅ `opencode.jsonc` completo (credenciales)
- ✅ Workspaces locales del usuario (protegidos)
- ✅ Sessions locales (protegidas)
- ✅ Codebase personal (protegido)
- ✅ Agentes/skills locales en `_local/`

**Protegido (nunca se sobrescribe)**:
- `core/.context/sessions`
- `core/.context/codebase`
- `core/.context/workspaces`
- `workspaces/` (root)
- `core/agents/subagents/_local`
- `core/skills/_local`

### PROD (Público)

**Ubicación**: `Pa_Pre_alpha_Opus_4_6` → GitHub público

**Contiene**:
- ✅ `opencode.jsonc.CLEAN-PROD` → `opencode.jsonc` (sin credenciales)
- ✅ `README-simple.md` → `README.md` (user-friendly)
- ✅ Docs públicos (sin backlog, sin docs internos)
- ✅ Skills públicas
- ✅ Agentes públicos

**NO contiene**:
- ❌ Credenciales o API keys
- ❌ `backlog.md` ni docs internos
- ❌ Workspaces del usuario
- ❌ Sessions o codebase personal
- ❌ Agentes/skills locales (`_local/`)
- ❌ PRPs (documentación interna)

## Flujo de Sincronización

```
BASE (código fuente)
    ↓
[sync-prealpha.py --mode=dev]
    ↓
DEV (testing + datos usuario)
    ↓
[sync-prealpha.py --mode=prod]
    ↓
PROD (saneado + validado)
    ↓
[git push upstream main]
    ↓
GitHub Público
```

## Cuándo Aplicar

- **Antes de push a remoto público**: Siempre sanitizar
- **Sync a PROD**: Ejecutar validación completa
- **Releases**: Usar RELEASE-STAGING para validación
- **Hotfixes**: Seguir protocolo de emergencia

## Flujo de Trabajo

### Paso 1: Preparar en BASE

Asegurar que exista `opencode.jsonc.CLEAN-PROD`:

```bash
# Verificar
ls opencode.jsonc.CLEAN-PROD

# Debe contener solo MCPs públicos:
# - context7
# - sequentialthinking
# - github-mcp-server (sin token real)
```

### Paso 2: Ejecutar Sync a PROD

```bash
cd BASE
python core/scripts/sync-prealpha.py --mode=prod
```

**El script automáticamente**:
- Usa `opencode.jsonc.CLEAN-PROD` en lugar de `opencode.jsonc`
- Sana archivos en `core/.context/codebase/` usando templates de `core/.context/codebase/.sanitized/`
- Excluye archivos en `PROD_ONLY_IGNORE_PATTERNS`
- Protege directorios sensibles
- Genera `RELEASE-STAGING/` para validación

#### Saneado de Archivos `codebase/`

Los archivos en `core/.context/codebase/` contienen información interna del usuario (ideas, recordatorios, backlog). **NO se excluyen del sync** porque son parte del framework, pero **sí se sanitizan**:

| Archivo | Template | Descripción |
|---------|----------|-------------|
| `ideas.md` | `.sanitized/ideas.md` | Solo estructura, sin ideas internas |
| `recordatorios.md` | `.sanitized/recordatorios.md` | Solo estructura de pendientes, sin tareas reales |
| `BACKLOG-2.0.md` | `.sanitized/BACKLOG-2.0.md` | Solo plantilla, sin contenido interno |
| `backlog.md` | `.sanitized/backlog.md` | Solo plantilla |

**Para agregar un nuevo archivo sanitizado**:
1. Crear template en `core/.context/codebase/.sanitized/{nombre_archivo}.md`
2. El sync lo usará automáticamente en modo PROD
3. NO agregar `.sanitized/` a git (ya está excluido)

### Paso 3: Validación POST-SYNC (CRÍTICO)

```bash
cd PROD

# Check 1: README es user-friendly
if grep -q "Dev HQ vs Public Release" README.md; then
    echo "❌ ERROR: README técnico detectado"
    exit 1
fi

# Check 2: Sin credenciales
grep -E "pk_|sk_|api_key|password" opencode.jsonc && echo "❌ ERROR" || echo "✅ OK"

# Check 3: No PRPs en root
ls PRPs/ 2>/dev/null && echo "❌ ERROR" || echo "✅ OK"

# Check 4: framework-guardian
python core/scripts/framework-guardian.py --timing pre-release
```

### Paso 4: Commit y Push

```bash
cd PROD
git add -A
git commit -m "release: vX.Y.Z-prealpha"
git push upstream main
```

## Validaciones de Seguridad

### Pre-Sync (BASE)

- [ ] `opencode.jsonc.CLEAN-PROD` existe
- [ ] `README-simple.md` actualizado
- [ ] `VERSION` coincide con CHANGELOG

### Post-Sync (PROD)

- [ ] `opencode.jsonc` sin credenciales
- [ ] `README.md` es user-friendly
- [ ] No archivos de backup (`*.backup-*`)
- [ ] No scripts de test (`test_*.py`)
- [ ] No docs internos (`backlog.md`, etc.)
- [ ] No PRPs en root
- [ ] `framework-guardian` pasa todos los checks

## Archivos Excluidos de PROD

### Directorios Ignorados

| Directorio | Razón |
|------------|-------|
| `PRPs/` | Documentación interna |
| `.opencode/plans/` | Planes de desarrollo |
| `workspaces/` | Datos del usuario |
| `core/.context/sessions/` | Sesiones privadas |
| `core/.context/codebase/` | Codebase personal |
| `vitals/` | Backups históricos |

### Archivos Ignorados

| Archivo | Razón |
|---------|-------|
| `opencode.jsonc` (original) | Tiene credenciales |
| `backlog.md` | Doc interno |
| `backlog.view.md` | Doc interno |
| `AGENT-CONFIGURATION.md` | Config interna |
| `RELEASE-CHECKLIST.md` | Proceso interno |
| `VITALS-*.md` | Herramientas internas |
| `SYNC-PROTOCOL.md` | Doc interno |
| `test_*.py` | Tests |
| `sync-*.sh/bat` | Scripts internos |

## Herramientas y Recursos

### Scripts
- `core/scripts/sync-prealpha.py`: Sync entre entornos
- `core/scripts/framework-guardian.py`: Validación de seguridad
- `core/scripts/validate-public-release.py`: Validador específico

### Configuración
- `config/framework.yaml`: Configuración de enforcement
- `.gitignore`: Exclusiones de git

### Documentación
- [SYNC-PROTOCOL.md](../SYNC-PROTOCOL.md) - Flujo completo de sync
- [RELEASE-CHECKLIST.md](../RELEASE-CHECKLIST.md) - Checklist de release

## Ejemplos Prácticos

### Ejemplo 1: Sync Exitoso

```bash
cd BASE

# 1. Preparar
echo "0.2.0-prealpha" > VERSION
python core/scripts/version-updater.py

# 2. Sync
python core/scripts/sync-prealpha.py --mode=prod

# 3. Validar
cd PROD
python core/scripts/framework-guardian.py --timing pre-release
# [✓] All checks passed

# 4. Push
git commit -m "release: v0.2.0-prealpha"
git push upstream main
```

### Ejemplo 2: Validación Fallida (Credenciales)

```bash
cd PROD
python core/scripts/framework-guardian.py --timing pre-release

# [CORE-007] Release Sanitization
#   [✗] Credentials found in opencode.jsonc
#   [✓] No PRPs in release target
#   FAILED: Credentials detected!

# Solución: Verificar CLEAN-PROD
cat opencode.jsonc.CLEAN-PROD | grep -E "pk_|sk_"
# Si encuentra, editar y re-sync
```

### Ejemplo 3: Hotfix de Emergencia

```bash
# Si necesitas fix urgente y no tienes acceso a BASE:
git clone https://github.com/.../PreAlpha.git
cd PreAlpha
# Hacer fix
git commit -m "fix: descripción"
git push

# Luego sincronizar a BASE cuando puedas
cd BASE
git fetch upstream
git checkout upstream/main -- [archivos-modificados]
```

## Archivos Críticos PROTEGIDOS

Los siguientes archivos NUNCA deben eliminarse de PROD:

| Archivo | Razón |
|---------|-------|
| `AGENTS.md` | Punto de entrada universal para cualquier CLI |
| `VERSION` | Fuente de verdad de versión |
| `README.md` | Documentación principal usuario |
| `docs/core/PRP-*.md` | Documentación CORE pública (8 archivos) |
| `core/.context/knowledge/skills-index.json` | Índice de skills |
| `core/.context/knowledge/agents-index.json` | Índice de agentes |

## Bug del Path "./" - CRÍTICO

**PROBLEMA**: `Path.relative_to()` retorna `"."` para archivos en directorio raíz.

**IMPACTO**: Todos los archivos en root se marcan como eliminados durante sync.

**SOLUCIÓN**: Normalizar siempre después de obtener path relativo:

```python
rel_path = str(path.relative_to(source)).replace("./", "")
if rel_path == ".":
    rel_path = os.path.basename(path)
```

## Validación y Verificación

- [ ] ¿`opencode.jsonc.CLEAN-PROD` existe en BASE?
- [ ] ¿El sync usó el archivo CLEAN?
- [ ] ¿No hay credenciales en archivos de PROD?
- [ ] ¿`framework-guardian` pasa todos los checks?
- [ ] ¿README.md es user-friendly (no técnico)?
- [ ] ¿No hay archivos de backup o tests?
- [ ] ¿Archivos críticos presentes en PROD? (AGENTS.md, VERSION, README.md)

## Referencias

- [AGENTS.md](../../AGENTS.md) - Router principal
- [SYNC-PROTOCOL.md](../SYNC-PROTOCOL.md) - Documentación completa de sync
- [RELEASE-CHECKLIST.md](../RELEASE-CHECKLIST.md) - Checklist detallado
- [Framework Guardian](../../core/scripts/framework-guardian.py) - Validador

## Changelog

### v0.2.0-prealpha (2026-03-11)
- Versión inicial simplificada para release público
- Sanitizado: eliminados datos de desarrollo interno
- Agregado: ejemplos de validación fallida y éxito
- Agregado: hotfix de emergencia
