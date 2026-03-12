---
name: skill-creator
description: Guia completa para crear y evaluar skills en el framework FreakingJSON. Use cuando el usuario quiera crear, evaluar, comparar o empaquetar una skill. Incluye sistema de evaluacion con @skill-evaluator para medir calidad MVI, claridad, completitud y accionabilidad.
license: MIT
metadata:
  author: Anthropic/FreakingJSON
  version: "2.0.0"
  source: https://github.com/anthropics/skills
  compatibility: Requiere Python 3.8+ para scripts de utilidad.
---

# Skill Creator v2

Guia completa para crear y evaluar skills efectivas en el framework FreakingJSON.

## Sobre las Skills

Las skills son paquetes modulares y auto-contenidos que extienden las capacidades del asistente proporcionando conocimiento especializado, workflows y herramientas. Piensa en ellas como "guias de onboarding" para dominios o tareas especificas.

### Que Proporcionan las Skills

1. **Workflows especializados** - Procedimientos multi-paso para dominios especificos
2. **Integraciones de herramientas** - Instrucciones para trabajar con formatos de archivo o APIs especificos
3. **Experiencia de dominio** - Conocimiento especifico de la empresa, esquemas, logica de negocio
4. **Recursos empaquetados** - Scripts, referencias y assets para tareas complejas y repetitivas

## Sistema de Evaluacion (NUEVO v2)

Skill-Creator v2 incluye un sistema completo de evaluacion de calidad mediante el subagente `@skill-evaluator`.

### Flujo de Evaluacion

```
Skill en desarrollo
        │
        ▼
┌─────────────────────────────┐
│ 1. Definir test cases       │
│    (evals/evals.json)       │
└─────────────┬───────────────┘
              │
              ▼
┌─────────────────────────────┐
│ 2. Ejecutar @skill-evaluator│
│    - Modo full/simplified   │
└─────────────┬───────────────┘
              │
              ▼
┌─────────────────────────────┐
│ 3. Revisar en eval-viewer   │
│    (viewer.html)            │
└─────────────┬───────────────┘
              │
              ▼
┌─────────────────────────────┐
│ 4. Iterar y mejorar         │
└─────────────────────────────┘
```

### Criterios de Calidad

#### Modo Full (default)

| Criterio | Peso | Descripcion |
|----------|------|-------------|
| **mvi_compliance** | 25% | Principio MVI: informacion esencial sin redundancia |
| **clarity** | 25% | Instrucciones claras, sin ambiguedad, legible en <30s |
| **completeness** | 20% | Secciones requeridas presentes (frontmatter, descripcion, uso) |
| **actionability** | 20% | Ejecutable sin contexto adicional, pasos bien definidos |
| **cross_platform** | 10% | Scripts compatibles Windows/Linux/macOS (si aplica) |

#### Modo Simplified

| Criterio | Peso | Descripcion |
|----------|------|-------------|
| **mvi_compliance** | 35% | Principio MVI |
| **clarity** | 35% | Claridad de instrucciones |
| **completeness** | 30% | Secciones basicas presentes |

### Escala de Calificacion

| Grado | Rango | Interpretacion |
|-------|-------|----------------|
| **A** | 90-100 | Excelente - Lista para produccion |
| **B** | 80-89 | Buena - Listo con mejoras menores |
| **C** | 70-79 | Aceptable - Necesita revision |
| **D** | 50-69 | Necesita mejoras - Revision significativa requerida |
| **F** | 0-49 | Inaceptable - Reescribir completamente |

### Comandos de Evaluacion

| Comando | Descripcion |
|---------|-------------|
| `@skill-evaluator evaluate_skill("<path>")` | Evalua skill individual |
| `@skill-evaluator batch_evaluate("<dir>")` | Evalua todas las skills en directorio |
| `@skill-evaluator compare_skills("<a>", "<b>")` | Compara dos skills |
| `python scripts/aggregate_benchmark.py` | Genera reporte de benchmark |

### Visualizar Resultados

```bash
# Abrir visualizador HTML interactivo
start core/skills/core/skill-creator/eval-viewer/viewer.html
```

El visualizador muestra:
- Puntaje general y por criterio
- Feedback detallado
- Sugerencias de mejora
- Comparacion con baseline

## Anatomia de una Skill

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
    ├── scripts/          - Codigo ejecutable (Python/Bash/etc.)
    ├── references/       - Documentacion para cargar en contexto segun necesidad
    └── assets/           - Archivos usados en output (templates, iconos, fuentes)
```

### SKILL.md (requerido)

**Calidad del Metadata:** Los campos `name` y `description` en el frontmatter YAML determinan cuando el asistente usara la skill. Se especifico sobre que hace la skill y cuando usarla.

### Recursos Empaquetados (opcionales)

#### Scripts (`scripts/`)

Codigo ejecutable para tareas que requieren confiabilidad deterministica.

- **Cuando incluir**: Cuando el mismo codigo se reescribe repetidamente
- **Ejemplo**: `scripts/rotate_pdf.py` para tareas de rotacion de PDF
- **Beneficios**: Eficiente en tokens, deterministico

#### References (`references/`)

Documentacion destinada a ser cargada segun necesidad.

- **Cuando incluir**: Para documentacion que el asistente deberia referenciar
- **Ejemplos**: `references/schema.md` para esquemas financieros
- **Mejor practica**: Si archivos son grandes (>10k palabras), incluye patrones de busqueda grep

#### Assets (`assets/`)

Archivos usados dentro del output que produce el asistente.

- **Ejemplos**: `assets/logo.png`, `assets/slides.pptx`
- **Casos de uso**: Templates, imagenes, iconos, codigo boilerplate

### Principio de Progressive Disclosure

Las skills usan un sistema de tres niveles:

1. **Metadata (name + description)** - Siempre en contexto (~100 palabras)
2. **SKILL.md body** - Cuando la skill se activa (<5k palabras)
3. **Bundled resources** - Segun necesidad del asistente (Ilimitado*)

## Proceso de Creacion de Skills

Para crear una skill, sigue el proceso en orden.

### Paso 1: Entender la Skill con Ejemplos Concretos

Para crear una skill efectiva, entiende claramente ejemplos concretos de como se usara.

**Preguntas utiles**:
- "Que funcionalidad deberia soportar la skill?"
- "Puedes dar algunos ejemplos de como se usaria?"
- "Que diria un usuario que deberia activar esta skill?"

**Concluir cuando**: Hay un sentido claro de la funcionalidad.

### Paso 2: Planificar los Contenidos Reutilizables

Analiza cada ejemplo para identificar que scripts, referencias y assets serian utiles.

### Paso 3: Inicializar la Skill

SIEMPRE ejecuta el script `init_skill.py`:

```bash
python core/skills/core/skill-creator/scripts/init_skill.py <nombre-skill> --path <directorio-salida>
```

El script:
- Crea el directorio de skill
- Genera template SKILL.md con frontmatter y placeholders TODO
- Crea directorios de recursos: `scripts/`, `references/`, `assets/`

### Paso 4: Editar la Skill

Al editar, enfocate en incluir informacion beneficiosa y no obvia.

**Estilo de Escritura**: Usa forma imperativa/infinitiva (instrucciones verbo-primero), no segunda persona.

Para completar SKILL.md, responde:
1. Cual es el proposito de la skill?
2. Cuando deberia usarse?
3. En la practica, como deberia usar el asistente la skill?

### Paso 5: Evaluar la Skill (NUEVO v2)

Antes de empaquetar, evalua la calidad:

```
@skill-evaluator evaluate_skill("core/skills/core/nueva-skill")
```

Revisar el output en `eval-viewer/viewer.html` e iterar hasta obtener grado A o B.

### Paso 6: Empaquetar la Skill

Una vez lista, empaquetar en ZIP distribuible:

```bash
python core/skills/core/skill-creator/scripts/package_skill.py <ruta/a/skill-folder>
```

El script valida automaticamente:
- Formato YAML frontmatter y campos requeridos
- Convenciones de nombres y estructura
- Completitud y calidad de la descripcion

### Paso 7: Validar Cross-Platform

Validar scripts Python sean cross-platform:

```bash
python core/skills/core/python-standards/scripts/check_script.py \
    core/skills/core/nueva-skill/scripts/*.py
```

**Criterios de aceptacion**:
- [ ] 0 errores de encoding
- [ ] 0 emojis en scripts de libreria
- [ ] Scripts CLI usan detect_env.py
- [ ] Todos los open() tienen encoding='utf-8'

## Referencia Rapida

### Estructura de SKILL.md

```yaml
---
name: nombre-skill
description: Descripcion especifica de que hace y cuando usarla.
license: MIT
metadata:
  author: Tu Nombre
  version: "1.0"
compatibility: Requisitos especificos si los hay.
---

# Nombre de la Skill

Descripcion breve del proposito.

## Casos de Uso
1. Caso 1
2. Caso 2

## Uso
Instrucciones detalladas.

## Ejemplos
Codigo de ejemplo si aplica.
```

### Comandos de Utilidad

| Comando | Descripcion |
|---------|-------------|
| `init_skill.py <nombre> --path <dir>` | Inicializa nueva skill |
| `package_skill.py <skill-folder>` | Valida y empaqueta skill en ZIP |
| `@skill-evaluator evaluate_skill("<path>")` | Evalua calidad de skill |
| `aggregate_benchmark.py --evals-dir <dir>` | Genera reporte benchmark |

### Directrices de Nomenclatura

- Usar minusculas con guiones (ej: `pdf-editor`)
- Nombres descriptivos pero concisos
- Evitar prefijos redundantes como "skill-"

## Mejores Practicas

1. **MVI (Minimal Viable Information)**: Documenta solo lo esencial, referencia el resto
2. **Progressive Disclosure**: Estructura informacion en niveles (metadata → SKILL.md → referencias)
3. **No dupliques**: Informacion en SKILL.md O en referencias, no ambos
4. **Scripts deterministicos**: Para operaciones que requieren confiabilidad exacta
5. **Evalua antes de empaquetar**: Usa @skill-evaluator para verificar calidad
6. **Valida cross-platform**: Asegura compatibilidad con Windows/Linux/macOS

## Referencias

| Archivo | Descripcion |
|---------|-------------|
| `agents/skill-evaluator.md` | Subagente de evaluacion |
| `eval-viewer/README.md` | Visualizador HTML interactivo |
| `references/evals-schema.md` | Schema JSON para evaluaciones |
| `scripts/aggregate_benchmark.py` | Generador de reportes benchmark |