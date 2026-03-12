---
title: "CORE-002: Context-Aware Discovery"
version: "0.2.0-prealpha"
type: "process"
scope: "public"
prp: "PRP-002"
---

# CORE-002: Context-Aware Discovery

## Principio Fundamental

**SIEMPRE validar si existe un archivo .md de contexto (instrucciones, README, agents, etc.) en el directorio de trabajo antes de iniciar cualquier tarea.**

## Descripción

El proceso CORE-002 obliga a los agentes AI a descubrir y cargar el contexto específico del proyecto antes de comenzar a trabajar. Esto asegura que se respeten convenciones, reglas y configuraciones particulares de cada proyecto.

Este principio evita:
- Ignorar convenciones del proyecto
- Redundancia de información
- Inconsistencias entre sesiones
- Trabajo fuera de especificaciones

## Objetivos

1. Respetar convenciones específicas del proyecto
2. Evitar redundancias de contexto
3. Mejorar calidad del output desde el inicio
4. Reducir correcciones necesarias

## Cuándo Aplicar

- **Al iniciar sesión en nuevo workspace**: Detectar contexto
- **Antes de cualquier tarea**: Verificar archivos de configuración
- **Al cambiar de directorio**: Re-evaluar contexto
- **En directorios desconocidos**: Siempre buscar instrucciones

## Flujo de Trabajo

### Paso 1: @context-scout Busca Archivos

El subagente @context-scout escanea automáticamente:

```bash
# Archivos de contexto buscados:
- README.md
- AGENTS.md
- INSTRUCTIONS.md
- .cursorrules
- CONTRIBUTING.md
- *.md en raíz del proyecto
```

### Paso 2: Identificar Contexto Relevante

Prioridad de archivos:
1. **AGENTS.md**: Instrucciones específicas para agentes AI
2. **README.md**: Contexto general del proyecto
3. **INSTRUCTIONS.md**: Guías específicas
4. **.cursorrules**: Reglas de Cursor IDE (si aplica)
5. **Otros .md**: Documentación adicional

### Paso 3: Cargar Contexto en Sesión

El contexto encontrado se integra automáticamente en:
- Instrucciones de sesión
- Preferencias del proyecto
- Convenciones a seguir

## Herramientas y Recursos

### Subagentes
- `@context-scout`: Descubre archivos de contexto
- `@session-manager`: Gestiona contexto de sesión

### Scripts
- `core/scripts/session-start.py`: Carga contexto automáticamente
- `core/scripts/context-scout.py`: Búsqueda manual de contexto

### Archivos de Contexto

| Archivo | Propósito | Prioridad |
|---------|-----------|-----------|
| AGENTS.md | Instrucciones para agentes AI | Alta |
| README.md | Contexto general del proyecto | Media |
| INSTRUCTIONS.md | Guías específicas | Media |
| .cursorrules | Reglas de IDE | Baja |
| CONTRIBUTING.md | Guías de contribución | Baja |

## Ejemplos Prácticos

### Ejemplo 1: Proyecto con AGENTS.md

**Contexto detectado**: `AGENTS.md` con instrucciones específicas

✅ **Acción correcta**:
1. Leer AGENTS.md completamente
2. Seguir instrucciones específicas del proyecto
3. Usar skills mencionadas
4. Respetar convenciones documentadas

### Ejemplo 2: Proyecto con .cursorrules

**Contexto detectado**: `.cursorrules` con reglas de estilo

✅ **Acción correcta**:
1. Leer reglas de estilo
2. Aplicar convenciones de código
3. Seguir patrones especificados
4. Mantener consistencia

### Ejemplo 3: Sin contexto específico

**Contexto detectado**: Ningún archivo de contexto

✅ **Acción correcta**:
1. Proceder con contexto genérico del framework
2. Usar convenciones estándar
3. Documentar decisiones en codebase/
4. Considerar crear AGENTS.md para el proyecto

## Patrones de Contexto Comunes

### Patrón 1: Framework Web
```markdown
AGENTS.md:
- Usar @ui-ux-pro-max para diseño
- Seguir design-system en design-system/
- Componentes en workspaces/components/
```

### Patrón 2: Procesamiento de Datos
```markdown
AGENTS.md:
- Usar @etl para transformaciones
- @csv-processor para archivos CSV
- @xlsx para reportes Excel
```

### Patrón 3: Documentación
```markdown
AGENTS.md:
- Usar @markdown-writer para consistencia
- Seguir MVI (Minimal Viable Information)
- Documentar en docs/
```

## Validación y Verificación

- [ ] ¿Ejecuté session-start.py al iniciar?
- [ ] ¿Se detectaron archivos de contexto?
- [ ] ¿Leí completamente AGENTS.md (si existe)?
- [ ] ¿Estoy aplicando las convenciones del proyecto?
- [ ] ¿Respeté las instrucciones específicas?

## Referencias

- [AGENTS.md](../../AGENTS.md) - Router principal del framework
- [@context-scout](../../core/agents/subagents/context-scout.md) - Subagente de descubrimiento
- [Workflow Standard](../WORKFLOW-STANDARD.md) - Proceso de 7 pasos

## Changelog

### v0.2.0-prealpha (2026-03-11)
- Versión inicial simplificada para release público
- Sanitizado: eliminados datos de desarrollo interno
- Agregado: priorización de archivos de contexto
- Agregado: patrones de contexto comunes
