---
title: "CORE-008: Knowledge Extraction Framework"
version: "0.2.0-prealpha"
type: "process"
scope: "public"
prp: "PRP-011"
---

# CORE-008: Knowledge Extraction Framework

## Principio Fundamental

**Extracción automática de conocimiento valioso durante las sesiones: descubrimientos, prompts efectivos, ideas y mejores prácticas se capturan automáticamente para beneficio futuro.**

## Descripción

El proceso CORE-008 implementa un sistema de extracción automática de conocimiento que analiza las sesiones de trabajo para identificar y preservar:
- **Descubrimientos**: Hallazgos importantes durante el trabajo
- **Prompts efectivos**: Prompts que produjeron buenos resultados
- **Ideas**: Conceptos para futuras implementaciones
- **Mejores prácticas**: Patrones que funcionan bien

Este principio asegura que el conocimiento generado no se pierda, creando una base de conocimiento que mejora continuamente.

## Objetivos

1. Capturar conocimiento valioso automáticamente
2. Preservar aprendizajes de sesiones
3. Reutilizar prompts efectivos
4. Documentar mejores prácticas descubiertas

## Cuándo Aplicar

- **Durante sesiones de trabajo**: Extracción automática al final
- **Al detectar tags especiales**: #discovery, #prompt-success, #idea, #best-practice
- **Cierre de sesión**: `session-end.py` extrae automáticamente
- **Revisión periódica**: Analizar knowledge-index.json

## Flujo de Trabajo

### Paso 1: Tags de Detección

Durante el trabajo, marcar con tags especiales:

```markdown
#discovery Aprendí que sync-prealpha.py tiene un bug con paths relativos

#prompt-success Este prompt funcionó perfectamente para generar READMEs

#idea Sería útil tener un skill @auto-test para testing automático

#best-practice Siempre usar git add -f para archivos en .gitignore
```

### Paso 2: Extracción Automática

Al ejecutar `session-end.py`, el sistema:

1. **Analiza la sesión** del día
2. **Detecta tags** especiales
3. **Extrae contexto** alrededor de cada tag
4. **Clasifica** en categorías:
   - Discoveries
   - Prompts
   - Ideas
   - Best Practices
   - Anti-patterns

### Paso 3: Almacenamiento

El conocimiento se guarda en:

```
core/.context/knowledge/
├── knowledge-index.json      # Índice central
├── learning/
│   ├── discoveries.md        # Descubrimientos
│   ├── best-practices.md     # Mejores prácticas
│   └── anti-patterns.md      # Anti-patrones
└── prompts/
    └── registry.json         # Prompts efectivos
```

### Paso 4: Reutilización

El conocimiento extraído está disponible para:
- **Futuras sesiones**: Consultar antes de empezar
- **Prompts**: Reusar prompts que funcionaron
- **Decisiones**: Basarse en aprendizajes previos
- **Documentación**: Enriquecer con experiencias

## Tags de Extracción

| Tag | Uso | Destino |
|-----|-----|---------|
| `#discovery` | Hallazgos importantes | `learning/discoveries.md` |
| `#prompt-success` | Prompts efectivos | `prompts/registry.json` |
| `#idea` | Ideas para backlog | `codebase/ideas.md` |
| `#best-practice` | Patrones exitosos | `learning/best-practices.md` |
| `#anti-pattern` | Patrones a evitar | `learning/anti-patterns.md` |

## Herramientas y Recursos

### Scripts
- `core/scripts/knowledge-extractor.py`: Extracción automática
- `core/scripts/session-end.py`: Integra extracción al cierre
- `core/scripts/pattern_analyzer.py`: Analiza patrones

### Knowledge Base
- `knowledge/knowledge-index.json`: Índice central
- `knowledge/learning/`: Aprendizajes documentados
- `knowledge/prompts/`: Registro de prompts

### Integración
- `config/framework.yaml`: Configuración de extracción
- `session-end.py`: Llamada automática vía atexit

## Ejemplos Prácticos

### Ejemplo 1: Descubrimiento

**Durante sesión**:
```markdown
Trabajando en sync-prealpha.py...

#discovery El bug de path mismatch ocurre porque rel_path 
agrega "./" para archivos en root, causando falsos deletes

Solución: Normalizar paths con .lstrip("./")
```

**Resultado**:
- Extraído a `learning/discoveries.md`
- Referenciado en `knowledge-index.json`
- Disponible para futuras sesiones sobre sync

### Ejemplo 2: Prompt Efectivo

**Durante sesión**:
```markdown
Generando PRPs simplificados...

#prompt-success "Crea documentación técnica con:
- Principio fundamental en 1-2 líneas
- Descripción detallada
- Pasos claros
- Ejemplos prácticos
- Referencias cruzadas"

Resultado: Excelente estructura y contenido
```

**Resultado**:
- Guardado en `prompts/registry.json`
- Categorizado como "documentación técnica"
- Reusable para crear docs similares

### Ejemplo 3: Idea para Backlog

**Durante sesión**:
```markdown
#idea Sería útil tener un skill @version-bumper que:
- Actualice VERSION automáticamente
- Sincronice a todos los archivos
- Genere CHANGELOG entry template
- Valide consistencia

Prioridad: Medium
Complejidad: Low
```

**Resultado**:
- Agregado a `codebase/ideas.md`
- Indexado en backlog
- Para considerar en próximas iteraciones

## Estructura del Knowledge Index

```json
{
  "version": "1.0.0",
  "stats": {
    "total_discoveries": 15,
    "total_prompts": 8,
    "total_ideas": 5,
    "total_best_practices": 12
  },
  "recent": {
    "discoveries": [...],
    "prompts": [...]
  },
  "sessions_processed": [
    "2026-03-11",
    "2026-03-10"
  ]
}
```

## Mejores Prácticas

### Para Usuarios

1. **Usar tags consistentemente**: Marcar hallazgos importantes
2. **Contexto suficiente**: Explicar por qué es valioso
3. **Revisar periódicamente**: Consultar knowledge antes de tareas similares
4. **Contribuir activamente**: Más tags = mejor knowledge base

### Para Desarrollo de Skills

1. **Integrar extracción**: Los skills pueden sugerir tags
2. **Validar calidad**: Filtrar extracciones de baja calidad
3. **Categorizar bien**: Tags correctos = mejor organización
4. **Preservar contexto**: Extraer suficiente contexto alrededor

## Validación y Verificación

- [ ] ¿`knowledge-extractor.py` ejecuta sin errores?
- [ ] ¿Los tags están bien formados?
- [ ] ¿El knowledge-index.json se actualiza?
- [ ] ¿Los descubrimientos son valiosos?
- [ ] ¿Los prompts son reusables?

## Configuración

En `config/framework.yaml`:

```yaml
knowledge_extraction:
  enabled: true
  mark_for_review: true
  auto_detect:
    discoveries: true
    prompts: true
    ideas: true
    best_practices: true
  tags:
    discovery: "#discovery"
    prompt_success: "#prompt-success"
    idea: "#idea"
    best_practice: "#best-practice"
```

## Referencias

- [AGENTS.md](../../AGENTS.md) - Router principal
- [Knowledge Index](../../core/.context/knowledge/knowledge-index.json) - Índice central
- [Discoveries](../../core/.context/knowledge/learning/discoveries.md) - Aprendizajes
- [Prompts Registry](../../core/.context/knowledge/prompts/registry.json) - Prompts efectivos

## Changelog

### v0.2.0-prealpha (2026-03-11)
- Versión inicial del Knowledge Extraction Framework
- Proceso CORE-008 agregado al framework
- Integración con session-end.py vía atexit
- Tags de extracción: #discovery, #prompt-success, #idea, #best-practice
