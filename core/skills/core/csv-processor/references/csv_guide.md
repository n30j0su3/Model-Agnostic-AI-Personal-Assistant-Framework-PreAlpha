# Guía de Formato CSV

Guía completa sobre el formato CSV (Comma-Separated Values) y mejores prácticas.

## ¿Qué es CSV?

CSV es un formato de texto plano para almacenar datos tabulares, donde:
- Cada línea representa una fila/registro
- Los campos se separan por un delimitador (comúnmente coma)
- La primera línea puede contener headers (nombres de columnas)

## Formatos Comunes

### CSV Estándar (RFC 4180)
```csv
Nombre,Edad,Ciudad
Juan,30,Madrid
María,25,Barcelona
```

### TSV (Tab-Separated Values)
```tsv
Nombre\tEdad\tCiudad
Juan\t30\tMadrid
```

### CSV con punto y coma (Europa/Latinoamérica)
```csv
Nombre;Edad;Ciudad
Juan;30;Madrid
```

## Encoding

| Encoding | Uso | Consideraciones |
|----------|-----|-----------------|
| **UTF-8** | Internacional | Recomendado por defecto |
| **UTF-8 BOM** | Excel | Para compatibilidad con Excel |
| **Latin-1** | Europa Occidental | Legacy |
| **CP1252** | Windows | Cuando el origen es Windows |

## Problemas Comunes y Soluciones

### 1. Campos con comas
```csv
# Incorrecto
Producto,Precio
Manzanas rojas,1.50

# Correcto (entre comillas)
Producto,Precio
"Manzanas, rojas",1.50
```

### 2. Campos con saltos de línea
```csv
Nombre,Descripción
Juan,"Línea 1
Línea 2"
```

### 3. Caracteres especiales
Siempre usar UTF-8 para evitar problemas con:
- Tildes (á, é, í, ó, ú)
- Eñes (ñ)
- Símbolos monetarios (€, $, £)

## Esquema de Datos

### Tipos de Datos en CSV

CSV no tiene tipos nativos, pero se pueden inferir:

| Tipo | Ejemplo | Inferencia |
|------|---------|------------|
| Entero | 42 | Dígitos sin punto decimal |
| Decimal | 3.14 | Dígitos con punto decimal |
| String | "Texto" | Cualquier texto |
| Fecha | 2026-02-11 | Formato ISO 8601 recomendado |
| Booleano | true/false | Case-insensitive |

### Conversión de Tipos (Pandas)

```python
import pandas as pd

# Especificar tipos al leer
dtypes = {
    'id': 'int64',
    'precio': 'float64',
    'fecha': 'str'
}
df = pd.read_csv('datos.csv', dtype=dtypes)

# Convertir después
df['fecha'] = pd.to_datetime(df['fecha'])
df['categoria'] = df['categoria'].astype('category')
```

## Mejores Prácticas

### 1. Nombres de Columnas
- Usar minúsculas
- Sin espacios (usar guiones bajos)
- Sin caracteres especiales
- Descriptivos pero concisos

```csv
# Bueno
user_id,first_name,last_name,email

# Malo
User ID,First Name,Last Name,Email Address
```

### 2. Manejo de Nulos
```csv
# Opciones representadas
Nombre,Edad,Ciudad
Juan,30,Madrid
María,,Barcelona  # Edad desconocida
Pedro,25,         # Ciudad desconocida
```

### 3. Consistencia
- Mismo número de columnas en todas las filas
- Mismo formato de fecha en toda la columna
- Mismo separador decimal (punto vs coma)

### 4. Tamaño de Archivo
- **Óptimo**: < 10MB para procesamiento rápido
- **Grande**: 10MB - 500MB (usar chunks)
- **Muy grande**: > 500MB (considerar otro formato)

## Integración con el Framework

### Flujo CSV → Excel
```bash
# 1. Limpiar con csv-processor
python csv_processor.py datos.csv limpio.csv --mode clean

# 2. Convertir a Excel (para formateo con @xlsx)
python csv_processor.py limpio.csv datos.xlsx --mode convert
```

### Flujo CSV → Análisis
```bash
# Análisis directo
python csv_processor.py datos.csv stats.json --mode analyze --stats all

# O cargar en Python para @data-viz
import pandas as pd
df = pd.read_csv('datos.csv')
```

### Flujo CSV → Documento
```bash
# 1. Procesar CSV
python csv_processor.py datos.csv resumen.csv --mode transform --select-columns col1,col2

# 2. Usar @docx para crear documento con tabla
```

## Validación de CSV

### Checklist de Calidad
- [ ] Encoding correcto (UTF-8)
- [ ] Sin filas vacías al final
- [ ] Headers presentes y únicos
- [ ] Mismo número de columnas por fila
- [ ] Tipos de datos consistentes por columna
- [ ] Sin caracteres de control (, \x00)

### Herramientas de Validación
```bash
# Contar filas y columnas
wc -l archivo.csv
head -1 archivo.csv | tr ',' '\n' | wc -l

# Ver encoding
file -i archivo.csv

# Verificar estructura
python csv_processor.py archivo.csv /dev/null --mode analyze
```

## Referencias

- [RFC 4180](https://tools.ietf.org/html/rfc4180) - Especificación CSV
- [Pandas read_csv](https://pandas.pydata.org/docs/reference/api/pandas.read_csv.html)
- [CSV on MDN](https://developer.mozilla.org/en-US/docs/Web/API/Document/cookie)
