# Decisiones Arquitectónicas

> Decisiones importantes del framework que afectan su evolución y diseño.

---

## 2026-03-04 - Knowledge Base Central (CORE VITALS)

### Contexto
Se requería un sistema de conocimiento central que integre:
- INF-003: Knowledge Base (URLs/mejoras)
- INF-004: Logging de prompts
- INF-005: Token tracking (preparado)
- BL-086: Historial de interacciones
- LSP Error Logging

### Decisión
Implementar **Knowledge Base Central** con estructura:

```
knowledge/
├── sessions-index.json      # Índice Dashboard SPA-compatible
├── interactions/            # JSON Lines (append-only)
├── insights/               # Markdown estructurado
└── README.md               # Guía central
```

### Rationale
| Opción | Pros | Cons |
|--------|------|------|
| SQLite | Consultas rápidas, ACID | Requiere schema, lock-in | 
| JSON puro | Simple, parseable | Sin queries complejas |
| **JSON + MD** | ✅ Human-readable, AI-parseable, compatible SPA | Búsqueda limitada (aceptable) |

### Impacto
- **Ahora**: Archivos .md + .json fáciles de mantener
- **Futuro**: sessions-index.json se consume directo por Dashboard SPA
- **Backup**: Todo es texto plano, fácil de versionar

---

## 2026-03-04 - Schema Sessions Index para Dashboard SPA

### Decisión
Diseñar `sessions-index.json` compatible con vista tipo ChatGPT/DeepSeek:

```json
{
  "id": "2026-03-04",
  "title": "...",
  "summary": "...",
  "topics": ["..."],
  "stats": {...},
  "highlights": [...]
}
```

### Campos clave para SPA
- `title` + `summary`: Vista lista con preview
- `topics`: Filtros y búsqueda
- `stats`: Métricas rápidas
- `highlights`: Destacados visuales

### Compatibilidad futura
- El índice carga completo (~10KB para 100 sesiones)
- Contenido se carga on-demand del .md
- Filtros/búsqueda en cliente (JavaScript)

---

## 2026-03-04 - LSP Error Logger

### Contexto
Errores LSP aparecen en output de edit tools pero no se persisten.

### Decisión
Crear `lsp-logger.py` que:
1. Parsea diagnósticos de herramientas
2. Guarda en `logs/lsp/YYYY-MM-DD.jsonl`
3. Actualiza sessions-index.json con conteo

### Rationale
- Simple: JSON Lines append-only
- Integrado: Se llama automáticamente post-edit
- Útil: Permite detectar errores frecuentes y calidad de código

---

## 2026-03-04 - Migración Skills desde DEV

### Contexto
`session-start.py` mostraba 7 skills hardcodeadas en lugar de las ~22 reales.

### Decisión
Migrar escaneo dinámico desde DEV:
```python
def get_all_skills():
    # Escanea core/skills/core/ dinámicamente
    # Retorna lista real de skills disponibles
```

### Impacto
- Usuarios ven conteo real: "skill1, skill2... (+19 más)"
- No requiere mantenimiento manual

---

## 2026-03-04 - Fix Loop MASTER.md en Instalación Fresca

### Problema
Instalación fresca quedaba en loop:
1. Sin MASTER.template.md en git
2. install.py no creaba MASTER.md
3. Sincronizar Contexto fallaba
4. Configurar Perfil requería MASTER.md

### Solución
1. **install.py**: Fallback para crear MASTER.md con contenido por defecto
2. **pa.py**: Verificación post-instalación

### Lección
Siempre tener fallback para archivos críticos en instalación.

---

---

## 2026-03-11 - Sistema de Skills Propio

### Contexto
El framework necesitaba capacidad de crear skills personalizadas sin depender de sistemas externos.

### Decisión
Implementar sistema de skills propio usando `@skill-creator`, adaptando el sistema de Anthropic a FreakingJSON.

### Proceso validado
1. Usar `@skill-creator` para diseñar skill
2. Implementar en `core/skills/core/<skill-name>/`
3. Registrar en SKILLS.md
4. Documentar uso y dependencias

### Resultado
Proceso de 5 pasos validado con creación exitosa de `@markdown-writer`.

### Mejoras identificadas
- Registry local de skills disponibles (más allá del catalog.json)
- Sistema de dependencias entre skills
- Validación automática de skills al commitear

### Referencias
- Documentación original: https://agentman.ai/agentskills/skill/skill-creator
- Implementación: `core/skills/core/skill-creator/`

*Migrado desde ideas.md - 2026-03-11*

---

## Plantilla para Nuevas Decisiones

```markdown
## YYYY-MM-DD - Título

### Contexto
[Describe el problema o feature]

### Decisión
[Qué se decidió hacer]

### Opciones Consideradas
| Opción | Pros | Cons |
|--------|------|------|
| A | ... | ... |
| B | ... | ... |

### Impacto
[Qué efecto tiene esta decisión]
```
