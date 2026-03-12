---
name: json-prompt-generator
description: Genera prompts JSON estructurados a partir de una idea inicial para IA, con objetivos y entregables claros.
license: MIT
metadata:
  author: opencode
  version: "1.0"
compatibility: OpenCode, Claude Code, Gemini CLI, Codex
---

# JSON Prompt Generator Skill

Habilidad para convertir ideas vagas de prompt en instrucciones JSON claras, listas para usar.

## Instrucciones para la IA

### 1. Contexto y objetivos
- Recibe la "Idea de prompt" como entrada.
- Determina el objetivo del usuario, el tipo de contexto (tecnico, creativo, analitico, etc.) y los entregables esperados.

### 2. Estructura y formato
- Traduce la idea a un JSON con campos claros y, cuando aplique, objetos anidados.
- Incluye parametros clave: tarea, audiencia, tono, estilo, longitud, restricciones y formato de salida.
- Evita texto redundante y mantiene valores concretos.

### 3. Ejemplo de conversion

text prompt: Write a marketing email for our new AI course. Make it exciting but professional. Include the price which is $299. Mention the 30-day guarantee. Keep it short but compelling. Use a friendly tone. Add urgency.

JSON prompt:
{
  "task": "Create marketing email",
  "product": {
    "name": "AI Mastery Course",
    "price": "$299",
    "guarantee": "30-day money-back"
  },
  "tone": "friendly and professional",
  "style": "exciting but trustworthy",
  "length": "under 200 words",
  "urgency": "limited-time offer",
  "call_to_action": "Enroll now"
}

### 4. Recursos adicionales
- Usa deep research y servidores MCP si estan disponibles.
- Documentacion y ejemplos de estructura: https://mpgone.com/json-prompt-guide/
- Ideas de prompt tradicionales: https://docsbot.ai/prompts/programming

### 5. Formato de salida
- Devuelve solo JSON valido, sin markdown ni comentarios.

## Comandos soportados
- "Crea un json-prompt para: <idea>"
- "Convierte esta idea en un prompt JSON: <idea>"
