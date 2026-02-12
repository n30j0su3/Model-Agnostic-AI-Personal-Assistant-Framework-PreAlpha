# CLI Script Standards

Estándares para scripts de consola interactivos (CLI tools, automatizaciones, utilidades).

---

## Detección de Emojis

**Detectar antes de usar**. Windows con code page diferente a UTF-8 no soporta emojis.

```python
import detect_env

# Detectar al inicio del script
USE_EMOJIS = detect_env.should_use_emojis()

# Usar condicionalmente
def log_success(msg):
    prefix = "✅" if USE_EMOJIS else "[OK]"
    print(f"{prefix} {msg}")
```

**Reglas**:
- Siempre detectar al inicio del script
- Usar ASCII fallback en Windows sin UTF-8
- No asumir soporte de emojis

---

## SafePrinter

**Usar la clase `SafePrinter`** para output consistente.

```python
from detect_env import SafePrinter

# Inicializar al inicio
printer = SafePrinter()

# Usar en todo el script
printer.success("Operación exitosa")  # ✅ o [OK]
printer.error("Error encontrado")     # ❌ o [ERROR]
printer.warning("Advertencia")        # ⚠️ o [WARN]
printer.info("Información")           # ℹ️ o [INFO]
```

**Mapeo de prefijos**:

| Tipo | Emoji | ASCII Fallback |
|------|-------|----------------|
| success | ✅ | [OK] |
| error | ❌ | [ERROR] |
| warning | ⚠️ | [WARN] |
| info | ℹ️ | [INFO] |
| arrow | ➜ | -> |
| bullet | • | - |
| check | ✓ | [X] |
| cross | ✗ | [ ] |

---

## Configuración de Consola

**Configurar UTF-8 al inicio** del script.

```python
import sys
import platform

def configure_stdout():
    """Configura stdout para UTF-8."""
    if platform.system() == "Windows":
        import ctypes
        kernel32 = ctypes.windll.kernel32
        kernel32.SetConsoleOutputCP(65001)  # UTF-8
    
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Llamar al inicio del script
configure_stdout()
```

---

## Output de Colores

**Usar colores condicionalmente** según soporte del terminal.

```python
import os
import sys

def supports_color():
    """Detecta si el terminal soporta colores."""
    if sys.platform == 'win32':
        return 'ANSICON' in os.environ or 'WT_SESSION' in os.environ
    return hasattr(sys.stdout, 'isatty') and sys.stdout.isatty()

# Códigos ANSI
COLORS = {
    'red': '\033[91m',
    'green': '\033[92m',
    'yellow': '\033[93m',
    'blue': '\033[94m',
    'reset': '\033[0m'
}

def colorize(text, color):
    if supports_color():
        return f"{COLORS.get(color, '')}{text}{COLORS['reset']}"
    return text

# Uso
print(colorize("Error crítico", "red"))
print(colorize("Operación exitosa", "green"))
```

---

## Estructura de Script CLI

Template estándar para scripts de consola:

```python
#!/usr/bin/env python3
"""
Descripción breve del script.

Uso:
    python script.py [opciones]
"""

import argparse
import sys
from pathlib import Path

# 1. Configurar stdout UTF-8
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# 2. Importar SafePrinter
from detect_env import SafePrinter
printer = SafePrinter()


def main():
    """Función principal."""
    parser = argparse.ArgumentParser(description="Descripción")
    parser.add_argument("input", help="Archivo de entrada")
    args = parser.parse_args()
    
    try:
        # Lógica principal
        result = process(args.input)
        printer.success(f"Procesado: {result}")
        return 0
    except Exception as e:
        printer.error(f"Fallo: {e}")
        return 1


def process(input_file: str) -> str:
    """Procesa el archivo."""
    path = Path(input_file)
    if not path.exists():
        raise FileNotFoundError(f"No existe: {input_file}")
    # ...
    return "output"


if __name__ == "__main__":
    sys.exit(main())
```

---

## Manejo de Errores en CLI

**Capturar, mostrar y salir con código apropiado**.

```python
import sys
from detect_env import SafePrinter

printer = SafePrinter()

def main():
    try:
        risky_operation()
        printer.success("Completado")
        return 0  # Éxito
    except FileNotFoundError as e:
        printer.error(f"Archivo no encontrado: {e}")
        return 2  # Error específico
    except PermissionError:
        printer.error("Sin permisos suficientes")
        return 3
    except Exception as e:
        printer.error(f"Error inesperado: {e}")
        return 1  # Error general

if __name__ == "__main__":
    sys.exit(main())
```

---

## Ejemplo Completo

```python
#!/usr/bin/env python3
"""
Ejemplo de script CLI con estándares cross-platform.
"""

import argparse
import sys
from pathlib import Path

# Configurar stdout
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from detect_env import SafePrinter

printer = SafePrinter()


def main():
    parser = argparse.ArgumentParser(
        description="Lee y muestra contenido de archivo"
    )
    parser.add_argument("file", help="Archivo a leer")
    args = parser.parse_args()
    
    file_path = Path(args.file)
    
    if not file_path.exists():
        printer.error(f"Archivo no existe: {file_path}")
        return 1
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        printer.info(f"Leyendo: {file_path}")
        print("-" * 40)
        print(content)
        print("-" * 40)
        printer.success(f"Leídos {len(content)} caracteres")
        return 0
        
    except UnicodeDecodeError:
        printer.error("El archivo no es UTF-8 válido")
        return 2
    except Exception as e:
        printer.error(f"Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
```

---

## Checklist CLI Scripts

- [ ] Incluir shebang `#!/usr/bin/env python3`
- [ ] Configurar UTF-8 en stdout
- [ ] Usar `SafePrinter` para output
- [ ] Detectar soporte de emojis
- [ ] Usar `pathlib.Path` para paths
- [ ] Manejar errores con try/except
- [ ] Retornar códigos de salida apropiados
- [ ] Incluir docstring con uso
