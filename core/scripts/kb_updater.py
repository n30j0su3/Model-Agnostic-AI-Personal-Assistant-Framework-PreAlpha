#!/usr/bin/env python3
"""
PA Framework — Knowledge Base Updater
=====================================
Updates Knowledge Base with new insights from mined session data.
Updates: insights/decisions.md, patterns.md, sessions-index.json

Usage:
    python core/scripts/kb-updater.py              # Update KB from last mined
    python core/scripts/kb-updater.py --input FILE # Use specific mined data
    python core/scripts/kb-updater.py --help      # Show this help

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
INSIGHTS_DIR = KNOWLEDGE_DIR / "insights"
SESSIONS_INDEX = KNOWLEDGE_DIR / "sessions-index.json"


def ensure_dirs():
    """Ensure required directories exist."""
    INSIGHTS_DIR.mkdir(parents=True, exist_ok=True)


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


def update_decisions(insights_dir: Path, mined: Dict) -> bool:
    """Update insights/decisions.md with new decisions."""
    decisions_file = insights_dir / "decisions.md"

    # Load existing content
    if decisions_file.exists():
        content = decisions_file.read_text(encoding="utf-8")
    else:
        content = "# Decisions Log\n\n> Auto-generated from session mining.\n\n"

    decisions = mined.get("decisions", [])
    if not decisions:
        return False

    date = mined.get("date", datetime.now().strftime("%Y-%m-%d"))

    # Check if decisions for this date already exist
    if f"## {date}" in content and all(d['text'][:30] in content for d in decisions[:2]):
        return False  # Already updated

    new_entries = []
    new_entries.append(f"\n## {date}\n")

    for decision in decisions:
        text = decision.get("text", "")
        if text:
            new_entries.append(f"- {text}\n")

    if len(new_entries) > 1:
        content += "\n".join(new_entries)
        try:
            decisions_file.write_text(content, encoding="utf-8")
            return True
        except Exception as e:
            print(f"[WARN] Failed to update decisions.md: {e}")
            return False

    return False


def update_patterns(insights_dir: Path, mined: Dict) -> bool:
    """Update insights/patterns.md with new patterns."""
    patterns_file = insights_dir / "patterns.md"

    # Load existing content
    if patterns_file.exists():
        content = patterns_file.read_text(encoding="utf-8")
    else:
        content = "# Patterns Log\n\n> Auto-generated from session mining.\n\n"

    patterns = mined.get("patterns", [])
    if not patterns:
        return False

    date = mined.get("date", datetime.now().strftime("%Y-%m-%d"))

    # Check if patterns for this date already exist
    if f"## {date}" in content:
        return False

    new_entries = []
    new_entries.append(f"\n## {date}\n")

    for pattern in patterns:
        category = pattern.get("category", "unknown")
        text = pattern.get("pattern", "")
        if text:
            new_entries.append(f"- **[{category}]**: {text}\n")

    if len(new_entries) > 1:
        content += "\n".join(new_entries)
        try:
            patterns_file.write_text(content, encoding="utf-8")
            return True
        except Exception as e:
            print(f"[WARN] Failed to update patterns.md: {e}")
            return False

    return False


def update_sessions_index(sessions_index: Path, mined: Dict) -> bool:
    """Update sessions-index.json with new topics and decisions."""
    # Load existing index
    if sessions_index.exists():
        try:
            index = json.loads(sessions_index.read_text(encoding="utf-8"))
        except Exception:
            index = {"sessions": [], "total_sessions": 0}
    else:
        index = {"sessions": [], "total_sessions": 0}

    date = mined.get("date", datetime.now().strftime("%Y-%m-%d"))

    # Check if this session is already in index
    session_id = date
    session_exists = False
    for s in index.get("sessions", []):
        if s.get("id") == session_id or s.get("date") == date:
            session_exists = True
            # Update existing
            s["topics"] = mined.get("topics", [])
            s["decisions"] = [d["text"] for d in mined.get("decisions", [])[:5]]
            s["pending"] = [p["text"] for p in mined.get("pending", [])[:10]]
            s["highlights"] = [h["text"] for h in mined.get("highlights", [])[:5]]
            s["stats"] = mined.get("stats", {})
            s["mined_at"] = datetime.now().isoformat()
            break

    if not session_exists:
        # Create new session entry
        session_entry = {
            "id": session_id,
            "date": date,
            "title": f"Session {date}",
            "topics": mined.get("topics", []),
            "decisions": [d["text"] for d in mined.get("decisions", [])[:5]],
            "pending": [p["text"] for p in mined.get("pending", [])[:10]],
            "highlights": [h["text"] for h in mined.get("highlights", [])[:5]],
            "stats": mined.get("stats", {}),
            "mined_at": datetime.now().isoformat(),
        }

        # Add to beginning
        if "sessions" not in index:
            index["sessions"] = []
        index["sessions"].insert(0, session_entry)

    # Update metadata
    index["total_sessions"] = len(index.get("sessions", []))
    index["last_updated"] = datetime.now().isoformat()

    # Update filters/by_topic
    if "filters" not in index:
        index["filters"] = {"by_topic": {}, "by_type": {}}
    if "by_topic" not in index["filters"]:
        index["filters"]["by_topic"] = {}

    for topic in mined.get("topics", []):
        if topic not in index["filters"]["by_topic"]:
            index["filters"]["by_topic"][topic] = []
        if date not in index["filters"]["by_topic"][topic]:
            index["filters"]["by_topic"][topic].append(date)

    # Save
    try:
        sessions_index.write_text(
            json.dumps(index, indent=2, ensure_ascii=False),
            encoding="utf-8"
        )
        return True
    except Exception as e:
        print(f"[WARN] Failed to update sessions-index.json: {e}")
        return False


def update_learnings(insights_dir: Path, mined: Dict) -> bool:
    """Update insights/learnings.md with new learnings."""
    learnings_file = insights_dir / "learnings.md"

    # Load existing content
    if learnings_file.exists():
        content = learnings_file.read_text(encoding="utf-8")
    else:
        content = "# Learnings Log\n\n> Auto-generated from session mining.\n\n"

    learnings = mined.get("learnings", [])
    if not learnings:
        return False

    date = mined.get("date", datetime.now().strftime("%Y-%m-%d"))

    new_entries = []
    new_entries.append(f"\n## {date}\n")

    for learning in learnings:
        text = learning.get("text", "")
        if text:
            new_entries.append(f"- {text}\n")

    if len(new_entries) > 1:
        content += "\n".join(new_entries)
        try:
            learnings_file.write_text(content, encoding="utf-8")
            return True
        except Exception as e:
            print(f"[WARN] Failed to update learnings.md: {e}")
            return False

    return False


def update_pending_items(insights_dir: Path, mined: Dict) -> bool:
    """Update insights/pending.md with pending items from session."""
    pending_file = insights_dir / "pending.md"

    pending = mined.get("pending", [])
    if not pending:
        return False

    # Load existing
    if pending_file.exists():
        content = pending_file.read_text(encoding="utf-8")
    else:
        content = "# Pending Items\n\n> Auto-generated from session mining.\n\n"

    date = mined.get("date", datetime.now().strftime("%Y-%m-%d"))

    new_entries = []
    new_entries.append(f"\n## {date}\n")

    for item in pending:
        text = item.get("text", "")
        if text:
            new_entries.append(f"- [ ] {text}\n")

    if len(new_entries) > 1:
        content += "\n".join(new_entries)
        try:
            pending_file.write_text(content, encoding="utf-8")
            return True
        except Exception as e:
            print(f"[WARN] Failed to update pending.md: {e}")
            return False

    return False


def update_kb(mined: Optional[Dict] = None) -> Dict:
    """
    Update all Knowledge Base files from mined data.
    Returns stats about what was updated.
    """
    if mined is None:
        mined = load_mined_data()
        if mined is None:
            print("[ERROR] No mined data available")
            return {"success": False}

    ensure_dirs()

    stats = {
        "decisions_updated": False,
        "patterns_updated": False,
        "learnings_updated": False,
        "pending_updated": False,
        "sessions_index_updated": False,
    }

    stats["decisions_updated"] = update_decisions(INSIGHTS_DIR, mined)
    stats["patterns_updated"] = update_patterns(INSIGHTS_DIR, mined)
    stats["learnings_updated"] = update_learnings(INSIGHTS_DIR, mined)
    stats["pending_updated"] = update_pending_items(INSIGHTS_DIR, mined)
    stats["sessions_index_updated"] = update_sessions_index(SESSIONS_INDEX, mined)

    return stats


def print_summary(stats: Dict):
    """Print summary of KB updates."""
    print("\n" + "=" * 50)
    print("Knowledge Base Update Summary")
    print("=" * 50)

    updates = [k for k, v in stats.items() if v]
    if not updates:
        print("\nNo updates needed (data already current).")
    else:
        print(f"\nUpdated ({len(updates)}):")
        for key in updates:
            print(f"  - {key}")

    print("\n" + "=" * 50)


def main():
    parser = argparse.ArgumentParser(
        description="PA Framework Knowledge Base Updater - Update KB from mined knowledge"
    )
    parser.add_argument(
        "--input",
        type=str,
        default=None,
        help="Path to mined data JSON file. Default: last_mined.json"
    )

    args = parser.parse_args()

    input_path = Path(args.input) if args.input else None
    mined = load_mined_data(input_path)

    if mined is None:
        print("[ERROR] No mined data found. Run knowledge-miner.py first.")
        sys.exit(1)

    stats = update_kb(mined)
    print_summary(stats)

    if any(stats.values()):
        print("\n[OK] Knowledge Base updated successfully.")


if __name__ == "__main__":
    main()
