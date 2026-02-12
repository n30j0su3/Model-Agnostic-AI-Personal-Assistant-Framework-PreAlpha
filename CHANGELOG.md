# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [0.1.0-alpha] - 2026-02-11

### Added
- **4 nuevas skills core**:
  - `@skill-creator`: Framework para crear nuevas skills
  - `@markdown-writer`: Toolkit Markdown con principio MVI
  - `@csv-processor`: Procesamiento de datos CSV con pandas
  - `@python-standards`: Estándares y validación de código Python
- **5 agentes desplegados** en arquitectura de subagentes:
  - `@pa-assistant` (principal)
  - `@session-manager`, `@context-scout`, `@doc-writer`, `@feature-architect`
- **15 skills totales** en producción
- **28 scripts validados** cross-platform (Windows/Linux/macOS)
- **Sistema de sync** entre 3 entornos: BASE (dev), DEV (test), PROD (release)
- **Scripts de utilidad**: backlog-manager.py, research-tool.py, test_framework.py
- **Metodología de trabajo** documentada con flujo BASE→DEV→PROD→PUBLIC

### Changed
- Reemplazados emojis por prefijos ASCII (`[OK]`, `[ERROR]`, `[WARN]`) para compatibilidad Windows
- Estandarizada estructura de skills con `SKILL.md`, `scripts/`, `references/`, `assets/`
- Configuración de agente por entorno (`FreakingJSON` en BASE/DEV, `pa-assistant` en PROD)

### Fixed
- `UnicodeEncodeError` en scripts con emojis en Windows
- Configuración de agente en PROD (ahora usa `pa-assistant`)
- Exclusión de archivos de desarrollo en entorno PROD

### Security
- Sanitización de archivos sensibles antes de deploy a PROD

---

## [0.0.x] - Pre-release

### Initial development
- Estructura base del framework
- Configuración inicial de agentes
- Sistema de contexto local (`.context/`)

---

**Full release notes**: [docs/RELEASES/](docs/RELEASES/)

[0.1.0-alpha]: https://github.com/n30j0su3/Model-Agnostic-AI-Personal-Assistant-Framework-PreAlpha/releases/tag/v0.1.0-alpha
