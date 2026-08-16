# Memory Architecture — Integral 4-Layer Persistence

> **Versión**: v0.3.7-alpha (HOTFIX4 candidate)  
> **Estado**: Activo  
> **Modelo**: Persistencia integral (no task-specific)

---

#### Resumen Ejecutivo

| **Campo** | **Valor** |
|---|---|
| Objetivo | No perder detalles, patrones ni contexto relacional durante toda la operación |
| Fuente primaria | `core/.context/sessions/YYYY-MM-DD.md` |
| Modelo | 4 capas persistentes y sincronizadas (no exclusivas) |
| Garantía | Captura continua + consolidación periódica + cierre robusto |
| Scripts núcleo | `session_start.py`, `message_hook.py`, `session_bridge.py`, `memory_pipeline.py`, `session_end.py` |

---

#### Definición Oficial de Capas (el equipo)

| **Capa** | **Rol** | **Naturaleza** | **Persistencia** |
|---|---|---|---|
| `.md (Sessions)` | Memoria simple/rápida | Log cronológico universal | Siempre |
| `Memory MD` | Memoria intermedia | Síntesis operativa + patrones reutilizables | Siempre |
| `SQLite` | Memoria permanente | Sesiones completas, TODOs, mensajes y metadata estructurada, ilimitada | Siempre |
| `Wiki` | Segundo cerebro relacional | Conocimiento relacionado, navegación semántica y relaciones tipo grafo | Siempre |

> Importante: las capas **no son alternativas**; son complementarias dentro de un sistema integral.

---

#### Flujo Integral (Lossless)

| **Etapa** | **Acción** | **Capas impactadas** |
|---|---|---|
| Captura en tiempo real | Hook de mensajes + bridge de sesión | Sessions `.md` + SQLite |
| Consolidación periódica | Minería, extracción, autopoblado, actualización KB, sync estructural | Memory MD + Wiki (+ validación de consistencia) |
| Consolidación de cierre | Full cycle de persistencia + indexación final | Las 4 capas |
| Recuperación | Rehidratación de contexto para continuidad | SQLite + Memory MD + Sessions + Wiki |

---

#### Garantías del Pipeline

| **Garantía** | **Implementación** |
|---|---|
| No pérdida de detalle | Captura de sesión + mensajes estructurados en SQLite |
| No pérdida de patrones | `knowledge_miner.py` + `knowledge_extractor.py` |
| No pérdida de relación contextual | `wiki_autopopulate.py` + `kb_updater.py` |
| Continuidad entre sesiones | `memory_pipeline.py --load-context` + indexación de sesión |
| Salud estructural | `memory_sync.py` periódico y al cierre |

---

#### Estado de Alineación

| **Componente** | **Estado** | **Nota** |
|---|---|---|
| `session_start.py` + `SessionBridge` | Alineado | Inicializa sesión persistente en SQLite |
| `message_hook.py` | Alineado | Captura continua de mensajes (si hooks CLI están activos) |
| `memory_pipeline.py` | Ajustado | Ciclo integral interval + cierre incluyendo wiki/kb/sync |
| `framework.yaml` | Ajustado | Declarado `mode: integral_4layer` y capas siempre persistentes |

---

#### Comandos Operativos

```bash
# Estado integral de memoria (4 capas)
python core/scripts/memory_pipeline.py --status

# Inyección de contexto al iniciar
python core/scripts/memory_pipeline.py --load-context

# Ciclo integral continuo
python core/scripts/memory_pipeline.py --watch --interval 15

# Consolidación integral al cierre
python core/scripts/memory_pipeline.py --full-cycle
```

---

#### Referencias

- `core/INIT-PROTOCOL.md`
- `docs/memory-pipeline/README.md`
- `config/framework.yaml`
