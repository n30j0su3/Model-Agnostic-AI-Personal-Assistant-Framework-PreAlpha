---
description: Muestra/crea sesión del día (formato .md local, NO sesión TUI de OpenCode)
agent: session-manager
---

# Gestión de Sesión Diaria

**Propósito**: Gestionar sesiones diarias en archivos `.md` locales (core/.context/sessions/).

**NOTA**: Este comando es DIFERENTE al `/session` de OpenCode CLI:
- OpenCode `/session` → Gestiona sesiones TUI (interactivas)
- Nuestro `/session` → Gestiona sesiones .md (persistencia local)

## Comandos Soportados

### Sin argumentos
- Si existe sesión para hoy: Muestra contenido
- Si NO existe: Crea nueva sesión con estructura estándar

### Con argumentos
- `/session create` → Fuerza creación de nueva sesión
- `/session show` → Solo muestra sesión actual
- `/session close` → Cierra sesión con resumen y métricas

## Estructura de Sesión

```markdown
# Sesión YYYY-MM-DD

## Inicio
- **Hora**: HH:MM
- **CLI**: ID de instancia

## Temas Tratados
- Lista de temas...

## Decisiones
- Decisiones tomadas...

## Pendientes Generados
- Nuevos pendientes...

## Resumen
- Resumen final...
```

## Archivos Relacionados
- core/.context/sessions/YYYY-MM-DD.md
- core/.context/codebase/ideas.md
- core/.context/codebase/recordatorios.md
