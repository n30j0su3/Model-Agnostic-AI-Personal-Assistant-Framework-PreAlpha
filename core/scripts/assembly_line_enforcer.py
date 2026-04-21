#!/usr/bin/env python3
"""Validate minimum workflow evidence for complex tasks."""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path


TASK_TYPE_KEYWORDS = {
    "prd": {"prd", "product requirements", "requirements document"},
    "roadmap": {"roadmap", "plan maestro", "milestone"},
    "architecture": {"architecture", "arquitectura", "design system"},
    "audit": {"audit", "auditoria", "review", "revision amplia"},
    "feature": {"feature", "feature-definition", "definicion de feature"},
    "multi-module": {"multi-module", "multi-modulo", "cross-module"},
}

COMPLEX_HINTS = {
    "prd",
    "roadmap",
    "architecture",
    "audit",
    "feature",
    "multi-module",
    "exploracion",
    "explorar",
    "arquitectura",
}

WORKFLOW_REQUIRED = {
    "prd",
    "roadmap",
    "architecture",
    "audit",
    "feature",
    "multi-module",
}
PRD_LIKE = {"prd", "roadmap", "feature"}


class AssemblyLineEnforcer:
    def __init__(self, root: Path | None = None):
        self.root = root.resolve() if root else Path(__file__).resolve().parents[2]
        self.warnings: list[str] = []
        self.errors: list[str] = []

    def _has(self, relative_path: str) -> bool:
        return (self.root / relative_path).exists()

    def _infer_task_type(self, task: str, task_type: str | None) -> str:
        if task_type:
            return task_type
        lowered = task.lower()
        for candidate, keywords in TASK_TYPE_KEYWORDS.items():
            if any(keyword in lowered for keyword in keywords):
                return candidate
        return "generic"

    def _requires_workflow(self, task: str, task_type: str) -> bool:
        if task_type in WORKFLOW_REQUIRED:
            return True
        lowered = task.lower()
        return any(keyword in lowered for keyword in COMPLEX_HINTS)

    def validate(
        self,
        task: str,
        task_type: str | None = None,
        context_scout_used: bool = False,
        skills_validated: bool = False,
        prd_generator_used: bool = False,
        plan_documented: bool = False,
        magic_prompt_applied: bool = False,
        force: bool = False,
    ) -> dict:
        self.warnings = []
        self.errors = []
        resolved = self._infer_task_type(task, task_type)
        workflow_required = self._requires_workflow(task, resolved)
        checks = {
            "workflow_standard_exists": self._has("docs/WORKFLOW-STANDARD.md"),
            "assembly_line_exists": self._has("docs/ASSEMBLY-LINE.md"),
            "skills_index_exists": self._has("core/skills/SKILLS.md"),
            "context_scout_available": self._has(
                "core/agents/subagents/context-scout.md"
            ),
            "session_end_available": self._has("core/scripts/session_end.py"),
            "plan_documented": plan_documented,
            "context_scout_used": context_scout_used,
            "skills_validated": skills_validated,
            "magic_prompt_applied": magic_prompt_applied,
        }
        if resolved in PRD_LIKE:
            checks["prd_generator_available"] = self._has(
                "core/skills/core/prd-generator/SKILL.md"
            )
            checks["prd_generator_used"] = prd_generator_used

        if workflow_required:
            for key in (
                "workflow_standard_exists",
                "assembly_line_exists",
                "skills_index_exists",
                "context_scout_available",
                "session_end_available",
            ):
                if not checks[key]:
                    self.errors.append(f"Missing required workflow asset: {key}")
            if not plan_documented:
                self.errors.append("Complex task requires a documented plan or PRP")
            if not context_scout_used:
                self.errors.append(
                    "Complex task requires @context-scout before broad exploration"
                )
            if not skills_validated:
                self.errors.append(
                    "Complex task requires skills validation before execution"
                )
            if resolved in PRD_LIKE and not prd_generator_used:
                self.errors.append("PRD/roadmap/feature work requires @prd-generator")

        return {
            "timestamp": datetime.now().isoformat(),
            "task": task,
            "task_type": resolved,
            "workflow_required": workflow_required,
            "checks": checks,
            "warnings": self.warnings,
            "errors": self.errors,
            "can_proceed": force or not self.errors,
        }


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(
        description="Validate workflow evidence for complex tasks"
    )
    parser.add_argument("task")
    parser.add_argument(
        "--task-type",
        choices=[
            "generic",
            "simple",
            "prd",
            "roadmap",
            "architecture",
            "audit",
            "feature",
            "multi-module",
        ],
    )
    parser.add_argument("--context-scout-used", action="store_true")
    parser.add_argument("--skills-validated", action="store_true")
    parser.add_argument("--prd-generator-used", action="store_true")
    parser.add_argument("--plan-documented", action="store_true")
    parser.add_argument("--magic-prompt-applied", action="store_true")
    parser.add_argument("--root", type=str)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    enforcer = AssemblyLineEnforcer(Path(args.root) if args.root else None)
    report = enforcer.validate(
        args.task,
        task_type=args.task_type,
        context_scout_used=args.context_scout_used,
        skills_validated=args.skills_validated,
        prd_generator_used=args.prd_generator_used,
        plan_documented=args.plan_documented,
        magic_prompt_applied=args.magic_prompt_applied,
        force=args.force,
    )
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(report)
    return 0 if report["can_proceed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
