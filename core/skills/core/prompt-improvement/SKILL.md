---
name: prompt-improvement
description: Mejora prompts con estandares modernos (RAG, few-shot, JSON prompts) y criterios de calidad. Usalo en el workspace @development.
license: MIT
metadata:
  author: opencode
  version: "1.0"
compatibility: OpenCode, Claude Code, Gemini CLI, Codex
---

# Prompt Improvement Skill

Habilidad para diagnosticar y mejorar prompts con enfoque user-friendly, local-first y orientado a resultados.

## Entradas

- Prompt original (texto completo)
- Objetivo y resultado esperado
- Audiencia objetivo
- Restricciones (tiempo, formato, tono, longitud)
- Contexto disponible (archivos, herramientas, datos)

## Flujo de trabajo

1. Clarificar si falta informacion critica (objetivo, audiencia, criterios de exito).
2. Diagnosticar ambiguedad, contradicciones y vacios.
3. Reescribir en estructura clara (rol, tarea, contexto, restricciones, formato).
4. Crear 2 variantes con diferente nivel de detalle.
5. Verificar que el prompt sea accionable y medible.

## Estandares modernos

- Contexto explicito y delimitado.
- Few-shot cuando el usuario provee ejemplos o el formato es complejo.
- RAG-ready: incluye instrucciones para usar fuentes si es requerido y pedir aclaraciones si no hay datos.
- JSON prompts cuando el flujo requiera estructura o integracion con herramientas.
- Razonamiento interno: si el modelo lo soporta, indicar que piense antes de responder y entregue solo el resultado final.
- Guardrails: definir limites, formato de salida y criterios de calidad.

## Plantilla recomendada

```
Rol: [rol principal]
Tarea: [que debe hacer]
Contexto: [datos y fuentes]
Restricciones: [limites y reglas]
Formato de salida: [estructura exacta]
Criterios de calidad: [como evaluar]
```

## JSON prompt base

```
{
  "task": "",
  "context": "",
  "inputs": [],
  "constraints": [],
  "output_format": "",
  "quality_checks": []
}
```

## Formato de salida

1. Prompt mejorado (listo para copiar)
2. Variantes (2)
3. Notas breves de mejora

## Actualizacion programable

- Referencias en `skills/core/prompt-improvement/references.md`.
- Script: `python skills/core/prompt-improvement/scripts/update-references.py`.
- Sugerencia: programar ejecucion mensual con cron/Task Scheduler y revisar manualmente los cambios.

## Comandos soportados

- "Mejora este prompt: <texto>"
- "Refina este prompt para hacerlo mas claro"
- "Convierte este prompt a JSON"
