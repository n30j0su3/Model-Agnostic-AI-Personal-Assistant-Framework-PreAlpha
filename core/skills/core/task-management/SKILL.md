---
name: task-management
description: Sistema avanzado de gestión de tareas multidisciplinarias. Permite crear, categorizar por workspace y mover tareas entre archivos de contexto y la sesión actual.
license: MIT
metadata:
  author: opencode
  version: "1.0"
compatibility: OpenCode, Claude Code, Gemini CLI, Codex
---

# Task Management Skill

Este skill permite una gestión fluida de tareas a través de múltiples workspaces.

## Estándar de Etiquetado
Toda tarea debe seguir el formato:
`- [ ] Descripción de la tarea @workspace #prioridad`

Workspaces válidos:
- `@personal`
- `@professional`
- `@research`
- `@content`
- `@development`

Prioridades:
- `#high` (Urgente/Importante)
- `#medium` (Normal)
- `#low` (Backlog)

## Instrucciones para la IA

### 1. Captura de Tareas
Cuando el usuario mencione una tarea, identifica el workspace y la prioridad.
Si no se especifica, asume `@personal` y `#medium`.

### 2. Sincronización con SESSION.md
- Las tareas de alta prioridad (`#high`) deben sugerirse para la sesión actual.
- Al iniciar el día, el agente debe buscar tareas en los archivos `CONTEXT.md` de cada workspace y proponerlas.

### 3. Comandos Soportados
- "Añade [Tarea] a mi lista profesional" -> Crea tarea con `@professional`.
- "¿Qué tengo pendiente en investigación?" -> Filtra tareas por `@research`.
- "Esta tarea es urgente" -> Cambia etiqueta a `#high`.

## Scripts
- `scripts/manage-tasks.py`: Script para filtrar y mover tareas programáticamente.
