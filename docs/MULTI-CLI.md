# Multi-CLI Support - FreakingJSON-PA Framework

> Soporte nativo para múltiples instancias CLI trabajando simultáneamente en el mismo proyecto.

## Índice

1. [Visión General](#visión-general)
2. [Arquitectura](#arquitectura)
3. [Uso Básico](#uso-básico)
4. [API del Coordinador](#api-del-coordinador)
5. [Eventos y Notificaciones](#eventos-y-notificaciones)
6. [Manejo de Conflictos](#manejo-de-conflictos)
7. [Best Practices](#best-practices)
8. [Troubleshooting](#troubleshooting)

---

## Visión General

El sistema **Multi-CLI** permite ejecutar múltiples instancias de asistentes AI (GPT-4, Claude, Gemini, etc.) simultáneamente en el mismo proyecto FreakingJSON-PA, coordinando automáticamente:

- ✅ Acceso a archivos compartidos (sesiones, recordatorios, código)
- ✅ Sincronización en tiempo real entre CLIs
- ✅ Detección de conflictos y prevención de pérdida de datos
- ✅ Notificaciones cuando otra CLI modifica archivos
- ✅ Limpieza automática de instancias muertas

### ¿Por qué Multi-CLI?

- **Trabajo paralelo**: Usar GPT-4 para código y Claude para documentación
- **Testing multi-modelo**: Comparar respuestas de diferentes modelos
- **Alta disponibilidad**: Fallback entre instancias
- **Productividad**: Dividir tareas complejas entre múltiples agentes

---

## Arquitectura

```
┌─────────────────────────────────────────────────────────────┐
│                     Multi-CLI Architecture                   │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐     │
│  │   CLI-001    │   │   CLI-002    │   │   CLI-003    │     │
│  │   (GPT-4)    │   │   (Claude)   │   │  (Gemini)    │     │
│  └──────┬───────┘   └──────┬───────┘   └──────┬───────┘     │
│         │                  │                  │             │
│         └──────────────────┼──────────────────┘             │
│                            │                                │
│              ┌─────────────┴─────────────┐                  │
│              │   MultiCLICoordinator     │                  │
│              │   (core/scripts/...)      │                  │
│              └─────────────┬─────────────┘                  │
│                            │                                │
│         ┌──────────────────┼──────────────────┐             │
│         ▼                  ▼                  ▼             │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐     │
│  │ File Locks   │   │Event Bridge  │   │ Heartbeat    │     │
│  │ (.locks/)    │   │(.events/)    │   │ (.instances/)│     │
│  └──────────────┘   └──────────────┘   └──────────────┘     │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Componentes

| Componente | Archivo | Propósito |
|------------|---------|-----------|
| **Coordinator** | `multi_cli_coordinator.py` | Orquestador principal |
| **File Lock** | `file_lock.py` | Locks distribuidos cross-platform |
| **Event Bridge** | `event_bridge.py` | Sistema pub/sub file-based |
| **Session Start** | `session-start.py` | Integración en inicio de sesión |

### Estructura de Archivos

```
core/.context/sessions/
├── 2026-02-25.md              # Sesión principal (compartida)
├── .instances/                # Registry de CLIs
│   ├── cli-abc123.json       # Metadata CLI-1
│   └── cli-def456.json       # Metadata CLI-2
├── .locks/                    # Locks activos
│   ├── 2026-02-25.md.lock
│   └── src/main.py.lock
├── .events/                   # Event log append-only
│   └── 2026-02-25.events
└── .conflicts/                # Archivos de conflicto
    └── 2026-02-25-143022.md
```

---

## Uso Básico

### 1. Inicio Automático (Recomendado)

Al ejecutar `session-start.py`, el coordinador Multi-CLI se inicializa automáticamente:

```bash
python core/scripts/session-start.py
```

**Salida esperada:**
```
============================================================
[LAUNCH] ¡SECUENCIA DE DÍA INICIADA!
============================================================

  [DATE] 2026-02-25 | [TIME] 14:32

[Multi-CLI] ⚡ Instancias Activas:
   • cli-abc123... (GPT-4)
   • cli-def456... (Claude)

...
```

### 2. Uso Programático

```python
from core.scripts.multi_cli_coordinator import MultiCLICoordinator

# Inicializar
coord = MultiCLICoordinator(model="GPT-4")
coord.start()

# Editar archivo protegido
try:
    with coord.lock_file("recordatorios.md", timeout=5.0):
        # Editar archivo de forma segura
        with open("recordatorios.md", "a") as f:
            f.write("\n- [ ] Nueva tarea desde GPT-4")
    
    # Notificar cambio a otras CLIs
    coord.notify_file_change("recordatorios.md", "added task")
    
except LockTimeoutError:
    print("Otra CLI está editando este archivo")

# Al finalizar
coord.shutdown()
```

### 3. Context Manager (Recomendado)

```python
from core.scripts.multi_cli_coordinator import MultiCLICoordinator

with MultiCLICoordinator(model="Claude") as coord:
    # Coordinator automáticamente hace start() y shutdown()
    
    with coord.lock_file("src/main.py"):
        # Editar código
        pass
```

---

## API del Coordinador

### Clase: `MultiCLICoordinator`

#### Constructor

```python
MultiCLICoordinator(
    model: str = "unknown",           # Nombre del modelo/CLI
    session_date: str = None,        # Fecha de sesión (default: hoy)
    instance_id: str = None          # ID específico (auto-generado)
)
```

#### Métodos Principales

| Método | Descripción |
|--------|-------------|
| `start()` | Inicia el coordinador y registra la instancia |
| `shutdown()` | Detiene el coordinador y libera recursos |
| `lock_file(path, timeout)` | Context manager para lockear archivo |
| `notify_file_change(path, desc)` | Notifica cambio a otras CLIs |
| `get_active_instances()` | Lista todas las instancias activas |
| `get_other_active_instances()` | Lista instancias excepto la actual |

#### Propiedades

```python
coordinator.instance_id  # ID único de esta instancia
coordinator.model        # Modelo configurado
coordinator.session_date # Fecha de sesión
```

---

## Eventos y Notificaciones

### Tipos de Eventos

```python
from core.scripts.event_bridge import EventType

EventType.INSTANCE_JOINED       # Nueva CLI conectada
EventType.INSTANCE_LEFT         # CLI desconectada
EventType.INSTANCE_HEARTBEAT    # Heartbeat periódico
EventType.FILE_MODIFIED         # Archivo modificado
EventType.FILE_LOCKED           # Archivo lockeado
EventType.FILE_UNLOCKED         # Archivo deslockeado
EventType.FILE_CONFLICT         # Conflicto detectado
```

### Suscribirse a Eventos

```python
def on_file_modified(event):
    print(f"Archivo {event.data['file']} modificado por {event.source}")

coord.event_bridge.subscribe(EventType.FILE_MODIFIED, on_file_modified)
```

### Notificaciones en Consola

El coordinador automáticamente muestra notificaciones:

```
[Multi-CLI] ⚡ Nueva CLI conectada: cli-abc123 (GPT-4)
[Sync] 📄 recordatorios.md actualizado por cli-abc123
[Sync] 🔒 src/main.py lockeado por cli-def456
[Conflict] ⚠️ CONFLICTO en session.md. Instancias: cli-abc123, cli-def456
```

---

## Manejo de Conflictos

### Detección Automática

El sistema detecta conflictos cuando:
- Dos CLIs intentan lockear el mismo archivo simultáneamente
- Una CLI modifica un archivo mientras otra lo tiene lockeado
- Dos CLIs escriben en la misma sección de un archivo compartido

### Estrategia de Resolución

1. **Locks obligatorios**: Antes de editar, se debe adquirir el lock
2. **Timeout**: Si no se puede adquirir, se muestra quién tiene el lock
3. **Auto-merge**: Para sesiones, se hace merge por secciones
4. **Conflict markers**: Para código, se crean archivos `.conflict`

### Ejemplo de Conflicto

```python
# CLI-1 tiene el lock
try:
    with coord.lock_file("src/main.py", timeout=5.0):
        # editar
        pass
except LockTimeoutError as e:
    # Mostrará: "No se pudo adquirir lock (owned by cli-abc123)"
    print(f"Esperando: {e}")
```

---

## Best Practices

### ✅ Hacer

1. **Siempre usar locks** antes de editar archivos compartidos
2. **Notificar cambios** después de editar: `coord.notify_file_change()`
3. **Mantener locks cortos** - adquirir, editar, liberar rápidamente
4. **Verificar instancias activas** antes de operaciones críticas
5. **Usar context managers** para garantizar liberación de locks

### ❌ Evitar

1. **No mantener locks por mucho tiempo** (bloqueas a otras CLIs)
2. **No ignorar notificaciones de conflicto**
3. **No editar archivos sin coordinador iniciado**
4. **No forzar locks** (break lock) a menos que sea necesario

### Patrones Recomendados

```python
# ✅ BUENO: Lock corto y específico
with coord.lock_file("file.md", timeout=5.0):
    with open("file.md", "a") as f:
        f.write("cambio\n")
coord.notify_file_change("file.md", "added line")

# ❌ MALO: Lock largo
with coord.lock_file("file.md"):  # Sin timeout específico
    time.sleep(60)  # Bloqueando por 1 minuto!
    # ... editar ...
```

---

## Troubleshooting

### Problema: "No se pudo adquirir lock"

**Causa**: Otra CLI tiene el archivo lockeado.

**Solución**:
```bash
# Ver quién tiene el lock
python core/scripts/file_lock.py archivo.txt --action check

# Esperar o forzar liberación (con precaución)
python core/scripts/file_lock.py archivo.txt --action force-release
```

### Problema: Instancia aparece como "zombie"

**Causa**: El proceso murió sin hacer shutdown limpio.

**Solución**:
```bash
# Cleanup manual
python core/scripts/multi_cli_coordinator.py --action cleanup

# O automático (se hace cada 60 segundos)
```

### Problema: Eventos no llegan en tiempo real

**Causa**: Polling interval o archivo de eventos corrupto.

**Solución**:
```bash
# Verificar archivo de eventos
ls -la core/.context/sessions/.events/

# Limpiar si es necesario
rm core/.context/sessions/.events/2026-02-25.events
```

### Problema: Muchos archivos de conflicto

**Causa**: Dos CLIs editando la misma sección frecuentemente.

**Solución**:
- Usar secciones separadas en sesiones
- Coordinar quién edita qué
- Usar locks con timeout más largo para edición colaborativa

---

## Comandos de Utilidad

```bash
# Ver estado de instancias
python core/scripts/multi_cli_coordinator.py --action status

# Test de locking
python core/scripts/multi_cli_coordinator.py --action test-lock

# Cleanup de instancias muertas
python core/scripts/multi_cli_coordinator.py --action cleanup

# Ver locks activos
ls -la core/.context/sessions/.locks/

# Monitorear eventos en tiempo real
python core/scripts/event_bridge.py --instance-id watcher --action listen
```

---

## Configuración Avanzada

### Variables de Entorno

```bash
# Identificar modelo automáticamente
export PA_MODEL="GPT-4"

# Cambiar intervalo de heartbeat (segundos)
export PA_HEARTBEAT_INTERVAL=30

# Cambiar threshold de stale (segundos)
export PA_STALE_THRESHOLD=120
```

### Configuración por Instancia

En `core/.context/sessions/.instances/cli-xxx.json`:

```json
{
  "instance_id": "cli-abc123",
  "pid": 12345,
  "model": "GPT-4",
  "start_time": "2026-02-25T14:30:00",
  "last_heartbeat": "2026-02-25T14:35:00",
  "status": "active",
  "open_files": ["recordatorios.md", "src/main.py"]
}
```

---

## Referencias

- **Coordinador**: `core/scripts/multi_cli_coordinator.py`
- **File Lock**: `core/scripts/file_lock.py`
- **Event Bridge**: `core/scripts/event_bridge.py`
- **Session Start**: `core/scripts/session-start.py`

---

## Changelog

### v2.0.0 (2026-02-25)
- ✅ Sistema Multi-CLI completo
- ✅ Locks distribuidos cross-platform
- ✅ Eventos en tiempo real
- ✅ Detección automática de instancias
- ✅ Manejo de conflictos

---

> *"True knowledge transcends to the public."*
> 
> *— FreakingJSON Framework*
