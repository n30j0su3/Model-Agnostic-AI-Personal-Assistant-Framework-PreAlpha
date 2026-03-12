#!/usr/bin/env python3
"""
Generate Review Data for Eval Viewer
=====================================

Aggregates evaluation data from all evals/*.json files and generates
review-data.json for viewer.html consumption.

Usage:
    python generate_review.py --evals-dir ../evals --output review-data.json

Author: FreakingJSON-PA Framework
Version: 1.0.0
"""

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def load_eval_files(evals_dir: str) -> list[dict[str, Any]]:
    """
    Load all evaluation JSON files from the specified directory.

    Args:
        evals_dir: Path to directory containing eval JSON files.

    Returns:
        List of evaluation dictionaries.
    """
    evals_path = Path(evals_dir)
    if not evals_path.exists():
        print(f"[ERROR] Directory not found: {evals_path}")
        return []

    evaluations = []

    for json_file in evals_path.glob("*.json"):
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)

                if isinstance(data, list):
                    evaluations.extend(data)
                elif isinstance(data, dict):
                    evaluations.append(data)

        except json.JSONDecodeError as e:
            print(f"[WARN] Invalid JSON in {json_file.name}: {e}")
        except Exception as e:
            print(f"[WARN] Error reading {json_file.name}: {e}")

    return evaluations


def compute_grade(score: float) -> str:
    """
    Convert numeric score to letter grade.

    Args:
        score: Numeric score (0-100).

    Returns:
        Letter grade (A, B, C, D, F).
    """
    if score >= 90:
        return "A"
    elif score >= 80:
        return "B"
    elif score >= 70:
        return "C"
    elif score >= 60:
        return "D"
    return "F"


def compute_summary(evaluations: list[dict[str, Any]]) -> dict[str, Any]:
    """
    Compute summary statistics from evaluations.

    Args:
        evaluations: List of evaluation dictionaries.

    Returns:
        Summary dictionary with averages and distributions.
    """
    if not evaluations:
        return {
            "average_score": 0,
            "grade_distribution": {"A": 0, "B": 0, "C": 0, "D": 0, "F": 0},
            "criteria_averages": {},
        }

    total_score = 0
    grade_counts = {"A": 0, "B": 0, "C": 0, "D": 0, "F": 0}
    criteria_totals: dict[str, list[float]] = {}

    for eval_data in evaluations:
        overall = eval_data.get("overall", 0)
        total_score += overall
        grade = eval_data.get("grade", compute_grade(overall))
        grade_counts[grade] = grade_counts.get(grade, 0) + 1

        scores = eval_data.get("scores", {})
        for criterion, value in scores.items():
            if criterion not in criteria_totals:
                criteria_totals[criterion] = []
            criteria_totals[criterion].append(value)

    criteria_averages = {}
    for criterion, values in criteria_totals.items():
        criteria_averages[criterion] = round(sum(values) / len(values), 1)

    return {
        "average_score": round(total_score / len(evaluations), 1),
        "grade_distribution": grade_counts,
        "criteria_averages": criteria_averages,
    }


def compute_baselines(evaluations: list[dict[str, Any]]) -> dict[str, Any]:
    """
    Compute baseline thresholds from evaluation data.

    Args:
        evaluations: List of evaluation dictionaries.

    Returns:
        Dictionary with baseline thresholds and examples.
    """
    if not evaluations:
        return {
            "excellent": {"min": 90, "example": None},
            "good": {"min": 80, "example": None},
            "acceptable": {"min": 70, "example": None},
        }

    sorted_evals = sorted(evaluations, key=lambda x: x.get("overall", 0), reverse=True)

    excellent_example = None
    good_example = None
    acceptable_example = None

    for eval_data in sorted_evals:
        score = eval_data.get("overall", 0)
        skill = eval_data.get("skill", "unknown")

        if score >= 90 and excellent_example is None:
            excellent_example = skill
        elif score >= 80 and score < 90 and good_example is None:
            good_example = skill
        elif score >= 70 and score < 80 and acceptable_example is None:
            acceptable_example = skill

    return {
        "excellent": {"min": 90, "example": excellent_example},
        "good": {"min": 80, "example": good_example},
        "acceptable": {"min": 70, "example": acceptable_example},
    }


def identify_improvements(evaluations: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Identify skills with improvement potential.

    Args:
        evaluations: List of evaluation dictionaries.

    Returns:
        List of improvement recommendations.
    """
    improvements = []

    for eval_data in evaluations:
        overall = eval_data.get("overall", 0)
        grade = eval_data.get("grade", compute_grade(overall))

        if overall < 85:
            potential_grade = "A" if overall >= 75 else ("B" if overall >= 65 else "C")

            suggestions = eval_data.get("suggestions", [])
            priority_suggestions = (
                suggestions[:3] if suggestions else ["Review skill documentation"]
            )

            improvements.append(
                {
                    "skill": eval_data.get("skill", "unknown"),
                    "current_grade": grade,
                    "potential_grade": potential_grade,
                    "current_score": overall,
                    "priority_suggestions": priority_suggestions,
                }
            )

    return sorted(improvements, key=lambda x: x.get("current_score", 0))


def generate_review_data(evals_dir: str) -> dict[str, Any]:
    """
    Generate aggregated review data from all eval JSON files.

    Args:
        evals_dir: Path to directory containing eval JSON files.

    Returns:
        Dictionary with aggregated review data.
    """
    evaluations = load_eval_files(evals_dir)

    return {
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "total_skills": len(evaluations),
        "summary": compute_summary(evaluations),
        "baselines": compute_baselines(evaluations),
        "improvements": identify_improvements(evaluations),
        "evaluations": evaluations,
    }


def generate_html_data(output_path: str, data: dict[str, Any]) -> None:
    """
    Write review data to JSON file for viewer.html consumption.

    Args:
        output_path: Path to output JSON file.
        data: Review data dictionary.
    """
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"[OK] Generated: {output_file}")
    print(f"   Total skills: {data['total_skills']}")
    print(f"   Average score: {data['summary']['average_score']}")


def main():
    parser = argparse.ArgumentParser(
        description="Generate aggregated review data for eval viewer"
    )
    parser.add_argument(
        "--evals-dir",
        default="../evals",
        help="Directory containing eval JSON files (default: ../evals)",
    )
    parser.add_argument(
        "--output",
        default="review-data.json",
        help="Output JSON file path (default: review-data.json)",
    )

    args = parser.parse_args()

    print("\n[REVIEW] Generating review data...")
    print("=" * 50)

    data = generate_review_data(args.evals_dir)
    generate_html_data(args.output, data)

    print("=" * 50)


if __name__ == "__main__":
    main()
