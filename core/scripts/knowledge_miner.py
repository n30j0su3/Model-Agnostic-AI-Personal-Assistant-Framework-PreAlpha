#!/usr/bin/env python3
"""
PA Framework — Knowledge Miner
==============================
Extracts structured knowledge from session content using pure Python text processing.
No external AI APIs - pure heuristic-based extraction.

Usage:
    python core/scripts/knowledge-miner.py              # Mine today's session
    python core/scripts/knowledge-miner.py --date DATE  # Mine specific date
    python core/scripts/knowledge-miner.py --help       # Show this help

Output:
    - ideas.md update
    - Console output with extracted knowledge
    - Returns structured dict for wiki-autopopulate.py

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
from typing import Dict, List, Optional, Tuple

# Paths
SCRIPT_DIR = Path(__file__).resolve().parent
CORE_DIR = SCRIPT_DIR.parent
REPO_ROOT = CORE_DIR.parent
CONTEXT_DIR = CORE_DIR / ".context"
SESSIONS_DIR = CONTEXT_DIR / "sessions"
CODEBASE_DIR = CONTEXT_DIR / "codebase"
KNOWLEDGE_DIR = CONTEXT_DIR / "knowledge"


def get_session_file(date: Optional[str] = None) -> Optional[Path]:
    """Get session file for given date or today."""
    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")
    session_file = SESSIONS_DIR / f"{date}.md"
    return session_file if session_file.exists() else None


def read_session_content(session_file: Path) -> str:
    """Read session file content."""
    return session_file.read_text(encoding="utf-8")


def extract_ideas(content: str) -> List[Dict]:
    """Extract ideas from session content."""
    ideas = []

    # Look for idea patterns
    patterns = [
        r"(?:idea|idear|nueva?\s+idea)[:\s]+(.+?)(?:\n\n|\Z)",
        r"##\s+Ideas.*?\n(.+?)(?=\n##|\Z)",
        r"###\s+\d{4}-\d{2}-\d{2}.*?(?:idea|hallazgo)[:\s]*\n(.+?)(?=\n---|\n###|\Z)",
    ]

    for pattern in patterns:
        matches = re.findall(pattern, content, re.IGNORECASE | re.DOTALL)
        for m in matches:
            text = m.strip()
            if len(text) > 10 and len(text) < 500:
                # Extract title (first line or first sentence)
                lines = text.split("\n")
                title = lines[0].strip()[:80]
                # Clean markdown
                title = re.sub(r"\*\*(.+?)\*\*", r"\1", title)
                title = re.sub(r"\[(.+?)\]\(.+?\)", r"\1", title)

                ideas.append({
                    "title": title,
                    "content": text[:500],
                    "type": "idea",
                    "date": datetime.now().strftime("%Y-%m-%d"),
                })

    # Deduplicate by title
    seen = set()
    unique = []
    for idea in ideas:
        if idea["title"] not in seen:
            seen.add(idea["title"])
            unique.append(idea)

    return unique[:10]


def extract_decisions(content: str) -> List[Dict]:
    """Extract decisions from session content."""
    decisions = []

    patterns = [
        r"(?:decidimos|decisión|aprobado|implementar)[:\s]+(.+?)(?:\n\n|\Z)",
        r"##\s+Decisiones.*?\n(.+?)(?=\n##|\Z)",
        r"(?:^\d+\.\s*.+?(?:decisión|decidimos|aprobado|implementar).+?$)",
    ]

    for pattern in patterns:
        matches = re.findall(pattern, content, re.IGNORECASE | re.MULTILINE)
        for m in matches[:5]:
            text = m.strip()
            if len(text) > 5 and len(text) < 300:
                # Clean
                text = re.sub(r"^\d+\.\s*", "", text)
                text = re.sub(r"\*\*", "", text)

                decisions.append({
                    "text": text[:200],
                    "type": "decision",
                    "date": datetime.now().strftime("%Y-%m-%d"),
                })

    # Deduplicate
    seen = set()
    unique = []
    for d in decisions:
        if d["text"] not in seen and len(d["text"]) > 10:
            seen.add(d["text"])
            unique.append(d)

    return unique[:10]


def extract_patterns(content: str) -> List[Dict]:
    """Extract patterns from session content."""
    patterns_found = []

    # Look for error patterns and fixes
    error_fix_patterns = [
        (r"(?:error|bug|fallo)[:\s]+(.+?)(?:\n\n|\Z)", "error"),
        (r"(?:fix|solución|corrección)[:\s]+(.+?)(?:\n\n|\Z)", "solution"),
        (r"(?:root\s*cause|causa\s*raíz)[:\s]+(.+?)(?:\n\n|\Z)", "root_cause"),
    ]

    for pattern, ptype in error_fix_patterns:
        matches = re.findall(pattern, content, re.IGNORECASE | re.DOTALL)
        for m in matches[:3]:
            text = m.strip()
            if len(text) > 5:
                patterns_found.append({
                    "pattern": text[:150],
                    "category": ptype,
                    "date": datetime.now().strftime("%Y-%m-%d"),
                })

    # Look for repeated actions/workflows
    workflow_patterns = [
        r"(?:flujo|workflow|proceso)[:\s]+(.+?)(?:\n\n|\Z)",
        r"(?:pasos?\s*(?:a\s*)?seguir|steps?)[:\s]+(.+?)(?:\n\n|\Z)",
    ]

    for pattern in workflow_patterns:
        matches = re.findall(pattern, content, re.IGNORECASE | re.DOTALL)
        for m in matches[:2]:
            text = m.strip()
            if len(text) > 10:
                patterns_found.append({
                    "pattern": text[:150],
                    "category": "workflow",
                    "date": datetime.now().strftime("%Y-%m-%d"),
                })

    return patterns_found[:10]


def extract_learnings(content: str) -> List[Dict]:
    """Extract learnings from session content."""
    learnings = []

    patterns = [
        r"(?:aprendimos?|aprendizaje|hallazgo|descubrimiento)[:\s]+(.+?)(?:\n\n|\Z)",
        r"(?:Nota|nota)\s+(?:aprendida|importante)[:\s]+(.+?)(?:\n\n|\Z)",
        r"##\s+Aprendizajes.*?\n(.+?)(?=\n##|\Z)",
    ]

    for pattern in patterns:
        matches = re.findall(pattern, content, re.IGNORECASE | re.DOTALL)
        for m in matches[:5]:
            text = m.strip()
            if len(text) > 10 and len(text) < 300:
                learnings.append({
                    "text": text[:200],
                    "type": "learning",
                    "date": datetime.now().strftime("%Y-%m-%d"),
                })

    # Deduplicate
    seen = set()
    unique = []
    for l in learnings:
        if l["text"] not in seen:
            seen.add(l["text"])
            unique.append(l)

    return unique[:10]


def extract_pending_items(content: str) -> List[Dict]:
    """Extract pending items from session content."""
    pending = []

    # Unchecked items: - [ ]
    unchecked = re.findall(r"-\s+\[\s*\]\s*(.+?)(?:\n|$)", content)
    for item in unchecked[:15]:
        text = item.strip()
        if len(text) > 3 and len(text) < 200:
            pending.append({
                "text": text,
                "status": "pending",
                "date": datetime.now().strftime("%Y-%m-%d"),
            })

    return pending[:15]


def extract_topics(content: str) -> List[str]:
    """Extract main topics from session."""
    topics = []

    # Look for topics section
    topic_section = re.search(
        r"##\s+Temas?\s*Tratados.*?\n(.+?)(?=\n##|\Z)",
        content,
        re.IGNORECASE | re.DOTALL
    )
    if topic_section:
        items = re.findall(r"[-*]\s*(.+?)(?:\n|$)", topic_section.group(1))
        for item in items[:10]:
            topic = item.strip().lower()[:30]
            if topic and topic not in topics:
                topics.append(topic)

    # Infer from content keywords
    keywords_map = {
        "skills": ["skill", "@skill", "habilidad"],
        "knowledge-base": ["knowledge base", "base de conocimiento"],
        "release": ["release", "v0.", "versión", "version"],
        "bugfix": ["bug", "error", "fix", "corrección", "fix"],
        "features": ["feature", "implementar", "nueva funcionalidad"],
        "architecture": ["arquitectura", "diseño", "estructura"],
        "dashboard": ["dashboard", "spa", "ui"],
        "migration": ["migrar", "migración", "sync"],
        "sync": ["sync", "sincronizar", "sincronización"],
        "scripts": ["script", "python"],
    }

    content_lower = content.lower()
    for topic, keywords in keywords_map.items():
        if any(kw in content_lower for kw in keywords):
            if topic not in topics:
                topics.append(topic)

    return topics[:10]


def extract_highlights(content: str) -> List[Dict]:
    """Extract highlights from session (completed items, key achievements)."""
    highlights = []

    # Completed items
    completed = re.findall(r"-\s+\[x\]\s*(.+?)(?:\n|$)", content, re.IGNORECASE)
    for item in completed[:5]:
        text = item.strip()
        if len(text) > 3:
            highlights.append({
                "text": text[:100],
                "type": "completed",
                "date": datetime.now().strftime("%Y-%m-%d"),
            })

    # Key decisions or achievements
    achievement_patterns = [
        r"(?:logro|éxito|completad|implementad|terminad)[:\s]+(.+?)(?:\n\n|\Z)",
    ]
    for pattern in achievement_patterns:
        matches = re.findall(pattern, content, re.IGNORECASE | re.DOTALL)
        for m in matches[:3]:
            text = m.strip()[:100]
            if len(text) > 5:
                highlights.append({
                    "text": text,
                    "type": "achievement",
                    "date": datetime.now().strftime("%Y-%m-%d"),
                })

    return highlights[:10]


def mine_session(session_file: Path) -> Dict:
    """
    Mine all knowledge from a session file.
    Returns structured dict with all extracted knowledge.
    """
    content = read_session_content(session_file)
    date = datetime.now().strftime("%Y-%m-%d")

    mined = {
        "date": date,
        "session_file": str(session_file.name),
        "timestamp": datetime.now().isoformat(),
        "topics": extract_topics(content),
        "ideas": extract_ideas(content),
        "decisions": extract_decisions(content),
        "patterns": extract_patterns(content),
        "learnings": extract_learnings(content),
        "pending": extract_pending_items(content),
        "highlights": extract_highlights(content),
        "stats": {
            "ideas_count": 0,
            "decisions_count": 0,
            "patterns_count": 0,
            "learnings_count": 0,
            "pending_count": 0,
            "highlights_count": 0,
        }
    }

    # Count items
    mined["stats"]["ideas_count"] = len(mined["ideas"])
    mined["stats"]["decisions_count"] = len(mined["decisions"])
    mined["stats"]["patterns_count"] = len(mined["patterns"])
    mined["stats"]["learnings_count"] = len(mined["learnings"])
    mined["stats"]["pending_count"] = len(mined["pending"])
    mined["stats"]["highlights_count"] = len(mined["highlights"])

    return mined


def update_ideas_file(mined: Dict) -> bool:
    """Update ideas.md with new ideas from mining."""
    ideas_file = CODEBASE_DIR / "ideas.md"
    if not ideas_file.exists():
        ideas_file.write_text("# Ideas y Notas\n\n## Ideas\n\n", encoding="utf-8")

    try:
        content = ideas_file.read_text(encoding="utf-8")
        new_ideas = []

        for idea in mined.get("ideas", []):
            title = idea.get("title", "")
            if title and title not in content:
                date = idea.get("date", datetime.now().strftime("%Y-%m-%d"))
                new_ideas.append(f"### {date} - {title}\n\n{idea.get('content', '')}\n\n---\n")

        if new_ideas:
            # Insert before "## Migrado" section if exists
            migrar_pos = content.find("## Migrado")
            if migrar_pos > 0:
                content = content[:migrar_pos] + "\n".join(new_ideas) + "\n" + content[migrar_pos:]
            else:
                content += "\n".join(new_ideas)

            ideas_file.write_text(content, encoding="utf-8")
            return True

        return False
    except Exception as e:
        print(f"[WARN] Failed to update ideas.md: {e}")
        return False


def print_summary(mined: Dict):
    """Print a summary of mined knowledge."""
    print("\n" + "=" * 50)
    print(f"Knowledge Mining Summary - {mined['date']}")
    print("=" * 50)

    print(f"\nTopics ({len(mined['topics'])}):")
    for topic in mined['topics'][:5]:
        print(f"  - {topic}")

    if mined['ideas']:
        print(f"\nIdeas ({len(mined['ideas'])}):")
        for idea in mined['ideas'][:3]:
            print(f"  - {idea['title'][:60]}...")

    if mined['decisions']:
        print(f"\nDecisions ({len(mined['decisions'])}):")
        for d in mined['decisions'][:3]:
            print(f"  - {d['text'][:60]}...")

    if mined['patterns']:
        print(f"\nPatterns ({len(mined['patterns'])}):")
        for p in mined['patterns'][:3]:
            print(f"  - [{p['category']}] {p['pattern'][:50]}...")

    if mined['learnings']:
        print(f"\nLearnings ({len(mined['learnings'])}):")
        for l in mined['learnings'][:3]:
            print(f"  - {l['text'][:60]}...")

    if mined['pending']:
        print(f"\nPending Items ({len(mined['pending'])}):")
        for p in mined['pending'][:3]:
            print(f"  - {p['text'][:60]}...")

    if mined['highlights']:
        print(f"\nHighlights ({len(mined['highlights'])}):")
        for h in mined['highlights'][:3]:
            print(f"  - {h['text'][:60]}...")

    print("\n" + "=" * 50)


def main():
    parser = argparse.ArgumentParser(
        description="PA Framework Knowledge Miner - Extract structured knowledge from sessions"
    )
    parser.add_argument(
        "--date",
        type=str,
        default=None,
        help="Mine session for specific date (YYYY-MM-DD). Default: today."
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Save output to JSON file."
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress console output."
    )

    args = parser.parse_args()

    session_file = get_session_file(args.date)
    if not session_file:
        date_str = args.date or datetime.now().strftime("%Y-%m-%d")
        print(f"[ERROR] No session found for date: {date_str}")
        sys.exit(1)

    # Mine the session
    mined = mine_session(session_file)

    # Update ideas.md
    update_ideas_file(mined)

    # Print summary unless quiet
    if not args.quiet:
        print_summary(mined)

    # Save to file if requested
    if args.output:
        output_path = Path(args.output)
        output_path.write_text(
            json.dumps(mined, indent=2, ensure_ascii=False),
            encoding="utf-8"
        )
        print(f"[OK] Output saved to {output_path}")

    # Also save as latest mined data
    mined_output = KNOWLEDGE_DIR / "last_mined.json"
    KNOWLEDGE_DIR.mkdir(parents=True, exist_ok=True)
    mined_output.write_text(
        json.dumps(mined, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )

    return mined


if __name__ == "__main__":
    main()
