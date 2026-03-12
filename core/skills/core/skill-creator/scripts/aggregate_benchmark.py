#!/usr/bin/env python3
"""
Skill Quality Benchmark Aggregator

Aggregates skill evaluation results and generates benchmark reports.
Compares skill evaluations against baselines to identify quality trends.

Usage:
    python aggregate_benchmark.py --evals-dir ../evals --output benchmark-report.md
    python aggregate_benchmark.py  # Uses defaults
"""

import argparse
import json
import math
import platform
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


def _should_use_emojis() -> bool:
    if platform.system() != "Windows":
        return True
    try:
        import ctypes

        kernel32 = ctypes.windll.kernel32
        code_page = kernel32.GetConsoleOutputCP()
        return code_page == 65001
    except Exception:
        return False


def _get_safe_prefix(prefix_type: str = "info") -> str:
    ascii_prefixes = {
        "success": "[OK]",
        "error": "[ERROR]",
        "warning": "[WARN]",
        "info": "[INFO]",
    }
    return ascii_prefixes.get(prefix_type, "[INFO]")


DEFAULT_EVALS_DIR = Path(__file__).parent.parent / "evals"
DEFAULT_OUTPUT = Path(__file__).parent.parent / "benchmark-report.md"

GRADE_RANGES = {
    "A": (90, 100),
    "B": (80, 89),
    "C": (70, 79),
    "D": (60, 69),
    "F": (0, 59),
}

BASELINE_SCORES = {
    "mvi_compliance": 80,
    "clarity": 75,
    "completeness": 70,
    "actionability": 75,
    "cross_platform": 70,
}


def aggregate_evals(evals_dir: str) -> List[Dict[str, Any]]:
    """
    Collect all evaluation JSON files from the specified directory.

    Args:
        evals_dir: Path to directory containing eval JSON files.

    Returns:
        List of evaluation dictionaries.
    """
    evals_path = Path(evals_dir)
    if not evals_path.exists():
        print(f"{_get_safe_prefix('error')} Directory not found: {evals_dir}")
        return []

    evals: List[Dict[str, Any]] = []
    json_files = list(evals_path.glob("*.json"))

    if not json_files:
        print(f"{_get_safe_prefix('warning')} No JSON files found in {evals_dir}")
        return []

    for json_file in json_files:
        try:
            with open(json_file, encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    evals.extend(data)
                elif isinstance(data, dict):
                    evals.append(data)
        except json.JSONDecodeError as e:
            print(f"{_get_safe_prefix('error')} Invalid JSON in {json_file.name}: {e}")
        except Exception as e:
            print(f"{_get_safe_prefix('error')} Error reading {json_file.name}: {e}")

    return evals


def compute_statistics(evals: List[Dict[str, Any]]) -> Dict[str, Dict[str, float]]:
    """
    Compute mean, median, and standard deviation for each criterion.

    Args:
        evals: List of evaluation dictionaries.

    Returns:
        Dictionary with statistics per criterion.
    """
    if not evals:
        return {}

    all_criteria: Dict[str, List[float]] = {}

    for eval_item in evals:
        scores = eval_item.get("scores", {})
        for criterion, score in scores.items():
            if criterion not in all_criteria:
                all_criteria[criterion] = []
            all_criteria[criterion].append(float(score))

    stats: Dict[str, Dict[str, float]] = {}

    for criterion, values in all_criteria.items():
        if not values:
            continue

        n = len(values)
        mean_val = sum(values) / n

        sorted_values = sorted(values)
        mid = n // 2
        if n % 2 == 0:
            median_val = (sorted_values[mid - 1] + sorted_values[mid]) / 2
        else:
            median_val = sorted_values[mid]

        variance = sum((x - mean_val) ** 2 for x in values) / n
        std_dev = math.sqrt(variance)

        stats[criterion] = {
            "mean": round(mean_val, 1),
            "median": round(median_val, 1),
            "std_dev": round(std_dev, 1),
            "min": round(min(values), 1),
            "max": round(max(values), 1),
            "count": n,
        }

    if evals:
        overall_scores = [float(e.get("overall", 0)) for e in evals if "overall" in e]
        if overall_scores:
            n = len(overall_scores)
            mean_val = sum(overall_scores) / n
            sorted_overall = sorted(overall_scores)
            mid = n // 2
            median_val = (
                (sorted_overall[mid - 1] + sorted_overall[mid]) / 2
                if n % 2 == 0
                else sorted_overall[mid]
            )
            variance = sum((x - mean_val) ** 2 for x in overall_scores) / n
            stats["overall"] = {
                "mean": round(mean_val, 1),
                "median": round(median_val, 1),
                "std_dev": round(math.sqrt(variance), 1),
                "min": round(min(overall_scores), 1),
                "max": round(max(overall_scores), 1),
                "count": n,
            }

    return stats


def compare_to_baseline(
    skill_eval: Dict[str, Any], baseline: Dict[str, int]
) -> Dict[str, Any]:
    """
    Compare a single skill evaluation against baseline scores.

    Args:
        skill_eval: Single skill evaluation dictionary.
        baseline: Dictionary of baseline scores per criterion.

    Returns:
        Comparison result with differences and status.
    """
    scores = skill_eval.get("scores", {})
    skill_name = skill_eval.get("skill", "Unknown")

    comparison: Dict[str, Any] = {
        "skill": skill_name,
        "overall": skill_eval.get("overall", 0),
        "grade": skill_eval.get("grade", "N/A"),
        "criteria": {},
        "above_baseline": 0,
        "below_baseline": 0,
        "meets_baseline": True,
    }

    for criterion, score in scores.items():
        baseline_score = baseline.get(criterion, 75)
        diff = score - baseline_score
        status = "above" if diff > 0 else ("below" if diff < 0 else "equal")

        comparison["criteria"][criterion] = {
            "score": score,
            "baseline": baseline_score,
            "difference": diff,
            "status": status,
        }

        if diff >= 0:
            comparison["above_baseline"] += 1
        else:
            comparison["below_baseline"] += 1
            comparison["meets_baseline"] = False

    return comparison


def get_grade_for_score(score: float) -> str:
    """Convert numeric score to letter grade."""
    for grade, (low, high) in GRADE_RANGES.items():
        if low <= score <= high:
            return grade
    return "F"


def compute_grade_distribution(
    evals: List[Dict[str, Any]],
) -> Dict[str, Dict[str, Any]]:
    """
    Compute distribution of grades across evaluations.

    Args:
        evals: List of evaluation dictionaries.

    Returns:
        Dictionary with grade distribution stats.
    """
    distribution: Dict[str, Dict[str, Any]] = {
        grade: {"count": 0, "skills": [], "percentage": 0.0} for grade in GRADE_RANGES
    }

    total = len(evals)

    for eval_item in evals:
        grade = eval_item.get("grade", get_grade_for_score(eval_item.get("overall", 0)))
        skill_name = eval_item.get("skill", "Unknown")

        if grade in distribution:
            distribution[grade]["count"] += 1
            distribution[grade]["skills"].append(skill_name)

    if total > 0:
        for grade in distribution:
            distribution[grade]["percentage"] = round(
                distribution[grade]["count"] / total * 100, 1
            )

    return distribution


def generate_benchmark_report(
    evals: List[Dict[str, Any]],
    stats: Dict[str, Dict[str, float]],
    distribution: Dict[str, Dict[str, Any]],
    baseline: Dict[str, int],
) -> str:
    """
    Generate a markdown benchmark report.

    Args:
        evals: List of evaluation dictionaries.
        stats: Statistics computed from evaluations.
        distribution: Grade distribution.
        baseline: Baseline scores for comparison.

    Returns:
        Markdown formatted report string.
    """
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    lines: List[str] = []
    lines.append("# Skill Quality Benchmark Report")
    lines.append(f"Generated: {now}")
    lines.append("")

    lines.append("## Summary Statistics")
    lines.append("")
    lines.append("| Criterion | Mean | Median | Std Dev | Min | Max | Count |")
    lines.append("|-----------|------|--------|---------|-----|-----|-------|")

    criterion_order = [
        "mvi_compliance",
        "clarity",
        "completeness",
        "actionability",
        "cross_platform",
        "overall",
    ]

    for criterion in criterion_order:
        if criterion in stats:
            s = stats[criterion]
            display_name = criterion.replace("_", " ").title()
            lines.append(
                f"| {display_name} | {s['mean']} | {s['median']} | "
                f"{s['std_dev']} | {s['min']} | {s['max']} | {s['count']} |"
            )

    for criterion, s in stats.items():
        if criterion not in criterion_order:
            display_name = criterion.replace("_", " ").title()
            lines.append(
                f"| {display_name} | {s['mean']} | {s['median']} | "
                f"{s['std_dev']} | {s['min']} | {s['max']} | {s['count']} |"
            )

    lines.append("")
    lines.append("## Grade Distribution")
    lines.append("")

    for grade in ["A", "B", "C", "D", "F"]:
        d = distribution[grade]
        low, high = GRADE_RANGES[grade]
        skills_str = ", ".join(d["skills"]) if d["skills"] else "None"
        lines.append(
            f"- **{grade} ({low}-{high})**: {d['count']} skills ({d['percentage']}%)"
        )
        if d["skills"]:
            lines.append(f"  - Skills: {skills_str}")

    lines.append("")
    lines.append("## Top Performers")
    lines.append("")

    sorted_evals = sorted(evals, key=lambda x: x.get("overall", 0), reverse=True)
    top_performers = sorted_evals[:5]

    if top_performers:
        for i, eval_item in enumerate(top_performers, 1):
            skill = eval_item.get("skill", "Unknown")
            overall = eval_item.get("overall", 0)
            grade = eval_item.get("grade", "N/A")
            lines.append(f"{i}. **{skill}**: {overall} ({grade})")
    else:
        lines.append("No evaluations available.")

    lines.append("")
    lines.append("## Needs Improvement")
    lines.append("")

    needs_improvement = [e for e in evals if e.get("overall", 100) < 75]
    needs_improvement.sort(key=lambda x: x.get("overall", 0))

    if needs_improvement:
        for i, eval_item in enumerate(needs_improvement, 1):
            skill = eval_item.get("skill", "Unknown")
            overall = eval_item.get("overall", 0)
            grade = eval_item.get("grade", "N/A")
            suggestions = eval_item.get("suggestions", [])

            lines.append(f"{i}. **{skill}**: {overall} ({grade})")
            if suggestions:
                for sug in suggestions[:3]:
                    lines.append(f"   - {sug}")
    else:
        lines.append("All skills meet quality thresholds.")

    lines.append("")
    lines.append("## Baseline Comparison")
    lines.append("")
    lines.append("| Skill | Overall | Above | Below | Meets Baseline |")
    lines.append("|-------|---------|-------|-------|----------------|")

    for eval_item in sorted_evals:
        comparison = compare_to_baseline(eval_item, baseline)
        status = "[OK]" if comparison["meets_baseline"] else "[WARN]"
        lines.append(
            f"| {comparison['skill']} | {comparison['overall']} | "
            f"{comparison['above_baseline']} | {comparison['below_baseline']} | {status} |"
        )

    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append(f"*Total skills evaluated: {len(evals)}*")
    lines.append(f"*Baseline used: {baseline}*")

    return "\n".join(lines)


def print_summary_table(
    evals: List[Dict[str, Any]], stats: Dict[str, Dict[str, float]]
) -> None:
    """
    Print a summary table to console.

    Args:
        evals: List of evaluation dictionaries.
        stats: Statistics computed from evaluations.
    """
    prefix_ok = _get_safe_prefix("success")
    prefix_info = _get_safe_prefix("info")
    prefix_warn = _get_safe_prefix("warning")

    print(f"\n{prefix_info} Skill Quality Benchmark Summary")
    print("=" * 60)

    if not evals:
        print(f"{prefix_warn} No evaluations found.")
        return

    print(f"\nTotal Skills Evaluated: {len(evals)}")

    if stats:
        print(f"\nMean Scores:")
        for criterion, s in stats.items():
            display_name = criterion.replace("_", " ").title()
            print(
                f"  {display_name}: {s['mean']} (median: {s['median']}, std: {s['std_dev']})"
            )

    grade_dist = compute_grade_distribution(evals)
    print(f"\nGrade Distribution:")
    for grade in ["A", "B", "C", "D", "F"]:
        d = grade_dist[grade]
        bar = "#" * d["count"]
        print(f"  {grade}: {bar} ({d['count']}, {d['percentage']}%)")

    sorted_evals = sorted(evals, key=lambda x: x.get("overall", 0), reverse=True)
    top = sorted_evals[0] if sorted_evals else None
    if top:
        print(
            f"\n{prefix_ok} Top Performer: {top.get('skill', 'Unknown')} ({top.get('overall', 0)})"
        )

    needs_improvement = [e for e in evals if e.get("overall", 100) < 75]
    if needs_improvement:
        worst = min(needs_improvement, key=lambda x: x.get("overall", 0))
        print(
            f"{prefix_warn} Needs Attention: {worst.get('skill', 'Unknown')} ({worst.get('overall', 0)})"
        )


def main() -> int:
    """Main entry point for CLI usage."""
    parser = argparse.ArgumentParser(
        description="Aggregate skill evaluations and generate benchmark reports."
    )
    parser.add_argument(
        "--evals-dir",
        type=str,
        default=str(DEFAULT_EVALS_DIR),
        help=f"Directory containing evaluation JSON files (default: {DEFAULT_EVALS_DIR})",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=str(DEFAULT_OUTPUT),
        help=f"Output markdown report file (default: {DEFAULT_OUTPUT})",
    )
    parser.add_argument(
        "--baseline",
        type=str,
        default=None,
        help="JSON file with baseline scores (optional)",
    )

    args = parser.parse_args()

    prefix_ok = _get_safe_prefix("success")
    prefix_info = _get_safe_prefix("info")
    prefix_error = _get_safe_prefix("error")

    print(f"{prefix_info} Loading evaluations from: {args.evals_dir}")

    evals = aggregate_evals(args.evals_dir)

    if not evals:
        print(f"{prefix_error} No evaluations found. Exiting.")
        return 1

    print(f"{prefix_ok} Loaded {len(evals)} evaluations")

    baseline = BASELINE_SCORES.copy()
    if args.baseline:
        try:
            with open(args.baseline, encoding="utf-8") as f:
                custom_baseline = json.load(f)
                baseline.update(custom_baseline)
                print(f"{prefix_ok} Loaded custom baseline from: {args.baseline}")
        except Exception as e:
            print(f"{prefix_error} Failed to load baseline: {e}")

    stats = compute_statistics(evals)
    distribution = compute_grade_distribution(evals)

    print_summary_table(evals, stats)

    report = generate_benchmark_report(evals, stats, distribution, baseline)

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(report)
        print(f"\n{prefix_ok} Report written to: {output_path}")
    except Exception as e:
        print(f"\n{prefix_error} Failed to write report: {e}")
        return 1

    return 0


def self_test() -> None:
    """Run self-tests for the module."""
    print("Running self-tests...")

    test_evals = [
        {
            "skill": "@test-skill-1",
            "overall": 95,
            "grade": "A",
            "scores": {"mvi_compliance": 95, "clarity": 90, "actionability": 100},
            "suggestions": [],
        },
        {
            "skill": "@test-skill-2",
            "overall": 72,
            "grade": "C",
            "scores": {"mvi_compliance": 70, "clarity": 75, "actionability": 71},
            "suggestions": ["Improve clarity", "Add examples"],
        },
    ]

    stats = compute_statistics(test_evals)
    assert "overall" in stats, "Missing overall stats"
    assert stats["overall"]["mean"] == 83.5, f"Wrong mean: {stats['overall']['mean']}"

    comparison = compare_to_baseline(test_evals[0], BASELINE_SCORES)
    assert comparison["meets_baseline"] == True, "Should meet baseline"
    assert comparison["above_baseline"] == 3, (
        f"Wrong above count: {comparison['above_baseline']}"
    )

    distribution = compute_grade_distribution(test_evals)
    assert distribution["A"]["count"] == 1, (
        f"Wrong A count: {distribution['A']['count']}"
    )
    assert distribution["C"]["count"] == 1, (
        f"Wrong C count: {distribution['C']['count']}"
    )

    report = generate_benchmark_report(test_evals, stats, distribution, BASELINE_SCORES)
    assert "# Skill Quality Benchmark Report" in report
    assert "@test-skill-1" in report
    assert "@test-skill-2" in report

    print("All self-tests passed!")


if __name__ == "__main__":
    import sys

    if "--test" in sys.argv:
        self_test()
    else:
        sys.exit(main())
