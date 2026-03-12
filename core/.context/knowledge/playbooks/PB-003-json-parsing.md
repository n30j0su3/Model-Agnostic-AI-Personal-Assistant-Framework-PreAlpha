---
id: PB-003
category: encoding
severity: medium
frequency: frequent
auto_generated: false
created: 2026-03-11
last_used: null
success_rate: null
---

# PB-003: Errores de Parsing JSON

> **Playbook para JSONDecodeError, JSON malformado y problemas de encoding en JSON.**

---

## Síntomas

### Mensajes Típicos

```
JSONDecodeError: Expecting value: line 1 column 1 (char 0)
```

```
JSONDecodeError: Expecting property name enclosed in double quotes: line 5 column 10 (char 156)
```

```
JSONDecodeError: Extra data: line 10 column 1 (char 234)
```

```
JSONDecodeError: Invalid control character at: line 3 column 15 (char 67)
```

### Cuándo Ocurre

- Lectura de archivos JSON corruptos
- APIs que retornan JSON inválido
- JSON con BOM (Byte Order Mark)
- Encoding incorrecto (UTF-16 vs UTF-8)
- Caracteres de control sin escape
- Comillas simples en lugar de dobles
- Trailing commas
- Comentarios en JSON (no permitidos en spec)

---

## Causa Raíz

| Error | Causa Principal |
|-------|-----------------|
| `Expecting value: line 1 column 1` | Archivo vacío, BOM, encoding incorrecto |
| `Expecting property name enclosed in double quotes` | Comillas simples, sin comillas |
| `Extra data` | Múltiples objetos JSON sin array |
| `Invalid control character` | Saltos de línea literales en strings |
| `Unterminated string` | String sin cerrar, escape incorrecto |

### Encoding Issues

- BOM (`\ufeff`) al inicio del archivo
- UTF-16 BOM leído como UTF-8
- Archivos guardados con encoding diferente

---

## Soluciones

### Inmediata (Quick Fix)

**Validar y diagnosticar JSON:**

```python
import json
from pathlib import Path

def diagnose_json(file_path: str | Path) -> dict:
    path = Path(file_path)
    raw = path.read_bytes()
    
    issues = []
    
    # Check BOM
    if raw.startswith(b'\xef\xbb\xbf'):
        issues.append("UTF-8 BOM detectado")
        raw = raw[3:]
    elif raw.startswith(b'\xff\xfe'):
        issues.append("UTF-16 LE BOM detectado")
    elif raw.startswith(b'\xfe\xff'):
        issues.append("UTF-16 BE BOM detectado")
    
    # Try to parse
    try:
        data = json.loads(raw)
        return {"valid": True, "issues": issues, "data": data}
    except json.JSONDecodeError as e:
        issues.append(f"JSONDecodeError: {e.msg} at line {e.lineno}, column {e.colno}")
        return {"valid": False, "issues": issues, "error": e}
```

**Fix BOM y encoding:**

```python
import json
from pathlib import Path

def read_json_robust(file_path: str | Path) -> dict:
    path = Path(file_path)
    raw = path.read_bytes()
    
    # Remove BOM if present
    if raw.startswith(b'\xef\xbb\xbf'):
        raw = raw[3:]
    
    # Decode with fallback
    for encoding in ['utf-8', 'utf-8-sig', 'latin-1']:
        try:
            text = raw.decode(encoding)
            break
        except UnicodeDecodeError:
            continue
    else:
        raise UnicodeDecodeError(f"No se pudo decodificar {file_path}")
    
    return json.loads(text)
```

**Fix JSON malformado común:**

```python
import json
import re

def fix_common_json_issues(text: str) -> str:
    # Remove trailing commas before ] or }
    text = re.sub(r',\s*([}\]])', r'\1', text)
    
    # Fix single quotes to double quotes (simple cases)
    # WARNING: This is a heuristic, may break valid strings with quotes
    # text = text.replace("'", '"')
    
    # Remove comments (not JSON spec, but common in config files)
    text = re.sub(r'//.*$', '', text, flags=re.MULTILINE)
    text = re.sub(r'/\*.*?\*/', '', text, flags=re.DOTALL)
    
    return text
```

### Permanente

**Función robusta de lectura JSON:**

```python
import json
from pathlib import Path
from typing import Any, Optional
import logging

logger = logging.getLogger(__name__)

def read_json(
    file_path: str | Path,
    default: Optional[Any] = None,
    fix_issues: bool = False
) -> Any:
    path = Path(file_path)
    
    if not path.exists():
        if default is not None:
            logger.warning(f"JSON no existe, usando default: {path}")
            return default
        raise FileNotFoundError(f"JSON no encontrado: {path}")
    
    try:
        text = path.read_text(encoding='utf-8')
    except UnicodeDecodeError:
        # Fallback to robust read
        text = path.read_bytes().decode('utf-8-sig')
    
    # Remove BOM if present
    if text.startswith('\ufeff'):
        text = text[1:]
    
    if fix_issues:
        text = fix_common_json_issues(text)
    
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        logger.error(f"JSON inválido en {path}: {e}")
        if default is not None:
            return default
        raise
```

**Función de escritura JSON segura:**

```python
import json
from pathlib import Path
from typing import Any

def write_json(
    file_path: str | Path,
    data: Any,
    indent: int = 2,
    ensure_ascii: bool = False
) -> None:
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    text = json.dumps(
        data,
        indent=indent,
        ensure_ascii=ensure_ascii,
        sort_keys=True
    )
    
    path.write_text(text, encoding='utf-8')
```

### Validación con Schema

```python
import json
from pathlib import Path
from typing import Any
try:
    from jsonschema import validate, ValidationError
    HAS_JSONSCHEMA = True
except ImportError:
    HAS_JSONSCHEMA = False

def validate_json_schema(data: Any, schema: dict) -> bool:
    if not HAS_JSONSCHEMA:
        return True  # Skip if jsonschema not installed
    
    try:
        validate(instance=data, schema=schema)
        return True
    except ValidationError as e:
        raise ValueError(f"JSON no cumple schema: {e.message}")
```

---

## Prevención

### Validar JSON de APIs

```python
import json
from typing import Any
import logging

logger = logging.getLogger(__name__)

def safe_json_parse(text: str, source: str = "unknown") -> Any:
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        logger.error(f"JSON inválido desde {source}: {e}")
        logger.debug(f"Primeros 200 chars: {text[:200]}")
        raise ValueError(f"Respuesta inválida de {source}") from e
```

### Usar Bibliotecas Tolerantes

```python
# Para JSON5 (permite comentarios, trailing commas, etc.)
try:
    import json5
    data = json5.loads(text)
except ImportError:
    # Fallback a json estándar
    data = json.loads(text)

# Para JSON con comentarios
try:
    import commentjson
    data = commentjson.loads(text)
except ImportError:
    data = json.loads(text)
```

### Testing de JSON

```python
import json
from pathlib import Path
import pytest

def test_json_files_valid():
    json_dir = Path("data/json")
    for json_file in json_dir.glob("*.json"):
        content = json_file.read_text(encoding='utf-8')
        try:
            json.loads(content)
        except json.JSONDecodeError as e:
            pytest.fail(f"JSON inválido en {json_file}: {e}")
```

---

## Referencias

- [JSON Specification (RFC 8259)](https://datatracker.ietf.org/doc/html/rfc8259)
- [Python json module](https://docs.python.org/3/library/json.html)
- [PB-001: Encoding Errors](./PB-001-encoding-errors.md)
- [jsonschema library](https://python-jsonschema.readthedocs.io/)

---

## Historial de Uso

| Fecha | Contexto | Resultado |
|-------|----------|-----------|
| 2026-03-11 | Creación del playbook | ✅ Documentado |

---

> *"JSON debe ser válido. UTF-8 sin BOM. Sin trailing commas. Sin comentarios."*