#!/usr/bin/env python3
"""
Search Indexer - PA Framework
=============================

Motor de búsqueda full-text usando SQLite FTS5.
Cero dependencias externas, ultrarrápido, local-first.

Uso:
    python core/scripts/search-indexer.py --rebuild     # Reconstruir índice
    python core/scripts/search-indexer.py --search "skills"  # Buscar
    python core/scripts/search-indexer.py --stats       # Estadísticas

Características:
    - Búsqueda full-text en sesiones, skills, y codebase
    - Autocompletado con trigramas
    - Ranking por relevancia
    - Sin dependencias (SQLite built-in)

Autor: FreakingJSON-PA Framework
Versión: 1.0.0
"""

import argparse
import json
import re
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

# Paths
SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent.parent
KNOWLEDGE_DIR = REPO_ROOT / "core" / ".context" / "knowledge"
SEARCH_DB = KNOWLEDGE_DIR / "search-index.db"
SESSIONS_DIR = REPO_ROOT / "core" / ".context" / "sessions"
SKILLS_DIR = REPO_ROOT / "core" / "skills"
CODEBASE_DIR = REPO_ROOT / "core" / ".context" / "codebase"


class SearchIndexer:
    """Full-text search indexer using SQLite FTS5."""

    def __init__(self):
        self.conn = None
        self.cursor = None
        self._init_db()

    def _init_db(self):
        """Initialize SQLite database with FTS5."""
        KNOWLEDGE_DIR.mkdir(parents=True, exist_ok=True)

        self.conn = sqlite3.connect(SEARCH_DB)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()

        # Check if FTS5 is available
        try:
            self.cursor.execute(
                "SELECT * FROM sqlite_master WHERE type='table' AND name='documents'"
            )
            if not self.cursor.fetchone():
                self._create_tables()
        except sqlite3.OperationalError:
            self._create_tables()

    def _create_tables(self):
        """Create FTS5 tables and indexes."""
        # Main FTS5 table for documents
        self.cursor.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS documents USING fts5(
                title,
                content,
                path,
                type,
                tags,
                tokenize='porter unicode61'
            )
        """)

        # Metadata table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS document_meta (
                doc_id INTEGER PRIMARY KEY,
                path TEXT UNIQUE,
                type TEXT,
                title TEXT,
                last_modified TIMESTAMP,
                indexed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Search history
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS search_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query TEXT,
                results_count INTEGER,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Trigram index for autocomplete
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS trigrams (
                trigram TEXT PRIMARY KEY,
                frequency INTEGER DEFAULT 1
            )
        """)

        self.conn.commit()

    def _extract_trigrams(self, text: str):
        """Extract trigrams for autocomplete."""
        text = text.lower()
        # Clean text
        text = re.sub(r"[^\w\s]", " ", text)
        words = text.split()

        trigrams = set()
        for word in words:
            if len(word) >= 3:
                for i in range(len(word) - 2):
                    trigrams.add(word[i : i + 3])
        return trigrams

    def _update_trigrams(self, text: str):
        """Update trigram frequencies."""
        trigrams = self._extract_trigrams(text)
        for trigram in trigrams:
            self.cursor.execute(
                """
                INSERT INTO trigrams (trigram, frequency) VALUES (?, 1)
                ON CONFLICT(trigram) DO UPDATE SET frequency = frequency + 1
            """,
                (trigram,),
            )

    def index_session(self, session_file: Path):
        """Index a session file."""
        try:
            with open(session_file, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            print(f"[WARN] Error reading {session_file}: {e}")
            return

        # Extract title
        title_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
        title = title_match.group(1) if title_match else session_file.stem

        # Extract tags/topics
        tags = []
        for match in re.finditer(r"\[([^\]]+)\]", content):
            tag = match.group(1).lower().replace(" ", "-")
            if len(tag) < 30:  # Filter out long matches
                tags.append(tag)
        tags = " ".join(set(tags))

        path_str = str(session_file.relative_to(REPO_ROOT))

        # Delete existing entry
        self.cursor.execute("DELETE FROM documents WHERE path = ?", (path_str,))
        self.cursor.execute("DELETE FROM document_meta WHERE path = ?", (path_str,))

        # Insert new entry
        self.cursor.execute(
            """
            INSERT INTO documents (title, content, path, type, tags)
            VALUES (?, ?, ?, 'session', ?)
        """,
            (title, content, path_str, tags),
        )

        doc_id = self.cursor.lastrowid

        self.cursor.execute(
            """
            INSERT INTO document_meta (doc_id, path, type, title, last_modified)
            VALUES (?, ?, 'session', ?, ?)
        """,
            (
                doc_id,
                path_str,
                title,
                datetime.fromtimestamp(session_file.stat().st_mtime),
            ),
        )

        # Update trigrams
        self._update_trigrams(title + " " + content + " " + tags)

        self.conn.commit()

    def index_skill(self, skill_file: Path):
        """Index a skill documentation file."""
        try:
            with open(skill_file, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            return

        # Extract skill name from path
        skill_name = skill_file.parent.name
        title = f"Skill: {skill_name}"

        # Extract description
        desc_match = re.search(r"description:\s*(.+)", content, re.IGNORECASE)
        description = desc_match.group(1) if desc_match else ""

        path_str = str(skill_file.relative_to(REPO_ROOT))
        content_with_desc = f"{description}\n\n{content}"

        # Delete existing
        self.cursor.execute("DELETE FROM documents WHERE path = ?", (path_str,))
        self.cursor.execute("DELETE FROM document_meta WHERE path = ?", (path_str,))

        # Insert
        self.cursor.execute(
            """
            INSERT INTO documents (title, content, path, type, tags)
            VALUES (?, ?, ?, 'skill', ?)
        """,
            (title, content_with_desc, path_str, skill_name),
        )

        doc_id = self.cursor.lastrowid

        self.cursor.execute(
            """
            INSERT INTO document_meta (doc_id, path, type, title, last_modified)
            VALUES (?, ?, 'skill', ?, ?)
        """,
            (
                doc_id,
                path_str,
                title,
                datetime.fromtimestamp(skill_file.stat().st_mtime),
            ),
        )

        self._update_trigrams(title + " " + content_with_desc)
        self.conn.commit()

    def index_codebase(self, file_path: Path):
        """Index a codebase file."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception:
            return

        title = file_path.stem.replace("-", " ").replace("_", " ").title()
        path_str = str(file_path.relative_to(REPO_ROOT))

        # Delete existing
        self.cursor.execute("DELETE FROM documents WHERE path = ?", (path_str,))
        self.cursor.execute("DELETE FROM document_meta WHERE path = ?", (path_str,))

        # Insert
        self.cursor.execute(
            """
            INSERT INTO documents (title, content, path, type, tags)
            VALUES (?, ?, ?, 'codebase', '')
        """,
            (title, content, path_str),
        )

        doc_id = self.cursor.lastrowid

        self.cursor.execute(
            """
            INSERT INTO document_meta (doc_id, path, type, title, last_modified)
            VALUES (?, ?, 'codebase', ?, ?)
        """,
            (
                doc_id,
                path_str,
                title,
                datetime.fromtimestamp(file_path.stat().st_mtime),
            ),
        )

        self._update_trigrams(title + " " + content)
        self.conn.commit()

    def rebuild_index(self):
        """Rebuild entire search index."""
        print("[INFO] Rebuilding search index...")

        # Clear existing
        self.cursor.execute("DELETE FROM documents")
        self.cursor.execute("DELETE FROM document_meta")
        self.cursor.execute("DELETE FROM trigrams")
        self.conn.commit()

        indexed = {"sessions": 0, "skills": 0, "codebase": 0}

        # Index sessions
        if SESSIONS_DIR.exists():
            for session_file in SESSIONS_DIR.glob("*.md"):
                if re.match(r"\d{4}-\d{2}-\d{2}", session_file.name):
                    self.index_session(session_file)
                    indexed["sessions"] += 1

        # Index skills
        if SKILLS_DIR.exists():
            for skill_file in SKILLS_DIR.rglob("SKILL.md"):
                self.index_skill(skill_file)
                indexed["skills"] += 1

        # Index codebase
        if CODEBASE_DIR.exists():
            for md_file in CODEBASE_DIR.rglob("*.md"):
                self.index_codebase(md_file)
                indexed["codebase"] += 1

        print(f"[OK] Index rebuilt:")
        print(f"   Sessions: {indexed['sessions']}")
        print(f"   Skills: {indexed['skills']}")
        print(f"   Codebase: {indexed['codebase']}")
        print(f"   Database: {SEARCH_DB}")

        return indexed

    def search(self, query: str, limit: int = 20) -> List[Dict]:
        """Search documents with ranking."""
        # Record search
        self.cursor.execute(
            """
            INSERT INTO search_history (query, results_count)
            VALUES (?, 0)
        """,
            (query,),
        )
        search_id = self.cursor.lastrowid

        # FTS5 search with ranking
        # Use MATCH for full-text, ORDER BY rank for relevance
        try:
            self.cursor.execute(
                """
                SELECT 
                    d.rowid,
                    d.title,
                    d.path,
                    d.type,
                    d.tags,
                    rank
                FROM documents d
                WHERE documents MATCH ?
                ORDER BY rank
                LIMIT ?
            """,
                (query, limit),
            )

            results = []
            for row in self.cursor.fetchall():
                results.append(
                    {
                        "id": row["rowid"],
                        "title": row["title"],
                        "path": row["path"],
                        "type": row["type"],
                        "tags": row["tags"],
                        "rank": row["rank"],
                    }
                )

            # Update results count
            self.cursor.execute(
                """
                UPDATE search_history SET results_count = ? WHERE id = ?
            """,
                (len(results), search_id),
            )
            self.conn.commit()

            return results

        except sqlite3.OperationalError as e:
            print(f"[ERROR] Search failed: {e}")
            return []

    def autocomplete(self, prefix: str, limit: int = 10) -> List[str]:
        """Get autocomplete suggestions."""
        prefix = prefix.lower()

        self.cursor.execute(
            """
            SELECT trigram, frequency
            FROM trigrams
            WHERE trigram LIKE ?
            ORDER BY frequency DESC
            LIMIT ?
        """,
            (f"{prefix}%", limit),
        )

        return [row["trigram"] for row in self.cursor.fetchall()]

    def get_stats(self) -> Dict:
        """Get index statistics."""
        stats = {}

        # Document counts by type
        self.cursor.execute("""
            SELECT type, COUNT(*) as count
            FROM document_meta
            GROUP BY type
        """)
        stats["by_type"] = {row["type"]: row["count"] for row in self.cursor.fetchall()}

        # Total documents
        self.cursor.execute("SELECT COUNT(*) as total FROM documents")
        stats["total_documents"] = self.cursor.fetchone()["total"]

        # Search history
        self.cursor.execute("SELECT COUNT(*) as total FROM search_history")
        stats["total_searches"] = self.cursor.fetchone()["total"]

        # Database size
        stats["db_size_bytes"] = SEARCH_DB.stat().st_size if SEARCH_DB.exists() else 0

        return stats

    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()


def main():
    parser = argparse.ArgumentParser(description="Search Indexer for PA Framework")
    parser.add_argument("--rebuild", action="store_true", help="Rebuild search index")
    parser.add_argument("--search", metavar="QUERY", help="Search documents")
    parser.add_argument(
        "--autocomplete", metavar="PREFIX", help="Get autocomplete suggestions"
    )
    parser.add_argument("--stats", action="store_true", help="Show statistics")
    parser.add_argument("--limit", type=int, default=20, help="Limit results")

    args = parser.parse_args()

    indexer = SearchIndexer()

    try:
        if args.rebuild:
            indexer.rebuild_index()

        elif args.search:
            results = indexer.search(args.search, args.limit)
            print(f"Search: '{args.search}'")
            print(f"Results: {len(results)}")
            print()
            for r in results:
                print(f"[{r['type']}] {r['title']}")
                print(f"    Path: {r['path']}")
                print(f"    Tags: {r['tags'] or 'N/A'}")
                print()

        elif args.autocomplete:
            suggestions = indexer.autocomplete(args.autocomplete, args.limit)
            print(f"Autocomplete for '{args.autocomplete}':")
            for s in suggestions:
                print(f"  {s}")

        elif args.stats:
            stats = indexer.get_stats()
            print("Search Index Statistics:")
            print(f"  Total documents: {stats['total_documents']}")
            print(f"  By type: {stats['by_type']}")
            print(f"  Total searches: {stats['total_searches']}")
            print(f"  DB size: {stats['db_size_bytes'] / 1024:.1f} KB")

        else:
            parser.print_help()

    finally:
        indexer.close()


if __name__ == "__main__":
    main()
