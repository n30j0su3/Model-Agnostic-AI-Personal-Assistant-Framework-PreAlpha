# CONFIG — @dashboard-pro

Configuración y personalización de la skill.

## Presets de Estilo

| Preset | Background | Primary | Secondary | Uso |
|--------|------------|---------|-----------|-----|
| fintech-dark | #0B0D10 | #F5A623 | #22C55E | Exchanges, trading |
| fintech-light | #FFFFFF | #2563EB | #10B981 | Banking, corporate |
| saas-modern | #FAFAFA | #7C3AED | #EC4899 | SaaS, startups |
| enterprise | #F9FAFB | #374151 | #6B7280 | B2B, admin panels |

## Crear Preset Personalizado

```yaml
style_presets:
  mi-preset:
    colors:
      background: "#0F172A"
      primary: "#6366F1"
      secondary: "#8B5CF6"
      textPrimary: "#F8FAFC"
      textSecondary: "#94A3B8"
    style: ["modern", "gradient"]
```

Uso: `@dashboard-pro style-preset=mi-preset "Mi dashboard"`

## Layouts Disponibles

| Tipo | Configuración | Ideal Para |
|------|---------------|------------|
| sidebar | `{"type":"sidebar","sidebar":{"width":260,"collapsible":true}}` | Navegación compleja |
| top-nav | `{"type":"top-nav","topbar":{"height":64,"sticky":true}}` | Apps simples |
| sidebar+top | `{"type":"sidebar+top","sidebar":{},"topbar":{}}` | Dashboards enterprise |
| bento | `{"type":"bento","grid":{"columns":12,"gap":24}}` | Analytics, múltiples métricas |

## Componentes

### KPI Card
```json
{"id":"revenue","title":"Revenue","metric":"$125K","format":"currency","trend":{"value":12.5,"direction":"up"},"icon":"TrendingUp","color":"primary"}
```

### Charts
- **Recharts**: LineChart, AreaChart, BarChart, PieChart, RadarChart
- **Chart.js**: line, bar, pie, doughnut, polarArea, radar
- **ApexCharts**: Todos + heatmap, candlestick

### Table Column Types
`text|number|currency|percentage|date|badge|action`

## Chart Library Selection

| Librería | Peso | Pros | Ideal Para |
|----------|------|------|------------|
| Chart.js | ~60KB | Ligera, simple | Mayoría de dashboards |
| ApexCharts | ~80KB | Heatmaps, tooltips avanzados | Financiero complejo |
| Vanilla SVG | ~0KB | Cero deps | Simples, emails |

## Troubleshooting

**Tailwind no carga**: Verificar CDN `https://cdn.tailwindcss.com`
**Charts no renderizan**: Verificar IDs únicos, formato de datos
**Dark mode no funciona**: Verificar clase `dark` en `<html>`, `darkMode: 'class'`

## Referencias
- [Tailwind CSS](https://tailwindcss.com/docs)
- [Recharts](https://recharts.org)
- [Chart.js](https://www.chartjs.org)
- [shadcn/ui](https://ui.shadcn.com)
