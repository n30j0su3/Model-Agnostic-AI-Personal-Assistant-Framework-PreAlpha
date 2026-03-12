---
title: "CORE-001: Framework-First Validation"
version: "0.2.0-prealpha"
type: "process"
scope: "public"
prp: "PRP-001"
---

# CORE-001: Framework-First Validation

## Principio Fundamental

**SIEMPRE validar y utilizar las skills, agentes y recursos del framework antes de crear soluciones ad-hoc.**

## Descripción

El proceso CORE-001 garantiza que cualquier agente AI que use el framework verifique primero si existe una skill, agente o recurso existente que resuelva el problema antes de crear código personalizado.

Este principio evita:
- Duplicación de código
- Deuda técnica
- Inconsistencias entre sesiones
- Desperdicio de tokens/recursos

## Objetivos

1. Maximizar reuso de componentes existentes
2. Mantener consistencia cross-session
3. Reducir tiempo de desarrollo
4. Optimizar uso de recursos computacionales

## Cuándo Aplicar

- **Antes de cualquier tarea nueva**: Verificar skills disponibles
- **Al procesar archivos**: Usar @pdf, @xlsx, @csv-processor, etc.
- **Antes de crear scripts**: Consultar si existe una skill
- **Durante migraciones**: Validar herramientas disponibles

## Flujo de Trabajo

### Paso 1: Consultar Skills Disponibles

Lee el catálogo de skills antes de actuar:

```markdown
📂 Archivo obligatorio: core/skills/SKILLS.md
```

### Paso 2: Identificar Skill Apropiada

Busca en el índice de skills:
- **@csv-processor**: Procesamiento de CSV
- **@xlsx**: Generación de Excel
- **@pdf**: Extracción de PDF
- **@etl**: Transformación de datos
- **@docx**: Procesamiento de Word
- Y 15+ skills más...

### Paso 3: Decisión

| Condición | Acción |
|-----------|--------|
| Skill existe | **Usar la skill** ✅ |
| No existe skill | Crear script propio (documentar en ideas.md) |
| Recurrente | Considerar crear **nueva skill** |

## Herramientas y Recursos

### Scripts
- `core/scripts/skills-indexer.py`: Genera índice de skills
- `core/scripts/session-start.py`: Muestra skills disponibles

### Skills de Apoyo
- `@skill-discovery`: Identifica skills apropiadas
- `@skill-evaluator`: Evalúa calidad de skills

### Documentación
- [SKILLS.md](../core/skills/SKILLS.md) - Catálogo completo
- [AGENTS.md](../../AGENTS.md) - Router principal

## Ejemplos Prácticos

### Ejemplo 1: Procesar CSV

❌ **Incorrecto**: Crear script Python con pandas
```python
import pandas as pd
df = pd.read_csv('data.csv')  # No usar
```

✅ **Correcto**: Usar skill existente
```
Usa @csv-processor para limpiar y analizar data.csv
```

### Ejemplo 2: Generar Excel

❌ **Incorrecto**: Script con openpyxl
```python
from openpyxl import Workbook  # No usar
```

✅ **Correcto**: Usar skill existente
```
Usa @xlsx para crear el reporte con formato profesional
```

### Ejemplo 3: Extraer PDF

❌ **Incorrecto**: Script con PyPDF2
```python
import PyPDF2  # No usar
```

✅ **Correcto**: Usar skill existente
```
Usa @pdf para extraer el contenido del documento
```

## Mapeo Tarea → Skill

| Tipo de Tarea | Skill a Usar | NO Crear |
|---------------|--------------|----------|
| Procesar CSV | @csv-processor | Script pandas |
| Generar Excel | @xlsx | Script openpyxl |
| Transformar datos | @etl | Script custom |
| Extraer PDF | @pdf | Script PyPDF2 |
| Crear Word | @docx | Script python-docx |
| Visualizar datos | @data-viz | Script matplotlib |
| Procesar imágenes | @image-processor | Script PIL |
| Generar prompts | @json-prompt-generator | Template manual |

## Validación y Verificación

- [ ] ¿Consulté SKILLS.md antes de empezar?
- [ ] ¿La tarea coincide con alguna skill existente?
- [ ] ¿Estoy usando el recurso más apropiado?
- [ ] ¿Documenté por qué no uso una skill existente (si aplica)?

## Referencias

- [AGENTS.md](../../AGENTS.md) - Router principal del framework
- [SKILLS.md](../core/skills/SKILLS.md) - Catálogo de skills
- [Workflow Standard](../WORKFLOW-STANDARD.md) - Proceso de 7 pasos

## Changelog

### v0.2.0-prealpha (2026-03-11)
- Versión inicial simplificada para release público
- Sanitizado: eliminados datos de desarrollo interno
- Agregado: mapeo completo tarea→skill
- Agregado: ejemplos prácticos comparativos
