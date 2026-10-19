# Evals Schema — @skill-creator

> Schema JSON de los archivos de evaluacion generados por `@skill-evaluator` y consumidos por `eval-viewer/`.

## Ubicacion

- Test cases de una skill: `evals/evals.json`
- Ejemplo de referencia: `evals/example-evals.json`
- Datos del visualizador: `eval-viewer/review-data.json`

## Estructura

El archivo es un **array** de objetos de evaluacion:

```json
[
  {
    "skill": "@nombre-skill",
    "evaluated_at": "2026-03-11T10:30:00Z",
    "mode": "full",
    "scores": {
      "mvi_compliance": 95,
      "clarity": 92,
      "completeness": 88,
      "actionability": 94,
      "cross_platform": 90
    },
    "overall": 92,
    "grade": "A",
    "feedback": "Texto libre con la justificacion del puntaje.",
    "suggestions": ["Mejora 1", "Mejora 2"]
  }
]
```

## Campos

| Campo | Tipo | Requerido | Descripcion |
|-------|------|-----------|-------------|
| `skill` | string | Si | Identificador de la skill (`@slug`) |
| `evaluated_at` | string (ISO 8601) | Si | Fecha/hora de la evaluacion |
| `mode` | enum | Si | `full` o `simplified` |
| `scores` | object | Si | Puntajes 0-100 por criterio |
| `overall` | number | Si | Puntaje global 0-100 |
| `grade` | enum | Si | `A` (90-100), `B` (80-89), `C` (70-79), `D` (50-69), `F` (0-49) |
| `feedback` | string | Si | Justificacion del resultado |
| `suggestions` | array de string | No | Mejoras accionables |

## Criterios por modo

- **full**: `mvi_compliance` (25%), `clarity` (25%), `completeness` (20%), `actionability` (20%), `cross_platform` (10%).
- **simplified**: `mvi_compliance` (35%), `clarity` (35%), `completeness` (30%).

Ver escala y flujo completo en `SKILL.md`.
