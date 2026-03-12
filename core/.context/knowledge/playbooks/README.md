---
name: playbooks-index
version: "1.0.0"
last_updated: "2026-03-11"
description: Recovery playbooks for Error Recovery System (PRP-007)
---

# Error Recovery Playbooks

> **Sistema de recuperación documentada para errores recurrentes.** Cada playbook captura síntomas, causas raíz, soluciones y prevención.

**Versión**: 1.0.0  
**PRP**: [PRP-007 Error Recovery Playbooks](../../../../../docs/PRPs/PRP-007-Error-Recovery-Playbooks.md)  
**CORE**: [PRP-003 Antifragile Error Recovery](../../../../../docs/PRPs/PRP-003-CORE-Antifragile-Errors.md)

---

## Propósito

Los playbooks documentan soluciones probadas para errores recurrentes, permitiendo:

- **Respuesta rápida**: Soluciones listas para ejecutar
- **Aprendizaje institucional**: Conocimiento persistente
- **Prevención proactiva**: Patrones para evitar errores

---

## Estructura de un Playbook

```markdown
---
id: PB-XXX
category: encoding | file_operations | network | configuration | other
severity: low | medium | high | critical
frequency: rare | occasional | frequent
auto_generated: true | false
created: YYYY-MM-DD
last_used: YYYY-MM-DD
success_rate: 0-100
---

# PB-XXX: [Nombre del Error]

## Síntomas
- Qué se observa
- Mensajes de error típicos

## Causa Raíz
- Explicación técnica

## Soluciones

### Inmediata (Quick Fix)
Solución rápida para aplicar ahora.

### Permanente
Solución definitiva.

### Alternativas
Otras opciones si aplica.

## Prevención
- Cómo evitar este error

## Referencias
- Links relevantes
```

---

## Generación de Playbooks

### Automática (auto_generated: true)

El sistema puede generar playbooks automáticamente cuando:

1. Un error ocurre 3+ veces en 30 días
2. Un error requiere >15 minutos para resolver
3. Se detecta un patrón en `interactions/*.jsonl`

Script: `core/scripts/playbook-generator.py` (futuro)

### Manual (auto_generated: false)

Playbooks creados manualmente por:

- Documentación de errores complejos
- Soluciones descubiertas en sesiones
- Conocimiento transferido

---

## Índice de Playbooks

| ID | Categoría | Descripción | Severidad |
|----|-----------|-------------|-----------|
| [PB-001](./PB-001-encoding-errors.md) | encoding | Errores de codificación Windows | high |

Ver [`index.json`](./index.json) para datos estructurados.

---

## Uso

### Consulta Rápida

```bash
# Buscar por síntoma
grep -r "UnicodeEncodeError" core/.context/knowledge/playbooks/

# Ver índice
cat core/.context/knowledge/playbooks/index.json
```

### Durante una Sesión

Cuando encuentres un error:

1. Buscar en playbooks existentes
2. Si existe → aplicar solución documentada
3. Si no existe → resolver y crear nuevo playbook
4. Actualizar `last_used` y `success_rate`

---

## Categorías

| Categoría | Ejemplos |
|-----------|----------|
| `encoding` | UnicodeEncodeError, charmap, UTF-8 |
| `file_operations` | Permisos, archivos bloqueados |
| `network` | Timeout, conexión rechazada |
| `configuration` | Variables de entorno, paths |
| `other` | Errores no clasificados |

---

## Mantenimiento

- **Revisar mensualmente**: `success_rate`, `frequency`
- **Deprecar**: Playbooks con `success_rate < 50` después de 6 meses
- **Consolidar**: Playbooks duplicados o similares

---

> *"Cada error documentado es una lección permanente."*