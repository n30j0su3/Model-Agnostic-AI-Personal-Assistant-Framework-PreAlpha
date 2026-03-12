# Framework Workflow Standard v1.0

> Proceso estructurado de 7 pasos para manejo de tareas complejas en FreakingJSON Framework

---

## Propósito

Este workflow estandariza cómo el framework maneja tareas complejas, garantizando:

- **Transparencia**: El usuario siempre sabe qué se va a hacer antes de ejecutar
- **Eficiencia**: Uso óptimo de skills y recursos disponibles
- **Documentación**: Cada tarea compleja queda registrada automáticamente
- **Control**: El usuario aprueba antes de ejecutar (con modo Express como excepción)

---

## Los 7 Pasos del Workflow

### Paso 1: Recepción y Comprensión

**Objetivo**: Entender completamente la solicitud del usuario.

**Acciones**:
- Escuchar/lectura completa del requerimiento
- Identificar intención principal y objetivos
- Detectar ambigüedades que requieran clarificación
- Extraer keywords indicadores de complejidad

**Output**: Comprensión clara del problema a resolver.

---

### Paso 2: Evaluar Recursos Locales

**Objetivo**: Detectar qué herramientas, skills y contexto están disponibles.

**Acciones**:
- Revisar skills disponibles (`core/skills/SKILLS.md`)
- Verificar workspace activo y configuración
- Consultar knowledge base existente
- Identificar agentes relevantes

**Output**: Lista de recursos aplicables a la tarea.

---

### Paso 3: Análisis y Planificación

**Objetivo**: Determinar el enfoque óptimo y crear un plan ejecutable.

**Acciones**:
- Clasificar complejidad (Simple vs Complex)
- Seleccionar skills y agentes a utilizar
- Definir secuencia de ejecución
- Estimar tiempo y recursos necesarios

**Criterios de Complejidad**:

| Tipo | Archivos | Tiempo | Skills | Ejemplo |
|------|----------|--------|--------|---------|
| **Simple** | 1-3 archivos | <15 min | 1-2 skills | Editar archivo, consulta rápida |
| **Complex** | >3 archivos | >30 min | 3+ skills | Migración, arquitectura, integración |

**Keywords detectores de complejidad**:
- "crear sistema", "de acuerdo a los requerimientos"
- "planificar", "diseñar", "arquitectura"
- "migrar", "refactorizar", "integrar"
- "automatización", "framework"

**Output**: Plan estructurado con pasos definidos.

---

### Paso 4: Presentar Plan (Resumen Ejecutivo)

**Objetivo**: Obtener autorización del usuario antes de ejecutar.

**Acciones**:
- Presentar resumen ejecutivo claro
- Listar archivos a modificar/crear
- Mostrar skills que se utilizarán
- Explicar tiempo estimado
- Solicitar aprobación o ajustes

**Formato de Resumen**:
```markdown
## Propuesta de Ejecución

**Objetivo**: [Descripción clara]
**Complejidad**: [Simple/Complex]
**Tiempo estimado**: [X minutos]

### Archivos a modificar:
- [ ] archivo1.md
- [ ] archivo2.py

### Skills a utilizar:
- @skill-name: [propósito]

### ¿Procedemos? [Sí/No/Ajustar]
```

**Output**: Aprobación del usuario o ajustes solicitados.

---

### Paso 5: Ejecución Estructurada

**Objetivo**: Ejecutar el plan aprobado usando todos los recursos del framework.

**Acciones**:
- Invocar skills necesarias
- Crear/modificar archivos según plan
- Seguir patrones del framework
- Mantener logs de acciones

**Reglas**:
- Usar `@skill-name` para invocar skills
- Seguir MVI (Minimal Viable Information)
- Respetar filosofía del framework
- Documentar decisiones en tiempo real

**Output**: Tarea completada según plan aprobado.

---

### Paso 6: Documentación Automática

**Objetivo**: Persistir el conocimiento en la base de conocimiento del framework.

**Acciones**:
- Actualizar sesión del día (`core/.context/sessions/YYYY-MM-DD.md`)
- Registrar en insights si es una decisión arquitectónica
- Actualizar índices y referencias
- Crear notas en `codebase/` si aplica

**Output**: Conocimiento preservado para sesiones futuras.

---

### Paso 7: Resumen Final

**Objetivo**: Entregar resultados al usuario y cerrar el ciclo.

**Acciones**:
- Presentar resumen de cambios realizados
- Listar archivos modificados/creados
- Confirmar tarea completada
- Sugerir próximos pasos si aplica

**Formato**:
```markdown
✅ **Tarea Completada**

**Archivos modificados**:
- archivo1.md
- archivo2.py

**Resumen**: [Breve descripción del resultado]

**Próximos pasos sugeridos**: [Si aplica]
```

**Output**: Cierre satisfactorio del workflow.

---

## Case Study: Dashboard SPA v2.0

### Contexto
Migración de features, corrección de bugs y creación del Dashboard SPA.

### Aplicación del Workflow:

**Paso 1**: Solicitud de migrar features del Dashboard SPA a v2.0

**Paso 2**: Evaluación:
- Skills: @dashboard-spa, @context-manager
- Knowledge: `docs/prd-dashboard-spa.md`
- Agentes: @context-scout, @session-manager

**Paso 3**: Planificación:
- **Complejidad**: Complex (>10 archivos, múltiples skills)
- **Archivos**: 15 archivos de configuración, scripts, y documentación
- **Tiempo**: ~45 minutos

**Paso 4**: Resumen Ejecutivo presentado al usuario:
```markdown
## Propuesta: Dashboard SPA v2.0

**Objetivo**: Migrar features, corregir bugs, crear estructura knowledge base
**Complejidad**: Complex
**Tiempo estimado**: 45 minutos

### Archivos a crear/modificar (15):
- docs/prd-dashboard-spa.md (actualizar)
- core/scripts/generate-sessions-index.py (crear)
- core/.context/knowledge/sessions-index.json (crear)
- ...

### Skills:
- @dashboard-spa: Generar dashboard SPA
- @context-manager: Manejo de contexto

### ¿Procedemos? ✅
```

**Paso 5**: Ejecución estructurada:
- Actualizar PRD del Dashboard SPA
- Crear script de generación de índice
- Implementar migración de features
- Corregir bugs detectados
- Generar dashboard SPA con nueva estructura

**Paso 6**: Documentación:
- Sesión del día actualizada con todos los cambios
- Registro de decisiones en insights
- Actualización de CHANGELOG

**Paso 7**: Resumen final:
```
✅ Dashboard SPA v2.0 Completado

**Archivos modificados/creados**: 15
**Features migradas**: Timeline, filtros, interacciones
**Bugs corregidos**: 3 (menú móvil, filtros, timezone)
**Knowledge base**: Estructura creada con índice automático
```

---

## Modo Express

### Propósito
Permitir ejecución rápida omitiendo Paso 4 para tareas urgentes o bien definidas.

### Cuándo Usar:
- Tarea ya discutida previamente
- Corrección rápida de typo
- Usuario explicitamente solicita "modo express"
- Emergencia (bug crítico en producción)

### Reglas del Modo Express:

1. **Transparencia**: Informar al usuario que se usa modo Express
2. **Justificación**: Breve explicación de por qué se salta el paso 4
3. **Documentación**: Aún así se ejecuta paso 6 y 7
4. **Reversibilidad**: Usuario puede pedir modo completo en cualquier momento

### Ejemplo de Uso:
```markdown
🚀 **Modo Express Activado**

Salto el paso 4 (aprobación previa) porque:
- Es una corrección de typo identificada
- Tarea simple: 1 archivo, <2 minutos

**Acción**: Corregir typo en README.md línea 45

Ejecutando ahora...
```

---

## Diagrama de Flujo

```
┌─────────────────────────────────────────────────────────────┐
│  INICIO: Solicitud del Usuario                              │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────┐
│  PASO 1: Recepción y Comprensión                            │
│  └─ Entender el requerimiento completo                      │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────┐
│  PASO 2: Evaluar Recursos Locales                           │
│  └─ Skills, workspaces, knowledge base                      │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────┐
│  PASO 3: Análisis y Planificación                           │
│  └─ Clasificar complejidad, crear plan                      │
└──────────────────┬──────────────────────────────────────────┘
                   │
         ┌─────────┴──────────┐
         │                    │
         ▼                    ▼
┌─────────────────┐  ┌────────────────────────────────────────┐
│  ¿Modo Express? │  │  PASO 4: Presentar Plan                │
│      [SÍ]       │  │  └─ Resumen ejecutivo, aprobación      │
└────────┬────────┘  └────────────────┬───────────────────────┘
         │                            │
         └────────────┬───────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│  PASO 5: Ejecución Estructurada                             │
│  └─ Usar skills, crear/modificar archivos                   │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────┐
│  PASO 6: Documentación Automática                           │
│  └─ Persistir en knowledge base                             │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────┐
│  PASO 7: Resumen Final                                      │
│  └─ Entregar resultados al usuario                          │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────┐
│  FIN: Tarea Completada                                      │
└─────────────────────────────────────────────────────────────┘
```

---

## Integración con Skills

Este workflow puede ser invocado mediante skill:

```markdown
@workflow-standard [complejidad]

Ejemplo:
@workflow-standard complex
@workflow-standard simple
@workflow-standard express
```

## Referencias

- [PHILOSOPHY.md](PHILOSOPHY.md) - Principio #7: Structured Workflow
- [SKILLS.md](../core/skills/SKILLS.md) - Skills disponibles
- [AGENTS.md](../AGENTS.md) - Agentes del framework
- `config/workflow-config.yaml` - Configuración de criterios

---

*Workflow Standard v1.0 - FreakingJSON Framework*

> "Estructura sin rigidez, flexibilidad sin caos."
