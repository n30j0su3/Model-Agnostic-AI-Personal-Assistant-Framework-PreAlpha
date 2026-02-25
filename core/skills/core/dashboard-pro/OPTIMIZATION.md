# OPTIMIZACIÓN — @dashboard-pro

## Resultados de Optimización

| Archivo | Original | Optimizado | Reducción |
|---------|----------|------------|-----------|
| base-template.html | 6,209 B | 4,451 B | **28.3%** |
| layout.tsx | 762 B | 586 B | **23.1%** |
| globals.css | 2,078 B | 1,789 B | **13.9%** |
| theme-provider.tsx | 332 B | 301 B | **9.3%** |
| theme-toggle.tsx | 692 B | 577 B | **16.6%** |
| utils.ts | 1,127 B | 888 B | **21.2%** |
| **Total Next.js** | **4,991 B** | **4,141 B** | **17.0%** |
| design-brief.md (con-deps) | ~8,500 B | ~2,800 B | **67%** |
| design-brief.md (sin-deps) | ~3,500 B | ~1,200 B | **66%** |
| **TOTAL SKILL** | **125,298 B** | **~82,000 B** | **~35%** |

## Técnicas Aplicadas

1. **HTML**: Eliminar espacios, comentarios, saltos de línea
2. **TSX**: Imports inline, tipos simplificados, props en línea
3. **CSS**: Variables compactas, sin espacios post-`:` y `;`
4. **JS**: Funciones arrow compactas, operadores booleanos (`!0`)
5. **Markdown**: Tablas, listas concisas, eliminar redundancias

## Estructura

```
dashboard-pro/
├── modes/
│   ├── sin-dependencias/templates/chart-js/
│   │   ├── base-template.html (original)
│   │   ├── partials/
│   │   └── .optimized/ (minificado)
│   └── con-dependencias/templates/nextjs-dashboard/
│       ├── app/, components/, lib/ (originales)
│       ├── partials/
│       └── .optimized/ (minificados)
├── partials/ (compartidos entre modos)
│   ├── *.html (vanilla)
│   ├── *.tsx (React)
│   └── README.md
└── prompts optimizados
```

## Uso

### Producción (rápido)
Usar archivos de `.optimized/`

### Desarrollo (debug)
Usar archivos originales

### Build Automático
```bash
python core/skills/core/dashboard-pro/scripts/optimize-templates.py
```

## Variables Preservadas

- `{{project_name}}`, `{{project_title}}`
- `{{colors.primary.main}}`
- `{{#each kpiCards}}`, `{{json kpiData}}`
- `{{default_theme}}`

## Partials Reutilizables

| Partial | HTML | React |
|---------|------|-------|
| KPI Card | ✅ | — |
| Chart Container | ✅ | — |
| Data Table | ✅ | — |
| Theme Toggle | ✅ | ✅ |
| Theme Provider | — | ✅ |
| Utils | — | ✅ |

## Próximas Optimizaciones

- Compresión Gzip/Brotli (60-80% adicional)
- Pre-compilar Handlebars
- Tree shaking en utils.ts
- CSS Purge para Tailwind
