# Guía de Integración con el Ecosistema de Skills

Guía para integrar nuevas skills con el ecosistema existente del framework FreakingJSON.

## Por Qué Integrar es Importante

Las skills aisladas son útiles, pero las skills integradas son **poderosas**. La integración permite:

- Workflows fluidos entre skills
- Reutilización de funcionalidad
- UX consistente para el usuario
- Menor duplicación de código

## Proceso de Integración

### Paso 1: Identificar Skills Relacionadas

Antes de crear una skill, investigar qué skills existentes:

- Procesan formatos similares
- Podrían ser upstream/downstream en workflows
- Tienen funcionalidad complementaria

**Herramienta**: Usar @context-scout para descubrir skills relacionadas.

**Ejemplo - @csv-processor**:
Al crear @csv-processor, identificamos:
- @etl: Para pipelines ETL complejos
- @xlsx: Para convertir CSV → Excel
- @docx/@pptx: Para exportar datos a documentos
- @data-viz: Para visualizar datos CSV

### Paso 2: Definir Relaciones

Documentar en SKILL.md cómo se relaciona con otras skills:

```markdown
## Integración con Otras Skills

| Skill | Relación | Flujo de Trabajo |
|-------|----------|------------------|
| @etl | Complementaria | CSV → @etl (transformaciones complejas) → Output |
| @xlsx | Downstream | @csv-processor (limpieza) → @xlsx (formateo) → Excel |
| @docx | Downstream | Datos CSV → @docx (tablas en Word) |
| @pptx | Downstream | Datos CSV → @pptx (slides) |
| @data-viz | Paralela | CSV → @data-viz (gráficos) |
```

**Tipos de Relaciones**:

- **Upstream**: Skills que producen input para tu skill
- **Downstream**: Skills que consumen output de tu skill
- **Complementaria**: Skills que trabajan juntas en paralelo
- **Alternativa**: Skills que resuelven problemas similares (cuándo usar cada una)

### Paso 3: Validar Compatibilidad

Verificar que las skills sean compatibles:

- [ ] **Formatos de entrada/salida**: ¿Los formatos son compatibles?
- [ ] **Dependencias**: ¿No hay conflictos de versiones?
- [ ] **Estándares**: ¿Todas siguen @python-standards?
- [ ] **No duplicación**: ¿No estás reimplementando funcionalidad existente?

**Ejemplo - Compatibilidad @csv-processor**:
- @etl puede leer CSV → Compatible ✅
- @xlsx puede crear Excel desde DataFrame → Compatible ✅
- @docx puede insertar tablas → Compatible ✅

### Paso 4: Documentar Workflows

Incluir ejemplos de workflows integrados:

```markdown
### Flujo 1: Limpieza → Excel → Documento

```
CSV sucio → @csv-processor (limpieza) → @xlsx (formateo) → @docx (reporte)
```

**Uso**:
```bash
# 1. Limpiar CSV
python core/skills/core/csv-processor/scripts/csv_processor.py \
    datos_sucios.csv datos_limpios.csv --mode clean

# 2. Convertir a Excel
python core/skills/core/csv-processor/scripts/csv_processor.py \
    datos_limpios.csv datos.xlsx --mode convert

# 3. Crear documento Word con @docx
# (usar skill @docx para insertar tabla)
```

### Flujo 2: Análisis → Visualización → Presentación

```
CSV → @csv-processor (agregaciones) → @data-viz (gráficos) → @pptx (slides)
```
```

### Paso 5: Pruebas de Integración

Probar los workflows completos:

```bash
# Test de integración ejemplo
python test_integration.py --workflow "csv-to-excel"
```

**Checklist de pruebas**:
- [ ] Flujo completo ejecuta sin errores
- [ ] Output de skill A es input válido para skill B
- [ ] Formatos intermedios son correctos
- [ ] Errores se manejan graceful

## Ejemplo de Éxito: @csv-processor

### Análisis de Integraciones

| Skill | Relación | Justificación |
|-------|----------|---------------|
| @etl | Complementaria | @csv-processor es especialización de ETL para CSV; @etl maneja pipelines más complejos |
| @xlsx | Downstream | Usuarios frecuentemente convierten CSV limpio a Excel para reporting |
| @docx | Downstream | Exportar datos procesados a documentos Word |
| @pptx | Downstream | Crear presentaciones con datos CSV |
| @data-viz | Paralela | Visualización es paso natural después de limpieza de datos |

### Workflows Documentados

```markdown
## Flujos de Integración Recomendados

#### Flujo 1: Limpieza → Excel → Documento
```
CSV sucio → @csv-processor (limpieza) → @xlsx (formateo) → @docx (reporte)
```

#### Flujo 2: Análisis → Visualización → Presentación
```
CSV → @csv-processor (agregaciones) → @data-viz (gráficos) → @pptx (slides)
```

#### Flujo 3: Pipeline ETL Completo
```
Múltiples CSV → @csv-processor (normalización) → @etl (joins/transformaciones) → Output
```
```

### Beneficios de esta Integración

1. **Usuario puede elegir**: Usar solo @csv-processor o combinar con otras skills
2. **No duplicación**: @csv-processor no reimplementa funcionalidad de @etl
3. **Workflows poderosos**: Combinaciones crean capacidades mayores
4. **Documentación clara**: Usuarios entienden cuándo usar cada skill

## Anti-Patrones a Evitar

### 1. Duplicar Funcionalidad

❌ **Mal**: Crear @mi-procesador-csv que hace lo mismo que @csv-processor

✅ **Bien**: Extender @csv-processor con funcionalidad específica, o crear skill que lo use

### 2. Dependencias Circulares

❌ **Mal**: @skill-a depende de @skill-b, y @skill-b depende de @skill-a

✅ **Bien**: Diseñar arquitectura donde el flujo sea unidireccional

### 3. Acoplamiento Fuerte

❌ **Mal**: @skill-a solo funciona con @skill-b específico

✅ **Bien**: @skill-a funciona standalone, mejora con @skill-b

### 4. Documentación Incompleta

❌ **Mal**: No documentar relaciones con otras skills

✅ **Bien**: Tabla clara de integraciones en SKILL.md

## Checklist de Integración

Al crear una nueva skill, verificar:

- [ ] Identifiqué skills relacionadas con @context-scout
- [ ] Documenté relaciones en SKILL.md (tabla)
- [ ] Definí workflows de integración
- [ ] Validé compatibilidad de formatos
- [ ] Probé al menos 2 workflows de integración
- [ ] No dupliqué funcionalidad existente
- [ ] Documenté cuándo usar mi skill vs alternativas

## Referencias

- [Ejemplo @csv-processor](../../csv-processor/SKILL.md) - Ejemplo de integración completa
- [Ejemplo @etl](../../etl/SKILL.md) - Skill que complementa a otras
- [Context Scout](../../subagents/context-scout.md) - Para descubrir skills relacionadas
