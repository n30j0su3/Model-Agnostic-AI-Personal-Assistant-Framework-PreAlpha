# Skills Index

> Catálogo de habilidades modulares del framework. Cada skill es invocable por agentes o el usuario.

## Core Skills

| Skill | Descripción | Ubicación |
|-------|-------------|-----------|
| **@task-management** | Gestión de tareas y seguimiento | `core/skills/core/task-management/` |
| **@pdf** | Procesamiento de archivos PDF | `core/skills/core/pdf/` |
| **@xlsx** | Procesamiento de hojas de cálculo | `core/skills/core/xlsx/` |
| **@prompt-improvement** | Optimización y refinamiento de prompts | `core/skills/core/prompt-improvement/` |
| **@ui-ux-pro-max** | Diseño inteligente UI/UX con base de datos buscable | `core/skills/core/ui-ux-pro-max/` |
| **@docx** | Toolkit for creating, editing, and analyzing Word documents. | `core/skills/core/docx/` |
| **@etl** | Manipulación y transformación de datos (Extract, Transform, Load) | `core/skills/core/etl/` |
| **@json-prompt-generator** | Genera prompts JSON estructurados a partir de una idea inicial para IA | `core/skills/core/json-prompt-generator/` |
| **@pptx** | Creación, edición y análisis de presentaciones PowerPoint | `core/skills/core/pptx/` |
| **@data-viz** | Visualización de datos con Seaborn/Matplotlib | `core/skills/core/data-viz/` |
| **@prd-generator** | Generación de Product Requirements Documents con historias de usuario | `core/skills/core/prd-generator/` |
| **@skill-creator** | Guía completa para crear nuevas skills en el framework | `core/skills/core/skill-creator/` |
| **@markdown-writer** | Toolkit para escribir Markdown consistente siguiendo MVI | `core/skills/core/markdown-writer/` |
| **@csv-processor** | Procesamiento de CSV para limpieza, transformación y análisis | `core/skills/core/csv-processor/` |
| **@python-standards** | Estándares cross-platform para scripts Python | `core/skills/core/python-standards/` |
| **@skill-discovery** | Helper para identificar skills apropiadas y evitar scripts duplicados | `core/skills/core/skill-discovery/` |
| **@content-optimizer** | Optimiza borradores de texto para SEO, legibilidad y engagement | `core/skills/core/content-optimizer/` |
| **@context-evaluator** | Framework para evaluar calidad de respuestas (LLM-as-a-Judge) | `core/skills/core/context-evaluator/` |
| **@dashboard-pro** | Genera dashboards profesionales con diseño consistente | `core/skills/core/dashboard-pro/` |
| **@decision-engine** | Decide entre ejecución local, delegación o LLM remoto | `core/skills/core/decision-engine/` |
| **@mcp-builder** | Guía para crear MCP servers con buenas prácticas | `core/skills/core/mcp-builder/` |
| **@paper-summarizer** | Analiza y resume papers científicos y documentos técnicos | `core/skills/core/paper-summarizer/` |
| **@error-recovery** | Self-healing error handling con recovery playbooks | `core/skills/core/error-recovery/` |

## Gate tarea→skill (obligatorio)

> **Antes de crear o modificar cualquier archivo**, mapea la tarea contra este catálogo y la tool `skill`. Si existe una skill aplicable, cárgala y úsala; si ninguna aplica, dilo explícitamente antes de escribir. No crees scripts ad-hoc sin pasar por `skill-discovery`.

## Uso Recomendado: Skill Discovery First

> **⚠️ ANTES de crear cualquier script**, consulta `@skill-discovery` para verificar
> si existe una skill que resuelva tu necesidad. Esto evita duplicar funcionalidad.

```
1. Lee: core/skills/core/skill-discovery/SKILL.md
2. Identifica la skill apropiada para tu tarea
3. Usa la skill existente en lugar de crear scripts ad-hoc
```

## Cómo Invocar

En OpenCode, las skills se cargan con la tool nativa `skill` usando el nombre de la skill (por ejemplo, `pdf`). En otros CLIs, usa `@nombre` según su convención:

```
Usa la skill pdf para extraer el contenido de este archivo.
Usa la skill task-management para crear una nueva tarea.
Usa la skill skill-discovery para encontrar la skill apropiada.
```

## Crear Nuevo Skill

1. Crear directorio en `core/skills/core/{nombre}/`
2. Crear `SKILL.md` con instrucciones, descripción y frontmatter YAML
3. Agregar entrada en este archivo (SKILLS.md)
4. Opcionalmente agregar scripts de soporte en `scripts/`
