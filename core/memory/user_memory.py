"""
User Memory Module — Persistent facts/entities storage for user data.

Based on OpenJarvis pattern (April 2026 research synthesis).
Part of PA Framework v0.3.0-alpha.

Purpose:
- Store important facts about the user (preferences, projects, goals)
- Persist across sessions (not cleared between conversations)
- Semantic, structured storage with timestamps and categories
- Query interface for retrieval

Features:
- Categories: preference, project, goal, fact, context
- Priority: critical, high, medium, low
- Soft delete (archived, not purged)
- Version tracking for facts
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
import sqlite3
import json
import time
import uuid
from typing import Optional, List, Dict, Any
from enum import Enum


# ============================================================================
# Framework Data Directory (Cross-Platform)
# ============================================================================


def _get_framework_data_dir() -> Path:
    """Get framework data directory - works on Windows, Linux, macOS.

    Priority:
    1. PA_FRAMEWORK_DATA env var (if set)
    2. Framework installation directory (parent of core/memory/)

    This ensures data persists WITH the framework, not in user home.
    """
    env_data = os.environ.get("PA_FRAMEWORK_DATA")
    if env_data:
        return Path(env_data)

    module_dir = Path(__file__).parent  # core/memory/
    framework_root = module_dir.parent.parent  # framework root

    data_dir = framework_root / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


# ============================================================================
# Enums
# ============================================================================


class FactCategory(str, Enum):
    """Categories for facts."""

    PREFERENCE = "preference"
    PROJECT = "project"
    GOAL = "goal"
    FACT = "fact"
    CONTEXT = "context"


class FactPriority(str, Enum):
    """Priority levels for facts."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


# ============================================================================
# Data Models
# ============================================================================


@dataclass(slots=True)
class UserFact:
    """Single fact about the user."""

    id: str
    category: str  # FactCategory
    priority: str  # FactPriority
    key: str  # e.g., "active_project", "favorite_color"
    value: Any  # e.g., "Libro", "#FF00FF"
    description: str = ""
    source: str = "user"  # "user", "system", "derived"
    created_at: float = 0.0
    updated_at: float = 0.0
    archived: bool = False
    version: int = 1
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "category": self.category,
            "priority": self.priority,
            "key": self.key,
            "value": self.value,
            "description": self.description,
            "source": self.source,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "archived": self.archived,
            "version": self.version,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "UserFact":
        return cls(**data)


# ============================================================================
# User Memory Store (SQLite-backed)
# ============================================================================


class UserMemoryStore:
    """SQLite-backed persistent user memory.

    Usage:
        store = UserMemoryStore()

        # Store a fact
        store.set_fact(
            category="project",
            priority="high",
            key="active_project",
            value="Libro",
            description="Vamos a escribir un libro usando IA"
        )

        # Get a fact
        fact = store.get_fact("active_project")

        # List facts by category
        projects = store.list_facts(category="project")

        # Update a fact
        store.update_fact("active_project", value="Nuevo valor")

        # Archive a fact (soft delete)
        store.archive_fact("active_project")
    """

    def __init__(
        self,
        db_path: Path = None,
    ) -> None:
        if db_path is None:
            db_path = _get_framework_data_dir() / "user_memory.db"
        self._db_path = Path(db_path)
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self._db_path), check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._create_tables()

    def _create_tables(self) -> None:
        """Create database tables if they don't exist."""
        self._conn.executescript("""
            CREATE TABLE IF NOT EXISTS user_facts (
                id TEXT PRIMARY KEY,
                category TEXT NOT NULL,
                priority TEXT NOT NULL,
                key TEXT NOT NULL UNIQUE,
                value TEXT NOT NULL,
                description TEXT DEFAULT '',
                source TEXT DEFAULT 'user',
                created_at REAL NOT NULL,
                updated_at REAL NOT NULL,
                archived INTEGER DEFAULT 0,
                version INTEGER DEFAULT 1,
                metadata TEXT DEFAULT '{}'
            );
            
            CREATE INDEX IF NOT EXISTS idx_facts_key ON user_facts(key);
            CREATE INDEX IF NOT EXISTS idx_facts_category ON user_facts(category);
            CREATE INDEX IF NOT EXISTS idx_facts_archived ON user_facts(archived);
        """)
        self._conn.commit()

    # --------------------------------------------------------------------------
    # CRUD Operations
    # --------------------------------------------------------------------------

    def set_fact(
        self,
        category: str,
        priority: str,
        key: str,
        value: Any,
        description: str = "",
        source: str = "user",
        metadata: dict = None,
    ) -> UserFact:
        """Store a fact (insert or update).

        Args:
            category: FactCategory value
            priority: FactPriority value
            key: Unique key for the fact
            value: Value to store
            description: Optional description
            source: Origin of the fact (user, system, derived)
            metadata: Optional metadata dict

        Returns:
            UserFact object
        """
        now = time.time()

        # Check if key exists
        existing = self.get_fact(key)
        if existing:
            # Update existing
            return self.update_fact(
                key=key,
                value=value,
                description=description or existing.description,
                metadata=metadata,
            )

        # Create new
        fact_id = str(uuid.uuid4())
        self._conn.execute(
            """INSERT INTO user_facts 
               (id, category, priority, key, value, description, source, created_at, updated_at, metadata)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                fact_id,
                category,
                priority,
                key,
                json.dumps(value),
                description,
                source,
                now,
                now,
                json.dumps(metadata or {}),
            ),
        )
        self._conn.commit()

        return UserFact(
            id=fact_id,
            category=category,
            priority=priority,
            key=key,
            value=value,
            description=description,
            source=source,
            created_at=now,
            updated_at=now,
            version=1,
            metadata=metadata or {},
        )

    def get_fact(self, key: str, include_archived: bool = False) -> Optional[UserFact]:
        """Get a fact by key.

        Args:
            key: Fact key to retrieve
            include_archived: Include archived facts

        Returns:
            UserFact or None
        """
        query = "SELECT * FROM user_facts WHERE key = ?"
        if not include_archived:
            query += " AND archived = 0"

        row = self._conn.execute(query, (key,)).fetchone()
        if not row:
            return None

        return UserFact(
            id=row["id"],
            category=row["category"],
            priority=row["priority"],
            key=row["key"],
            value=json.loads(row["value"]),
            description=row["description"],
            source=row["source"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            archived=bool(row["archived"]),
            version=row["version"],
            metadata=json.loads(row["metadata"]),
        )

    def update_fact(
        self,
        key: str,
        value: Any = None,
        description: str = None,
        priority: str = None,
        metadata: dict = None,
    ) -> Optional[UserFact]:
        """Update an existing fact.

        Args:
            key: Fact key to update
            value: New value (optional)
            description: New description (optional)
            priority: New priority (optional)
            metadata: New metadata (optional)

        Returns:
            Updated UserFact or None
        """
        existing = self.get_fact(key, include_archived=True)
        if not existing:
            return None

        now = time.time()

        updates = []
        params = []

        if value is not None:
            updates.append("value = ?")
            params.append(json.dumps(value))

        if description is not None:
            updates.append("description = ?")
            params.append(description)

        if priority is not None:
            updates.append("priority = ?")
            params.append(priority)

        if metadata is not None:
            updates.append("metadata = ?")
            params.append(json.dumps(metadata))

        if updates:
            updates.append("updated_at = ?")
            params.append(now)
            updates.append("version = version + 1")

            params.append(key)

            self._conn.execute(
                f"UPDATE user_facts SET {', '.join(updates)} WHERE key = ?",
                params,
            )
            self._conn.commit()

        return self.get_fact(key)

    def archive_fact(self, key: str) -> bool:
        """Archive a fact (soft delete).

        Args:
            key: Fact key to archive

        Returns:
            True if archived
        """
        result = self._conn.execute(
            "UPDATE user_facts SET archived = 1, updated_at = ? WHERE key = ?",
            (time.time(), key),
        )
        self._conn.commit()
        return result.rowcount > 0

    def list_facts(
        self,
        category: str = None,
        priority: str = None,
        include_archived: bool = False,
        limit: int = 100,
    ) -> List[UserFact]:
        """List facts with optional filters.

        Args:
            category: Filter by category
            priority: Filter by priority
            include_archived: Include archived facts
            limit: Max results

        Returns:
            List of UserFact
        """
        query = "SELECT * FROM user_facts WHERE 1=1"
        params = []

        if category:
            query += " AND category = ?"
            params.append(category)

        if priority:
            query += " AND priority = ?"
            params.append(priority)

        if not include_archived:
            query += " AND archived = 0"

        query += " ORDER BY priority DESC, updated_at DESC LIMIT ?"
        params.append(limit)

        rows = self._conn.execute(query, params).fetchall()

        return [
            UserFact(
                id=row["id"],
                category=row["category"],
                priority=row["priority"],
                key=row["key"],
                value=json.loads(row["value"]),
                description=row["description"],
                source=row["source"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
                archived=bool(row["archived"]),
                version=row["version"],
                metadata=json.loads(row["metadata"]),
            )
            for row in rows
        ]

    # --------------------------------------------------------------------------
    # Search & Query
    # --------------------------------------------------------------------------

    def search(self, query: str, limit: int = 10) -> List[UserFact]:
        """Search facts by key or description.

        Args:
            query: Search string
            limit: Max results

        Returns:
            List of matching UserFact
        """
        rows = self._conn.execute(
            """SELECT * FROM user_facts 
               WHERE (key LIKE ? OR description LIKE ?) AND archived = 0
               ORDER BY priority DESC LIMIT ?""",
            (f"%{query}%", f"%{query}%", limit),
        ).fetchall()

        return [
            UserFact(
                id=row["id"],
                category=row["category"],
                priority=row["priority"],
                key=row["key"],
                value=json.loads(row["value"]),
                description=row["description"],
                source=row["source"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
                archived=bool(row["archived"]),
                version=row["version"],
                metadata=json.loads(row["metadata"]),
            )
            for row in rows
        ]

    # --------------------------------------------------------------------------
    # Maintenance
    # --------------------------------------------------------------------------

    def stats(self) -> Dict[str, Any]:
        """Get user memory statistics."""
        total = self._conn.execute("SELECT COUNT(*) FROM user_facts").fetchone()[0]
        active = self._conn.execute(
            "SELECT COUNT(*) FROM user_facts WHERE archived = 0"
        ).fetchone()[0]
        archived = self._conn.execute(
            "SELECT COUNT(*) FROM user_facts WHERE archived = 1"
        ).fetchone()[0]

        by_category = dict(
            self._conn.execute(
                "SELECT category, COUNT(*) FROM user_facts WHERE archived = 0 GROUP BY category"
            ).fetchall()
        )

        by_priority = dict(
            self._conn.execute(
                "SELECT priority, COUNT(*) FROM user_facts WHERE archived = 0 GROUP BY priority"
            ).fetchall()
        )

        return {
            "total_facts": total,
            "active_facts": active,
            "archived_facts": archived,
            "by_category": by_category,
            "by_priority": by_priority,
            "db_path": str(self._db_path),
            "db_size_bytes": self._db_path.stat().st_size
            if self._db_path.exists()
            else 0,
        }

    def close(self) -> None:
        """Close database connection."""
        self._conn.close()


# ============================================================================
# Convenience Factory
# ============================================================================


def get_user_memory() -> UserMemoryStore:
    """Get UserMemoryStore with framework data directory."""
    return UserMemoryStore()


# ============================================================================
# CLI Interface
# ============================================================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="PA Framework User Memory CLI")
    parser.add_argument("--stats", action="store_true", help="Show memory statistics")
    parser.add_argument("--list", type=str, help="List facts by category")
    parser.add_argument("--get", type=str, help="Get fact by key")
    parser.add_argument("--search", type=str, help="Search facts")
    parser.add_argument(
        "--set", nargs=3, metavar=("KEY", "VALUE", "DESCRIPTION"), help="Set a fact"
    )
    parser.add_argument("--archive", type=str, help="Archive a fact")

    args = parser.parse_args()

    store = get_user_memory()

    if args.stats:
        print(json.dumps(store.stats(), indent=2))

    if args.list:
        facts = store.list_facts(category=args.list)
        for f in facts:
            print(f"- [{f.priority}] {f.key}: {f.value}")
            if f.description:
                print(f"  {f.description}")

    if args.get:
        fact = store.get_fact(args.get)
        if fact:
            print(json.dumps(fact.to_dict(), indent=2))
        else:
            print(f"Fact not found: {args.get}")

    if args.search:
        facts = store.search(args.search)
        for f in facts:
            print(f"- {f.key}: {f.value}")

    if args.set:
        key, value, description = args.set
        store.set_fact(
            category="fact",
            priority="medium",
            key=key,
            value=value,
            description=description,
        )
        print(f"Set: {key} = {value}")

    if args.archive:
        store.archive_fact(args.archive)
        print(f"Archived: {args.archive}")

    store.close()
