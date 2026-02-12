# Python Standards (Cross-Platform)

Estándares generales para scripts Python compatibles con Windows, macOS y Linux.

---

## File Encoding

**Siempre usar UTF-8** para lectura/escritura de archivos.

- **Incorrecto**: `open(file, 'r')` — usa encoding del sistema
- **Correcto**: `open(file, 'r', encoding='utf-8')`

```python
# Siempre especificar encoding
with open('data.txt', 'r', encoding='utf-8') as f:
    content = f.read()

# Para escritura igualmente
with open('output.txt', 'w', encoding='utf-8') as f:
    f.write(content)
```

---

## Path Handling

**Usar `pathlib.Path`** en lugar de concatenación de strings.

- **Incorrecto**: `path + "/" + filename` o `path + "\\" + filename`
- **Correcto**: `path / filename`

```python
from pathlib import Path

# Cross-platform path construction
base_dir = Path("/home/user")  # o Path("C:\\Users")
config_file = base_dir / "config" / "app.json"

# Path operations
config_file.exists()
config_file.parent.mkdir(parents=True, exist_ok=True)
```

---

## Console Output

**Gestionar encoding de stdout** para evitar errores en Windows.

```python
import sys
import platform

# Configurar UTF-8 en stdout al inicio del script
if platform.system() == "Windows":
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# O usar SafePrinter para emojis cross-platform
from detect_env import SafePrinter
printer = SafePrinter()
printer.success("Operación completada")
```

---

## Imports

**Orden estándar**: stdlib → third-party → local.

```python
#!/usr/bin/env python3
"""Docstring del módulo."""

# 1. Standard library
import os
import sys
from pathlib import Path
from typing import Dict, List

# 2. Third-party (si hay)
# import requests

# 3. Local modules
# from .utils import helper
```

**Reglas**:
- Usar imports absolutos cuando sea posible
- Agrupar imports relacionados
- Evitar `from module import *`

---

## Error Handling

**Usar excepciones específicas** y proporcionar mensajes útiles.

```python
from pathlib import Path

def process_file(file_path: str) -> str:
    """Procesa un archivo y retorna su contenido."""
    path = Path(file_path)
    
    if not path.exists():
        raise FileNotFoundError(f"Archivo no encontrado: {file_path}")
    
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    except UnicodeDecodeError as e:
        raise ValueError(f"Archivo no es UTF-8 válido: {e}")
    except PermissionError:
        raise PermissionError(f"Sin permisos para leer: {file_path}")
```

**Principios**:
- Capturar excepciones específicas, no `except Exception`
- Usar context managers (`with`) para recursos
- Propagar errores con contexto adicional

---

## Scripts vs Libraries

| Aspecto | CLI Scripts | Library Modules |
|---------|-------------|-----------------|
| Emojis | Permitidos (con detección) | Prohibidos |
| Print | Para output de usuario | Nunca usar |
| Shebang | `#!/usr/bin/env python3` | No necesario |
| `if __name__ == "__main__"` | Sí | No |
| Excepciones | Capturar y mostrar | Propagar |

**Ver referencias específicas**:
- `cli_standards.md` — Scripts interactivos
- `lib_standards.md` — Módulos reutilizables

---

## Validación

Usar `check_script.py` para validar código:

```bash
# Validar un archivo
python check_script.py mi_script.py

# Ver sugerencias de corrección
python check_script.py mi_script.py --fix-suggestions

# Validar directorio recursivamente
python check_script.py . --recursive
```

---

## Recursos

- `detect_env.py` — Detección de soporte de emojis
- `check_script.py` — Validador de estándares
- `fix_script.py` — Corrector automático
