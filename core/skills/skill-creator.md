# Skill Creator Automático

> **Versión**: v0.5.0-alpha  
> **Propósito**: Generar skills automáticamente desde ejemplos o descripciones en lenguaje natural  
> **Principios**: YAGNI, Impeccable, DRY, Local-First

---

## 🚀 Quick Start

```bash
python core/scripts/skill_creator.py --from-example "path/to/ejemplo.py" --name "mi-skill"
python core/scripts/skill_creator.py --from-prompt "Quiero una skill que revise ortografía"
```

---

## 📋 Funcionalidades

### 1. **Crear Skill desde Ejemplo**
- Analiza código Python/Markdown existente
- Extrae patrón reusable
- Genera skill con metadata completa

### 2. **Crear Skill desde Prompt**
- Usa IA local (opencode) para interpretar descripción
- Genera estructura de skill
- Incluye ejemplos de uso

### 3. **Auto-Mejorar Skill**
- Analiza skill existente
- Sugiere mejoras (performance, claridad, edge cases)
- Aplica mejoras automáticamente (opcional)

### 4. **Validar Skill**
- Verifica sintaxis Python
- Valida metadata TOML
- Testea con casos básicos

---

## 🏗️ Arquitectura

```
skill_creator.py
├── from_example() → analiza ejemplo → genera skill
├── from_prompt() → llama a opencode → genera skill
├── improve() → analiza → sugiere → aplica
└── validate() → verifica → reporta
```

---

## 📝 Estructura de Skill Generada

```toml
# core/skills/mi-skill.toml
name = "mi-skill"
version = "1.0.0"
description = "Descripción automática desde ejemplo/prompt"
category = "productivity"
tags = ["auto-generated", "user-created"]

[entrypoint]
script = "core/scripts/skills/mi_skill.py"
function = "execute"

[parameters]
input = { type = "string", required = true, description = "Input del usuario" }
output = { type = "string", required = false, description = "Resultado procesado" }

[examples]
ex1 = { input = "ejemplo1", output = "resultado1" }
ex2 = { input = "ejemplo2", output = "resultado2" }
```

---

## 🔧 Uso Detallado

### Desde Ejemplo

```bash
# Ejemplo: crear skill que resume texto
python core/scripts/skill_creator.py \\
  --from-example "examples/summarize.py" \\
  --name "text-summarizer" \\
  --category "productivity"

# Output:
# ✓ Skill creada: core/skills/text-summarizer.toml
# ✓ Script generado: core/scripts/skills/text_summarizer.py
# ✓ Validación: PASSED (sintaxis + metadata)
```

### Desde Prompt

```bash
# Ejemplo: skill que traduce texto
python core/scripts/skill_creator.py \\
  --from-prompt "Quiero una skill que traduzca texto al inglés manteniendo el tono" \\
  --name "english-translator"

# Proceso:
# 1. Analiza prompt con opencode
# 2. Genera estructura TOML
# 3. Crea script Python
# 4. Valida y reporta
```

### Auto-Mejora

```bash
# Mejorar skill existente
python core/scripts/skill_creator.py \\
  --improve "core/skills/pdf-extractor.toml" \\
  --auto-apply

# Output:
# Análisis:
#   ✓ Sintaxis: OK
#   ⚠ Edge cases: faltan 3 casos
#   ⚠ Performance: se puede optimizar línea 45
#   ✓ Documentación: completa
#
# Mejoras aplicadas:
#   + Manejo de PDFs corruptos
#   + Optimización de memoria (buffer streaming)
#   + Tests para edge cases
```

---

## 🧪 Validación

```bash
# Validar todas las skills
python core/scripts/skill_creator.py --validate-all

# Validar skill específica
python core/scripts/skill_creator.py --validate "core/skills/mi-skill.toml"
```

**Checks realizados**:
- ✓ Sintaxis TOML válida
- ✓ Script Python compila
- ✓ Función `execute()` existe
- ✓ Parameters match signature
- ✓ Examples son consistentes

---

## 🎯 Principios Aplicados

### YAGNI (You Ain't Gonna Need It)
- Solo genera lo necesario para el caso descrito
- Sin features anticipadas
- Metadata mínima viable

### Impeccable
- Código generado sigue estándares del framework
- Documentación clara en español
- Ejemplos realistas y testeables

### DRY (Don't Repeat Yourself)
- Reutiliza patrones de skills existentes
- Plantillas parametrizadas
- Sin duplicación de lógica

### Local-First
- Todo se genera en archivos locales
- Sin dependencias cloud
- Preservación automática en repo

---

## 📚 Ejemplos Reales

### Skill 1: Revisor de Ortografía

```bash
python core/scripts/skill_creator.py \\
  --from-prompt "Skill que revise ortografía en español y sugiera correcciones" \\
  --name "spanish-proofreader"
```

**Genera**:
- `core/skills/spanish-proofreader.toml`
- `core/scripts/skills/spanish_proofreader.py`
- 5 ejemplos de uso
- Tests básicos

### Skill 2: Extractor de Datos de PDF

```bash
python core/scripts/skill_creator.py \\
  --from-example "scripts/extract_invoice_data.py" \\
  --name "invoice-extractor" \\
  --category "data-extraction"
```

**Genera**:
- Skill con parámetros `pdf_path`, `fields_to_extract`
- Manejo de errores (PDF corrupto, campos faltantes)
- Ejemplos con facturas reales

### Skill 3: Generador de Reportes

```bash
python core/scripts/skill_creator.py \\
  --from-prompt "Skill que genere reporte semanal de productividad en HTML" \\
  --name "weekly-report-generator"
```

**Genera**:
- Plantilla HTML profesional
- Integración con sessions del framework
- Opción de exportar a PDF

---

## 🔌 Integración con Framework

### Auto-Registro

Las skills creadas se registran automáticamente en:
- `core/skills/catalog.json` (si existe)
- `core/.context/knowledge/skills-index.json`

### Disponibilidad Inmediata

```python
# Después de crear skill, está disponible para:
# - pa.py menú → Skills
# - Dashboard → Skills tab
# - Agentes vía @mi-skill
```

---

## 🛠️ Troubleshooting

### Error: "Python no encontrado"
```bash
# Verificar instalación
python --version

# Si usas Windows:
where python

# Si usas macOS/Linux:
which python3
```

### Error: "opencode no disponible"
```bash
# Instalar opencode
npm install -g opencode-ai

# Verificar
opencode --version
```

### Error: "Metadata inválida"
```bash
# Validar TOML manualmente
python -c "import tomllib; tomllib.load(open('core/skills/mi-skill.toml', 'rb'))"

# Si falla, revisar sintaxis TOML (comillas, comas, etc.)
```

---

## 📈 Métricas

**Skills generadas exitosamente**: tracking en `core/.context/knowledge/learning/skill-creator-stats.json`

**Tasa de validación**: % de skills que pasan validación al primer intento

**Mejoras aplicadas**: número de auto-mejoras por skill

---

*Skill Creator v0.5.0-alpha — "De la idea a la skill en segundos"*
