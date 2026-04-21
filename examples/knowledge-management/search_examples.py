#!/usr/bin/env python3
"""
PA Framework — Knowledge Management Examples
=============================================
Ejemplos de uso para las features de Knowledge Management (Phase 5 WS2).

Run:
    python examples/knowledge-management/search_examples.py
"""

import sys
from pathlib import Path

# Add core/scripts to path
SCRIPT_DIR = Path(__file__).resolve().parent.parent.parent / "core" / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

# Import modules
import importlib.util

def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

session_search = load_module("session_search", SCRIPT_DIR / "session_search.py")
knowledge_export = load_module("knowledge_export", SCRIPT_DIR / "knowledge_export.py")
usage_insights = load_module("usage_insights", SCRIPT_DIR / "usage_insights.py")

SessionSearch = session_search.SessionSearch
KnowledgeExporter = knowledge_export.KnowledgeExporter
UsageAnalyzer = usage_insights.UsageAnalyzer


def example_1_basic_search():
    """Example 1: Basic session search."""
    print("\n" + "=" * 60)
    print("Example 1: Basic Session Search")
    print("=" * 60)

    searcher = SessionSearch()

    # Search for sessions about "error"
    results = searcher.search_sessions(query="error", limit=5)

    print(f"\nFound {len(results)} sessions matching 'error':\n")
    for i, session in enumerate(results, 1):
        print(f"{i}. [{session.get('id')}] {session.get('title')}")
        if 'search_score' in session:
            print(f"   Relevance: {session['search_score']:.4f}")


def example_2_filtered_search():
    """Example 2: Search with filters."""
    print("\n" + "=" * 60)
    print("Example 2: Filtered Search")
    print("=" * 60)

    searcher = SessionSearch()

    # Search with multiple filters
    results = searcher.search_sessions(
        query="python",
        filters={
            "topic": "features",
            "from_date": "2026-01-01"
        },
        limit=10
    )

    print(f"\nSessions about 'python' with topic 'features' since 2026-01-01:")
    print(f"Found: {len(results)} sessions\n")
    for session in results:
        print(f"  - [{session.get('id')}] {session.get('title')}")


def example_3_facets():
    """Example 3: Get search facets."""
    print("\n" + "=" * 60)
    print("Example 3: Search Facets")
    print("=" * 60)

    searcher = SessionSearch()
    facets = searcher.get_facets()

    print(f"\nTotal Sessions: {facets['total_sessions']}")
    print(f"Date Range: {facets['date_range']['min']} to {facets['date_range']['max']}")

    print("\nTop Topics:")
    for topic, count in list(facets['topics'].items())[:5]:
        print(f"  {topic}: {count}")

    print("\nSession Types:")
    for stype, count in facets['types'].items():
        print(f"  {stype}: {count}")


def example_4_export_json():
    """Example 4: Export to JSON."""
    print("\n" + "=" * 60)
    print("Example 4: Export to JSON")
    print("=" * 60)

    exporter = KnowledgeExporter()

    # Export to JSON (in-memory example, won't write file in this demo)
    print("\nExport configuration:")
    print("  Format: JSON")
    print("  Include content: Yes")
    print("  Compact: No")

    # In real usage:
    # result = exporter.export_to_json(Path("./backup.json"))
    # print(f"Exported {result['sessions_exported']} sessions")


def example_5_export_portable():
    """Example 5: Export to portable format."""
    print("\n" + "=" * 60)
    print("Example 5: Export to Portable Format")
    print("=" * 60)

    exporter = KnowledgeExporter()

    print("\nPortable export (.pa-export) includes:")
    print("  - manifest.json (metadata)")
    print("  - sessions-index.json (index)")
    print("  - sessions/*.md (full content)")
    print("  - metadata.json (statistics)")
    print("\nRecommended for backups and transfers.")


def example_6_usage_insights():
    """Example 6: Get usage insights."""
    print("\n" + "=" * 60)
    print("Example 6: Usage Insights")
    print("=" * 60)

    analyzer = UsageAnalyzer()
    insights = analyzer.get_usage_insights(timeframe='all')

    summary = insights.get('summary', {})
    print(f"\nSummary:")
    print(f"  Total Sessions: {summary.get('total_sessions', 0)}")
    print(f"  Total Words: {summary.get('total_words', 0):,}")
    print(f"  Total Files Modified: {summary.get('total_files_modified', 0)}")
    print(f"  Total Decisions: {summary.get('total_decisions', 0)}")

    activity = insights.get('activity', {})
    print(f"\nActivity:")
    print(f"  Most Active Day: {activity.get('most_active_day', 'N/A')}")
    print(f"  Avg Sessions/Week: {activity.get('avg_sessions_per_week', 0)}")

    topics = insights.get('topics', {})
    print(f"\nTop Topics:")
    for topic_info in topics.get('top_topics', [])[:5]:
        print(f"  {topic_info['topic']}: {topic_info['count']} sessions")


def example_7_error_patterns():
    """Example 7: Analyze error patterns."""
    print("\n" + "=" * 60)
    print("Example 7: Error Pattern Analysis")
    print("=" * 60)

    analyzer = UsageAnalyzer()
    patterns = analyzer.get_error_patterns(limit=5)

    print(f"\nTop Error Patterns:")
    for i, pattern in enumerate(patterns, 1):
        print(f"\n{i}. [{pattern['count']}x occurrences]")
        print(f"   {pattern['pattern'][:80]}...")
        print(f"   Sessions: {', '.join(pattern['sessions'][:3])}")


def example_8_activity_timeline():
    """Example 8: Activity timeline."""
    print("\n" + "=" * 60)
    print("Example 8: Activity Timeline")
    print("=" * 60)

    analyzer = UsageAnalyzer()
    timeline = analyzer.get_activity_timeline(granularity='week')

    print(f"\nWeekly Activity (last 5 weeks):")
    print(f"{'Period':<15} {'Sessions':>10} {'Words':>12} {'Files':>10}")
    print("-" * 50)
    for entry in timeline[-5:]:
        print(f"{entry['period']:<15} {entry['sessions']:>10} {entry['words']:>12,} {entry['files']:>10}")


def main():
    """Run all examples."""
    print("\n" + "=" * 60)
    print("PA Framework — Knowledge Management Examples")
    print("Phase 5 Workstream 2")
    print("=" * 60)

    example_1_basic_search()
    example_2_filtered_search()
    example_3_facets()
    example_4_export_json()
    example_5_export_portable()
    example_6_usage_insights()
    example_7_error_patterns()
    example_8_activity_timeline()

    print("\n" + "=" * 60)
    print("Examples Complete!")
    print("=" * 60)
    print("\nFor more information, see:")
    print("  docs/knowledge-management/README.md")
    print("\nRun individual scripts:")
    print("  python core/scripts/session_search.py --interactive")
    print("  python core/scripts/usage_insights.py --timeframe 30d")
    print("  python core/scripts/knowledge_export.py --portable backup.pa-export")
    print()


if __name__ == "__main__":
    main()
