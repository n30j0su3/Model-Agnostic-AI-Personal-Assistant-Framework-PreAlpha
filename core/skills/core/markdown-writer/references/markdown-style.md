# Guía de Estilo Markdown - FreakingJSON

Esta guía define los estándares de formato para todo Markdown en el framework.

## Estructura General

### Frontmatter YAML

Usar frontmatter para documentos estructurados (sesiones, skills, ADRs):

```yaml
---
name: nombre-documento          # Para skills y recursos identificables
date: YYYY-MM-DD               # Para sesiones y eventos
title: Título del Documento    # Alternativa a name
status: active|archived        # Estado del documento
tags: [tag1, tag2]             # Categorización
author: @usuario               # Autor o responsable
version: "1.0"                # Versión del documento
---
```

### Jerarquía de Headers

```markdown
# H1 - Título principal (uno por documento, opcional si hay frontmatter)
## H2 - Secciones principales
### H3 - Subsecciones (usar con moderación)
```

**Reglas:**
- Solo un H1 por documento
- No saltar niveles (H2 → H4 ❌)
- Preferir H2 sobre H3 cuando sea posible
- No usar H4+ excepto en documentación extensa de referencia

## Formato de Texto

### Énfasis

```markdown
**Negrita** - Para términos importantes, nombres de archivos
*Cursiva* - Para énfasis suave, términos extranjeros
`Código` - Para comandos, variables, nombres de funciones
~~Tachado~~ - Para contenido deprecado
```

### Listas

**Bullets no ordenados:**

```markdown
- Item 1
- Item 2
  - Sub-item 2.1
  - Sub-item 2.2
- Item 3
```

**Máximo 3-5 items por nivel.** Para lists más largas, agrupar o referenciar.

**Listas ordenadas:**

```markdown
1. Paso 1
2. Paso 2
3. Paso 3
```

**Checklists:**

```markdown
- [x] Completado
- [ ] Pendiente
- [~] En progreso (convenio del framework)
```

### Tablas

```markdown
| Columna 1 | Columna 2 | Columna 3 |
|-----------|-----------|-----------|
| Valor A   | Valor B   | Valor C   |
| Valor D   | Valor E   | Valor F   |
```

**Reglas:**
- Headers en cada columna
- Alinear pipes para legibilidad
- Máximo 5 columnas
- Para tablas grandes, referenciar a archivo externo

## Código

### Bloques Inline

```markdown
Usa `pip install` para instalar dependencias.
```

### Bloques de Código

Especificar lenguaje para syntax highlighting:

```markdown
```python
def funcion():
    return "Hola"
```

```bash
echo "Hola Mundo"
```

```yaml
clave: valor
```
```

### Líneas de Comando

Prefijar con `$` para comandos a ejecutar:

```markdown
```bash
$ python script.py
$ ls -la
```
```

Sin `$` para output o ejemplos de código:

```markdown
```python
def main():
    print("Hola")
```
```

## Enlaces

### Enlaces Internos

```markdown
[Otra sesión](./2026-02-10.md)
[SKILL de PDF](../skills/core/pdf/SKILL.md)
[Referencia](references/guide.md)
```

### Enlaces Externos

```markdown
[Documentación oficial](https://example.com)
```

### Anchors

Generados automáticamente desde headers:

```markdown
## Mi Sección

[Link a sección](#mi-seccion)
```

Reglas para anchors:
- Minúsculas
- Espacios → guiones
- Sin caracteres especiales

## Citas y Notas

### Blockquotes

```markdown
> Nota importante sobre el proceso.
> Puede tener múltiples líneas.
```

### Llamadas de Atención

Usar emojis estándar del framework:

```markdown
> 💡 **Tip**: Atajo de teclado útil.

> ⚠️ **Advertencia**: Esto modifica archivos.

> 🚫 **Importante**: No usar en producción.

> ✅ **Éxito**: Operación completada.
```

## Separadores

Usar `---` para separar secciones grandes:

```markdown
## Sección 1

Contenido...

---

## Sección 2

Contenido...
```

## Fechas y Horas

Formato estándar:

```markdown
**Fecha**: 2026-02-11
**Hora**: 14:30
**Timestamp**: 2026-02-11 14:30:00
**Rango**: 2026-02-11 a 2026-02-15
```

## Emojis

Usar con moderación y consistencia:

| Emoji | Uso |
|-------|-----|
| ✅ | Completado, éxito |
| ❌ | Error, rechazado |
| 📝 | Borrador, pendiente |
| 🚧 | En progreso |
| ⚠️ | Advertencia |
| 💡 | Idea, tip |
| 🔍 | Investigación |
| 🎯 | Objetivo, meta |
| 📅 | Fecha, calendario |
| 🔗 | Enlace, referencia |

## Nombres de Archivos y Rutas

Formato consistente:

```markdown
- Archivo: `SKILL.md`
- Directorio: `core/skills/core/`
- Ruta completa: `core/.context/sessions/2026-02-11.md`
```

## Convenciones por Tipo de Documento

### Sesiones (`sessions/YYYY-MM-DD.md`)

```markdown
---
date: YYYY-MM-DD
workspace: Nombre
status: active
tags: []
---

# Sesión YYYY-MM-DD

**Inicio**: HH:MM  
**Workspace**: Nombre  
**Objetivo**: Descripción

---

## Resumen

## Tareas Completadas

## Tareas Pendientes

## Decisiones

## Próximos Pasos

---

**Fin**: HH:MM
```

### Skills (`skills/core/{name}/SKILL.md`)

```markdown
---
name: skill-name
description: Descripción específica y cuándo usarla
license: MIT
metadata:
  author: Nombre
  version: "1.0"
---

# Skill Name

## Casos de Uso

## Cuándo Usar

## Instrucciones

## Ejemplos

## Recursos Disponibles

## Mejores Prácticas
```

### Ideas (`codebase/ideas.md`)

```markdown
## Idea: Título

**Fecha**: YYYY-MM-DD  
**Categoría**: Tipo  
**Estado**: 📝 Borrador

### Descripción

### Beneficios

### Implementación

### Siguientes Pasos
```

## Validación

Usar el script de linting:

```bash
python core/skills/core/markdown-writer/scripts/md-lint.py archivo.md
```

Verifica:
- ✅ Frontmatter válido
- ✅ Jerarquía de headers correcta
- ✅ Longitud de líneas (<100 chars)
- ✅ Principio MVI aplicado
- ✅ Enlaces funcionales

## Checklist Pre-Commit

- [ ] Headers siguen jerarquía correcta
- [ ] Listas tienen 3-5 items máximo
- [ ] Código tiene lenguaje especificado
- [ ] Enlaces son funcionales
- [ ] Sin líneas >100 caracteres
- [ ] MVI aplicado consistentemente
- [ ] Fechas en formato YYYY-MM-DD

## Ejemplos Completos

### Buen Ejemplo: Sesión

```markdown
---
date: 2026-02-11
workspace: API Development
tags: [auth, api]
---

# Sesión 2026-02-11

**Inicio**: 09:00  
**Workspace**: API Development  
**Objetivo**: Implementar JWT authentication

---

## Resumen

Implementación completa de autenticación JWT con refresh tokens.

## Tareas Completadas

- [x] Diseñar schema de tokens
- [x] Implementar endpoint `/auth/login`
- [x] Agregar middleware de verificación
- [x] Tests unitarios (coverage: 94%)

## Decisiones

**Decisión**: Tokens con expiración de 24h + refresh de 7 días  
**Razón**: Balance seguridad/UX según OWASP guidelines  
**Impacto**: Requiere tabla adicional para refresh tokens

## Bloqueos

- Necesito acceso a servicio de email (ticket #234)

## Próximos Pasos

1. Configurar envío de emails
2. Implementar `/auth/reset-password`
3. Documentar API en Swagger

---

**Fin**: 18:30  
**Estado**: ✅ Completado
```

## Recursos Adicionales

- [Guía MVI](./mvi-guide.md) - Principio Minimal Viable Information
- [Original Markdown Guide](https://www.markdownguide.org)
- [GitHub Flavored Markdown](https://github.github.com/gfm/)
