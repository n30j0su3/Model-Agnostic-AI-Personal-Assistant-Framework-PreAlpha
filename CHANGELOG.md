# Changelog

## [v0.4.0-beta] - 2026-08-15 (Fresh Install Impecable + Ecosistema)

> Release consolidado del plan de mejora 2026-08 (4 fases). Sin breaking changes de API;
> los datos del usuario (sesiones, memoria, backlog, workspaces) se preservan al actualizar.

### Fase 1 — Memoria Unificada
- Búsqueda unificada MD + SQLite (`session_search` ya ve las capturas del `message_hook`).
- `knowledge_extractor` lee SQLite directamente (adapter) + CLI completa.
- Facts automáticos: "Recuerda que..." -> `user_facts` sin tags residuales.
- `system_check --fix` crea MASTER.md/profile.md desde templates.
- MASTER.md/profile.md movidos a .gitignore (previene leak de contexto personal).
- Dashboard-data conectado a la memoria unificada; fecha real (antes hardcodeada).

### Fase 2 — Fresh Install Impecable
- `session_start` auto-heal: primer arranque crea contexto base (0 errores sin comandos extra).
- Doc-drift cero: 17 archivos limpiados (framework-guardian inexistente, scripts con
  guion renombrados, launchers reales, propagación legacy).
- Versiones sincronizadas en todos los archivos vía `version_updater`.

### Fase 3 — Ecosistema
- context-scout v1+v2 fusionados (la v2 era huérfana y estaba sin router).
- Catálogo de skills 23/23 sincronizado (8 skills faltantes agregadas).
- `migrate.py`: bug crítico corregido — creaba backlog.md como JSON '{}'.
  Ahora los .md se crean desde seeds con el formato correcto.
- Backlog CRUD funcional desde fresh install (seed + auto-fix).

### Fase 4 — Release v0.4.0-beta
- Version bump coordinado (VERSION, README, AGENTS, dashboard, pa.py, ROADMAP, branding).
- Release notes honestas en docs/RELEASES/v0.4.0-beta.md.
- Gate E2E de actualización validado (v0.3.8 -> v0.4.0 preservando datos).

**Tests:** 231 passed, 1 skipped (suite completa).



All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [v0.3.9-alpha] - 2026-08-15 (Unified Memory)

### Fixed

- **Busqueda unificada MD + SQLite**: `session_search.py` ahora indexa TAMBIEN las sesiones capturadas via `message_hook`/`SessionBridge` en `data/sessions.db` (antes: solo leia `.context/sessions/*.md`, por lo que la memoria capturada era invisible para la busqueda). Feature-flag `sessions.unified_search` en `config/framework.yaml` para rollback.
- **Knowledge extraction conectado a SQLite**: nuevo adapter `SQLiteSessionContent` + CLI en `knowledge_extractor.py`. Antes el script no tenia CLI y `memory_pipeline` lo invocaba sin efecto (false-green reportado como exito).
- **Facts automaticos**: `message_hook.py` extrae "Recuerda que..." de mensajes de usuario y los persiste en `user_facts` (SQLite) via `SessionBridge.set_user_fact`.
- **system_check --fix crea MASTER.md y profile.md**: desde `MASTER.template.md` / `profile.template.md`. Fresh install queda en 0 errores tras `--fix`.
- **Dashboard data conectado a la memoria unificada**: `generate_dashboard_data.py` incluye sesiones SQLite capturadas (antes solo leia el indice MD = 0 sesiones visibles) y usa fecha real de generacion (antes hardcodeada a 2026-03-06).

### Added

- `core/.context/profile.template.md`: template de perfil personal (no se sube al repo).
- `.gitignore`: `core/.context/MASTER.md` y `core/.context/profile.md` nunca se commitean (contexto personal del usuario).

---

## [v0.3.8-alpha] - 2026-04-28 (Production Audit + Sanitization)

### Added

- **system_check.py**: Script de validacion integral con 23 componentes, modo `--fix` y salida JSON.
- **Auto-descubrimiento de memoria**: `session_start.py` ejecuta automaticamente `persistent_storage_discover.py` y muestra estado de SQLite, Wiki, MD Memory y Sessions MD al iniciar sesion.
- **Seed files para MD Memory y Wiki**: Directorios `core/.context/memory/` y `core/.context/knowledge/wiki/` incluidos en distribucion con archivos semilla.
- **pa.bat /help /version**: Seccion de ayuda para usuarios no tecnicos en ASCII puro.
- **README.md redirect**: Usuarios nuevos redirigidos a `README-simple.md` como entry point.
- **navigation.md**: Archivo de navegacion faltante creado con mapa completo de archivos clave.
- **update-protected-paths.txt**: Poblado con 27 paths protegidos durante actualizaciones.

### Fixed

- **Windows UTF-8 encoding**: `pa.py`, `install.py`, `system_check.py` ahora configuran `sys.stdout` para UTF-8 en Windows, corrigiendo acentos corruptos.
- **CLI opencode error**: Mensaje cambiado de `[ERROR]` a `[WARN]` con fallback automatico a modo manual.
- **Migraciones auto-aplicadas**: `session_start.py` ya no solo muestra warning — aplica `migrate.py --apply` automaticamente.
- **Leaks sanitizados**: Eliminados paths reales de desarrollador (`/home/freakingjson/`) de documentacion y ejemplos. Eliminado QA checklist interno con datos de entorno DEV.
- **Terminologia interna sanitizada**: Referencias a BASE/DEV/PROD reemplazadas por lenguaje generico.
- **Versiones sincronizadas**: Todos los archivos actualizados de `v0.3.0-alpha` a `v0.3.7-alpha` (READMEs, docstrings, banners, metadata).

### Changed

- **quick-start.md**: Auto-descubrimiento movido al TOP como instruccion obligatoria.

## [v0.3.7-alpha] - 2026-04-20 (Memory Pipeline + Dashboard)

### Added

- **Dashboard Visual Interface v2.0**: dashboard.html (20KB) — Glass morphism + neon glow + CRT scanlines + LED indicators animados. Matrix/Cyberpunk themes (press 'T'). JetBrains Mono + Space Grotesk typography. Professional dark cyberpunk aesthetic.
  - Visual overview de scripts, storage, y configuration.
  - Links a documentation files.
  - Responsive grid layout con dark theme.
  - Generado via generate_dashboard_data.py.
- **Memory Pipeline System**: Sistema de memoria persistente que permite recordar entre sesiones.
  - **MODE A (Session Start)**: Cargar contexto de sesiones anteriores al iniciar sesión.
  - **MODE B (Interval Timer)**: Ejecutar ciclo de memoria cada N minutos (configurable, default 15 min).
  - **MODE C (Session End)**: Guardar estado completo al cerrar sesión.
- **memory_pipeline.py**: Orquestador central con CLI completo:
  - `--load-context`: Cargar contexto para session_start
  - `--full-cycle`: Ejecutar ciclo completo (session_end)
  - `--watch --interval N`: Watch mode background
  - `--status`: Ver estado del pipeline
  - `--set-interval N`: Configurar intervalo
- **core/.context/memory/**: Nueva estructura de directorios para memoria persistente:
  - `summaries/`: Resúmenes de sesión
  - `context/`: Context injection files
  - `profile/`: Perfil de usuario actualizado automáticamente
- **docs/memory-pipeline/**: Documentación del sistema:
  - `MEMORY-PIPELINE-PLAN.md`: Plan unificado con arquitectura y flujos
  - `README.md`: Guía de uso rápida
- **persistent_storage_discover.py**: Script de auto-descubrimiento de sistemas de almacenamiento.
  - Detecta SQLite (sessions.db), Wiki (MkDocs), MD memory automáticamente.
  - CLI: `--verbose`, `--json`, `--integration` (status para agent prompts).
  - Integración en quick-start.md como paso obligatorio antes de responder usuario.

### Fixed

- **pa.py menu**: Opción "4. [CONFIG] Skills" eliminada (no funcional en esta versión).
  - Menu ahora 7 opciones (1-7 + 0 exit).
  - Handlers renumerados: SYNC→4, LAUNCH→5, UPDATE→6, HELP→7.

### Configuration

```yaml
# config/framework.yaml
memory_pipeline:
  enabled: true
  interval_minutes: 15
  modes:
    session_start: true   # MODE A
    interval: true        # MODE B
    session_end: true     # MODE C
  memory_dir: core/.context/memory
  max_sessions_in_context: 3
  max_context_length: 2000
```

### Integration Points

| Script | Integration | Mode |
|--------|-------------|------|
| `session_start.py` | Load context | MODE A |
| `session_end.py` | Full cycle | MODE C |
| `session_autosave.py` | Optional interval | MODE B |

---

## [v0.3.6-alpha] - 2026-04-20 (QA regression: memory/session/recovery)

### Fixed

- **Blocker: integration recovery flow could not import orchestrator in path-loaded contexts**.
  - `core/recovery/orchestrator.py` used only `from core.recovery.triggers ...`.
  - In integration runs that load modules via `importlib` with `core/` on `sys.path`, this raised `ModuleNotFoundError: No module named 'core'`.
  - Added resilient fallback import path that loads `core/recovery/triggers.py` directly via `importlib.util.spec_from_file_location` when package import is unavailable.

### Validation

- `python3 -m py_compile core/scripts/session_start.py core/scripts/session_end.py core/scripts/session_saver.py core/scripts/session_bridge.py core/scripts/memory_sync.py core/memory/session_memory.py core/recovery/orchestrator.py core/recovery/triggers.py core/scripts/pa.py` → **OK**
- `python3` compile sweep over `core/scripts/*.py` → **checked=56, all_ok**
- `pytest -q core/scripts/tests/test_session_start_v22.py core/scripts/tests/recovery_test.py core/scripts/tests/error_logger_test.py` → **137 passed**
- `pytest -q tests/integration/test_phase3_e2e.py` → **28 passed** (after fix; previously 7 failed)
- Static scan (non-obsolete `core/scripts`) for `SCRIPT_DIR` + hyphenated `.py` references → **no blockers found**
- Runtime sanity: `python3 core/scripts/session_start.py --skip-context` → **session/memory startup OK**

---

## [v0.3.5-alpha] - 2026-04-20 (Windows test follow-up)

### Fixed

- **CRITICAL UX regression in bootstrap docs**: `core/.context/quick-start.md` still instructed `session-start.py` (hyphen), but runtime script is `session_start.py` (underscore). On Windows test sessions this caused startup failure on first command.
- Updated quick-start bootstrap command to:
  - `python core/scripts/session_start.py`
- Added persistent-preferences reminder to quick-start so new sessions load user preferences from:
  - `core/.context/knowledge/users/default/preferences.md`

### Validation

- Confirmed in tested package logs: SQLite memory **was** being created (`sessions`/`session_messages` increasing), but first-step bootstrap command failed due to stale filename.
- `python -m py_compile core/scripts/pa.py core/scripts/session_start.py` → **OK**
- `python core/scripts/session_start.py --skip-context` and `session_end.py --silent` → **OK**

---

## [v0.3.4-alpha] - 2026-04-19 (Hotfix Memory Persistence)

### Fixed

- **CRITICAL: Memory persistence gap in `pa.py --cli` flow**. Direct CLI mode (`opencode`, `gemini`, `claude`, `codex`) only created a markdown session file and did not initialize SQLite session memory bridge, causing cross-session memory loss in real usage.
- Added best-effort `SessionBridge` lifecycle in `core/scripts/pa.py` for both:
  - direct mode: `pa.py --cli <provider>`
  - menu launch mode
- CLI launch now records at least:
  - initial user prompt (`magic prompt`)
  - CLI launch event metadata
  - explicit session close summary when CLI exits
- **Stability fix**: `pause()` now handles `EOFError` and `KeyboardInterrupt` gracefully for non-interactive shells/tests.

### Validation

- `python -m py_compile core/scripts/pa.py` → **OK**
- `python core/scripts/pa.py --cli codex` in non-interactive shell → no crash on input pause; memory DB receives session records.
- SQLite check confirms new `sessions` and `session_messages` rows generated from CLI launcher flow.

---

## [v0.3.3-alpha] - 2026-04-19

### Fixed

- **CRITICAL: Hidden regressions after hyphen→underscore migration**. Multiple runtime script paths still pointed to non-existent hyphenated files and were being silently ignored by broad `try/except` blocks.
  - `session_start.py`: fixed `session-indexer.py` → `session_indexer.py`
  - `session_end.py`: fixed `session-indexer.py`, `knowledge-miner.py`, `wiki-autopopulate.py`, `kb-updater.py`
  - `learning_cron.py`: fixed `knowledge-miner.py`, `wiki-autopopulate.py`, `kb-updater.py`, `session-saver.py`
  - `install.py`: fixed `sync-context.py`, `kb-init.py`
  - `pa.py`: fixed `sync-context.py` lookup + user-facing error message
  - `session_start.py`: fixed `vitals-guardian.py` references
  - `cron_setup.py`: fixed scheduler targets to underscore filenames
  - `migrate.py`: fixed migration script names to underscore filenames
  - `assembly_line_enforcer.py`: fixed `session-end.py` availability check
- **Windows I/O shutdown handling cleanup**: removed redundant catch-all tuple entries (`..., Exception`) in `session_start.py` shutdown handlers so only expected shutdown errors are swallowed (`ValueError`, `OSError`, `subprocess.TimeoutExpired`).
- **Operational reliability**: session indexing now runs successfully during startup (verified in real execution), instead of failing silently due to wrong script path.

### Validation

- `pytest -q core/scripts/tests/test_session_start_v22.py core/scripts/tests/recovery_test.py` → **96 passed**
- `python core/scripts/session_start.py --skip-context` → **startup OK, indexing OK**
- `python core/scripts/session_end.py --silent` → **session close OK**
- `python -c "from core.memory import SessionStore, SessionContentSQLite; ..."` → **SQLite integrity + repair OK**

---

## [v0.3.1-alpha] - 2026-04-18

### Fixed

- **CRITICAL: SQLite import path on Windows/macOS**: Fixed `session-start.py` and `session_bridge.py` to add `SCRIPT_DIR` to sys.path, enabling SQLite imports regardless of working directory. Fixes "No module named 'sqlite3'" errors caused by incorrect import resolution.
- **CRITICAL: Data persistence location**: Changed from `Path.home()/.pa-framework/` to framework directory `data/`. Added `_get_framework_data_dir()` helper to both `session_memory.py` and `session_bridge.py` for cross-platform compatibility. Users can now simply unzip and run.
- **Clean distribution ZIP**: Created `scripts/build-clean-zip.py` with proper exclusion patterns:
  - Excludes: `__pycache__/`, `*.pyc`, `.git/`, `obsolete/`, `*.db`, `*.log`, `memory/` (root-level legacy), `llm-wiki/content/`, `node_modules/`, `_node_modules_backup/`
  - Preserves: `core/memory/` (code), `core/scripts/`, all essential framework files
- **Fresh install test**: Linux test PASS — SQLite functional, session init 0.2s, no import errors.

### Known Issues (Auditoría 2026-04-18)

- **RESOLVED in v0.3.2-alpha**: Message capture now implemented via `message_hook.py`.
- **Session file empty**: Previously `sessions/YYYY-MM-DD.md` was never written during conversations. Now messages are captured in SQLite via `MessageHook`.

### Roadmap to Fix

- **FASE 1**: ✅ COMPLETE — `message-hook.py` created with real-time capture
- **FASE 2**: Intelligent knowledge extraction from SQLite messages
- **FASE 3**: Resilience (fallback, orphan recovery, integrity validation)

---

## [v0.3.2-alpha] - 2026-04-18 (Late)

### Added

- **message_hook.py** (FASE 1 implementation): Real-time message capture component that was MISSING from architecture.
  - `MessageHook` class: Singleton pattern for session-aware capture
  - `quick_capture()` function: Simple one-line capture for external CLIs
  - CLI interface: `python message_hook.py --capture "user" "message"`
  - Fallback buffer: JSON-based fallback when SQLite unavailable
  - Session stats tracking: Message count, session duration, bridge status
  - Integration options: Python import, shell hook, environment variable, CLI invocation

### Fixed

- **CRITICAL ARCHITECTURAL FLAW RESOLVED**: Messages are now captured during conversations.
  - `SessionBridge.add_message()` is now called by `MessageHook.capture()`
  - Every user/assistant/tool message persists to SQLite in real-time
  - Knowledge extraction can now work with actual session data

---

## [v0.3.0-alpha] - 2026-04-18

### Fixed

- **ERR-20260311-121003**: Added `config/user-settings.json` with default schema to prevent FileNotFoundError on fresh installs. Users can now customize preferences, timezone, and notification settings without creating the file manually.
- **ERR-20260416-234402**: Enhanced logging in `core/recovery/triggers.py` for unclassified errors. Unknown errors now emit debug logs with error type and message context for easier diagnosis.
- **opencode.jsonc**: Reverted to minimal schema-only format (`{"$schema": "https://opencode.ai/config.json"}`). Provider/model configuration is now handled via `opencode auth login` on user's machine, making the framework truly standalone.

### Changed

- **Recovery system**: Improved `detect_error_type()` logging for "unknown" category errors, providing context for debugging.
- **Release package**: Clean ZIP with no provider credentials, ready for distribution.

---

## [Unreleased]

### Added

- **Context Loader** (`core/scripts/context_loader.py` v1.0.0): Lazy tier-based
  context loading with token budget tracking. Implements ADR-001 lazy loading
  strategy across 5 tiers (Tier 0–4). Supports parallel tier loading via
  `ThreadPoolExecutor`. Includes `TokenBudgetTracker` for budget enforcement
  and `@track_tokens` decorator for automatic token/load-time measurement.
- **Knowledge Pattern Detector** (`core/scripts/knowledge-pattern-detector.py`
  v1.0.0): Cross-session pattern analysis for recurring themes, topics, and
  errors. Extracts knowledge items from individual sessions and detects
  patterns across multiple sessions with configurable frequency thresholds.
- **Recovery System** (`core/recovery/`): New self-healing subsystem:
  - `orchestrator.py` v1.0.0: Matches errors to playbooks using ADR-004
    taxonomy, executes recovery actions, and maintains execution history.
    Supports custom action registration via `register_action()`.
  - `triggers.py` v1.0.0: Error classification engine mapping Python
    exceptions to 7 ADR-004 taxonomy categories with keyword fuzzy matching.
    Includes `should_trigger_recovery()` gate logic.
  - `__init__.py`: Package initializer for `core.recovery` module.
- **Recovery Playbook PB-009** (`core/.context/knowledge/playbooks/PB-009-authentication-errors.md`):
  Authentication error recovery playbook for handling 401 Unauthorized, token expiration,
  invalid credentials, and OAuth refresh scenarios. Includes production patterns for
  token refresh, credential validation, and secret management.
- **Test suites** for all new components:
  - `tests/context_loader_test.py`: ContextLoader + TokenBudgetTracker tests
  - `tests/knowledge_pattern_detector_test.py`: PatternDetector tests
  - `tests/recovery_test.py`: RecoveryOrchestrator + triggers tests
  - `tests/test_session_start_v22.py`: Session-start v2.2.0 integration tests
  - `tests/phase4_metrics_test.py`: Phase 4 validation metrics (recovery rate, memory, auth)

### Changed

- **session-start.py** upgraded to v2.2.0: Integrates `ContextLoader` for
  lazy tier-based initialization (ADR-001). Tiers 0–1 load immediately at
  startup; Tiers 2–4 are lazy (deferred). Init time reduced to ~4.58s cold,
  <2s warm.
- **error_logger.py** upgraded to v2.0.0: Adds error classification via
  ADR-004 taxonomy, recovery suggestion generation, playbook triggering
  integration with `RecoveryOrchestrator`, and pattern detection support.
- **knowledge-extractor.py** refactored to v2.0.0: Now uses
  `PatternDetector` from `knowledge-pattern-detector.py` for parsing;
  handles file I/O and orchestration. Dual output (JSON + MD) preserved.

### Performance

- **Initialization time: 92% improvement** — reduced from ~58s (v0.2.x) to
  ~4.58s (v0.3.0-alpha) through lazy tier loading and parallel checks.
- **Context bloat: 85% reduction** — AGENTS-lite.md bootstrap is ~500 tokens
  vs. 20,990 tokens in pre-redesign.
- **231 tests passing**, 1 skipped — comprehensive coverage of all Phase 3
  components + Phase 4 validation.

### Tests

- 231 tests passed, 1 skipped
- New test files for context_loader, pattern_detector, recovery orchestrator,
  session-start v2.2.0 integration, and phase4_metrics
- Coverage improvements across all new modules
- **Phase 4 Validation**: 3/3 metrics PASS (recovery rate 100%, memory 24.3MB, auth playbook ✅)

### Phase 5 (v0.3.0-alpha) — API Stabilization + Knowledge Management

#### Added — API Stabilization (Workstream 1)

- **API Documentation** (`docs/api/`):
  - `README.md` — API index with quick reference
  - `context-loader.md` — Complete ContextLoader API reference
  - `recovery-system.md` — RecoveryOrchestrator + Triggers documentation
  - `knowledge-management.md` — PatternDetector + Extractor docs
- **Integration Tests** (`tests/integration/test_phase3_e2e.py`): 28 E2E tests covering all Phase 3 components
- **API Freezing**: All Phase 3 components frozen at v0.3.0-alpha

#### Added — Knowledge Management (Workstream 2)

- **Session Search** (`core/scripts/session_search.py` v1.0.0):
  - BM25 full-text search algorithm (Python stdlib only)
  - Filters: date, topic, session_type, has_errors, min_word_count
  - Relevance ranking with scores
  - Faceted exploration
  - Performance: <0.5s on 17 sessions
- **Knowledge Export** (`core/scripts/knowledge_export.py` v1.0.0):
  - Export to JSON (with/without content)
  - Export to Markdown (individual or single-file)
  - Export portable format (.pa-export) — ZIP with manifest
  - Date range filtering
- **Knowledge Import** (`core/scripts/knowledge_import.py` v1.0.0):
  - Import from JSON
  - Import from .pa-export portable format
  - Import from Markdown directory
  - Validation with --dry-run
  - Merge/skip-existing options
- **Usage Insights** (`core/scripts/usage_insights.py` v1.0.0):
  - Summary statistics (sessions, words, files, decisions, errors)
  - Activity patterns (by day/week/month)
  - Error pattern detection
  - Topic analysis with trends
  - Productivity metrics
  - Trend analysis (first/second half comparison)
- **Knowledge Management Tests** (`tests/knowledge_management_test.py`): 26 tests, 97% coverage
- **Documentation** (`docs/knowledge-management/README.md`): Complete feature documentation
- **Examples** (`examples/knowledge-management/search_examples.py`): Working usage examples

#### Performance — Phase 5

- **Session search**: <0.5s (4x faster than 2s target)
- **Knowledge export/import**: ~2s for 100 sessions (2.5x faster than 5s target)
- **Usage insights**: <1s for 30d timeframe (3x faster than 3s target)

#### Tests — Phase 5

- **285 tests passed, 1 skipped** (231 Phase 3 + 28 integration + 26 knowledge management)
- **97% coverage** on knowledge management components
- **100% pass rate** on integration tests

---

## [0.2.2-prealpha] - 2026-03-20

### Added

- Public safe-update documentation for end users
- `config/update-protected-paths.txt` exposed in public release for clarity

### Changed

- Version bump to `0.2.2-prealpha` to distribute the update to all users
- `update.py` now guarantees backup + restore + migrations as the official
  update flow

### Fixed

- Backward compatibility of the updater with preservation of context, KB,
  workspaces, and sensitive user configuration
- Refresh of `RELEASE-STAGING` and public release to ensure the updater
  detects the new version

---

## [0.2.1-prealpha] - 2026-03-19

### Added

- `propagate-framework-updates.py` for documenting and propagating
  Framework core stabilization with clean release packaging workflow
- `reference-integrity-check.py` for validating internal references between
  docs, agents, skills, and scripts
- Sub-agents `@skill-finder` for discovery
- `config/update-protected-paths.txt` to preserve user data during updates

### Changed

- `framework-guardian.py` now supports `pre-execution`
- `sync-prealpha.py` hardens sanitization of `PROD` and `RELEASE-STAGING`
- `update.py` now creates backup, restores user state, and executes
  post-update migrations
- Version synchronized to `v0.2.1-prealpha`
- Public documentation updated with safe-update instructions

### Fixed

- Clean session-end in public runtime (`RELEASE-STAGING`) now works even
  when minimal files are missing
- Broken or outdated references between docs, agents, skills, and catalogs
- `DEV` protection to preserve sensitive state without blocking legitimate
  framework improvements
- Staging sanitization to exclude vitals, logs, internal manifests, PRPs,
  and internal documentation

---

## [0.2.0-prealpha] - 2026-03-11

### Added

#### Framework Enforcement System
- **CORE-008 Framework Enforcement**: Mandatory validation system for CORE
  processes
- **framework-guardian.py**: Automatic validation before
  commits/pushes/releases
- Configuration in `config/framework.yaml` with levels (warn/block/log)

#### Knowledge Extraction
- **knowledge-extractor.py**: Automatic extraction of discoveries, prompts,
  ideas
- Detection tags: `#discovery`, `#prompt-success`, `#idea`, `#best-practice`
- Integration with session-end.py for automatic preservation

#### Session Management
- **AGENTS.md**: Added to version tracking
- **session-end.py**: Automatic close via atexit
- **session-start.py**: Optional enforcement verification

### Changed
- **VERSION sync**: Now synchronizes 9 files (including AGENTS.md,
  ROADMAP.md, pa.py)
- **Enforcement timing**: pre-commit, pre-push, pre-release, session-end
- **CHANGELOG.md**: Improved structure with security sections

### Fixed
- VERSION mismatch between commits and files
- AGENTS.md missing in BASE

---

## [0.1.8-prealpha] - 2026-03-11

### Added

#### CORE Processes
- **CORE-005 Structured Execution Loop**: Standard loop for complex tasks
  with stage validation
- **CORE-006 Version Governance**: Automatic framework version management
- **CORE-007 Release Sanitization**: User data protection during updates

#### Skills
- **@error-recovery**: Error recovery system with dual logging (JSON+MD)
- **@skill-evaluator**: Skill quality evaluator (LLM-as-a-Judge)
- **Pattern Analyzer**: Error trend analysis
- **eval-viewer**: HTML viewer for skill evaluations

#### Recovery Playbooks
- PB-001: Encoding errors (UnicodeEncodeError, charmap codec)
- PB-002: File operations (FileNotFoundError, permissions)
- PB-003: JSON parsing (JSONDecodeError, malformed JSON)

#### Tools
- **version-updater.py**: Automatic version sync across 9 files
- **skills-index.json**: Auto-generated index of 23 skills
- **agents-index.json**: Auto-generated index of 6 agents

### Changed
- Dashboard updated with new skills and agents
- `sync-prealpha.py`: Data protection improvements
- Knowledge Base structured with learning/, self-healing/, prompts/

### Fixed
- Version synchronization across all framework files
- Improved first-run session messages

### Security
- Staging validation before push to public repository
- Automatic exclusion of internal development files

---

## [0.1.7-prealpha] - 2026-03-11

### Added
- **Skill-Creator v2**: Enhanced skill creation workflow
  - `@skill-evaluator`: Automated skill quality assessment
  - `eval-viewer`: HTML visualization for skill evaluations
- **@error-recovery**: Antifragile error handling skill
  - Pattern analyzer for error classification and learning
  - Recovery playbooks system for reusable error solutions
- `config/framework.yaml`: Centralized framework configuration

### Fixed
- `sync-prealpha.py`: Branch validation and push improvements
- `session-indexer.py`: KeyError exception on missing session fields
- Various session management edge cases

---

## [0.1.6-prealpha] - 2026-03-10

### Fixed
- **Context Initialization**: Session start error corrected
  - Created `core/.context/codebase/` structure
  - Created `core/.context/knowledge/` structure
  - Script `kb-init.py` for manual KB initialization
- **Knowledge Base**: Functional knowledge storage system
- **Session Start**: Correctly displays available KB

---

## [0.1.5-prealpha] - 2026-03-06

### Fixed
- **docs/dashboard/ structure**: Created in BASE and DEV for consistency
- **dashboard-data.js path**: Corrected to `docs/dashboard/dashboard-data.js`
- **PROD sanitization**: Removed sensitive internal docs
- **VERSION bump**: Versioning correction for automatic updates

---

## [0.1.4-prealpha] - 2026-03-06

### Added
- **Dashboard 2.0**: Functional SPA with embedded data (CORS-free)
- **Knowledge-base System**: Knowledge infrastructure
  - `knowledge-indexer.py`, `interaction-logger.py`,
    `optimization-reporter.py`
- **Custom Commands**: 7 commands (`ideas`, `optimize`, `pa-help`,
  `pa-status`, `pending`, `save`, `session`)
- **Sync System v2**: Extended protections for DEV

### Fixed
- Restoration of critical functionalities damaged by sync
- CORS for offline use (file://)
- Dashboard modals operational

---

## [0.1.3-prealpha] - 2026-03-04

### Added
- **Structured Task Flow v1.0**: Guided 7-step process for complex tasks
- **Automatic complexity detection**: Simple vs Complex vs Critical
- **Express Mode**: Option to skip approval with transparency
- **Dashboard SPA Integration**: Interactive "Workflow" tab

### Changed
- `docs/PHILOSOPHY.md`: Principle #7 "Structured Workflow"
- `core/agents/pa-assistant.md`: Workflow updated to 7 steps

---

## [0.1.2-prealpha] - 2026-03-04

### Added
- **Dynamic Skill Scanning** in `session-start.py`
  - `get_all_skills()`: Dynamic scan of `core/skills/core/`
  - Real skills detected (~22) vs hardcoded (7)

### Fixed
- **Installation loop**: Fallback to create MASTER.md
- `pa.py`: Post-installation verification

---

## [0.1.1-prealpha] - 2026-03-03

### Added
- **macOS/Linux support**: Native `install.sh` for shell
- **Updated skills**: 22 skills documented, 6 new
- User-friendly README with download links

### Fixed
- `opencode.jsonc`: Relative paths, no hardcoded credentials
- Duplicate descriptions corrected in SKILLS.md

---

## [0.1.0-alpha] - 2026-02-11

### Added
- **4 new core skills**: `@skill-creator`, `@markdown-writer`,
  `@csv-processor`, `@python-standards`
- **5 deployed agents**: `@PA-assistant`, `@session-manager`,
  `@context-scout`, `@doc-writer`, `@feature-architect`
- **15 total skills** in production
- **28 validated scripts** cross-platform
- **Sync system** across 3 environments

### Changed
- Emojis replaced by ASCII prefixes for Windows compatibility
- Standardized skill structure

---

## [0.0.x] - Pre-release

### Added
- Base framework structure
- Initial agent configuration
- Local context system (`.context/`)

---

**Full release notes**: [docs/RELEASES/](docs/RELEASES/)

[Unreleased]: https://github.com/n30j0su3/Model-Agnostic-AI-Personal-Assistant-Framework-PreAlpha/compare/v0.2.2-prealpha...HEAD
[0.2.2-prealpha]: https://github.com/n30j0su3/Model-Agnostic-AI-Personal-Assistant-Framework-PreAlpha/compare/v0.2.1-prealpha...v0.2.2-prealpha
[0.2.1-prealpha]: https://github.com/n30j0su3/Model-Agnostic-AI-Personal-Assistant-Framework-PreAlpha/compare/v0.2.0-prealpha...v0.2.1-prealpha
[0.2.0-prealpha]: https://github.com/n30j0su3/Model-Agnostic-AI-Personal-Assistant-Framework-PreAlpha/compare/v0.1.8-prealpha...v0.2.0-prealpha
[0.1.8-prealpha]: https://github.com/n30j0su3/Model-Agnostic-AI-Personal-Assistant-Framework-PreAlpha/compare/v0.1.7-prealpha...v0.1.8-prealpha
[0.1.7-prealpha]: https://github.com/n30j0su3/Model-Agnostic-AI-Personal-Assistant-Framework-PreAlpha/compare/v0.1.6-prealpha...v0.1.7-prealpha
[0.1.6-prealpha]: https://github.com/n30j0su3/Model-Agnostic-AI-Personal-Assistant-Framework-PreAlpha/releases/tag/v0.1.6-prealpha
