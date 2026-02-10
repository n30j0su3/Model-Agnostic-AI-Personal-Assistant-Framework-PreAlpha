# Prompt Improvement References

Ultima revision: 2026-01-25

## Principios

- Claridad sobre creatividad
- Contexto delimita el resultado
- Ejemplos reducen ambiguedad
- Formatos estrictos facilitan automatizacion

## Referencias confiables

- OpenAI Prompt Engineering Guide: https://platform.openai.com/docs/guides/prompt-engineering
- OpenAI Structured Outputs: https://platform.openai.com/docs/guides/structured-outputs
- Anthropic Prompt Engineering: https://docs.anthropic.com/claude/docs/prompt-engineering
- Google Gemini Prompting: https://ai.google.dev/gemini-api/docs/prompting
- Microsoft Prompt Engineering: https://learn.microsoft.com/azure/ai-services/openai/concepts/prompt-engineering
- Prompt Engineering Guide: https://www.promptingguide.ai

## Programacion recomendada

Actualiza las referencias de forma manual y programada cuando sea posible.

Linux/macOS (cron mensual):

```bash
0 9 1 * * cd /ruta/al/framework && python skills/core/prompt-improvement/scripts/update-references.py --json
```

Windows (Task Scheduler):

```powershell
python "C:\Ruta\al\framework\skills\core\prompt-improvement\scripts\update-references.py" --json
```

Despues de cada actualizacion, revisa los cambios manualmente para validar calidad y vigencia.
