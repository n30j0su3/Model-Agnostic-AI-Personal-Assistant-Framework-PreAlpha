#!/usr/bin/env python3
"""
Tests for Knowledge Pattern Detector and Knowledge Extractor.

Covers:
- PatternDetector: single-session extraction (discoveries, prompts, ideas, best practices)
- PatternDetector: cross-session analysis (analyze_sessions)
- KnowledgeExtractor: config loading, file I/O, extract_all_knowledge
- SessionContent: lazy loading
"""

import importlib
import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

# Ensure the scripts directory is importable
SCRIPTS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS_DIR))

_kpd = importlib.import_module("knowledge_pattern_detector")
PatternDetector = _kpd.PatternDetector
SessionContent = _kpd.SessionContent
lazy_load = _kpd.lazy_load
TAGS = _kpd.TAGS


# =====================================================================
# Fixtures
# =====================================================================

@pytest.fixture
def tmp_dir(tmp_path):
    """Provide a temp directory for test files."""
    return tmp_path


@pytest.fixture
def sample_session(tmp_path):
    """Create a sample session file with all knowledge types."""
    content = """\
# Session 2026-04-15

## Inicio

**Hora**: 10:00

## Hallazgos

- Descubrimiento: El nuevo patron de error handling funciona mejor
- El modulo de extraction puede ser reutilizado #discovery

## Solucion

Se resolvio el problema de encoding usando:

```python
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
```

Esto funciono correctamente. [OK]

## Ideas

- [x] Implementar nuevo modulo de extraction
- [ ] Agregar soporte para YAML

## Prompt Exitoso

#prompt-success

```python
def extract_patterns(text):
    return re.findall(r'pattern', text)
```

Exitoso - funciono perfectamente.

---

## Best Practice

Usar siempre `encoding='utf-8'` al leer archivos en Windows #best-practice
"""
    sf = tmp_path / "session_2026-04-15.md"
    sf.write_text(content, encoding="utf-8")
    return sf


@pytest.fixture
def sample_session_2(tmp_path):
    """Second session file for cross-session tests."""
    content = """\
# Session 2026-04-16

## Hallazgos

- Descubrimiento: El patron de error handling es consistente
- Nueva tecnica de refactoring #discovery

## Solucion

Refactor del modulo principal:

```bash
git rebase -i HEAD~5
```

funciono correctamente

## Ideas

- [x] Usar pattern detector para cross-session
- [x] Implementar lazy loading de sesiones
"""
    sf = tmp_path / "session_2026-04-16.md"
    sf.write_text(content, encoding="utf-8")
    return sf


@pytest.fixture
def detector():
    """Provide a PatternDetector instance with default config."""
    return PatternDetector()


@pytest.fixture
def extractor(tmp_path, monkeypatch):
    """Provide a KnowledgeExtractor writing to temp directory."""
    _ke = importlib.import_module("knowledge_extractor")
    KnowledgeExtractor = _ke.KnowledgeExtractor
    output_cfg = {
        "discoveries": str(tmp_path / "discoveries.md"),
        "prompts": str(tmp_path / "prompts.json"),
        "ideas": str(tmp_path / "ideas.md"),
        "best_practices": str(tmp_path / "best_practices.md"),
        "index": str(tmp_path / "index.json"),
    }
    # Patch REPO_ROOT so paths resolve to tmp_path
    monkeypatch.setattr(_ke, "REPO_ROOT", tmp_path)
    config = {"output": {k: str(v) for k, v in output_cfg.items()}}
    return KnowledgeExtractor(config=config)


# =====================================================================
# Tests: SessionContent lazy loading
# =====================================================================

class TestSessionContent:
    def test_lazy_raw(self, sample_session):
        sc = SessionContent(sample_session)
        assert sc._raw is None
        _ = sc.raw
        assert sc._raw is not None
        assert "Session" in sc.raw

    def test_lazy_lines(self, sample_session):
        sc = SessionContent(sample_session)
        assert sc._lines is None
        lines = sc.lines
        assert isinstance(lines, list)
        assert len(lines) > 0

    def test_cached_lines(self, sample_session):
        sc = SessionContent(sample_session)
        lines1 = sc.lines
        lines2 = sc.lines
        assert lines1 is lines2  # same object, cached

    def test_invalidate(self, sample_session):
        sc = SessionContent(sample_session)
        _ = sc.raw
        sc.invalidate()
        assert sc._raw is None
        assert sc._lines is None

    def test_name(self, sample_session):
        sc = SessionContent(sample_session)
        assert sc.name == sample_session.name


# =====================================================================
# Tests: lazy_load decorator
# =====================================================================

class TestLazyLoadDecorator:
    def test_caches_result(self):
        call_count = 0

        class Obj:
            @lazy_load("data")
            def get_data(self):
                nonlocal call_count
                call_count += 1
                return [1, 2, 3]

        o = Obj()
        result1 = o.get_data()
        result2 = o.get_data()
        assert result1 == [1, 2, 3]
        assert call_count == 1  # called only once
        assert result1 is result2


# =====================================================================
# Tests: PatternDetector - single-session extraction
# =====================================================================

class TestPatternDetectorDiscoveries:
    def test_extracts_tagged_discovery(self, detector, sample_session):
        sc = SessionContent(sample_session)
        results = detector.extract_discoveries(sc)
        tagged = [d for d in results if not d["auto_detected"]]
        assert len(tagged) >= 1
        assert any("reutilizado" in d.get("title", d.get("discovery", "")) for d in tagged)

    def test_extracts_section_discoveries(self, detector, sample_session):
        sc = SessionContent(sample_session)
        results = detector.extract_discoveries(sc)
        auto = [d for d in results if d["auto_detected"]]
        assert len(auto) >= 1

    def test_extracts_inline_discovery(self, detector, sample_session):
        sc = SessionContent(sample_session)
        results = detector.extract_discoveries(sc)
        inline = [d for d in results if "inline" in d.get("context", "").lower()]
        assert len(inline) >= 1

    def test_empty_file(self, detector, tmp_path):
        sf = tmp_path / "empty.md"
        sf.write_text("# Empty\n", encoding="utf-8")
        results = detector.extract_discoveries(SessionContent(sf))
        assert results == []

    def test_discovery_has_required_fields(self, detector, sample_session):
        sc = SessionContent(sample_session)
        results = detector.extract_discoveries(sc)
        for d in results:
            assert "title" in d
            assert "extracted_from" in d
            assert "auto_detected" in d
            assert "timestamp" in d


class TestPatternDetectorPrompts:
    def test_extracts_code_block_prompt(self, detector, sample_session):
        sc = SessionContent(sample_session)
        results = detector.extract_prompts(sc)
        assert len(results) >= 1
        assert any(r["auto_detected"] for r in results)

    def test_extracts_tagged_prompt(self, detector, sample_session):
        sc = SessionContent(sample_session)
        results = detector.extract_prompts(sc)
        tagged = [r for r in results if not r["auto_detected"]]
        assert len(tagged) >= 1

    def test_prompt_has_id(self, detector, sample_session):
        sc = SessionContent(sample_session)
        results = detector.extract_prompts(sc)
        for r in results:
            assert "id" in r
            assert r["id"].startswith("PROMPT-")

    def test_prompt_categorization(self, detector, sample_session):
        sc = SessionContent(sample_session)
        results = detector.extract_prompts(sc)
        cats = {r["category"] for r in results}
        assert "python" in cats


class TestPatternDetectorIdeas:
    def test_extracts_tagged_ideas(self, detector, sample_session):
        sc = SessionContent(sample_session)
        results = detector.extract_ideas(sc)
        assert len(results) >= 1

    def test_extracts_checked_ideas(self, detector, sample_session):
        sc = SessionContent(sample_session)
        results = detector.extract_ideas(sc)
        checked = [r for r in results if r.get("status") == "validated"]
        assert len(checked) >= 1

    def test_idea_priority(self, detector, sample_session):
        sc = SessionContent(sample_session)
        results = detector.extract_ideas(sc)
        priorities = {r.get("priority") for r in results}
        assert priorities.issubset({"low", "medium", "high"})


class TestPatternDetectorBestPractices:
    def test_extracts_tagged_practice(self, detector, sample_session):
        sc = SessionContent(sample_session)
        results = detector.extract_best_practices(sc)
        tagged = [r for r in results if not r["auto_detected"]]
        assert len(tagged) >= 1

    def test_extracts_solution_section(self, detector, sample_session):
        sc = SessionContent(sample_session)
        results = detector.extract_best_practices(sc)
        assert len(results) >= 1

    def test_practice_has_benefit(self, detector, sample_session):
        sc = SessionContent(sample_session)
        results = detector.extract_best_practices(sc)
        for r in results:
            assert "benefit" in r

    def test_skips_empty_code_solution(self, detector, tmp_path):
        sf = tmp_path / "empty_code_solution.md"
        sf.write_text(
            "# Session\n\n```python\n```\nThis worked\n",
            encoding="utf-8",
        )
        results = detector.extract_best_practices(SessionContent(sf))
        assert results == []


# =====================================================================
# Tests: PatternDetector - cross-session analysis
# =====================================================================

class TestPatternDetectorCrossSession:
    def test_analyze_sessions_returns_patterns(self, detector, sample_session, sample_session_2):
        patterns = detector.analyze_sessions([sample_session, sample_session_2])
        assert isinstance(patterns, list)
        assert len(patterns) > 0

    def test_pattern_structure(self, detector, sample_session, sample_session_2):
        patterns = detector.analyze_sessions([sample_session, sample_session_2])
        for p in patterns:
            assert "pattern_type" in p
            assert "description" in p
            assert "frequency" in p
            assert "sessions" in p

    def test_recurring_theme_detected(self, detector, sample_session, sample_session_2):
        patterns = detector.analyze_sessions([sample_session, sample_session_2])
        # Cross-session analysis should detect recurring patterns
        # Both sessions mention "error handling" and "patron" — any pattern type counts
        assert len(patterns) >= 1, f"Expected ≥1 pattern, got {len(patterns)}: {patterns}"

    def test_empty_sessions_list(self, detector):
        patterns = detector.analyze_sessions([])
        assert patterns == []

    def test_nonexistent_files_skipped(self, detector, tmp_path):
        fake = tmp_path / "nonexistent.md"
        patterns = detector.analyze_sessions([fake])
        assert patterns == []

    def test_single_session_analysis(self, detector, sample_session):
        patterns = detector.analyze_sessions([sample_session])
        assert isinstance(patterns, list)

    def test_prompt_category_pattern(self, detector, sample_session, sample_session_2):
        patterns = detector.analyze_sessions([sample_session, sample_session_2])
        cat_patterns = [p for p in patterns if p["pattern_type"] == "prompt_category"]
        assert len(cat_patterns) >= 1

    def test_sorted_by_frequency(self, detector, sample_session, sample_session_2):
        patterns = detector.analyze_sessions([sample_session, sample_session_2])
        freqs = [p["frequency"] for p in patterns]
        assert freqs == sorted(freqs, reverse=True)


# =====================================================================
# Tests: KnowledgeExtractor (refactored)
# =====================================================================

class TestKnowledgeExtractor:
    def test_init_creates_files(self, extractor, tmp_path):
        assert (tmp_path / "discoveries.md").exists()
        assert (tmp_path / "prompts.json").exists()
        assert (tmp_path / "ideas.md").exists()
        assert (tmp_path / "best_practices.md").exists()
        assert (tmp_path / "index.json").exists()

    def test_extract_all_knowledge(self, extractor, sample_session):
        results = extractor.extract_all_knowledge(sample_session)
        assert results["success"] is True
        assert results["discoveries"] >= 1
        assert results["prompts"] >= 1
        assert results["ideas"] >= 1
        assert results["best_practices"] >= 1

    def test_extract_updates_index(self, extractor, sample_session):
        extractor.extract_all_knowledge(sample_session)
        idx = extractor._read_json(extractor.index_file)
        assert idx["discoveries"] >= 1
        assert idx["last_extraction"] is not None
        assert len(idx["history"]) == 1

    def test_extract_updates_discoveries_md(self, extractor, sample_session):
        extractor.extract_all_knowledge(sample_session)
        content = extractor.discoveries_file.read_text(encoding="utf-8")
        assert "PENDIENTE VALIDACION" in content

    def test_extract_updates_prompts_json(self, extractor, sample_session):
        extractor.extract_all_knowledge(sample_session)
        data = json.loads(extractor.prompts_file.read_text(encoding="utf-8"))
        assert len(data["prompts"]) >= 1

    def test_disabled_extraction(self, extractor, sample_session):
        extractor.config["enabled"] = False
        results = extractor.extract_all_knowledge(sample_session)
        assert results["success"] is False
        assert results["message"] == "Knowledge extraction disabled"

    def test_empty_session(self, extractor, tmp_path):
        sf = tmp_path / "empty_session.md"
        sf.write_text("# Empty\nNothing here.\n", encoding="utf-8")
        results = extractor.extract_all_knowledge(sf)
        assert results["success"] is True
        assert results["discoveries"] == 0

    def test_extract_all_knowledge_skips_empty_code_solution(self, extractor, tmp_path):
        sf = tmp_path / "empty_code_solution.md"
        sf.write_text(
            "# Session\n\n```python\n```\nThis worked\n",
            encoding="utf-8",
        )
        results = extractor.extract_all_knowledge(sf)
        assert results["success"] is True
        assert results["best_practices"] == 0

    def test_convenience_functions(self, sample_session, tmp_path, monkeypatch):
        """Test module-level convenience functions still work."""
        _ke = importlib.import_module("knowledge_extractor")
        monkeypatch.setattr(_ke, "REPO_ROOT", tmp_path)
        # Just verify it doesn't crash - it creates a fresh extractor
        results = _ke.extract_session_discoveries(sample_session)
        assert isinstance(results, list)

    def test_paths_properties(self, extractor, tmp_path):
        assert extractor.discoveries_file == tmp_path / "discoveries.md"
        assert extractor.prompts_file == tmp_path / "prompts.json"
        assert extractor.ideas_file == tmp_path / "ideas.md"
        assert extractor.best_practices_file == tmp_path / "best_practices.md"
        assert extractor.index_file == tmp_path / "index.json"

    def test_multiple_extractions_accumulate(self, extractor, sample_session, sample_session_2):
        extractor.extract_all_knowledge(sample_session)
        extractor.extract_all_knowledge(sample_session_2)
        idx = extractor._read_json(extractor.index_file)
        assert len(idx["history"]) == 2
        assert idx["discoveries"] >= 2

    def test_prompt_dedup(self, extractor, sample_session):
        """Running same session twice shouldn't duplicate prompts in registry."""
        extractor.extract_all_knowledge(sample_session)
        extractor.extract_all_knowledge(sample_session)
        data = json.loads(extractor.prompts_file.read_text(encoding="utf-8"))
        ids = [p["id"] for p in data["prompts"]]
        assert len(ids) == len(set(ids)), "Duplicate prompt IDs found"


# =====================================================================
# Tests: Categorization
# =====================================================================

class TestCategorization:
    def test_python(self):
        assert PatternDetector._categorize("def foo():\n    import bar") == "python"

    def test_bash(self):
        assert PatternDetector._categorize("git commit -m 'test'") == "bash"

    def test_javascript(self):
        assert PatternDetector._categorize("const x = function() {}") == "javascript"

    def test_sql(self):
        assert PatternDetector._categorize("SELECT * FROM table") == "sql"

    def test_config(self):
        assert PatternDetector._categorize("yaml or json config") == "config"

    def test_general(self):
        assert PatternDetector._categorize("some random text") == "general"
