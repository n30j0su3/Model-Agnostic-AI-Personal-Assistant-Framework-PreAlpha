#!/usr/bin/env python3
"""
Version Updater - Interactive version synchronizer for PA Framework.

Synchronizes version across all framework files from a single source of truth
(VERSION file). Provides preview and confirmation before applying changes.

Usage:
    python core/scripts/version-updater.py
    python core/scripts/version-updater.py --dry-run
    python core/scripts/version-updater.py --no-confirm
    python core/scripts/version-updater.py --version 1.0.0
"""

import argparse
import re
import sys
from datetime import date
from pathlib import Path
from typing import Optional


SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from version import normalize


TARGETS = (
    "README.md",
    "AGENTS.md",
    "dashboard.html",
    "config/framework.yaml",
    "core/scripts/pa.py",
    "ROADMAP.md",
    "config/branding.txt",
)

_VERSION_TEXT_RE = re.compile(
    r"(?<![\w-])v?(\d+\.\d+\.\d+(?:-[0-9A-Za-z]+(?:[.-][0-9A-Za-z]+)*)?)(?![\w-])"
)


def get_root_dir() -> Path:
    """Get framework root directory."""
    return Path(__file__).resolve().parents[2]


def get_current_version(version_path: Optional[Path] = None) -> str:
    """
    Read current version from VERSION file.

    Args:
        version_path: Optional path to VERSION file.

    Returns:
        Version string (e.g., "0.1.7-prealpha").

    Raises:
        FileNotFoundError: If VERSION file doesn't exist.
    """
    if version_path is None:
        version_path = get_root_dir() / "VERSION"

    if not version_path.exists():
        raise FileNotFoundError(f"VERSION file not found: {version_path}")

    return normalize(version_path.read_text(encoding="utf-8"))


def parse_version_from_text(text: str) -> Optional[str]:
    """Parse a standalone version token, never a shields.io/CSS class."""
    if "--" in text:
        return None
    match = _VERSION_TEXT_RE.search(text)
    return normalize(match.group(1)) if match else None


def detect_version_in_file(file_path: Path, patterns: list) -> Optional[str]:
    """
    Detect version in a file using regex patterns.

    Args:
        file_path: Path to the file.
        patterns: List of regex patterns with version capture group.

    Returns:
        Detected version string or None.
    """
    if not file_path.exists():
        return None

    content = file_path.read_text(encoding="utf-8")

    for pattern in patterns:
        match = re.search(pattern, content, re.MULTILINE)
        if match:
            try:
                return normalize(match.group(1))
            except ValueError:
                continue

    return None


def detect_version_in_files() -> dict:
    """
    Detect versions in all tracked files.

    Returns:
        Dict with file paths as keys and detected versions as values.
    """
    root = get_root_dir()

    patterns_by_target = {
        "README.md": [
            r"Versión actual:\s*\*\*v?(\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?)\*\*",
        ],
        "AGENTS.md": [
            r"^> \*\*Version: v?(\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?)\*\*",
        ],
        "dashboard.html": [
            r"<title>PA Framework Command Center v?(\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?)</title>",
        ],
        "config/framework.yaml": [
            r"^version:\s*['\"]?v?(\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?)['\"]?\s*$",
        ],
        "core/scripts/pa.py": [],
        "ROADMAP.md": [
            r"^\*\*Versión actual\*\*:\s*v?(\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?)\s*$",
        ],
        "config/branding.txt": [],
    }

    results = {}
    for name in TARGETS:
        path = root / name
        detected = detect_version_in_file(path, patterns_by_target[name])
        results[name] = {
            "path": path,
            "detected": detected,
            "exists": path.exists(),
        }

    return results


def preview_changes(detected_versions: dict, new_version: str) -> list:
    """
    Generate preview of changes to be made.

    Args:
        detected_versions: Dict of detected versions per file.
        new_version: New version to apply.

    Returns:
        List of (file_name, old_version, new_version) tuples for files needing update.
    """
    changes = []

    for name, info in detected_versions.items():
        if not info["exists"]:
            continue
        if info["detected"] and info["detected"] != new_version:
            changes.append((name, info["detected"], new_version))

    return changes


def apply_changes(changes: list, new_version: str, dry_run: bool = False) -> int:
    """
    Apply version changes to files.

    Args:
        changes: List of files to update.
        new_version: New version to apply.
        dry_run: If True, don't write changes.

    Returns:
        Number of files updated.
    """
    if dry_run:
        print("[DRY RUN] No files will be modified.")
        return 0

    root = get_root_dir()
    updated = 0

    token = r"\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?"
    badge_version = new_version.replace("-", "--")
    file_replacements = {
        "README.md": [
            (
                rf"(https://img\.shields\.io/badge/version-v){token}(-lime)",
                lambda match: f"{match.group(1)}{badge_version}{match.group(2)}",
            ),
            (
                rf"^(Ver `CHANGELOG\.md`\. Versión actual: \*\*)v?{token}(\.\*\*)$",
                lambda match: f"{match.group(1)}v{new_version}{match.group(2)}",
            ),
        ],
        "AGENTS.md": [
            (
                rf"^(> \*\*Version: )v?{token}(\*\*.*)$",
                lambda match: f"{match.group(1)}v{new_version}{match.group(2)}",
            ),
        ],
        "dashboard.html": [
            (
                rf"(<title>PA Framework Command Center )v?{token}(</title>)",
                lambda match: f"{match.group(1)}v{new_version}{match.group(2)}",
            ),
            (
                rf"(<p class=\"text-xs text-slate-400\">)v?{token}( <span id=\"build-id\")",
                lambda match: f"{match.group(1)}v{new_version}{match.group(2)}",
            ),
            (
                rf"(Framework )v?{token}( — 100% Local, 100% Privado)",
                lambda match: f"{match.group(1)}v{new_version}{match.group(2)}",
            ),
        ],
        "config/framework.yaml": [
            (
                rf"^(\s*version:\s*)['\"]?v?{token}['\"]?(\s*(?:#.*)?)$",
                lambda match: f"{match.group(1)}{new_version}{match.group(2)}",
            ),
        ],
        "core/scripts/pa.py": [],
        "ROADMAP.md": [
            (
                rf"^(\*\*Versión actual\*\*:\s*)v?{token}(\s*)$",
                lambda match: f"{match.group(1)}v{new_version}{match.group(2)}",
            ),
        ],
        "config/branding.txt": [],
    }

    for file_name, old_ver, _ in changes:
        file_path = root / file_name

        if not file_path.exists():
            print(f"[WARN] File not found: {file_path}")
            continue

        content = file_path.read_text(encoding="utf-8")
        new_content = content

        if file_name in file_replacements:
            for pattern, replacement in file_replacements[file_name]:
                new_content = re.sub(
                    pattern, replacement, new_content, flags=re.MULTILINE
                )

        if new_content != content:
            file_path.write_text(new_content, encoding="utf-8")
            updated += 1
            print(f"[OK] Updated: {file_name}")

    return updated


def update_changelog(new_version: str, dry_run: bool = False) -> bool:
    """
    Add new version section to CHANGELOG.md.

    Args:
        new_version: New version to add.
        dry_run: If True, don't write changes.

    Returns:
        True if changelog was updated.
    """
    root = get_root_dir()
    changelog_path = root / "CHANGELOG.md"

    if not changelog_path.exists():
        print(f"[WARN] CHANGELOG.md not found at {changelog_path}")
        return False

    content = changelog_path.read_text(encoding="utf-8")

    if f"[{new_version}]" in content:
        print(f"[INFO] Version {new_version} already in CHANGELOG.md")
        return False

    today = date.today().isoformat()

    new_section = f"""---

## [{new_version}] - {today}

### Added / Agregado
- 

### Changed / Cambiado
- 

### Fixed / Corregido
- 

"""

    unreleased_match = re.search(r"## \[Unreleased\]", content)

    if unreleased_match:
        insert_pos = unreleased_match.end()
        new_content = content[:insert_pos] + "\n" + new_section + content[insert_pos:]
    else:
        first_version_match = re.search(r"## \[", content)
        if first_version_match:
            insert_pos = first_version_match.start()
            new_content = content[:insert_pos] + new_section + content[insert_pos:]
        else:
            new_content = content + "\n" + new_section

    if not dry_run:
        changelog_path.write_text(new_content, encoding="utf-8")
        print(f"[OK] Added version section to CHANGELOG.md")
        return True

    return False


def confirm_action(prompt: str, default: bool = True) -> bool:
    """
    Ask user for confirmation.

    Args:
        prompt: Prompt message.
        default: Default value if user just presses Enter.

    Returns:
        True if confirmed.
    """
    default_str = "Y/n" if default else "y/N"
    try:
        response = input(f"{prompt} [{default_str}]: ").strip().lower()
        if not response:
            return default
        return response in ("y", "yes", "s", "si")
    except EOFError:
        return default


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="PA Framework Version Updater",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without writing",
    )
    parser.add_argument(
        "--no-confirm",
        action="store_true",
        help="Skip confirmation prompts (for CI)",
    )
    parser.add_argument(
        "--version",
        type=str,
        help="Override VERSION file (for testing)",
    )
    parser.add_argument(
        "--changelog",
        action="store_true",
        help="Also add new version section to CHANGELOG.md",
    )

    args = parser.parse_args()

    root = get_root_dir()

    print("=" * 60)
    print("PA Framework - Version Updater")
    print("=" * 60)

    try:
        if args.version:
            new_version = normalize(args.version)
            print(f"[INFO] Using override version: {new_version}")
        else:
            new_version = get_current_version()
            print(f"[INFO] Version from VERSION file: {new_version}")
    except FileNotFoundError as e:
        print(f"[ERROR] {e}")
        return 1

    detected = detect_version_in_files()

    print(f"\nFiles to check:")
    for name, info in detected.items():
        status = info["detected"] if info["detected"] else "NOT FOUND"
        exists = "OK" if info["exists"] else "MISSING"
        print(f"  [{exists}] {name}: {status}")

    changes = preview_changes(detected, new_version)

    if not changes:
        print(f"\n[INFO] All files already at version {new_version}")
        return 0

    print(f"\nChanges needed:")
    for file_name, old_ver, new_ver in changes:
        print(f"  {file_name}:")
        print(f"    - {old_ver}")
        print(f"    + {new_ver}")

    if args.dry_run:
        print("\n[DRY RUN] Preview complete. No changes made.")
        return 0

    if not args.no_confirm:
        print()
        if not confirm_action("Preview changes?", default=True):
            print("[CANCELLED] No changes made.")
            return 0

        if not confirm_action("Apply changes?", default=True):
            print("[CANCELLED] No changes made.")
            return 0

    updated = apply_changes(changes, new_version)

    print(f"\n[OK] Updated {updated} file(s)")

    if args.changelog:
        update_changelog(new_version)
    else:
        print("[!] Don't forget to update CHANGELOG.md manually!")

    print("=" * 60)

    return 0


def self_test():
    """Self-test for version-updater module."""
    import tempfile

    print("Running self-tests...")

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        version_file = tmpdir / "VERSION"
        version_file.write_text("1.2.3-beta\n", encoding="utf-8")

        test_version = get_current_version(version_file)
        assert test_version == "1.2.3-beta", (
            f"Expected '1.2.3-beta', got '{test_version}'"
        )
        print("  [PASS] get_current_version()")

        test_md = tmpdir / "test.md"
        test_md.write_text("# Project v1.0.0\n", encoding="utf-8")

        detected = detect_version_in_file(test_md, [r"v(\d+\.\d+\.\d+[a-z0-9-]*)"])
        assert detected == "1.0.0", f"Expected '1.0.0', got '{detected}'"
        print("  [PASS] detect_version_in_file()")

        missing = tmpdir / "missing.md"
        detected = detect_version_in_file(missing, [r"v(\d+\.\d+\.\d+)"])
        assert detected is None, f"Expected None for missing file, got '{detected}'"
        print("  [PASS] detect_version_in_file() missing file")

    print("All self-tests passed!")


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        self_test()
        sys.exit(0)

    sys.exit(main())
