#!/usr/bin/env python3
"""
memory-sync.py — PA Framework LLM-Wiki Health Check

Purpose:
    - Creates missing directory structure for wiki
    - Validates wiki schema compliance
    - Reports wiki health status

This is a Python-only solution with no external CLI dependencies.
Engram has been removed (was requiring external npm CLI).
"""

import os
import sys
import yaml
from pathlib import Path
from datetime import datetime

# Constants
FRAMEWORK_ROOT = Path(__file__).parent.parent.parent
WIKI_ROOT = FRAMEWORK_ROOT / "core" / ".context" / "knowledge" / "wiki"
SCHEMA_PATH = WIKI_ROOT / "SCHEMA.md"

# Required wiki structure
REQUIRED_DIRS = [
    WIKI_ROOT / "raw" / "inputs",
    WIKI_ROOT / "raw" / "observations",
    WIKI_ROOT / "raw" / "extracts",
    WIKI_ROOT / "entities",
    WIKI_ROOT / "concepts",
    WIKI_ROOT / "comparisons",
    WIKI_ROOT / "queries",
]

# Required frontmatter fields
REQUIRED_FRONTMATTER = ["title", "type", "tags", "created"]
VALID_TYPES = ["entity", "concept", "comparison", "query", "raw"]
MAX_SUMMARY_LENGTH = 100


class Colors:
    # Windows-safe ASCII markers (no ANSI codes)
    GREEN = "[+]"
    RED = "[-]"
    YELLOW = "[!]"
    BLUE = "[*]"
    RESET = ""


def log(msg, color=None):
    if color:
        print(f"{color}{msg}{Colors.RESET}")
    else:
        print(msg)


def log_header(msg):
    log(f"\n{'=' * 60}", Colors.BLUE)
    log(f"  {msg}", Colors.BLUE)
    log(f"{'=' * 60}\n", Colors.BLUE)


def log_status(name, status, details=""):
    symbol = "[OK]" if status else "[X]"
    color = Colors.GREEN if status else Colors.RED
    log(f"  [{symbol}] {name}", color)
    if details:
        log(f"      {details}", Colors.YELLOW if not status else None)


def ensure_directory_structure():
    """Create missing directories for wiki."""
    log_header("Wiki Directory Structure Check")
    
    all_exist = True
    for dir_path in REQUIRED_DIRS:
        exists = dir_path.exists()
        status = "exists" if exists else "CREATED"
        if not exists:
            dir_path.mkdir(parents=True, exist_ok=True)
            all_exist = False
        log_status(str(dir_path.relative_to(FRAMEWORK_ROOT)), True if exists else True, status)
    
    # Check for gitkeep in empty dirs
    for dir_path in REQUIRED_DIRS:
        gitkeep = dir_path / ".gitkeep"
        if dir_path.exists() and not list(dir_path.iterdir()):
            if not gitkeep.exists():
                gitkeep.touch()
                log_status(f".gitkeep in {dir_path.name}", True, "created")
            else:
                log_status(f".gitkeep in {dir_path.name}", True, "present")
    
    return True


def validate_frontmatter(file_path):
    """Validate frontmatter of a wiki page."""
    errors = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        return [f"Cannot read file: {e}"]
    
    # Check for frontmatter
    if not content.startswith('---'):
        return ["Missing frontmatter (no --- at start)"]
    
    # Extract frontmatter
    parts = content.split('---', 2)
    if len(parts) < 3:
        return ["Malformed frontmatter"]
    
    try:
        fm = yaml.safe_load(parts[1])
        if not isinstance(fm, dict):
            return ["Frontmatter is not a YAML dict"]
    except yaml.YAMLError as e:
        return [f"Invalid YAML: {e}"]
    
    # Check required fields
    for field in REQUIRED_FRONTMATTER:
        if field not in fm:
            errors.append(f"Missing required field: {field}")
    
    # Validate type
    if 'type' in fm and fm['type'] not in VALID_TYPES:
        errors.append(f"Invalid type '{fm['type']}'. Must be one of: {VALID_TYPES}")
    
    # Check summary length
    if 'summary' in fm and len(str(fm['summary'])) > MAX_SUMMARY_LENGTH:
        errors.append(f"Summary exceeds {MAX_SUMMARY_LENGTH} chars")
    
    # Check tags format
    if 'tags' in fm:
        if not isinstance(fm['tags'], list):
            errors.append("Tags must be a list")
    
    return errors


def validate_wiki_schema():
    """Validate wiki pages against schema."""
    log_header("Wiki Schema Validation")
    
    total_pages = 0
    valid_pages = 0
    error_pages = []
    
    # Find all markdown files in wiki (except SCHEMA.md, index.md, log.md)
    for md_file in WIKI_ROOT.rglob("*.md"):
        # Skip special files
        if md_file.name in ["SCHEMA.md", "index.md", "log.md"]:
            continue
        # Skip if in root wiki dir (only subdirectories)
        if md_file.parent == WIKI_ROOT:
            continue
        
        total_pages += 1
        errors = validate_frontmatter(md_file)
        
        if errors:
            error_pages.append((md_file, errors))
            rel_path = str(md_file.relative_to(FRAMEWORK_ROOT))
            log_status(rel_path, False, "; ".join(errors[:2]))
        else:
            valid_pages += 1
            rel_path = str(md_file.relative_to(FRAMEWORK_ROOT))
            log_status(rel_path, True)
    
    if total_pages == 0:
        log("  No wiki pages to validate (empty wiki)", Colors.YELLOW)
        return True
    
    # Summary
    log(f"\n  Pages validated: {total_pages}")
    log(f"  Valid pages: {valid_pages}", Colors.GREEN if valid_pages == total_pages else Colors.YELLOW)
    if error_pages:
        log(f"  Pages with errors: {len(error_pages)}", Colors.RED)
    else:
        log(f"  Pages with errors: 0", Colors.GREEN)
    
    return len(error_pages) == 0


def report_health():
    """Generate overall health report."""
    log_header("LLM-Wiki Health Report")
    
    # Directory structure
    all_dirs_exist = all(d.exists() for d in REQUIRED_DIRS)
    log_status("Wiki directory structure", all_dirs_exist)
    
    # Schema file
    schema_exists = SCHEMA_PATH.exists()
    log_status("Wiki SCHEMA.md", schema_exists)
    
    # Count wiki pages
    wiki_pages = list(WIKI_ROOT.rglob("*.md"))
    wiki_pages = [p for p in wiki_pages if p.parent != WIKI_ROOT or p.name in ["SCHEMA.md", "index.md", "log.md"]]
    if WIKI_ROOT in wiki_pages:
        wiki_pages.remove(WIKI_ROOT)
    log_status(f"Wiki pages total", True, str(len(wiki_pages)))
    
    # Calculate approximate size
    total_size = 0
    for p in WIKI_ROOT.rglob("*"):
        if p.is_file():
            total_size += p.stat().st_size
    
    size_kb = total_size / 1024
    size_mb = size_kb / 1024
    
    log(f"\n  Total wiki footprint: {size_kb:.1f} KB ({size_mb:.2f} MB)")
    
    if size_mb < 10:
        log(f"  Status: EXCELLENT (target: <50MB)", Colors.GREEN)
    elif size_mb < 25:
        log(f"  Status: GOOD (target: <50MB)", Colors.GREEN)
    elif size_mb < 50:
        log(f"  Status: ACCEPTABLE (target: <50MB)", Colors.YELLOW)
    else:
        log(f"  Status: WARNING - exceeds 50MB target", Colors.RED)
    
    return True


def main():
    """Main entry point."""
    log_header("PA Framework LLM-Wiki Sync")
    log(f"Framework root: {FRAMEWORK_ROOT}")
    log(f"Wiki root: {WIKI_ROOT}")
    log(f"Timestamp: {datetime.now().isoformat()}")
    
    # Run checks
    ensure_directory_structure()
    validate_wiki_schema()
    report_health()
    
    log_header("Check Complete")
    log("LLM-Wiki is ready.")
    log("\nNote: This script validates structure only.")
    log("Full sync is handled by Python scripts.")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
