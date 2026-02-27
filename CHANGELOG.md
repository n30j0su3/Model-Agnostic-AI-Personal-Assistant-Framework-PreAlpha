# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased] - 2026-02-26

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

[0.1.0-alpha]: https://github.com/n30j0su3/Model-Agnostic-AI-Personal-Assistant-Framework-PreAlpha/releases/tag/v0.1.0-alpha
