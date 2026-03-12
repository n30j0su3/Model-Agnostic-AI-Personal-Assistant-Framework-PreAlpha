# Assembly Line — Proceso CORE-005

> **Bucle Agentico**: Delimitar → Mapear → Ejecutar → Validar → Preservar  
> **Complementario al Workflow Standard de 7 pasos**

---

## Visión General

El Assembly Line es un proceso CORE estandarizado para tareas complejas que asegura calidad en cada etapa mediante un flujo definido: Delimitar → Mapear → Ejecutar → Validar → Preservar.

**Relación con Workflow Standard**:
- El Workflow Standard define las 7 fases macro de cualquier tarea
- El Assembly Line es el motor de ejecución para las tareas complejas
- Los PRPs (Blueprints) guían el proceso

---

## Diagrama de Flujo

```
┌─────────────────────────────────────────────────────────────────┐
│                    FASE 1: DELIMITAR                             │
│                      (Planificación)                             │
├─────────────────────────────────────────────────────────────────┤
│ • Definir alcance claro                                          │
│ • Crear/validar PRP (Blueprint)                                  │
│ • Identificar recursos necesarios (skills, agents, MCPs)         │
│ • Estimar complejidad                                            │
└────────────────────────────────┬────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                    FASE 2: MAPEAR                                │
│                   (Descubrimiento)                               │
├─────────────────────────────────────────────────────────────────┤
│ • @context-scout descubre archivos relevantes                    │
│ • Buscar archivos .md de contexto (CORE-002)                     │
│ • Validar dependencias contra SKILLS.md (CORE-001)               │
│ • Cargar contexto necesario                                      │
└────────────────────────────────┬────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                   FASE 3: EJECUTAR                               │
│                    (Subtareas)                                   │
├─────────────────────────────────────────────────────────────────┤
│ • Aplicar MAGIC PROMPT 2:                                        │
│   "Recuerda desplegar agentes para optimizar recursos/tokens/etc.│
│    Usar los recursos/skills/agentes del framework.               │
│    Si un error bloquea el avance, ARREGLALO.                     │
│    No lo reportes esperando respuesta."                          │
│ • Delegar a subagentes según especialidad                        │
│ • Ejecutar workflow                                              │
│ • Capturar métricas (tokens, tiempo)                             │
│ • Si error: aplicar self-healing (CORE-004)                      │
└────────────────────────────────┬────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                   FASE 4: VALIDAR                                │
│               (Control de Calidad)                               │
├─────────────────────────────────────────────────────────────────┤
│ • Assertions cuantitativos (si aplica)                           │
│ • Revisión cualitativa                                           │
│ • Benchmark vs baseline (si aplica)                              │
│ • Self-healing: Si falla, aplicar recovery playbook              │
│ • Validar contra PRP (Blueprint)                                 │
└────────────────────────────────┬────────────────────────────────┘
                                 │
                                 ▼
┬─────────────────────────────────────────────────────────────────┐
│                  FASE 5: PRESERVAR                               │
│                  (Knowledge)                                     │
├─────────────────────────────────────────────────────────────────┤
│ • Guardar en sesión del día                                      │
│ • Actualizar codebase/ideas.md                                   │
│ • Actualizar codebase/recordatorios.md                           │
│ • Documentar errores en knowledge/errors/ (CORE-003)             │
└─────────────────────────────────────────────────────────────────┘
```

---

## Fases Detalladas

### FASE 1: DELIMITAR (Planificación)

**Objetivo**: Definir claramente qué se va a hacer y cómo.

**Pasos**:
1. **Definir alcance**
   - ¿Qué está incluido?
   - ¿Qué está excluido?
   - ¿Cuáles son los entregables?

2. **Crear/validar PRP (Blueprint)**
   - Si no existe PRP, crear uno en `/PRPs/`
   - Si existe, validar que aplica
   - El PRP es el "plano" que guía la ejecución

3. **Identificar recursos**
   - ¿Qué skills del framework se necesitan?
   - ¿Qué subagentes se deben desplegar?
   - ¿Hay MCPs relevantes?

4. **Estimar complejidad**
   - Simple: 1-3 archivos, sin dependencias
   - Compleja: Múltiples archivos, dependencias
   - Crítica: Afecta arquitectura, datos sensibles

**Output**: PRP validado, alcance definido, recursos identificados.

---

### FASE 2: MAPEAR (Descubrimiento)

**Objetivo**: Descubrir y cargar todo el contexto necesario.

**Pasos**:
1. **@context-scout descubre archivos**
   - Archivos relevantes para la tarea
   - Patrones de código existentes
   - Dependencias

2. **Buscar archivos .md de contexto (CORE-002)**
   - `AGENTS.md`
   - `README.md`
   - `INSTRUCTIONS.md`
   - `.cursorrules`
   - Cualquier `.md` en directorio raíz

3. **Validar dependencias contra SKILLS.md (CORE-001)**
   - ¿Existe skill para esta tarea?
   - ¿Debo usar skill o crear solución?
   - Consultar checklist de skills

4. **Cargar contexto necesario**
   - Leer archivos de contexto
   - Cargar en sesión activa
   - No cargar archivos irrelevantes

**Output**: Contexto descubierto y cargado, dependencias validadas.

---

### FASE 3: EJECUTAR (Subtareas)

**Objetivo**: Ejecutar la tarea con los recursos óptimos.

**Pasos**:
1. **Aplicar MAGIC PROMPT 2** (Instrucción permanente):
   > "Recuerda desplegar agentes para optimizar recursos/tokens/etc. 
   > Usar los recursos/skills/agentes del framework. 
   > Si un error bloquea el avance, ARREGLALO. No lo reportes esperando respuesta."

2. **Delegar a subagentes según especialidad**
   - `@context-scout` para descubrimiento
   - `@session-manager` para gestión de sesiones
   - `@doc-writer` para documentación
   - `@skill-evaluator` para evaluación

3. **Ejecutar workflow**
   - Seguir instrucciones del PRP
   - Usar skills identificadas
   - Aplicar mejores prácticas

4. **Capturar métricas**
   - Tokens usados
   - Tiempo transcurrido
   - Pasos ejecutados

5. **Si error: aplicar self-healing (CORE-004)**
   - Documentar error
   - Consultar recovery playbook
   - Intentar recuperación
   - Escalar si no se recupera

**Output**: Tarea ejecutada, métricas capturadas, errores manejados.

---

### FASE 4: VALIDAR (Control de Calidad)

**Objetivo**: Asegurar que el resultado cumple con los requisitos.

**Pasos**:
1. **Assertions cuantitativos (si aplica)**
   - Validaciones automáticas
   - Tests unitarios
   - Checklist de criterios

2. **Revisión cualitativa**
   - ¿El resultado cumple el objetivo?
   - ¿Sigue las convenciones del proyecto?
   - ¿Es mantenible?

3. **Benchmark vs baseline (si aplica)**
   - Comparar con versión anterior (si mejora)
   - Comparar sin skill (si nueva skill)
   - Métricas: pass rate, tiempo, tokens

4. **Self-healing: Si falla, aplicar recovery playbook**
   - Si hay errores, intentar recuperación
   - Documentar fallos
   - Generar nuevo playbook si es necesario

5. **Validar contra PRP (Blueprint)**
   - ¿Se cumplieron los requisitos del PRP?
   - ¿El alcance fue respetado?
   - ¿Los entregables son correctos?

**Output**: Validación completa, feedback documentado, aprobación/rechazo.

---

### FASE 5: PRESERVAR (Knowledge)

**Objetivo**: Guardar el conocimiento generado para futuras sesiones.

**Pasos**:
1. **Guardar en sesión del día**
   - Temas tratados
   - Decisiones tomadas
   - Pendientes generados

2. **Actualizar codebase/ideas.md**
   - Ideas surgidas
   - Descubrimientos
   - Mejoras potenciales

3. **Actualizar codebase/recordatorios.md**
   - Pendientes nuevos
   - Tareas de seguimiento
   - Recordatorios

4. **Documentar errores en knowledge/errors/ (CORE-003)**
   - Si hubo errores, documentarlos
   - JSON estructurado + MD legible
   - Enlazar con recovery playbooks

**Output**: Conocimiento persistido, sesión actualizada, errores documentados.

---

## Relación con Workflow Standard

| Workflow Standard | Assembly Line | Descripción |
|-------------------|---------------|-------------|
| 1. Inicialización | - | Setup previo al Assembly Line |
| 2. Detección Complejidad | Fase 1: Delimitar | Decide si usar Assembly Line |
| 3. Comprensión | Fase 2: Mapear | Entender el contexto |
| 4. Planificación | Fase 1: Delimitar | Crear/validar PRP |
| 5. Ejecución | Fase 3: Ejecutar | Hacer el trabajo |
| 6. Validación | Fase 4: Validar | Verificar calidad |
| 7. Preservación | Fase 5: Preservar | Guardar conocimiento |

---

## Relación con Procesos CORE

| Proceso CORE | Fase del Assembly Line |
|--------------|------------------------|
| CORE-001: Framework-First | Fase 2: MAPEAR |
| CORE-002: Context-Aware | Fase 2: MAPEAR |
| CORE-003: Antifragile Errors | Fase 3: EJECUTAR, Fase 4: VALIDAR |
| CORE-004: Self-Healing | Fase 3: EJECUTAR |
| CORE-005: Assembly Line | Todo el proceso |

---

## PRPs como Blueprints

Los **PRPs (Product Requirements Proposals)** actúan como los **Blueprints** (planos) de la Assembly Line:

- **Fase 1 (Delimitar)**: Crea/valida el PRP
- **Fase 2 (Mapear)**: Usa el PRP para identificar recursos
- **Fase 3 (Ejecutar)**: Sigue el PRP para ejecutar
- **Fase 4 (Validar)**: Valida contra el PRP
- **Fase 5 (Preservar)**: Actualiza el PRP si es necesario

**Ubicación**: `/PRPs/PRP-XXX-*.md`

---

## MAGIC PROMPT 2

**Instrucción permanente** aplicada en Fase 3 (Ejecutar):

```markdown
"Recuerda desplegar agentes para optimizar recursos/tokens/etc. 
Usar los recursos/skills/agentes del framework. 
Si un error bloquea el avance, ARREGLALO. No lo reportes esperando respuesta."
```

Esta instrucción:
- Asegura uso óptimo de recursos
- Prioriza skills/agentes del framework
- Empodera al agente para arreglar errores
- Elimina bloqueos por espera de respuesta

---

## Cuándo Usar Assembly Line

### Usar Assembly Line para:
- Tareas complejas (múltiples archivos)
- Cambios estructurales
- Nuevas features
- Mejoras arquitectónicas
- Cualquier tarea con PRP

### Omitir Assembly Line para:
- Tareas simples (1-3 archivos)
- Cambios menores
- Fixes rápidos
- Tareas de rutina

**Nota**: Para tareas simples, usar modo **Express** del Workflow Standard (omitir planificación detallada con transparencia).

---

## Métricas de Éxito

| Métrica | Objetivo |
|---------|----------|
| Tiempo por fase | Variable según complejidad |
| Tasa de éxito | > 90% con PRP válido |
| Recuperación de errores | > 70% con self-healing |
| Uso de skills del framework | 100% |
| Documentación de errores | 100% |

---

## Checklist de Ejecución

### Pre-ejecución:
- [ ] PRP creado/validado
- [ ] Alcance definido
- [ ] Recursos identificados

### Durante ejecución:
- [ ] Contexto mapeado
- [ ] Skills validadas
- [ ] MAGIC PROMPT 2 aplicado
- [ ] Métricas capturadas

### Post-ejecución:
- [ ] Assertions pasan
- [ ] Revisión cualitativa completa
- [ ] Benchmark vs baseline (si aplica)
- [ ] Conocimiento preservado

---

## Referencias

- **PRP-005**: CORE-005 Assembly Line
- **docs/WORKFLOW-STANDARD.md**: Workflow Standard de 7 pasos
- **PRPs/*.md**: Blueprints/Planos
- **PRP-001 a PRP-004**: Procesos CORE relacionados

---

**Versión**: 1.0  
**Fecha**: 2026-03-10  
**Estado**: APPROVED

> *"Delimitar → Mapear → Ejecutar → Validar → Preservar"*  
> *"La calidad es resultado de proceso, no accidente."*
