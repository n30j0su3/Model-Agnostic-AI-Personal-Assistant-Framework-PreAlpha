#!/usr/bin/env python3
"""
Session Bridge - Connects session-start.py with SessionStore (SQLite memory)

This is the MISSING LINK that was preventing memory persistence.
Every session now automatically saves to SQLite + can be searched.

Usage:
    python session-bridge.py --start              # Start new session
    python session-bridge.py --search "alfa"      # Search all sessions
    python session-bridge.py --project "Alfa"     # Get project history
    python session-bridge.py --stats              # Show memory stats
    python session-bridge.py --add "user" "msg"   # Add message manually

Cross-platform: Works on Windows, Linux, macOS
"""

import sys
import os
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any


# ============================================================================
# Framework Data Directory (Cross-Platform)
# ============================================================================

def _get_framework_data_dir() -> Path:
    """Get framework data directory - works on Windows, Linux, macOS.
    
    Priority:
    1. PA_FRAMEWORK_DATA env var (if set)
    2. Framework installation directory (parent of core/scripts/)
    
    This ensures data persists WITH the framework, not in user home.
    """
    # Check env override first
    env_data = os.environ.get("PA_FRAMEWORK_DATA")
    if env_data:
        return Path(env_data)
    
    # Detect framework root from module location
    # core/scripts/session_bridge.py -> parent.parent = framework root
    module_dir = Path(__file__).parent  # core/scripts/
    framework_root = module_dir.parent.parent  # framework root (above core/)
    
    # Data directory inside framework
    data_dir = framework_root / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Add memory directory to path (CRITICAL for session_memory import)
MEMORY_DIR = Path(__file__).parent.parent / "memory"
if str(MEMORY_DIR) not in sys.path:
    sys.path.insert(0, str(MEMORY_DIR))

try:
    # Import directly from memory directory (path configured above)
    from session_memory import SessionStore, Session, SessionMessage, get_default_store
    MEMORY_AVAILABLE = True
except ImportError:
    MEMORY_AVAILABLE = False
    print("[BRIDGE] Warning: session_memory not available, using fallback")

# v0.3.7-alpha: User Memory integration (persistent facts)
try:
    from user_memory import get_user_memory, UserMemoryStore
    USER_MEMORY_AVAILABLE = True
except ImportError:
    USER_MEMORY_AVAILABLE = False
    print("[BRIDGE] Warning: user_memory not available")


class SessionBridge:
    """
    Bridge between PA Framework sessions and SQLite memory.
    
    This class ensures every session is persisted and searchable.
    It's the CORE of the memory system that was missing.
    """
    
    def __init__(self, store_path: Optional[str] = None):
        """Initialize bridge with SessionStore + UserMemoryStore (v0.3.7-alpha)"""
        if MEMORY_AVAILABLE:
            self.store = get_default_store()
        else:
            # Fallback: JSON file storage (in framework data dir)
            self.store = None
            self.fallback_path = Path(store_path or _get_framework_data_dir() / "sessions-fallback.json")
            self.fallback_path.parent.mkdir(parents=True, exist_ok=True)
            if not self.fallback_path.exists():
                self.fallback_path.write_text(json.dumps({"sessions": []}))
        
        # v0.3.7-alpha: User Memory for persistent facts
        self.user_memory: Optional[UserMemoryStore] = None
        if USER_MEMORY_AVAILABLE:
            self.user_memory = get_user_memory()
        
        self.current_session: Optional[str] = None
        self._session_metadata: Dict[str, Any] = {}
        
    def start_session(self, user_input: Optional[str] = None, metadata: Optional[Dict] = None) -> str:
        """
        Create new session and persist it.
        
        Args:
            user_input: Initial user message (optional)
            metadata: Additional session metadata
            
        Returns:
            Session ID
        """
        timestamp = datetime.now()
        session_id = f"session-{timestamp.strftime('%Y%m%d-%H%M%S')}"
        
        base_metadata = {
            "started_at": timestamp.isoformat(),
            "framework_version": "v0.3.7-alpha",
            "platform": sys.platform,
            "init_type": self._determine_init_type()
        }
        
        if metadata:
            base_metadata.update(metadata)
        
        if self.store:
            # Use SQLite SessionStore (correct API: get_or_create)
            session_obj = self.store.get_or_create(
                user_id="default_user",  # Can be overridden via metadata
                channel="cli"
            )
            self.current_session = session_obj.session_id
            
            # Update metadata if provided
            if metadata:
                session_obj.metadata.update(base_metadata)
            
            if user_input:
                self.store.add_message(
                    session_id=self.current_session,
                    role="user",
                    content=user_input,
                    metadata={"timestamp": timestamp.isoformat(), "type": "init"}
                )
        else:
            # Fallback: JSON storage
            self.current_session = session_id
            self._session_metadata = base_metadata
            self._save_fallback_session(session_id, base_metadata, user_input)
        
        # Log session start
        self._log_event("SESSION_START", session_id)
        
        return session_id
    
    def add_message(self, role: str, content: str, metadata: Optional[Dict] = None) -> bool:
        """
        Add message to current session.
        
        Args:
            role: Message role (user, assistant, system, tool)
            content: Message content
            metadata: Additional metadata
            
        Returns:
            Success status
        """
        if not self.current_session:
            print("[BRIDGE] Warning: No active session, message not saved")
            return False
        
        msg_metadata = {
            "timestamp": datetime.now().isoformat(),
            "type": "message"
        }
        if metadata:
            msg_metadata.update(metadata)
        
        if self.store:
            self.store.add_message(
                session_id=self.current_session,
                role=role,
                content=content,
                metadata=msg_metadata
            )
        else:
            # Fallback
            self._append_fallback_message(self.current_session, role, content, msg_metadata)
        
        return True
    
    def register_project(self, project_name: str, project_path: str, description: Optional[str] = None) -> bool:
        """
        Register a project in session memory.
        
        This is CRITICAL for memory - projects become searchable.
        
        Args:
            project_name: Project name (e.g., "Alfa")
            project_path: Project path
            description: Optional description
            
        Returns:
            Success status
        """
        if not self.current_session:
            print("[BRIDGE] Warning: No active session")
            return False
        
        # Add as system message
        project_msg = f"PROJECT_REGISTERED: {project_name}"
        if description:
            project_msg += f" | {description}"
        
        self.add_message(
            role="system",
            content=project_msg,
            metadata={
                "type": "project_registration",
                "project_name": project_name,
                "project_path": project_path,
                "description": description
            }
        )
        
        # Update session metadata
        if self.store:
            self.store.update_metadata(
                session_id=self.current_session,
                key=f"project_{project_name.lower()}",
                value=project_path
            )
        else:
            self._session_metadata[f"project_{project_name.lower()}"] = project_path
        
        # Also update registry file
        self._update_project_registry(project_name, project_path, description)
        
        self._log_event("PROJECT_REGISTERED", project_name)
        
        return True
    
    def end_session(self, summary: Optional[str] = None) -> bool:
        """
        End current session with optional summary.
        
        Args:
            summary: Session summary (optional)
            
        Returns:
            Success status
        """
        if not self.current_session:
            return False
        
        if summary:
            self.add_message(
                role="system",
                content=f"SESSION_SUMMARY: {summary}",
                metadata={"type": "summary", "timestamp": datetime.now().isoformat()}
            )
        
        if self.store:
            # SessionStore doesn't have close_session - sessions auto-managed via decay()
            # Mark session end by updating metadata
            try:
                session_obj = self.store.get_session(self.current_session)
                if session_obj:
                    session_obj.metadata["status"] = "closed"
                    session_obj.metadata["end_time"] = datetime.now().isoformat()
            except Exception:
                pass  # Ignore close errors
        else:
            # Fallback: mark session as closed
            self._close_fallback_session(self.current_session)
        
        self._log_event("SESSION_END", self.current_session)
        self.current_session = None
        
        return True
    
    def search_sessions(self, query: str, limit: int = 10) -> List[Dict]:
        """
        Search across all sessions for content.
        
        Args:
            query: Search query
            limit: Max results
            
        Returns:
            List of matching sessions/messages
        """
        if self.store:
            return self.store.search(query, limit=limit)
        else:
            # Fallback: search in JSON
            return self._search_fallback(query, limit)
    
    def get_project_history(self, project_name: str) -> List[Dict]:
        """
        Get all sessions mentioning a project.
        
        Args:
            project_name: Project name
            
        Returns:
            List of sessions/messages about project
        """
        return self.search_sessions(f"project_{project_name.lower()}")
    
    def get_stats(self) -> Dict:
        """
        Get memory statistics.
        
        Returns:
            Stats dictionary
        """
        if self.store:
            return self.store.stats()
        else:
            # Fallback stats
            data = json.loads(self.fallback_path.read_text())
            sessions = data.get("sessions", [])
            total_msgs = sum(len(s.get("messages", [])) for s in sessions)
            return {
                "total_sessions": len(sessions),
                "total_messages": total_msgs,
                "memory_type": "fallback_json",
                "fallback_path": str(self.fallback_path)
            }
    
    def get_recent_sessions(self, days: int = 7) -> List[str]:
        """
        Get recent session IDs.
        
        Args:
            days: Number of days to look back
            
        Returns:
            List of session IDs
        """
        if self.store:
            stats = self.store.stats()
            # Would need to implement in SessionStore
            return []
        else:
            cutoff = datetime.now() - timedelta(days=days)
            data = json.loads(self.fallback_path.read_text())
            recent = []
            for session in data.get("sessions", []):
                started = datetime.fromisoformat(session.get("metadata", {}).get("started_at", ""))
                if started > cutoff:
                    recent.append(session.get("session_id"))
            return recent
    
    # === User Memory Methods (v0.3.7-alpha) ===
    
    def get_user_facts(self, category: Optional[str] = None, priority: Optional[str] = None) -> List[Dict]:
        """
        Get user facts from persistent memory (v0.3.7-alpha).
        
        Args:
            category: Filter by category (project, preference, goal, fact, context)
            priority: Filter by priority (critical, high, medium, low)
            
        Returns:
            List of user facts as dicts
        """
        if not self.user_memory:
            return []
        
        facts = self.user_memory.list_facts(category=category, priority=priority)
        return [f.to_dict() for f in facts]
    
    def get_user_fact(self, key: str) -> Optional[Dict]:
        """
        Get a specific user fact by key (v0.3.7-alpha).
        
        Args:
            key: Fact key (e.g., "active_project")
            
        Returns:
            Fact dict or None
        """
        if not self.user_memory:
            return None
        
        fact = self.user_memory.get_fact(key)
        return fact.to_dict() if fact else None
    
    def set_user_fact(
        self,
        key: str,
        value: Any,
        category: str = "fact",
        priority: str = "medium",
        description: str = "",
        source: str = "user",
        metadata: Optional[Dict] = None
    ) -> Optional[Dict]:
        """
        Set a user fact in persistent memory (v0.3.7-alpha).
        
        Args:
            key: Unique key for the fact
            value: Value to store
            category: Category (preference, project, goal, fact, context)
            priority: Priority (critical, high, medium, low)
            description: Optional description
            source: Origin (user, system, derived)
            metadata: Optional metadata dict
            
        Returns:
            Created/updated fact dict
        """
        if not self.user_memory:
            return None
        
        fact = self.user_memory.set_fact(
            category=category,
            priority=priority,
            key=key,
            value=value,
            description=description,
            source=source,
            metadata=metadata
        )
        return fact.to_dict() if fact else None
    
    def archive_user_fact(self, key: str) -> bool:
        """
        Archive a user fact (soft delete) (v0.3.7-alpha).
        
        Args:
            key: Fact key to archive
            
        Returns:
            True if archived
        """
        if not self.user_memory:
            return False
        
        return self.user_memory.archive_fact(key)
    
    def get_user_context_summary(self) -> str:
        """
        Get formatted user context for session start (v0.3.7-alpha).
        
        Returns a concise summary of user facts suitable for
        injection into session context.
        
        Returns:
            Formatted string of user facts
        """
        if not self.user_memory:
            return ""
        
        facts = self.user_memory.list_facts(limit=10)
        if not facts:
            return ""
        
        lines = ["## User Context (Persistent Facts)"]
        for f in facts:
            lines.append(f"- **{f.key}**: {f.value}")
            if f.description:
                lines.append(f"  {f.description[:50]}...")
        
        return "\n".join(lines)
    
    def get_user_memory_stats(self) -> Dict:
        """
        Get user memory statistics (v0.3.7-alpha).
        
        Returns:
            User memory stats dict
        """
        if not self.user_memory:
            return {"available": False}
        
        stats = self.user_memory.stats()
        stats["available"] = True
        return stats
    
    # === Private Methods ===
    
    def _determine_init_type(self) -> str:
        """Determine if this is cold or warm start"""
        stats = self.get_stats()
        if stats.get("total_sessions", 0) == 0:
            return "cold"
        return "warm"
    
    def _log_event(self, event_type: str, event_data: str):
        """Log event to system log (in framework data dir)"""
        log_path = _get_framework_data_dir() / "bridge.log"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        log_entry = f"[{datetime.now().isoformat()}] {event_type}: {event_data}\n"
        log_path.write_text(log_path.read_text() + log_entry if log_path.exists() else log_entry)
    
    def _update_project_registry(self, name: str, path: str, description: Optional[str]):
        """Update projects registry file"""
        registry_path = Path(__file__).parent.parent / ".context" / "projects" / "_registry.md"
        registry_path.parent.mkdir(parents=True, exist_ok=True)
        
        entry = f"""
## {name}

| Campo | Valor |
|-------|-------|
| **Path** | {path} |
| **Registered** | {datetime.now().isoformat()} |
| **Description** | {description or 'No description'} |

"""
        
        current = registry_path.read_text() if registry_path.exists() else "# Projects Registry\n\nThis file tracks all registered projects.\n\n"
        if name not in current:  # Avoid duplicates
            registry_path.write_text(current + entry)
    
    # === Fallback Methods (JSON storage when SQLite unavailable) ===
    
    def _save_fallback_session(self, session_id: str, metadata: Dict, user_input: Optional[str]):
        """Save session to JSON fallback"""
        data = json.loads(self.fallback_path.read_text())
        
        session = {
            "session_id": session_id,
            "metadata": metadata,
            "messages": [],
            "status": "active"
        }
        
        if user_input:
            session["messages"].append({
                "role": "user",
                "content": user_input,
                "metadata": {"timestamp": datetime.now().isoformat(), "type": "init"}
            })
        
        data["sessions"].append(session)
        self.fallback_path.write_text(json.dumps(data, indent=2))
    
    def _append_fallback_message(self, session_id: str, role: str, content: str, metadata: Dict):
        """Append message to JSON fallback"""
        data = json.loads(self.fallback_path.read_text())
        
        for session in data["sessions"]:
            if session["session_id"] == session_id:
                session["messages"].append({
                    "role": role,
                    "content": content,
                    "metadata": metadata
                })
                break
        
        self.fallback_path.write_text(json.dumps(data, indent=2))
    
    def _close_fallback_session(self, session_id: str):
        """Mark session as closed in JSON fallback"""
        data = json.loads(self.fallback_path.read_text())
        
        for session in data["sessions"]:
            if session["session_id"] == session_id:
                session["status"] = "closed"
                session["metadata"]["ended_at"] = datetime.now().isoformat()
                break
        
        self.fallback_path.write_text(json.dumps(data, indent=2))
    
    def _search_fallback(self, query: str, limit: int) -> List[Dict]:
        """Search in JSON fallback"""
        data = json.loads(self.fallback_path.read_text())
        results = []
        query_lower = query.lower()
        
        for session in data.get("sessions", []):
            for msg in session.get("messages", []):
                if query_lower in msg.get("content", "").lower():
                    results.append({
                        "session_id": session["session_id"],
                        "role": msg["role"],
                        "content": msg["content"],
                        "metadata": msg.get("metadata", {})
                    })
                    if len(results) >= limit:
                        return results
        
        # Also search metadata
        for session in data.get("sessions", []):
            for key, value in session.get("metadata", {}).items():
                if query_lower in str(value).lower():
                    results.append({
                        "session_id": session["session_id"],
                        "type": "metadata",
                        "key": key,
                        "value": value
                    })
        
        return results[:limit]


# === CLI Interface ===

def main():
    """CLI interface for SessionBridge"""
    
    bridge = SessionBridge()
    
    if len(sys.argv) < 2:
        print(__doc__)
        return
    
    arg = sys.argv[1]
    
    if arg == "--start":
        session_id = bridge.start_session()
        print(f"[MEMORY] Session started: {session_id}")
        print(f"[MEMORY] Stats: {json.dumps(bridge.get_stats(), indent=2)}")
        
    elif arg == "--end":
        if len(sys.argv) > 2:
            summary = sys.argv[2]
            bridge.end_session(summary=summary)
        else:
            bridge.end_session()
        print("[MEMORY] Session ended")
        
    elif arg == "--search" and len(sys.argv) > 2:
        query = sys.argv[2]
        results = bridge.search_sessions(query)
        print(f"[MEMORY] Found {len(results)} results for '{query}':")
        print(json.dumps(results, indent=2))
        
    elif arg == "--project" and len(sys.argv) > 2:
        project_name = sys.argv[2]
        history = bridge.get_project_history(project_name)
        print(f"[MEMORY] Project '{project_name}' history:")
        print(json.dumps(history, indent=2))
        
    elif arg == "--stats":
        stats = bridge.get_stats()
        print("[MEMORY] Memory Statistics:")
        print(json.dumps(stats, indent=2))
        
    elif arg == "--register" and len(sys.argv) >= 4:
        project_name = sys.argv[2]
        project_path = sys.argv[3]
        description = sys.argv[4] if len(sys.argv) > 4 else None
        
        # Ensure session is active
        if not bridge.current_session:
            bridge.start_session()
        
        bridge.register_project(project_name, project_path, description)
        print(f"[MEMORY] Project registered: {project_name}")
        
    elif arg == "--add" and len(sys.argv) >= 4:
        role = sys.argv[2]
        content = sys.argv[3]
        
        if not bridge.current_session:
            bridge.start_session()
        
        bridge.add_message(role, content)
        print(f"[MEMORY] Message added: {role}")
        
    elif arg == "--recent":
        days = int(sys.argv[2]) if len(sys.argv) > 2 else 7
        recent = bridge.get_recent_sessions(days)
        print(f"[MEMORY] Recent sessions ({days} days):")
        for s in recent:
            print(f"  - {s}")
        
    else:
        print(__doc__)


if __name__ == "__main__":
    main()