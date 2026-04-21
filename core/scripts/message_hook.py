#!/usr/bin/env python3
"""
PA Framework — Message Hook for Real-Time Capture
====================================================

CRITICAL: This is the MISSING LINK that fixes the persistence system.

Problem discovered in audit:
- SessionBridge.add_message() exists but is NEVER called during conversations
- Messages only captured at session START/END, not during active chat
- Knowledge extraction fails because session files are empty

Solution:
- This module provides hooks that CLIs can integrate
- Captures every user/assistant message in real-time
- Persists to SQLite via SessionBridge

Integration Options:
====================

1. **Python Import** (for Python-based CLIs):
   ```python
   from message_hook import MessageHook
   
   hook = MessageHook()
   hook.capture("user", "¿Cómo implementar X?")
   hook.capture("assistant", "La solución es...")
   ```

2. **Shell Hook** (for any CLI via subprocess):
   ```bash
   python core/scripts/message_hook.py --capture "user" "mensaje"
   ```

3. **Environment Variable** (auto-capture mode):
   ```bash
   export PA_MESSAGE_HOOK=1
   # Messages written to framework/data/messages-buffer.json (cross-platform)
   ```

4. **Framework Integration**:
   - Load this module in your AI agent runtime
   - Auto-capture from session context

Architecture:
=============

MessageHook ──► SessionBridge ──► SessionStore (SQLite)
                     │
                     ▼
              sessions.db (data/sessions.db)

Cross-Platform: Works on Windows, Linux, macOS
Data Location: Framework directory (not user home)

Version: 1.0.0 (FASE 1 implementation)
Author: FreakingJSON-PA Framework
"""

import sys
import os
import json
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List, Any

# Add paths for imports
SCRIPT_DIR = Path(__file__).resolve().parent
CORE_DIR = SCRIPT_DIR.parent
MEMORY_DIR = CORE_DIR / "memory"

if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))
if str(MEMORY_DIR) not in sys.path:
    sys.path.insert(0, str(MEMORY_DIR))

# Import SessionBridge
try:
    from session_bridge import SessionBridge, _get_framework_data_dir
    SESSION_BRIDGE_AVAILABLE = True
except ImportError:
    SESSION_BRIDGE_AVAILABLE = False
    print("[HOOK] Warning: SessionBridge not available, using fallback")


class MessageHook:
    """
    Real-time message capture hook for PA Framework.
    
    This is the component that was MISSING - it captures messages
    during conversations and persists them via SessionBridge.
    
    Usage:
        hook = MessageHook()
        hook.start_session()  # Creates session in SQLite
        hook.capture("user", "message")  # Captures user input
        hook.capture("assistant", "response")  # Captures AI response
        hook.end_session()  # Closes and saves
    """
    
    _instance: Optional['MessageHook'] = None
    
    def __init__(self, auto_start: bool = True):
        """
        Initialize message hook.
        
        Args:
            auto_start: Automatically start session on init (default: True)
        """
        self.bridge: Optional[SessionBridge] = None
        self.session_active: bool = False
        self.message_count: int = 0
        self._buffer: List[Dict] = []  # Fallback buffer
        
        if SESSION_BRIDGE_AVAILABLE:
            self.bridge = SessionBridge()
        
        if auto_start:
            self.start_session()
    
    @classmethod
    def get_instance(cls) -> 'MessageHook':
        """Get singleton instance (for global hook usage)."""
        if cls._instance is None:
            cls._instance = cls(auto_start=False)
        return cls._instance
    
    def start_session(self, metadata: Optional[Dict] = None) -> str:
        """
        Start a new capture session.
        
        Args:
            metadata: Optional session metadata
            
        Returns:
            Session ID
        """
        if self.session_active:
            return self.bridge.current_session if self.bridge else "fallback"
        
        base_metadata = {
            "hook_version": "1.0.0",
            "capture_mode": "real_time",
            "started_by": "message_hook"
        }
        if metadata:
            base_metadata.update(metadata)
        
        session_id = "none"
        
        if self.bridge:
            session_id = self.bridge.start_session(metadata=base_metadata)
            self.session_active = True
            self._log("SESSION_START", session_id)
        else:
            # Fallback: use buffer
            session_id = f"fallback-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
            self.session_active = True
            self._buffer.append({
                "type": "session_start",
                "session_id": session_id,
                "metadata": base_metadata,
                "timestamp": datetime.now().isoformat()
            })
            self._save_buffer()
            self._log("SESSION_START_FALLBACK", session_id)
        
        return session_id
    
    def capture(self, role: str, content: str, metadata: Optional[Dict] = None) -> bool:
        """
        Capture a message in real-time.
        
        THIS IS THE KEY METHOD - call this for every message.
        
        Args:
            role: Message role (user, assistant, system, tool)
            content: Message content
            metadata: Optional metadata (tags, context, etc.)
            
        Returns:
            Success status
        """
        if not self.session_active:
            # Auto-start if not active
            self.start_session()
        
        # Sanitize content
        content = self._sanitize_content(content)
        
        # Add capture metadata
        capture_meta = {
            "capture_timestamp": datetime.now().isoformat(),
            "capture_source": "message_hook",
            "message_index": self.message_count
        }
        if metadata:
            capture_meta.update(metadata)
        
        success = False
        
        if self.bridge:
            success = self.bridge.add_message(role, content, capture_meta)
            if success:
                self.message_count += 1
                self._log("CAPTURE", f"{role}: {len(content)} chars")
        else:
            # Fallback: append to buffer
            self._buffer.append({
                "type": "message",
                "role": role,
                "content": content,
                "metadata": capture_meta,
                "timestamp": datetime.now().isoformat()
            })
            self.message_count += 1
            self._save_buffer()
            success = True
            self._log("CAPTURE_FALLBACK", f"{role}: {len(content)} chars")
        
        return success
    
    def capture_batch(self, messages: List[Dict]) -> int:
        """
        Capture multiple messages at once.
        
        Args:
            messages: List of {role, content, metadata?} dicts
            
        Returns:
            Number of messages captured
        """
        captured = 0
        for msg in messages:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            metadata = msg.get("metadata")
            if self.capture(role, content, metadata):
                captured += 1
        return captured
    
    def end_session(self, summary: Optional[str] = None) -> bool:
        """
        End capture session.
        
        Args:
            summary: Optional session summary
            
        Returns:
            Success status
        """
        if not self.session_active:
            return False
        
        # Add summary if provided
        if summary:
            self.capture("system", f"SESSION_SUMMARY: {summary}")
        
        # Add session stats
        stats_msg = f"SESSION_STATS: {self.message_count} messages captured"
        self.capture("system", stats_msg, {"type": "stats"})
        
        success = False
        
        if self.bridge:
            success = self.bridge.end_session(summary=summary)
            self._log("SESSION_END", f"{self.message_count} messages")
        else:
            # Save final buffer
            self._buffer.append({
                "type": "session_end",
                "message_count": self.message_count,
                "timestamp": datetime.now().isoformat()
            })
            self._save_buffer()
            success = True
            self._log("SESSION_END_FALLBACK", f"{self.message_count} messages")
        
        self.session_active = False
        self.message_count = 0
        
        return success
    
    def get_stats(self) -> Dict:
        """
        Get capture statistics.
        
        Returns:
            Stats dictionary
        """
        stats = {
            "session_active": self.session_active,
            "messages_captured": self.message_count,
            "bridge_available": self.bridge is not None,
            "hook_version": "1.0.0"
        }
        
        if self.bridge:
            bridge_stats = self.bridge.get_stats()
            stats["bridge_stats"] = bridge_stats
        
        return stats
    
    # === Private Methods ===
    
    def _sanitize_content(self, content: str) -> str:
        """Sanitize message content."""
        # Remove excessive whitespace
        content = content.strip()
        # Limit length (prevent huge messages)
        max_len = 50000  # 50KB max
        if len(content) > max_len:
            content = content[:max_len] + "... [TRUNCATED]"
        return content
    
    def _log(self, event: str, data: str):
        """Log capture event."""
        log_path = _get_framework_data_dir() / "hook.log"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        entry = f"[{datetime.now().isoformat()}] {event}: {data}\n"
        current = log_path.read_text() if log_path.exists() else ""
        log_path.write_text(current + entry)
    
    def _save_buffer(self):
        """Save fallback buffer to JSON."""
        if not self._buffer:
            return
        
        buffer_path = _get_framework_data_dir() / "messages-buffer.json"
        buffer_path.parent.mkdir(parents=True, exist_ok=True)
        
        data = {
            "buffer": self._buffer,
            "last_updated": datetime.now().isoformat()
        }
        buffer_path.write_text(json.dumps(data, indent=2))


# === Singleton Global Hook ===

_global_hook: Optional[MessageHook] = None


def get_hook() -> MessageHook:
    """Get global message hook instance."""
    global _global_hook
    if _global_hook is None:
        _global_hook = MessageHook(auto_start=True)
    return _global_hook


def quick_capture(role: str, content: str) -> bool:
    """
    Quick capture function - use this for simple captures.
    
    Usage:
        from message_hook import quick_capture
        quick_capture("user", "my message")
    
    Args:
        role: Message role
        content: Message content
        
    Returns:
        Success status
    """
    hook = get_hook()
    return hook.capture(role, content)


# === CLI Interface ===

def main():
    """CLI interface for MessageHook."""
    
    if len(sys.argv) < 2:
        print(__doc__)
        return
    
    arg = sys.argv[1]
    
    hook = MessageHook(auto_start=False)
    
    if arg == "--start":
        session_id = hook.start_session()
        print(f"[HOOK] Session started: {session_id}")
        
    elif arg == "--capture" and len(sys.argv) >= 4:
        role = sys.argv[2]
        content = sys.argv[3]
        metadata = json.loads(sys.argv[4]) if len(sys.argv) > 4 else None
        success = hook.capture(role, content, metadata)
        print(f"[HOOK] Captured: {role} ({len(content)} chars) - {success}")
        
    elif arg == "--end":
        summary = sys.argv[2] if len(sys.argv) > 2 else None
        success = hook.end_session(summary)
        print(f"[HOOK] Session ended: {success}")
        
    elif arg == "--stats":
        stats = hook.get_stats()
        print(json.dumps(stats, indent=2))
        
    elif arg == "--batch" and len(sys.argv) >= 3:
        # Batch capture from JSON file
        json_path = sys.argv[2]
        messages = json.loads(Path(json_path).read_text())
        captured = hook.capture_batch(messages)
        print(f"[HOOK] Captured {captured} messages")
        
    else:
        print(f"[HOOK] Unknown command: {arg}")
        print(__doc__)


if __name__ == "__main__":
    main()