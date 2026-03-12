# Mejores Prácticas para Skills

Guía de mejores prácticas para crear skills efectivas en el framework FreakingJSON.

## Principio MVI (Minimal Viable Information)

El principio MVI es fundamental para mantener las skills útiles y eficientes:

### Qué Significa
- **Máximo 1-3 oraciones** por concepto
- **3-5 bullets** por sección
- **Ejemplo mínimo** cuando aplique
- **Referencia** a docs completos, no duplicar contenido

### Por Qué Importa
1. **Contexto limitado**: Las skills deben caber en la ventana de contexto
2. **Precisión**: Menos es más cuando se instruye a un AI
3. **Mantenibilidad**: Menos contenido = menos lugares para actualizar
4. **Claridad**: Lo esencial destaca cuando no hay ruido

### Ejemplo

❌ **Sin MVI** (Verbose):
```markdown
## Extracción de Texto de PDFs

Para extraer texto de un archivo PDF, primero necesitas asegurarte de que el archivo existe en el sistema de archivos. Luego, debes abrir el archivo usando la librería adecuada. Una vez abierto, puedes iterar sobre cada página del documento y extraer el texto de cada una. El texto extraído puede incluir saltos de línea, espacios adicionales y otros caracteres de formato que podrías querer limpiar después...
```

✅ **Con MVI**:
```markdown
## Extracción de Texto

Extrae texto de PDFs página por página.

```python
import pdfplumber
with pdfplumber.open("doc.pdf") as pdf:
    text = "\n".join(page.extract_text() for page in pdf.pages)
```

Para casos complejos, ver: `references/advanced-extraction.md`
```

## Progressive Disclosure

Organiza la información en 3 niveles según necesidad:

### Nivel 1: Metadata (Siempre en Contexto)
- `name` + `description` en YAML frontmatter
- ~100 palabras máximo
- Determina cuándo se activa la skill

### Nivel 2: SKILL.md Body (Cuando se Activa)
- Instrucciones esenciales para usar la skill
- <5,000 palabras idealmente
- Casos de uso, ejemplos, workflows

### Nivel 3: Bundled Resources (Bajo Demanda)
- Scripts ejecutables (no necesitan contexto)
- References para consulta
- Assets para output

### Implementación

```
skill-name/
├── SKILL.md          # Niveles 1 + 2
├── scripts/          # Nivel 3: Ejecución directa
├── references/       # Nivel 3: Cargar según necesidad
└── assets/           # Nivel 3: Usar en output
```

## Estructura de SKILL.md

### Frontmatter YAML (Requerido)

```yaml
---
name: nombre-skill              # kebab-case, requerido
description: Qué hace y cuándo  # Específica, requerida
license: MIT                    # Opcional pero recomendada
metadata:
  author: Tu Nombre             # Opcional
  version: "1.0"               # Opcional
  created: 2026-01-01          # Opcional
compatibility: Requisitos       # Opcional
---
```

### Cuerpo del Documento

```markdown
# Título de la Skill

Descripción en 1-2 oraciones.

## Casos de Uso
1. Principal
2. Secundario
3. Especial

## Cuándo Usar
Condiciones específicas de activación.

## Instrucciones
Pasos claros y concisos.

## Ejemplos
Código/comandos mínimos.

## Recursos
Qué hay disponible en scripts/, references/, assets/.

## Mejores Prácticas
3-5 puntos clave.

## Notas
Limitaciones o consideraciones.
```

## Estilo de Escritura

### Usa Imperativo/Infinitivo

✅ **Correcto**:
- "Para extraer texto, usa `pdfplumber`"
- "Valida el resultado antes de entregar"
- "Consulta `references/schema.md` para detalles"

❌ **Incorrecto**:
- "Deberías usar `pdfplumber` para extraer texto"
- "Tú puedes validar el resultado"
- "Si necesitas más detalles, puedes consultar..."

### Sé Específico en Descripciones

La `description` en el frontmatter determina cuándo se usa la skill. Debe:

1. **Describir qué hace** la skill en específico
2. **Indicar cuándo usarla** con claridad
3. **Usar tercera persona** ("Esta skill debe usarse...")

✅ **Buena**:
```yaml
description: Procesa archivos PDF para extraer texto, tablas y metadatos. Esta skill debe usarse cuando el usuario necesite manipular documentos PDF, incluyendo extracción de contenido,合并 de archivos múltiples, o generación de nuevos PDFs desde cero.
```

❌ **Mala**:
```yaml
description: Trabaja con PDFs
```

## Organización de Recursos

### Scripts (`scripts/`)

**Cuándo usar**: Operaciones determinísticas que se reescriben frecuentemente

**Ejemplos**:
- Conversión de formatos
- Transformaciones de datos
- Operaciones de archivos repetitivas

**Beneficios**:
- Eficiencia de tokens (no cargar en contexto)
- Confiabilidad determinística
- Reusabilidad entre sesiones

**Nota**: Los scripts pueden necesitar ser leídos para parches o ajustes.

### References (`references/`)

**Cuándo usar**: Documentación que el asistente necesita consultar

**Ejemplos**:
- Esquemas de bases de datos
- Documentación de APIs
- Guías detalladas de workflows
- Políticas o reglas de negocio

**Beneficios**:
- Mantiene SKILL.md lean
- Cargado solo cuando se necesita
- Permite documentación extensa sin penalizar contexto

**Mejor práctica**: Si archivos son >10k palabras, incluye patrones de búsqueda.

### Assets (`assets/`)

**Cuándo usar**: Archivos usados en el output, no para contexto

**Ejemplos**:
- Templates (HTML, Word, PowerPoint)
- Imágenes o logos
- Fuentes tipográficas
- Archivos de configuración base

**Beneficios**:
- Separación clara de recursos de output
- El asistente puede usarlos sin cargarlos
- Templates consistentes

## Validación Pre-Empaque

Antes de distribuir una skill, verifica:

### Estructura
- [ ] Directorio con nombre en kebab-case
- [ ] SKILL.md presente
- [ ] YAML frontmatter válido
- [ ] Campos `name` y `description` presentes

### Contenido
- [ ] Nombre coincide con nombre de directorio
- [ ] Descripción es específica (20+ caracteres)
- [ ] Instrucciones claras y accionables
- [ ] Ejemplos funcionan

### Recursos
- [ ] Scripts referenciados existen
- [ ] References referenciados existen
- [ ] Assets referenciados existen
- [ ] No hay archivos huérfanos

### Calidad
- [ ] Sigue principio MVI
- [ ] Usa progressive disclosure
- [ ] Estilo imperativo/infinitivo
- [ ] Sin información duplicada

## Anti-Patrones a Evitar

### 1. Duplicación de Información

❌ **Mal**:
```markdown
# En SKILL.md
El formato de fecha es YYYY-MM-DD.

# En references/formatos.md  
El formato de fecha es YYYY-MM-DD.
```

✅ **Bien**:
```markdown
# En SKILL.md
Usa formato YYYY-MM-DD. Ver `references/formatos.md` para detalles.

# En references/formatos.md
El formato de fecha es YYYY-MM-DD según ISO 8601 porque...
[explicación completa]
```

### 2. Descripciones Vagas

❌ **Mal**:
```yaml
description: Ayuda con datos
```

✅ **Bien**:
```yaml
description: Procesa datasets CSV/Excel para limpieza, transformación y análisis exploratorio. Esta skill debe usarse cuando el usuario necesite manipular datos tabulares, aplicar transformaciones ETL, o generar visualizaciones básicas.
```

### 3. Instrucciones Ambiguas

❌ **Mal**:
```markdown
## Uso
Procesa los datos según sea necesario.
```

✅ **Bien**:
```markdown
## Uso

### Paso 1: Cargar Datos
```python
import pandas as pd
df = pd.read_csv("data.csv")
```

### Paso 2: Limpiar
- Elimina duplicados: `df.drop_duplicates()`
- Maneja nulos: `df.fillna()` o `df.dropna()`

### Paso 3: Validar
Verifica: [ ] Sin nulos críticos [ ] Tipos correctos [ ] Rangos válidos
```

### 4. Falta de Ejemplos

❌ **Mal**:
```markdown
Puedes rotar PDFs usando pypdf.
```

✅ **Bien**:
```markdown
### Rotar PDF
```python
from pypdf import PdfReader, PdfWriter

reader = PdfReader("input.pdf")
writer = PdfWriter()

for page in reader.pages:
    page.rotate(90)
    writer.add_page(page)

with open("rotated.pdf", "wb") as f:
    writer.write(f)
```
```

## Testing de Skills

Antes de publicar una skill:

1. **Prueba la inicialización**:
   ```bash
   python scripts/init_skill.py test-skill --path /tmp/
   ```

2. **Valida el empaquetado**:
   ```bash
   python scripts/package_skill.py /tmp/test-skill
   ```

3. **Verifica referencias**:
   - Revisa que todos los archivos referenciados existen
   - Confirma que los ejemplos son funcionales

4. **Revisa el estilo**:
   - Sigue el principio MVI
   - Usa imperativo/infinitivo
   - Descripciones específicas

## Recursos Adicionales

- [skill-template.md](./skill-template.md) - Template de SKILL.md
- [SKILL.md](../SKILL.md) - Documentación completa de skill-creator
- [Anthropic Skills Guide](https://github.com/anthropics/skills) - Documentación oficial
