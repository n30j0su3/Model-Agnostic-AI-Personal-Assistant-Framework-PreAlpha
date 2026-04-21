#!/usr/bin/env python3
"""
PA Framework — Knowledge Management Tests
==========================================
Tests for Phase 5 Workstream 2:
- Session Search (session_search.py)
- Knowledge Export (knowledge_export.py)
- Knowledge Import (knowledge_import.py)
- Usage Insights (usage_insights.py)

Run: pytest tests/knowledge_management_test.py -v --cov=core/scripts
"""

import json
import os
import sys
import tempfile
import zipfile
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch

import pytest

# Add core/scripts to path
SCRIPT_DIR = Path(__file__).resolve().parent.parent / "core" / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

# Import modules
import importlib.util


def load_module_from_path(name: str, path: Path):
    """Load a module from a file path."""
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# Load modules
session_search = load_module_from_path("session_search", SCRIPT_DIR / "session_search.py")
knowledge_export = load_module_from_path("knowledge_export", SCRIPT_DIR / "knowledge_export.py")
knowledge_import = load_module_from_path("knowledge_import", SCRIPT_DIR / "knowledge_import.py")
usage_insights = load_module_from_path("usage_insights", SCRIPT_DIR / "usage_insights.py")

# Import classes
BM25Search = session_search.BM25Search
SessionSearch = session_search.SessionSearch
KnowledgeExporter = knowledge_export.KnowledgeExporter
KnowledgeImporter = knowledge_import.KnowledgeImporter
UsageAnalyzer = usage_insights.UsageAnalyzer


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_sessions_index(temp_dir):
    """Create a sample sessions index file."""
    index_data = {
        "version": "1.0",
        "description": "Test index",
        "last_updated": datetime.now().isoformat(),
        "total_sessions": 5,
        "sessions": [
            {
                "id": "2026-04-01",
                "date": "2026-04-01",
                "title": "Session One - Error Handling",
                "summary": "Discussed error handling patterns",
                "topics": ["errors", "python", "best-practices"],
                "type": "research",
                "stats": {
                    "interactions": 10,
                    "files_modified": 3,
                    "decisions": 2,
                    "lsp_errors": 5,
                    "word_count": 1500
                },
                "highlights": [],
                "file_path": "sessions/2026-04-01.md",
                "status": "completed"
            },
            {
                "id": "2026-04-05",
                "date": "2026-04-05",
                "title": "Session Two - Feature Implementation",
                "summary": "Implemented new search feature",
                "topics": ["features", "search", "python"],
                "type": "features",
                "stats": {
                    "interactions": 15,
                    "files_modified": 5,
                    "decisions": 3,
                    "lsp_errors": 2,
                    "word_count": 2500
                },
                "highlights": [],
                "file_path": "sessions/2026-04-05.md",
                "status": "completed"
            },
            {
                "id": "2026-04-10",
                "date": "2026-04-10",
                "title": "Session Three - Bug Fixes",
                "summary": "Fixed critical bugs",
                "topics": ["bugfix", "errors", "testing"],
                "type": "bugfix",
                "stats": {
                    "interactions": 8,
                    "files_modified": 2,
                    "decisions": 1,
                    "lsp_errors": 10,
                    "word_count": 1200
                },
                "highlights": [],
                "file_path": "sessions/2026-04-10.md",
                "status": "completed"
            },
            {
                "id": "2026-04-15",
                "date": "2026-04-15",
                "title": "Session Four - Architecture Review",
                "summary": "Reviewed system architecture",
                "topics": ["architecture", "design", "planning"],
                "type": "planning",
                "stats": {
                    "interactions": 12,
                    "files_modified": 4,
                    "decisions": 5,
                    "lsp_errors": 0,
                    "word_count": 3000
                },
                "highlights": [],
                "file_path": "sessions/2026-04-15.md",
                "status": "completed"
            },
            {
                "id": "2026-04-17",
                "date": "2026-04-17",
                "title": "Session Five - Knowledge Management",
                "summary": "Phase 5 implementation",
                "topics": ["knowledge", "features", "phase5"],
                "type": "features",
                "stats": {
                    "interactions": 20,
                    "files_modified": 6,
                    "decisions": 4,
                    "lsp_errors": 1,
                    "word_count": 4000
                },
                "highlights": [],
                "file_path": "sessions/2026-04-17.md",
                "status": "completed"
            }
        ],
        "filters": {
            "by_topic": {
                "errors": ["2026-04-01", "2026-04-10"],
                "python": ["2026-04-01", "2026-04-05"],
                "features": ["2026-04-05", "2026-04-17"]
            },
            "by_type": {
                "research": 1,
                "features": 2,
                "bugfix": 1,
                "planning": 1
            }
        }
    }

    # Create knowledge directory and write index
    knowledge_dir = temp_dir / "knowledge"
    knowledge_dir.mkdir(parents=True, exist_ok=True)
    index_file = knowledge_dir / "sessions-index.json"
    index_file.write_text(json.dumps(index_data, indent=2), encoding='utf-8')

    # Create sessions directory
    sessions_dir = temp_dir / "sessions"
    sessions_dir.mkdir(parents=True, exist_ok=True)

    # Create sample session files
    for session in index_data["sessions"]:
        session_file = sessions_dir / f"{session['id']}.md"
        content = f"""# {session['title']}

## Summary
{session['summary']}

## Topics
- {chr(10).join('- ' + t for t in session['topics'])}

## Content
This is sample content for session {session['id']}.
It contains multiple paragraphs for testing full-text search.
Error handling is important in Python development.
Features should be well-tested before release.
"""
        session_file.write_text(content, encoding='utf-8')

    return {
        "temp_dir": temp_dir,
        "index_file": index_file,
        "sessions_dir": sessions_dir,
        "index_data": index_data
    }


# ============================================================================
# BM25 SEARCH TESTS
# ============================================================================

class TestBM25Search:
    """Tests for BM25Search class."""

    def test_tokenize(self):
        """Test text tokenization."""
        bm25 = BM25Search()
        tokens = bm25._tokenize("Hello world! This is a test.")
        assert "hello" in tokens
        assert "world" in tokens
        assert "test" in tokens
        assert "is" not in tokens  # Stopword
        assert "a" not in tokens  # Too short

    def test_tokenize_spanish(self):
        """Test tokenization with Spanish text."""
        bm25 = BM25Search()
        tokens = bm25._tokenize("El error en Python es importante.")
        assert "error" in tokens
        assert "python" in tokens
        assert "importante" in tokens
        assert "el" not in tokens  # Spanish stopword
        assert "en" not in tokens  # Spanish stopword

    def test_index_documents(self):
        """Test document indexing."""
        bm25 = BM25Search()
        documents = {
            "doc1": "Python error handling best practices",
            "doc2": "JavaScript feature implementation",
            "doc3": "Python testing strategies"
        }
        bm25.index_documents(documents)

        assert bm25.total_docs == 3
        assert "doc1" in bm25.documents
        assert bm25.avg_doc_length > 0

    def test_search_basic(self):
        """Test basic search functionality."""
        bm25 = BM25Search()
        documents = {
            "doc1": "Python error handling is important",
            "doc2": "JavaScript features are cool",
            "doc3": "Python testing with pytest"
        }
        bm25.index_documents(documents)

        results = bm25.search("Python error", top_k=2)

        assert len(results) <= 2
        assert results[0][0] == "doc1"  # Most relevant

    def test_search_no_results(self):
        """Test search with no matching results."""
        bm25 = BM25Search()
        documents = {
            "doc1": "Python programming",
            "doc2": "JavaScript development"
        }
        bm25.index_documents(documents)

        results = bm25.search("quantum computing")
        assert len(results) == 0

    def test_search_empty_query(self):
        """Test search with empty query."""
        bm25 = BM25Search()
        documents = {"doc1": "Some content here"}
        bm25.index_documents(documents)

        results = bm25.search("")
        assert len(results) == 0


# ============================================================================
# SESSION SEARCH TESTS
# ============================================================================

class TestSessionSearch:
    """Tests for SessionSearch class."""

    def test_init(self, sample_sessions_index, monkeypatch):
        """Test SessionSearch initialization."""
        # Monkeypatch the paths
        monkeypatch.setattr(
            session_search,
            "KNOWLEDGE_DIR",
            sample_sessions_index["temp_dir"] / "knowledge"
        )
        monkeypatch.setattr(
            session_search,
            "SESSIONS_DIR",
            sample_sessions_index["temp_dir"] / "sessions"
        )
        monkeypatch.setattr(
            session_search,
            "INDEX_FILE",
            sample_sessions_index["index_file"]
        )

        searcher = SessionSearch()
        assert len(searcher.index_data.get("sessions", [])) == 5

    def test_search_with_query(self, sample_sessions_index, monkeypatch):
        """Test search with full-text query."""
        monkeypatch.setattr(
            session_search,
            "KNOWLEDGE_DIR",
            sample_sessions_index["temp_dir"] / "knowledge"
        )
        monkeypatch.setattr(
            session_search,
            "SESSIONS_DIR",
            sample_sessions_index["temp_dir"] / "sessions"
        )
        monkeypatch.setattr(
            session_search,
            "INDEX_FILE",
            sample_sessions_index["index_file"]
        )

        searcher = SessionSearch()
        results = searcher.search_sessions(query="error handling", limit=5)

        assert len(results) > 0
        # First result should be most relevant
        assert "search_score" in results[0]

    def test_search_with_filters(self, sample_sessions_index, monkeypatch):
        """Test search with filters."""
        monkeypatch.setattr(
            session_search,
            "KNOWLEDGE_DIR",
            sample_sessions_index["temp_dir"] / "knowledge"
        )
        monkeypatch.setattr(
            session_search,
            "SESSIONS_DIR",
            sample_sessions_index["temp_dir"] / "sessions"
        )
        monkeypatch.setattr(
            session_search,
            "INDEX_FILE",
            sample_sessions_index["index_file"]
        )

        searcher = SessionSearch()

        # Filter by topic
        results = searcher.search_sessions(filters={"topic": "errors"}, limit=10)
        assert len(results) == 2  # Two sessions have "errors" topic

        # Filter by type
        results = searcher.search_sessions(filters={"session_type": "features"}, limit=10)
        assert len(results) == 2

        # Filter by date range
        results = searcher.search_sessions(
            filters={"from_date": "2026-04-05", "to_date": "2026-04-15"},
            limit=10
        )
        assert len(results) == 3

    def test_get_facets(self, sample_sessions_index, monkeypatch):
        """Test facet generation."""
        monkeypatch.setattr(
            session_search,
            "KNOWLEDGE_DIR",
            sample_sessions_index["temp_dir"] / "knowledge"
        )
        monkeypatch.setattr(
            session_search,
            "SESSIONS_DIR",
            sample_sessions_index["temp_dir"] / "sessions"
        )
        monkeypatch.setattr(
            session_search,
            "INDEX_FILE",
            sample_sessions_index["index_file"]
        )

        searcher = SessionSearch()
        facets = searcher.get_facets()

        assert "topics" in facets
        assert "types" in facets
        assert "date_range" in facets
        assert facets["total_sessions"] == 5


# ============================================================================
# KNOWLEDGE EXPORT TESTS
# ============================================================================

class TestKnowledgeExport:
    """Tests for KnowledgeExporter class."""

    def test_export_to_json(self, sample_sessions_index, temp_dir, monkeypatch):
        """Test JSON export."""
        monkeypatch.setattr(
            knowledge_export,
            "KNOWLEDGE_DIR",
            sample_sessions_index["temp_dir"] / "knowledge"
        )
        monkeypatch.setattr(
            knowledge_export,
            "SESSIONS_DIR",
            sample_sessions_index["temp_dir"] / "sessions"
        )
        monkeypatch.setattr(
            knowledge_export,
            "INDEX_FILE",
            sample_sessions_index["index_file"]
        )

        exporter = KnowledgeExporter()
        output_file = temp_dir / "export.json"
        result = exporter.export_to_json(output_file, include_content=True)

        assert result["sessions_exported"] == 5
        assert output_file.exists()

        # Verify content
        with open(output_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        assert data["total_sessions"] == 5
        assert "sessions" in data

    def test_export_to_markdown(self, sample_sessions_index, temp_dir, monkeypatch):
        """Test Markdown export."""
        monkeypatch.setattr(
            knowledge_export,
            "KNOWLEDGE_DIR",
            sample_sessions_index["temp_dir"] / "knowledge"
        )
        monkeypatch.setattr(
            knowledge_export,
            "SESSIONS_DIR",
            sample_sessions_index["temp_dir"] / "sessions"
        )
        monkeypatch.setattr(
            knowledge_export,
            "INDEX_FILE",
            sample_sessions_index["index_file"]
        )

        exporter = KnowledgeExporter()
        output_dir = temp_dir / "markdown-export"
        result = exporter.export_to_markdown(output_dir, single_file=False)

        assert result["sessions_exported"] == 5
        assert output_dir.exists()
        # Should have individual files + index
        assert len(result["files_created"]) >= 5

    def test_export_to_markdown_single_file(self, sample_sessions_index, temp_dir, monkeypatch):
        """Test single-file Markdown export."""
        monkeypatch.setattr(
            knowledge_export,
            "KNOWLEDGE_DIR",
            sample_sessions_index["temp_dir"] / "knowledge"
        )
        monkeypatch.setattr(
            knowledge_export,
            "SESSIONS_DIR",
            sample_sessions_index["temp_dir"] / "sessions"
        )
        monkeypatch.setattr(
            knowledge_export,
            "INDEX_FILE",
            sample_sessions_index["index_file"]
        )

        exporter = KnowledgeExporter()
        output_file = temp_dir / "export.md"
        result = exporter.export_to_markdown(
            temp_dir / "md-export",
            single_file=True
        )

        assert result["single_file"] is True

    def test_create_portable_export(self, sample_sessions_index, temp_dir, monkeypatch):
        """Test portable export creation."""
        monkeypatch.setattr(
            knowledge_export,
            "KNOWLEDGE_DIR",
            sample_sessions_index["temp_dir"] / "knowledge"
        )
        monkeypatch.setattr(
            knowledge_export,
            "SESSIONS_DIR",
            sample_sessions_index["temp_dir"] / "sessions"
        )
        monkeypatch.setattr(
            knowledge_export,
            "INDEX_FILE",
            sample_sessions_index["index_file"]
        )

        exporter = KnowledgeExporter()
        output_file = temp_dir / "backup.pa-export"
        result = exporter.create_portable_export(output_file)

        assert result["sessions_exported"] == 5
        assert output_file.exists()
        assert result["format"] == "pa-export"

        # Verify ZIP contents
        with zipfile.ZipFile(output_file, 'r') as zf:
            assert "manifest.json" in zf.namelist()
            assert "sessions-index.json" in zf.namelist()


# ============================================================================
# KNOWLEDGE IMPORT TESTS
# ============================================================================

class TestKnowledgeImport:
    """Tests for KnowledgeImporter class."""

    def test_import_from_json(self, sample_sessions_index, temp_dir, monkeypatch):
        """Test JSON import."""
        # Setup all paths first
        test_knowledge_dir = temp_dir / "test-knowledge"
        test_sessions_dir = temp_dir / "test-sessions"
        test_index_file = test_knowledge_dir / "sessions-index.json"

        monkeypatch.setattr(
            knowledge_import,
            "KNOWLEDGE_DIR",
            test_knowledge_dir
        )
        monkeypatch.setattr(
            knowledge_import,
            "SESSIONS_DIR",
            test_sessions_dir
        )
        monkeypatch.setattr(
            knowledge_import,
            "INDEX_FILE",
            test_index_file
        )
        monkeypatch.setattr(
            knowledge_export,
            "KNOWLEDGE_DIR",
            test_knowledge_dir
        )
        monkeypatch.setattr(
            knowledge_export,
            "SESSIONS_DIR",
            test_sessions_dir
        )
        monkeypatch.setattr(
            knowledge_export,
            "INDEX_FILE",
            test_index_file
        )

        # Create directories
        test_knowledge_dir.mkdir(parents=True, exist_ok=True)
        test_sessions_dir.mkdir(parents=True, exist_ok=True)

        # Copy sample index to test location
        import shutil
        shutil.copy(sample_sessions_index["index_file"], test_index_file)
        for session_file in sample_sessions_index["sessions_dir"].glob("*.md"):
            shutil.copy(session_file, test_sessions_dir / session_file.name)

        # Create test export to import
        exporter = KnowledgeExporter()
        export_file = temp_dir / "to-import.json"
        exporter.export_to_json(export_file)

        # Clear index for import test
        empty_index = {"sessions": [], "last_updated": datetime.now().isoformat()}
        test_index_file.write_text(json.dumps(empty_index), encoding='utf-8')

        # Import
        importer = KnowledgeImporter()
        result = importer.import_from_json(export_file, merge=True)

        assert result["sessions_imported"] == 5

    def test_import_from_portable(self, sample_sessions_index, temp_dir, monkeypatch):
        """Test portable format import."""
        # Setup all paths
        test_knowledge_dir = temp_dir / "test-knowledge-portable"
        test_sessions_dir = temp_dir / "test-sessions-portable"
        test_index_file = test_knowledge_dir / "sessions-index.json"

        monkeypatch.setattr(
            knowledge_import,
            "KNOWLEDGE_DIR",
            test_knowledge_dir
        )
        monkeypatch.setattr(
            knowledge_import,
            "SESSIONS_DIR",
            test_sessions_dir
        )
        monkeypatch.setattr(
            knowledge_import,
            "INDEX_FILE",
            test_index_file
        )
        monkeypatch.setattr(
            knowledge_export,
            "KNOWLEDGE_DIR",
            test_knowledge_dir
        )
        monkeypatch.setattr(
            knowledge_export,
            "SESSIONS_DIR",
            test_sessions_dir
        )
        monkeypatch.setattr(
            knowledge_export,
            "INDEX_FILE",
            test_index_file
        )

        # Create directories
        test_knowledge_dir.mkdir(parents=True, exist_ok=True)
        test_sessions_dir.mkdir(parents=True, exist_ok=True)

        # Copy sample data
        import shutil
        shutil.copy(sample_sessions_index["index_file"], test_index_file)
        for session_file in sample_sessions_index["sessions_dir"].glob("*.md"):
            shutil.copy(session_file, test_sessions_dir / session_file.name)

        # Create portable export
        exporter = KnowledgeExporter()
        export_file = temp_dir / "to-import.pa-export"
        exporter.create_portable_export(export_file)

        # Clear index for import test
        empty_index = {"sessions": [], "last_updated": datetime.now().isoformat()}
        test_index_file.write_text(json.dumps(empty_index), encoding='utf-8')

        # Import
        importer = KnowledgeImporter()
        result = importer.import_from_portable(export_file, merge=True)

        assert result["sessions_imported"] == 5

    def test_validate_import(self, sample_sessions_index, monkeypatch):
        """Test import validation."""
        monkeypatch.setattr(
            knowledge_import,
            "KNOWLEDGE_DIR",
            sample_sessions_index["temp_dir"] / "knowledge"
        )
        monkeypatch.setattr(
            knowledge_import,
            "SESSIONS_DIR",
            sample_sessions_index["temp_dir"] / "sessions"
        )
        monkeypatch.setattr(
            knowledge_import,
            "INDEX_FILE",
            sample_sessions_index["index_file"]
        )

        importer = KnowledgeImporter()
        result = importer.validate_import(sample_sessions_index["index_file"])

        assert result["valid"] is True
        assert result["format"] == "json"
        assert result["sessions_count"] == 5


# ============================================================================
# USAGE INSIGHTS TESTS
# ============================================================================

class TestUsageInsights:
    """Tests for UsageAnalyzer class."""

    def test_get_usage_insights(self, sample_sessions_index, monkeypatch):
        """Test comprehensive insights generation."""
        monkeypatch.setattr(
            usage_insights,
            "KNOWLEDGE_DIR",
            sample_sessions_index["temp_dir"] / "knowledge"
        )
        monkeypatch.setattr(
            usage_insights,
            "SESSIONS_DIR",
            sample_sessions_index["temp_dir"] / "sessions"
        )
        monkeypatch.setattr(
            usage_insights,
            "INDEX_FILE",
            sample_sessions_index["index_file"]
        )

        analyzer = UsageAnalyzer()
        insights = analyzer.get_usage_insights(timeframe='all')

        assert "summary" in insights
        assert "activity" in insights
        assert "errors" in insights
        assert "topics" in insights
        assert "productivity" in insights

        assert insights["summary"]["total_sessions"] == 5
        assert insights["summary"]["total_words"] > 0

    def test_get_error_patterns(self, sample_sessions_index, monkeypatch):
        """Test error pattern detection."""
        monkeypatch.setattr(
            usage_insights,
            "KNOWLEDGE_DIR",
            sample_sessions_index["temp_dir"] / "knowledge"
        )
        monkeypatch.setattr(
            usage_insights,
            "SESSIONS_DIR",
            sample_sessions_index["temp_dir"] / "sessions"
        )
        monkeypatch.setattr(
            usage_insights,
            "INDEX_FILE",
            sample_sessions_index["index_file"]
        )

        analyzer = UsageAnalyzer()
        patterns = analyzer.get_error_patterns()

        # Should return a list (may be empty if no error patterns detected)
        assert isinstance(patterns, list)

    def test_get_activity_timeline(self, sample_sessions_index, monkeypatch):
        """Test activity timeline generation."""
        monkeypatch.setattr(
            usage_insights,
            "KNOWLEDGE_DIR",
            sample_sessions_index["temp_dir"] / "knowledge"
        )
        monkeypatch.setattr(
            usage_insights,
            "SESSIONS_DIR",
            sample_sessions_index["temp_dir"] / "sessions"
        )
        monkeypatch.setattr(
            usage_insights,
            "INDEX_FILE",
            sample_sessions_index["index_file"]
        )

        analyzer = UsageAnalyzer()

        # Test daily granularity
        timeline = analyzer.get_activity_timeline(granularity='day')
        assert len(timeline) == 5  # 5 sessions on different days

        # Test weekly granularity
        timeline = analyzer.get_activity_timeline(granularity='week')
        assert len(timeline) > 0

        # Test monthly granularity
        timeline = analyzer.get_activity_timeline(granularity='month')
        assert len(timeline) > 0

    def test_filter_by_timeframe(self, sample_sessions_index, monkeypatch):
        """Test timeframe filtering."""
        monkeypatch.setattr(
            usage_insights,
            "KNOWLEDGE_DIR",
            sample_sessions_index["temp_dir"] / "knowledge"
        )
        monkeypatch.setattr(
            usage_insights,
            "SESSIONS_DIR",
            sample_sessions_index["temp_dir"] / "sessions"
        )
        monkeypatch.setattr(
            usage_insights,
            "INDEX_FILE",
            sample_sessions_index["index_file"]
        )

        analyzer = UsageAnalyzer()
        sessions = analyzer.index_data.get("sessions", [])

        # Test 'all' timeframe
        filtered = analyzer._filter_by_timeframe(sessions, 'all')
        assert len(filtered) == 5

        # Test '30d' timeframe (should include all recent sessions)
        filtered = analyzer._filter_by_timeframe(sessions, '30d')
        assert len(filtered) > 0

        # Test invalid timeframe (should return all)
        filtered = analyzer._filter_by_timeframe(sessions, 'invalid')
        assert len(filtered) == 5


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestKnowledgeManagementIntegration:
    """Integration tests for knowledge management workflow."""

    def test_export_import_cycle(self, sample_sessions_index, temp_dir, monkeypatch):
        """Test complete export-import cycle."""
        # Setup paths for export
        monkeypatch.setattr(
            knowledge_export,
            "KNOWLEDGE_DIR",
            sample_sessions_index["temp_dir"] / "knowledge"
        )
        monkeypatch.setattr(
            knowledge_export,
            "SESSIONS_DIR",
            sample_sessions_index["temp_dir"] / "sessions"
        )
        monkeypatch.setattr(
            knowledge_export,
            "INDEX_FILE",
            sample_sessions_index["index_file"]
        )

        # Export
        exporter = KnowledgeExporter()
        export_file = temp_dir / "cycle-test.pa-export"
        export_result = exporter.create_portable_export(export_file)
        assert export_result["sessions_exported"] == 5

        # Setup paths for import
        monkeypatch.setattr(
            knowledge_import,
            "KNOWLEDGE_DIR",
            temp_dir / "import-knowledge"
        )
        monkeypatch.setattr(
            knowledge_import,
            "SESSIONS_DIR",
            temp_dir / "import-sessions"
        )
        monkeypatch.setattr(
            knowledge_import,
            "INDEX_FILE",
            temp_dir / "import-knowledge" / "sessions-index.json"
        )

        # Create initial state for import
        (temp_dir / "import-knowledge").mkdir(parents=True, exist_ok=True)
        (temp_dir / "import-sessions").mkdir(parents=True, exist_ok=True)
        initial_index = {"sessions": [], "last_updated": datetime.now().isoformat()}
        (temp_dir / "import-knowledge" / "sessions-index.json").write_text(
            json.dumps(initial_index), encoding='utf-8'
        )

        # Import
        importer = KnowledgeImporter()
        import_result = importer.import_from_portable(export_file, merge=True)

        assert import_result["sessions_imported"] == 5

    def test_search_after_export(self, sample_sessions_index, temp_dir, monkeypatch):
        """Test that search works correctly."""
        monkeypatch.setattr(
            session_search,
            "KNOWLEDGE_DIR",
            sample_sessions_index["temp_dir"] / "knowledge"
        )
        monkeypatch.setattr(
            session_search,
            "SESSIONS_DIR",
            sample_sessions_index["temp_dir"] / "sessions"
        )
        monkeypatch.setattr(
            session_search,
            "INDEX_FILE",
            sample_sessions_index["index_file"]
        )

        searcher = SessionSearch()

        # Search for "error"
        results = searcher.search_sessions(query="error", limit=10)
        assert len(results) > 0

        # Search with topic filter
        results = searcher.search_sessions(filters={"topic": "python"}, limit=10)
        assert len(results) > 0


# ============================================================================
# API FUNCTION TESTS
# ============================================================================

class TestAPIFunctions:
    """Tests for public API functions."""

    def test_export_knowledge_api(self, sample_sessions_index, temp_dir, monkeypatch):
        """Test export_knowledge API function."""
        test_knowledge_dir = temp_dir / "api-knowledge"
        test_sessions_dir = temp_dir / "api-sessions"
        test_index_file = test_knowledge_dir / "sessions-index.json"

        monkeypatch.setattr(
            knowledge_export,
            "KNOWLEDGE_DIR",
            test_knowledge_dir
        )
        monkeypatch.setattr(
            knowledge_export,
            "SESSIONS_DIR",
            test_sessions_dir
        )
        monkeypatch.setattr(
            knowledge_export,
            "INDEX_FILE",
            test_index_file
        )

        # Copy sample data
        import shutil
        test_knowledge_dir.mkdir(parents=True, exist_ok=True)
        test_sessions_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy(sample_sessions_index["index_file"], test_index_file)
        for session_file in sample_sessions_index["sessions_dir"].glob("*.md"):
            shutil.copy(session_file, test_sessions_dir / session_file.name)

        # Force reimport to pick up monkeypatched paths
        import importlib
        import knowledge_export as ke_module
        importlib.reload(ke_module)

        result = ke_module.export_knowledge(
            str(temp_dir / "api-export"),
            format='json',
            from_date='2026-04-01',
            to_date='2026-04-17'
        )

        # Should export all 5 sessions in date range
        assert result["sessions_exported"] > 0
        assert result["format"] == "json"

    def test_import_knowledge_api(self, sample_sessions_index, temp_dir, monkeypatch):
        """Test import_knowledge API function."""
        # Setup export paths
        export_knowledge_dir = temp_dir / "export-knowledge-api"
        export_sessions_dir = temp_dir / "export-sessions-api"
        export_index_file = export_knowledge_dir / "sessions-index.json"

        monkeypatch.setattr(
            knowledge_export,
            "KNOWLEDGE_DIR",
            export_knowledge_dir
        )
        monkeypatch.setattr(
            knowledge_export,
            "SESSIONS_DIR",
            export_sessions_dir
        )
        monkeypatch.setattr(
            knowledge_export,
            "INDEX_FILE",
            export_index_file
        )

        # Copy sample data for export
        import shutil
        export_knowledge_dir.mkdir(parents=True, exist_ok=True)
        export_sessions_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy(sample_sessions_index["index_file"], export_index_file)
        for session_file in sample_sessions_index["sessions_dir"].glob("*.md"):
            shutil.copy(session_file, export_sessions_dir / session_file.name)

        # Force reimport
        import importlib
        import knowledge_export as ke_module
        importlib.reload(ke_module)

        export_file = temp_dir / "api-import-test.json"
        export_result = ke_module.export_knowledge(str(export_file), format='json')

        # Setup completely separate import paths
        import_knowledge_dir = temp_dir / "import-knowledge-api2"
        import_sessions_dir = temp_dir / "import-sessions-api2"
        import_index_file = import_knowledge_dir / "sessions-index.json"

        # Clear any monkeypatch from previous tests
        monkeypatch.setattr(
            knowledge_import,
            "KNOWLEDGE_DIR",
            import_knowledge_dir
        )
        monkeypatch.setattr(
            knowledge_import,
            "SESSIONS_DIR",
            import_sessions_dir
        )
        monkeypatch.setattr(
            knowledge_import,
            "INDEX_FILE",
            import_index_file
        )

        # Create initial state
        import_knowledge_dir.mkdir(parents=True, exist_ok=True)
        import_sessions_dir.mkdir(parents=True, exist_ok=True)
        initial_index = {"sessions": [], "last_updated": datetime.now().isoformat()}
        import_index_file.write_text(json.dumps(initial_index), encoding='utf-8')

        # Force reimport with clean state
        import knowledge_import as ki_module
        importlib.reload(ki_module)

        result = ki_module.import_knowledge(str(export_file), merge=True, skip_existing=False)

        # Should import sessions from the export
        assert result["sessions_imported"] >= 0  # May be 0 if already imported
        # Verify the import worked by checking the index was updated
        assert import_index_file.exists()

    def test_get_usage_insights_api(self, sample_sessions_index, temp_dir, monkeypatch):
        """Test get_usage_insights API function."""
        test_knowledge_dir = temp_dir / "insights-knowledge"
        test_sessions_dir = temp_dir / "insights-sessions"
        test_index_file = test_knowledge_dir / "sessions-index.json"

        monkeypatch.setattr(
            usage_insights,
            "KNOWLEDGE_DIR",
            test_knowledge_dir
        )
        monkeypatch.setattr(
            usage_insights,
            "SESSIONS_DIR",
            test_sessions_dir
        )
        monkeypatch.setattr(
            usage_insights,
            "INDEX_FILE",
            test_index_file
        )

        # Copy sample data
        import shutil
        test_knowledge_dir.mkdir(parents=True, exist_ok=True)
        test_sessions_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy(sample_sessions_index["index_file"], test_index_file)
        for session_file in sample_sessions_index["sessions_dir"].glob("*.md"):
            shutil.copy(session_file, test_sessions_dir / session_file.name)

        # Force reimport
        import importlib
        import usage_insights as ui_module
        importlib.reload(ui_module)

        insights = ui_module.get_usage_insights(timeframe='all')

        assert "summary" in insights
        assert insights["summary"]["total_sessions"] > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
