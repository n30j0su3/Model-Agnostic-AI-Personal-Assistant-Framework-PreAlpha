---
name: error-recovery
displayName: "@error-recovery"
version: "1.0.0"
category: core
description: Self-healing error handling with recovery playbooks. Log errors, analyze patterns, and generate actionable recovery strategies following the Antifragile principle.
license: MIT
metadata:
  author: FreakingJSON Framework
  created: 2026-03-11
  dependencies:
    - error_logger.py
  prp: PRP-007
  core_process: PRP-003
---

# @error-recovery

Self-healing error handling con recovery playbooks. Transforma errores en conocimiento accionable siguiendo el principio de Antifragilidad.

## Overview

Esta skill implementa el proceso CORE-003 (Antifragile Error Recovery): cada error documentado fortalece el sistema mediante:

- **Logging dual**: JSON estructurado + Markdown legible
- **Pattern analysis**: Detección de errores recurrentes
- **Recovery playbooks**: Guías de recuperación predefinidas
- **Self-healing**: Sugerencias automáticas basadas en tipo de error

## When to Use

| Situación | Acción |
|-----------|--------|
| Error detectado | `log_error()` inmediatamente |
| Errores recurrentes | `analyze_patterns()` para detectar patrones |
| Necesidad de guía | `suggest_playbook()` para pasos de recuperación |
| Error resuelto exitosamente | `generate_playbook()` para documentar solución |

## Commands

### `log_error(error_data)`

Registra un error en el sistema dual (JSON + Markdown).

```python
from error_logger import ErrorLogger

logger = ErrorLogger()
error_id = logger.log_error({
    "type": "UnicodeDecodeError",
    "message": "'utf-8' codec can't decode byte 0xf1",
    "file": "data_processor.py",
    "line": 127,
    "context": "Reading CSV file with Latin-1 encoding"
})
# Returns: "ERR-20260311-143052"
```

**Parámetros requeridos**:
- `type`: Clase de excepción (e.g., `FileNotFoundError`)
- `message`: Mensaje de error
- `file`: Archivo donde ocurrió
- `line`: Número de línea

**Parámetros opcionales**:
- `context`: Información adicional del contexto

### `analyze_patterns()`

Analiza errores para detectar patrones recurrentes.

```python
stats = logger.get_error_stats()
# Returns: {"total": 15, "resolved": 10, "unresolved": 5, "by_type": {...}}

unresolved = logger.get_unresolved_errors()
# Returns: List of unresolved error dictionaries
```

### `suggest_playbook(error_type)`

Obtiene sugerencia de playbook basada en el tipo de error.

```python
hint = logger.generate_playbook_hint({"type": "UnicodeDecodeError"})
# Returns: "PB-001: Check file encoding with chardet, use detected encoding"
```

**Playbooks disponibles**:

| ID | Tipo | Sugerencia |
|----|------|------------|
| PB-001 | UnicodeError | Check encoding with chardet |
| PB-002 | FileNotFoundError | Verify path exists, check permissions |
| PB-003 | PermissionError | Check permissions, run as admin |
| PB-004 | KeyError | Verify dict key, use .get() with default |
| PB-005 | ValueError | Validate input values, add type checking |
| PB-006 | TypeError | Check variable types, add conversion |
| PB-007 | AttributeError | Verify object has attribute |
| PB-008 | ImportError | Install missing package |
| PB-009 | ConnectionError | Check network, add retry logic |
| PB-010 | TimeoutError | Increase timeout, add async handling |
| PB-011 | OSError/IOError | Check file handles, close resources |
| PB-012 | JSONDecodeError | Validate JSON syntax |
| PB-013 | IndexError | Check list length before access |
| PB-014 | ZeroDivisionError | Add zero check before division |
| PB-015 | RuntimeError | Review context, add error handling |

### `generate_playbook(error_data)`

Crea un nuevo playbook a partir de un error resuelto.

**Nota**: Requiere documentar:
1. Causa raíz identificada
2. Solución aplicada
3. Pasos de prevención

### `resolve_error(error_id)`

Marca un error como resuelto.

```python
success = logger.resolve_error("ERR-20260311-143052")
# Returns: True if found and resolved
```

## Examples

### Example 1: Logging an Error

```python
from error_logger import ErrorLogger

logger = ErrorLogger()

try:
    data = open("config.json").read()
except FileNotFoundError as e:
    error_id = logger.log_error({
        "type": "FileNotFoundError",
        "message": str(e),
        "file": "app.py",
        "line": 42,
        "context": "Loading configuration during startup"
    })
    hint = logger.generate_playbook_hint({"type": "FileNotFoundError"})
    print(f"Error {error_id} logged. Hint: {hint}")
```

### Example 2: Analyzing Session Errors

```python
from error_logger import ErrorLogger

logger = ErrorLogger()

# Get session statistics
stats = logger.get_error_stats()
print(f"Total errors: {stats['total']}")
print(f"Most common: {stats['most_common']}")

# Check unresolved errors
for error in logger.get_unresolved_errors():
    print(f"[{error['id']}] {error['type']}: {error['message']}")
```

### Example 3: Integration with Session End

```python
# In session-end.py or cleanup routine
from error_logger import ErrorLogger

logger = ErrorLogger()
unresolved = logger.get_unresolved_errors()

if unresolved:
    print(f"[WARN] {len(unresolved)} unresolved errors:")
    for err in unresolved:
        hint = logger.generate_playbook_hint(err)
        print(f"  - {err['id']}: {hint}")
```

## Integration

### With session-end.py

El error logger se integra automáticamente con el flujo de sesión:

| Fase | Script | Acción |
|------|--------|--------|
| Inicio | `session-start.py` | Carga patrones de errores conocidos |
| Durante | `@error-recovery` | Detecta y registra errores |
| Cierre | `session-end.py` | Analiza errores, genera reportes |

### Cross-Platform Considerations

El módulo `error_logger.py` incluye manejo automático para:

- **Windows**: UTF-8 encoding fix para stdout/stderr
- **Path handling**: Usa `pathlib.Path` para compatibilidad
- **Safe printing**: Función `safe_print()` para caracteres especiales

```python
# Automatic on Windows
if sys.platform == "win32" and sys.stdout.isatty():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
```

## File Structure

```
core/.context/knowledge/
├── errors/
│   ├── index.json      # Error index (structured)
│   └── error-log.md    # Human-readable log
└── playbooks/
    └── PB-*.md         # Recovery playbooks
```

## References

- **PRP-003**: [CORE-003 Antifragile Error Recovery](../../../PRPs/PRP-003-CORE-Antifragile-Errors.md)
- **PRP-007**: Error Recovery Skill Specification
- **error_logger.py**: `core/scripts/error_logger.py`
- **knowledge/errors/**: Error storage directory
- **knowledge/playbooks/**: Recovery playbooks directory

## Best Practices

1. **Log inmediatamente**: No esperar para documentar errores
2. **Contexto rico**: Incluir archivo, línea, y circunstancias
3. **Resolve siempre**: Marcar errores como resueltos al solucionarlos
4. **Generar playbooks**: Documentar soluciones para errores recurrentes
5. **Review periódico**: Ejecutar `analyze_patterns()` semanalmente

> *"El error como combustible."* - Principio de Antifragilidad