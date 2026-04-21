#!/usr/bin/env python3
"""
Session Indexer - PA Framework
==============================

Escanear sesiones históricas y generar/actualizar sessions-index.json
Compatible con versiones anteriores del framework.

Uso:
    python core/scripts/session-indexer.py           # Indexar todas las sesiones
    python core/scripts/session-indexer.py --today   # Indexar solo hoy
    python core/scripts/session-indexer.py --rebuild # Reconstruir índice completo

Autor: FreakingJSON-PA Framework
Versión: 1.0.0
"""

import argparse
import json
import re
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

# Paths
SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent.parent
SESSIONS_DIR = REPO_ROOT / "core" / ".context" / "sessions"
KNOWLEDGE_DIR = REPO_ROOT / "core" / ".context" / "knowledge"
INDEX_FILE = KNOWLEDGE_DIR / "sessions-index.json"

# Ensure knowledge dir exists
KNOWLEDGE_DIR.mkdir(parents=True, exist_ok=True)


class SessionIndexer:
    """Indexer for session files with retrocompatibility."""

    def __init__(self):
        self.index = self._load_existing_index()
        self.new_sessions = 0
        self.updated_sessions = 0

    def _load_existing_index(self) -> dict:
        """Load existing index or create new structure."""
        if INDEX_FILE.exists():
            try:
                with open(INDEX_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except json.JSONDecodeError:
                pass

        # Return default structure
        return {
            "version": "1.0",
            "description": "Índice central de sesiones para consulta histórica y Dashboard SPA",
            "last_updated": datetime.now().isoformat(),
            "total_sessions": 0,
            "schema": {
                "session": {
                    "id": "YYYY-MM-DD",
                    "date": "YYYY-MM-DD",
                    "time_start": "HH:MM",
                    "time_end": "HH:MM o null",
                    "title": "Título auto-generado o editable",
                    "summary": "Resumen de 1-2 líneas",
                    "topics": ["array", "de", "tags"],
                    "type": "features|bugfix|research|planning|other",
                    "stats": {
                        "interactions": 0,
                        "files_modified": 0,
                        "decisions": 0,
                        "lsp_errors": 0,
                        "word_count": 0,
                    },
                    "highlights": [
                        {"type": "decision|error|feature", "text": "descripción"}
                    ],
                    "file_path": "sessions/YYYY-MM-DD.md",
                    "status": "active|completed",
                }
            },
            "sessions": [],
            "filters": {"by_topic": {}, "by_type": {}},
            "topics_registry": [],
        }

    def _extract_frontmatter(self, content: str) -> dict:
        """Extract YAML frontmatter if present."""
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                frontmatter = parts[1].strip()
                # Simple key: value extraction
                data = {}
                for line in frontmatter.split("\n"):
                    if ":" in line:
                        key, value = line.split(":", 1)
                        data[key.strip()] = value.strip()
                return data
        return {}

    def _extract_title(self, content: str) -> str:
        """Extract title from session content."""
        # Try H1
        match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
        if match:
            return match.group(1).strip()

        # Try "## Inicio" section
        match = re.search(
            r"##\s+Inicio.*?\n.*?-\s+\*\*Hora\*\*:\s*(.+?)\n", content, re.DOTALL
        )
        if match:
            return f"Sesión del {match.group(1).strip()}"

        return "Sesión sin título"

    def _extract_summary(self, content: str) -> str:
        """Extract summary from session content."""
        # Try ## Resumen section
        match = re.search(r"##\s+Resumen\s*\n(.+?)(?=\n##|\Z)", content, re.DOTALL)
        if match:
            summary = match.group(1).strip()
            # Truncate to 150 chars
            if len(summary) > 150:
                summary = summary[:147] + "..."
            return summary

        # Try first paragraph after title
        lines = content.split("\n")
        for line in lines[1:]:
            line = line.strip()
            if line and not line.startswith("#") and not line.startswith("-"):
                if len(line) > 50:
                    return line[:147] + "..." if len(line) > 150 else line

        return "Sin resumen disponible"

    def _extract_topics(self, content: str) -> List[str]:
        """Extract topics/tags from session content."""
        topics = []

        # Look for "## Temas" or topics in content
        topic_patterns = [
            r"##\s+Temas\s*Tratados.*?\n(.+?)(?=\n##|\Z)",
            r"topics?:\s*\[?([^\]]+)\]?",
            r"##\s+Features.*?\n(.+?)(?=\n##|\Z)",
        ]

        for pattern in topic_patterns:
            match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
            if match:
                text = match.group(1)
                # Extract bullet points or tags
                bullets = re.findall(r"[-*]\s*\[?\s*([^\]]+?)\s*\]?\s*(?:\n|$)", text)
                topics.extend(
                    [b.strip().lower().replace(" ", "-") for b in bullets if b.strip()]
                )

        # Also look for common keywords
        keywords = {
            "skills": ["skill", "@skill"],
            "knowledge-base": ["knowledge", "knowlege base"],
            "release": ["release", "v0.", "version"],
            "bugfix": ["fix", "bug", "error", "loop"],
            "features": ["feature", "implementación", "implementar"],
            "architecture": ["arquitectura", "diseño", "estructura"],
            "dashboard": ["dashboard", "spa", "ui"],
            "migration": ["migrar", "migración", "sync"],
        }

        content_lower = content.lower()
        for topic, keywords_list in keywords.items():
            if any(kw in content_lower for kw in keywords_list):
                if topic not in topics:
                    topics.append(topic)

        return topics[:10]  # Max 10 topics

    def _extract_type(self, content: str) -> str:
        """Extract session type."""
        content_lower = content.lower()

        if any(word in content_lower for word in ["release", "v0.", "versión"]):
            return "release"
        elif any(
            word in content_lower for word in ["fix", "bug", "error", "corrección"]
        ):
            return "bugfix"
        elif any(
            word in content_lower for word in ["research", "investigación", "análisis"]
        ):
            return "research"
        elif any(
            word in content_lower for word in ["planning", "planificación", "roadmap"]
        ):
            return "planning"
        elif any(
            word in content_lower
            for word in ["feature", "implementar", "nueva funcionalidad"]
        ):
            return "features"

        return "other"

    def _extract_stats(self, content: str) -> dict:
        """Extract stats from session content."""
        stats = {
            "interactions": 0,
            "files_modified": 0,
            "decisions": 0,
            "lsp_errors": 0,
            "word_count": len(content.split()),
        }

        # Count decisions
        decisions = re.findall(r"##?\s+Decisiones", content, re.IGNORECASE)
        if decisions:
            # Count numbered/bulleted items after decisions
            decision_section = re.search(
                r"##?\s+Decisiones.*?\n(.+?)(?=\n##|\Z)", content, re.DOTALL
            )
            if decision_section:
                items = re.findall(
                    r"^\d+\.|^[-*]", decision_section.group(1), re.MULTILINE
                )
                stats["decisions"] = len(items)

        # Count files modified
        file_patterns = [
            r"(?:archivo|file|modificado)\s*:?\s*`?([^`\n]+\.(?:py|md|json|js|html|css|sh|bat))`?",
            r"`([^`]+\.(?:py|md|json|js|html|css|sh|bat))`",
        ]
        files = set()
        for pattern in file_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            files.update(matches)
        stats["files_modified"] = len(files)

        return stats

    def _extract_highlights(self, content: str) -> List[dict]:
        """Extract highlights from session content."""
        highlights = []

        # Look for completed items
        completed = re.findall(r"[-*]\s*\[x\]\s*(.+?)(?:\n|$)", content, re.IGNORECASE)
        for item in completed[:3]:
            highlights.append({"type": "feature", "text": item.strip()[:100]})

        # Look for decisions
        decisions = re.findall(
            r"(?:\d+\.|[-*])\s*(?:Decidimos|Decisión|Aprobado|Implementar)\s*:?\s*(.+?)(?:\n|$)",
            content,
            re.IGNORECASE,
        )
        for decision in decisions[:2]:
            highlights.append({"type": "decision", "text": decision.strip()[:100]})

        return highlights[:5]  # Max 5 highlights

    def parse_session_file(self, file_path: Path) -> Optional[dict]:
        """Parse a single session file and return structured data."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            print(f"[WARN] Error reading {file_path}: {e}")
            return None

        # Extract date from filename
        date_match = re.search(r"(\d{4}-\d{2}-\d{2})", file_path.name)
        if not date_match:
            return None

        session_id = date_match.group(1)

        # Check frontmatter
        frontmatter = self._extract_frontmatter(content)

        # Build session entry
        session = {
            "id": session_id,
            "date": session_id,
            "time_start": frontmatter.get("time_start", "--:--"),
            "time_end": frontmatter.get("time_end", None),
            "title": self._extract_title(content),
            "summary": self._extract_summary(content),
            "topics": self._extract_topics(content),
            "type": self._extract_type(content),
            "stats": self._extract_stats(content),
            "highlights": self._extract_highlights(content),
            "file_path": f"sessions/{file_path.name}",
            "status": "completed",  # Assume completed if in index
        }

        return session

    def index_all_sessions(self):
        """Index all session files."""
        if not SESSIONS_DIR.exists():
            print(f"[ERROR] Sessions directory not found: {SESSIONS_DIR}")
            return

        # Find all session files
        session_files = sorted(SESSIONS_DIR.glob("*.md"))

        # Filter out special files
        session_files = [
            f for f in session_files if re.match(r"\d{4}-\d{2}-\d{2}", f.name)
        ]

        print(f"[INFO] Found {len(session_files)} session files")

        # Parse each session
        existing_ids = {s["id"] for s in self.index["sessions"]}

        for file_path in session_files:
            session = self.parse_session_file(file_path)
            if not session:
                continue

            if session["id"] in existing_ids:
                # Update existing
                for i, existing in enumerate(self.index["sessions"]):
                    if existing["id"] == session["id"]:
                        self.index["sessions"][i] = session
                        self.updated_sessions += 1
                        break
            else:
                # Add new
                self.index["sessions"].append(session)
                self.new_sessions += 1

        # Sort by date (newest first)
        self.index["sessions"].sort(key=lambda x: x["id"], reverse=True)

        # Update metadata
        self.index["total_sessions"] = len(self.index["sessions"])
        self.index["last_updated"] = datetime.now().isoformat()

        # Update filters
        self._update_filters()

        # Save index
        self._save_index()

        print(f"[OK] Indexed {self.index['total_sessions']} sessions")
        print(f"   New: {self.new_sessions}")
        print(f"   Updated: {self.updated_sessions}")

    def _update_filters(self):
        """Update filter indexes."""
        # Asegurar que la estructura existe (fix para índices creados externamente)
        if "filters" not in self.index:
            self.index["filters"] = {"by_topic": {}, "by_type": {}}
        if "topics_registry" not in self.index:
            self.index["topics_registry"] = []

        by_topic = {}
        by_type = {}
        topics_registry = {}

        for session in self.index["sessions"]:
            # By topic
            for topic in session.get("topics", []):
                if topic not in by_topic:
                    by_topic[topic] = []
                by_topic[topic].append(session["id"])

                # Topics registry
                if topic not in topics_registry:
                    topics_registry[topic] = {"count": 0, "description": ""}
                topics_registry[topic]["count"] += 1

            # By type
            session_type = session.get("type", "other")
            by_type[session_type] = by_type.get(session_type, 0) + 1

        self.index["filters"]["by_topic"] = by_topic
        self.index["filters"]["by_type"] = by_type

        # Convert topics registry to list
        self.index["topics_registry"] = [
            {"name": k, "count": v["count"], "description": v["description"]}
            for k, v in sorted(
                topics_registry.items(), key=lambda x: x[1]["count"], reverse=True
            )
        ]

    def _save_index(self):
        """Save index to file."""
        with open(INDEX_FILE, "w", encoding="utf-8") as f:
            json.dump(self.index, f, indent=2, ensure_ascii=False)
        print(f"[OK] Index saved to {INDEX_FILE}")

    def get_stats(self) -> dict:
        """Get statistics about indexed sessions."""
        return {
            "total_sessions": len(self.index["sessions"]),
            "topics": len(self.index["filters"]["by_topic"]),
            "types": dict(self.index["filters"]["by_type"]),
            "last_updated": self.index["last_updated"],
        }


def main():
    parser = argparse.ArgumentParser(description="Session Indexer for PA Framework")
    parser.add_argument(
        "--today", action="store_true", help="Index only today's session"
    )
    parser.add_argument(
        "--rebuild", action="store_true", help="Rebuild index from scratch"
    )
    parser.add_argument("--stats", action="store_true", help="Show statistics")

    args = parser.parse_args()

    indexer = SessionIndexer()

    if args.stats:
        stats = indexer.get_stats()
        print("Session Index Statistics:")
        print(f"  Total sessions: {stats['total_sessions']}")
        print(f"  Unique topics: {stats['topics']}")
        print(f"  By type: {stats['types']}")
        print(f"  Last updated: {stats['last_updated']}")
        return

    if args.rebuild:
        print("[INFO] Rebuilding index from scratch...")
        indexer.index = indexer._load_existing_index()
        indexer.index["sessions"] = []

    if args.today:
        # Index only today's session
        today = datetime.now().strftime("%Y-%m-%d")
        today_file = SESSIONS_DIR / f"{today}.md"
        if today_file.exists():
            session = indexer.parse_session_file(today_file)
            if session:
                # Update or add
                existing_ids = {s["id"] for s in indexer.index["sessions"]}
                if session["id"] in existing_ids:
                    for i, existing in enumerate(indexer.index["sessions"]):
                        if existing["id"] == session["id"]:
                            indexer.index["sessions"][i] = session
                            break
                else:
                    indexer.index["sessions"].append(session)

                indexer.index["sessions"].sort(key=lambda x: x["id"], reverse=True)
                indexer.index["total_sessions"] = len(indexer.index["sessions"])
                indexer.index["last_updated"] = datetime.now().isoformat()
                indexer._update_filters()
                indexer._save_index()
                print(f"[OK] Indexed today's session: {today}")
        else:
            print(f"[WARN] No session file found for today: {today}")
    else:
        # Index all sessions
        indexer.index_all_sessions()


if __name__ == "__main__":
    main()
