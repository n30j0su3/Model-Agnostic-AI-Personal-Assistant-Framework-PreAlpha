# Quick-Start — PA Framework

> **Fecha**: 2026-04-28 | **Version**: 0.3.7-alpha | Archivo de inicio rapido (<500 tokens)

---

## ⚠️ PASO OBLIGATORIO — AUTO-DESCUBRIMIENTO DE MEMORIA

**Antes de responder al usuario, el agente DEBE ejecutar:**

```bash
python core/scripts/persistent_storage_discover.py --integration
```

Esto descubre **SQLite** (sesiones persistentes), **Wiki** (MkDocs/conocimiento),
**MD Memory** (memoria en archivos .md) y **Sessions MD** (bitacoras diarias).

Si algun sistema esta disponible, usarlo como fuente de contexto adicional.

**Segundo paso obligatorio** — revisar preferencias de usuario:
```bash
cat core/.context/knowledge/users/default/preferences.md
```

---

## Usuario

- **Idioma**: ES (primario), EN (secundario)
- **Estilo**: Claro y conciso; ampliar cuando sea necesario
- **Decisiones**: Presenta opciones con pros/contras cuando aplique

---

## Skills Disponibles (invocar con @nombre)

| Skill | Proposito |
|-------|-----------|
| @task-management | Gestion y seguimiento de tareas |
| @pdf | Procesamiento de archivos PDF |
| @xlsx | Hojas de calculo Excel |
| @csv-processor | Limpieza y analisis de CSV |
| @docx | Documentos Word |
| @pptx | Presentaciones PowerPoint |
| @data-viz | Visualizacion con Seaborn/Matplotlib |
| @etl | Extraccion, transformacion, carga de datos |
| @prd-generator | Product Requirements Documents |
| @skill-discovery | Encontrar skills existentes antes de crear |
| @prompt-improvement | Optimizacion de prompts |
| @decision-engine | Decidir: local, delegacion, o LLM remoto |
| @error-recovery | Self-healing con recovery playbooks |

> **⚠️ ANTES de crear scripts**: Consultar `@skill-discovery` para evitar duplicados.

---

## Agentes

| Agente | Proposito |
|--------|-----------|
| @FreakingJSON-PA | Agente principal (orquestacion, sesiones) |
| @context-scout | Descubrimiento de contexto relevante |
| @skill-finder | Ruteo de capabilities |
| @session-manager | Gestion de sesiones diarias |
| @doc-writer | Documentacion MVI |

---

## Navegacion Clave

| Archivo | Proposito |
|---------|-----------|
| `core/.context/sessions/YYYY-MM-DD.md` | Sesion del dia |
| `core/.context/codebase/ideas.md` | Ideas y descubrimientos |
| `core/.context/codebase/recordatorios.md` | Pendientes |
| `core/.context/knowledge/users/default/preferences.md` | Preferencias persistentes del usuario |
| `core/skills/SKILLS.md` | Catalogo completo de skills |
| `core/agents/AGENTS.md` | Indice de agentes |
| `core/.context/navigation.md` | Mapa completo de archivos del framework |

---

## Principio MVI

**Minimal Viable Information**: Solo lo esencial por archivo.
- 1-3 oraciones por concepto
- 3-5 bullets por seccion
- Referencia docs completos, no duplicar

---

## Inicio de Sesion

```bash
python core/scripts/session_start.py
```

> Antes de responder al usuario en una nueva sesion, revisar tambien:
>
> - `core/.context/knowledge/users/default/preferences.md`

Este archivo (`quick-start.md`) es el punto de entrada canonical.
Para tareas complejas, leer `pa-assistant.md` para detalle completo del workflow.
