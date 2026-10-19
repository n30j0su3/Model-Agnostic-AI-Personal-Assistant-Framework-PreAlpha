---
name: paper-summarizer
description: Analiza y resume documentos tecnicos, papers cientificos o articulos extensos. Extrae metodologia, hallazgos clave y conclusiones. Usalo en el workspace @research.
license: MIT
metadata:
  author: FreakingJSON Framework
  version: "1.0"
compatibility: [OpenCode, Claude, Gemini, Codex]
---

# Paper Summarizer Skill

Este skill optimiza la lectura de documentos tecnicos para investigadores.

## Instrucciones para la IA

### 1. Análisis Estructurado
Al resumir un documento, busca siempre los siguientes puntos:
- **Problema**: ¿Qué problema intentan resolver?
- **Metodología**: ¿Cómo lo resolvieron? (Arquitectura, algoritmos, datasets).
- **Hallazgos Clave**: Los resultados más importantes.
- **Limitaciones**: ¿Qué falta por resolver?
- **Conclusión**: El veredicto final de los autores.

### 2. Flujo de Trabajo
1. El usuario proporciona un archivo (PDF convertido a texto o MD) o un link.
2. La IA lee el contenido y genera un resumen en el workspace `@research` (`workspaces/<research>/summary-[nombre].md`, si el workspace está habilitado en `data/user/workspaces.json`).
3. Registra la referencia del paper en el índice del workspace `@research`.

### 3. Comandos Soportados
- "Resume este paper @archivo"
- "¿Qué dice el análisis de [X] sobre la metodología?"
- "Extrae los puntos clave de este artículo"

## Scripts
- `scripts/summarize.py`: Script base para formatear el resumen.
