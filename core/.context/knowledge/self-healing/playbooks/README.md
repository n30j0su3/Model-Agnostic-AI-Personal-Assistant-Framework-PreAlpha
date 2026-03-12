# Recovery Playbooks

> Soluciones documentadas para errores recurrentes. Cuando un error ocurre, el framework busca aquí la solución.

## Uso

1. **Detección**: Error ocurre durante sesión
2. **Búsqueda**: Buscar playbook por `error_type`
3. **Aplicación**: Seguir pasos de recovery
4. **Verificación**: Confirmar que el error se resolvió

## Playbooks Disponibles

| Playbook | Error Type | Causa Común |
|----------|------------|-------------|
| `encoding-error.md` | UnicodeEncodeError | Windows cp1252 vs UTF-8 |
| `file-not-found.md` | FileNotFoundError | Archivo no creado |
| `permission-denied.md` | PermissionError | Archivo bloqueado |

## Crear Nuevo Playbook

```markdown
# {error-type}.md

## Síntomas
- [Descripción de lo que se observa]

## Causa Raíz
- [Por qué ocurre]

## Solución Inmediata
1. [Paso 1]
2. [Paso 2]

## Prevención
- [Cómo evitar que vuelva a ocurrir]

## Metadata
- Creado: YYYY-MM-DD
- Sesión: session-id
- Ocurrencias: N
```