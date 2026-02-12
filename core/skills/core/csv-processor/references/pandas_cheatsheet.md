# Pandas Cheatsheet - Operaciones Comunes

Referencia rápida de operaciones pandas útiles para procesamiento CSV.

## Lectura/Escritura

```python
import pandas as pd

# Leer CSV
df = pd.read_csv('archivo.csv')
df = pd.read_csv('archivo.csv', encoding='utf-8')
df = pd.read_csv('archivo.csv', sep=';')  # Delimitador personalizado

# Leer grandes archivos (en chunks)
chunks = pd.read_csv('grande.csv', chunksize=10000)
for chunk in chunks:
    procesar(chunk)

# Escribir CSV
df.to_csv('output.csv', index=False)
df.to_csv('output.csv', encoding='utf-8', sep=';')
```

## Inspección de Datos

```python
# Primeras/últimas filas
df.head(10)
df.tail(10)

# Información general
df.info()
df.describe()

# Dimensiones
len(df)           # Número de filas
len(df.columns)   # Número de columnas
df.shape          # (filas, columnas)

# Columnas y tipos
df.columns.tolist()
df.dtypes
```

## Selección de Datos

```python
# Seleccionar columnas
df['columna']
df[['col1', 'col2']]

# Seleccionar filas por índice
df.iloc[0:10]        # Primeras 10 filas
df.loc[0:10]         # Filas con índice 0 a 10

# Filtrar condiciones
df[df['edad'] > 18]
df[(df['edad'] > 18) & (df['ciudad'] == 'Madrid')]
df.query('edad > 18 and ciudad == "Madrid"')
```

## Limpieza

```python
# Manejo de nulos
df.dropna()                    # Eliminar filas con nulos
df.dropna(subset=['col1'])     # Solo en columnas específicas
df.fillna(0)                   # Rellenar con 0
df['col'].fillna(df['col'].mean())  # Rellenar con media

# Duplicados
df.drop_duplicates()
df.drop_duplicates(subset=['email'])

# Strings
df['nombre'].str.lower()
df['nombre'].str.upper()
df['nombre'].str.strip()
df['nombre'].str.contains('Juan')
df['nombre'].str.replace('old', 'new')
```

## Transformación

```python
# Renombrar columnas
df.rename(columns={'old': 'new'})
df.columns = ['a', 'b', 'c']

# Nueva columna
df['total'] = df['precio'] * df['cantidad']

# Aplicar función
df['categoria'] = df['edad'].apply(lambda x: 'adulto' if x >= 18 else 'menor')

# Agrupar
grupo = df.groupby('ciudad')
grupo['ventas'].sum()
grupo.agg({'ventas': 'sum', 'clientes': 'count'})

# Ordenar
df.sort_values('edad')
df.sort_values('edad', ascending=False)
df.sort_values(['ciudad', 'edad'])

# Pivotar
df.pivot(index='fecha', columns='producto', values='ventas')
df.pivot_table(values='ventas', index='ciudad', aggfunc='sum')
```

## Tipos de Datos

```python
# Convertir tipos
df['edad'] = df['edad'].astype(int)
df['precio'] = df['precio'].astype(float)
df['fecha'] = pd.to_datetime(df['fecha'])
df['categoria'] = df['categoria'].astype('category')

# Fechas
df['fecha'].dt.year
df['fecha'].dt.month
df['fecha'].dt.day
df['fecha'].dt.dayofweek
```

## Estadísticas

```python
# Básicas
df['columna'].mean()
df['columna'].median()
df['columna'].std()
df['columna'].min()
df['columna'].max()
df['columna'].sum()

# Conteos
df['columna'].value_counts()
df['columna'].nunique()

# Correlación
df.corr()
```

## Operaciones Avanzadas

```python
# Merge (join)
pd.merge(df1, df2, on='id')
pd.merge(df1, df2, left_on='id1', right_on='id2', how='left')

# Concatenar
pd.concat([df1, df2])
pd.concat([df1, df2], axis=1)  # Lateral

# Melt (unpivot)
df.melt(id_vars=['id'], value_vars=['col1', 'col2'])

# Ventanas rodantes
df['ventas'].rolling(window=7).mean()
```

## Filtrado Condicional Complejo

```python
# Múltiples condiciones
mask = (
    (df['edad'] >= 18) & 
    (df['edad'] <= 65) & 
    (df['ciudad'].isin(['Madrid', 'Barcelona'])) &
    (~df['email'].isnull())
)
df_filtrado = df[mask]

# Query (sintaxis SQL-like)
df.query('edad >= 18 and ciudad in ["Madrid", "Barcelona"]')
df.query('nombre.str.contains("Juan")', engine='python')
```

## Exportación Específica

```python
# A Excel (requiere openpyxl)
df.to_excel('output.xlsx', index=False, sheet_name='Datos')

# A JSON
df.to_json('output.json', orient='records')

# A HTML
df.to_html('output.html')

# A Markdown
df.to_markdown()
```

## Optimización de Memoria

```python
# Ver uso de memoria
df.info(memory_usage='deep')

# Optimizar tipos
df['entero'] = df['entero'].astype('int32')  # En lugar de int64
df['categoria'] = df['categoria'].astype('category')
df['float'] = df['float'].astype('float32')

# Leer solo columnas necesarias
pd.read_csv('archivo.csv', usecols=['col1', 'col2'])
```

## Patrones Comunes en el Framework

### Patrón 1: Limpieza Completa
```python
df = pd.read_csv('sucio.csv')
df = df.drop_duplicates()
df = df.dropna(subset=['email', 'telefono'])
df['nombre'] = df['nombre'].str.strip().str.title()
df.to_csv('limpio.csv', index=False)
```

### Patrón 2: Agregación para Reporting
```python
df = pd.read_csv('ventas.csv')
resumen = df.groupby(['mes', 'categoria']).agg({
    'ventas': 'sum',
    'unidades': 'sum',
    'cliente_id': 'nunique'
}).reset_index()
resumen.to_csv('resumen.csv', index=False)
```

### Patrón 3: Normalización para ETL
```python
# Unificar formatos de diferentes fuentes
df['fecha'] = pd.to_datetime(df['fecha'], errors='coerce')
df['monto'] = df['monto'].str.replace(',', '.').astype(float)
df['categoria'] = df['categoria'].str.lower().str.strip()
```

## Referencias

- [Pandas Documentation](https://pandas.pydata.org/docs/)
- [Pandas Cheat Sheet (PDF)](https://pandas.pydata.org/Pandas_Cheat_Sheet.pdf)
- [10 Minutes to Pandas](https://pandas.pydata.org/docs/user_guide/10min.html)
