#!/usr/bin/env python3
"""
PA Framework — Usage Insights
==============================
Analiza patrones de uso recurrentes en el historial de sesiones:
- Top errores frecuentes
- Top skills más usadas
- Sesiones por día/semana/mes
- Patrones de actividad
- Métricas de productividad

API:
    get_usage_insights(timeframe='all')
    get_error_patterns(limit=10)
    get_activity_timeline(granularity='day')
    get_productivity_metrics()

Usage:
    python core/scripts/usage_insights.py
    python core/scripts/usage_insights.py --timeframe 30d
    python core/scripts/usage_insights.py --errors
    python core/scripts/usage_insights.py --timeline --granularity week
    python core/scripts/usage_insights.py --json

Autor: FreakingJSON-PA Framework
Version: 1.0.0 (Phase 5 Workstream 2)
"""

import argparse
import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Paths
SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent.parent
CONTEXT_DIR = REPO_ROOT / "core" / ".context"
SESSIONS_DIR = CONTEXT_DIR / "sessions"
KNOWLEDGE_DIR = CONTEXT_DIR / "knowledge"
INDEX_FILE = KNOWLEDGE_DIR / "sessions-index.json"
ERRORS_LOG = REPO_ROOT / "logs" / "lsp" / "errors.log"


class UsageAnalyzer:
    """
    Analyze usage patterns from session history.
    """

    def __init__(self):
        self.index_data: Dict = {}
        self.sessions_content: Dict[str, str] = {}
        self._load_index()
        self._load_session_content()

    def _load_index(self):
        """Load sessions index."""
        if INDEX_FILE.exists():
            try:
                with open(INDEX_FILE, 'r', encoding='utf-8') as f:
                    self.index_data = json.load(f)
            except (json.JSONDecodeError, IOError):
                self.index_data = {"sessions": []}
        else:
            self.index_data = {"sessions": []}

    def _load_session_content(self):
        """Load full session content for analysis."""
        self.sessions_content = {}
        if not SESSIONS_DIR.exists():
            return

        for session_file in SESSIONS_DIR.glob("*.md"):
            if re.match(r"\d{4}-\d{2}-\d{2}", session_file.name):
                try:
                    content = session_file.read_text(encoding='utf-8')
                    self.sessions_content[session_file.stem] = content
                except IOError:
                    pass

    def _filter_by_timeframe(
        self,
        sessions: List[Dict],
        timeframe: str
    ) -> List[Dict]:
        """Filter sessions by timeframe."""
        if timeframe == 'all':
            return sessions

        # Parse timeframe (e.g., '30d', '7d', '3m', '1y')
        now = datetime.now()
        match = re.match(r"(\d+)([dmy])", timeframe.lower())
        if not match:
            return sessions

        value = int(match.group(1))
        unit = match.group(2)

        if unit == 'd':
            delta = timedelta(days=value)
        elif unit == 'm':
            delta = timedelta(days=value * 30)
        elif unit == 'y':
            delta = timedelta(days=value * 365)
        else:
            return sessions

        cutoff = (now - delta).strftime('%Y-%m-%d')
        return [s for s in sessions if s.get('id', '') >= cutoff]

    def get_usage_insights(self, timeframe: str = 'all') -> Dict[str, Any]:
        """
        Get comprehensive usage insights.

        Args:
            timeframe: Time period ('all', '30d', '7d', '3m', '1y')

        Returns:
            Dict with all insights
        """
        sessions = self.index_data.get("sessions", [])
        filtered = self._filter_by_timeframe(sessions, timeframe)

        insights = {
            "timeframe": timeframe,
            "generated_at": datetime.now().isoformat(),
            "summary": self._get_summary(filtered),
            "activity": self._get_activity_patterns(filtered),
            "errors": self._get_error_insights(filtered),
            "topics": self._get_topic_insights(filtered),
            "productivity": self._get_productivity_metrics(filtered),
            "trends": self._get_trends(filtered)
        }

        return insights

    def _get_summary(self, sessions: List[Dict]) -> Dict[str, Any]:
        """Get summary statistics."""
        if not sessions:
            return {"total_sessions": 0}

        total_words = sum(s.get("stats", {}).get("word_count", 0) for s in sessions)
        total_files = sum(s.get("stats", {}).get("files_modified", 0) for s in sessions)
        total_decisions = sum(s.get("stats", {}).get("decisions", 0) for s in sessions)
        total_errors = sum(s.get("stats", {}).get("lsp_errors", 0) for s in sessions)

        # Date range
        session_ids = sorted([s.get("id", "") for s in sessions if s.get("id")])
        date_range = {
            "from": session_ids[0] if session_ids else None,
            "to": session_ids[-1] if session_ids else None,
            "days": self._calculate_days(session_ids[0], session_ids[-1]) if len(session_ids) > 1 else 1
        }

        # Session types distribution
        type_counts = Counter(s.get("type", "other") for s in sessions)

        return {
            "total_sessions": len(sessions),
            "total_words": total_words,
            "total_files_modified": total_files,
            "total_decisions": total_decisions,
            "total_errors": total_errors,
            "date_range": date_range,
            "avg_words_per_session": round(total_words / len(sessions), 1) if sessions else 0,
            "session_types": dict(type_counts)
        }

    def _calculate_days(self, start: str, end: str) -> int:
        """Calculate days between two date strings."""
        try:
            start_date = datetime.strptime(start, '%Y-%m-%d')
            end_date = datetime.strptime(end, '%Y-%m-%d')
            return (end_date - start_date).days + 1
        except ValueError:
            return 1

    def _get_activity_patterns(self, sessions: List[Dict]) -> Dict[str, Any]:
        """Analyze activity patterns."""
        if not sessions:
            return {}

        # Sessions by day of week
        day_counts = Counter()
        for session in sessions:
            session_id = session.get("id", "")
            try:
                date = datetime.strptime(session_id, '%Y-%m-%d')
                day_name = date.strftime('%A')
                day_counts[day_name] += 1
            except ValueError:
                pass

        # Sessions by month
        month_counts = Counter()
        for session in sessions:
            session_id = session.get("id", "")
            if len(session_id) >= 7:
                month = session_id[:7]  # YYYY-MM
                month_counts[month] += 1

        # Most active day
        most_active_day = day_counts.most_common(1)[0] if day_counts else (None, 0)

        return {
            "by_day_of_week": dict(day_counts),
            "by_month": dict(month_counts.most_common(12)),
            "most_active_day": most_active_day[0],
            "avg_sessions_per_week": round(len(sessions) / max(1, self._get_weeks_span(sessions)), 2)
        }

    def _get_weeks_span(self, sessions: List[Dict]) -> float:
        """Calculate weeks span of sessions."""
        session_ids = [s.get("id", "") for s in sessions if s.get("id")]
        if len(session_ids) < 2:
            return 1.0

        try:
            start = datetime.strptime(min(session_ids), '%Y-%m-%d')
            end = datetime.strptime(max(session_ids), '%Y-%m-%d')
            return max(1.0, (end - start).days / 7.0)
        except ValueError:
            return 1.0

    def _get_error_insights(self, sessions: List[Dict]) -> Dict[str, Any]:
        """Analyze error patterns."""
        # Sessions with errors
        error_sessions = [
            s for s in sessions
            if s.get("stats", {}).get("lsp_errors", 0) > 0
        ]

        # Error count distribution
        error_counts = [s.get("stats", {}).get("lsp_errors", 0) for s in error_sessions]

        # Analyze error content from sessions
        error_types = Counter()
        error_contexts = []

        for session_id, content in self.sessions_content.items():
            # Look for error patterns in content
            error_matches = re.findall(
                r'(?:error|Error|ERROR|fail|Fail|FAIL)[:\s]+(.+?)(?:\n|$)',
                content,
                re.IGNORECASE
            )
            for match in error_matches[:5]:  # Max 5 per session
                # Categorize error
                error_lower = match.lower()
                if 'syntax' in error_lower:
                    error_types['syntax'] += 1
                elif 'type' in error_lower:
                    error_types['type'] += 1
                elif 'import' in error_lower:
                    error_types['import'] += 1
                elif 'null' in error_lower or 'none' in error_lower:
                    error_types['null_reference'] += 1
                else:
                    error_types['other'] += 1

                error_contexts.append({
                    "session": session_id,
                    "error": match.strip()[:100]
                })

        return {
            "sessions_with_errors": len(error_sessions),
            "total_errors": sum(error_counts),
            "avg_errors_per_session": round(sum(error_counts) / len(error_sessions), 2) if error_sessions else 0,
            "error_types": dict(error_types),
            "recent_errors": error_contexts[:10]
        }

    def _get_topic_insights(self, sessions: List[Dict]) -> Dict[str, Any]:
        """Analyze topic patterns."""
        topic_counts = Counter()
        topic_sessions: Dict[str, List[str]] = defaultdict(list)

        for session in sessions:
            topics = session.get("topics", [])
            session_id = session.get("id", "")
            for topic in topics:
                topic_counts[topic] += 1
                topic_sessions[topic].append(session_id)

        # Top topics
        top_topics = topic_counts.most_common(10)

        # Topic trends (which topics are growing)
        topic_trends = {}
        for topic, sessions_list in topic_sessions.items():
            if len(sessions_list) >= 2:
                # Compare first half vs second half
                mid = len(sessions_list) // 2
                first_half = len(sessions_list[:mid])
                second_half = len(sessions_list[mid:])
                if first_half > 0:
                    growth = (second_half - first_half) / first_half
                    topic_trends[topic] = round(growth, 2)

        return {
            "top_topics": [{"topic": t, "count": c} for t, c in top_topics],
            "total_unique_topics": len(topic_counts),
            "topic_trends": topic_trends
        }

    def _get_productivity_metrics(self, sessions: List[Dict]) -> Dict[str, Any]:
        """Calculate productivity metrics."""
        if not sessions:
            return {}

        # Words per session trend
        words_over_time = []
        for session in sorted(sessions, key=lambda x: x.get("id", "")):
            words_over_time.append({
                "date": session.get("id", ""),
                "words": session.get("stats", {}).get("word_count", 0)
            })

        # Calculate averages
        word_counts = [s.get("stats", {}).get("word_count", 0) for s in sessions]
        file_counts = [s.get("stats", {}).get("files_modified", 0) for s in sessions]
        decision_counts = [s.get("stats", {}).get("decisions", 0) for s in sessions]

        # Identify high-productivity sessions
        avg_words = sum(word_counts) / len(word_counts) if word_counts else 0
        high_productivity = [
            s for s in sessions
            if s.get("stats", {}).get("word_count", 0) > avg_words * 1.5
        ]

        return {
            "avg_words_per_session": round(avg_words, 1),
            "avg_files_per_session": round(sum(file_counts) / len(file_counts), 1) if file_counts else 0,
            "avg_decisions_per_session": round(sum(decision_counts) / len(decision_counts), 1) if decision_counts else 0,
            "high_productivity_sessions": len(high_productivity),
            "words_trend": words_over_time[-7:]  # Last 7 sessions
        }

    def _get_trends(self, sessions: List[Dict]) -> Dict[str, Any]:
        """Identify trends in session data."""
        if len(sessions) < 4:
            return {"message": "Not enough data for trend analysis"}

        # Sort by date
        sorted_sessions = sorted(sessions, key=lambda x: x.get("id", ""))

        # Split into first half and second half
        mid = len(sorted_sessions) // 2
        first_half = sorted_sessions[:mid]
        second_half = sorted_sessions[mid:]

        # Compare metrics
        first_words = sum(s.get("stats", {}).get("word_count", 0) for s in first_half)
        second_words = sum(s.get("stats", {}).get("word_count", 0) for s in second_half)

        first_files = sum(s.get("stats", {}).get("files_modified", 0) for s in first_half)
        second_files = sum(s.get("stats", {}).get("files_modified", 0) for s in second_half)

        first_errors = sum(s.get("stats", {}).get("lsp_errors", 0) for s in first_half)
        second_errors = sum(s.get("stats", {}).get("lsp_errors", 0) for s in second_half)

        return {
            "word_count_change": self._calc_change(first_words, second_words),
            "files_change": self._calc_change(first_files, second_files),
            "errors_change": self._calc_change(first_errors, second_errors),
            "trend_direction": "increasing" if second_words > first_words else "decreasing"
        }

    def _calc_change(self, first: int, second: int) -> float:
        """Calculate percentage change."""
        if first == 0:
            return 0.0 if second == 0 else 100.0
        return round((second - first) / first * 100, 1)

    def get_error_patterns(self, limit: int = 10) -> List[Dict]:
        """Get top error patterns."""
        error_patterns = []

        for session_id, content in self.sessions_content.items():
            # Find error sections
            error_sections = re.findall(
                r'##?\s*(?:Errors?|Problemas?|Issues?).*?\n(.+?)(?=\n##|\Z)',
                content,
                re.IGNORECASE | re.DOTALL
            )

            for section in error_sections:
                # Extract individual errors
                errors = re.findall(r'[-*]\s*(.+?)(?:\n|$)', section)
                for error in errors[:limit]:
                    error_patterns.append({
                        "session": session_id,
                        "error": error.strip()[:200]
                    })

        # Group by similarity
        pattern_groups = self._group_similar_errors(error_patterns)
        return sorted(pattern_groups, key=lambda x: x['count'], reverse=True)[:limit]

    def _group_similar_errors(self, errors: List[Dict]) -> List[Dict]:
        """Group similar errors together."""
        groups: Dict[str, Dict] = {}

        for error in errors:
            # Normalize error text
            normalized = self._normalize_text(error['error'])
            key = normalized[:50]  # Use first 50 chars as key

            if key in groups:
                groups[key]['count'] += 1
                groups[key]['sessions'].append(error['session'])
            else:
                groups[key] = {
                    'pattern': error['error'][:100],
                    'count': 1,
                    'sessions': [error['session']]
                }

        return list(groups.values())

    def _normalize_text(self, text: str) -> str:
        """Normalize text for comparison."""
        text = text.lower()
        text = re.sub(r'[^\w\s]', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    def get_activity_timeline(
        self,
        granularity: str = 'day'
    ) -> List[Dict]:
        """
        Get activity timeline.

        Args:
            granularity: 'day', 'week', or 'month'

        Returns:
            List of timeline entries
        """
        sessions = self.index_data.get("sessions", [])
        timeline: Dict[str, Dict] = {}

        for session in sessions:
            session_id = session.get("id", "")
            if not session_id:
                continue

            # Determine time bucket
            if granularity == 'day':
                bucket = session_id
            elif granularity == 'week':
                try:
                    date = datetime.strptime(session_id, '%Y-%m-%d')
                    # ISO week number
                    bucket = f"{date.year}-W{date.isocalendar()[1]:02d}"
                except ValueError:
                    bucket = session_id[:10]
            elif granularity == 'month':
                bucket = session_id[:7] if len(session_id) >= 7 else session_id
            else:
                bucket = session_id

            if bucket not in timeline:
                timeline[bucket] = {
                    "period": bucket,
                    "sessions": 0,
                    "words": 0,
                    "files": 0,
                    "decisions": 0
                }

            timeline[bucket]["sessions"] += 1
            timeline[bucket]["words"] += session.get("stats", {}).get("word_count", 0)
            timeline[bucket]["files"] += session.get("stats", {}).get("files_modified", 0)
            timeline[bucket]["decisions"] += session.get("stats", {}).get("decisions", 0)

        return sorted(timeline.values(), key=lambda x: x["period"])


def get_usage_insights(timeframe: str = 'all') -> Dict[str, Any]:
    """
    Main API function for getting usage insights.

    Args:
        timeframe: Time period ('all', '30d', '7d', '3m', '1y')

    Returns:
        Comprehensive insights dict
    """
    analyzer = UsageAnalyzer()
    return analyzer.get_usage_insights(timeframe=timeframe)


def format_insights(insights: Dict[str, Any]) -> str:
    """Format insights for display."""
    output = []

    output.append("=" * 70)
    output.append("PA Framework - Usage Insights")
    output.append("=" * 70)
    output.append(f"Generated: {insights.get('generated_at', 'N/A')}")
    output.append(f"Timeframe: {insights.get('timeframe', 'all')}")
    output.append("")

    # Summary
    summary = insights.get("summary", {})
    output.append("## Summary")
    output.append(f"  Total Sessions: {summary.get('total_sessions', 0)}")
    output.append(f"  Total Words: {summary.get('total_words', 0):,}")
    output.append(f"  Total Files Modified: {summary.get('total_files_modified', 0)}")
    output.append(f"  Total Decisions: {summary.get('total_decisions', 0)}")
    output.append(f"  Total Errors: {summary.get('total_errors', 0)}")
    output.append(f"  Avg Words/Session: {summary.get('avg_words_per_session', 0)}")
    output.append("")

    # Activity
    activity = insights.get("activity", {})
    output.append("## Activity Patterns")
    output.append(f"  Most Active Day: {activity.get('most_active_day', 'N/A')}")
    output.append(f"  Avg Sessions/Week: {activity.get('avg_sessions_per_week', 0)}")
    output.append("  By Day of Week:")
    for day, count in activity.get("by_day_of_week", {}).items():
        output.append(f"    {day}: {count}")
    output.append("")

    # Errors
    errors = insights.get("errors", {})
    output.append("## Error Insights")
    output.append(f"  Sessions with Errors: {errors.get('sessions_with_errors', 0)}")
    output.append(f"  Avg Errors/Session: {errors.get('avg_errors_per_session', 0)}")
    output.append("  Error Types:")
    for etype, count in errors.get("error_types", {}).items():
        output.append(f"    {etype}: {count}")
    output.append("")

    # Topics
    topics = insights.get("topics", {})
    output.append("## Top Topics")
    for topic_info in topics.get("top_topics", [])[:5]:
        output.append(f"  {topic_info['topic']}: {topic_info['count']} sessions")
    output.append("")

    # Productivity
    productivity = insights.get("productivity", {})
    output.append("## Productivity Metrics")
    output.append(f"  Avg Words/Session: {productivity.get('avg_words_per_session', 0)}")
    output.append(f"  Avg Files/Session: {productivity.get('avg_files_per_session', 0)}")
    output.append(f"  High-Productivity Sessions: {productivity.get('high_productivity_sessions', 0)}")
    output.append("")

    # Trends
    trends = insights.get("trends", {})
    output.append("## Trends")
    output.append(f"  Direction: {trends.get('trend_direction', 'N/A')}")
    output.append(f"  Word Count Change: {trends.get('word_count_change', 0)}%")
    output.append(f"  Files Change: {trends.get('files_change', 0)}%")
    output.append(f"  Errors Change: {trends.get('errors_change', 0)}%")
    output.append("")

    output.append("=" * 70)

    return "\n".join(output)


def main():
    parser = argparse.ArgumentParser(
        description="PA Framework Usage Insights",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python usage_insights.py
  python usage_insights.py --timeframe 30d
  python usage_insights.py --errors
  python usage_insights.py --timeline --granularity week
  python usage_insights.py --json
        """
    )

    parser.add_argument("--timeframe", "-t", default="all",
                        help="Time period (all, 30d, 7d, 3m, 1y)")
    parser.add_argument("--errors", action="store_true",
                        help="Show only error patterns")
    parser.add_argument("--timeline", action="store_true",
                        help="Show activity timeline")
    parser.add_argument("--granularity", choices=['day', 'week', 'month'], default='day',
                        help="Timeline granularity")
    parser.add_argument("--topics", action="store_true",
                        help="Show only topic analysis")
    parser.add_argument("--json", action="store_true",
                        help="Output as JSON")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="Verbose output")

    args = parser.parse_args()

    analyzer = UsageAnalyzer()

    if args.errors:
        patterns = analyzer.get_error_patterns()
        if args.json:
            print(json.dumps(patterns, indent=2, ensure_ascii=False))
        else:
            print("Top Error Patterns:")
            print("-" * 50)
            for i, pattern in enumerate(patterns[:10], 1):
                print(f"{i}. [{pattern['count']}x] {pattern['pattern'][:80]}")
                print(f"   Sessions: {', '.join(pattern['sessions'][:3])}")
        return

    if args.timeline:
        timeline = analyzer.get_activity_timeline(granularity=args.granularity)
        if args.json:
            print(json.dumps(timeline, indent=2, ensure_ascii=False))
        else:
            print(f"Activity Timeline ({args.granularity}):")
            print("-" * 50)
            print(f"{'Period':<15} {'Sessions':>10} {'Words':>12} {'Files':>10}")
            print("-" * 50)
            for entry in timeline[-12:]:  # Last 12 periods
                print(f"{entry['period']:<15} {entry['sessions']:>10} {entry['words']:>12,} {entry['files']:>10}")
        return

    if args.topics:
        insights = analyzer.get_usage_insights(timeframe=args.timeframe)
        topics = insights.get("topics", {})
        if args.json:
            print(json.dumps(topics, indent=2, ensure_ascii=False))
        else:
            print("Topic Analysis:")
            print("-" * 50)
            for topic_info in topics.get("top_topics", [])[:10]:
                print(f"  {topic_info['topic']}: {topic_info['count']} sessions")
        return

    # Full insights
    insights = analyzer.get_usage_insights(timeframe=args.timeframe)

    if args.json:
        print(json.dumps(insights, indent=2, ensure_ascii=False))
    else:
        print(format_insights(insights))


if __name__ == "__main__":
    main()
