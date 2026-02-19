---
id: context-evaluator
name: Context Evaluator
description: Framework para evaluar la calidad de las respuestas de los agentes mediante el patron "LLM-as-a-Judge". Permite comparacion de respuestas y evaluacion contra rubricas.
category: core
type: core
version: 1.0.0
license: MIT
metadata:
  author: FreakingJSON
  source: OBSOLETE/migration
compatibility: [OpenCode, Claude, Gemini, Codex]
---

# Context Evaluator Skill

Esta skill implementa tecnicas avanzadas de evaluacion de agentes, permitiendo medir la precision, coherencia y adherencia a la filosofia del framework.

## Objetivos
- Evaluar respuestas individuales contra rubricas especificas.
- Realizar comparaciones "pairwise" entre dos respuestas para determinar cual es mejor.
- Identificar degradacion de contexto o alucinaciones.

## Protocolo "LLM-as-a-Judge"

Cuando se requiere evaluar una respuesta, se deben seguir estos pasos:
1. **Definicion de Rubrica**: Cargar los criterios de evaluacion (ej: precision tecnica, tono user-friendly).
2. **Evaluacion Directa**: Asignar un puntaje (1-5) y una justificacion por cada criterio.
3. **Sugerencias de Mejora**: Identificar que falto para alcanzar el puntaje maximo.

## Rubricas Disponibles
- `rubrics/general.json`: Evaluacion de proposito general.
- `rubrics/technical.json`: Enfoque en precision de codigo y arquitectura.
- `rubrics/ux.json`: Enfoque en claridad y tono para el usuario.

## Herramientas

### `scripts/evaluate.py`
CLI para ejecutar evaluaciones desde la terminal o scripts de automatizacion.

```bash
python core/skills/core/context-evaluator/scripts/evaluate.py --prompt "..." --response "..." --rubric general
```

## Reglas de Calidad
- Las evaluaciones deben ser objetivas y basadas en evidencia.
- Siempre incluir una justificacion clara para cada puntaje.
- Identificar sesgos en la evaluacion si se detectan.
