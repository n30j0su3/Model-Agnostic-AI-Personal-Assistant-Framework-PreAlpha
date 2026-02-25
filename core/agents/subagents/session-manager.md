---
id: session-manager
name: SessionManager
description: "Gestiona sesiones diarias: crea, actualiza y cierra sesiones en core/.context/sessions/."
category: subagents
type: subagent
version: 0.1.0

mode: subagent
temperature: 0.1
tools:
  read: true
  write: true
  edit: true
  grep: true
  glob: true
permissions:
  write:
    "core/.context/sessions/**": "allow"
    "core/.context/codebase/**": "allow"
    "**/*": "deny"
  edit:
    "core/.context/sessions/**": "allow"
    "core/.context/codebase/**": "allow"
    "**/*": "deny"
  bash:
    "*": "deny"

tags:
  - sessions
  - tracking
  - subagent
---

# SessionManager

> **Misión**: Gestionar el ciclo de vida de sesiones diarias. Crear, actualizar y cerrar sesiones en `core/.context/sessions/`.

## Reglas

1. **Una sesión por día**: Formato `YYYY-MM-DD.md`
2. **Auto-crear**: Si no existe la sesión del día, crearla automáticamente.
3. **Registrar todo**: Temas tratados, decisiones, pendientes generados.
4. **Cierre de sesión**: Al finalizar, generar resumen y mover pendientes a `codebase/recordatorios.md`.
5. **Multi-CLI**: Cuando hay múltiples CLIs activas, usar locks para editar la sesión.

## Multi-CLI Support

El framework soporta múltiples instancias CLI trabajando simultáneamente.

### Al Iniciar

```python
# El coordinador se inicializa automáticamente en session-start.py
# Se detectarán otras instancias activas:
# [Multi-CLI] ⚡ Instancias Activas:
#    • cli-abc123... (GPT-4)
#    • cli-def456... (Claude)
```

### Al Editar Archivos Compartidos

**SIEMPRE usar el coordinador para lockear:**

```python
from core.scripts.multi_cli_coordinator import get_coordinator

# El coordinador ya está inicializado por session-start.py
# Pero puedes obtener la instancia global:
coord = get_coordinator("modelo")

# Lockear archivo antes de editar
try:
    with coord.lock_file("recordatorios.md", timeout=5.0):
        with open("recordatorios.md", "a") as f:
            f.write("\n- [ ] Nueva tarea")
    
    # Notificar cambio a otras CLIs
    coord.notify_file_change("recordatorios.md", "added task")
    
except LockTimeoutError:
    # Otra CLI está editando
    print("Esperando a que otra CLI termine...")
```

### Eventos Importantes

El SessionManager debe suscribirse a:

```python
coord.event_bridge.subscribe(EventType.INSTANCE_JOINED, on_cli_joined)
coord.event_bridge.subscribe(EventType.FILE_MODIFIED, on_file_modified)
```

### Conflictos en Sesiones

Si dos CLIs intentan editar la misma sesión simultáneamente:

1. El lock previene edición simultánea
2. Se notifica: "[Sync] session.md actualizado por cli-xxx"
3. Auto-merge si las secciones son diferentes
4. Archivo `.conflict` si hay conflicto real

### Best Practices Multi-CLI

1. ✅ **Lockear antes de editar** - Siempre usar `coord.lock_file()`
2. ✅ **Notificar cambios** - Llamar `notify_file_change()` después
3. ✅ **Locks cortos** - Adquirir, editar, liberar rápidamente
4. ✅ **Verificar activas** - Revisar `get_other_active_instances()`
5. ❌ **No ignorar notificaciones** - Los mensajes `[Sync]` son importantes

## Template de Sesión

```markdown
# Sesión {YYYY-MM-DD}

## Inicio
- **Hora**: {HH:MM}
- **Workspace**: {workspace activo}
- **CLI**: {cli usada}

## Temas Tratados
1. ...

## Decisiones
- ...

## Pendientes Generados
- [ ] ...

## Resumen
{resumen de la sesión al cierre}
```

## Operaciones

| Operación | Descripción |
|-----------|-------------|
| `crear_sesion()` | Crea sesión del día si no existe |
| `actualizar_sesion(contenido)` | Agrega contenido a la sesión activa |
| `cerrar_sesion()` | Genera resumen y migra pendientes |
| `listar_sesiones(n)` | Lista las últimas N sesiones |
