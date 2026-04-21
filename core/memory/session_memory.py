"""
Session Memory Module — SQLite-backed session persistence with consolidation and decay.

Based on OpenJarvis pattern (April 2026 research synthesis).
Part of PA Framework v0.3.0-alpha.

Features:
- Zero-config SQLite persistence
- Automatic consolidation when message threshold exceeded
- Decay removes stale sessions after configurable age
- Cross-channel identity support (Discord, CLI, web map to same user)
"""

import os  # For environ check
from dataclasses import dataclass, field
from pathlib import Path
import sqlite3
import json
import time
import uuid
from typing import Optional, List, Dict, Any


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
    # Check env override first
    env_data = os.environ.get("PA_FRAMEWORK_DATA")
    if env_data:
        return Path(env_data)
    
    # Detect framework root from module location
    # core/memory/session_memory.py -> parent.parent = framework root
    module_dir = Path(__file__).parent  # core/memory/
    framework_root = module_dir.parent.parent  # framework root (above core/)
    
    # Data directory inside framework
    data_dir = framework_root / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


# ============================================================================
# Data Models
# ============================================================================

@dataclass(slots=True)
class SessionMessage:
    """Single message within a session."""
    role: str           # "user" | "assistant" | "system"
    content: str
    channel: str = ""   # "discord" | "telegram" | "cli" | "web"
    timestamp: float = 0.0
    metadata: dict = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        return {
            "role": self.role,
            "content": self.content,
            "channel": self.channel,
            "timestamp": self.timestamp,
            "metadata": self.metadata,
        }


@dataclass
class Session:
    """Active conversation session."""
    session_id: str = ""
    user_id: str = ""
    messages: List[SessionMessage] = field(default_factory=list)
    created_at: float = 0.0
    last_activity: float = 0.0
    metadata: dict = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "messages": [m.to_dict() for m in self.messages],
            "created_at": self.created_at,
            "last_activity": self.last_activity,
            "metadata": self.metadata,
        }


# ============================================================================
# Session Store (SQLite-backed)
# ============================================================================

class SessionStore:
    """SQLite-backed session persistence with consolidation and decay.
    
    Usage:
        store = SessionStore(Path("~/.pa-framework/sessions.db"))
        
        # Create/get session
        session = store.get_or_create(user_id="user123", channel="discord")
        
        # Add messages
        store.add_message(session.session_id, "user", "Hello!")
        store.add_message(session.session_id, "assistant", "Hi there!")
        
        # Retrieve session history
        history = store.get_session(session.session_id)
        
        # Automatic cleanup
        store.decay(max_age_hours=24)  # Remove sessions older than 24h
    """
    
    def __init__(
        self,
        db_path: Path = None,
        *,
        max_age_hours: float = 24.0,
        consolidation_threshold: int = 100,
    ) -> None:
        """Initialize session store.
        
        Args:
            db_path: Path to SQLite database file (default: ~/.pa-framework/sessions.db)
            max_age_hours: Hours before session decay (default: 24)
            consolidation_threshold: Message count trigger for consolidation (default: 100)
        """
        if db_path is None:
            # Use framework data directory (cross-platform)
            db_path = _get_framework_data_dir() / "sessions.db"
        self._db_path = Path(db_path)
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self._db_path), check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._max_age_hours = max_age_hours
        self._consolidation_threshold = consolidation_threshold
        self._create_tables()
    
    def _create_tables(self) -> None:
        """Create database tables if they don't exist."""
        self._conn.executescript("""
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                created_at REAL NOT NULL,
                last_activity REAL NOT NULL,
                metadata TEXT DEFAULT '{}'
            );
            
            CREATE TABLE IF NOT EXISTS session_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                channel TEXT DEFAULT '',
                timestamp REAL NOT NULL,
                metadata TEXT DEFAULT '{}',
                FOREIGN KEY (session_id) REFERENCES sessions(session_id)
            );
            
            CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user_id);
            CREATE INDEX IF NOT EXISTS idx_sessions_activity ON sessions(last_activity);
            CREATE INDEX IF NOT EXISTS idx_messages_session ON session_messages(session_id);
            CREATE INDEX IF NOT EXISTS idx_messages_timestamp ON session_messages(timestamp);
        """)
        self._conn.commit()
    
    # --------------------------------------------------------------------------
    # Session CRUD
    # --------------------------------------------------------------------------
    
    def get_or_create(
        self,
        user_id: str,
        channel: str = "",
        session_id: Optional[str] = None,
    ) -> Session:
        """Get existing session or create new one.
        
        Args:
            user_id: User identifier (cross-channel identity)
            channel: Communication channel (discord, telegram, cli, web)
            session_id: Optional existing session ID to resume
            
        Returns:
            Session object with messages loaded
        """
        if session_id:
            existing = self.get_session(session_id)
            if existing and existing.user_id == user_id:
                return existing
        
        # Create new session
        new_id = session_id or str(uuid.uuid4())
        now = time.time()
        
        self._conn.execute(
            "INSERT OR REPLACE INTO sessions (session_id, user_id, created_at, last_activity, metadata) "
            "VALUES (?, ?, ?, ?, '{}')",
            (new_id, user_id, now, now),
        )
        self._conn.commit()
        
        return Session(
            session_id=new_id,
            user_id=user_id,
            messages=[],
            created_at=now,
            last_activity=now,
        )
    
    def get_session(self, session_id: str) -> Optional[Session]:
        """Retrieve session by ID with all messages."""
        row = self._conn.execute(
            "SELECT * FROM sessions WHERE session_id = ?",
            (session_id,),
        ).fetchone()
        
        if not row:
            return None
        
        messages = self._load_messages(session_id)
        
        return Session(
            session_id=row["session_id"],
            user_id=row["user_id"],
            messages=messages,
            created_at=row["created_at"],
            last_activity=row["last_activity"],
            metadata=json.loads(row["metadata"]),
        )
    
    def get_user_sessions(self, user_id: str, limit: int = 10) -> List[Session]:
        """Get recent sessions for a user."""
        rows = self._conn.execute(
            "SELECT session_id FROM sessions WHERE user_id = ? "
            "ORDER BY last_activity DESC LIMIT ?",
            (user_id, limit),
        ).fetchall()
        
        sessions = []
        for row in rows:
            session = self.get_session(row["session_id"])
            if session:
                sessions.append(session)
        
        return sessions
    
    def _load_messages(self, session_id: str) -> List[SessionMessage]:
        """Load all messages for a session."""
        rows = self._conn.execute(
            "SELECT * FROM session_messages WHERE session_id = ? "
            "ORDER BY timestamp ASC",
            (session_id,),
        ).fetchall()
        
        return [
            SessionMessage(
                role=row["role"],
                content=row["content"],
                channel=row["channel"],
                timestamp=row["timestamp"],
                metadata=json.loads(row["metadata"]),
            )
            for row in rows
        ]
    
    # --------------------------------------------------------------------------
    # Message Operations
    # --------------------------------------------------------------------------
    
    def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        channel: str = "",
        metadata: dict = None,
    ) -> SessionMessage:
        """Add message to session.
        
        Args:
            session_id: Target session
            role: "user" | "assistant" | "system"
            content: Message content
            channel: Communication channel
            metadata: Optional metadata dict
            
        Returns:
            Created SessionMessage
        """
        now = time.time()
        meta_json = json.dumps(metadata or {})
        
        self._conn.execute(
            "INSERT INTO session_messages (session_id, role, content, channel, timestamp, metadata) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (session_id, role, content, channel, now, meta_json),
        )
        self._conn.execute(
            "UPDATE sessions SET last_activity = ? WHERE session_id = ?",
            (now, session_id),
        )
        self._conn.commit()
        
        # Check consolidation threshold
        msg_count = self._conn.execute(
            "SELECT COUNT(*) FROM session_messages WHERE session_id = ?",
            (session_id,),
        ).fetchone()[0]
        
        if msg_count >= self._consolidation_threshold:
            self.consolidate(session_id)
        
        return SessionMessage(
            role=role,
            content=content,
            channel=channel,
            timestamp=now,
            metadata=metadata or {},
        )
    
    def get_recent_messages(
        self,
        session_id: str,
        limit: int = 20,
    ) -> List[SessionMessage]:
        """Get most recent messages from session."""
        rows = self._conn.execute(
            "SELECT * FROM session_messages WHERE session_id = ? "
            "ORDER BY timestamp DESC LIMIT ?",
            (session_id, limit),
        ).fetchall()
        
        # Reverse to get chronological order
        return [
            SessionMessage(
                role=row["role"],
                content=row["content"],
                channel=row["channel"],
                timestamp=row["timestamp"],
                metadata=json.loads(row["metadata"]),
            )
            for row in reversed(rows)
        ]
    
    # --------------------------------------------------------------------------
    # Consolidation & Decay
    # --------------------------------------------------------------------------
    
    def consolidate(self, session_id: str) -> None:
        """Summarize oldest half of messages, keep recent half.
        
        When message count exceeds threshold, create a summary of older
        messages and delete them, keeping recent context intact.
        """
        messages = self._load_messages(session_id)
        if len(messages) <= self._consolidation_threshold // 2:
            return
        
        split = len(messages) // 2
        old_messages = messages[:split]
        
        # Create summary (simple truncation for now, could use LLM)
        summary_parts = []
        for m in old_messages[-20:]:  # Last 20 of old half
            preview = m.content[:100] if len(m.content) > 100 else m.content
            summary_parts.append(f"[{m.role}] {preview}")
        
        summary = "Session history summary:\n" + "\n".join(summary_parts)
        
        # Delete old messages
        oldest_ts = old_messages[-1].timestamp
        self._conn.execute(
            "DELETE FROM session_messages WHERE session_id = ? AND timestamp <= ?",
            (session_id, oldest_ts),
        )
        
        # Insert summary as system message
        self._conn.execute(
            "INSERT INTO session_messages (session_id, role, content, timestamp) "
            "VALUES (?, 'system', ?, ?)",
            (session_id, summary, time.time()),
        )
        self._conn.commit()
    
    def decay(self, max_age_hours: float = None) -> int:
        """Remove expired sessions. Returns count of sessions removed.
        
        Args:
            max_age_hours: Override default max age
            
        Returns:
            Number of sessions deleted
        """
        age = max_age_hours or self._max_age_hours
        cutoff = time.time() - (age * 3600)
        
        # Get expired session IDs
        expired = self._conn.execute(
            "SELECT session_id FROM sessions WHERE last_activity < ?",
            (cutoff,),
        ).fetchall()
        
        count = len(expired)
        
        if count > 0:
            # Delete messages first (foreign key constraint)
            session_ids = [row["session_id"] for row in expired]
            self._conn.execute(
                "DELETE FROM session_messages WHERE session_id IN ({})".format(
                    ",".join("?" * len(session_ids))
                ),
                session_ids,
            )
            self._conn.execute(
                "DELETE FROM sessions WHERE session_id IN ({})".format(
                    ",".join("?" * len(session_ids))
                ),
                session_ids,
            )
            self._conn.commit()
        
        return count
    
    # --------------------------------------------------------------------------
    # Stats & Maintenance
    # --------------------------------------------------------------------------
    
    def stats(self) -> Dict[str, Any]:
        """Get session store statistics."""
        sessions = self._conn.execute("SELECT COUNT(*) FROM sessions").fetchone()[0]
        messages = self._conn.execute("SELECT COUNT(*) FROM session_messages").fetchone()[0]
        oldest = self._conn.execute(
            "SELECT MIN(created_at) FROM sessions"
        ).fetchone()[0] or 0
        
        return {
            "total_sessions": sessions,
            "total_messages": messages,
            "oldest_session": oldest,
            "db_path": str(self._db_path),
            "db_size_bytes": self._db_path.stat().st_size if self._db_path.exists() else 0,
        }
    
    # --------------------------------------------------------------------------
    # Resilience (Phase 3)
    # --------------------------------------------------------------------------
    
    def integrity_check(self) -> Dict[str, Any]:
        """Check database integrity and return status report.
        
        Returns:
            Dict with 'ok', 'errors', 'orphan_messages', 'orphan_sessions'
        """
        result = {"ok": True, "errors": [], "orphan_messages": 0, "orphan_sessions": 0}
        
        try:
            # SQLite integrity check
            integrity = self._conn.execute("PRAGMA integrity_check").fetchone()[0]
            if integrity != "ok":
                result["ok"] = False
                result["errors"].append(f"SQLite integrity: {integrity}")
            
            # Check for orphan messages (messages without session)
            orphans = self._conn.execute(
                "SELECT COUNT(*) FROM session_messages sm "
                "WHERE NOT EXISTS (SELECT 1 FROM sessions s WHERE s.session_id = sm.session_id)"
            ).fetchone()[0]
            result["orphan_messages"] = orphans
            
            # Check for sessions without messages (empty sessions)
            empty = self._conn.execute(
                "SELECT COUNT(*) FROM sessions s "
                "WHERE NOT EXISTS (SELECT 1 FROM session_messages sm WHERE sm.session_id = s.session_id)"
            ).fetchone()[0]
            result["orphan_sessions"] = empty
            
            if orphans > 0 or empty > 10:  # Allow some empty sessions
                result["ok"] = False
                
        except Exception as e:
            result["ok"] = False
            result["errors"].append(str(e))
        
        return result
    
    def repair(self) -> Dict[str, Any]:
        """Auto-repair common issues. Returns repair report."""
        report = {"fixed_orphans": 0, "fixed_empty": 0, "vacuumed": False}
        
        try:
            # Remove orphan messages
            self._conn.execute(
                "DELETE FROM session_messages WHERE session_id NOT IN "
                "(SELECT session_id FROM sessions)"
            )
            report["fixed_orphans"] = self._conn.execute(
                "SELECT changes()"
            ).fetchone()[0]
            
            # Remove sessions older than 7 days with no messages
            cutoff = time.time() - (7 * 24 * 3600)
            self._conn.execute(
                "DELETE FROM sessions WHERE last_activity < ? "
                "AND session_id NOT IN (SELECT DISTINCT session_id FROM session_messages)"
            )
            report["fixed_empty"] = self._conn.execute(
                "SELECT changes()"
            ).fetchone()[0]
            
            # Vacuum to reclaim space
            self._conn.execute("VACUUM")
            report["vacuumed"] = True
            
            self._conn.commit()
            
        except Exception:
            pass
        
        return report
    
    def backup(self, backup_path: Path = None) -> bool:
        """Create backup of database file.
        
        Args:
            backup_path: Optional custom backup location
            
        Returns:
            True if backup succeeded
        """
        import shutil
        
        if not self._db_path.exists():
            return False
        
        backup = backup_path or self._db_path.with_suffix(".db.bak")
        
        try:
            # Close connection first
            self._conn.close()
            shutil.copy2(self._db_path, backup)
            # Reopen connection
            self._conn = sqlite3.connect(str(self._db_path))
            self._conn.row_factory = sqlite3.Row
            return True
        except Exception:
            return False
    
    def close(self) -> None:
        """Close database connection."""
        self._conn.close()


# ============================================================================
# Convenience Factory
# ============================================================================

def get_default_store() -> SessionStore:
    """Get SessionStore with framework data directory.
    
    Default location: <framework_root>/data/sessions.db
    Works on Windows, Linux, macOS - data stays WITH framework.
    """
    return SessionStore()  # Uses _get_framework_data_dir() by default


# ============================================================================
# CLI Test Interface
# ============================================================================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="PA Framework Session Memory CLI")
    parser.add_argument("--stats", action="store_true", help="Show session statistics")
    parser.add_argument("--decay", type=float, help="Run decay with custom max age (hours)")
    parser.add_argument("--list", type=str, help="List sessions for user ID")
    
    args = parser.parse_args()
    
    store = get_default_store()
    
    if args.stats:
        print(json.dumps(store.stats(), indent=2))
    
    if args.decay:
        removed = store.decay(args.decay)
        print(f"Removed {removed} expired sessions")
    
    if args.list:
        sessions = store.get_user_sessions(args.list)
        for s in sessions:
            print(f"- {s.session_id}: {len(s.messages)} messages, last: {s.last_activity}")
    
    store.close()


# ============================================================================
# SessionContentSQLite — Adapter for PatternDetector Integration
# ============================================================================

class SessionContentSQLite:
    """Adapter: Session → Markdown format for PatternDetector.
    
    Converts Session.messages to markdown format that PatternDetector
    can parse (same format as session markdown files).
    
    This enables PatternDetector to work with SQLite-backed sessions
    without modifying its file-based parsing logic.
    
    Properties match SessionContent interface (duck typing):
    - path: db_path (for reference)
    - name: session_id  
    - raw: formatted markdown string
    - lines: raw.split("\\n")
    
    Usage:
        store = SessionStore()
        session = store.get_session("session_id")
        adapter = SessionContentSQLite(session, store._db_path)
        
        # Now PatternDetector can use it:
        detector = PatternDetector()
        prompts = detector.extract_prompts(adapter)
        ideas = detector.extract_ideas(adapter)
    """
    
    def __init__(self, session: Session, db_path: Path = None):
        """Initialize adapter for a Session.
        
        Args:
            session: Session object with messages to format
            db_path: Optional database path (for path property)
        """
        self._session = session
        self._db_path = db_path or Path("sqlite://memory")
        self._raw: Optional[str] = None
        self._lines: Optional[List[str]] = None
    
    @property
    def path(self) -> Path:
        """Path reference (database location)."""
        return self._db_path
    
    @property
    def name(self) -> str:
        """Session identifier."""
        return self._session.session_id
    
    @property
    def raw(self) -> str:
        """Formatted markdown content (lazy)."""
        if self._raw is None:
            self._raw = self._format_messages()
        return self._raw
    
    @property
    def lines(self) -> List[str]:
        """Lines for PatternDetector parsing (lazy)."""
        if self._lines is None:
            self._lines = self.raw.split("\n")
        return self._lines
    
    def _format_messages(self) -> str:
        """Format Session.messages as markdown.
        
        Format matches session file format PatternDetector expects:
        - [user] user message content
        - [assistant] assistant response
        - [system] system context
        
        Also includes metadata as comments for debugging.
        """
        parts = []
        
        # Header with session metadata
        parts.append(f"# Session: {self._session.session_id}")
        parts.append(f"# User: {self._session.user_id}")
        parts.append(f"# Created: {self._session.created_at}")
        parts.append("")
        
        for m in self._session.messages:
            # Role prefix matching PatternDetector format
            role_marker = f"[{m.role}]"
            
            # Add channel info if present (as comment)
            if m.channel:
                parts.append(f"<!-- channel: {m.channel} -->")
            
            # Main content
            parts.append(f"{role_marker} {m.content}")
            parts.append("")
        
        return "\n".join(parts)
    
    def invalidate(self) -> None:
        """Clear cached formatting (reload from session)."""
        self._raw = None
        self._lines = None
    
    def __repr__(self) -> str:
        return f"SessionContentSQLite({self.name}, {len(self._session.messages)} msgs)"