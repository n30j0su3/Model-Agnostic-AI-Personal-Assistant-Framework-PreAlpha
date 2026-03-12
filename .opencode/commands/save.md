---
description: Fuerza guardado de contexto actual en archivos .md locales
agent: doc-writer
---

# Guardado de Contexto

**Propósito**: Persistir conocimiento valioso de la conversación actual en archivos locales.

## ¿Qué se Guarda?

### 1. Decisiones
- Decisiones tomadas durante la sesión
- Justificaciones y alternativas consideradas
- Archivos modificados

### 2. Ideas y Hallazgos
- Ideas nuevas surgidas durante la sesión
- Descubrimientos relevantes
- URLs o referencias importantes

### 3. Pendientes
- Tareas identificadas pero no ejecutadas
- Follow-ups requeridos
- Dependencias externas

### 4. Código/Cambios
- Snippets de código importantes
- Cambios arquitectónicos
- Patrones identificados

## Destinos

| Tipo | Archivo Destino |
|------|-----------------|
| Decisiones | core/.context/sessions/YYYY-MM-DD.md |
| Ideas | core/.context/codebase/ideas.md |
| Pendientes | core/.context/codebase/recordatorios.md |
| Código | Según contexto (referenciar en sesión) |

## Formato MVI

- Máximo 1-3 oraciones por concepto
- 3-5 bullets por sección
- Ejemplo mínimo cuando aplique
- Referencia a docs completos, no duplicar contenido

## Confirmación

Después de guardar, confirmar:
- ✅ Archivos actualizados
- ✅ Cantidad de items guardados por categoría
- ✅ Próximos pasos sugeridos
