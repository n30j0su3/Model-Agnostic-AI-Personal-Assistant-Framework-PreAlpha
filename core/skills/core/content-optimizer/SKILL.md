---
id: content-optimizer
name: Content Optimizer
description: Optimiza borradores de texto para SEO, legibilidad y engagement. Ajusta el tono de voz y la estructura del contenido. Usalo en el workspace @content.
category: content
type: core
version: 1.0.0
license: MIT
metadata:
  author: FreakingJSON
  source: OBSOLETE/migration
compatibility: [OpenCode, Claude, Gemini, Codex]
---

# Content Optimizer Skill

Habilidad diseniada para maximizar el alcance y la claridad de tus textos.

## Instrucciones para la IA

### 1. Checklist de Optimización
- **SEO**: Presencia de palabras clave, etiquetas H1-H3 logicas, meta-descripciones.
- **Legibilidad**: Uso de voz activa, parrafos cortos, evitar jerga innecesaria.
- **Engagement**: Fuerza del Hook inicial, CTA (Call to Action) claro.
- **Tono**: Asegurar que coincida con la voz definida en `workspaces/content/CONTEXT.md`.

### 2. Flujo de Trabajo
1. Analizar el borrador actual en `workspaces/content/drafts/`.
2. Proporcionar un reporte de "Antes y Despues".
3. Sugerir 3 variaciones de titulos (Hooks) de alto impacto.

### 3. Comandos Soportados
- "Optimiza este post para SEO"
- "Revisa el tono de este guion"
- "Dame 5 ideas de titulos para @archivo"

## Scripts
- `scripts/seo-checker.py`: Script para validar densidad de keywords y estructura.
