# Personal Assistant Agents Index

> Índice central de agentes del framework. Los agentes se definen en archivos `.md` con YAML frontmatter.

## Arquitectura

```
Main Agent (pa-assistant)
├── ContextScout      → Descubrimiento de contexto (read-only)
├── SessionManager    → Gestión de sesiones diarias
├── DocWriter         → Documentación automática
└── FeatureArchitect  → Arquitecto de producto (dev-only)
```

## Agente Principal

### @pa-assistant
- **Propósito**: Asistente personal principal. Orquesta sesiones, contexto y delegación.
- **Archivo**: `pa-assistant.md`
- **Estado**: OPERATIVO
- **Dependencias**: context-scout, session-manager, doc-writer, feature-architect

## Subagentes

### @context-scout
- **Propósito**: Descubre y recomienda archivos de contexto. Read-only.
- **Archivo**: `subagents/context-scout.md`
- **Estado**: OPERATIVO

### @session-manager
- **Propósito**: Crea, gestiona y cierra sesiones diarias.
- **Archivo**: `subagents/session-manager.md`
- **Estado**: OPERATIVO

### @doc-writer
- **Propósito**: Genera documentación de sesiones y conocimiento.
- **Archivo**: `subagents/doc-writer.md`
- **Estado**: OPERATIVO

### @feature-architect
- **Propósito**: Arquitecto de producto y guardián de la filosofía. Evalúa, planea y ejecuta features del backlog sin solapamientos.
- **Archivo**: `subagents/feature-architect.md`
- **Estado**: OPERATIVO
- **Modo**: DEV-ONLY (no disponible en producción)
- **Dependencias**: prd-generator, task-management

---

## Jerarquía de Delegación

```
Usuario → pa-assistant → [Comprende tarea]
                        ├── ContextScout (¿qué contexto necesito?)
                        ├── Ejecuta directamente (tareas simples)
                        ├── SessionManager (gestión de sesión)
                        ├── DocWriter (documentación)
                        └── FeatureArchitect (arquitectura de features - dev)
```

## Crear Nuevo Agente

1. Crear archivo `.md` en `subagents/` con YAML frontmatter
2. Definir: `id`, `name`, `description`, `type: subagent`, `tools`, `permissions`
3. Agregar referencia en este archivo (AGENTS.md)
4. Agregar dependencia en `pa-assistant.md` si aplica
