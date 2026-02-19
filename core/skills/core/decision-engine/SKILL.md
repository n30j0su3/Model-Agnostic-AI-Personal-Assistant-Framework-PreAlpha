---
id: decision-engine
name: Decision Engine
description: Evalua instrucciones con enfoque local-first y decide entre ejecucion local, delegacion a agentes o uso de LLM remoto. Usalo para optimizar contexto, cuota y resultados.
category: core
type: core
version: 1.0.0
license: MIT
metadata:
  author: FreakingJSON
  source: OBSOLETE/migration
compatibility: [OpenCode, Claude, Gemini, Codex]
---

# Decision Engine Skill

Skill central para decidir **como** ejecutar una instruccion: local, delegacion o LLM remoto.

## Objetivo
- Optimizar cuota, latencia y contexto.
- Delegar a agentes cuando sea mas eficiente.
- Usar LLM remoto solo cuando sea necesario.

## Entradas
- Instruccion del usuario (texto libre).
- Contexto actual (opcional).

## Flujo basico
1. Reglas locales (regex/politicas).
2. Delegacion explicita (mencion @agent).
3. Delegacion implicita (intencion/score).
4. Fallback a LLM remoto.

## Archivos clave
- `local-rules.json`: reglas locales.
- `agent-routing.json`: rutas de delegacion.
- `scripts/route.py`: router CLI (salida JSON).

## Comandos soportados

```bash
python core/skills/core/decision-engine/scripts/route.py "texto del usuario"
```

Opciones:
- `--explain`: incluye razonamiento resumido.
- `--list-rules`: lista reglas locales.
- `--list-agents`: lista agentes y keywords.

## Reglas de uso
- Si la instruccion no es clara, pedir aclaracion.
- Si la instruccion es sensible, requerir confirmacion del usuario antes de delegar o ejecutar.
