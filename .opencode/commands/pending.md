---
description: Muestra/gestiona pendientes y recordatorios del framework
agent: task-management
---

# Gestión de Pendientes

**Propósito**: Centralizar y gestionar tareas pendientes y recordatorios.

## Archivos

- **Principal**: core/.context/codebase/recordatorios.md
- **Histórico**: core/.context/knowledge/insights/trends.md (estadísticas)

## Comandos Soportados

### Sin argumentos
- Lee recordatorios.md completo
- Muestra pendientes agrupados por estado

### Con argumentos
- `/pending list` → Lista todos los pendientes
- `/pending add "texto del pendiente"` → Agrega nuevo pendiente
- `/pending complete [ID]` → Marca pendiente como completado
- `/pending search "término"` → Busca en pendientes existentes
- `/pending archive` → Mueve completados a archivo histórico

## Formato de Pendiente

```markdown
### Pendientes Activos

- [ ] **[ID]** Descripción del pendiente
  - Prioridad: Alta | Media | Baja
  - Categoría: #feature #bug #docs #optimization
  - Fecha creación: YYYY-MM-DD
  - Dependencias: [ID-referencia]

### Completados (Esta Semana)

- [x] **[ID]** Descripción
  - Completado: YYYY-MM-DD
  - Notas: Breve descripción del resultado
```

## Integración con Skills

Este comando usa la skill `@task-management` para:
- Priorización automática
- Detección de dependencias
- Estimación de esfuerzo
- Seguimiento de tiempo

## Métricas

Al mostrar pendientes, incluir:
- Total activos
- Completados esta semana
- Completados este mes
- Tasa de completitud (%)
