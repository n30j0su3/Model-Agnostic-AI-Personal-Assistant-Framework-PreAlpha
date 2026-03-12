# Anti-Patrones

> Patrones negativos detectados. Lo que NO hacer.

## Sesiones y Persistencia

### ❌ Confiar solo en memoria de conversación

**Problema**: La memoria de la IA es volátil. Entre sesiones se pierde contexto.

**Síntomas**:
- Agente no recuerda decisiones anteriores
- Pendientes no se migran
- Work duplicado

**Solución**: 
- SIEMPRE guardar en archivos .md
- Ejecutar `session-end.py` al terminar
- Verificar que `recordatorios.md` tiene pendientes

---

### ❌ No ejecutar session-end.py

**Problema**: Sesión queda en estado "active", índice desactualizado.

**Síntomas**:
- `sessions-index.json` no refleja última sesión
- `time_end` es null
- Resumen no generado

**Solución**:
- Ejecutar `python core/scripts/session-end.py` antes de salir
- O confiar en atexit (cierre automático)

---

## Código y Scripts

### ❌ Crear scripts ad-hoc sin verificar skills

**Problema**: Duplicar funcionalidad que ya existe como skill.

**Síntomas**:
- Deuda técnica acumulada
- Inconsistencias entre scripts
- Código no mantenible

**Solución**:
1. Consultar `core/skills/SKILLS.md` antes
2. Usar skill existente si aplica
3. Si es recurrente, crear nueva skill

---

### ❌ Import con guión en nombre de archivo

**Problema**: `from session-indexer import X` no funciona.

**Síntomas**:
- ImportError
- Script no carga

**Solución**:
- Usar `importlib.util` para carga dinámica
- O renombrar archivo con underscore

---

## Documentación

### ❌ Duplicar listas de pendientes en múltiples archivos

**Problema**: `recordatorios.md` y `PLAN-v0.2.0.md` con listas idénticas.

**Síntomas**:
- Desincronización
- Confusión sobre cuál es "source of truth"

**Solución**:
- `recordatorios.md` = ejecutivo (checklist)
- `PLAN-*.md` = descriptivo (detalles)
- Referencia cruzada en lugar de duplicar