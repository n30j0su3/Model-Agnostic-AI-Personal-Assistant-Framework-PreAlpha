#!/usr/bin/env python3
"""
PA Framework - Pattern Analyzer Module
Analyzes error patterns and suggests playbook creation.

Part of PRP-007: Error Recovery Skill

Usage:
    from pattern_analyzer import PatternAnalyzer

    analyzer = PatternAnalyzer()
    analysis = analyzer.analyze_error_patterns(days=30)
    report = analyzer.generate_trend_report()
"""

import json
import sys
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

if sys.platform == "win32" and sys.stdout.isatty():
    try:
        import io

        sys.stdout = io.TextIOWrapper(
            sys.stdout.buffer, encoding="utf-8", errors="replace"
        )
        sys.stderr = io.TextIOWrapper(
            sys.stderr.buffer, encoding="utf-8", errors="replace"
        )
    except (ValueError, AttributeError):
        pass

SCRIPT_DIR = Path(__file__).resolve().parent
CORE_DIR = SCRIPT_DIR.parent
CONTEXT_DIR = CORE_DIR / ".context"
KNOWLEDGE_DIR = CONTEXT_DIR / "knowledge"
ERRORS_DIR = KNOWLEDGE_DIR / "errors"
PLAYBOOKS_DIR = KNOWLEDGE_DIR / "playbooks"
INSIGHTS_DIR = KNOWLEDGE_DIR / "insights"

ERROR_INDEX_FILE = ERRORS_DIR / "index.json"
PLAYBOOK_INDEX_FILE = PLAYBOOKS_DIR / "index.json"
ANALYSIS_OUTPUT_FILE = INSIGHTS_DIR / "error-analysis.md"


class Colors:
    HEADER = "\033[95m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    END = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"


def c(text: str, color: str) -> str:
    return f"{color}{text}{Colors.END}"


def safe_print(text: str, **kwargs):
    try:
        print(text, **kwargs)
    except UnicodeEncodeError:
        encoding = sys.stdout.encoding or "utf-8"
        safe_text = text.encode(encoding, errors="replace").decode(encoding)
        print(safe_text, **kwargs)


class PatternAnalyzer:
    """
    Analyzes error patterns from the knowledge base.

    Provides insights into error trends, hotspots, and suggests
    playbook creation for recurring error types.

    Attributes:
        errors_dir: Directory containing error data
        playbooks_dir: Directory containing playbook data
        insights_dir: Directory for analysis output
    """

    def __init__(
        self,
        errors_dir: Optional[Path] = None,
        playbooks_dir: Optional[Path] = None,
        insights_dir: Optional[Path] = None,
    ):
        """
        Initialize PatternAnalyzer with custom or default paths.

        Args:
            errors_dir: Optional custom directory for error data.
            playbooks_dir: Optional custom directory for playbook data.
            insights_dir: Optional custom directory for analysis output.
        """
        self.errors_dir = errors_dir or ERRORS_DIR
        self.playbooks_dir = playbooks_dir or PLAYBOOKS_DIR
        self.insights_dir = insights_dir or INSIGHTS_DIR
        self._ensure_directories()

    def _ensure_directories(self) -> None:
        """Create directories if they don't exist."""
        self.errors_dir.mkdir(parents=True, exist_ok=True)
        self.playbooks_dir.mkdir(parents=True, exist_ok=True)
        self.insights_dir.mkdir(parents=True, exist_ok=True)

    def _read_error_index(self) -> Dict[str, Any]:
        """Read and return error index data."""
        try:
            with open(ERROR_INDEX_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {"errors": [], "version": "1.0.0"}

    def _read_playbook_index(self) -> Dict[str, Any]:
        """Read and return playbook index data."""
        try:
            with open(PLAYBOOK_INDEX_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {"playbooks": [], "version": "1.0.0"}

    def _filter_errors_by_days(self, errors: List[Dict], days: int) -> List[Dict]:
        """
        Filter errors from the last N days.

        Args:
            errors: List of error dictionaries.
            days: Number of days to look back.

        Returns:
            Filtered list of errors within the time range.
        """
        cutoff = datetime.now() - timedelta(days=days)
        filtered = []

        for error in errors:
            timestamp_str = error.get("timestamp", "")
            if not timestamp_str:
                continue

            try:
                error_date = datetime.fromisoformat(timestamp_str)
                if error_date >= cutoff:
                    filtered.append(error)
            except (ValueError, TypeError):
                continue

        return filtered

    def analyze_error_patterns(self, days: int = 30) -> Dict[str, Any]:
        """
        Analyze errors from the last N days to find patterns.

        Args:
            days: Number of days to analyze. Defaults to 30.

        Returns:
            Dictionary containing analysis results including:
                - analysis_date: ISO date string
                - period_days: Number of days analyzed
                - total_errors: Count of errors in period
                - top_types: List of most common error types
                - hotspots: List of files with most errors
                - playbook_suggestions: List of suggested new playbooks
                - resolution_rate: Percentage of resolved errors

        Example:
            >>> analyzer = PatternAnalyzer()
            >>> results = analyzer.analyze_error_patterns(days=7)
            >>> print(results["total_errors"])
            15
        """
        index_data = self._read_error_index()
        all_errors = index_data.get("errors", [])
        errors = self._filter_errors_by_days(all_errors, days)

        total_errors = len(errors)
        top_types = self.get_top_error_types(errors=errors)
        hotspots = self.get_error_hotspots(errors=errors)
        playbook_suggestions = self.suggest_playbook_creation(errors=errors)
        resolution_rate = self._calculate_resolution_rate(errors)

        return {
            "analysis_date": datetime.now().strftime("%Y-%m-%d"),
            "period_days": days,
            "total_errors": total_errors,
            "top_types": top_types,
            "hotspots": hotspots,
            "playbook_suggestions": playbook_suggestions,
            "resolution_rate": resolution_rate,
        }

    def get_top_error_types(
        self, limit: int = 10, errors: Optional[List[Dict]] = None
    ) -> List[Dict[str, Any]]:
        """
        Get the most common error types.

        Args:
            limit: Maximum number of error types to return. Defaults to 10.
            errors: Optional pre-filtered list of errors.

        Returns:
            List of dictionaries with error type, count, and associated playbook.

        Example:
            >>> analyzer = PatternAnalyzer()
            >>> top = analyzer.get_top_error_types(limit=5)
            >>> print(top[0])
            {'type': 'UnicodeDecodeError', 'count': 5, 'playbook': 'PB-001'}
        """
        if errors is None:
            index_data = self._read_error_index()
            errors = index_data.get("errors", [])

        type_counter: Counter = Counter()
        playbook_mapping: Dict[str, Optional[str]] = {}

        for error in errors:
            error_type = error.get("type", "Unknown")
            type_counter[error_type] += 1

            if error_type not in playbook_mapping:
                playbook_mapping[error_type] = error.get("playbook_suggestion")

        top_types = []
        for error_type, count in type_counter.most_common(limit):
            top_types.append(
                {
                    "type": error_type,
                    "count": count,
                    "playbook": playbook_mapping.get(error_type),
                }
            )

        return top_types

    def get_error_hotspots(
        self, limit: int = 10, errors: Optional[List[Dict]] = None
    ) -> List[Dict[str, Any]]:
        """
        Find files and modules with the most errors.

        Args:
            limit: Maximum number of hotspots to return. Defaults to 10.
            errors: Optional pre-filtered list of errors.

        Returns:
            List of dictionaries with file path and error count.

        Example:
            >>> analyzer = PatternAnalyzer()
            >>> hotspots = analyzer.get_error_hotspots(limit=5)
            >>> print(hotspots[0])
            {'file': 'session-start.py', 'error_count': 4}
        """
        if errors is None:
            index_data = self._read_error_index()
            errors = index_data.get("errors", [])

        file_counter: Counter = Counter()

        for error in errors:
            file_path = error.get("file", "Unknown")
            if file_path and file_path != "Unknown":
                file_counter[file_path] += 1

        hotspots = []
        for file_path, count in file_counter.most_common(limit):
            hotspots.append({"file": file_path, "error_count": count})

        return hotspots

    def suggest_playbook_creation(
        self, errors: Optional[List[Dict]] = None, min_count: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Recommend new playbooks based on error patterns.

        Analyzes errors that don't have associated playbooks and
        suggests creating new ones for recurring patterns.

        Args:
            errors: Optional pre-filtered list of errors.
            min_count: Minimum occurrences to suggest a playbook. Defaults to 3.

        Returns:
            List of dictionaries with error type, count, and suggested playbook name.

        Example:
            >>> analyzer = PatternAnalyzer()
            >>> suggestions = analyzer.suggest_playbook_creation()
            >>> print(suggestions[0])
            {'error_type': 'FileNotFoundError', 'count': 5, 'suggested_name': 'PB-XXX-file-not-found'}
        """
        if errors is None:
            index_data = self._read_error_index()
            errors = index_data.get("errors", [])

        playbook_index = self._read_playbook_index()
        existing_playbooks = {
            pb.get("id", ""): pb.get("keywords", [])
            for pb in playbook_index.get("playbooks", [])
        }

        unplaybooked_counter: Counter = Counter()
        for error in errors:
            error_type = error.get("type", "")
            playbook = error.get("playbook_suggestion")

            if not playbook and error_type:
                unplaybooked_counter[error_type] += 1

        suggestions = []
        for error_type, count in unplaybooked_counter.most_common():
            if count >= min_count:
                safe_type = error_type.lower().replace("error", "").replace("_", "-")
                safe_type = "".join(c for c in safe_type if c.isalnum() or c == "-")
                suggested_name = f"PB-XXX-{safe_type}"

                suggestions.append(
                    {
                        "error_type": error_type,
                        "count": count,
                        "suggested_name": suggested_name,
                        "priority": "high" if count >= 5 else "medium",
                    }
                )

        return suggestions

    def _calculate_resolution_rate(self, errors: List[Dict]) -> float:
        """
        Calculate the percentage of resolved errors.

        Args:
            errors: List of error dictionaries.

        Returns:
            Resolution rate as a float between 0 and 1.
        """
        if not errors:
            return 0.0

        resolved = sum(1 for e in errors if e.get("resolved", False))
        return round(resolved / len(errors), 2)

    def get_error_trends(self, days: int = 30) -> Dict[str, Any]:
        """
        Analyze error trends over time.

        Args:
            days: Number of days to analyze.

        Returns:
            Dictionary with daily error counts and trend direction.
        """
        index_data = self._read_error_index()
        all_errors = index_data.get("errors", [])
        errors = self._filter_errors_by_days(all_errors, days)

        daily_counts: Dict[str, int] = {}
        for error in errors:
            timestamp_str = error.get("timestamp", "")
            if timestamp_str:
                try:
                    error_date = datetime.fromisoformat(timestamp_str)
                    date_key = error_date.strftime("%Y-%m-%d")
                    daily_counts[date_key] = daily_counts.get(date_key, 0) + 1
                except (ValueError, TypeError):
                    continue

        sorted_dates = sorted(daily_counts.keys())
        if len(sorted_dates) >= 2:
            first_half = sorted_dates[: len(sorted_dates) // 2]
            second_half = sorted_dates[len(sorted_dates) // 2 :]

            first_avg = sum(daily_counts.get(d, 0) for d in first_half) / max(
                len(first_half), 1
            )
            second_avg = sum(daily_counts.get(d, 0) for d in second_half) / max(
                len(second_half), 1
            )

            if second_avg > first_avg * 1.1:
                trend = "increasing"
            elif second_avg < first_avg * 0.9:
                trend = "decreasing"
            else:
                trend = "stable"
        else:
            trend = "insufficient_data"

        return {
            "daily_counts": daily_counts,
            "trend": trend,
            "total_days_with_errors": len(daily_counts),
            "average_per_day": round(
                sum(daily_counts.values()) / max(len(daily_counts), 1), 2
            ),
        }

    def generate_trend_report(
        self, days: int = 30, output_file: Optional[Path] = None
    ) -> str:
        """
        Generate a markdown report of error trends.

        Args:
            days: Number of days to include in analysis.
            output_file: Optional path to write the report.

        Returns:
            The markdown report as a string.

        Example:
            >>> analyzer = PatternAnalyzer()
            >>> report = analyzer.generate_trend_report(days=7)
            >>> print(report[:100])
            '# Error Analysis Report\\n\\n> Generated: 2026-03-11\\n...'
        """
        analysis = self.analyze_error_patterns(days)
        trends = self.get_error_trends(days)

        report_lines = [
            "# Error Analysis Report",
            "",
            f"> Generated: {analysis['analysis_date']}",
            f"> Period: Last {analysis['period_days']} days",
            "",
            "## Summary",
            "",
            f"| Metric | Value |",
            f"|--------|-------|",
            f"| Total Errors | {analysis['total_errors']} |",
            f"| Resolution Rate | {analysis['resolution_rate'] * 100:.0f}% |",
            f"| Trend | {trends['trend']} |",
            f"| Days with Errors | {trends['total_days_with_errors']} |",
            f"| Avg Errors/Day | {trends['average_per_day']} |",
            "",
            "## Top Error Types",
            "",
        ]

        if analysis["top_types"]:
            report_lines.extend(
                [
                    "| Type | Count | Playbook |",
                    "|------|-------|----------|",
                ]
            )
            for item in analysis["top_types"]:
                playbook = item.get("playbook") or "-"
                report_lines.append(
                    f"| {item['type']} | {item['count']} | {playbook} |"
                )
        else:
            report_lines.append("_No errors recorded in this period._")

        report_lines.extend(
            [
                "",
                "## Error Hotspots",
                "",
            ]
        )

        if analysis["hotspots"]:
            report_lines.extend(
                [
                    "| File | Error Count |",
                    "|------|-------------|",
                ]
            )
            for item in analysis["hotspots"]:
                report_lines.append(f"| {item['file']} | {item['error_count']} |")
        else:
            report_lines.append("_No hotspots identified._")

        report_lines.extend(
            [
                "",
                "## Playbook Suggestions",
                "",
            ]
        )

        if analysis["playbook_suggestions"]:
            report_lines.extend(
                [
                    "| Error Type | Count | Suggested Name | Priority |",
                    "|------------|-------|----------------|----------|",
                ]
            )
            for item in analysis["playbook_suggestions"]:
                report_lines.append(
                    f"| {item['error_type']} | {item['count']} | {item['suggested_name']} | {item['priority']} |"
                )
        else:
            report_lines.append("_No playbook suggestions at this time._")

        if trends["daily_counts"]:
            report_lines.extend(
                [
                    "",
                    "## Daily Error Counts",
                    "",
                    "| Date | Count |",
                    "|------|-------|",
                ]
            )
            for date in sorted(trends["daily_counts"].keys(), reverse=True)[:14]:
                count = trends["daily_counts"][date]
                report_lines.append(f"| {date} | {count} |")

        report_lines.extend(
            [
                "",
                "---",
                "",
                "_This report was auto-generated by the Pattern Analyzer module._",
            ]
        )

        report = "\n".join(report_lines)

        if output_file is None:
            output_file = ANALYSIS_OUTPUT_FILE

        try:
            output_file.parent.mkdir(parents=True, exist_ok=True)
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(report)
            safe_print(c(f"[OK] Report saved to {output_file}", Colors.GREEN))
        except Exception as e:
            safe_print(c(f"[WARN] Could not save report: {e}", Colors.YELLOW))

        return report

    def get_errors_by_context(self, days: int = 30) -> Dict[str, List[Dict]]:
        """
        Group errors by their context field.

        Args:
            days: Number of days to analyze.

        Returns:
            Dictionary mapping context strings to lists of errors.
        """
        index_data = self._read_error_index()
        all_errors = index_data.get("errors", [])
        errors = self._filter_errors_by_days(all_errors, days)

        context_groups: Dict[str, List[Dict]] = {}

        for error in errors:
            context = error.get("context", "No context provided")
            if context not in context_groups:
                context_groups[context] = []
            context_groups[context].append(
                {
                    "id": error.get("id"),
                    "type": error.get("type"),
                    "file": error.get("file"),
                    "timestamp": error.get("timestamp"),
                }
            )

        return context_groups

    def get_resolution_time_stats(self, days: int = 30) -> Dict[str, Any]:
        """
        Calculate statistics on error resolution time.

        Args:
            days: Number of days to analyze.

        Returns:
            Dictionary with resolution time statistics.
        """
        index_data = self._read_error_index()
        all_errors = index_data.get("errors", [])
        errors = self._filter_errors_by_days(all_errors, days)

        resolution_times = []

        for error in errors:
            if error.get("resolved") and error.get("resolved_at"):
                try:
                    created = datetime.fromisoformat(error["timestamp"])
                    resolved = datetime.fromisoformat(error["resolved_at"])
                    delta = resolved - created
                    resolution_times.append(delta.total_seconds() / 3600)
                except (ValueError, TypeError):
                    continue

        if resolution_times:
            avg_time = sum(resolution_times) / len(resolution_times)
            min_time = min(resolution_times)
            max_time = max(resolution_times)

            return {
                "average_hours": round(avg_time, 2),
                "min_hours": round(min_time, 2),
                "max_hours": round(max_time, 2),
                "sample_size": len(resolution_times),
            }

        return {
            "average_hours": 0,
            "min_hours": 0,
            "max_hours": 0,
            "sample_size": 0,
        }


def analyze_error_patterns(days: int = 30) -> Dict[str, Any]:
    """
    Convenience function to analyze error patterns.

    Args:
        days: Number of days to analyze.

    Returns:
        Dictionary with analysis results.
    """
    analyzer = PatternAnalyzer()
    return analyzer.analyze_error_patterns(days)


def get_top_error_types(limit: int = 10) -> List[Dict[str, Any]]:
    """
    Convenience function to get top error types.

    Args:
        limit: Maximum number of types to return.

    Returns:
        List of top error types.
    """
    analyzer = PatternAnalyzer()
    return analyzer.get_top_error_types(limit)


def get_error_hotspots() -> List[Dict[str, Any]]:
    """
    Convenience function to get error hotspots.

    Returns:
        List of files with most errors.
    """
    analyzer = PatternAnalyzer()
    return analyzer.get_error_hotspots()


def suggest_playbook_creation() -> List[Dict[str, Any]]:
    """
    Convenience function to get playbook suggestions.

    Returns:
        List of suggested playbooks.
    """
    analyzer = PatternAnalyzer()
    return analyzer.suggest_playbook_creation()


def generate_trend_report(days: int = 30) -> str:
    """
    Convenience function to generate a trend report.

    Args:
        days: Number of days to analyze.

    Returns:
        Markdown report string.
    """
    analyzer = PatternAnalyzer()
    return analyzer.generate_trend_report(days)


if __name__ == "__main__":
    print(c("\n" + "=" * 50, Colors.HEADER))
    print(c("Pattern Analyzer Module Test", Colors.BOLD + Colors.CYAN))
    print(c("=" * 50, Colors.HEADER))

    analyzer = PatternAnalyzer()

    print(c("\n[TEST 1] Analyzing error patterns (last 30 days)...", Colors.CYAN))
    analysis = analyzer.analyze_error_patterns(days=30)
    print(f"  Total errors: {analysis['total_errors']}")
    print(f"  Resolution rate: {analysis['resolution_rate'] * 100:.0f}%")
    print(f"  Top types: {len(analysis['top_types'])}")
    print(f"  Hotspots: {len(analysis['hotspots'])}")
    print(f"  Playbook suggestions: {len(analysis['playbook_suggestions'])}")

    print(c("\n[TEST 2] Getting top error types...", Colors.CYAN))
    top_types = analyzer.get_top_error_types(limit=5)
    for item in top_types[:3]:
        print(f"  {item['type']}: {item['count']} (PB: {item['playbook'] or 'None'})")

    print(c("\n[TEST 3] Getting error hotspots...", Colors.CYAN))
    hotspots = analyzer.get_error_hotspots(limit=5)
    for item in hotspots[:3]:
        print(f"  {item['file']}: {item['error_count']} errors")

    print(c("\n[TEST 4] Getting playbook suggestions...", Colors.CYAN))
    suggestions = analyzer.suggest_playbook_creation()
    if suggestions:
        for item in suggestions[:3]:
            print(
                f"  {item['error_type']}: {item['count']} -> {item['suggested_name']}"
            )
    else:
        print("  No suggestions needed - all patterns have playbooks.")

    print(c("\n[TEST 5] Getting error trends...", Colors.CYAN))
    trends = analyzer.get_error_trends(days=30)
    print(f"  Trend direction: {trends['trend']}")
    print(f"  Days with errors: {trends['total_days_with_errors']}")
    print(f"  Average per day: {trends['average_per_day']}")

    print(c("\n[TEST 6] Getting resolution time stats...", Colors.CYAN))
    stats = analyzer.get_resolution_time_stats(days=30)
    print(f"  Average resolution time: {stats['average_hours']} hours")
    print(f"  Sample size: {stats['sample_size']}")

    print(c("\n[TEST 7] Generating trend report...", Colors.CYAN))
    report = analyzer.generate_trend_report(days=30)
    print(f"  Report length: {len(report)} characters")

    print(c("\n" + "=" * 50, Colors.HEADER))
    print(c("Tests completed successfully!", Colors.GREEN))
    print(c("=" * 50, Colors.HEADER))
