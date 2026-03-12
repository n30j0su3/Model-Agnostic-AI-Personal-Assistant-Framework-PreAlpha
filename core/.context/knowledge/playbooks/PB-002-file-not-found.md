---
id: PB-002
category: file_operations
severity: high
frequency: frequent
auto_generated: false
created: 2026-03-11
last_used: null
success_rate: null
---

# PB-002: Archivo No Encontrado y Permisos

> **Playbook para FileNotFoundError, PermissionError y problemas de rutas.**

---

## Síntomas

### Mensajes Típicos

```
FileNotFoundError: [Errno 2] No such file or directory: 'path/to/file'
```

```
PermissionError: [Errno 13] Permission denied: 'path/to/file'
```

```
FileNotFoundError: [Errno 2] No such file or directory: 'path/to/file' (creating directory)
```

### Cuándo Ocurre

- Lectura/escritura de archivos con rutas incorrectas
- Directorios padre inexistentes al crear archivos
- Permisos insuficientes en Windows/Linux
- Rutas relativas vs absolutas confusas
- Archivos bloqueados por otros procesos

---

## Causa Raíz

| Error | Causa Principal |
|-------|-----------------|
| `FileNotFoundError` | Ruta no existe, typo en nombre, directorio padre falta |
| `PermissionError` | Sin permisos de escritura/lectura, archivo en uso |
| `IsADirectoryError` | Se esperaba archivo, se encontró directorio |

### Windows Específico

- Rutas con espacios sin comillas
- Caracteres no permitidos (`:`, `*`, `?`, `"`, `<`, `>`, `|`)
- Archivos ocultos o de sistema
- Antivirus bloqueando acceso

---

## Soluciones

### Inmediata (Quick Fix)

**Verificar existencia antes de operar:**

```python
from pathlib import Path

file_path = Path("path/to/file")

if not file_path.exists():
    raise FileNotFoundError(f"Archivo no encontrado: {file_path}")

if file_path.is_dir():
    raise IsADirectoryError(f"Se esperaba archivo, es directorio: {file_path}")
```

**Crear directorios padre automáticamente:**

```python
from pathlib import Path

file_path = Path("path/to/new/file.txt")
file_path.parent.mkdir(parents=True, exist_ok=True)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
```

**Manejo de permisos:**

```python
import os
from pathlib import Path

file_path = Path("path/to/file")

try:
    with open(file_path, 'r') as f:
        content = f.read()
except PermissionError:
    # Verificar permisos
    print(f"Permisos actuales: {oct(file_path.stat().st_mode)[-3:]}")
    # O ejecutar con privilegios elevados
    raise
```

### Permanente

**Usar Path en lugar de strings:**

```python
from pathlib import Path

# Configurar rutas base
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
CONFIG_FILE = DATA_DIR / "config.json"

# Crear estructura
DATA_DIR.mkdir(parents=True, exist_ok=True)
```

**Función robusta de lectura:**

```python
from pathlib import Path
from typing import Optional

def safe_read(file_path: str | Path, default: Optional[str] = None) -> str:
    path = Path(file_path)
    
    if not path.exists():
        if default is not None:
            return default
        raise FileNotFoundError(f"Archivo no encontrado: {path}")
    
    if not path.is_file():
        raise IsADirectoryError(f"Se esperaba archivo: {path}")
    
    try:
        return path.read_text(encoding='utf-8')
    except PermissionError as e:
        raise PermissionError(f"Sin permisos para leer: {path}") from e
```

**Función robusta de escritura:**

```python
from pathlib import Path

def safe_write(file_path: str | Path, content: str, overwrite: bool = False) -> None:
    path = Path(file_path)
    
    if path.exists() and not overwrite:
        raise FileExistsError(f"Archivo ya existe: {path}")
    
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding='utf-8')
```

### Windows Específico

**Manejo de archivos bloqueados:**

```python
import time
from pathlib import Path

def retry_operation(file_path: Path, operation: callable, max_retries: int = 3):
    for attempt in range(max_retries):
        try:
            return operation(file_path)
        except PermissionError:
            if attempt < max_retries - 1:
                time.sleep(0.5 * (attempt + 1))
                continue
            raise
```

---

## Prevención

### Usar pathlib Siempre

```python
# ❌ Mal - strings y os.path
import os
file_path = os.path.join('data', 'file.txt')

# ✅ Bien - pathlib
from pathlib import Path
file_path = Path('data') / 'file.txt'
```

### Validar Entrada de Usuario

```python
from pathlib import Path

def validate_path(base_dir: Path, user_path: str) -> Path:
    full_path = (base_dir / user_path).resolve()
    
    if not str(full_path).startswith(str(base_dir.resolve())):
        raise ValueError(f"Path traversal detectado: {user_path}")
    
    return full_path
```

### Estructura de Proyecto Predecible

```python
from pathlib import Path

class ProjectPaths:
    ROOT = Path(__file__).parent.parent
    DATA = ROOT / "data"
    CONFIG = ROOT / "config"
    LOGS = ROOT / "logs"
    TEMP = ROOT / "temp"
    
    @classmethod
    def init(cls):
        for path in [cls.DATA, cls.CONFIG, cls.LOGS, cls.TEMP]:
            path.mkdir(parents=True, exist_ok=True)

ProjectPaths.init()
```

---

## Referencias

- [pathlib documentation](https://docs.python.org/3/library/pathlib.html)
- [PRP-003: Antifragile Error Recovery](../PRPs/PRP-003-CORE-Antifragile-Errors.md)
- [os.path vs pathlib](https://realpython.com/python-pathlib/)

---

## Historial de Uso

| Fecha | Contexto | Resultado |
|-------|----------|-----------|
| 2026-03-11 | Creación del playbook | ✅ Documentado |

---

> *"Usa pathlib. Resolve tus rutas. Crea directorios padres."*