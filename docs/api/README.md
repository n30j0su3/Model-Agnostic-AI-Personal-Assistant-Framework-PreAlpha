# PA Framework — API Reference (Phase 3 Frozen APIs)

**Version**: v0.3.7-alpha  
**Status**: APIs FROZEN — No breaking changes allowed  
**Phase**: 5 Workstream 1 — API Stabilization  

---

## Overview

This document provides the complete API reference for all Phase 3 components. These APIs are now **frozen** and will maintain backward compatibility through Phase 4 and beyond.

### Components

| Component | Module | Version | Status |
|-----------|--------|---------|--------|
| ContextLoader | `core/scripts/context_loader.py` | v1.0.0 | ✅ Frozen |
| RecoveryOrchestrator | `core/recovery/orchestrator.py` | v1.0.0 | ✅ Frozen |
| RecoveryTriggers | `core/recovery/triggers.py` | v1.0.0 | ✅ Frozen |
| KnowledgePatternDetector | `core/scripts/knowledge-pattern-detector.py` | v1.0.0 | ✅ Frozen |
| KnowledgeExtractor | `core/scripts/knowledge-extractor.py` | v2.0.0 | ✅ Frozen |
| ErrorLogger v2 | `core/scripts/error_logger.py` | v2.0.0 | ✅ Frozen |

---

## Documentation Index

### Core Components

- **[ContextLoader API](context-loader.md)** — Tier-based lazy context loading
- **[Recovery System API](recovery-system.md)** — Error recovery orchestration and triggers
- **[Knowledge Management API](knowledge-management.md)** — Pattern detection and extraction

---

## Quick Reference

### ContextLoader

```python
from context_loader import ContextLoader, TokenBudgetTracker

loader = ContextLoader()
bootstrap = loader.load_tier(0)  # Tier 0: Bootstrap
config = loader.load_tier(1)     # Tier 1: Essential
context = loader.load_tier(2)    # Tier 2: Context (lazy)
```

### RecoveryOrchestrator

```python
from recovery.orchestrator import RecoveryOrchestrator

orchestrator = RecoveryOrchestrator()
playbook_id = orchestrator.match_playbook(error)
result = orchestrator.execute_playbook(playbook_id, context)
# Or end-to-end:
result = orchestrator.recover(error, context)
```

### ErrorLogger

```python
from error_logger import ErrorLogger

logger = ErrorLogger()
error_id = logger.log_error({
    "type": "FileNotFoundError",
    "message": "config.json not found",
    "file": "app.py",
    "line": 42
})
category = logger.classify_error(error_dict)
recovery = logger.suggest_recovery("network")
```

### KnowledgeExtractor

```python
from knowledge_extractor import KnowledgeExtractor

extractor = KnowledgeExtractor()
results = extractor.extract_all_knowledge(session_file)
# Returns: {discoveries: N, prompts: N, ideas: N, best_practices: N, success: bool}
```

### KnowledgePatternDetector

```python
from knowledge_pattern_detector import PatternDetector, SessionContent

detector = PatternDetector()
patterns = detector.analyze_sessions(session_paths)
# Returns list of Pattern dicts with pattern_type, description, frequency, sessions
```

---

## Type Safety

All Phase 3 components use Python 3.11+ type hints. Validate with:

```bash
mypy --strict core/scripts/context_loader.py
mypy --strict core/recovery/orchestrator.py
mypy --strict core/scripts/error_logger.py
mypy --strict core/scripts/knowledge-extractor.py
mypy --strict core/scripts/knowledge-pattern-detector.py
```

---

## Testing

Integration tests are located in `tests/integration/`:

```bash
pytest tests/integration/ -v --cov=core/scripts --cov=core/recovery
```

### Test Coverage Requirements

- **Minimum**: 90% coverage on Phase 3 components
- **Type checking**: 100% mypy --strict pass
- **E2E tests**: All integration tests passing

---

## API Stability Guarantee

Phase 3 APIs are **frozen** as of v0.3.0-alpha:

- ✅ No breaking changes to public method signatures
- ✅ No removal of public classes or functions
- ✅ Backward compatibility maintained
- ✅ New features added via extension, not modification

### Change Protocol

Any changes to frozen APIs require:

1. Phase lead approval (Morpheus)
2. Security review (Seraph)
3. QA validation (Dozer)
4. Version bump to next minor version

---

## Related Documentation

- [AGENTS-full.md](../AGENTS-full.md) — Full framework documentation
- [CHANGELOG.md](../../CHANGELOG.md) — Version history
- [ROADMAP.md](../../ROADMAP.md) — Development roadmap

---

*Last updated: April 17, 2026*  
*Phase 5 Workstream 1 — API Stabilization*
