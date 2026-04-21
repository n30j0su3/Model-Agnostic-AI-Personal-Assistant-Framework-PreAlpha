# Quick-Start — PA Framework

> **Fecha**: 2026-04-20 | **Versión**: 0.3.7-alpha | Archivo de inicio rápido (<500 tokens)

---

## Usuario
- **Idioma**: ES (primario), EN (secundario)
- **Estilo**: Claro y conciso; ampliar cuando sea necesario
- **Decisiones**: Presenta opciones con pros/contras cuando aplique

---

## Skills Disponibles (invocar con @nombre)

| Skill | Propósito |
|-------|-----------|
| @task-management | Gestión y seguimiento de tareas |
| @pdf | Procesamiento de archivos PDF |
| @xlsx | Hojas de cálculo Excel |
| @csv-processor | Limpieza y análisis de CSV |
| @docx | Documentos Word |
| @pptx | Presentaciones PowerPoint |
| @data-viz | Visualización con Seaborn/Matplotlib |
| @etl | Extracción, transformación, carga de datos |
| @prd-generator | Product Requirements Documents |
| @skill-discovery | Encontrar skills existentes antes de crear |
| @prompt-improvement | Optimización de prompts |
| @decision-engine | Decidir: local, delegación, o LLM remoto |
| @error-recovery | Self-healing con recovery playbooks |

> **⚠️ ANTES de crear scripts**: Consultar `@skill-discovery` para evitar duplicados.

---

## Agentes

| Agente | Propósito |
|--------|-----------|
| @FreakingJSON-PA | Agente principal (orquestación, sesiones) |
| @context-scout | Descubrimiento de contexto relevante |
| @skill-finder | Ruteo de capabilities |
| @session-manager | Gestión de sesiones diarias |
| @doc-writer | Documentación MVI |
| @skill-finder | Discovery de skills |

---

## Navegación Clave

| Archivo | Propósito |
|---------|-----------|
| `core/.context/sessions/YYYY-MM-DD.md` | Sesión del día |
| `core/.context/codebase/ideas.md` | Ideas y descubrimientos |
| `core/.context/codebase/recordatorios.md` | Pendientes |
| `core/.context/knowledge/users/default/preferences.md` | Preferencias persistentes del usuario |
| `core/skills/SKILLS.md` | Catálogo completo de skills |
| `core/agents/AGENTS.md` | Índice de agentes |

---

## Principio MVI

**Minimal Viable Information**: Solo lo esencial por archivo.
- 1-3 oraciones por concepto
- 3-5 bullets por sección
- Referencia docs completos, no duplicar

---

## Inicio de Sesión

```bash
python core/scripts/session_start.py
```

> **⚠️ AUTO-DESCUBRIMIENTO**: Antes de responder al usuario, el agente DEBE ejecutar:
>
> ```bash
> python core/scripts/persistent_storage_discover.py
> ```
>
> Esto auto-descubre SQLite (sesiones persistentes), Wiki (MkDocs), y MD memory.
> Si algún sistema está disponible, usarlo como fuente de contexto adicional.

> Antes de responder al usuario en una nueva sesión, revisar también:
>
> - `core/.context/knowledge/users/default/preferences.md`

Este archivo (`quick-start.md`) es el punto de entrada canonical.
Para tareas complejas, leer `pa-assistant.md` para detalle completo del workflow.
