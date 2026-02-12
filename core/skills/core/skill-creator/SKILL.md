---
name: skill-creator
description: Guía completa para crear nuevas skills en el framework FreakingJSON. Use cuando el usuario quiera crear, actualizar o empaquetar una skill que extienda las capacidades del asistente con conocimiento especializado, workflows o integraciones de herramientas.
license: MIT
metadata:
  author: Anthropic/FreakingJSON
  version: "1.0"
  source: https://github.com/anthropics/skills
compatibility: Requiere Python 3.8+ para scripts de utilidad.
---

# Skill Creator

Guía completa para crear skills efectivas en el framework FreakingJSON.

## Sobre las Skills

Las skills son paquetes modulares y auto-contenidos que extienden las capacidades del asistente proporcionando conocimiento especializado, workflows y herramientas. Piensa en ellas como "guías de onboarding" para dominios o tareas específicas — transforman al asistente de un agente de propósito general en un agente especializado equipado con conocimiento procedural que ningún modelo puede poseer completamente.

### Qué Proporcionan las Skills

1. **Workflows especializados** - Procedimientos multi-paso para dominios específicos
2. **Integraciones de herramientas** - Instrucciones para trabajar con formatos de archivo o APIs específicos
3. **Experiencia de dominio** - Conocimiento específico de la empresa, esquemas, lógica de negocio
4. **Recursos empaquetados** - Scripts, referencias y assets para tareas complejas y repetitivas

## Anatomía de una Skill

Cada skill consiste en un archivo SKILL.md requerido y recursos empaquetados opcionales:

```
skill-name/
├── SKILL.md (requerido)
│   ├── YAML frontmatter metadata (requerido)
│   │   ├── name: (requerido)
│   │   ├── description: (requerido)
│   │   ├── license: (opcional)
│   │   ├── metadata: (opcional)
│   │   └── compatibility: (opcional)
│   └── Markdown instructions (requerido)
└── Recursos Empaquetados (opcional)
    ├── scripts/          - Código ejecutable (Python/Bash/etc.)
    ├── references/       - Documentación para cargar en contexto según necesidad
    └── assets/           - Archivos usados en output (templates, íconos, fuentes)
```

### SKILL.md (requerido)

**Calidad del Metadata:** Los campos `name` y `description` en el frontmatter YAML determinan cuándo el asistente usará la skill. Sé específico sobre qué hace la skill y cuándo usarla. Usa tercera persona (ej: "Esta skill debe usarse cuando..." en lugar de "Usa esta skill cuando...").

### Recursos Empaquetados (opcionales)

#### Scripts (`scripts/`)

Código ejecutable (Python/Bash/etc.) para tareas que requieren confiabilidad determinística o se reescriben repetidamente.

- **Cuándo incluir**: Cuando el mismo código se reescribe repetidamente o se necesita confiabilidad determinística
- **Ejemplo**: `scripts/rotate_pdf.py` para tareas de rotación de PDF
- **Beneficios**: Eficiente en tokens, determinístico, puede ejecutarse sin cargar en contexto
- **Nota**: Los scripts pueden necesitar ser leídos por el asistente para parches o ajustes específicos del entorno

#### References (`references/`)

Documentación y material de referencia destinado a ser cargado según necesidad en el contexto para informar el proceso y pensamiento del asistente.

- **Cuándo incluir**: Para documentación que el asistente debería referenciar mientras trabaja
- **Ejemplos**: `references/schema.md` para esquemas financieros, `references/policies.md` para políticas de empresa
- **Casos de uso**: Esquemas de base de datos, documentación de APIs, conocimiento de dominio, políticas de empresa
- **Beneficios**: Mantiene SKILL.md lean, cargado solo cuando el asistente determina que se necesita
- **Mejor práctica**: Si archivos son grandes (>10k palabras), incluye patrones de búsqueda grep en SKILL.md
- **Evitar duplicación**: La información debe vivir en SKILL.md O en archivos de referencia, no ambos

#### Assets (`assets/`)

Archivos no destinados a ser cargados en contexto, sino usados dentro del output que produce el asistente.

- **Cuándo incluir**: Cuando la skill necesita archivos que se usarán en el output final
- **Ejemplos**: `assets/logo.png` para assets de marca, `assets/slides.pptx` para templates de PowerPoint
- **Casos de uso**: Templates, imágenes, íconos, código boilerplate, fuentes, documentos de muestra

### Principio de Progressive Disclosure

Las skills usan un sistema de tres niveles para manejar el contexto eficientemente:

1. **Metadata (name + description)** - Siempre en contexto (~100 palabras)
2. **SKILL.md body** - Cuando la skill se activa (<5k palabras)
3. **Bundled resources** - Según necesidad del asistente (Ilimitado*)

*Ilimitado porque los scripts pueden ejecutarse sin leerse en la ventana de contexto.

## Proceso de Creación de Skills

Para crear una skill, sigue el "Proceso de Creación de Skills" en orden, saltando pasos solo si hay una razón clara por la cual no son aplicables.

### Paso 1: Entender la Skill con Ejemplos Concretos

**Omitir este paso solo cuando**: Los patrones de uso de la skill ya sean claramente entendidos.

Para crear una skill efectiva, entiende claramente ejemplos concretos de cómo se usará la skill. Esta comprensión puede venir de ejemplos directos del usuario o ejemplos generados que se validan con feedback del usuario.

Por ejemplo, al construir una skill de image-editor, preguntas relevantes incluyen:
- "¿Qué funcionalidad debería soportar la skill de image-editor? ¿Edición, rotación, algo más?"
- "¿Puedes dar algunos ejemplos de cómo se usaría esta skill?"
- "¿Qué diría un usuario que debería activar esta skill?"

Para evitar abrumar al usuario, evita hacer demasiadas preguntas en un solo mensaje. Comienza con las preguntas más importantes y haz seguimiento según sea necesario.

**Concluir este paso cuando**: Hay un sentido claro de la funcionalidad que la skill debería soportar.

### Paso 2: Planificar los Contenidos Reutilizables de la Skill

Para convertir ejemplos concretos en una skill efectiva, analiza cada ejemplo:

1. Considera cómo ejecutar el ejemplo desde cero
2. Identifica qué scripts, referencias y assets serían útiles al ejecutar estos workflows repetidamente

**Ejemplo - pdf-editor**: Para queries como "Ayúdame a rotar este PDF":
- Rotar un PDF requiere re-escribir el mismo código cada vez
- Un script `scripts/rotate_pdf.py` sería útil

**Ejemplo - frontend-webapp-builder**: Para queries como "Constrúyeme una app de todo":
- Escribir una webapp requiere el mismo boilerplate HTML/React cada vez
- Un template `assets/hello-world/` con boilerplate sería útil

**Ejemplo - big-query**: Para queries como "¿Cuántos usuarios han iniciado sesión hoy?":
- Consultar BigQuery requiere re-descubrir esquemas de tablas cada vez
- Un archivo `references/schema.md` documentando esquemas sería útil

### Paso 3: Inicializar la Skill

**Omitir este paso solo si**: La skill que se desarrolla ya existe y se necesita iteración o empaquetado.

Al crear una nueva skill desde cero, SIEMPRE ejecuta el script `init_skill.py`:

```bash
python core/skills/core/skill-creator/scripts/init_skill.py <nombre-skill> --path <directorio-salida>
```

El script:
- Crea el directorio de skill en la ruta especificada
- Genera un template SKILL.md con frontmatter y placeholders TODO
- Crea directorios de recursos de ejemplo: `scripts/`, `references/`, `assets/`
- Agrega archivos de ejemplo en cada directorio

Después de la inicialización, personaliza o elimina los archivos generados según necesidad.

### Paso 4: Editar la Skill

Al editar la skill (recién generada o existente), recuerda que la skill se está creando para otra instancia del asistente. Enfócate en incluir información que sería beneficiosa y no obvia para el asistente.

#### Comenzar con Contenidos Reutilizables

Para comenzar la implementación, empieza con los recursos identificados: archivos `scripts/`, `references/` y `assets/`. Nota que este paso puede requerir input del usuario.

También, elimina archivos y directorios de ejemplo que no se necesiten para la skill.

#### Actualizar SKILL.md

**Estilo de Escritura:** Escribe toda la skill usando **forma imperativa/infinitiva** (instrucciones verbo-primero), no segunda persona. Usa lenguaje objetivo e instructivo (ej: "Para lograr X, haz Y" en lugar de "Deberías hacer X").

Para completar SKILL.md, responde las siguientes preguntas:

1. ¿Cuál es el propósito de la skill, en pocas oraciones?
2. ¿Cuándo debería usarse la skill?
3. ¿En la práctica, cómo debería usar el asistente la skill?

### Paso 5: Empaquetar la Skill

Una vez que la skill está lista, debe empaquetarse en un archivo ZIP distribuible:

```bash
python core/skills/core/skill-creator/scripts/package_skill.py <ruta/a/skill-folder>
```

Especificación opcional del directorio de salida:

```bash
python core/skills/core/skill-creator/scripts/package_skill.py <ruta/a/skill-folder> ./dist
```

El script de empaquetado:

1. **Valida** la skill automáticamente, verificando:
   - Formato YAML frontmatter y campos requeridos
   - Convenciones de nombres y estructura de directorios
   - Completitud y calidad de la descripción
   - Organización de archivos y referencias de recursos

2. **Empaqueta** los contenidos de la skill en un archivo ZIP listo para distribuir

### Paso 6: Validar Cross-Platform (NUEVO)

Antes de considerar la skill completa, validar que todos los scripts Python sean cross-platform:

```bash
# Validar scripts con @python-standards
python core/skills/core/python-standards/scripts/check_script.py \
    core/skills/core/nueva-skill/scripts/*.py

# Si hay issues, corregir automáticamente
python core/skills/core/python-standards/scripts/fix_script.py \
    core/skills/core/nueva-skill/scripts/*.py --in-place

# Re-validar
python core/skills/core/python-standards/scripts/check_script.py \
    core/skills/core/nueva-skill/scripts/*.py
```

**Criterios de aceptación**:
- [ ] 0 errores de encoding
- [ ] 0 emojis en scripts de librería
- [ ] Scripts CLI usan detect_env.py
- [ ] Todos los open() tienen encoding='utf-8'
- [ ] Tests pasan en Windows y Linux/macOS

**Documentar en SKILL.md**:
```markdown
## Compatibilidad Cross-Platform

Esta skill sigue los estándares @python-standards:
- Scripts validados con check_script.py
- Compatible con Windows, Linux y macOS
- Sin dependencias de encoding específicas
```

## Referencia Rápida

### Estructura de SKILL.md

```yaml
---
name: nombre-skill
description: Descripción específica de qué hace y cuándo usarla. Use tercera persona.
license: MIT
metadata:
  author: Tu Nombre
  version: "1.0"
compatibility: Requisitos específicos si los hay.
---

# Nombre de la Skill

Descripción breve del propósito.

## Casos de Uso
1. Caso 1
2. Caso 2

## Uso
Instrucciones detalladas para el asistente.

## Ejemplos
```python
# Código de ejemplo si aplica
```
```

### Comandos de Utilidad

| Comando | Descripción |
|---------|-------------|
| `init_skill.py <nombre> --path <dir>` | Inicializa nueva skill con estructura base |
| `package_skill.py <skill-folder>` | Valida y empaqueta skill en ZIP |

### Directrices de Nomenclatura

- Usar minúsculas con guiones para nombres de skill (ej: `pdf-editor`)
- Nombres descriptivos pero concisos
- Evitar prefijos redundantes como "skill-" a menos que sea necesario para claridad

## Mejores Prácticas

1. **MVI (Minimal Viable Information)**: Documenta solo lo esencial, referencia el resto
2. **Progressive Disclosure**: Estructura información en niveles (metadata → SKILL.md → referencias)
3. **No dupliques**: Información en SKILL.md O en referencias, no ambos
4. **Scripts determinísticos**: Para operaciones que requieren confiabilidad exacta
5. **Referencias para contexto**: Para información que el asistente necesita consultar
6. **Assets para output**: Para archivos que se usan en el resultado final
7. **Valida antes de empaquetar**: Siempre usa package_skill.py para verificar integridad
