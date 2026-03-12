# INTEGRACIÓN — FeatureArchitect ↔ Dashboard-Pro

Integración para generación de dashboards como parte de features.

## Flujo de Integración

```
Usuario solicita feature
    ↓
FeatureArchitect detecta keywords [dashboard, analytics, métricas, gráficos]
    ↓
Evaluación: ¿Complejidad? ¿App existente?
    ↓
Delegación a @dashboard-pro con inputs:
  - app_description (del PRD)
  - mode: con-dependencias|sin-dependencias
  - style_preset
  - feature_id
    ↓
Dashboard-pro genera Design Brief + Código + IMPLEMENTATION.md
    ↓
FeatureArchitect integra entregables en workspace
```

## Determinación de Modo

| Contexto | Modo Recomendado |
|----------|------------------|
| Prototipo/MVP | sin-dependencias |
| App Next.js existente | con-dependencias |
| Reporte puntual | sin-dependencias |
| Producto completo | con-dependencias |

## Inputs (FA → Dashboard-pro)

| Campo | Tipo | Requerido |
|-------|------|-----------|
| app_description | string | Sí |
| mode | enum | Sí |
| chart_library | enum | No |
| style_preset | enum | No |
| context.feature_id | string | No |

## Outputs (Dashboard-pro → FA)

```json
{
  "status": "success|partial|failed",
  "feature_id": "BL-042",
  "deliverables": {
    "design_brief": "workspaces/dashboards/BL-042/design-brief.jsonc",
    "dashboard_code": "workspaces/dashboards/BL-042/dashboard/",
    "implementation_notes": "workspaces/dashboards/BL-042/IMPLEMENTATION.md"
  },
  "metrics": {
    "complexity_score": 7,
    "lines_of_code": 1250,
    "components_count": 8
  }
}
```

## Casos de Uso

### Caso 1: Dashboard Analytics E-commerce
- **Input**: "Dashboard con revenue diario, conversión por canal, DAU/MAU"
- **Modo**: con-dependencias
- **Preset**: fintech-dark

### Caso 2: Reporte Ventas Rápido
- **Input**: "Reporte visual Q4 para reunión de mañana"
- **Modo**: sin-dependencias
- **Preset**: enterprise

### Caso 3: Feature CRM Compleja
- **Estrategia**: Dividir en sub-features
  - BL-050: Gestión leads
  - BL-051: Pipeline
  - BL-052: Dashboard métricas (dashboard-pro)

## Modificaciones en FeatureArchitect

### Agregar Dependencia
```yaml
dependencies:
  - skill:prd-generator
  - skill:task-management
  - skill:dashboard-pro  # NUEVO
```

### Extender The Filter (Paso 5)
```markdown
### Paso 5: Skills Especializadas

**Detección Dashboard**:
- [ ] ¿Keywords de dashboard?
- [ ] Verificar skill:dashboard-pro disponible
- [ ] Determinar modo: sin-dependencias | con-dependencias
- [ ] Agregar a PRD: "Integración Dashboard-Pro"
```

## Mejores Prácticas

1. **Verificar catalog.json** antes de delegar
2. **Preferir sin-dependencias** para prototipos
3. **Documentar decisiones** en IMPLEMENTATION.md
4. **Un dashboard por feature**: Dividir si es complejo
5. **Mantener consistencia**: Reutilizar style_presets
