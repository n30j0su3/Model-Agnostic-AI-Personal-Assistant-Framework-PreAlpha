---
title: "CORE-006: Version Governance"
version: "0.2.0-prealpha"
type: "process"
scope: "public"
prp: "PRP-008"
---

# CORE-006: Version Governance

## Principio Fundamental

**Una sola versión, múltiples fuentes, sincronización automática. Mantener consistencia de versión en todos los archivos del framework.**

## Descripción

El proceso CORE-006 establece un sistema de gobernanza de versiones donde existe una única fuente de verdad (archivo `VERSION`) que se sincroniza automáticamente a múltiples archivos del framework.

Este principio asegura:
- Una única versión en todo el framework
- Consistencia entre archivos
- Automatización del proceso de actualización
- Prevención de inconsistencias

## Objetivos

1. Mantener una única fuente de verdad para versión
2. Sincronizar versión automáticamente
3. Prevenir inconsistencias entre archivos
4. Facilitar releases consistentes

## Cuándo Aplicar

- **Antes de cualquier release**: Actualizar versión
- **Cambios significativos**: Bump de versión
- **Hotfixes**: Versión patch
- **Nuevas features**: Versión minor/major

## Flujo de Trabajo

### Paso 1: Actualizar Archivo VERSION

El archivo `VERSION` en la raíz es la **única fuente de verdad**:

```bash
echo "0.2.0-prealpha" > VERSION
```

### Paso 2: Ejecutar version-updater.py

El script sincroniza automáticamente a todos los archivos:

```bash
python core/scripts/version-updater.py
```

**Archivos actualizados**:
- `README.md`
- `AGENTS.md`
- `CHANGELOG.md`
- `ROADMAP.md`
- `GEMINI.md`
- `README-technical.md`
- `dashboard.html`
- `config/branding.txt`
- `core/scripts/pa.py`

### Paso 3: Actualizar CHANGELOG.md Manualmente

Agregar entrada para la nueva versión:

```markdown
## [0.2.0-prealpha] - 2026-03-11

### Added
- Nueva feature importante

### Changed
- Cambio significativo

### Fixed
- Bug corregido
```

### Paso 4: Validar Consistencia

Verificar que todos los archivos tienen la misma versión:

```bash
grep -r "v0.2.0-prealpha" . --include="*.md" --include="*.html" | head -10
```

## Estructura de Versionado

### Formato de Versión

```
MAJOR.MINOR.PATCH-prestage
```

**Ejemplos**:
- `0.1.0-prealpha`: Versión inicial
- `0.1.1-prealpha`: Hotfix
- `0.2.0-prealpha`: Nueva feature
- `1.0.0-prealpha`: Release estable (futuro)

### Significado

| Componente | Cuándo incrementar | Ejemplo |
|------------|-------------------|---------|
| **MAJOR** | Cambios breaking | 0.x.x → 1.x.x |
| **MINOR** | Nuevas features | x.1.x → x.2.x |
| **PATCH** | Bug fixes | x.x.1 → x.x.2 |
| **prealpha** | Estado de desarrollo | Siempre en pre-alpha |

## Herramientas y Recursos

### Scripts
- `core/scripts/version-updater.py`: Sincroniza versión a todos los archivos
- `core/scripts/framework-guardian.py`: Valida consistencia (CORE-006 check)

### Archivos a Versionar

| Archivo | Ubicación | Patrón de versión |
|---------|-----------|-------------------|
| VERSION | `/VERSION` | `0.2.0-prealpha` |
| README.md | `/README.md` | `v0.2.0-prealpha` |
| AGENTS.md | `/AGENTS.md` | `v0.2.0-prealpha` |
| CHANGELOG.md | `/CHANGELOG.md` | Sección `[0.2.0-prealpha]` |
| ROADMAP.md | `/ROADMAP.md` | `v0.2.0-prealpha` |
| GEMINI.md | `/GEMINI.md` | `v0.2.0-prealpha` |
| dashboard.html | `/dashboard.html` | `v0.2.0-prealpha` |
| pa.py | `core/scripts/pa.py` | En docstring/variable |

## Ejemplos Prácticos

### Ejemplo 1: Bump de Versión (Minor)

**Cambio**: Agregar nueva feature (Knowledge Framework)

```bash
# 1. Actualizar VERSION
echo "0.2.0-prealpha" > VERSION

# 2. Sincronizar
python core/scripts/version-updater.py

# 3. Actualizar CHANGELOG
# Agregar sección ## [0.2.0-prealpha]

# 4. Commit
git add VERSION README.md AGENTS.md ...
git commit -m "chore: bump version to v0.2.0-prealpha"
```

### Ejemplo 2: Hotfix (Patch)

**Cambio**: Corregir bug crítico

```bash
# 1. Actualizar VERSION
echo "0.1.9-prealpha" > VERSION

# 2. Sincronizar
python core/scripts/version-updater.py

# 3. Actualizar CHANGELOG
# Agregar ## [0.1.9-prealpha] con sección ### Fixed

# 4. Commit y tag
git add VERSION ...
git commit -m "fix: correct critical bug"
git tag -a v0.1.9-prealpha -m "Hotfix v0.1.9"
```

### Ejemplo 3: Validación Fallida

**Problema**: AGENTS.md tiene `v0.1.8`, README.md tiene `v0.1.9`

```bash
# Ejecutar framework-guardian
python core/scripts/framework-guardian.py --timing pre-release

# Output:
# [CORE-006] Version Governance
#   [✗] AGENTS.md: v0.1.8-prealpha
#   [✓] README.md: v0.1.9-prealpha
#   ERROR: Version mismatch detected!

# Solución:
python core/scripts/version-updater.py
```

## Checklist de Versionado

### Pre-Release

- [ ] Actualizar archivo `VERSION`
- [ ] Ejecutar `version-updater.py`
- [ ] Actualizar `CHANGELOG.md` manualmente
- [ ] Verificar consistencia con `framework-guardian.py`
- [ ] Commit con mensaje claro de versión

### Post-Release

- [ ] Crear tag git: `git tag -a vX.Y.Z-prealpha`
- [ ] Push del tag: `git push origin vX.Y.Z-prealpha`
- [ ] Verificar en GitHub que la versión es correcta

## Validación y Verificación

- [ ] ¿El archivo `VERSION` existe y es legible?
- [ ] ¿`version-updater.py` ejecutó sin errores?
- [ ] ¿CHANGELOG.md tiene entrada para la nueva versión?
- [ ] ¿Todos los archivos muestran la misma versión?
- [ ] ¿`framework-guardian.py` pasa el check CORE-006?

## Referencias

- [AGENTS.md](../../AGENTS.md) - Router principal (tiene versión)
- [CHANGELOG.md](../../CHANGELOG.md) - Historial de cambios
- [RELEASE-CHECKLIST.md](../RELEASE-CHECKLIST.md) - Checklist de release
- [SYNC-PROTOCOL.md](../SYNC-PROTOCOL.md) - Flujo de sincronización

## Changelog

### v0.2.0-prealpha (2026-03-11)
- Versión inicial simplificada para release público
- Sanitizado: eliminados datos de desarrollo interno
- Agregado: ejemplos prácticos de bump de versión
- Agregado: checklist pre/post-release
