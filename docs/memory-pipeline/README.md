# Memory Pipeline — Integral/Complete Mode

> **Fecha**: 2026-04-21  
> **Versión**: 1.2.0  
> **Estado**: Operativo

---

#### Objetivo

Garantizar un pipeline de memoria **integral** donde las 4 capas persisten en conjunto y se sincronizan automáticamente para evitar pérdida de detalle, patrones y relaciones.

---

#### Modelo de Persistencia

| **Campo** | **Valor** |
|---|---|
| Modo | `integral_4layer` |
| Captura | Continua (event-driven) |
| Consolidación | Intervalo + cierre |
| Capas | Sessions `.md`, Memory MD, SQLite, Wiki |
| Alcance | Memoria operativa + memoria estructurada + memoria relacional |

---

#### Semántica de Capas

| **Capa** | **Qué guarda** | **Propósito** |
|---|---|---|
| Sessions `.md` | Registro cronológico completo | Rastro rápido y humano |
| Memory MD | Resúmenes operativos, patrones, decisiones normalizadas | Capa intermedia reutilizable |
| SQLite | Sesiones completas, mensajes, TODOs, metadata | Consulta estructurada ilimitada |
| Wiki | Páginas relacionadas, conceptos/entidades/patrones enlazados | Segundo cerebro relacional |

---

#### Ciclo Integral Ejecutado por `memory_pipeline.py`

| **Modo** | **Comando** | **Acciones** |
|---|---|---|
| Load Context | `--load-context` | Rehidratación de contexto persistente |
| Watch | `--watch --interval N` | checkpoint + miner + extractor + wiki + kb_updater + memory_sync |
| Full Cycle | `--full-cycle` | Consolidación final integral de las 4 capas |
| Status | `--status` | Health snapshot por capa |

---

#### Configuración

Archivo: `config/framework.yaml`

```yaml
memory_pipeline:
  enabled: true
  mode: integral_4layer
  interval_minutes: 15
  guarantees:
    lossless_capture: true
    persistent_all_layers: true
    relational_context: true
```

---

#### Verificación rápida

```bash
python core/scripts/memory_pipeline.py --status
python core/scripts/memory_pipeline.py --watch --interval 15
python core/scripts/memory_pipeline.py --full-cycle
```

---

#### Notas de implementación

| **Punto** | **Detalle** |
|---|---|
| SQLite real-time | Depende de `session_start.py` + `session_bridge.py` + `message_hook.py` |
| Wiki relacional | Se fortalece vía `wiki_autopopulate.py` + `kb_updater.py` |
| Robustez | `memory_sync.py` valida estructura/esquema de memoria/wiki |
