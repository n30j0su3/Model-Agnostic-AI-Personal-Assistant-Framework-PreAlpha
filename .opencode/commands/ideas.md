---
description: Abre/gestiona archivo de ideas del framework
agent: FreakingJSON
---

# Gestión de Ideas

**Propósito**: Centralizar y gestionar ideas, hallazgos y notas del usuario.

## Archivos

- **Principal**: core/.context/codebase/ideas.md
- **Backup**: core/.context/knowledge/insights/ (auto-generado)

## Comandos Soportados

### Sin argumentos
- Lee ideas.md completo
- Muestra últimas 10 ideas (orden cronológico inverso)

### Con argumentos
- `/ideas add "texto de la idea"` → Agrega nueva idea
- `/ideas list` → Lista todas las ideas
- `/ideas search "término"` → Busca en ideas existentes
- `/ideas archive` → Mueve ideas antiguas a archivo histórico

## Formato de Idea (MVI)

```markdown
### [YYYY-MM-DD HH:MM] Título Corto

- Descripción concisa (1-3 oraciones)
- Puntos clave (3-5 bullets máx)
- Referencias: [[archivo-relacionado.md]]
- Tags: #categoria #subcategoria
```

## Categorías Sugeridas

| Categoría | Ejemplo |
|-----------|---------|
| `#feature` | Nueva funcionalidad del framework |
| `#optimization` | Mejora de rendimiento/process |
| `#integration` | Integración con herramientas externas |
| `#documentation` | Mejoras en docs |
| `#bug` | Bug identificado |
| `#research` | Hallazgo de investigación |

## Integración con Knowledge Base

Las ideas frecuentemente referenciadas se promueven a:
- `core/.context/knowledge/insights/patterns.md`
- `core/.context/knowledge/projects/[nombre]/context.md`
