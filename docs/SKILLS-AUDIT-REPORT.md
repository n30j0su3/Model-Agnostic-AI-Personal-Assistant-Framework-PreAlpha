# Skills Audit Report — PA Framework

> **Versión framework**: v0.4.1-beta
> **Fecha de auditoría**: 2026-10-18
> **Alcance**: 23 skills Markdown (`core/skills/core/*/SKILL.md`) + índices + indexador
> **Método**: lectura de los 23 `SKILL.md` · verificación en disco de cada recurso citado · parseo de frontmatter con PyYAML · cotejo `SKILLS.md` ↔ `catalog.json` ↔ `skills-index.json` ↔ `skills_indexer.py`
> **Estado**: ✅ RESUELTO — fixes aplicados el 2026-10-18 (ver §7)

---

## 1. Resumen Ejecutivo

El inventario está **completo** (23 skills en disco, 23 en `SKILLS.md`, 23 en `catalog.json`, 23 en `skills-index.json`), pero la **calidad de los metadatos y referencias es inconsistente**.

| Severidad | Hallazgos | Impacto |
|-----------|-----------|---------|
| 🔴 Bloqueante | 2 (etl, dashboard-pro) | Parseo de frontmatter falla |
| 🟠 Funcional | 2 categorías | Índice corrupto + referencias rotas |
| 🟡 Consistencia | 3 categorías | Schema y convenciones divergentes |
| 🔵 Legado / higiene | 3 categorías | Sistema TOML fantasma, manifests duplicados, drift de índices |

**Causa raíz principal**: convivencia de **dos esquemas de frontmatter** (slug vs Display Name) + un **sistema de skills TOML heredado** que ya no está en disco pero sigue referenciado.

---

## 2. Inventario de Skills

| # | Skill | `name` frontmatter | Frontmatter | Hallazgos |
|---|-------|--------------------|-------------|-----------|
| 1 | content-optimizer | `Content Optimizer` ⚠️ | `id`+`name` (legacy) | NAME_MISMATCH · refs workspace |
| 2 | context-evaluator | `Context Evaluator` ⚠️ | `id`+`name` (legacy) | NAME_MISMATCH · rubricas rotas |
| 3 | csv-processor | `csv-processor` ✅ | estándar | import Python inválido |
| 4 | dashboard-pro | — ❌ | ❌ mal ubicado | frontmatter no parseable |
| 5 | data-viz | `data-viz` ✅ | mínimo | script en raíz · categoría drift |
| 6 | decision-engine | `Decision Engine` ⚠️ | `id`+`name` (legacy) | NAME_MISMATCH |
| 7 | docx | `docx` ✅ | estándar | autor `Agentman` |
| 8 | error-recovery | `error-recovery` ✅ | `displayName` | schema único · dirs runtime |
| 9 | etl | — ❌ | ❌ ausente | sin frontmatter · script en raíz |
| 10 | json-prompt-generator | `json-prompt-generator` ✅ | estándar | autor `opencode` |
| 11 | markdown-writer | `markdown-writer` ✅ | estándar | 2 refs rotas |
| 12 | mcp-builder | `MCP Builder` ⚠️ | `id`+`name` (legacy) | NAME_MISMATCH |
| 13 | paper-summarizer | `Paper Summarizer` ⚠️ | `id`+`name` (legacy) | NAME_MISMATCH · refs workspace |
| 14 | pdf | `pdf` ✅ | estándar | autor `Agentman` |
| 15 | pptx | `pptx` ✅ | estándar | autor `Agentman` |
| 16 | prd-generator | `prd-generator` ✅ | estándar | autor `opencode` |
| 17 | prompt-improvement | `prompt-improvement` ✅ | estándar | prefijo de path |
| 18 | python-standards | `python-standards` ✅ | estándar | — |
| 19 | skill-creator | `skill-creator` ✅ | estándar | ref rota `evals-schema.md` |
| 20 | skill-discovery | `Skill Discovery Helper` ⚠️ | `id`+`name` (legacy) | NAME_MISMATCH |
| 21 | task-management | `task-management` ✅ | estándar | — |
| 22 | ui-ux-pro-max | `ui-ux-pro-max` ✅ | mínimo | prefijo de path · sin license |
| 23 | xlsx | `xlsx` ✅ | estándar | autor `Agentman` |

⚠️ = `name` con Display Name (debe ser slug) · ❌ = frontmatter inválido/ausente

---

## 3. Hallazgos Detallados

### 🔴 3.1 Frontmatter no parseable

`core/scripts/skills_indexer.py` (L76) exige que el contenido empiece con `---`. Dos skills lo incumplen:

| Skill | Problema | Evidencia |
|-------|----------|-----------|
| **etl** | No tiene frontmatter YAML; empieza en `# ETL Data Processor` | `name`/`description` caen a fallback |
| **dashboard-pro** | Línea 1 = `# dashboard-pro — Skill`; el `---` está en L2 | Frontmatter ignorado |

**Efecto colateral confirmado** en `skills-index.json`:
```json
"dashboard-pro": {
  "description": "---\nid: dashboard-pro\nname: Dashboard Pro\ndescription: Genera dashboards..."
}
```
La descripción indexada es el **bloque de frontmatter crudo**, no la descripción real.

---

### 🟠 3.2 `skills-index.json` corrupto (tokens inválidos)

El indexador sobreescribe el `id` con el campo `name` del frontmatter:

```python
# core/scripts/skills_indexer.py L210-212
if "name" in frontmatter:
    skill_data["id"] = frontmatter["name"]
    skill_data["name"] = f"@{frontmatter['name']}"
```

6 skills declaran `name` como Display Name → generan ids con espacios y tokens `@` inválidos:

| `id` indexado (mal) | `name` indexado (mal) | Slug correcto |
|---------------------|-----------------------|---------------|
| `Content Optimizer` | `@Content Optimizer` | `content-optimizer` |
| `Context Evaluator` | `@Context Evaluator` | `context-evaluator` |
| `Decision Engine` | `@Decision Engine` | `decision-engine` |
| `MCP Builder` | `@MCP Builder` | `mcp-builder` |
| `Paper Summarizer` | `@Paper Summarizer` | `paper-summarizer` |
| `Skill Discovery Helper` | `@Skill Discovery Helper` | `skill-discovery` |

> Nota: estas 6 skills **ya declaran `id:` correcto** en su frontmatter, pero el indexador lo **ignora** (solo lee `name`). Dos correcciones posibles: normalizar `name` (Tier 1) **y/o** que el indexador prefiera `id` cuando exista.

---

### 🟠 3.3 Referencias rotas (archivos citados que no existen)

| Skill | Referencia citada | Estado real |
|-------|-------------------|-------------|
| context-evaluator | `rubrics/technical.json` | ❌ (solo existe `general.json`) |
| context-evaluator | `rubrics/ux.json` | ❌ |
| markdown-writer | `references/skill-template.md` | ❌ (vive en `skill-creator/references/`) |
| markdown-writer | `assets/templates/readme-template.md` | ❌ |
| skill-creator | `references/evals-schema.md` | ❌ |
| content-optimizer | `workspaces/content/drafts/` | ❌ |
| content-optimizer | `workspaces/content/CONTEXT.md` | ❌ |
| paper-summarizer | `workspaces/research/analysis/` | ❌ |
| paper-summarizer | `workspaces/research/papers/README.md` | ❌ |
| error-recovery | `core/.context/knowledge/errors/` | ❌ (¿lazy/runtime?) |
| error-recovery | `core/.context/knowledge/playbooks/` | ❌ (¿lazy/runtime?) |

> Las refs a `workspaces/*` y `knowledge/{errors,playbooks}` pueden ser **rutas de runtime** que se crean bajo demanda — verificar antes de borrarlas; si es así, documentarlo como tal.

---

### 🟠 3.4 Rutas de scripts con prefijo incorrecto (falta `core/`)

| Skill | Ruta citada | Ruta real |
|-------|-------------|-----------|
| etl | `skills/core/etl/processor.py` | `core/skills/core/etl/processor.py` |
| prompt-improvement | `skills/core/prompt-improvement/...` | `core/skills/core/prompt-improvement/...` |
| ui-ux-pro-max | `skills/ui-ux-pro-max/scripts/search.py` (×4) | `core/skills/core/ui-ux-pro-max/scripts/search.py` |
| csv-processor | `from core.skills.core.csv_processor.scripts.csv_processor import process_csv` | módulo con **guion** (`csv-processor`) → import inválido |

---

### 🟡 3.5 Esquema de frontmatter inconsistente

Schema documentado por **@skill-creator**: `name` (slug) + `description` + `license` (opc) + `metadata` (opc) + `compatibility` (opc).

| Esquema | Skills | Campos |
|---------|--------|--------|
| **Legacy "OBSOLETE/migration"** | content-optimizer, context-evaluator, decision-engine, dashboard-pro, mcp-builder, paper-summarizer, skill-discovery | `id, name, description, category, type, version, license, metadata{source: OBSOLETE/migration}, compatibility` |
| **`displayName`** | error-recovery | `name, displayName, version, category, description, license, metadata` |
| **Mínimo** | ui-ux-pro-max (`name, description`), data-viz (`name, description, category, version`) | sin `license`/`metadata` |
| **Estándar** | 13 skills restantes | conforme |

**Impacto**: `id` y `type` son ignorados por el indexador; `name` con Display Name rompe el `id` indexado (§3.2).

---

### 🟡 3.6 Scripts fuera de convención → invisibles al indexador

El indexador solo detecta `scripts/*.py` (`has_scripts`):

| Skill | Script | Ubicación real | Detectado |
|-------|--------|----------------|-----------|
| etl | `processor.py` | raíz de la skill | ❌ |
| data-viz | `viz_handler.py` | raíz de la skill | ❌ |

**Efecto**: `has_scripts: false` y `scripts_count` ausente en `skills-index.json`.

---

### 🔵 3.7 Sistema de skills TOML fantasma (legado)

Existe una **segunda arquitectura de skills** documentada pero inexistente en disco:

| Elemento | Estado |
|----------|--------|
| `core/skills/skill-creator.md` (v0.4.0-beta) | Describe skills `.toml` en `core/skills/<name>.toml` + `[entrypoint]` |
| `core/skills/skill_executor.py` (575 líneas) | Carga/ejecuta skills TOML (`discover_skills` hace glob de `*.toml`) |
| `core/scripts/skill_creator.py` (344 líneas) | Genera TOML; **0 refs a SKILL.md ni catalog.json** |
| Archivos `.toml` en `core/skills/` | **0** |

→ `skill_executor.discover_skills()` encontraría **0 skills** con el layout actual. Sistema paralelo muerto.

---

### 🔵 3.8 Manifests duplicados

| Skill | Archivos manifest | Nota |
|-------|-------------------|------|
| dashboard-pro | `SKILL.md` (frontmatter roto) + `skill.yaml` (schema propio: `modes`, `inputs`, `outputs`, `workflow`) | Solapa; `skill.yaml` parsea como 2 documentos YAML |
| skill-creator | `core/skills/core/skill-creator/SKILL.md` + `core/skills/skill-creator.md` (root) | Dos "creators" distintos |

---

### 🔵 3.9 Drift entre fuentes de verdad

Tres índices, sin sincronización garantizada:

| Fuente | Formato | Ejemplo de drift |
|--------|---------|------------------|
| `core/skills/SKILLS.md` | Tabla MD | descripción etl: "Manipulación y transformación de datos…" |
| `core/skills/catalog.json` | JSON | descripción etl: "Procesamiento ETL de datos" |
| `core/.context/knowledge/skills-index.json` | JSON (generado) | id `Content Optimizer` |
| — | categoría | data-viz: `Data` (SKILL.md) vs `Development` (catalog.json) |

---

### 🔵 3.10 Metadatos y contenido

| Hallazgo | Skills |
|----------|--------|
| `metadata.author: Agentman` (heredado de upstream) | pdf, xlsx, docx, pptx |
| `author: opencode` | json-prompt-generator, prd-generator, prompt-improvement, task-management |
| Ejemplo en **vietnamita** ("Làm landing page…") | ui-ux-pro-max |
| Typo `"diseniada"` (→ "diseñada") | content-optimizer |
| `catalog.json` `last_updated: 2026-08-15` | (desactualizado) |

---

## 4. Plan de Remediación

### Tier 1 — Desbloquear el indexado (crítico)

| Acción | Archivos |
|--------|----------|
| Normalizar `name:` al slug en 6 skills | `content-optimizer`, `context-evaluator`, `decision-engine`, `mcp-builder`, `paper-summarizer`, `skill-discovery` |
| Mover frontmatter al inicio (eliminar H1 previo) | `dashboard-pro/SKILL.md` |
| Añadir frontmatter YAML (`name`, `description`, `license`, `metadata`) | `etl/SKILL.md` |
| Regenerar índice | `python core/scripts/skills_indexer.py --rebuild` |

### Tier 2 — Reparar referencias

| Acción | Detalle |
|--------|---------|
| Corregir prefijos `core/` | etl, prompt-improvement, ui-ux-pro-max (×4) |
| Arreglar import Python | csv-processor (usar import por path o renombrar dir → decisión) |
| Crear o re-apuntar refs rotas | `rubrics/technical.json` + `ux.json`, `markdown-writer/references/skill-template.md` → apuntar a skill-creator, `readme-template.md`, `skill-creator/references/evals-schema.md` |
| Validar si son runtime y documentar | `workspaces/*`, `knowledge/{errors,playbooks}` |

### Tier 3 — Unificar esquema

- Eliminar `id`/`type`/`category` redundantes del esquema legacy; conservar `name` (slug), `description`, `license`, `metadata`, `compatibility`.
- Alinear `error-recovery` (quitar `displayName`).
- Añadir `license`/`metadata` a `ui-ux-pro-max` y `data-viz`.

### Tier 4 — Higiene / legado (requiere decisión)

- Archivar o eliminar sistema TOML fantasma (`skill-creator.md`, `skill_executor.py`) o marcarlo explícitamente como legacy.
- Resolver `dashboard-pro/skill.yaml` (fusionar en frontmatter o separar como manifiesto oficial).
- Mover scripts a `scripts/` (etl, data-viz) o ajustar el indexador.

### Tier 5 — Sincronización

- Unificar autores (`Agentman`/`opencode` → `FreakingJSON Framework`).
- Regenerar índice y verificar 0 drift entre `SKILLS.md` ↔ `catalog.json` ↔ `skills-index.json`.

---

## 5. Verificación

```bash
# 1. Regenerar índice
python core/scripts/skills_indexer.py --rebuild

# 2. Comprobar que todos los ids son slugs (sin espacios)
python -c "import json,io;d=json.load(io.open(r'core/.context/knowledge/skills-index.json',encoding='utf-8'));print([s['id'] for s in d['skills'] if ' ' in s['id']] or 'OK')"

# 3. Verificar frontmatter de las 23 skills
python -c "import glob,io,yaml;[print(p.split(chr(92))[-2], 'OK' if io.open(p,encoding='utf-8').read().lstrip(chr(65279)).startswith('---') else 'FAIL') for p in sorted(glob.glob('core/skills/core/*/SKILL.md'))]"
```

**Criterio de aceptación**: 0 ids con espacios · 0 `FAIL` de frontmatter · 23 skills con `name` == nombre de carpeta.

---

## 6. Anexo — Evidencia recolectada

- Parseo de frontmatter de los 23 `SKILL.md` (PyYAML): 6 NAME_MISMATCH, 2 sin frontmatter válido, 2 schema mínimo.
- `Test-Path` de 27+ rutas referenciadas: 7 MISS.
- `skills-index.json` (23 entries): 6 ids con Display Name, 1 descripción = frontmatter crudo.
- `catalog.json` (23) ↔ `SKILLS.md` (23) ↔ disco (23): conteos coinciden, contenidos divergen.
- `core/skills/**/*.toml`: **0** archivos → sistema TOML inactivo.

---

## 7. Fixes aplicados (2026-10-18)

### Tier 1 — Frontmatter
- Normalizado `name:` a slug en 6 skills (content-optimizer, context-evaluator, decision-engine, mcp-builder, paper-summarizer, skill-discovery).
- `dashboard-pro/SKILL.md`: frontmatter movido al inicio (H1 duplicado eliminado).
- `etl/SKILL.md`: frontmatter YAML agregado.

### Tier 2 — Referencias
- Creados `context-evaluator/rubrics/technical.json` y `rubrics/ux.json`.
- `markdown-writer`: ref a `skill-template.md` reapuntada a `skill-creator/references/`; creado `assets/templates/readme-template.md`.
- Creado `skill-creator/references/evals-schema.md`.
- Corregidos prefijos `core/`: etl, prompt-improvement (`SKILL.md` + `references.md`), ui-ux-pro-max (×4), markdown-style.md (enlace relativo).
- `csv-processor`: import Python inválido reemplazado por carga vía `importlib.util` (dir con guion).
- `error-recovery`: directorios `knowledge/{errors,playbooks}` documentados como auto-creados.
- `content-optimizer` / `paper-summarizer`: refs a `workspaces/*` reescritas como relativas al workspace configurado.

### Tier 3 — Schema
- Eliminados `id`/`type`/`category`/`source: OBSOLETE` redundantes; unificados `license`, `metadata`, `compatibility`.
- `error-recovery`: eliminado `displayName`.
- `ui-ux-pro-max` y `data-viz`: agregados `license`/`metadata`/`compatibility`.

### Tier 4 — Legado
- `core/skills/skill-creator.md` → `docs/legacy/skill-creator-toml.md`.
- Banners de deprecación en `skill_executor.py`, `skill_creator.py` y `__init__.py`.
- Creado `docs/legacy/README.md`.
- `dashboard-pro/skill.yaml`: se conserva como manifiesto extendido (referenciado por su README); el frontmatter de `SKILL.md` es la fuente canónica.
- **Eliminación definitiva (2026-10-18)**: ver §9.

### Tier 5 — Sincronización
- Scripts reubicados a `scripts/` (`etl/scripts/processor.py`, `data-viz/scripts/viz_handler.py`) → ahora detectados por el indexador.
- Autores normalizados a `FreakingJSON Framework` (pdf, xlsx, docx, pptx, json-prompt-generator, prd-generator, prompt-improvement, task-management).
- `catalog.json`: descripción de etl alineada y `last_updated` actualizado.
- `skills_indexer.py`: ahora lee `category` desde `catalog.json` (fuente canónica) en vez de fijar `core`.
- `skills-index.json` regenerado (`python core/scripts/skills_indexer.py --rebuild`).

### Verificación final
- 23/23 skills con frontmatter válido y `name` == carpeta.
- 0 ids con espacios en `skills-index.json`.
- 0 referencias rotas restantes (excluyendo la convención relativa `skills/core/{name}/SKILL.md` de la tabla de markdown-writer).

---

## 8. Integración nativa con OpenCode (2026-10-18)

Las 23 skills pasan de ser una **convención interna** (solo visibles si el agente leía los índices) a **skills nativas de OpenCode**, con alcance de framework.

### Mecanismo (3 capas)

| Capa | Archivo | Rol |
|------|---------|-----|
| **Declaración** | `opencode.jsonc` → `skills.paths: ["core/skills/core"]` | OpenCode escanea `**/SKILL.md` y expone las 23 skills vía la tool `skill` (progressive disclosure). |
| **Auto-reparación** | `.opencode/plugins/freakingjson-framework.ts` → hook `config` | Re-registra la ruta de skills en runtime si faltara (idempotente). `dev` → `core/skills/core`. |
| **Comportamiento** | mismo plugin → `experimental.chat.system.transform` | Inyecta reglas del framework (MVI, privacidad, persistencia, routing de workspaces). Marcador idempotente `<!-- freakingjson-framework -->`. |

Además `default_agent: "FreakingJSON"` fija el orquestador del framework como agente por defecto.

### Por qué es "condicionado al framework"
- La ruta de skills es **relativa al repo** → registro de proyecto, no global (`~/.config/opencode`).
- El plugin es **propiedad del framework** (`.opencode/plugins/`) y deriva la raíz de su propia ubicación.
- El comportamiento en runtime queda gobernado por las reglas del framework, no por defaults genéricos.

### Verificación
- 23/23 skills: `name` (frontmatter) == carpeta, slug válido, `description` presente → compatibles con el loader de OpenCode.
- `opencode.jsonc` parsea como JSON válido (comentarios `//` permitidos).
- `.opencode/plugins/freakingjson-framework.ts` pasa `node --experimental-strip-types --check`.

### Requisito operativo
- **Reiniciar OpenCode** para que cargue `skills.paths` + el plugin (la config no se recarga en caliente).

---

## 9. Eliminación del sistema TOML (2026-10-18)

Decisión: **eliminar** el sistema TOML en lugar de mantener shims deprecados. Evidencia: 0 archivos `*.toml` en el repo, `discover_skills()` encontraba 0 skills, y `pa.py` tenía un submenú de skills que nunca se invocaba.

| Acción | Artefacto |
|--------|-----------|
| Eliminado | `core/skills/skill_executor.py` |
| Eliminado | `core/scripts/skill_creator.py` |
| Eliminado | Submenú Skills de `core/scripts/pa.py` (7 funciones muertas) + `__pycache__` |
| Reescrito | `core/skills/__init__.py` → marcador de namespace (sin re-export) |
| Corregido | `pa.py` help: numeración del menú (Skills ya no existe) y listas de skills/agentes desactualizadas → apuntan a `SKILLS.md` / `AGENTS.md` |
| Conservado | `docs/legacy/skill-creator-toml.md` (solo documentación histórica) |
| Documentado | `docs/legacy/README.md`, `docs/SETUP-STANDALONE.md` |

`dashboard-pro/skill.yaml` **no** es legacy: es un manifiesto extendido activo (modos, inputs/outputs, workflow, style presets) referenciado por `SKILL.md` y `README.md`.

**Verificación**: `py_compile` OK · `import core.skills` OK · 0 referencias residuales a símbolos eliminados · contratos de documentación/versión/warm-start (25 tests) OK.

---

*Reporte generado por FreakingJSON-PA · fixes aplicados el 2026-10-18.*
