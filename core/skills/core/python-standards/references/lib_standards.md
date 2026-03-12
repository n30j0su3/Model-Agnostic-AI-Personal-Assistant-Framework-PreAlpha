# Library Standards

Estándares estrictos para módulos y librerías Python (código reutilizable, sin interacción de consola).

---

## Prohibido: Emojis

**Nunca usar emojis** en librerías. Deben ser completamente ASCII.

- **Prohibido**: `"✅ Success"`, `"❌ Error"`, `"⚠️ Warning"`
- **Permitido**: `"Success"`, `"[OK] Success"`, `"Error"`

```python
# INCORRECTO
raise ValueError("❌ Invalid input")

# CORRECTO
raise ValueError("Invalid input")

# INCORRECTO
return {"status": "✅", "data": result}

# CORRECTO
return {"status": "success", "data": result}
```

---

## Prohibido: Print Statements

**Nunca usar `print()`** en librerías. Usar logging o retornar valores.

```python
import logging
from typing import Optional

# Configurar logger (el caller lo configura)
logger = logging.getLogger(__name__)

def process_data(data: dict) -> dict:
    """Procesa datos y retorna resultado."""
    # INCORRECTO: print("Processing data...")
    
    # CORRECTO: Usar logging
    logger.debug("Processing data with keys: %s", list(data.keys()))
    
    result = transform(data)
    
    # CORRECTO: Usar logging
    logger.info("Processed %d items", len(result))
    
    return result
```

**Alternativas a print**:
- `logging.debug()` — Información de desarrollo
- `logging.info()` — Eventos normales
- `logging.warning()` — Advertencias
- Retornar resultados para que el caller decida mostrarlos

---

## Exception Handling

**Propagar excepciones** con contexto adicional. No capturar silenciosamente.

```python
from pathlib import Path
from typing import Dict

class DataError(Exception):
    """Error específico del módulo."""
    pass

class ValidationError(DataError):
    """Error de validación."""
    pass

def load_config(path: str) -> Dict:
    """Carga configuración desde archivo."""
    file_path = Path(path)
    
    # Validar precondiciones
    if not file_path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return parse_config(content)
        
    except UnicodeDecodeError as e:
        # Agregar contexto y re-lanzar
        raise DataError(f"Config file is not valid UTF-8: {e}") from e
    except json.JSONDecodeError as e:
        raise ValidationError(f"Invalid JSON in config: {e}") from e
```

**Principios**:
- Definir excepciones específicas del módulo
- Usar `raise ... from e` para preservar stack trace
- No capturar `Exception` genérico a menos que sea necesario
- Documentar excepciones en docstrings

---

## Tipado Estricto

**Usar type hints** en todas las funciones públicas.

```python
from pathlib import Path
from typing import Dict, List, Optional, Union, Iterator

def parse_items(
    source: Union[str, Path],
    delimiter: str = ",",
    skip_empty: bool = True
) -> List[str]:
    """
    Parsea items desde archivo o string.
    
    Args:
        source: Ruta al archivo o string con datos
        delimiter: Separador de items
        skip_empty: Si ignorar líneas vacías
    
    Returns:
        Lista de items parseados
    
    Raises:
        FileNotFoundError: Si source es path y no existe
        ValueError: Si el formato es inválido
    """
    # Implementación...
    pass


def process_batch(items: List[dict]) -> Iterator[dict]:
    """
    Procesa items en batch.
    
    Yields:
        Resultados procesados uno a uno
    """
    for item in items:
        yield transform(item)
```

---

## API Pública Clara

**Definir explícitamente** qué es público con `__all__`.

```python
"""
Módulo de utilidades para procesamiento de datos.

Este módulo proporciona funciones para cargar, validar y transformar datos.
"""

__all__ = [
    "load_data",
    "validate_schema",
    "transform_records",
    "DataLoader",
    "ValidationError",
]

# Imports internos (no exportados)
from ._internal import _helper_function

# API Pública
def load_data(source: str) -> dict:
    """Carga datos desde fuente."""
    pass

def validate_schema(data: dict) -> bool:
    """Valida datos contra esquema."""
    pass

def transform_records(records: list) -> list:
    """Transforma registros."""
    pass

class DataLoader:
    """Cargador de datos configurable."""
    pass

class ValidationError(Exception):
    """Error de validación de datos."""
    pass
```

---

## Documentación de Funciones

**Docstrings con formato consistente**.

```python
def calculate_metrics(
    data: List[float],
    include_std: bool = False
) -> Dict[str, float]:
    """
    Calcula métricas estadísticas básicas.
    
    Args:
        data: Lista de valores numéricos
        include_std: Si incluir desviación estándar
    
    Returns:
        Diccionario con métricas:
        - mean: Media aritmética
        - median: Mediana
        - std: Desviación estándar (si include_std=True)
    
    Raises:
        ValueError: Si data está vacía
        TypeError: Si data contiene no-numéricos
    
    Example:
        >>> calculate_metrics([1.0, 2.0, 3.0])
        {'mean': 2.0, 'median': 2.0}
    """
    if not data:
        raise ValueError("Data cannot be empty")
    
    # ... implementación
```

---

## Ejemplo de Librería Completa

```python
#!/usr/bin/env python3
"""
ConfigManager - Gestor de configuración tipo librería.

Uso:
    from config_manager import ConfigManager, ConfigError
    
    config = ConfigManager("config.json")
    value = config.get("database.host", default="localhost")
"""

__all__ = ["ConfigManager", "ConfigError", "ConfigNotFoundError"]

import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional, Union

logger = logging.getLogger(__name__)


class ConfigError(Exception):
    """Error base de configuración."""
    pass


class ConfigNotFoundError(ConfigError):
    """Configuración no encontrada."""
    pass


class ConfigManager:
    """Gestor de configuración con soporte de paths anidados."""
    
    def __init__(self, config_path: Union[str, Path]):
        """
        Inicializa el gestor.
        
        Args:
            config_path: Ruta al archivo de configuración JSON
        
        Raises:
            ConfigNotFoundError: Si el archivo no existe
            ConfigError: Si el JSON es inválido
        """
        self._path = Path(config_path)
        self._data: Dict[str, Any] = {}
        
        self._load()
    
    def _load(self) -> None:
        """Carga configuración desde archivo."""
        if not self._path.exists():
            raise ConfigNotFoundError(f"Config file not found: {self._path}")
        
        try:
            with open(self._path, 'r', encoding='utf-8') as f:
                self._data = json.load(f)
            logger.info("Loaded config from %s", self._path)
        except json.JSONDecodeError as e:
            raise ConfigError(f"Invalid JSON: {e}") from e
        except UnicodeDecodeError as e:
            raise ConfigError(f"File not UTF-8: {e}") from e
    
    def get(
        self,
        key: str,
        default: Any = None
    ) -> Any:
        """
        Obtiene valor por clave (soporta notación punto).
        
        Args:
            key: Clave en formato "section.subkey"
            default: Valor por defecto si no existe
        
        Returns:
            Valor encontrado o default
        
        Example:
            >>> config.get("database.host", "localhost")
            'localhost'
        """
        keys = key.split('.')
        value = self._data
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def get_section(self, section: str) -> Dict[str, Any]:
        """
        Obtiene sección completa.
        
        Args:
            section: Nombre de la sección
        
        Returns:
            Diccionario con la sección
        
        Raises:
            ConfigError: Si la sección no existe
        """
        if section not in self._data:
            raise ConfigError(f"Section not found: {section}")
        
        result = self._data[section]
        if not isinstance(result, dict):
            raise ConfigError(f"Section '{section}' is not a dict")
        
        return result
```

---

## Checklist Library Modules

- [ ] Sin emojis (ASCII únicamente)
- [ ] Sin `print()` statements (usar logging)
- [ ] Type hints en funciones públicas
- [ ] Docstrings completos
- [ ] Excepciones específicas del módulo
- [ ] `__all__` definido explícitamente
- [ ] Manejo de encoding UTF-8 en archivos
- [ ] Uso de `pathlib.Path` para paths
- [ ] No incluir `if __name__ == "__main__"`
- [ ] Logging en lugar de output directo
