# Patrones de Uso Detectados

> Patrones, tendencias y hábitos identificados del uso del framework.

---

## Patrones de Sesión

### Duración
- **Promedio**: ~2 horas por sesión
- **Tipo**: Sesiones de features requieren más tiempo (~4 horas)

### Tipos de Sesión Frecuentes
| Tipo | Frecuencia | Descripción |
|------|------------|-------------|
| features | Alta | Desarrollo de nuevas funcionalidades |
| bugfix | Media | Corrección de errores |
| release | Baja | Preparación y publicación de releases |
| research | Media | Investigación de tecnologías/skills |

### Temas Recurrentes
- `skills` - Desarrollo del sistema de skills
- `knowledge-base` - Gestión de conocimiento
- `architecture` - Decisiones de diseño
- `release` - Publicación de versiones

---

## Patrones de Interacción

### Herramientas Más Usadas
1. **read** - Inspección de código/archivos
2. **edit** - Modificación de archivos
3. **write** - Creación de nuevos archivos
4. **bash** - Comandos git/scripts
5. **grep/glob** - Búsqueda en codebase

### Flujo Típico
```
read (contexto) → edit/modify → bash (git) → write (docs)
```

### Archivos Más Modificados
- `core/scripts/session-start.py` - Inicio de sesión
- `core/scripts/pa.py` - Panel de control
- `docs/backlog.md` - Seguimiento de tareas
- `CHANGELOG.md` - Registro de cambios

---

## Patrones de Error

### Errores LSP Frecuentes
| Tipo | Frecuencia | Solución Típica |
|------|------------|-----------------|
| Type mismatch | Media | Ajustar type hints |
| Import not resolved | Baja | Verificar rutas/install |
| Undefined variable | Baja | Definir o importar |

### Archivos con Más Errores
- `session-start.py` - Complejidad creciente

### Corrección
- Errores se capturan automáticamente con `lsp-logger.py`
- Análisis disponible en: `logs/lsp/YYYY-MM-DD.jsonl`

---

## Horarios de Productividad

*(Requiere más datos)*

Patrón esperado:
- Sesiones largas: Fines de semana o días con bloques libres
- Sesiones cortas: Revisión rápida, fixes urgentes

---

## Tendencias

### Crecimiento del Framework
| Métrica | Tendencia |
|---------|-----------|
| Skills | ↑ Creciendo (+6 nuevas recientemente) |
| Sessions | ↑ Actividad sostenida |
| Líneas de código | ↑ Framework madurando |

### Enfoque Actual
- **CORE VITALS**: Alta prioridad
- **Dashboard SPA**: Preparando base (sessions-index.json)
- **Sistema de conocimiento**: En implementación

---

## Recomendaciones Basadas en Patrones

1. **Automatizar** más tareas repetitivas (release checklist)
2. **Documentar** decisiones arquitectónicas en `insights/decisions.md`
3. **Revisar** errores LSP semanalmente para mejorar calidad
4. **Planificar** sesiones de research para explorar nuevas skills

---

> *Los patrones se actualizan automáticamente al analizar interactions/*
