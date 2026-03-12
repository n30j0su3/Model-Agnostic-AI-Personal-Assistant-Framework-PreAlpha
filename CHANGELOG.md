# Changelog / Registro de Cambios

All notable changes to this project will be documented in this file.  
Todos los cambios notables de este proyecto se documentarán en este archivo.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

---

## [0.2.1-prealpha] - 2026-03-12

### Added / Agregado

#### Sistema de Sanitización PROD
- **Sanitización de codebase/**: Templates en `.sanitized/` para limpiar información interna
- **sync-auditor.py**: Script de auditoría para verificar exclusiones en local/remote
- **Validación POST-SYNC**: Verifica que archivos excluidos no existan en destino
- **SESSION_TEMPLATE.md**: Template de sesión para usuarios nuevos

### Changed / Cambiado
- **PROD_ONLY_IGNORE_PATTERNS**: Exclusiones expandidas para knowledge/users, interactions, errors
- **Cleanup POST-SYNC**: Eliminación automática de directorios con datos de usuario
- **docs/core/PRP-009**: Documentación actualizada con proceso de saneado

### Fixed / Corregido
- **CORE-007**: Archivos excluidos eliminados del repositorio remoto público
- **Staging = Remote**: Garantizado que el staging publicado es idéntico al remoto
- **Validación framework-guardian**: Pasa en pre-release y pre-push

### Security / Seguridad
- Limpieza de información interna en PROD (sesiones, usuarios, interacciones)
- Config obsoleta eliminada (knowledge_base.json, mcp.json, quotas.json)

---

## [0.2.0-prealpha] - 2026-03-11

### Added / Agregado

#### Framework Enforcement System
- **CORE-008 Framework Enforcement**: Sistema de validación obligatoria de procesos CORE
- **framework-guardian.py**: Validación automática antes de commits/pushes/releases
- Configuración en `config/framework.yaml` con niveles (warn/block/log)

#### Knowledge Extraction
- **knowledge-extractor.py**: Extracción automática de descubrimientos, prompts, ideas
- Tags de detección: `#discovery`, `#prompt-success`, `#idea`, `#best-practice`
- Integración con session-end.py para preservación automática

#### Session Management
- **AGENTS.md**: Agregado al tracking de versiones
- **session-end.py**: Cierre automático via atexit
- **session-start.py**: Verificación opcional de enforcement

### Changed / Cambiado
- **VERSION sync**: Ahora sincroniza 9 archivos (incluyendo AGENTS.md, ROADMAP.md, pa.py)
- **Enforcement timing**: pre-commit, pre-push, pre-release, session-end
- **CHANGELOG.md**: Estructura mejorada con secciones de seguridad

### Fixed / Corregido
- VERSION mismatch entre commits y archivos
- AGENTS.md faltante en BASE

---

## [0.1.8-prealpha] - 2026-03-11

### Added / Agregado

#### Procesos CORE
- **CORE-005 Assembly Line**: Bucle agéntico estándar para tareas complejas (Delimitar → Mapear → Ejecutar → Validar → Preservar)
- **CORE-006 Version Governance**: Gestión automática de versión del framework
- **CORE-007 Release Sanitization**: Protección de datos del usuario durante actualizaciones

#### Skills
- **@error-recovery**: Sistema de recuperación de errores con logging dual (JSON+MD)
- **@skill-evaluator**: Evaluador de calidad de skills (LLM-as-a-Judge)
- **Pattern Analyzer**: Análisis de tendencias de errores
- **eval-viewer**: Visualizador HTML para evaluaciones de skills

#### Recovery Playbooks
- PB-001: Encoding errors (UnicodeEncodeError, charmap codec)
- PB-002: File operations (FileNotFoundError, permissions)
- PB-003: JSON parsing (JSONDecodeError, malformed JSON)

#### Herramientas
- **version-updater.py**: Sincronización automática de versión en 9 archivos
- **skills-index.json**: Índice de 23 skills generadas automáticamente
- **agents-index.json**: Índice de 6 agentes generados automáticamente

### Changed / Cambiado
- Dashboard actualizado con nuevos skills y agentes
- `sync-prealpha.py`: Mejoras en protección de datos
- Knowledge Base estructurada con learning/, self-healing/, prompts/

### Fixed / Corregido
- Sincronización de versión en todos los archivos del framework
- Mensajes de sesión mejorados para primera ejecución

### Security / Seguridad
- Validación de staging antes de push a repositorio público
- Exclusión automática de archivos internos de desarrollo

---

## [0.1.7-prealpha] - 2026-03-11

### Added / Agregado
- **FASE 2A: Skill-Creator v2** - Enhanced skill creation workflow
  - `@skill-evaluator`: Automated skill quality assessment
  - `eval-viewer`: HTML visualization for skill evaluations
- **FASE 2B: @error-recovery** - Antifragile error handling skill
  - Pattern analyzer for error classification and learning
  - Recovery playbooks system for reusable error solutions
- `config/framework.yaml` - Centralized framework configuration

### Fixed / Corregido
- `sync-prealpha.py`: Branch validation and push improvements
- `session-indexer.py`: KeyError exception on missing session fields
- Various session management edge cases

---

## [0.1.6-prealpha] - 2026-03-10

### Fixed / Corregido
- **Inicialización de Contexto**: Error al iniciar sesión corregido
  - Creada estructura `core/.context/codebase/` (recordatorios.md, ideas.md)
  - Creada estructura `core/.context/knowledge/` completa
  - Script `kb-init.py` para inicializar KB manualmente
- **Knowledge Base**: Sistema de almacenamiento de conocimiento funcional
- **Session Start**: Muestra KB disponible correctamente

---

## [0.1.5-prealpha] - 2026-03-06

### Fixed / Corregido
- **Estructura docs/dashboard/**: Creado en BASE y DEV para consistencia
- **Ruta dashboard-data.js**: Corregida a `docs/dashboard/dashboard-data.js`
- **Sanitización PROD**: Eliminados docs internos sensibles
- **VERSION bump**: Corrección de versionado para updates automáticos

---

## [0.1.4-prealpha] - 2026-03-06

### Added / Agregado
- **Dashboard 2.0**: SPA funcional con datos embebidos (CORS-free)
- **Knowledge-base System**: Infraestructura de conocimiento
  - `knowledge-indexer.py`, `interaction-logger.py`, `optimization-reporter.py`
- **Comandos Opencode**: 7 comandos personalizados (`ideas`, `optimize`, `pa-help`, `pa-status`, `pending`, `save`, `session`)
- **Sync System v2**: Protecciones extendidas para DEV

### Fixed / Corregido
- Restauración de funcionalidades críticas dañadas por sync
- CORS para uso offline (file://)
- Modales del Dashboard operativos

---

## [0.1.3-prealpha] - 2026-03-04

### Added / Agregado
- **Workflow Standard v1.0**: Proceso estructurado de 7 pasos
- **Detección automática de complejidad**: Simple vs Complex vs Critical
- **Modo Express**: Opción para saltir aprobación con transparencia
- **Integración Dashboard SPA**: Tab "Workflow" interactivo

### Changed / Cambiado
- `docs/PHILOSOPHY.md`: Principio #7 "Structured Workflow"
- `core/agents/pa-assistant.md`: Workflow actualizado a 7 pasos

---

## [0.1.2-prealpha] - 2026-03-04

### Added / Agregado
- **Dynamic Skill Scanning** en `session-start.py`
  - `get_all_skills()`: Escaneo dinámico de `core/skills/core/`
  - Skills reales detectadas (~22) vs hardcodeadas (7)

### Fixed / Corregido
- **Loop de instalación**: Fallback para crear MASTER.md
- `pa.py`: Verificación post-instalación

---

## [0.1.1-prealpha] - 2026-03-03

### Added / Agregado
- **Soporte macOS/Linux**: `install.sh` nativo para shell
- **Skills actualizadas**: 22 skills documentadas, 6 nuevas
- README user-friendly con enlaces de descarga

### Fixed / Corregido
- `opencode.jsonc`: Rutas relativas, sin credenciales hardcodeadas
- Descripciones duplicadas corregidas en SKILLS.md

---

## [0.1.1-alpha] - 2026-02-27

### Added / Agregado
- **Skill Discovery System** (`@skill-discovery`)
- **Sistema de Sync Bidireccional** (DEV ↔ BASE ↔ PROD)
- **Validación de Recursos** (`validate-dev-resources.py`)

### Security / Seguridad
- Sanitización completa de PROD
- Validación automática de archivos sensibles

---

## [0.1.0-alpha] - 2026-02-11

### Added / Agregado
- **4 nuevas skills core**: `@skill-creator`, `@markdown-writer`, `@csv-processor`, `@python-standards`
- **5 agentes desplegados**: `@FreakingJSON-PA`, `@session-manager`, `@context-scout`, `@doc-writer`, `@feature-architect`
- **15 skills totales** en producción
- **28 scripts validados** cross-platform
- **Sistema de sync** entre 3 entornos

### Changed / Cambiado
- Emojis reemplazados por prefijos ASCII para compatibilidad Windows
- Estructura de skills estandarizada

---

## [0.0.x] - Pre-release

### Added / Agregado
- Estructura base del framework
- Configuración inicial de agentes
- Sistema de contexto local (`.context/`)

---

**Full release notes**: [docs/RELEASES/](docs/RELEASES/)

[Unreleased]: https://github.com/n30j0su3/Model-Agnostic-AI-Personal-Assistant-Framework-PreAlpha/compare/v0.1.7-prealpha...HEAD
[0.1.7-prealpha]: https://github.com/n30j0su3/Model-Agnostic-AI-Personal-Assistant-Framework-PreAlpha/compare/v0.1.6-prealpha...v0.1.7-prealpha
[0.1.6-prealpha]: https://github.com/n30j0su3/Model-Agnostic-AI-Personal-Assistant-Framework-PreAlpha/releases/tag/v0.1.6-prealpha