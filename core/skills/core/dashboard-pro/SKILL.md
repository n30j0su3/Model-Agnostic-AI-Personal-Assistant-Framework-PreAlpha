# dashboard-pro — Skill

---
id: dashboard-pro
name: Dashboard Pro
description: Genera dashboards profesionales con diseño consistente usando design tokens y component library. Genera Design Brief, código y IMPLEMENTATION.md. Usalo cuando necesites visualizar datos o métricas.
category: dev
type: core
version: 1.0.0
license: MIT
metadata:
  author: FreakingJSON
  source: dashboard-pro/integration
compatibility: [OpenCode, Claude, Gemini, Codex]
---

# Dashboard Pro Skill

Habilidad para generar dashboards profesionales con diseño consistente.

## Instrucciones para la IA

### 1. Flujo de Trabajo
1. Leer los design tokens desde `schemas/design-tokens.json`.
2. Seleccionar componentes del `schemas/component-library.json`.
3. Generar un **Design Brief** antes del código (modo, estilo, datos).
4. Generar el código del dashboard según el brief.
5. Escribir `IMPLEMENTATION.md` documentando decisiones.

### 2. Modos
- `sin-dependencias`: HTML/CSS/JS vanilla autocontenido (file:// safe).
- `con-dependencias`: App existente (Next.js, React) con componentes.

### 3. Comandos Soportados
- "Genera un dashboard de [datos] con @dashboard-pro"
- "Dashboard sin dependencias para [métricas]"
- "Usa el style preset [nombre]"

## Referencias
- `INTEGRATION.md`: Integración con FeatureArchitect.
- `OPTIMIZATION-REPORT.md`: Reporte de optimización del component library.
- `scripts/optimize-templates.py`: Optimizador de templates.
