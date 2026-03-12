#!/usr/bin/env python3
"""
Framework Guardian - Enforcement System
========================================

Validates CORE processes before commits, pushes, and releases.

Usage:
    python framework-guardian.py --timing pre-commit
    python framework-guardian.py --timing pre-push --branch main
    python framework-guardian.py --checks 006,007 --level block
    python framework-guardian.py --fix

Author: FreakingJSON-PA Framework
Version: 1.0.0
"""

import argparse
import hashlib
import os
import re
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set

try:
    import yaml

    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False

TIMING_PRESETS = {
    "pre-commit": {
        "checks": ["006", "007"],
        "max_duration_seconds": 5,
        "level": "warn",
    },
    "pre-push": {
        "checks": ["006", "007"],
        "max_duration_seconds": 10,
        "level": "block",
    },
    "pre-release": {
        "checks": ["001", "006", "007"],
        "max_duration_seconds": 30,
        "level": "block",
    },
    "session-end": {
        "checks": ["003", "005"],
        "max_duration_seconds": 10,
        "level": "warn",
    },
}

DEFAULT_ENFORCEMENT_CONFIG = {
    "enabled": True,
    "level": "warn",
    "checks": {
        "001": {"enabled": True, "severity": "warn"},
        "006": {"enabled": True, "severity": "block"},
        "007": {"enabled": True, "severity": "block"},
    },
    "timing": TIMING_PRESETS,
}

FORBIDDEN_SCRIPTS = [
    "core/scripts/sync-prealpha.py",
    "core/scripts/sync-prealpha-optimized.py",
    "core/scripts/sync-base-to-dev.sh",
    "core/scripts/sync-base-to-prod.sh",
    "core/scripts/sync-dev-to-base.sh",
    "core/scripts/sync-dev-safe.bat",
    "core/scripts/sync-menu.bat",
    "core/scripts/backup-critical.bat",
    "core/scripts/restore-from-backup.py",
    "core/scripts/restore-dev-resources.py",
    "core/scripts/recover-maaji.py",
    "core/scripts/validate-dev-resources.py",
    "core/scripts/vitals-remote-setup.py",
    "core/scripts/test_framework.py",
    "core/scripts/test_sync_prealpha_optimized.py",
]

FORBIDDEN_DOCS = [
    "docs/RELEASE-CHECKLIST.md",
    "docs/backlog.md",
    "docs/backlog.view.md",
    "docs/AGENT-CONFIGURATION.md",
    "docs/SYNC-PROTOCOL.md",
    "docs/workflow-test-example.md",
]

PROD_ONLY_IGNORE_PATTERNS = {
    "PRPs",
    ".opencode/plans",
    "core/scripts/test_*.py",
    "core/scripts/.backup-*",
    "*.backup-*",
    "docs/backlog.md",
    "docs/backlog.view.md",
    "docs/AGENT-CONFIGURATION.md",
    "docs/MULTI-CLI.md",
    "docs/RELEASE-CHECKLIST.md",
    "docs/VITALS-GUARDIAN.md",
    "docs/VITALS-QUICKSTART.md",
    "docs/WORKFLOW-STANDARD.md",
    "docs/prd-*.md",
    "docs/workflow-test-*.md",
    "docs/PLAN-*.md",
    "docs/SYNC-PROTOCOL.md",
}

CREDENTIAL_PATTERNS = [
    r"(?i)(password|passwd|pwd)\s*[=:]\s*['\"]?[^'\"\s]+['\"]?",
    r"(?i)(api_key|apikey|api-key)\s*[=:]\s*['\"]?[^'\"\s]+['\"]?",
    r"(?i)(secret|token|auth)\s*[=:]\s*['\"]?[^'\"\s]+['\"]?",
    r"(?i)(bearer\s+[a-zA-Z0-9\-_]+)",
    r"(?i)(aws_access_key_id|aws_secret_access_key)\s*[=:]\s*['\"]?[^'\"\s]+['\"]?",
]

VERSION_TRACKED_FILES = [
    "VERSION",
    "README.md",
    "AGENTS.md",
    "config/framework.yaml",
    "CHANGELOG.md",
]


@dataclass
class EnforcementResult:
    passed: bool
    check_id: str
    message: str
    fix_suggestion: str = ""
    details: List[str] = field(default_factory=list)


@dataclass
class CheckDetail:
    status: bool
    message: str


class Colors:
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    CYAN = "\033[96m"
    RESET = "\033[0m"
    BOLD = "\033[1m"

    @classmethod
    def disable(cls):
        cls.GREEN = ""
        cls.RED = ""
        cls.YELLOW = ""
        cls.CYAN = ""
        cls.RESET = ""
        cls.BOLD = ""


class FrameworkGuardian:
    def __init__(self, config_path: str = "config/framework.yaml"):
        self.root = self._find_root()
        self.config = self._load_config(config_path)
        self._results_cache: Dict[str, EnforcementResult] = {}

    def _find_root(self) -> Path:
        current = Path(__file__).resolve()
        for parent in current.parents:
            if (parent / "VERSION").exists() and (parent / "AGENTS.md").exists():
                return parent
        return Path.cwd()

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        config = DEFAULT_ENFORCEMENT_CONFIG.copy()
        full_path = self.root / config_path

        if not full_path.exists():
            return config

        if not YAML_AVAILABLE:
            return config

        try:
            with open(full_path, "r", encoding="utf-8") as f:
                yaml_config = yaml.safe_load(f) or {}

            if "enforcement" in yaml_config:
                self._deep_merge(config, yaml_config["enforcement"])
        except Exception:
            pass

        return config

    def _deep_merge(self, base: dict, override: dict):
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = value

    def _check_pass(self, message: str) -> str:
        return f"{Colors.GREEN}[OK]{Colors.RESET} {message}"

    def _check_fail(self, message: str) -> str:
        return f"{Colors.RED}[X]{Colors.RESET} {message}"

    def _check_warn(self, message: str) -> str:
        return f"{Colors.YELLOW}[!]{Colors.RESET} {message}"

    def check_core_001_framework_first(
        self, context: Optional[Dict] = None
    ) -> EnforcementResult:
        check_id = "001"
        details: List[CheckDetail] = []
        context = context or {}

        skills_md = self.root / "core" / "skills" / "SKILLS.md"
        agents_md = self.root / "AGENTS.md"

        if skills_md.exists():
            details.append(CheckDetail(True, "SKILLS.md exists"))
            skills_content = skills_md.read_text(encoding="utf-8")
            skill_count = len(
                re.findall(r"^\| \*\*@[\w-]+\*\*", skills_content, re.MULTILINE)
            )
            details.append(
                CheckDetail(True, f"SKILLS.md: {skill_count} skills registered")
            )
        else:
            details.append(CheckDetail(False, "SKILLS.md not found"))

        if agents_md.exists():
            details.append(CheckDetail(True, "AGENTS.md exists"))
            agents_content = agents_md.read_text(encoding="utf-8")
            agent_count = len(re.findall(r"\*\*@[A-Za-z-]+\*\*", agents_content))
            details.append(CheckDetail(True, f"AGENTS.md: {agent_count} agents found"))
        else:
            details.append(CheckDetail(False, "AGENTS.md not found"))

        if "action" in context:
            action = context["action"].lower()
            if "skill" in action:
                details.append(
                    CheckDetail(
                        True,
                        "Framework-first: Consult SKILLS.md before creating new skills",
                    )
                )
            elif "agent" in action:
                details.append(
                    CheckDetail(
                        True,
                        "Framework-first: Consult AGENTS.md before creating new agents",
                    )
                )

        all_passed = all(d.status for d in details)
        messages = [d.message for d in details]

        return EnforcementResult(
            passed=all_passed,
            check_id=check_id,
            message="Framework-First Validation "
            + ("passed" if all_passed else "failed"),
            fix_suggestion="Consult core/skills/SKILLS.md before creating new skills/agents"
            if not all_passed
            else "",
            details=messages,
        )

    def check_core_006_version_governance(self) -> EnforcementResult:
        check_id = "006"
        details: List[CheckDetail] = []

        version_file = self.root / "VERSION"
        if not version_file.exists():
            return EnforcementResult(
                passed=False,
                check_id=check_id,
                message="VERSION file not found",
                fix_suggestion="Create VERSION file with semantic version (e.g., 0.1.8-prealpha)",
            )

        current_version = version_file.read_text(encoding="utf-8").strip()
        details.append(CheckDetail(True, f"VERSION file exists"))
        details.append(CheckDetail(True, f"VERSION: {current_version}"))

        version_pattern = re.compile(r"^\d+\.\d+\.\d+(-[a-zA-Z0-9.]+)?$")
        if not version_pattern.match(current_version):
            details.append(
                CheckDetail(False, f"VERSION format invalid: {current_version}")
            )
        else:
            details.append(CheckDetail(True, f"VERSION format valid"))

        tracked_versions: Dict[str, Optional[str]] = {}
        version_mismatches: List[str] = []

        for tracked_file in VERSION_TRACKED_FILES:
            file_path = self.root / tracked_file
            if not file_path.exists():
                continue

            try:
                content = file_path.read_text(encoding="utf-8")
                patterns = [
                    rf"version:\s*{re.escape(current_version)}",
                    rf"Version:\s*{re.escape(current_version)}",
                    rf"v{re.escape(current_version)}",
                    rf"{re.escape(current_version)}",
                ]

                found = False
                for pattern in patterns:
                    if re.search(pattern, content, re.IGNORECASE):
                        found = True
                        break

                if tracked_file == "CHANGELOG.md":
                    changelog_pattern = re.compile(
                        rf"^##\s+\[?{re.escape(current_version)}\]?", re.MULTILINE
                    )
                    found = bool(changelog_pattern.search(content))

                tracked_versions[tracked_file] = current_version if found else None

                if found:
                    details.append(
                        CheckDetail(True, f"{tracked_file}: {current_version}")
                    )
                else:
                    if tracked_file != "CHANGELOG.md":
                        details.append(
                            CheckDetail(False, f"{tracked_file}: version mismatch")
                        )
                        version_mismatches.append(tracked_file)
                    else:
                        details.append(
                            CheckDetail(
                                False, f"{tracked_file}: no entry for {current_version}"
                            )
                        )
                        version_mismatches.append(tracked_file)
            except Exception as e:
                details.append(CheckDetail(False, f"{tracked_file}: read error - {e}"))

        all_passed = all(d.status for d in details)
        messages = [d.message for d in details]

        fix_suggestion = ""
        if version_mismatches:
            fix_suggestion = f"Run: python core/scripts/version-updater.py to sync versions in: {', '.join(version_mismatches)}"

        return EnforcementResult(
            passed=all_passed,
            check_id=check_id,
            message="Version Governance " + ("passed" if all_passed else "failed"),
            fix_suggestion=fix_suggestion,
            details=messages,
        )

    def check_core_007_release_sanitization(
        self, target: str = "prod"
    ) -> EnforcementResult:
        check_id = "007"
        details: List[CheckDetail] = []
        issues: List[str] = []

        credential_found = self._scan_for_credentials()
        if credential_found:
            details.append(
                CheckDetail(
                    False, f"Credentials found in {len(credential_found)} files"
                )
            )
            issues.extend(credential_found[:5])
        else:
            details.append(CheckDetail(True, "No credentials found"))

        if target == "prod":
            prp_dir = self.root / "PRPs"
            if prp_dir.exists():
                prp_files = list(prp_dir.glob("**/*.md"))
                if prp_files:
                    details.append(
                        CheckDetail(
                            False, f"PRPs directory exists with {len(prp_files)} files"
                        )
                    )
                    issues.append("Remove PRPs/ directory before release")
                else:
                    details.append(CheckDetail(True, "PRPs directory is empty"))
            else:
                details.append(CheckDetail(True, "No PRPs in release target"))

            for pattern in PROD_ONLY_IGNORE_PATTERNS:
                matched_files = self._match_pattern(pattern)
                if matched_files:
                    details.append(
                        CheckDetail(False, f"Internal docs found: {pattern}")
                    )
                    issues.extend(matched_files[:3])

            if not any(not d.status for d in details if "Internal docs" in d.message):
                details.append(CheckDetail(True, "No internal docs in release target"))

            test_scripts = list(self.root.glob("core/scripts/test_*.py"))
            if test_scripts:
                details.append(
                    CheckDetail(False, f"Test scripts found: {len(test_scripts)} files")
                )
                issues.extend([str(s.relative_to(self.root)) for s in test_scripts[:3]])
            else:
                details.append(CheckDetail(True, "No test scripts in release target"))

        for forbidden in FORBIDDEN_SCRIPTS:
            path = self.root / forbidden
            if path.exists():
                details.append(CheckDetail(False, f"Forbidden script: {forbidden}"))
                issues.append(forbidden)

        if not any("Forbidden script" in d.message for d in details if not d.status):
            details.append(CheckDetail(True, "No forbidden scripts"))

        for forbidden in FORBIDDEN_DOCS:
            path = self.root / forbidden
            if path.exists():
                details.append(CheckDetail(False, f"Forbidden doc: {forbidden}"))
                issues.append(forbidden)

        if not any("Forbidden doc" in d.message for d in details if not d.status):
            details.append(CheckDetail(True, "No forbidden docs"))

        all_passed = all(d.status for d in details)
        messages = [d.message for d in details]

        fix_suggestion = ""
        if issues:
            unique_issues = list(dict.fromkeys(issues))[:5]
            fix_suggestion = "Remove before release:\n  - " + "\n  - ".join(
                unique_issues
            )

        return EnforcementResult(
            passed=all_passed,
            check_id=check_id,
            message="Release Sanitization " + ("passed" if all_passed else "failed"),
            fix_suggestion=fix_suggestion,
            details=messages,
        )

    def _scan_for_credentials(self) -> List[str]:
        findings: List[str] = []
        scan_dirs = ["core/scripts", "config"]

        for scan_dir in scan_dirs:
            dir_path = self.root / scan_dir
            if not dir_path.exists():
                continue

            for ext in ["*.py", "*.yaml", "*.json", "*.env"]:
                for file_path in dir_path.rglob(ext):
                    if file_path.name.startswith("."):
                        continue

                    try:
                        content = file_path.read_text(encoding="utf-8")
                        for pattern in CREDENTIAL_PATTERNS:
                            if re.search(pattern, content):
                                rel_path = str(file_path.relative_to(self.root))
                                if rel_path not in findings:
                                    findings.append(rel_path)
                                break
                    except Exception:
                        continue

        return findings

    def _match_pattern(self, pattern: str) -> List[str]:
        matches: List[str] = []

        if "*" in pattern:
            for match in self.root.glob(pattern):
                if match.exists():
                    matches.append(str(match.relative_to(self.root)))
        else:
            path = self.root / pattern
            if path.exists():
                matches.append(pattern)

        return matches

    def check_core_003_antifragile_errors(self) -> EnforcementResult:
        check_id = "003"
        details: List[CheckDetail] = []

        errors_dir = self.root / "core" / ".context" / "knowledge" / "errors"
        if errors_dir.exists():
            error_logs = list(errors_dir.glob("*.md"))
            details.append(
                CheckDetail(True, f"Error logging enabled ({len(error_logs)} logs)")
            )
        else:
            details.append(CheckDetail(True, "Error logging directory ready"))

        playbooks_dir = self.root / "core" / ".context" / "knowledge" / "playbooks"
        if playbooks_dir.exists():
            playbooks = list(playbooks_dir.glob("PB-*.md"))
            details.append(
                CheckDetail(
                    True, f"Recovery playbooks available ({len(playbooks)} playbooks)"
                )
            )
        else:
            details.append(CheckDetail(True, "Playbooks directory ready"))

        all_passed = all(d.status for d in details)
        messages = [d.message for d in details]

        return EnforcementResult(
            passed=all_passed,
            check_id=check_id,
            message="Antifragile Error Recovery "
            + ("passed" if all_passed else "failed"),
            fix_suggestion="Ensure error logging is configured in config/framework.yaml"
            if not all_passed
            else "",
            details=messages,
        )

    def check_core_005_assembly_line(self) -> EnforcementResult:
        check_id = "005"
        details: List[CheckDetail] = []

        session_end = self.root / "core" / "scripts" / "session-end.py"
        if session_end.exists():
            details.append(
                CheckDetail(True, "session-end.py available for preservation")
            )
        else:
            details.append(CheckDetail(False, "session-end.py not found"))

        sessions_dir = self.root / "core" / ".context" / "sessions"
        if sessions_dir.exists():
            sessions = list(sessions_dir.glob("*.md"))
            details.append(
                CheckDetail(
                    True, f"Sessions directory active ({len(sessions)} sessions)"
                )
            )
        else:
            details.append(CheckDetail(True, "Sessions directory ready"))

        all_passed = all(d.status for d in details)
        messages = [d.message for d in details]

        return EnforcementResult(
            passed=all_passed,
            check_id=check_id,
            message="Assembly Line " + ("passed" if all_passed else "failed"),
            fix_suggestion="Ensure session-end.py is available for workflow preservation"
            if not all_passed
            else "",
            details=messages,
        )

    def run_validation(
        self,
        timing: str,
        checks: Optional[List[str]] = None,
        level: Optional[str] = None,
    ) -> List[EnforcementResult]:
        if timing in TIMING_PRESETS:
            preset = TIMING_PRESETS[timing]
            if checks is None:
                checks = preset.get("checks", [])
            if level is None:
                level = preset.get("level", "warn")

        if checks is None:
            checks = ["006", "007"]

        if level is None:
            level = self.config.get("level", "warn")

        check_map: Dict[str, Callable[..., EnforcementResult]] = {
            "001": self.check_core_001_framework_first,
            "003": self.check_core_003_antifragile_errors,
            "005": self.check_core_005_assembly_line,
            "006": self.check_core_006_version_governance,
            "007": self.check_core_007_release_sanitization,
        }

        results: List[EnforcementResult] = []
        for check_id in checks:
            if check_id in check_map:
                cache_key = f"{check_id}_{timing}"
                if cache_key in self._results_cache:
                    results.append(self._results_cache[cache_key])
                else:
                    result = check_map[check_id]()
                    self._results_cache[cache_key] = result
                    results.append(result)

        return results

    def print_report(
        self, results: List[EnforcementResult], timing: str = "", level: str = ""
    ):
        print("\n" + "=" * 60)
        print(f"{Colors.BOLD}FRAMEWORK ENFORCEMENT SYSTEM{Colors.RESET}")
        if timing:
            print(f"Timing: {timing} | Level: {level}")
        print("=" * 60)

        all_passed = True
        for result in results:
            core_name = self._get_core_name(result.check_id)
            status_icon = "[+]" if result.passed else "[-]"
            status_color = Colors.GREEN if result.passed else Colors.RED

            print(f"\n{status_color}[CORE-{result.check_id}] {core_name}{Colors.RESET}")

            for detail in result.details:
                if (
                    "[OK]" in detail
                    or detail.startswith("OK")
                    or "exists" in detail.lower()
                ):
                    print(f"  {Colors.GREEN}[OK]{Colors.RESET} {detail}")
                elif (
                    "[X]" in detail
                    or detail.startswith("X")
                    or "found" in detail.lower()
                ):
                    print(f"  {Colors.RED}[X]{Colors.RESET} {detail}")
                    all_passed = False
                else:
                    print(f"  {Colors.GREEN}[OK]{Colors.RESET} {detail}")

            if not result.passed:
                all_passed = False
                if result.fix_suggestion:
                    print(
                        f"  {Colors.YELLOW}Fix:{Colors.RESET} {result.fix_suggestion}"
                    )

        print("\n" + "=" * 60)
        if all_passed:
            print(f"{Colors.GREEN}PASSED: All checks passed{Colors.RESET}")
        else:
            print(f"{Colors.RED}FAILED: Some checks failed{Colors.RESET}")
        print("=" * 60)

        return all_passed

    def _get_core_name(self, check_id: str) -> str:
        names = {
            "001": "Framework-First Validation",
            "003": "Antifragile Error Recovery",
            "005": "Assembly Line",
            "006": "Version Governance",
            "007": "Release Sanitization",
        }
        return names.get(check_id, f"Core {check_id}")


def main():
    parser = argparse.ArgumentParser(
        description="Framework Guardian - Enforcement System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python framework-guardian.py --timing pre-commit
    python framework-guardian.py --timing pre-push --branch main
    python framework-guardian.py --checks 006,007 --level block
    python framework-guardian.py --fix
        """,
    )

    parser.add_argument(
        "--timing",
        choices=list(TIMING_PRESETS.keys()),
        help="Timing preset for validation",
    )
    parser.add_argument(
        "--checks",
        type=str,
        help="Comma-separated check IDs (001,006,007)",
    )
    parser.add_argument(
        "--level",
        choices=["warn", "block"],
        help="Enforcement level",
    )
    parser.add_argument(
        "--branch",
        type=str,
        help="Target branch (for context)",
    )
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Show fix suggestions for failures",
    )
    parser.add_argument(
        "--config",
        type=str,
        default="config/framework.yaml",
        help="Path to config file",
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        help="Disable colored output",
    )
    parser.add_argument(
        "--target",
        choices=["prod", "dev"],
        default="prod",
        help="Target environment for sanitization check",
    )

    args = parser.parse_args()

    if args.no_color or not sys.stdout.isatty():
        Colors.disable()

    guardian = FrameworkGuardian(args.config)

    checks = None
    if args.checks:
        checks = [c.strip() for c in args.checks.split(",")]

    timing = args.timing or "pre-commit"
    level = args.level

    start_time = time.time()
    results = guardian.run_validation(timing, checks, level)
    elapsed = time.time() - start_time

    effective_level = level or TIMING_PRESETS.get(timing, {}).get("level", "warn")
    all_passed = guardian.print_report(results, timing, effective_level)

    if timing in TIMING_PRESETS:
        max_duration = TIMING_PRESETS[timing].get("max_duration_seconds", 30)
        if elapsed > max_duration:
            print(
                f"\n{Colors.YELLOW}[!] Duration {elapsed:.2f}s exceeded limit {max_duration}s{Colors.RESET}"
            )

    if not all_passed:
        if args.fix:
            print(f"\n{Colors.CYAN}Fix Suggestions:{Colors.RESET}")
            for result in results:
                if not result.passed and result.fix_suggestion:
                    print(f"  [CORE-{result.check_id}] {result.fix_suggestion}")

        if effective_level == "block":
            sys.exit(1)

    sys.exit(0)


def self_test():
    print("=" * 60)
    print("FRAMEWORK GUARDIAN - SELF TEST")
    print("=" * 60)

    Colors.disable()

    guardian = FrameworkGuardian()

    print("\n[TEST 1] Configuration Loading")
    print(f"  Root: {guardian.root}")
    print(f"  Config keys: {list(guardian.config.keys())}")

    print("\n[TEST 2] CORE-001 Framework-First")
    result = guardian.check_core_001_framework_first()
    print(f"  Passed: {result.passed}")
    print(f"  Message: {result.message}")

    print("\n[TEST 3] CORE-006 Version Governance")
    result = guardian.check_core_006_version_governance()
    print(f"  Passed: {result.passed}")
    print(f"  Message: {result.message}")
    for detail in result.details[:3]:
        print(f"    - {detail}")

    print("\n[TEST 4] CORE-007 Release Sanitization")
    result = guardian.check_core_007_release_sanitization()
    print(f"  Passed: {result.passed}")
    print(f"  Message: {result.message}")

    print("\n[TEST 5] Full Validation Run")
    results = guardian.run_validation("pre-commit")
    all_passed = all(r.passed for r in results)
    print(f"  All passed: {all_passed}")

    print("\n" + "=" * 60)
    print("SELF TEST COMPLETE")
    print("=" * 60)

    return all_passed


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--self-test":
        success = self_test()
        sys.exit(0 if success else 1)
    main()
