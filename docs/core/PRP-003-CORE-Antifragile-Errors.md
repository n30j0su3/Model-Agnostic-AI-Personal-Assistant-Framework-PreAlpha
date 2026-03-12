---
title: "CORE-003: Antifragile Error Recovery"
version: "0.2.0-prealpha"
type: "process"
scope: "public"
prp: "PRP-003"
---

# CORE-003: Antifragile Error Recovery

## Principio Fundamental

**DOCUMENTAR cada error, fortalecer la base de conocimientos, aprender y mejorar para la siguiente iteración.**

> "El error como combustible para hacer el sistema más fuerte" - Concepto de Antifragilidad (Taleb)

## Descripción

El proceso CORE-003 implementa el concepto de "Autoblindaje": cada error documentado y analizado fortalece el framework, creando un sistema que mejora con el stress/errores en lugar de degradarse.

Este principio asegura:
- Cada error hace el framework más fuerte
- Recovery playbooks para errores recurrentes
- Base de conocimiento de errores estructurada
- Menos tiempo en debug en el futuro

## Objetivos

1. Documentar errores estructuradamente
2. Analizar causas raíz sistemáticamente
3. Crear recovery playbooks para errores recurrentes
4. Actualizar skills/agentes para evitar recurrencia

## Cuándo Aplicar

- **Cuando ocurre cualquier error**: Documentar inmediatamente
- **Errores recurrentes**: Crear recovery playbook
- **Después de solucionar**: Analizar y aprender
- **Al cerrar sesión**: Revisar errores del día

## Flujo de Trabajo

### Paso 1: Documentar Inmediatamente

Cuando ocurre un error, registrar en:

```
core/.context/knowledge/errors/
├── error-log.md          # Log legible
├── index.json            # Índice estructurado
└── YYYY-MM/              # Organizado por mes
    └── error-001.json    # Error individual
```

**Información a capturar**:
- Timestamp
- Tipo de error
- Contexto (qué se intentaba hacer)
- Stack trace (si aplica)
- Solución aplicada

### Paso 2: Analizar Error

Análisis de causa raíz:
1. ¿Qué causó el error?
2. ¿Por qué no se detectó antes?
3. ¿Cómo se solucionó?
4. ¿Puede prevenirse en el futuro?

### Paso 3: ¿Error Recurrente?

**SÍ → Generar Recovery Playbook**

Crear en `core/.context/knowledge/playbooks/`:
- PB-XXX-error-name.md
- Pasos de diagnóstico
- Pasos de solución
- Verificación post-fix

**NO → Actualizar KB**

Agregar aprendizaje a:
- `core/.context/knowledge/learning/anti-patterns.md`
- `core/.context/knowledge/learning/best-practices.md`

### Paso 4: Mejorar Sistema

Actualizar para evitar recurrencia:
- Skills relacionadas
- Agentes afectados
- Documentación
- Checklists de validación

## Herramientas y Recursos

### Scripts
- `core/scripts/error_logger.py`: Logging dual (JSON + MD)
- `core/scripts/pattern_analyzer.py`: Analiza patrones de errores

### Knowledge Base
- `knowledge/errors/`: Logs de errores
- `knowledge/playbooks/`: Recovery playbooks
- `knowledge/learning/`: Anti-patterns y best practices

### Recovery Playbooks Existentes

| ID | Error | Archivo |
|----|-------|---------|
| PB-001 | Encoding Windows | PB-001-encoding-errors.md |
| PB-002 | File Not Found | PB-002-file-not-found.md |
| PB-003 | JSON Parsing | PB-003-json-parsing.md |

## Ejemplos Prácticos

### Ejemplo 1: UnicodeEncodeError

**Error**: `UnicodeEncodeError: 'charmap' codec can't encode`

**Flujo CORE-003**:
1. **Documentar**: Log en knowledge/errors/
2. **Analizar**: Error de encoding en Windows
3. **¿Recurrente?**: SÍ - Muy común
4. **Playbook**: PB-001-encoding-errors.md
5. **Solución**: Usar `encoding='utf-8'` en archivos

### Ejemplo 2: FileNotFoundError

**Error**: `FileNotFoundError: [Errno 2] No such file`

**Flujo CORE-003**:
1. **Documentar**: Log con contexto
2. **Analizar**: Ruta incorrecta o archivo no creado
3. **¿Recurrente?**: SÍ - Común en migraciones
4. **Playbook**: PB-002-file-not-found.md
5. **Solución**: Validar existencia antes de usar

### Ejemplo 3: Error Único

**Error**: Error específico de configuración local

**Flujo CORE-003**:
1. **Documentar**: Log completo
2. **Analizar**: Causa específica del entorno
3. **¿Recurrente?**: NO - Caso único
4. **KB**: Agregar a learnings del día
5. **Solución**: Fix local, documentar para referencia

## Estructura de Documentación

### Error Log (Markdown)
```markdown
## Error: [Tipo] - [Descripción breve]

**Fecha**: YYYY-MM-DD HH:MM
**Contexto**: [Qué se intentaba hacer]
**Error**: [Mensaje completo]
**Causa**: [Análisis de causa raíz]
**Solución**: [Pasos aplicados]
**Prevención**: [Cómo evitar en futuro]
```

### Recovery Playbook
```markdown
# PB-XXX: [Nombre del Error]

## Síntomas
- [Síntoma 1]
- [Síntoma 2]

## Diagnóstico
1. [Paso de diagnóstico]
2. [Verificación]

## Solución
1. [Paso 1]
2. [Paso 2]

## Verificación
- [ ] [Check 1]
- [ ] [Check 2]
```

## Validación y Verificación

- [ ] ¿Documenté el error inmediatamente?
- [ ] ¿Analicé la causa raíz?
- [ ] ¿Determiné si es recurrente?
- [ ] ¿Creé playbook si es recurrente?
- [ ] ¿Actualicé KB con aprendizaje?
- [ ] ¿Mejoré el sistema para prevenir recurrencia?

## Referencias

- [AGENTS.md](../../AGENTS.md) - Router principal
- [Playbooks](../core/.context/knowledge/playbooks/) - Recovery playbooks
- [Error Log](../core/.context/knowledge/errors/) - Logs de errores

## Changelog

### v0.2.0-prealpha (2026-03-11)
- Versión inicial simplificada para release público
- Sanitizado: eliminados datos de desarrollo interno
- Agregado: ejemplos prácticos de aplicación
- Agregado: estructura de documentación
