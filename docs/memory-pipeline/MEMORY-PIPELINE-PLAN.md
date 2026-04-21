# Memory Pipeline — Plan Unificado

> **Fecha**: 2026-04-20  
> **Versión**: 1.0.0  
> **Estado**: Propuesto - Pendiente de implementación  
> **Autor**: PA Framework

---

## 1. Resumen Ejecutivo

### Problema
El sistema actual **guarda pero no recuerda** entre sesiones:
- Contexto se reinicia en cada inicio
- No hay inyección de contexto relevante
- El LLM no sabe en qué trabajaste anteriormente

### Solución Propuesta
**Memory Pipeline Unificado** que combina 3 modos de ejecución:

| Modo | Cuándo Ejecuta | Trigger |
|------|--------------|---------|
| **A: Session Start** | Al iniciar sesión | Manual/auto |
| **B: Intervalo** | Cada N minutos (configurable) | Timer (background) |
| **C: Session End** | Al cerrar sesión | Manual/auto |

---

## 2. Arquitectura del Pipeline

```
┌─────────────────────────────────────────────────────────────────┐
│                    MEMORY PIPELINE                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                  PIPELINE CORE                            │   │
│  │  memory_pipeline.py (orquestador central)                │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                              ↑                                 │
│         ┌──────────────────┼──────────────────┐                 │
│         │                  │                  │                  │
│         ▼                  ▼                  ▼                  │
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐          │
│  │   MODE A   │   │   MODE B   │   │   MODE C   │          │
│  │Session    │   │ Interval  │   │Session    │          │
│  │Start      │   │ Timer    │   │End       │          │
│  │(auto)    │   │(cron)    │   │(auto)    │          │
│  └─────────────┘   └─────────────┘   └─────────────┘          │
│         │                  │                  │                  │
│         └──────────────────┼──────────────────┘                 │
│                          ↓                                    │
│              ┌───────────────────────┐                            │
│              │  OUTPUTS (shared) │                            │
│              ├───────────────────┤                            │
│              │ context.md     │                            │
│              │ summary.md   │                            │
│              │ profile.md  │                            │
│              │ decisions.md │                            │
│              │ topics.md   │                            │
│              │ session.json│                            │
│              └───────────────────────┘                            │
│                          ↓                                    │
│              ┌───────────────────────┐                            │
│              │  INTEGRATION POINTS   │                            │
│              ├───────────────────┤                            │
│              │ session_start.py │                            │
│              │ session_end.py   │                            │
│              │ context_loader.py│                            │
│              └───────────────────────┘                            │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. Modos de Ejecución

### 3.1 MODE A: Session Start (Inicio de Sesión)

**Propósito**: Cargar contexto de sesiones anteriores al iniciar.

**Trigger**: automático en `session_start.py`

**Flujo**:
```
session_start.py
    ↓
 lee session.json (última sesión)
    ↓
 load context_injection.md
    ↓
 injeta en prompt del LLM
    ↓
 "Hola. Detecté que ayer estuviste trabajando en X..."
```

**Código** (pseudocode):
```python
# En session_start.py
def load_memory_context():
    context_file = MEMORY_DIR / "context_injection.md"
    if context_file.exists():
        return context_file.read_text()
    return None  # Primera sesión
```

---

### 3.2 MODE B: Interval Timer (Temporizador)

**Propósito**: Capturar progreso durante sesión larga (>15 min).

**Trigger**: Timer configurable (default: 15 min)

**Configuración**:
```yaml
# config/framework.yaml
memory_pipeline:
  interval_minutes: 15  # configurable
  enabled: true
  watch_mode: true  # ejecutar en background
```

**Flujo**:
```
Timer (15 min)
    ↓
 checkpoint_session()
    ↓
 extract_knowledge()
    ↓
 update_context()
    ↓
 save_to_memory()
```

**Código** (pseudocode):
```python
# En memory_pipeline.py --watch
def run_interval_watch(interval_minutes=15):
    while session_active:
        time.sleep(interval_minutes * 60)
        run_memory_cycle()  # Same as learning_cron
        save_context_injection()
```

---

### 3.3 MODE C: Session End (Cierre de Sesión)

**Propósito**: Guardar estado completo al cerrar.

**Trigger**: automático en `session_end.py` o manual

**Flujo**:
```
session_end.py
    ↓
 run_full_learning_cycle()
    ↓
 generate_session_summary()
    ↓
 update_profile()
    ↓
 generate_context_injection()  # Listo para próxima sesión
    ↓
 save_to_sqlite()
    ↓
 mark_session_complete()
```

**Código** (pseudocode):
```python
# En session_end.py
def on_session_end():
    pipeline = MemoryPipeline()
    pipeline.run_full_cycle()
    pipeline.save_context_injection()
    pipeline.save_to_sqlite()
```

---

## 4. Componentes del Pipeline

### 4.1 Scripts Existentes a Reutilizar

| Script | Función | Reutilizar |
|--------|---------|----------|
| `session_saver.py` | Checkpoint | ✅ |
| `knowledge_miner.py` | Extraer patrones | ✅ |
| `knowledge_pattern_detector.py` | Detectar temas | ✅ |
| `knowledge_extractor.py` | Extraer knowledge | ✅ |
| `wiki_autopopulate.py` | Poblar wiki | ✅ |
| `context_loader.py` | Cargar contexto | ✅ |
| `session_indexer.py` | Indexar sesiones | ✅ |

### 4.2 Scripts a Crear

| Script | Función |
|--------|--------|
| `memory_pipeline.py` | Orquestador central |
| `context_injector.py` | Generar context_injection.md |

### 4.3 Archivos de Memoria

```
core/.context/memory/
├── context_injection.md    ← Inyectar en inicio
├── session_summary.md   ← Resumen actual
├── topics_registry.md   ← Temas activos
├── decisions_log.md    ← Decisiones tomadas
├── profile.md       ← Perfil usuario
├── session.json     ← Estado actual (JSON)
└── config.yaml     ← Configuración
```

---

## 5. Flujo Completo: Sesión → Memoria → Nueva Sesión

### 5.1 Ciclo Completo

```
┌─────────────────────────────────────────────────────────────────┐
│                    FULL MEMORY CYCLE                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ╔═══════════════════════════════════════════════════════════╗   │
│  ║  SESIÓN N: 2026-04-20                                    ║   │
│  ║                                                           ║   │
│  ║  [SESSION START]                                          ║   │
│  ║  ├── load_context_from_memory()  ← MODE A                ║   │
│  ║  └── "Hola. Detecté que..."                             ║   │
│  ║         ↓                                               ║   │
│  ║  [WORKING...]                                           ║   │
│  ║  usuario trabaja en tareas                               ║   │
│  ║         ↓                                               ║   │
│  ║  [INTERVAL TRIGGER - cada 15 min]  ← MODE B             ║   │
│  ║  ├── checkpoint_session()                               ║   │
│  ║  ├── extract_knowledge()                                ║   │
│  ║  └── update_context()                                  ║   │
│  ║         ↓                                               ║   │
│  ║  [SESSION END]                                          ║   │
│  ║  ├── run_full_learning_cycle()   ← MODE C                ║   │
│  ║  ├── generate_summary()                                ║   │
│  ║  ├── update_profile()                                ║   │
│  ║  ├── generate_context_injection()                    ║   │
│  ║  └── save_to_sqlite()                               ║   │
│  ╚═══════════════════════════════════════════════════════════╝   │
│                              ↓                                   │
│  ╔═══════════════════════════════════════════════════════════╗   │
│  ║  SESIÓN N+1: 2026-04-21 (día siguiente)               ║   │
│  ║                                                           ║   │
│  ║  [SESSION START]                                          ║   │
│  ║  ├── load_context_from_memory()                         ║   │
│  ║  └─��� "Hola. Detecté que ayer estuviste en X.            ║   │
│  ║       Continuamos donde quedamos."                        ║   │
│  ╚═══════════════════════════════════════════════════════════╝   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 6. Configuración

### 6.1 Parámetros Configurables

```yaml
# config/framework.yaml
memory_pipeline:
  # Intervalo de ejecución (MODE B)
  interval_minutes: 15
  
  # Habilitar/deshabilitar
  enabled: true
  
  # Modos activos
  modes:
    session_start: true   # MODE A
    interval: true       # MODE B
    session_end: true    # MODE C
  
  # Rutas
  memory_dir: core/.context/memory
  
  # TTL
  max_sessions_in_context: 3
  max_context_length: 2000
```

### 6.2 Usuario Configura Intervalo

```bash
# Desde terminal
python core/scripts/memory_pipeline.py --interval 30  # 30 min
python core/scripts/memory_pipeline.py --interval 5    # 5 min
python core/scripts/memory_pipeline.py --interval 0   # disable
```

---

## 7. Casos de Uso

### Caso 1: Sesión Corta (<15 min)
```
Inicio → Trabajo → Cierre
         │
         └→ MODE C only (session_end ejecuta pipeline)
```

### Caso 2: Sesión Larga (>15 min)
```
Inicio → Trabajo → Interval (15min) → Trabajo → Interval (15min) → Cierre
              │                   │
              └─→ MODE B (x2)  └─→ MODE C
```

### Caso 3: Nueva Sesión (sin memoria previa)
```
Inicio → (no hay context_injection) → Trabajo → Cierre → MODE C
```

### Caso 4: Reanudar Sesión Anterior
```
Inicio → (carga context_injection) → "Continuamos donde quedamos"
```

---

## 8. Validación

### 8.1 Métricas de Éxito

| Métrica | Target |
|--------|--------|
| Context Injected | >90% |
| Memory Recall | >80% |
| Pipeline Success | >95% |
| User Profile Updated | >70% |

### 8.2 Diagnóstico

```bash
python core/scripts/memory_pipeline.py --status
```

Output:
```
Memory Pipeline Status:
  Enabled: true
  Interval: 15 min
  Last Run: 2026-04-20 19:45
  Context Available: YES
  Sessions in Memory: 3
  Profile Updated: 2026-04-19
```

---

## 9. Roadmap de Implementación

### Fase 1: Core Pipeline
- [ ] Crear `memory_pipeline.py`
- [ ] Reutilizar scripts existentes
- [ ] Implementar MODE A (session_start)

### Fase 2: Interval Timer
- [ ] Implementar MODE B (watch mode)
- [ ] Agregar configuración en framework.yaml
- [ ] Integrar con session_autosave.py

### Fase 3: Session End
- [ ] Implementar MODE C (session_end)
- [ ] Integrar en session_end.py
- [ ] Generar context_injection.md

### Fase 4: Integración
- [ ] Modificar context_loader.py
- [ ] Crear estructura memory/
- [ ] Integrar con SQLite

### Fase 5: Testing
- [ ] Test completo
- [ ] Validar recall
- [ ] Documentar

---

## 10. Comparación de Opciones

| Aspecto | Opción A | Opción B | Opción C |
|--------|----------|---------|---------|
| Timing | Inicio | Intervalo | Cierre |
| Frecuencia | 1x/sesión | Nx/sesión | 1x/sesión |
| Contexto | ✅ | ⚠️ Parcial | ✅ |
| Profile | ❌ | ❌ | ✅ |
| Summary | ❌ | ❌ | ✅ |

**Amal gama**: Los 3 modos se complementan y ejecutan según timing.

---

## 11. Notas Técnicas

### SQLite Integration
- Guardar estado en `core/.context/memory/session.json`
- Usar misma DB que session_indexer

### Lazy Loading
- Solo cargar context_injection si existe
- No bloquea inicio de sesión

### Error Handling
- Si pipeline falla, continuar sin memoria
- Loggear error, no romper sesión