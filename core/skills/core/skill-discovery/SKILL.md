---
id: skill-discovery
name: Skill Discovery Helper
description: Helper para identificar skills apropiadas para tareas comunes y evitar crear scripts innecesarios
category: core
type: helper
version: 1.0.0
---

# Skill Discovery Helper

## Propósito

Este helper ayuda a identificar la skill apropiada para una tarea, evitando crear scripts innecesarios que dupliquen funcionalidad existente.

## Mapeo Rápido: Tarea → Skill

### Procesamiento de Datos

| Tarea | Skill | Ubicación | Ejemplo de Uso |
|-------|-------|-----------|----------------|
| Procesar CSV | @csv-processor | `core/skills/core/csv-processor/` | Limpiar, transformar, analizar CSV |
| Generar Excel | @xlsx | `core/skills/core/xlsx/` | Crear hojas de cálculo con formato |
| Transformar datos | @etl | `core/skills/core/etl/` | ETL: Extract, Transform, Load |
| Visualizar datos | @data-viz | `core/skills/core/data-viz/` | Gráficos con Seaborn/Matplotlib |

### Documentos

| Tarea | Skill | Ubicación | Ejemplo de Uso |
|-------|-------|-----------|----------------|
| Extraer PDF | @pdf | `core/skills/core/pdf/` | Leer contenido de PDFs |
| Crear Word | @docx | `core/skills/core/docx/` | Generar documentos .docx |
| Crear PowerPoint | @pptx | `core/skills/core/pptx/` | Generar presentaciones |
| Escribir Markdown | @markdown-writer | `core/skills/core/markdown-writer/` | Markdown consistente con MVI |

### Productividad

| Tarea | Skill | Ubicación | Ejemplo de Uso |
|-------|-------|-----------|----------------|
| Gestión de tareas | @task-management | `core/skills/core/task-management/` | Crear, tracking, recordatorios |
| Mejorar prompts | @prompt-improvement | `core/skills/core/prompt-improvement/` | Optimizar prompts para IA |
| Generar PRD | @prd-generator | `core/skills/core/prd-generator/` | Product Requirements Documents |

### Desarrollo

| Tarea | Skill | Ubicación | Ejemplo de Uso |
|-------|-------|-----------|----------------|
| Estándares Python | @python-standards | `core/skills/core/python-standards/` | Cross-platform scripts |
| Diseño UI/UX | @ui-ux-pro-max | `core/skills/core/ui-ux-pro-max/` | Diseño con base de datos buscable |
| Crear nueva skill | @skill-creator | `core/skills/core/skill-creator/` | Guía para crear skills |
| Evaluar contexto | @context-evaluator | `core/skills/core/context-evaluator/` | Analizar archivos de contexto |

## Cómo Usar una Skill

### 1. Leer el SKILL.md

```
read: core/skills/core/{nombre}/SKILL.md
```

### 2. Invocar por nombre

```
@skill-name

"Usa @csv-processor para limpiar este archivo CSV"
```

### 3. Seguir instrucciones específicas

Cada skill tiene su propio protocolo de uso documentado en su SKILL.md.

## Anti-Patrones (Qué NO Hacer)

### ❌ Anti-Patrón #1: Script ad-hoc para CSV

```python
# MAL: Crear esto...
import pandas as pd
df = pd.read_csv('data.csv')
df.to_excel('output.xlsx')

# BIEN: Usar skill existente
@csv-processor → transform → @xlsx
```

### ❌ Anti-Patrón #2: Script para PDF

```python
# MAL: Instalar PyPDF2 y crear script...
import PyPDF2
reader = PyPDF2.PdfReader('doc.pdf')

# BIEN: Usar skill existente
@pdf → extract
```

### ❌ Anti-Patrón #3: Excel manual

```python
# MAL: Usar openpyxl directamente...
from openpyxl import Workbook
wb = Workbook()

# BIEN: Usar skill existente
@xlsx → create
```

## Decision Tree

```
¿Necesito procesar datos?
├── CSV → @csv-processor
├── Excel → @xlsx
├── Transformación compleja → @etl
└── Visualización → @data-viz

¿Necesito documentos?
├── PDF → @pdf
├── Word → @docx
├── PowerPoint → @pptx
└── Markdown → @markdown-writer

¿Necesito productividad?
├── Tareas → @task-management
├── Mejorar prompts → @prompt-improvement
└── PRD → @prd-generator

¿No existe skill para mi tarea?
├── Crear script propio (justificado)
└── Considerar crear nueva skill @skill-creator
```

## Verificación Rápida

Antes de crear cualquier script, pregúntate:

1. **¿He revisado `core/skills/SKILLS.md`?**
2. **¿Existe una skill para esta tarea?**
3. **¿Estoy duplicando funcionalidad?**

Si la respuesta a #2 es "Sí" → **Usar la skill.**  
Si la respuesta a #2 es "No" → Crear script o considerar nueva skill.

## Contacto

Para agregar nuevas skills al índice, actualizar este archivo y `core/skills/SKILLS.md`.

---

*"No reinventes la rueda. Usa las skills del framework."*  
*— Principio DRY, FreakingJSON-PA*
