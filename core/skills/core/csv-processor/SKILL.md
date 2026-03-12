---
name: csv-processor
description: Procesa archivos CSV para limpieza, transformación y análisis de datos tabulares. Esta skill debe usarse cuando el usuario necesite manipular datos CSV, incluyendo limpieza de datos, transformaciones (filtros, agregaciones, joins), conversión a otros formatos, o análisis exploratorio de datasets en formato CSV.
license: MIT
metadata:
  author: FreakingJSON Framework
  version: "1.0"
  created: 2026-02-11
compatibility: Requiere Python 3.8+ con pandas instalado.
---

# CSV Processor

Herramienta especializada para procesamiento de archivos CSV con operaciones de limpieza, transformación y análisis. Diseñada para integrarse seamless con el ecosistema de skills del framework.

## Casos de Uso

1. **Limpieza de Datos**: Eliminar duplicados, manejar valores nulos, normalizar formatos
2. **Transformación**: Filtrar filas, agregar/renombrar columnas, pivotar datos
3. **Conversión**: CSV a Excel, JSON, o formatos de documentos (Word/PowerPoint)
4. **Análisis**: Estadísticas descriptivas, detección de outliers, profiling básico

## Cuándo Usar Esta Skill

Esta skill debe usarse cuando el usuario necesite:
- Procesar archivos CSV de manera eficiente con Python/pandas
- Realizar operaciones ETL específicas sobre datos tabulares
- Convertir CSV a otros formatos para reporting o análisis
- Limpiar datasets antes de visualización o análisis avanzado

## Integración con Otras Skills

| Skill | Relación | Uso Combinado |
|-------|----------|---------------|
| **@etl** | Complementaria | csv-processor para CSV específico, @etl para pipelines ETL multi-formato |
| **@xlsx** | Flujo de trabajo | CSV (procesado) → Excel (reporte formateado) vía @xlsx |
| **@docx** | Exportación | Datos CSV procesados → Tablas en documentos Word |
| **@pptx** | Presentación | Datos CSV → Gráficos/tablas en presentaciones PowerPoint |
| **@data-viz** | Análisis | CSV limpio → Visualizaciones con matplotlib/seaborn |

### Flujos de Integración Recomendados

#### Flujo 1: Limpieza → Excel → Documento
```
CSV sucio → @csv-processor (limpieza) → @xlsx (formateo) → @docx (reporte)
```

#### Flujo 2: Análisis → Visualización → Presentación
```
CSV → @csv-processor (agregaciones) → @data-viz (gráficos) → @pptx (slides)
```

#### Flujo 3: Pipeline ETL Completo
```
Múltiples CSV → @csv-processor (normalización) → @etl (joins/transformaciones) → Output
```

## Instrucciones de Uso

### Paso 1: Entender el Dataset
Antes de procesar, comprender:
- Tamaño del archivo (filas/columnas)
- Codificación del archivo
- Separador utilizado (coma, punto y coma, tab)
- Calidad de datos (nulos, duplicados, formatos inconsistentes)

### Paso 2: Seleccionar Operaciones
Usar el script `csv_processor.py` con el modo apropiado:

```bash
python core/skills/core/csv-processor/scripts/csv_processor.py \
    input.csv output.csv \
    --mode clean|transform|analyze|convert \
    [opciones específicas]
```

### Paso 3: Validar Output
Verificar:
- [ ] Formato de datos correcto
- [ ] Sin pérdida de información crítica
- [ ] Listo para siguiente etapa (si aplica integración con otras skills)

## Ejemplos

### Ejemplo 1: Limpieza Básica
```bash
python core/skills/core/csv-processor/scripts/csv_processor.py \
    datos_sucios.csv datos_limpios.csv \
    --mode clean \
    --remove-duplicates \
    --handle-nulls drop \
    --normalize-whitespace
```

### Ejemplo 2: Transformación con Filtros
```bash
python core/skills/core/csv-processor/scripts/csv_processor.py \
    ventas.csv ventas_filtradas.csv \
    --mode transform \
    --filter "region=='Norte'" \
    --select-columns fecha,producto,total \
    --sort-by fecha
```

### Ejemplo 3: Análisis Rápido
```bash
python core/skills/core/csv-processor/scripts/csv_processor.py \
    datos.csv analysis.json \
    --mode analyze \
    --stats all
```

### Ejemplo 4: Uso en Python
```python
import pandas as pd
from core.skills.core.csv_processor.scripts.csv_processor import process_csv

# Limpieza simple
df = process_csv('input.csv', mode='clean')

# Transformación avanzada
df_filtered = process_csv(
    'input.csv', 
    mode='transform',
    filter_query='edad >= 18',
    columns=['nombre', 'edad', 'ciudad']
)
```

## Recursos Disponibles

### Scripts (`scripts/`)
- `csv_processor.py` - Script principal de procesamiento CSV

### References (`references/`)
- `csv_guide.md` - Guía de formato CSV y mejores prácticas
- `pandas_cheatsheet.md` - Referencia rápida de operaciones pandas comunes

## Mejores Prácticas

### 1. Manejo de Encoding
Siempre especificar encoding para archivos con caracteres especiales:
```bash
--encoding utf-8  # o latin-1, cp1252 para Windows
```

### 2. Trabajo con Grandes Datasets
Para archivos >100MB, usar chunks:
```bash
--chunksize 10000  # Procesar en bloques de 10k filas
```

### 3. Preservar Datos Originales
Nunca sobrescribir el archivo fuente. Siempre crear output nuevo.

### 4. Validación Post-Proceso
Después de limpieza, verificar con:
```bash
--validate  # Activa validaciones automáticas
```

### 5. Integración con ETL
Cuando el pipeline es complejo (múltiples fuentes, joins), usar:
- @csv-processor para normalización individual de cada CSV
- @etl para el pipeline completo con joins y transformaciones avanzadas

## Compatibilidad y Limitaciones

### Formatos Soportados
- CSV estándar (RFC 4180)
- TSV (Tab-separated values)
- CSV con delimitadores personalizados
- Archivos con o sin headers

### Limitaciones Conocidas
- No soporta archivos Excel directamente (usar @xlsx → @csv-processor)
- No realiza operaciones de machine learning (usar @data-viz + scikit-learn)
- No conecta a bases de datos directamente (usar @etl para eso)

## Comparativa: @csv-processor vs @etl

| Aspecto | @csv-processor | @etl |
|---------|----------------|------|
| **Enfoque** | CSV específico | Multi-formato (CSV, JSON, Excel, DB) |
| **Complejidad** | Operaciones simples/medias | Pipelines complejos |
| **Performance** | Optimizado para CSV | Generalista |
| **Casos de uso** | Limpieza rápida, conversión | Pipelines ETL enterprise |
| **Integración** | Punto de entrada/salida | Orquestación central |

**Regla de oro**: 
- Un solo CSV → Operaciones simples → Usar @csv-processor
- Múltiples fuentes → Joins complejos → Usar @etl

## Notas

- csv-processor está diseñado como **skill de entrada/salida** en pipelines de datos
- Para operaciones matemáticas complejas sobre datasets, combinar con @data-viz
- Para generación de reportes, usar como pre-procesador antes de @docx o @pptx
