# Partials Reutilizables — @dashboard-pro

Componentes modulares para uso en ambos modos.

## HTML Partials (sin-dependencias)

| Archivo | Props Requeridas | Descripción |
|---------|------------------|-------------|
| `kpi-card.html` | title, metric, trend, icon, color | Tarjeta de métrica con tendencia |
| `chart-container.html` | title, id | Contenedor para Chart.js canvas |
| `data-table.html` | title?, columns[], id | Tabla HTML con thead estructurado |
| `theme-toggle.html` | — | Botón toggle dark/light |

## React/TS Partials (con-dependencias)

| Archivo | Props | Descripción |
|---------|-------|-------------|
| `theme-provider.tsx` | children, ThemeProviderProps | Provider de next-themes |
| `theme-toggle.tsx` | — | Botón toggle con iconos Sun/Moon |
| `utils.ts` | — | cn(), formatCurrency, formatNumber, formatPercentage, convertToRgba |

## Uso

### HTML
```html
<!-- Incluir partial -->
{{#each kpiCards}}
  {{include 'kpi-card' this}}
{{/each}}
```

### Next.js
```tsx
import{ThemeToggle}from"@/components/partials/theme-toggle";
import{formatCurrency}from"@/lib/utils";
```

## Variables Handlebars

Las variables usan sintaxis `{{variable}}` o `{{#each}}` loops.
Helpers disponibles: `{{json data}}`, `{{eq a b}}`.
