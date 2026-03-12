---
title: "CORE-005: Assembly Line"
version: "0.2.0-prealpha"
type: "process"
scope: "public"
prp: "PRP-005"
---

# CORE-005: Assembly Line

## Principio Fundamental

**Bucle agentico estándar para tareas complejas: Delimitar → Mapear → Ejecutar → Validar → Preservar.**

## Descripción

El proceso CORE-005 define el "Assembly Line" (Línea de Montaje) para tareas complejas en el framework. Inspirado en manufactura lean, establece fases claras con control de calidad en cada etapa, asegurando resultados consistentes y de alta calidad.

Este proceso es complementario al Workflow Standard de 7 pasos, enfocándose específicamente en la **ejecución estructurada** de tareas complejas.

## Objetivos

1. Estandarizar proceso para tareas complejas
2. Garantizar calidad en cada etapa
3. Integrar PRPs (Blueprints) en el flujo
4. Permitir mejora continua

## Cuándo Aplicar

- **Tareas complejas**: >3 archivos, >30 minutos, múltiples skills
- **Migraciones**: Cambios de estructura grandes
- **Arquitectura**: Diseño de nuevos sistemas
- **Integraciones**: Conectar con sistemas externos
- **Keywords**: "crear sistema", "planificar", "diseñar", "arquitectura", "migrar", "refactorizar"

## Las 5 Fases del Assembly Line

### FASE 1: DELIMITAR (Planificar)

**Objetivo**: Definir claramente qué se va a hacer y cómo.

**Pasos**:
1. **Definir alcance**
   - ¿Qué está incluido?
   - ¿Qué está excluido?
   - ¿Cuáles son los entregables?

2. **Crear/validar PRP (Blueprint)**
   - Si no existe PRP, considerar crear uno
   - Si existe, validar que aplica
   - El PRP es el "plano" que guía la ejecución

3. **Identificar recursos**
   - Skills necesarias: @skill-name
   - Agentes a delegar: @agent-name
   - MCP servers: @context7, @sequentialthinking

4. **Estimar complejidad**
   - Simple: 1-3 archivos, <15 min
   - Complex: >3 archivos, >30 min

**Output**: Plan estructurado con pasos definidos.

### FASE 2: MAPEAR (Descubrimiento)

**Objetivo**: Descubrir todo el contexto necesario antes de ejecutar.

**Pasos**:
1. **@context-scout descubre archivos**
   - Buscar archivos .md relevantes (CORE-002)
   - Detectar README.md, AGENTS.md, etc.

2. **Validar dependencias contra SKILLS.md (CORE-001)**
   - ¿Qué skills se necesitan?
   - ¿Están disponibles?

3. **Cargar contexto necesario**
   - Leer archivos de contexto detectados
   - Integrar en sesión activa

**Output**: Contexto completo cargado, dependencias identificadas.

### FASE 3: EJECUTAR (Subtareas)

**Objetivo**: Ejecutar el plan usando todos los recursos del framework.

**Pasos**:
1. **Aplicar MAGIC PROMPT 2**:
   ```
   "Recuerda desplegar agentes para optimizar recursos/tokens/etc.
   Usar los recursos/skills/agentes del framework.
   Si un error bloquea el avance, ARREGLALO. No lo reportes esperando respuesta."
   ```

2. **Delegar a subagentes según especialidad**
   - @context-scout: Descubrimiento
   - @skill-evaluator: Evaluación
   - @doc-writer: Documentación

3. **Ejecutar workflow**
   - Seguir el plan paso a paso
   - Capturar métricas (tokens, tiempo)

4. **Si error: aplicar self-healing (CORE-004)**
   - Intentar auto-recuperación
   - Usar recovery playbooks si es necesario

**Output**: Tarea ejecutada según plan.

### FASE 4: VALIDAR (Control de Calidad)

**Objetivo**: Verificar que el resultado cumple con los requisitos.

**Pasos**:
1. **Assertions cuantitativos (si aplica)**
   - Tests automatizados
   - Validaciones de formato
   - Métricas de calidad

2. **Revisión cualitativa**
   - ¿Cumple con el PRP/Blueprint?
   - ¿Sigue las convenciones del framework?
   - ¿Es MVI (Minimal Viable Information)?

3. **Benchmark vs baseline (si aplica)**
   - Comparar con versión anterior
   - Medir mejoras

4. **Self-healing: Si falla, aplicar recovery playbook**
   - Documentar fallo
   - Aplicar fix
   - Revalidar

**Output**: Resultado validado y aprobado.

### FASE 5: PRESERVAR (Knowledge)

**Objetivo**: Persistir el conocimiento para futuras sesiones.

**Pasos**:
1. **Guardar en sesión del día**
   - Actualizar `core/.context/sessions/YYYY-MM-DD.md`
   - Documentar decisiones y aprendizajes

2. **Actualizar codebase/ideas.md**
   - Ideas surgidas durante ejecución
   - Mejoras identificadas

3. **Actualizar codebase/recordatorios.md**
   - Tareas pendientes
   - Follow-ups necesarios

4. **Documentar errores en knowledge/errors/ (CORE-003)**
   - Si hubo errores, documentarlos
   - Crear playbooks si es recurrente

**Output**: Conocimiento preservado para el futuro.

## Flujo Completo

```
DELIMITAR → MAPEAR → EJECUTAR → VALIDAR → PRESERVAR
    ↑___________________________________________↓
              (Mejora continua)
```

## Herramientas y Recursos

### Subagentes
- `@context-scout`: Descubrimiento de contexto
- `@skill-evaluator`: Evaluación de calidad
- `@doc-writer`: Documentación MVI
- `@session-manager`: Gestión de sesión

### Scripts
- `core/scripts/session-start.py`: Inicia sesión con contexto
- `core/scripts/session-end.py`: Cierra y preserva
- `core/scripts/framework-guardian.py`: Validación

### Documentación
- [Workflow Standard](../WORKFLOW-STANDARD.md) - Proceso de 7 pasos macro
- [AGENTS.md](../../AGENTS.md) - Router principal

## Ejemplo Práctico: Dashboard SPA v2.0

**Tarea**: Migrar features del Dashboard SPA a v2.0

### FASE 1: DELIMITAR
- **Alcance**: Migrar timeline, filtros, interacciones
- **PRP**: PRD-Dashboard-SPA-v2.md
- **Recursos**: @dashboard-spa, @context-manager
- **Complejidad**: Complex (~45 min)

### FASE 2: MAPEAR
- @context-scout encuentra: docs/prd-dashboard-spa.md
- Skills necesarias: @dashboard-spa, @ui-ux-pro-max
- Contexto cargado: PRD completo

### FASE 3: EJECUTAR
- Delegar a @dashboard-spa: Generar componentes
- Aplicar MAGIC PROMPT 2
- Capturar métricas

### FASE 4: VALIDAR
- Revisión cualitativa del código
- Tests de componentes
- Benchmark vs v1.0

### FASE 5: PRESERVAR
- Sesión actualizada con cambios
- Insights documentados
- Recordatorios de follow-up

## Validación y Verificación

- [ ] ¿Delimité claramente el alcance?
- [ ] ¿Mapeé todo el contexto necesario?
- [ ] ¿Ejecuté con todos los recursos disponibles?
- [ ] ¿Validé el resultado contra requisitos?
- [ ] ¿Preservé el conocimiento en KB?

## Referencias

- [AGENTS.md](../../AGENTS.md) - Router principal del framework
- [Workflow Standard](../WORKFLOW-STANDARD.md) - Proceso macro de 7 pasos
- [Assembly Line](../ASSEMBLY-LINE.md) - Documentación completa

## Changelog

### v0.2.0-prealpha (2026-03-11)
- Versión inicial simplificada para release público
- Sanitizado: eliminados datos de desarrollo interno
- Agregado: ejemplo práctico Dashboard SPA
- Agregado: checklist de validación por fase
