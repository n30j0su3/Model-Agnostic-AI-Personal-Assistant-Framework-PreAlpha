# Personal Assistant Agents Index

> Índice central de agentes del framework. Los agentes se definen en archivos `.md` con YAML frontmatter.

## Arquitectura

```
Main Agent (pa-assistant)
├── ContextScout      → Descubrimiento de contexto (read-only)
├── SessionManager    → Gestión de sesiones diarias
└── DocWriter         → Documentación automática
```

## Agente Principal

### @pa-assistant
- **Propósito**: Asistente personal principal. Orquesta sesiones, contexto y delegación.
- **Archivo**: `pa-assistant.md`
- **Estado**: OPERATIVO
- **Dependencias**: context-scout, session-manager, doc-writer

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

---

## Jerarquía de Delegación

```
Usuario → pa-assistant → [Comprende tarea]
                        ├── ContextScout (¿qué contexto necesito?)
                        ├── Ejecuta directamente (tareas simples)
                        ├── SessionManager (gestión de sesión)
                        └── DocWriter (documentación)
```

## Crear Nuevo Agente

1. Crear archivo `.md` en `subagents/` con YAML frontmatter
2. Definir: `id`, `name`, `description`, `type: subagent`, `tools`, `permissions`
3. Agregar referencia en este archivo (AGENTS.md)
4. Agregar dependencia en `pa-assistant.md` si aplica
