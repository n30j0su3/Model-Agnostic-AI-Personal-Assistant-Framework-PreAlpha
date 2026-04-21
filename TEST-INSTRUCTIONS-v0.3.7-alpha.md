# PA Framework v0.3.7-alpha — Instrucciones de Prueba

## 1) Arranque rápido

```bash
python core/scripts/session_start.py --skip-context
python core/scripts/session_end.py --silent
```

## 2) Smoke test de compilación

```bash
python3 -m py_compile \
  core/scripts/session_start.py \
  core/scripts/session_end.py \
  core/scripts/session_saver.py \
  core/scripts/session_bridge.py \
  core/scripts/memory_sync.py \
  core/scripts/memory_pipeline.py \
  core/memory/session_memory.py \
  core/recovery/orchestrator.py \
  core/recovery/triggers.py \
  core/scripts/pa.py
```

## 3) Tests recomendados (rápidos)

```bash
pytest -q \
  core/scripts/tests/test_session_start_v22.py \
  core/scripts/tests/recovery_test.py \
  core/scripts/tests/error_logger_test.py

pytest -q tests/integration/test_phase3_e2e.py
```

## 4) Memory Pipeline smoke test

```bash
# Ver estado del pipeline
python core/scripts/memory_pipeline.py --status

# Cargar contexto (MODE A)
python core/scripts/memory_pipeline.py --load-context

# Ejecutar ciclo completo (MODE C)
python core/scripts/memory_pipeline.py --full-cycle
```

## 5) Estado esperado

- `VERSION` = `0.3.7-alpha`
- `core/.context/quick-start.md` usa `session_start.py` (underscore)
- Recovery import fallback activo en `core/recovery/orchestrator.py`
- Memory Pipeline structure: `core/.context/memory/` with `summaries/`, `context/`, `profile/`

## 6) Novedades v0.3.7-alpha

- **Memory Pipeline System**: 3 modes (Session Start, Interval Timer, Session End)
- `memory_pipeline.py`: Orquestador central con CLI
- `docs/memory-pipeline/`: Plan + README documentation

## 7) Nota importante

Este paquete es **STAGING para pruebas internas**. Parte de la documentación histórica aún referencia versiones anteriores; no bloquea las pruebas funcionales actuales.
