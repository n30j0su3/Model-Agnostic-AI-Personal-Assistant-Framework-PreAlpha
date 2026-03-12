---
id: PB-001
category: encoding
severity: high
frequency: frequent
auto_generated: false
created: 2026-03-11
last_used: 2026-03-11
success_rate: 100
---

# PB-001: Errores de Codificación Windows

> **Playbook para errores UnicodeEncodeError y problemas de charmap en Windows.**

---

## Síntomas

### Mensajes Típicos

```
UnicodeEncodeError: 'charmap' codec can't encode characters in position X-Y: character maps to <undefined>
```

```
UnicodeDecodeError: 'utf-8' codec can't decode byte 0xXX in position X: invalid continuation byte
```

### Cuándo Ocurre

- Escritura de archivos con caracteres especiales (ñ, á, é, etc.)
- Lectura de archivos sin encoding especificado
- Pipes/redirección en consola Windows
- Impresión a stdout con caracteres no-ASCII

---

## Causa Raíz

Windows usa **cp1252** (Windows-1252) como encoding por defecto en consola, mientras que:

- Python 3 usa UTF-8 por defecto internamente
- Archivos modernos suelen ser UTF-8
- La consola no puede representar ciertos caracteres

**Conflicto**: Python intenta codificar Unicode a cp1252, pero cp1252 no tiene mapeo para todos los caracteres Unicode.

---

## Soluciones

### Inmediata (Quick Fix)

**Para escritura de archivos:**

```python
with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
```

**Para lectura de archivos:**

```python
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()
```

**Para stdout/print:**

```python
import sys
sys.stdout.reconfigure(encoding='utf-8')
```

### Permanente

**Opción A: Variable de entorno**

```bash
# PowerShell
$env:PYTHONIOENCODING = "utf-8"

# CMD
set PYTHONIOENCODING=utf-8
```

Agregar a perfil de PowerShell (`$PROFILE`):

```powershell
$env:PYTHONIOENCODING = "utf-8"
```

**Opción B: Configurar consola Windows Terminal**

En `settings.json`:

```json
{
  "profiles": {
    "defaults": {
      "font": {
        "face": "Cascadia Code"
      }
    }
  }
}
```

**Opción C: Código Python al inicio**

```python
import sys
import io

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
```

### Alternativas

**Usar `errors` parameter:**

```python
# Ignorar caracteres problemáticos
with open(file_path, 'w', encoding='utf-8', errors='ignore') as f:
    f.write(content)

# Reemplazar con ?
with open(file_path, 'w', encoding='utf-8', errors='replace') as f:
    f.write(content)

# Escapar caracteres (xmlcharrefreplace para HTML)
with open(file_path, 'w', encoding='utf-8', errors='xmlcharrefreplace') as f:
    f.write(content)
```

---

## Prevención

### Siempre Especificar Encoding

```python
# ❌ Mal
with open(file_path, 'w') as f:
    f.write(content)

# ✅ Bien
with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
```

### Configurar Proyecto

Crear `.env` o configuración:

```env
PYTHONIOENCODING=utf-8
PYTHONUTF8=1
```

### Validación de Entrada

```python
def safe_write(file_path: str, content: str) -> None:
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
    except UnicodeEncodeError as e:
        # Log y manejo
        print(f"Encoding error: {e}")
        raise
```

---

## Referencias

- [Python Unicode HOWTO](https://docs.python.org/3/howto/unicode.html)
- [PEP 597 – EncodingWarnings](https://peps.python.org/pep-0597/)
- [Windows Code Pages](https://learn.microsoft.com/en-us/windows/win32/intl/code-page-identifiers)

---

## Historial de Uso

| Fecha | Contexto | Resultado |
|-------|----------|-----------|
| 2026-03-11 | Creación del playbook | ✅ Documentado |

---

> *"Siempre especifica encoding='utf-8'. Ahorra horas de debugging."*