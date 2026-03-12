---
id: feature-architect-modifications
name: Propuestas de Modificación para FeatureArchitect
description: Cambios propuestos al agente FeatureArchitect para soportar integración con dashboard-pro
version: 1.0.0
related: dashboard-pro/INTEGRATION.md
type: proposal
---

# Propuestas de Modificación: FeatureArchitect

## Resumen Ejecutivo

Este documento detalla los cambios necesarios en `@feature-architect` para habilitar la integración con `@dashboard-pro`. Los cambios son **no-breaking** y siguen el principio MVI (Minimal Viable Information).

**Impacto**: Bajo-Medio  
**Es fuerzo**: ~2 horas de implementación  
**Riesgo**: Bajo (cambios aditivos)

---

## Cambios Propuestos

### 1. Agregar Dependencia en YAML Frontmatter

**Archivo**: `core/agents/subagents/feature-architect.md`  
**Líneas**: 11-17 (sección dependencies)

**Cambio**:
```yaml
dependencies:
  - skill:prd-generator
  - skill:task-management
  - skill:dashboard-pro  # NUEVO: Dependencia opcional
  - context:core/.context/MASTER.md
  - context:core/.context/codebase/backlog.md
  - context:core/agents/AGENTS.md
  - context:core/skills/SKILLS.md
  - context:core/skills/catalog.json
```

**Justificación**: FeatureArchitect necesita saber que puede delegar a dashboard-pro. La dependencia es opcional pero recomendada.

---

### 2. Extender Protocolo de Evaluación - Paso 5

**Archivo**: `core/agents/subagents/feature-architect.md`  
**Ubicación**: Después del Paso 4 de "Protocolo de Evaluación (The Filter)"
**Línea de referencia**: ~186

**Cambio**:
```markdown
### Paso 5: Skills Especializadas

Si la feature involucra componentes especializados, evaluar necesidad de skills adicionales:

**Detección de Dashboard (NUEVO)**:
- [ ] Revisar descripción de feature para keywords: ["dashboard", "analytics", "métricas", "gráficos", "reportes", "KPIs", "visualización"]
- [ ] Si se detecta keyword:
  - [ ] Verificar disponibilidad de `skill:dashboard-pro` en catalog.json
  - [ ] Determinar modo recomendado:
    - `sin-dependencias`: Prototipos, reportes puntuales, MVPs
    - `con-dependencias`: Apps completas, mantenimiento a largo plazo, integración con código existente
  - [ ] Seleccionar style_preset basado en contexto del proyecto
  - [ ] Agregar nota al PRD: "Requiere integración con dashboard-pro"

**Resultado:**
- [ ] **Requiere dashboard-pro** → Modo: [con-dependencias / sin-dependencias]
- [ ] **No requiere skills especializadas**

**Checklist de integración**:
- [ ] Skill disponible en catalog.json
- [ ] Inputs preparados desde PRD
- [ ] Modo determinado según complejidad
- [ ] Style_preset seleccionado
```

**Justificación**: FeatureArchitect debe detectar automáticamente cuando una feature requiere dashboard y preparar el contexto para delegación.

---

### 3. Extender Protocolo de Ejecución - Sub-paso 3b

**Archivo**: `core/agents/subagents/feature-architect.md`  
**Ubicación**: Dentro de "Protocolo de Ejecución", después del paso 3
**Línea de referencia**: ~216

**Cambio**:
```markdown
#### Sub-paso 3b: Ejecutar Skills Especializadas (NUEVO)

Si la feature fue marcada como "requiere dashboard-pro" en Paso 5 de la evaluación:

**3b.1 Preparar Inputs**:
```
Extraer del PRD:
- app_description: Descripción detallada del dashboard (user stories + acceptance criteria)
- mode: [con-dependencias|sin-dependencias] (determinado en evaluación)
- chart_library: auto (default) o específico según necesidades
- style_preset: [fintech-dark|fintech-light|saas-modern|enterprise] (basado en contexto)
- context:
  - feature_id: BL-XXX
  - project_context: [Contexto del proyecto]
  - user_persona: [Quién usará el dashboard]
```

**3b.2 Invocar Dashboard-pro**:
- Cargar skill dashboard-pro desde core/skills/core/dashboard-pro/
- Ejecutar workflow de dashboard-pro con los inputs preparados
- Monitorear ejecución y capturar logs

**3b.3 Recibir y Verificar Outputs**:
- Verificar que status == "success"
- Validar que existan:
  - design-brief.jsonc
  - dashboard_code (directorio o archivo)
  - IMPLEMENTATION.md
- Revisar métricas de complejidad
- Verificar notas de advertencia si existen

**3b.4 Integrar en Feature**:
- Mover entregables a workspace del proyecto: `workspaces/{project}/dashboards/BL-XXX/`
- Actualizar PRD con rutas de entregables generados
- Agregar sección "Entregables de Dashboard" al PRD
- Documentar integración en IMPLEMENTATION.md de la feature

**3b.5 Comandos de Soporte**:
```bash
# Verificar disponibilidad de skill
python core/scripts/skill-check.py dashboard-pro

# Verificar entregables
python core/scripts/verify-deliverable.py --feature BL-XXX --type dashboard

# Integrar entregables
python core/scripts/integrate-deliverable.py --feature BL-XXX --source workspaces/temp/ --target workspaces/{project}/
```
```

**Justificación**: Protocolo claro para la delegación, ejecución, verificación e integración del dashboard generado.

---

### 4. Agregar Sección de Integración con Skills Especializadas

**Archivo**: `core/agents/subagents/feature-architect.md`  
**Ubicación**: Nueva sección antes del cierre (antes de "Reglas de Calidad")
**Línea de referencia**: ~288

**Cambio**:
```markdown
## Integración con Skills Especializadas

FeatureArchitect puede delegar a skills especializadas para componentes específicos de las features. Esto permite reutilizar capacidades probadas y mantener consistencia.

### Dashboard-Pro Integration

**Cuándo delegar**:
- La feature contiene keywords: dashboard, analytics, métricas, gráficos, reportes, KPIs
- Se requiere visualización de datos profesional
- El usuario necesita una interfaz de reporting

**Flujo de integración**:
```
Detección (Paso 5) 
    ↓
Preparación de inputs desde PRD
    ↓
Delegación a @dashboard-pro
    ↓
Generación de entregables
    ↓
Verificación de calidad
    ↓
Integración en workspace del proyecto
    ↓
Actualización de documentación
```

**Responsabilidades**:

| FeatureArchitect | Dashboard-pro |
|-----------------|---------------|
| Detectar necesidad | Generar código del dashboard |
| Preparar contexto | Crear design brief |
| Determinar modo/style | Implementar gráficos y UI |
| Orquestar ejecución | Verificar calidad visual |
| Integrar entregables | Documentar implementación |
| Actualizar backlog | Retornar métricas |

**Verificación de entregables**:
- [ ] design-brief.jsonc existe y es JSON válido
- [ ] dashboard_code generado sin errores de sintaxis
- [ ] IMPLEMENTATION.md documenta el entregable
- [ ] Métricas de complejidad razonables (score 1-10)
- [ ] No hay advertencias críticas en verification

**Manejo de errores**:
- Si status == "failed": Reintentar con inputs ajustados o escalar a usuario
- Si status == "partial": Revisar advertencias y determinar si es aceptable
- Si skill no disponible: Registrar en backlog como dependencia pendiente

**Ejemplo de invocación**:
```markdown
**Contexto**: BL-042 requiere dashboard de analytics

**Acción**: Invocar dashboard-pro con:
- app_description: "[Extraído del PRD] Dashboard de analytics..."
- mode: "con-dependencias"
- style_preset: "fintech-dark"
- context: { feature_id: "BL-042", project_context: "..." }

**Resultado esperado**: Proyecto Next.js generado en workspaces/dashboards/BL-042/
```
```

**Justificación**: Documentación completa de la integración para referencia futura y mantenimiento.

---

### 5. Actualizar Workflow de Trabajo (Diagrama)

**Archivo**: `core/agents/subagents/feature-architect.md`  
**Ubicación**: Sección "Workflow de Trabajo"
**Línea de referencia**: ~295

**Cambio**:
Reemplazar el diagrama existente con versión actualizada que incluya la rama de skills especializadas:

```markdown
## Workflow de Trabajo

```
Usuario solicita feature
        ↓
[Bootstrap] Leo contexto
        ↓
[Clarificación] ¿Falta info?
   ↓ Si              ↓ No
Pregunto        [Evaluación]
   ↓                  ↓
Respuesta       ¿Pasa The Filter?
   ↓              ↓ Si    ↓ No
Continuar    [Paso 5]   Reformulo
            ¿Dashboard?   o Rechazo
            ↓ Si   ↓ No
    [Delegar a      [Ejecución
     dashboard-pro]  Estándar]
            ↓              ↓
    [Integrar] ←──────┘
            ↓
    Documento
            ↓
    Actualizo backlog
```

**Notas**:
- Paso 5 evalúa necesidad de skills especializadas
- Si requiere dashboard → Delega a dashboard-pro
- Si no → Ejecución estándar
- Ambos caminos convergen en integración y documentación
```

**Justificación**: El diagrama actualizado refleja el nuevo flujo con integración de skills.

---

## Checklist de Implementación

### Pre-implementación
- [ ] Revisar y aprobar este documento
- [ ] Verificar que dashboard-pro esté en catalog.json
- [ ] Crear script `skill-check.py` (opcional pero recomendado)
- [ ] Crear script `verify-deliverable.py` (opcional pero recomendado)

### Implementación
- [ ] Cambio 1: Agregar dependencia en YAML
- [ ] Cambio 2: Extender Protocolo de Evaluación
- [ ] Cambio 3: Extender Protocolo de Ejecución
- [ ] Cambio 4: Agregar sección de Integración
- [ ] Cambio 5: Actualizar Workflow

### Post-implementación
- [ ] Probar integración con feature de ejemplo
- [ ] Actualizar versión de feature-architect (0.1.0 → 0.2.0)
- [ ] Documentar en changelog
- [ ] Notificar a usuarios del framework

---

## Notas de Implementación

### Compatibilidad Hacia Atrás

Todos los cambios son **aditivos**:
- No se modifican protocolos existentes, solo se extienden
- Skills especializadas son opcionales
- Si dashboard-pro no está disponible, FA opera en modo degradado

### Escenarios de Edge Case

1. **Skill no disponible**: FA registra en backlog "requiere instalar dashboard-pro"
2. **Delegación falla**: FA puede reintentar o escalar a usuario
3. **Múltiples skills**: El protocolo permite extensión a otras skills (ej: @pdf-exporter, @chart-generator)
4. **Feature puramente dashboard**: FA la trata como skill sin componentes adicionales

### Extensibilidad Futura

El protocolo diseñado permite fácil integración de otras skills:

```yaml
# Ejemplo futuro
dependencies:
  - skill:prd-generator
  - skill:task-management
  - skill:dashboard-pro
  - skill:pdf-exporter      # Futuro
  - skill:chart-generator   # Futuro
  - skill:api-generator     # Futuro
```

Cada skill seguiría el mismo patrón: detección → evaluación → delegación → integración.

---

## Métricas de Éxito

Para medir el éxito de la integración:

1. **Tiempo de desarrollo**: Reducción en tiempo para features con dashboard
2. **Consistencia**: Dashboards generados siguen estándares del framework
3. **Trazabilidad**: 100% de features con dashboard tienen BL-XXX vinculado
4. **Satisfacción**: Feedback positivo de usuarios sobre calidad de dashboards

---

**Documento preparado por**: Arquitecto de Software  
**Fecha**: 2026-02-24  
**Estado**: Listo para implementación  
**Prioridad**: Media-Alta
