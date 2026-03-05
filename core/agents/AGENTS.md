# Personal Assistant Agents Index

> Índice central de agentes del framework. Los agentes se definen en archivos `.md` con YAML frontmatter.

## Arquitectura

```
Main Agent (FreakingJSON-PA)
├── ContextScout      → Descubrimiento de contexto (read-only)
├── SessionManager    → Gestión de sesiones diarias
├── DocWriter         → Documentación automática
└── FeatureArchitect  → Arquitecto de producto (dev-only)
```

## Agente Principal

### @FreakingJSON-PA
- **Propósito**: Asistente personal principal en modo producción. Orquesta sesiones, contexto y delegación para usuarios finales.
- **Archivo**: `pa-assistant.md` (agente: FreakingJSON-PA)
- **Estado**: OPERATIVO
- **Dependencias**: context-scout, session-manager, doc-writer, feature-architect

## Subagentes

### @context-scout
- **Propósito**: Descubre y recomienda archivos de contexto. Read-only.
- **Archivo**: `subagents/context-scout.md`
- **Estado**: OPERATIVO

### @session-manager
- **Propósito**: Crea, gestiona y cierra sesiones diarias.
- **Archivo**: `subagents/session-manager.md`
- **Estado**: OPERATIVO

### @doc-writer
- **Propósito**: Genera documentación de sesiones y conocimiento.
- **Archivo**: `subagents/doc-writer.md`
- **Estado**: OPERATIVO

### @feature-architect
- **Propósito**: Arquitecto de producto y guardián de la filosofía. Evalúa, planea y ejecuta features del backlog sin solapamientos.
- **Archivo**: `subagents/feature-architect.md`
- **Estado**: OPERATIVO
- **Modo**: DEV-ONLY (no disponible en producción)
- **Dependencias**: prd-generator, task-management

---

## Jerarquía de Delegación

```
Usuario → FreakingJSON-PA → [Comprende tarea]
                        ├── ContextScout (¿qué contexto necesito?)
                        ├── Ejecuta directamente (tareas simples)
                        ├── SessionManager (gestión de sesión)
                        ├── DocWriter (documentación)
                        └── FeatureArchitect (arquitectura de features - dev)
```

> **Workflow Standard**: Todos los agentes del framework siguen el **Workflow Standard de 7 pasos** para tareas complejas. Ver documentación completa en `docs/WORKFLOW-STANDARD.md`.
>
> **Modo Express**: Para tareas simples (1-3 archivos), los agentes pueden operar en modo express omitiendo la planificación detallada (paso 4), siempre con transparencia hacia el usuario.

## Crear Nuevo Agente

1. Crear archivo `.md` en `subagents/` con YAML frontmatter
2. Definir: `id`, `name`, `description`, `type: subagent`, `tools`, `permissions`
3. Agregar referencia en este archivo (AGENTS.md)
4. Agregar dependencia en `FreakingJSON-PA` (pa-assistant.md) si aplica

---

## 🧠 Filosofía de los Agentes

### FreakingJSON

El agente **FreakingJSON** representa la esencia del framework: un asistente que prioriza la soberanía del conocimiento y el control del usuario sobre sus datos.

**Frase Insignia:**
> *"El conocimiento verdadero trasciende a lo público."*
> 
> *"True knowledge transcends to the public."*

**Principios:**
- **Local-first**: El conocimiento reside en archivos locales, no en servidores externos
- **Vendor-agnostic**: Funciona con cualquier proveedor de IA (OpenAI, Claude, Gemini, local)
- **Extensible**: Arquitectura de skills que permite crecer sin límites
- **Trazable**: Cada sesión, decisión y aprendizaje queda documentado

### Instrucción Vital-Core Permanente (BL-131)

**TODOS los agentes del framework DEBEN cumplir:**

1. **Uso de Agentes del Framework**: Delegar a `@context-scout`, `@session-manager`, `@doc-writer` cuando sea apropiado
2. **Prioridad Local**: Preferir `read/grep/glob` de archivos sobre memoria de conversación
3. **Persistencia**: Guardar TODO conocimiento valioso en archivos `.md` locales

**Verificación**: ¿Usé agentes? ¿Verifiqué locales? ¿Guardé en .md?

**Filosofía operativa:**
> *"I own my context. I am FreakingJSON."*
