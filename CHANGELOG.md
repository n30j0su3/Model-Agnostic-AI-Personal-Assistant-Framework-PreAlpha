# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Added
- *(En desarrollo - ver rama DEV)*

---

## [0.1.3-prealpha] - 2026-03-04

### Added
- **Workflow Standard v1.0**: Proceso estructurado de 7 pasos para tareas complejas
  - Paso 1: Recepción y Comprensión
  - Paso 2: Evaluar Recursos Locales  
  - Paso 3: Análisis y Planificación
  - Paso 4: Presentar Plan (autorización usuario)
  - Paso 5: Ejecución Estructurada
  - Paso 6: Documentación Automática
  - Paso 7: Resumen Final
- **Detección automática de complejidad**: Simple vs Complex vs Critical
- **Modo Express**: Opción para saltar paso 4 (aprobación) con transparencia al usuario
- **Configuración personalizable**: `config/workflow-config.yaml` con criterios ajustables
- **Integración Dashboard SPA**: Tab "Workflow" con visual guide, checklist interactivo, indicador de complejidad
- **Case Study**: Dashboard SPA v2.0 como ejemplo del workflow en acción
- **Documentación**: `docs/WORKFLOW-STANDARD.md` completo

### Changed
- `docs/PHILOSOPHY.md`: Agregado Principio #7 "Structured Workflow"
- `core/agents/pa-assistant.md`: Actualizado workflow a 7 pasos
- `core/agents/AGENTS.md`: Referencia al Workflow Standard
- `core/.context/navigation.md`: Rutas al nuevo workflow doc
- `dashboard.html`: Nuevo tab Workflow con visual guide interactivo

### Files Added/Modified
- docs/WORKFLOW-STANDARD.md (new, 351 lines)
- config/workflow-config.yaml (new, 212 lines)
- docs/workflow-test-example.md (new, ejemplo vivo)
- docs/PHILOSOPHY.md (updated)
- core/agents/pa-assistant.md (updated)
- core/agents/AGENTS.md (updated)
- core/.context/navigation.md (updated)
- dashboard.html (updated, +~100 líneas)

---

## [0.1.2-prealpha] - 2026-03-04

### Added
- **Dynamic Skill Scanning** (`core/scripts/session-start.py`)
  - `get_all_skills()`: Escanear `core/skills/core/` dinámicamente
  - Skills reales detectadas (~22) en lugar de subset hardcodeado (7)
  - Display actualizado: `"skill1, skill2... (+N más)"`

### Fixed
- **Loop de instalación en primera ejecución** (Issue crítico)
  - `install.py`: Fallback para crear `MASTER.md` si `MASTER.template.md` no existe
  - `pa.py`: Verificación post-instalación - sale con error si instalación falla
  - Evita loop infinito: "No se encontró MASTER.md" → "Sincroniza contexto primero"

---

## [0.1.1-prealpha] - 2026-03-03

### Fixed (Issues Críticos PROD)
- **Documentación MAC** - Soporte completo macOS/Linux
  - Creado `install.sh` - Instalador nativo shell para macOS/Linux
  - `install.py` ahora detecta SO y muestra comando correcto (`pa.bat` o `./pa.sh`)
  - README con comandos corregidos para todas las plataformas
  
- **Configuración OpenCode saneada**
  - `opencode.jsonc` con rutas relativas (npx) en lugar de rutas Windows absolutas
  - Token GitHub como placeholder (`YOUR_GITHUB_TOKEN_HERE`)
  - Sin credenciales hardcodeadas
  
- **README User-Friendly**
  - Tabla de requisitos con enlaces directos de descarga:
    - Python: python.org/downloads
    - Node.js: nodejs.org
    - Git: git-scm.com/downloads
    - OpenCode: `npm install -g opencode-ai`
  - Versión simplificada para usuarios (README-simple.md)
  
- **Skills actualizadas**
  - SKILLS.md: 22 skills documentadas completamente
  - 6 skills nuevas agregadas: content-optimizer, context-evaluator, dashboard-pro, decision-engine, mcp-builder, paper-summarizer
  - Corregidas descripciones duplicadas (copy-paste errors)

### Notes
- **Versión prealpha**: Mantiene `-prealpha` hasta completar frontend/dashboard (FE-001/002/003)
- **Cross-platform**: Validado en Windows, macOS y Linux
- **Sanitizado**: Sin archivos de desarrollo, sin credenciales, sin datos sensibles

---

## [0.1.1-alpha] - 2026-02-27

### Added
- **Skill Discovery System** (`@skill-discovery`)
  - Mapeo automático de tareas a skills existentes
  - Evita duplicación de funcionalidad (anti-patrones documentados)
  - Tablas de referencia rápida: CSV, Excel, PDF, documentos, productividad
  - Ubicación: `core/skills/core/skill-discovery/SKILL.md`
  
- **Sistema de Sync Bidireccional** (DEV ↔ BASE ↔ PROD)
  - `sync-dev-to-base.sh`: Sync seguro DEV → BASE con detección de commits [FRAMEWORK]
  - `sync-base-to-dev.sh`: Pull de actualizaciones de framework a DEV
  - `sync-base-to-prod.sh`: Publicación limpia a PROD con validaciones de seguridad
  - `sync-menu.bat`: Menú interactivo Windows para operaciones de sync
  - Validación automática de archivos sensibles antes de cualquier sync
  
- **Validación de Recursos** (`validate-dev-resources.py`)
  - Verifica recursos críticos antes de operaciones de sync
  - Previene pérdida de datos durante migraciones

### Changed
- **AGENTS.md**: Paso 3 obligatorio ahora incluye lectura de `SKILLS.md`
  - Los agentes AI deben verificar skills disponibles antes de crear scripts
  - Previene duplicación de funcionalidad existente
  
- **pa-assistant.md**: Nuevo "Protocolo Pre-Tarea"
  - Checklist obligatorio antes de ejecutar cualquier tarea
  - Paso 1: Verificar skill-discovery
  - Paso 2: Leer SKILL.md de la skill identificada
  - Paso 3: Ejecutar según protocolo de la skill

### Security
- **Sanitización completa de PROD**
  - Eliminados todos los archivos de usuario: sessions/, codebase/, vitals/, MASTER.md
  - PROD ahora contiene SOLO archivos de framework
  - Validación automática en sync-base-to-prod.sh previene subida de datos sensibles
  - Lista de exclusiones: API keys, secrets, passwords, shop IDs específicos

### Documentation
- **docs/backlog.md**: Backlog del framework con historial de decisiones
- **docs/backlog.view.md**: Vista alternativa del backlog (formato timeline)

### Dev Notes
- Framework versión: 0.1.0-alpha → 0.1.1-alpha (incremento menor, pre-alpha)
- Repositorios sincronizados: DEV → BASE → PROD
- Total de skills: 17 (incluyendo skill-discovery)
- Total de scripts de sync: 7 archivos

---

## [0.1.0-alpha.2] - 2026-02-26

### Added
- **INIT-PROTOCOL.md**: Complete framework initialization protocol
  - Detectable by any AI CLI (OpenCode, Claude, Gemini, Codex)
  - Workflow: Context → Understanding → Execution → Preservation
  - Quick commands system (/status, /save, /session, /ideas, /pending, /help)
- **context-scout-v2.md**: Enhanced context detection agent v2
  - Automatic discovery of relevant context files
  - MVI (Minimal Viable Information) principle
- **detect-workspace.py**: Automated workspace detection script
  - Framework and workspace detection by path
  - Manual search fallback

### Security
- Comprehensive PROD sanitization completed
- Removed: Template files, DEV-only tracking files, temporary reports
- Removed: Private context files
- Enhanced PROD_ONLY_IGNORE_PATTERNS with 20+ exclusion patterns
- Validated: opencode.jsonc contains only public MCP tools

### Pre-Deploy Validation Checklist
- [ ] No API keys in *.jsonc files
- [ ] No DEV tracking files
- [ ] No temporary reports
- [ ] core/.context/ contains only navigation.md + structure
- [ ] workspaces/ contains only empty structure

---

## [0.2.0-alpha] - 2026-02-24

### Added
- **@dashboard-pro** skill completa para generación de dashboards profesionales
  - **Modo con-dependencias**: Proyectos Next.js 15 + TypeScript + Tailwind + shadcn/ui + Recharts + TanStack Table
  - **Modo sin-dependencias**: Dashboards SPA en archivo HTML único (Tailwind CDN + Chart.js/ApexCharts/Vanilla SVG)
  - **4 presets de estilo**: fintech-dark, fintech-light, saas-modern, enterprise
  - **3 templates de charts**: Chart.js, ApexCharts, Vanilla SVG
  - **Documentación completa**: README.md, CONFIG.md, INTEGRATION.md, OPTIMIZATION.md
  - **Ejemplo funcional**: Dashboard fintech con 8 componentes (KPIs, charts, tablas)
- **Sistema de validación pre/post sync**:
  - `validate-dev-resources.py` - Verifica recursos críticos antes del sync
  - `validate-post-sync.py` - Valida integridad después del sync
- **Scripts de sync optimizados**:
  - `sync-prealpha-optimized.py` - Versión mejorada con reportes categorizados
  - Protección de directorios `_local/` (agentes/skills locales)
  - Modo `skill-only` para actualizaciones rápidas
- **Testing completo**: Dashboards de prueba en ambos modos (Next.js y HTML)

### Changed
- **sync-prealpha.py mejorado**: Agregada protección de directorios `_local/` y `workspaces/`
- **Documentación MVI**: Optimización de 35.2% en tamaño de documentación
- **Templates optimizados**: Reducción de 85.7% en templates HTML

### Stats
- +20 archivos nuevos
- +2,500 líneas de código/documentación
- 16 skills totales
- 35.2% optimización de templates

---

## [0.1.0-alpha] - 2026-02-11

### Added
- **4 nuevas skills core**:
  - `@skill-creator`: Framework para crear nuevas skills
  - `@markdown-writer`: Toolkit Markdown con principio MVI
  - `@csv-processor`: Procesamiento de datos CSV con pandas
  - `@python-standards`: Estándares y validación de código Python
- **5 agentes desplegados** en arquitectura de subagentes:
  - `@FreakingJSON-PA` (principal - modo producción)
  - `@session-manager`, `@context-scout`, `@doc-writer`, `@feature-architect`
- **15 skills totales** en producción
- **28 scripts validados** cross-platform (Windows/Linux/macOS)
- **Sistema de sync** entre 3 entornos: BASE (dev), DEV (test), PROD (release)
- **Scripts de utilidad**: backlog-manager.py, research-tool.py, test_framework.py
- **Metodología de trabajo** documentada con flujo BASE→DEV→PROD→PUBLIC

### Changed
- Reemplazados emojis por prefijos ASCII (`[OK]`, `[ERROR]`, `[WARN]`) para compatibilidad Windows
- Estandarizada estructura de skills con `SKILL.md`, `scripts/`, `references/`, `assets/`
- Configuración de agente por entorno (`FreakingJSON` en BASE/DEV, `FreakingJSON-PA` en PROD)

### Fixed
- `UnicodeEncodeError` en scripts con emojis en Windows
- Configuración de agente en PROD (ahora usa `FreakingJSON-PA`)
- Exclusión de archivos de desarrollo en entorno PROD

### Security
- Sanitización de archivos sensibles antes de deploy a PROD

### Philosophy
- **Frase insignia oficial**: *"El conocimiento verdadero trasciende a lo público."* / *"True knowledge transcends to the public."*
- **Enlaces del creador**: Instagram [@freakingjson](https://instagram.com/freakingjson), Blog [freakingjson.com](https://freakingjson.com), Linktree [linktr.ee/freakingjson](https://linktr.ee/freakingjson)

---

## [0.0.x] - Pre-release

### Initial development
- Estructura base del framework
- Configuración inicial de agentes
- Sistema de contexto local (`.context/`)

---

**Full release notes**: [docs/RELEASES/](docs/RELEASES/)

[0.1.1-prealpha]: https://github.com/n30j0su3/Model-Agnostic-AI-Personal-Assistant-Framework-PreAlpha/releases/tag/v0.1.1-prealpha
[0.1.1-alpha]: https://github.com/n30j0su3/Model-Agnostic-AI-Personal-Assistant-Framework-PreAlpha/releases/tag/v0.1.1-alpha
[0.1.0-alpha]: https://github.com/n30j0su3/Model-Agnostic-AI-Personal-Assistant-Framework-PreAlpha/releases/tag/v0.1.0-alpha
