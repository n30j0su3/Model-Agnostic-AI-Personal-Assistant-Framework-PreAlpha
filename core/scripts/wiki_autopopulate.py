#!/usr/bin/env python3
"""
PA Framework — Wiki Auto-Populate
================================
Auto-populates LLM-Wiki from extracted knowledge.
Reads knowledge-miner output and creates wiki pages following SCHEMA.md format.

Wiki Types: entity, concept, comparison, query, raw
Directories: entities/, concepts/, comparisons/, queries/, raw/

Usage:
    python core/scripts/wiki-autopopulate.py              # Auto-populate from last mined
    python core/scripts/wiki-autopopulate.py --input FILE # Use specific mined data
    python core/scripts/wiki-autopopulate.py --help      # Show this help

Schema:
    ---
    title: "Concept Name"
    type: concept  # entity, concept, comparison, query, raw
    tags: [learning, session, topic]
    created: 2026-04-15
    summary: "Brief description (max 100 chars)"
    ---
    Content here...

Autor: FreakingJSON-PA Framework
Version: 1.0.0
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# Paths
SCRIPT_DIR = Path(__file__).resolve().parent
CORE_DIR = SCRIPT_DIR.parent
REPO_ROOT = CORE_DIR.parent
CONTEXT_DIR = CORE_DIR / ".context"
KNOWLEDGE_DIR = CONTEXT_DIR / "knowledge"

# Wiki directories
WIKI_BASE = KNOWLEDGE_DIR / "wiki"
WIKI_ENTITIES = WIKI_BASE / "entities"
WIKI_CONCEPTS = WIKI_BASE / "concepts"
WIKI_COMPARISONS = WIKI_BASE / "comparisons"
WIKI_QUERIES = WIKI_BASE / "queries"
WIKI_RAW = WIKI_BASE / "raw"


def ensure_wiki_dirs():
    """Ensure all wiki directories exist."""
    for d in [WIKI_BASE, WIKI_ENTITIES, WIKI_CONCEPTS, WIKI_COMPARISONS, WIKI_QUERIES, WIKI_RAW]:
        d.mkdir(parents=True, exist_ok=True)


def sanitize_filename(name: str) -> str:
    """Convert a title to a safe filename."""
    # Remove/replace unsafe characters
    name = re.sub(r'[<>:"/\\|?*]', "_", name)
    name = re.sub(r"\s+", "_", name)
    name = name[:50]  # Limit length
    return name.lower()


def generate_summary(text: str, max_len: int = 100) -> str:
    """Generate a brief summary from text."""
    if not text:
        return ""
    # Clean markdown
    text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
    text = re.sub(r"\*([^*]+)\*", r"\1", text)
    text = re.sub(r"`([^`]+)`", r"\1", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    # Take first sentence or first N chars
    sentences = re.split(r"[.!?]", text)
    if sentences and sentences[0].strip():
        summary = sentences[0].strip()
    else:
        summary = text[:max_len]
    # Truncate
    if len(summary) > max_len:
        summary = summary[:max_len - 3] + "..."
    return summary


def create_wiki_entry(
    title: str,
    wiki_type: str,
    content: str,
    tags: List[str],
    summary: str = ""
) -> Dict:
    """
    Create a wiki entry following the schema.
    Returns the entry metadata.
    """
    if not summary:
        summary = generate_summary(content)

    date = datetime.now().strftime("%Y-%m-%d")

    # Build frontmatter
    frontmatter = f"""---
title: "{title}"
type: {wiki_type}
tags: [{', '.join(tags)}]
created: {date}
summary: "{summary}"
---

"""

    # Build full content
    full_content = frontmatter + content

    return {
        "title": title,
        "type": wiki_type,
        "tags": tags,
        "created": date,
        "summary": summary,
        "content": full_content,
    }


def save_wiki_entry(entry: Dict) -> Optional[Path]:
    """Save a wiki entry to the appropriate directory."""
    wiki_type = entry["type"]
    title = entry["title"]

    # Select directory
    type_dirs = {
        "entity": WIKI_ENTITIES,
        "concept": WIKI_CONCEPTS,
        "comparison": WIKI_COMPARISONS,
        "query": WIKI_QUERIES,
        "raw": WIKI_RAW,
    }

    target_dir = type_dirs.get(wiki_type, WIKI_RAW)
    if wiki_type not in type_dirs:
        target_dir = WIKI_RAW

    # Generate filename
    base_name = sanitize_filename(title)
    file_path = target_dir / f"{base_name}.md"

    # Handle duplicates
    counter = 1
    while file_path.exists():
        file_path = target_dir / f"{base_name}_{counter}.md"
        counter += 1

    # Write file
    try:
        file_path.write_text(entry["content"], encoding="utf-8")
        return file_path
    except Exception as e:
        print(f"[WARN] Failed to save wiki entry '{title}': {e}")
        return None


def ideas_to_wiki_entries(mined: Dict) -> List[Dict]:
    """Convert ideas from mined data to wiki entries."""
    entries = []

    for idea in mined.get("ideas", []):
        title = idea.get("title", "Untitled Idea")
        content = idea.get("content", "")

        entry = create_wiki_entry(
            title=title,
            wiki_type="concept",
            content=content,
            tags=["idea", "session", "learning"],
        )
        entries.append(entry)

    return entries


def decisions_to_wiki_entries(mined: Dict) -> List[Dict]:
    """Convert decisions from mined data to wiki entries."""
    entries = []

    # Group decisions by topic or date
    decisions = mined.get("decisions", [])
    if decisions:
        # Create a consolidated decisions entry
        content_lines = [f"## Decisions from {mined['date']}\n"]
        for d in decisions:
            content_lines.append(f"- {d['text']}")

        entry = create_wiki_entry(
            title=f"Decisions {mined['date']}",
            wiki_type="entity",
            content="\n".join(content_lines),
            tags=["decisions", "session"],
        )
        entries.append(entry)

    return entries


def patterns_to_wiki_entries(mined: Dict) -> List[Dict]:
    """Convert patterns from mined data to wiki entries."""
    entries = []

    for pattern in mined.get("patterns", []):
        category = pattern.get("category", "unknown")
        pattern_text = pattern.get("pattern", "")

        title = f"Pattern: {category.title()}"
        content = f"""## Pattern Detected

**Category**: {category}
**Date**: {pattern.get('date', 'unknown')}
**Pattern**: {pattern_text}

## Context

This pattern was automatically extracted from session mining.

### Related Topics
{', '.join(mined.get('topics', []))}
"""

        entry = create_wiki_entry(
            title=title,
            wiki_type="concept",
            content=content,
            tags=["pattern", "learning", category],
        )
        entries.append(entry)

    return entries


def learnings_to_wiki_entries(mined: Dict) -> List[Dict]:
    """Convert learnings from mined data to wiki entries."""
    entries = []

    for learning in mined.get("learnings", []):
        text = learning.get("text", "")
        if not text:
            continue

        entry = create_wiki_entry(
            title=f"Learning: {text[:40]}...",
            wiki_type="concept",
            content=f"""## Learning

**Date**: {learning.get('date', 'unknown')}

{text}

## Related Topics
{', '.join(mined.get('topics', []))}
""",
            tags=["learning", "session"],
        )
        entries.append(entry)

    return entries


def topics_to_wiki_entries(mined: Dict) -> List[Dict]:
    """Convert topics from mined data to wiki entries (entity pages)."""
    entries = []

    for topic in mined.get("topics", []):
        title = topic.replace("-", " ").title()

        # Skip if too generic
        if len(title) < 3:
            continue

        content = f"""## Topic: {title}

**First Seen**: {mined['date']}
**Type**: Entity

### Session History
- {mined['date']}: Topic discussed in session

### Related
{', '.join([t for t in mined.get('topics', []) if t != topic])}
"""

        entry = create_wiki_entry(
            title=title,
            wiki_type="entity",
            content=content,
            tags=["topic", "entity", "session"],
        )
        entries.append(entry)

    return entries


def load_mined_data(input_file: Optional[Path] = None) -> Optional[Dict]:
    """Load mined data from file."""
    if input_file is None:
        input_file = KNOWLEDGE_DIR / "last_mined.json"

    if not input_file.exists():
        return None

    try:
        return json.loads(input_file.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"[WARN] Failed to load mined data: {e}")
        return None


def autopopulate(mined: Optional[Dict] = None) -> List[Dict]:
    """
    Auto-populate wiki from mined data.
    Returns list of created entries.
    """
    if mined is None:
        mined = load_mined_data()
        if mined is None:
            print("[ERROR] No mined data available")
            return []

    ensure_wiki_dirs()

    all_entries = []

    # Convert all types
    all_entries.extend(ideas_to_wiki_entries(mined))
    all_entries.extend(decisions_to_wiki_entries(mined))
    all_entries.extend(patterns_to_wiki_entries(mined))
    all_entries.extend(learnings_to_wiki_entries(mined))
    all_entries.extend(topics_to_wiki_entries(mined))

    # Save entries
    created = []
    for entry in all_entries:
        path = save_wiki_entry(entry)
        if path:
            created.append({
                "title": entry["title"],
                "type": entry["type"],
                "path": str(path),
            })

    return created


def print_summary(created: List[Dict]):
    """Print summary of created wiki entries."""
    print("\n" + "=" * 50)
    print("Wiki Auto-Populate Summary")
    print("=" * 50)

    if not created:
        print("\nNo new entries created.")
        return

    # Group by type
    by_type = {}
    for entry in created:
        wiki_type = entry["type"]
        if wiki_type not in by_type:
            by_type[wiki_type] = []
        by_type[wiki_type].append(entry["title"])

    print(f"\nTotal Created: {len(created)}")
    for wiki_type, titles in by_type.items():
        print(f"\n{wiki_type.title()} ({len(titles)}):")
        for title in titles[:5]:
            print(f"  - {title[:50]}...")
        if len(titles) > 5:
            print(f"  ... and {len(titles) - 5} more")

    print("\n" + "=" * 50)


def main():
    parser = argparse.ArgumentParser(
        description="PA Framework Wiki Auto-Populate - Create wiki pages from mined knowledge"
    )
    parser.add_argument(
        "--input",
        type=str,
        default=None,
        help="Path to mined data JSON file. Default: last_mined.json"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be created without creating files."
    )

    args = parser.parse_args()

    input_path = Path(args.input) if args.input else None

    mined = load_mined_data(input_path)
    if mined is None:
        print("[ERROR] No mined data found. Run knowledge-miner.py first.")
        sys.exit(1)

    if args.dry_run:
        # Just show what would be created
        entries = (
            ideas_to_wiki_entries(mined) +
            decisions_to_wiki_entries(mined) +
            patterns_to_wiki_entries(mined) +
            learnings_to_wiki_entries(mined) +
            topics_to_wiki_entries(mined)
        )
        print(f"\nWould create {len(entries)} wiki entries:")
        for e in entries:
            print(f"  [{e['type']}] {e['title'][:50]}...")
        return

    created = autopopulate(mined)
    print_summary(created)

    if created:
        print(f"\n[OK] Wiki auto-populate complete. {len(created)} entries created.")


if __name__ == "__main__":
    main()
