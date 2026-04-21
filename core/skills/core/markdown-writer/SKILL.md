---
name: markdown-writer
description: Guía para escribir documentación Markdown de alta calidad siguiendo el principio MVI del framework FreakingJSON. Esta skill debe usarse cuando el usuario necesite crear o editar archivos .md en el framework, asegurando consistencia, claridad y adherencia al principio de Minimal Viable Information.
license: MIT
metadata:
  author: FreakingJSON Framework
  version: "1.0"
  created: 2026-02-11
compatibility: Python 3.8+ para scripts de utilidad.
---

# Markdown Writer

Toolkit para escribir documentación Markdown consistente y efectiva en el framework FreakingJSON, siguiendo el principio MVI (Minimal Viable Information).

## Casos de Uso

1. **Crear Sesiones Diarias**: Estructurar archivos de sesión en `core/.context/sessions/`
2. **Documentar Skills**: Escribir archivos SKILL.md para nuevas habilidades
3. **Capturar Ideas**: Formatear notas en `core/.context/codebase/ideas.md`
4. **Documentar Decisiones**: Crear ADRs (Architecture Decision Records)

## Cuándo Usar Esta Skill

Esta skill debe usarse cuando el usuario necesite:
- Crear o editar archivos Markdown en el framework
- Asegurar consistencia con el estilo del framework
- Aplicar el principio MVI a documentación existente
- Generar templates para nuevos documentos
- Validar formato Markdown según estándares del framework

## Instrucciones de Uso

### Paso 1: Identificar el Tipo de Documento

Determina qué tipo de documento necesita crear:

| Tipo | Ubicación | Template | Propósito |
|------|-----------|----------|-----------|
| **Sesión** | `sessions/YYYY-MM-DD.md` | `assets/templates/session-template.md` | Log diario de trabajo |
| **Skill** | `skills/core/{name}/SKILL.md` | `references/skill-template.md` | Documentación de skill |
| **Idea** | `codebase/ideas.md` | `assets/templates/idea-template.md` | Notas y descubrimientos |
| **ADR** | `codebase/decisions/` | `assets/templates/adr-template.md` | Decisiones arquitectónicas |

### Paso 2: Seleccionar el Template Apropiado

Usa el template base según el tipo de documento:

```markdown
# Cargar template
Leer archivo de template correspondiente de `assets/templates/`
Adaptar según necesidad específica
```

### Paso 3: Aplicar Principio MVI

Valida cada sección contra el principio MVI:

- **Máximo 1-3 oraciones** por concepto
- **3-5 bullets** por sección
- **Ejemplo mínimo** cuando aplique
- **Referencia** a docs completos, no duplicar

### Paso 4: Validar Formato

Ejecutar validación de formato:

```bash
python core/skills/core/markdown-writer/scripts/md-lint.py archivo.md
```

Verifica:
- [ ] YAML frontmatter válido (si aplica)
- [ ] No más de 5 bullets por lista
- [ ] Secciones con contenido apropiado
- [ ] Enlaces funcionales
- [ ] Consistencia de estilo

### Paso 5: Generar Tabla de Contenidos (Opcional)

Para documentos largos (>300 líneas):

```bash
python core/skills/core/markdown-writer/scripts/toc-generator.py archivo.md
```

## Ejemplos

### Ejemplo 1: Crear Sesión Diaria

```markdown
---
name: session-2026-02-11
date: 2026-02-11
workspace: Development
tags: [feature, api]
---

# Sesión 2026-02-11

**Inicio**: 09:00 AM  
**Workspace**: Development  
**Objetivo**: Implementar endpoint de autenticación

---

## Resumen

Implementación completa del endpoint POST /auth/login con JWT y rate limiting.

## Tareas Completadas

- [x] Diseñar schema de autenticación
- [x] Implementar endpoint básico
- [x] Agregar rate limiting
- [x] Escribir tests unitarios

## Decisiones

**Decisión**: Usar JWT con expiración de 24h  
**Razón**: Balance entre seguridad y UX  
**Alternativas**: Sessions (rechazado - stateful)

## Bloqueos

- Necesito acceso al servicio de email para reset de password

## Próximos Pasos

1. Configurar servicio de email
2. Implementar endpoint de reset
3. Documentar API

## Notas

- La librería `python-jose` funcionó bien
- Considerar refresh tokens en v2
```

### Ejemplo 2: Documentar una Idea

```markdown
## Idea: Sistema de Plugins para Skills

**Fecha**: 2026-02-11  
**Categoría**: Mejora Framework  
**Estado**: 📝 Borrador

### Descripción

Permitir que las skills se extiendan mediante plugins sin modificar el core.

### Motivación

- Facilitar contribuciones de la comunidad
- Reducir tamaño del core
- Permitir versionado independiente

### Implementación Propuesta

1. Definir interfaz IPlugin
2. Crear registry de plugins
3. Implementar loader dinámico
4. Agregar validación de compatibilidad

### Recursos

- [Plugin Architecture Pattern](https://example.com)
- Similar a sistema de VSCode extensions

### Siguientes Pasos

- [ ] Diseñar interfaz base
- [ ] Crear proof of concept
```

### Ejemplo 3: Architecture Decision Record (ADR)

```markdown
# ADR 001: Uso de SQLite para Almacenamiento de Contexto

**Estado**: Aceptado  
**Fecha**: 2026-02-11  
**Decisores**: @freakingjson-team

## Contexto

Necesitamos persistir contexto de sesiones entre ejecuciones del asistente.

## Decisión

Usar SQLite como almacenamiento principal para datos de contexto.

## Consecuencias

### Positivas

- Sin configuración adicional
- Portátil (archivo único)
- SQL estándar
- Buen rendimiento para <1GB

### Negativas

- No escalable a múltiples instancias
- Limitaciones de concurrencia
- Backup manual necesario

## Alternativas Consideradas

| Opción | Pros | Contras | Decisión |
|--------|------|---------|----------|
| PostgreSQL | Robustez | Overkill para local | Rechazado |
| JSON files | Simple | No consultas complejas | Rechazado |
| SQLite | Balance | Limitado | Aceptado |

## Referencias

- [SQLite When to Use](https://sqlite.org/whentouse.html)
```

## Recursos Disponibles

### Templates (`assets/templates/`)

- **`session-template.md`** - Estructura para sesiones diarias
- **`idea-template.md`** - Formato para capturar ideas
- **`adr-template.md`** - Architecture Decision Records
- **`readme-template.md`** - READMEs de proyectos

### Scripts (`scripts/`)

- **`md-lint.py`** - Valida formato MVI y estándares del framework
- **`toc-generator.py`** - Genera tabla de contenidos automática

### References (`references/`)

- **`mvi-guide.md`** - Guía detallada del principio MVI
- **`markdown-style.md`** - Guía de estilo específica del framework

## Mejores Prácticas

### 1. Siempre Usar Frontmatter para Documentos Estructurados

Los documentos en `sessions/`, `skills/` y metadata deben tener YAML frontmatter.

### 2. Seguir Jerarquía de Headers Consistente

```markdown
# H1 - Título principal (uno por documento)
## H2 - Secciones principales
### H3 - Subsecciones (usar con moderación)
```

### 3. Preferir Tablas para Comparaciones

```markdown
| Opción | Pros | Contras |
|--------|------|---------|
| A      | X    | Y       |
| B      | Z    | W       |
```

### 4. Usar Checklists para Estado

```markdown
- [x] Completado
- [ ] Pendiente
- [~] En progreso
```

### 5. Limitar Longitud de Línea

- Máximo 100 caracteres por línea
- Facilita diff en git
- Mejor lectura en pantallas pequeñas

## Validación de Calidad

### Checklist Pre-Guardado

- [ ] YAML frontmatter válido (si aplica)
- [ ] Título claro y descriptivo
- [ ] Fecha actualizada
- [ ] Tags relevantes agregados
- [ ] Enlaces verificados
- [ ] Formato MVI aplicado
- [ ] Sin información duplicada
- [ ] Ejemplos incluidos si aplica

### Métricas de Calidad

| Métrica | Bueno | Revisar |
|---------|-------|---------|
| Palabras por sección | <150 | >200 |
| Bullets por lista | 3-5 | >7 |
| Nivel de header | H1-H3 | H4+ |
| Enlaces rotos | 0 | >0 |

## Notas

- Esta skill complementa a `@skill-creator` para documentación
- El principio MVI aplica a TODO el contenido del framework
- Los templates son guías, no requisitos rígidos
- Priorizar claridad sobre formalidad
- Cuando en duda, menos es más
