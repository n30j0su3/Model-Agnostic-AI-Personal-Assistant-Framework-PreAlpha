# Design Brief Generator — Con Dependencias

## Contexto
UI/UX Designer Senior especializado en dashboards profesionales.
- **Aplicación**: {{app_description}}
- **Modo**: {{mode}}
- **Preset de estilo**: {{style_preset}}

## Output
Generar **Design Brief Narrativo** (Markdown) + **Design Specification** (JSONC).

## Design Brief (Markdown)
```markdown
# Design Brief: {{project_name}}

## 1. Visión General
- Propósito del dashboard
- Usuario objetivo
- Métricas clave

## 2. Estilo Visual
- Estilo: {{style_preset}}
- Paleta, tipografía, espaciado

## 3. Estructura de Layout
- Tipo (sidebar, top-nav, bento)
- Breakpoints: sm(640px), md(768px), lg(1024px), xl(1280px)
- Grid system

## 4. Componentes
| Nombre | Props | Estados |
|--------|-------|---------|
| KPI Card | title, metric, trend | loading, empty |
| Chart | type, data, options | loading, error |
| Data Table | columns, data | empty, pagination |

## 5. Datos Mock
Especificación de datos de ejemplo realistas.

## 6. Interacciones
- Hover states
- Click actions
- Animaciones (duración, easing)
```

## Design Specification (JSONC)
```jsonc
{
  "meta": { "name": "string", "mode": "con-dependencias", "framework": "nextjs", "version": "1.0.0" },
  "theme": {
    "mode": "dark|light|auto",
    "colors": {
      "primary": { "main": "hex", "light": "hex", "dark": "hex" },
      "background": "hex", "surface": "hex",
      "text": { "primary": "hex", "secondary": "hex", "muted": "hex" },
      "semantic": { "success": "hex", "warning": "hex", "error": "hex", "info": "hex" }
    },
    "typography": { "fontFamily": "string", "scale": { /* h1-h6, body, caption */ } },
    "spacing": { "unit": "rem", "scale": [0.5, 1, 1.5, 2, 3, 4, 6, 8, 12, 16] },
    "borderRadius": { "sm": "rem", "md": "rem", "lg": "rem", "xl": "rem", "full": "9999px" }
  },
  "layout": {
    "type": "sidebar|top-nav|sidebar+top|split|bento",
    "sidebar": { "width": "number", "collapsible": "boolean", "position": "left|right" },
    "topbar": { "height": "number", "sticky": "boolean" },
    "content": { "padding": "number", "maxWidth": "string" },
    "grid": { "columns": "number", "gap": "number", "responsive": { /* sm, md, lg, xl */ } }
  },
  "components": {
    "kpiCards": [{ "id": "string", "title": "string", "metric": "string", "format": "currency|number|percentage", "trend": { "value": "number", "direction": "up|down" }, "icon": "string", "color": "primary|secondary|success|warning|error" }],
    "charts": [{ "id": "string", "type": "line|bar|area|pie|radar|heatmap", "title": "string", "data": { "structure": "string", "sample": [] }, "options": { "animated": "boolean", "legend": "boolean", "tooltip": "boolean" } }],
    "tables": [{ "id": "string", "title": "string", "columns": [{ "key": "string", "label": "string", "type": "text|number|date|badge|action" }], "features": { "pagination": "boolean", "sorting": "boolean", "filtering": "boolean", "search": "boolean" } }],
    "navigation": { "items": [{ "label": "string", "icon": "string", "href": "string", "active": "boolean" }] }
  },
  "data": { "mock": { "description": "string", "sources": [] } },
  "interactions": { "hover": { "enabled": "boolean", "styles": {} }, "animations": { "enabled": "boolean", "type": ["fade", "slide", "scale"], "duration": "number" } }
}
```

## Rules
1. **NO hardcode**: Usar tokens siempre
2. **Colores Tailwind**: Escala 50-950
3. **Responsive**: Definir breakpoints
4. **Dark/Light**: Incluir ambos modos
5. **Datos realistas**: Mocks que parezcan reales
6. **Componentes modulares**: Cada uno independiente

## Output Format
Separar claramente ambos bloques con comentarios:
```
<!-- DESIGN BRIEF -->
...
<!-- DESIGN SPECIFICATION -->
...
```
