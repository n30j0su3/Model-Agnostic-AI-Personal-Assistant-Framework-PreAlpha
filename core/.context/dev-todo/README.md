# Dev To-do - Estructura Exclusiva prealpha-dev

Este directorio contiene el sistema de gestion de pendientes cotidianos para desarrolladores del framework.

## Archivos

- `todo.md` - Lista de pendientes de desarrollo

## Reglas

1. **Exclusivo prealpha-dev**: Este directorio NO se mergea a `base` o `prod`
2. **Diferente de backlog**: El backlog (`core/.context/codebase/backlog.md`) contiene features del framework
3. **Pendientes cotidianos**: El todo contiene tareas de desarrollo diarias (PRs, testing, fixes rapidos, etc.)

## Promocion a Backlog

Cuando una tarea del todo evoluciona a una feature del framework:

1. Crear item en backlog con `backlog-manager.py`
2. Marcar todo como completado
3. Referenciar el ID del backlog en el historial
