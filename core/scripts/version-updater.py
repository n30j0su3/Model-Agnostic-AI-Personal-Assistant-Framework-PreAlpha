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

    content = version_path.read_text(encoding="utf-8").strip()
    return content


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
        match = re.search(pattern, content)
        if match:
            return match.group(1)

    return None


def detect_version_in_files() -> dict:
    """
    Detect versions in all tracked files.

    Returns:
        Dict with file paths as keys and detected versions as values.
    """
    root = get_root_dir()

    file_patterns = {
        "README.md": {
            "path": root / "README.md",
            "patterns": [
                r"v(\d+\.\d+\.\d+[a-z0-9-]*)",  # Badge URL or text
            ],
        },
        "AGENTS.md": {
            "path": root / "AGENTS.md",
            "patterns": [
                r"Version: v(\d+\.\d+\.\d+[a-z0-9-]*)",
                r"Framework v(\d+\.\d+\.\d+[a-z0-9-]*)",
                r"v(\d+\.\d+\.\d+[a-z0-9-]*)",
            ],
        },
        "dashboard.html": {
            "path": root / "dashboard.html",
            "patterns": [
                r"v(\d+\.\d+\.\d+[a-z0-9-]*)",
            ],
        },
        "config/framework.yaml": {
            "path": root / "config" / "framework.yaml",
            "patterns": [
                r"^version:\s*['\"]?(\d+\.\d+\.\d+[a-z0-9-]*)['\"]?",
                r"# Version:\s*(\d+\.\d+\.\d+[a-z0-9-]*)",
            ],
        },
        "core/scripts/pa.py": {
            "path": root / "core" / "scripts" / "pa.py",
            "patterns": [
                r"Pre-Alpha (\d+\.\d+\.\d+[a-z0-9-]*)",
                r"v(\d+\.\d+\.\d+[a-z0-9-]*)",
                r'version = "(\d+\.\d+\.\d+[a-z0-9-]*)"',
            ],
        },
        "ROADMAP.md": {
            "path": root / "ROADMAP.md",
            "patterns": [
                r"v(\d+\.\d+\.\d+[a-z0-9-]*)",
                r"Versión actual.*?v(\d+\.\d+\.\d+[a-z0-9-]*)",
            ],
        },
        "README-technical.md": {
            "path": root / "README-technical.md",
            "patterns": [
                r"v(\d+\.\d+\.\d+[a-z0-9-]*)",
                r"release-v(\d+\.\d+\.\d+[a-z0-9-]*)",
            ],
        },
        "GEMINI.md": {
            "path": root / "GEMINI.md",
            "patterns": [
                r"v(\d+\.\d+\.\d+[a-z0-9-]*)",
                r"Framework.*?v(\d+\.\d+\.\d+[a-z0-9-]*)",
            ],
        },
        "config/branding.txt": {
            "path": root / "config" / "branding.txt",
            "patterns": [
                r"v(\d+\.\d+\.\d+[a-z0-9-]*)",
            ],
        },
    }

    results = {}
    for name, config in file_patterns.items():
        detected = detect_version_in_file(config["path"], config["patterns"])
        results[name] = {
            "path": config["path"],
            "detected": detected,
            "exists": config["path"].exists(),
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

    file_replacements = {
        "README.md": [
            (r"v\d+\.\d+\.\d+[a-z0-9-]*", f"v{new_version}"),
        ],
        "AGENTS.md": [
            (r"Framework v\d+\.\d+\.\d+[a-z0-9-]*", f"Framework v{new_version}"),
        ],
        "dashboard.html": [
            (r"v\d+\.\d+\.\d+[a-z0-9-]*", f"v{new_version}"),
        ],
        "config/framework.yaml": [
            (r"(# Version:)\s*\d+\.\d+\.\d+[a-z0-9-]*", f"\\1 {new_version}"),
        ],
        "core/scripts/pa.py": [
            (r"Pre-Alpha \d+\.\d+\.\d+[a-z0-9-]*", f"Pre-Alpha {new_version}"),
            (r"v\d+\.\d+\.\d+[a-z0-9-]*", f"v{new_version}"),
            (r'version = "\d+\.\d+\.\d+[a-z0-9-]*"', f'version = "{new_version}"'),
        ],
        "ROADMAP.md": [
            (r"v\d+\.\d+\.\d+[a-z0-9-]*", f"v{new_version}"),
        ],
        "README-technical.md": [
            (r"v\d+\.\d+\.\d+[a-z0-9-]*", f"v{new_version}"),
            (r"release-v\d+\.\d+\.\d+[a-z0-9-]*", f"release-v{new_version}"),
        ],
        "GEMINI.md": [
            (r"Framework v\d+\.\d+\.\d+[a-z0-9-]*", f"Framework v{new_version}"),
            (r"v\d+\.\d+\.\d+[a-z0-9-]*", f"v{new_version}"),
        ],
        "config/branding.txt": [
            (r"v\d+\.\d+\.\d+[a-z0-9-]*", f"v{new_version}"),
        ],
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
                new_content = re.sub(pattern, replacement, new_content)

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
            new_version = args.version
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
