---
name: etl
description: Core Skill para manipulación y transformación de datos (Extract, Transform, Load). Especializado en operaciones locales rápidas sobre CSV, JSON y Excel.
license: MIT
metadata:
  author: FreakingJSON Framework
  version: "1.0"
compatibility: Requires Python 3.8+. pandas/openpyxl opcionales.
---

# ETL Data Processor

Core Skill para manipulación y transformación de datos (Extract, Transform, Load). Especializado en operaciones locales rápidas sobre CSV, JSON y Excel (si librerías están disponibles).

## Capacidades

1.  **Conversión de Formatos**:
    *   CSV -> JSON
    *   JSON -> CSV
    *   Excel -> CSV/JSON (Requiere `openpyxl` o `pandas`)

2.  **Operaciones**:
    *   `merge`: Unificar múltiples archivos CSV con headers idénticos.
    *   `filter`: Filtrar filas donde una columna coincida con un valor.
    *   `sample`: Extraer una muestra aleatoria o las primeras N filas.

## Uso (CLI)

```bash
# Convertir CSV a JSON
python core/skills/core/etl/scripts/processor.py csv2json --input data.csv --output data.json

# Unificar carpeta de CSVs
python core/skills/core/etl/scripts/processor.py merge --input ./folder_with_csvs --output merged.csv

# Filtrar datos
python core/skills/core/etl/scripts/processor.py filter --input data.csv --column "status" --value "active"
```

## Dependencias
- Standard Library: `csv`, `json`, `pathlib`
- Opcional: `pandas`, `openpyxl` (detectados automáticamente)
