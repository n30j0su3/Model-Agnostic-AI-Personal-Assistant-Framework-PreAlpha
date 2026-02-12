# Skills Index

> Catálogo de habilidades modulares del framework. Cada skill es invocable por agentes o el usuario.

## Core Skills

| Skill | Descripción | Ubicación |
|-------|-------------|-----------|
| **@task-management** | Gestión de tareas y seguimiento | `core/task-management/` |
| **@pdf** | Procesamiento de archivos PDF | `core/pdf/` |
| **@xlsx** | Procesamiento de hojas de cálculo | `core/xlsx/` |
| **@prompt-improvement** | Optimización y refinamiento de prompts | `core/prompt-improvement/` |
| **@ui-ux-pro-max** | Diseño inteligente UI/UX con base de datos buscable | `core/ui-ux-pro-max/` |
| **@docx** | Toolkit for creating, editing, and analyzing Word documents. | `core/docx/` |
| **@etl** | Diseño inteligente UI/UX con base de datos buscable | `core/etl/` |
| **@json-prompt-generator** | Diseño inteligente UI/UX con base de datos buscable | `core/json-prompt-generator/` |
| **@pptx** | Diseño inteligente UI/UX con base de datos buscable | `core/pptx/` |
| **@data-viz** | Visualización de datos con Seaborn/Matplotlib | `core/data-viz/` |
| **@prd-generator** | Generación de Product Requirements Documents con historias de usuario | `core/prd-generator/` |
| **@skill-creator** | Guía completa para crear nuevas skills en el framework | `core/skill-creator/` |
| **@markdown-writer** | Toolkit para escribir Markdown consistente siguiendo MVI | `core/markdown-writer/` |
| **@csv-processor** | Procesamiento de CSV para limpieza, transformación y análisis | `core/csv-processor/` |
| **@python-standards** | Estándares cross-platform para scripts Python | `core/python-standards/` |

## Cómo Invocar

Desde una sesión AI, menciona el skill:
```
Usa @pdf para extraer el contenido de este archivo.
Usa @task-management para crear una nueva tarea.
```

## Crear Nuevo Skill

1. Crear directorio en `core/skills/core/{nombre}/`
2. Crear `SKILL.md` con instrucciones, descripción y frontmatter YAML
3. Agregar entrada en este archivo (SKILLS.md)
4. Opcionalmente agregar scripts de soporte en `scripts/`
