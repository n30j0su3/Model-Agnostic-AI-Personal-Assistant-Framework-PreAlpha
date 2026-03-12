# Knowledge Base Central

> **El cerebro del framework.** Conocimiento persistente, historial de sesiones, & insights extraídos de la interacción usuario-framework.

**Versión**: 1.0  
**Última actualización**: 2026-03-04

---

## 🎯 Propósito

Este directorio es el **conocimiento central** del framework, accesible tanto por el usuario como por el agente AI (@FreakingJSON-PA). Contiene:

- **Historial completo de sesiones** - Metadatos enriquecidos para consulta rápida
- **Log de interacciones** - BL-086: Registro estructurado de cada comando
- **Insights extraídos** - Patrones, decisiones y aprendizajes
- **Errores LSP** - Seguimiento de calidad de código

---

## 📁 Estructura

```
knowledge/
├── README.md                   # Este archivo - guía central
├── sessions-index.json         # Índice de todas las sesiones (Dashboard SPA)
├── interactions/               # BL-086: Historial de interacciones
│   └── 2026-03.jsonl          # Log mensual en formato JSON Lines
├── insights/                   # Aprendizajes extraídos
│   ├── patterns.md            # Patrones de uso detectados
│   └── decisions.md           # Decisiones arquitectónicas importantes
└── topics-registry.json       # (Futuro) Registro de temas
```

---

## 🔍 Navegación Rápida

### Para el Usuario

| Quiero... | Ir a... |
|-----------|---------|
| Ver sesiones recientes | [`sessions-index.json`](sessions-index.json) |
| Consultar historial de comandos | [`interactions/`](interactions/) |
| Ver decisiones importantes | [`insights/decisions.md`](insights/decisions.md) |
| Entender patrones de uso | [`insights/patterns.md`](insights/patterns.md) |

### Para el Agente AI

```yaml
# Al iniciar sesión, cargar:
1. sessions-index.json      # Contexto de sesiones previas
2. insights/decisions.md    # Decisiones relevantes
3. insights/patterns.md     # Patrones del usuario

# Durante la sesión, actualizar:
- interactions/YYYY-MM.jsonl    # Cada comando
- sessions-index.json           # Al finalizar
```

---

## 📊 Sessions Index

El archivo [`sessions-index.json`](sessions-index.json) es el **corazón** del Knowledge Base:

### Schema

```json
{
  "id": "2026-03-04",
  "title": "Título descriptivo de la sesión",
  "summary": "Resumen de 1-2 líneas",
  "topics": ["tag1", "tag2"],
  "type": "features|bugfix|research",
  "stats": {
    "interactions": 45,
    "files_modified": 8,
    "decisions": 3,
    "lsp_errors": 2
  },
  "highlights": [
    {"type": "decision", "text": "..."},
    {"type": "feature", "text": "..."}
  ]
}
```

### Uso: Dashboard SPA (Futuro)

El índice está diseñado para ser consumido directamente por el Dashboard SPA:

```javascript
// Cargar índice completo (pequeño, ~10KB para 100 sesiones)
const index = await fetch('knowledge/sessions-index.json').then(r => r.json());

// Filtrar y ordenar en cliente
const recentSessions = index.sessions
  .filter(s => s.topics.includes('features'))
  .sort((a, b) => new Date(b.date) - new Date(a.date));

// Cargar sesión específica on-demand
const sessionContent = await fetch(`sessions/${sessionId}.md`).then(r => r.text());
```

---

## 📝 Interactions Log (BL-086)

Formato: **JSON Lines** (`interactions/YYYY-MM.jsonl`)

### Estructura de entrada

```jsonl
{"timestamp":"2026-03-04T10:30:00","session":"2026-03-04","type":"read","tool":"read","target":"session-start.py","duration_ms":150}
{"timestamp":"2026-03-04T10:35:00","session":"2026-03-04","type":"edit","tool":"edit","target":"session-start.py","lines_changed":15,"lsp_errors_before":1,"lsp_errors_after":0}
```

### Campos

| Campo | Descripción |
|-------|-------------|
| `timestamp` | ISO 8601 |
| `session` | ID de sesión (YYYY-MM-DD) |
| `type` | read, edit, write, bash, grep, etc. |
| `tool` | Herramienta específica |
| `target` | Archivo/objetivo |
| `duration_ms` | Tiempo de ejecución |
| `lsp_errors_*` | Errores antes/después (solo edit) |

---

## 🐛 LSP Error Logging

Errores de diagnóstico se guardan en: `logs/lsp/YYYY-MM-DD.jsonl`

### Captura automática

```python
# Después de cada edit tool con diagnósticos:
python core/scripts/lsp-logger.py --parse-string "$diagnostic_output"
```

### Ver resumen

```bash
python core/scripts/lsp-logger.py --summary
```

---

## 💡 Insights

### Patrones Detectados

Ver [`insights/patterns.md`](insights/patterns.md)

- Frecuencia de uso de herramientas
- Workspaces más activos
- Tipos de tareas recurrentes
- Horarios de mayor productividad

### Decisiones Arquitectónicas

Ver [`insights/decisions.md`](insights/decisions.md)

- Decisiones CORE VITALS
- Cambios de arquitectura
- Selección de tecnologías
- Trade-offs documentados

---

## 🔄 Flujo de Actualización

```
Inicio de Sesión
    ↓
Cargar Knowledge Base (sessions-index.json)
    ↓
Durante Sesión
    ├── Cada comando → interactions/ (append)
    ├── Errores LSP → logs/lsp/ (append)
    └── Decisiones → insights/decisions.md (manual)
    ↓
Cierre de Sesión
    ├── Actualizar sessions-index.json
    ├── Extraer highlights automáticos
    └── Update last_updated
```

---

## 🚀 Integración con Dashboard SPA (Futuro)

### Vista Lista (Sidebar)

```
Hoy
├── Release v0.1.2-prealpha + Knowledge Base...
    
Esta Semana
├── Migración skills desde DEV
├── Fix loop MASTER.md
    
Marzo 2026
├── Investigación agentes externos
```

### Filtros Disponibles

- Por fecha (calendario)
- Por topics/tags
- Por tipo (features/bugfix/research)
- Por archivos modificados
- Por decisiones incluidas

### Búsqueda

```javascript
// Búsqueda local en navegador
const results = index.sessions.filter(s => 
  s.title.toLowerCase().includes(query) ||
  s.summary.toLowerCase().includes(query) ||
  s.topics.some(t => t.includes(query))
);
```

---

## 📈 Métricas

| Métrica | Valor Actual | Descripción |
|---------|--------------|-------------|
| Total Sesiones | 1 | Sesiones indexadas |
| Total Interacciones | 85 | Comandos ejecutados |
| Archivos Modificados | 12 | En sesión actual |
| Errores LSP | 3 | Errores de diagnóstico |

---

## 🛠️ Mantenimiento

### Backup

El Knowledge Base se sincroniza automáticamente con:
- Repo privado (contexto completo)
- Opcional: Gist/JSON online para Dashboard SPA

### Limpieza

```bash
# Rotación de logs antiguos (automático)
# Mantener últimos 90 días de interactions
# Mantener últimos 30 días de LSP errors
```

---

## 🔗 Referencias

- [Sessions](../../sessions/) - Archivos de sesiones completos
- [Logs](../../../logs/) - Logs del sistema y LSP
- [Backlog](../../../docs/backlog.md) - Features planificadas
- [CORE VITALS](../../../docs/backlog.md#core-vitals)

---

> *"El conocimiento que no se estructura, se pierde en el ruido."*
