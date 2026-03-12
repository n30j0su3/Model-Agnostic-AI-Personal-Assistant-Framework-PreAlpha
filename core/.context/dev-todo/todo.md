# Dev To-do - Exclusivo prealpha-dev

Ultima actualizacion: 2026-02-19

> **NOTA**: Este archivo es exclusivo de la rama `prealpha-dev`.
> No se sincroniza con `base` ni `prod`.
> Gestiona pendientes cotidianos del desarrollo del framework.

## Versionado

- Estandar: TD-XXX (To-Do)
- Formato: Tabla con columna Tags para categorizacion

## Historial de cambios

- 2026-02-19: Estructura inicial creada para gestion de pendientes de desarrollo cotidianos.

## To-do Items

| ID | Item | Prioridad | Estado | Tags | Criterios de aceptacion |
| --- | --- | --- | --- | --- | --- |
| TD-001 | Ejemplo de tarea de desarrollo | Media | Pendiente | ejemplo | Criterio de ejemplo para ilustrar formato |
| TD-002 | Test: Verificar integridad del sistema dual | Alta | Pendiente | test,system | El sistema debe listar, agregar y actualizar items correctamente en ambos tipos |
| TD-003 | Actualizar CHANGELOG.md con cambios de sesion 2026-02-19 | Alta | Pendiente | docs,sync | Incluir: Vitals Guardian, Sistema Dual Backlog/To-do, Instruccion Vital-Core (BL-131), nuevas skills |
| TD-004 | Actualizar README.md en PROD con nuevas skills y features | Alta | Pendiente | docs,readme | Agregar: content-optimizer, context-evaluator, decision-engine, mcp-builder, paper-summarizer, Vitals Guardian, Backlog/To-do system |

## Tags Disponibles

- `bug` - Correcciones urgentes
- `feature` - Pequenas mejoras no documentadas en backlog
- `docs` - Documentacion interna
- `refactor` - Refactorizacion de codigo
- `test` - Tareas de testing
- `research` - Investigacion/exploracion
- `sync` - Sincronizacion entre ramas
- `review` - Revision de PRs/code
- `setup` - Configuracion de entorno
- `misc` - Miscelaneos

## Uso

```bash
# Listar items del todo
python core/scripts/backlog-manager.py list --type todo

# Agregar nuevo item
python core/scripts/backlog-manager.py add --type todo --item "Descripcion" --priority Alta --tags "bug,urgente" --criteria "Criterio de aceptacion"

# Actualizar item
python core/scripts/backlog-manager.py update TD-001 --status "En Progreso"
```
