---
name: python-standards
description: Estándares y validación para scripts Python cross-platform (Windows/Linux/macOS). Esta skill debe usarse cuando se escriban scripts Python en el framework para garantizar compatibilidad multi-SO, evitar problemas de encoding (emojis en Windows), y asegurar calidad consistente en todo el código.
license: MIT
metadata:
  author: FreakingJSON Framework
  version: "1.0"
  created: 2026-02-11
compatibility: Requiere Python 3.8+. Funciona en Windows, Linux y macOS.
---

# Python Standards

Sistema completo de estándares, validación y auto-corrección para scripts Python cross-platform en el framework FreakingJSON.

## Problema que Resuelve

### El Problema del Encoding en Windows

Windows utiliza code pages diferentes (cp1252, cp437) en lugar de UTF-8 por defecto. Esto causa errores como:

```
UnicodeEncodeError: 'charmap' codec can't encode character '\U0001f680'
```

Cuando se usan emojis (✅, ❌, ⚠️) en scripts Python ejecutados en consolas Windows sin UTF-8 configurado.

### Solución: Detección Automática de Entorno

En lugar de prohibir emojis completamente (que reduce UX en Linux/macOS), detectamos el entorno y adaptamos la salida:

```python
from core.skills.core.python-standards.scripts.detect_env import should_use_emojis, get_safe_prefix

if should_use_emojis():
    print("✅ Éxito")
else:
    print("[OK] Éxito")
```

## Casos de Uso

1. **Crear Scripts Nuevos**: Usar templates CLI o lib para empezar con estándares correctos
2. **Validar Scripts Existentes**: Chequear cumplimiento de estándares antes de deployment
3. **Corregir Scripts**: Auto-fixear problemas simples (emojis → ASCII, encoding en open())
4. **Integrar en Skills**: Validar automáticamente scripts de nuevas skills

## Cuándo Usar Esta Skill

Esta skill debe usarse cuando:
- Se escriba un nuevo script Python en el framework
- Se modifique un script existente antes de commit
- Se cree una nueva skill (integración con @skill-creator)
- Se prepare un deployment a PROD
- Se reporten errores de encoding en Windows

## Tipos de Scripts

### Scripts CLI (Interactivos)

Scripts que interactúan con el usuario por consola:
- `pa.py` - Control panel del framework
- `install.py` - Instalador
- `sync-context.py` - Sincronización

**Características**:
- ✅ Pueden usar emojis (con detección automática)
- ✅ Output a consola (print, input)
- ✅ Experiencia de usuario importante
- ✅ Deben usar `detect_env.py`

**Template**: `references/template_cli.py`

### Scripts Librería (Módulos)

Scripts reutilizables, sin interacción directa con consola:
- `csv_processor.py` - Procesamiento de CSV
- `init_skill.py` - Inicializador de skills
- `check_script.py` - Validador

**Características**:
- ❌ No emojis (nunca, independiente del entorno)
- ❌ No print statements (return values)
- ✅ Logging para debugging
- ✅ ASCII puro para máxima compatibilidad

**Template**: `references/template_lib.py`

## Scripts Disponibles

### detect_env.py

**Uso**: Detectar si es seguro usar emojis en el entorno actual

```python
# Al inicio de cualquier script CLI
import sys
sys.path.insert(0, 'core/skills/core/python-standards/scripts')
from detect_env import should_use_emojis, SafePrinter

USE_EMOJIS = should_use_emojis()
printer = SafePrinter()

# Uso individual
if USE_EMOJIS:
    print("✅ Éxito")
else:
    print("[OK] Éxito")

# O usar SafePrinter (recomendado)
printer.success("Operación exitosa")
printer.error("Algo falló")
printer.warning("Advertencia")
printer.info("Información")
```

### check_script.py

**Uso**: Validar un script contra estándares cross-platform

```bash
# Validar un archivo
python core/skills/core/python-standards/scripts/check_script.py mi_script.py

# Validar con sugerencias de corrección
python core/skills/core/python-standards/scripts/check_script.py mi_script.py --fix-suggestions

# Validar todo un directorio
python core/skills/core/python-standards/scripts/check_script.py . --recursive
```

**Checks realizados**:
- ✅ Shebang correcto
- ✅ encoding='utf-8' en open()
- ❌ Emojis en print() (librerías)
- ❌ Emojis en mensajes de error
- ⚠️ Concatenación de paths con strings
- ℹ️ Orden de imports
- ⚠️ Line endings mixtos

### fix_script.py

**Uso**: Corregir automáticamente problemas simples

```bash
# Crear copia corregida
python core/skills/core/python-standards/scripts/fix_script.py mi_script.py --output mi_script_fixed.py

# Corregir en lugar (crea backup)
python core/skills/core/python-standards/scripts/fix_script.py mi_script.py --in-place

# Procesar directorio completo
python core/skills/core/python-standards/scripts/fix_script.py . --recursive --in-place

# Simular cambios sin aplicar
python core/skills/core/python-standards/scripts/fix_script.py mi_script.py --dry-run
```

**Correcciones automáticas**:
- ✅ → [OK]
- ❌ → [ERROR]
- ⚠️ → [WARN]
- ℹ️ → [INFO]
- open(file) → open(file, encoding='utf-8')
- Agregar shebang si falta

## Recursos Disponibles

### References

- **`standards.md`** - Estándares generales cross-platform
- **`cli_standards.md`** - Estándares específicos para scripts CLI
- **`lib_standards.md`** - Estándares estrictos para librerías

### Templates

- **`template_cli.py`** - Plantilla para scripts CLI con detección de entorno
- **`template_lib.py`** - Plantilla para librerías sin dependencia de consola

### Assets

- **`header_cli.txt`** - Header para scripts CLI
- **`header_lib.txt`** - Header para librerías

## Integración con @skill-creator

Esta skill está integrada en el proceso de creación de skills:

### Paso Adicional en Creación de Skills

Al usar @skill-creator para crear una nueva skill, el proceso incluye:

```markdown
## Proceso de Creación de Skills (Actualizado)

### Paso 6: Validar Cross-Platform (NUEVO)

Antes de empaquetar, validar todos los scripts Python:

```bash
# Validar scripts de la nueva skill
python core/skills/core/python-standards/scripts/check_script.py \
    core/skills/core/nueva-skill/scripts/*.py

# Si hay issues, corregir automáticamente
python core/skills/core/python-standards/scripts/fix_script.py \
    core/skills/core/nueva-skill/scripts/*.py --in-place

# Re-validar
python core/skills/core/python-standards/scripts/check_script.py \
    core/skills/core/nueva-skill/scripts/*.py
```

**Criterios de aceptación**:
- [ ] 0 errores de encoding
- [ ] 0 emojis en scripts librería
- [ ] Scripts CLI usan detect_env.py
- [ ] Todos los open() tienen encoding='utf-8'
```

### Plantilla para SKILL.md

Cuando se crea una skill que incluye scripts, agregar en SKILL.md:

```markdown
## Compatibilidad Cross-Platform

Esta skill sigue los estándares @python-standards:
- Scripts validados con check_script.py
- Compatible con Windows, Linux y macOS
- Sin dependencias de encoding específicas
```

## Mejores Prácticas

### 1. Siempre Validar Antes de Commit

```bash
# Antes de hacer commit de un script
python core/skills/core/python-standards/scripts/check_script.py mi_script.py
```

### 2. Usar Templates para Scripts Nuevos

```bash
# Copiar template apropiado
cp core/skills/core/python-standards/references/template_cli.py \
   core/skills/core/mi-skill/scripts/mi_script.py
```

### 3. Testing en Windows

Si tienes acceso a Windows, siempre testear:
```bash
# En Windows con cmd (no PowerShell)
python mi_script.py
```

### 4. Documentar Decisiones

Si un script DEBE usar emojis (por requerimiento de UX), documentarlo:
```python
# Nota: Este script usa emojis intencionalmente para UX
# Requiere Windows con UTF-8 o Linux/macOS
```

## Flujo de Trabajo Recomendado

### Para Desarrolladores de Skills

```
1. Crear script usando template apropiado
2. Desarrollar funcionalidad
3. Ejecutar check_script.py
4. Si hay issues: ejecutar fix_script.py
5. Re-ejecutar check_script.py (debe pasar limpio)
6. Testing manual en tu SO
7. Commit
```

### Para Deployment a PROD

```
1. Ejecutar check_script.py en todos los scripts
2. Documentar cualquier issue no resuelto
3. Validar en Windows si es posible
4. Proceder con deployment
```

## Troubleshooting

### Problema: "UnicodeEncodeError al imprimir"

**Causa**: Emojis en consola Windows sin UTF-8

**Solución**:
```python
from detect_env import SafePrinter
printer = SafePrinter()
printer.success("Mensaje")  # Usa [OK] o ✅ según entorno
```

### Problema: "Script funciona en Linux pero no en Windows"

**Causa**: Probablemente paths con `/` o encoding

**Solución**:
```python
from pathlib import Path
# ❌ path = "dir/" + filename
# ✅ path = Path("dir") / filename
```

### Problema: "Archivo se lee mal en Windows"

**Causa**: open() sin encoding='utf-8'

**Solución**:
```python
# ❌ with open('file.txt') as f:
# ✅ with open('file.txt', encoding='utf-8') as f:
```

## Referencias

- [PEP 8 - Style Guide for Python Code](https://peps.python.org/pep-0008/)
- [PEP 263 - Defining Python Source Code Encodings](https://peps.python.org/pep-0263/)
- [Python pathlib Documentation](https://docs.python.org/3/library/pathlib.html)
- [Windows Code Pages](https://docs.microsoft.com/en-us/windows/win32/intl/code-pages)

## Notas

- Esta skill es CORE del framework y debe mantenerse actualizada
- Los estándares evolucionan según se descubren nuevos problemas cross-platform
- Contribuciones al mejoramiento de estándares son bienvenidas vía ideas.md
