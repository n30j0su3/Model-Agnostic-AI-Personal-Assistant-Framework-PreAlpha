# Plantilla SKILL.md

Template base para crear el archivo SKILL.md de una nueva skill.

```markdown
---
name: nombre-de-tu-skill
description: Descripción específica de qué hace esta skill y cuándo usarla. Usa tercera persona (ej: "Esta skill debe usarse cuando..."). Sé específico sobre el propósito y casos de uso.
license: MIT
metadata:
  author: Tu Nombre
  version: "1.0"
  created: 2026-01-01
  updated: 2026-01-01
compatibility: Requisitos específicos si los hay (ej: Python 3.8+, Node.js 16+, librerías específicas)
---

# Nombre de Tu Skill

Descripción concisa del propósito de esta skill en 2-3 oraciones.

## Casos de Uso

1. **Caso Principal**: Describe el caso de uso más común
2. **Caso Secundario**: Describe otro caso de uso importante
3. **Caso Especial**: Describe un caso de uso específico o avanzado

## Cuándo Usar Esta Skill

Esta skill debe usarse cuando el usuario necesite:
- Condición específica 1
- Condición específica 2
- Condición específica 3

## Instrucciones de Uso

### Paso 1: Entender el Requerimiento
Descubre qué necesita el usuario exactamente. Haz preguntas si falta contexto:
- "¿Cuál es el objetivo final?"
- "¿Hay algún formato específico requerido?"
- "¿Hay restricciones o preferencias?"

### Paso 2: Ejecutar el Workflow
Sigue el procedimiento adecuado según el caso de uso:

#### Para Caso 1:
1. Acción específica
2. Siguiente acción
3. Validación

#### Para Caso 2:
1. Acción específica
2. Siguiente acción
3. Validación

### Paso 3: Validar y Entregar
Verifica que el resultado cumpla con:
- [ ] Criterio de calidad 1
- [ ] Criterio de calidad 2
- [ ] Criterio de calidad 3

## Ejemplos

### Ejemplo 1: Descripción del Ejemplo
```python
# Código de ejemplo si aplica
# Incluye comentarios explicativos
```

### Ejemplo 2: Descripción del Ejemplo
```bash
# Comandos de ejemplo si aplica
# Explica qué hace cada comando
```

## Recursos Disponibles

### Scripts (`scripts/`)
- `scripts/utilidad.py` - Descripción de qué hace este script y cuándo usarlo

### References (`references/`)
- `references/guia.md` - Documentación de referencia para consultar durante el trabajo

### Assets (`assets/`)
- `assets/template.xyz` - Template o archivo base para usar en outputs

## Mejores Prácticas

1. **Práctica 1**: Explicación de por qué es importante
2. **Práctica 2**: Explicación de por qué es importante
3. **Práctica 3**: Explicación de por qué es importante

## Notas Importantes

- Nota 1 sobre limitaciones o consideraciones especiales
- Nota 2 sobre comportamientos esperados
- Nota 3 sobre dependencias o requisitos

## Referencias Externas

- [Documentación relevante](https://example.com)
- [Recurso adicional](https://example.com/resource)
```

## Checklist de SKILL.md

Antes de considerar la skill completa, verifica:

### Frontmatter
- [ ] `name` está en kebab-case (minúsculas y guiones)
- [ ] `description` tiene al menos 20 caracteres y es específica
- [ ] `description` usa tercera persona ("Esta skill...")
- [ ] `license` está incluida (MIT recomendado)
- [ ] `metadata` tiene autor y versión

### Contenido
- [ ] Título claro que describe la skill
- [ ] Sección "Casos de Uso" con al menos 2-3 casos
- [ ] Sección "Cuándo Usar" específica
- [ ] Instrucciones paso a paso claras
- [ ] Ejemplos prácticos con código/comandos
- [ ] Recursos disponibles documentados
- [ ] Mejores prácticas incluidas
- [ ] Notas importantes sobre limitaciones

### Estilo
- [ ] Usa forma imperativa/infinitiva ("Haz X", no "Deberías hacer X")
- [ ] Lenguaje objetivo e instructivo
- [ ] 3-5 bullets por sección (principio MVI)
- [ ] Ejemplos mínimos cuando apliquen
- [ ] Referencias a docs completos, no duplicar contenido

## Ejemplos de Buenas Descripciones

✅ **Buena**: "Procesa y analiza archivos PDF para extraer texto, tablas y metadatos. Esta skill debe usarse cuando el usuario necesite manipular documentos PDF, ya sea para extracción de contenido,合并 de archivos, o generación de nuevos PDFs."

❌ **Mala**: "Trabaja con PDFs"

✅ **Buena**: "Genera visualizaciones de datos usando Seaborn y Matplotlib con estilos predefinidos. Esta skill debe usarse cuando el usuario necesite crear gráficos, charts o visualizaciones de datos de manera rápida y consistente."

❌ **Mala**: "Hace gráficos"
