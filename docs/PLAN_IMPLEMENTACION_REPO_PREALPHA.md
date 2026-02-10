# Plan de Implementacion/Ejecucion — PreAlpha

> Fecha: 2026-02-10
> Owner GitHub: `n30j0su3`
> Repo legacy protegido: `n30j0su3/Model-Agnostic-AI-Personal-Assistant-Framework` (no reemplazar)

## Objetivos
1. Crear un repositorio remoto nuevo para este proyecto PreAlpha.
2. Asegurar que `pa.bat` muestre la version correcta del PreAlpha.
3. Asegurar que la opcion `4. Buscar Actualizaciones` consulte el repo remoto nuevo.

## Decisiones Aprobadas
- Se versiona contexto vital del framework: `core/.context/profile.md`, `core/.context/sessions/`, `core/.context/codebase/`, `core/.context/backups/` y `.opencode/`.
- Se mantiene sanitizacion de secretos reales (tokens, claves, `.env`, `env_vars.json`).
- Se crea repo nuevo sin tocar el repo legacy.

## Fase 1 — Seguridad y Sanitizacion
- Ajustar `.gitignore` para no excluir el contexto vital del framework.
- Mantener exclusiones de datos sensibles (`core/.context/env_vars.json`, `.env`, llaves, artefactos temporales).
- Ejecutar revision de patrones de secretos antes del primer push.

## Fase 2 — Repo Remoto Nuevo
- Crear repo: `n30j0su3/Model-Agnostic-AI-Personal-Assistant-Framework-PreAlpha`.
- Inicializar git local, configurar `origin` al repo nuevo y hacer primer push.
- Verificar `git remote -v` antes de subir.

## Fase 3 — Version Correcta en `pa.bat`
- Usar `VERSION` como fuente unica de version runtime.
- Corregir banner para que no use versiones legacy hardcodeadas.
- Alinear output visible a `0.1.0-alpha`.

## Fase 4 — Actualizaciones (Opcion 4)
- Corregir `core/scripts/update.py` para resolver correctamente el root del repo.
- Soportar versiones semver con sufijo pre-release (`0.1.0-alpha`).
- Apuntar fallback remoto al repo nuevo de PreAlpha.
- Diferenciar estados: actualizado, update disponible, error de verificacion.

## Fase 5 — Validacion
- `pa.bat` muestra `0.1.0-alpha`.
- Opcion 4 reporta correctamente:
  - actualizado,
  - update disponible,
  - error real de conectividad/config.
- El repo nuevo contiene el proyecto sin secretos.

## Entregables
- Cambios en `.gitignore`, `config/branding.txt`, `core/scripts/pa.py`, `core/scripts/update.py`.
- Repo remoto nuevo creado y enlazado.
- Primer push completo del PreAlpha.
