---
id: paper-summarizer
name: Paper Summarizer
description: Analiza y resume documentos tecnicos, papers cientificos o articulos extensos. Extrae metodologia, hallazgos clave y conclusiones. Usalo en el workspace @research.
category: research
type: core
version: 1.0.0
license: MIT
metadata:
  author: FreakingJSON
  source: OBSOLETE/migration
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
2. La IA lee el contenido y genera un archivo en `workspaces/research/analysis/summary-[nombre].md`.
3. Registra la referencia en `workspaces/research/papers/README.md`.

### 3. Comandos Soportados
- "Resume este paper @archivo"
- "¿Qué dice el análisis de [X] sobre la metodología?"
- "Extrae los puntos clave de este artículo"

## Scripts
- `scripts/summarize.py`: Script base para formatear el resumen.
