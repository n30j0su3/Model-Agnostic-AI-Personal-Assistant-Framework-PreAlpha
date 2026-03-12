---
description: Genera reporte de optimización e insights del día
agent: doc-writer
---

# Reporte de Optimización

**Propósito**: Ejecutar `knowledge-indexer.py` y `optimization-reporter.py` para generar insights automáticos.

## Qué Hace

1. **Ejecuta knowledge-indexer.py**
   - Lee `interactions/interactions-*.log` del día
   - Genera `insights/patterns.md` (frases top, categorías)
   - Genera `insights/trends.md` (tendencias de uso)

2. **Ejecuta optimization-reporter.py**
   - Calcula tokens usados/ahorrados
   - Estima tiempo ahorrado (framework vs tradicional)
   - Genera `insights/optimization-report.md`

3. **Muestra resumen**
   - Tokens usados
   - Horas ahorradas
   - Frases top
   - Categorías más usadas
   - Recomendaciones de optimización

## Comandos Relacionados

```bash
# Ejecutar manualmente
python core/scripts/knowledge-indexer.py
python core/scripts/optimization-reporter.py

# Ver insights generados
cat core/.context/knowledge/insights/patterns.md
cat core/.context/knowledge/insights/optimization-report.md
```

## Configuración

Ver: `core/.context/knowledge/users/default/logging-config.md`

## Output Esperado

```
📊 Reporte de Optimización - 2026-03-06

✅ Insights generados:
   - patterns.md: 10 frases top, 5 categorías
   - trends.md: Actividad por hora, modelos usados
   - optimization-report.md: 2.5h ahorradas

🏆 Logros del día:
   - 45 prompts ejecutados
   - 23 archivos modificados
   - 69k tokens procesados
   - 2.5h ahorradas vs método tradicional

💡 Recomendaciones:
   - Usar más @context-scout antes de editar
   - Cachear respuestas frecuentes
   - Agrupar tareas similares
```

---

*Comando slash para BL-100 (Aprendizaje Continuo)*
