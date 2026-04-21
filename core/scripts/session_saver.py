#!/usr/bin/env python3
"""
PA Framework — Session Saver (Checkpoint System)
================================================
Lightweight cron-like script that saves session state periodically.

Usage:
    python core/scripts/session-saver.py              # Save checkpoint
    python core/scripts/session-saver.py --check     # Verify checkpoint system
    python core/scripts/session-saver.py --status     # Show current checkpoint status

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
SESSIONS_DIR = CONTEXT_DIR / "sessions"
CHECKPOINTS_DIR = CONTEXT_DIR / "checkpoints"


def ensure_dirs():
    """Ensure required directories exist."""
    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
    CHECKPOINTS_DIR.mkdir(parents=True, exist_ok=True)


def get_today_session() -> Optional[Path]:
    """Get today's session file path."""
    today = datetime.now().strftime("%Y-%m-%d")
    session_file = SESSIONS_DIR / f"{today}.md"
    return session_file if session_file.exists() else None


def extract_pending_tasks(content: str) -> List[str]:
    """Extract pending tasks from session content."""
    pending = []
    # Look for unchecked items: - [ ]
    matches = re.findall(r"-\s+\[\s*\]\s*(.+?)(?:\n|$)", content)
    for m in matches[:10]:  # Max 10
        task = m.strip()
        if task and len(task) < 200:
            pending.append(task)
    return pending


def extract_recent_decisions(content: str) -> List[str]:
    """Extract recent decisions from session content."""
    decisions = []
    # Look for decisions section or patterns like "Decidimos:", "Decision:", "- Decision"
    patterns = [
        r"(?:Decidimos|Decision|Aprobado|Implementar)[:\s]+(.+?)(?:\n|-二世|\Z)",
        r"##\s+Decisiones.*?\n(.+?)(?=\n##|\Z)",
    ]
    for pattern in patterns:
        matches = re.findall(pattern, content, re.IGNORECASE | re.DOTALL)
        for m in matches[:5]:
            line = m.strip().split("\n")[0][:100]
            if line and line not in decisions:
                decisions.append(line)
    return decisions[:5]


def extract_topics(content: str) -> List[str]:
    """Extract topics discussed in session."""
    topics = []
    # Look for topic patterns
    patterns = [
        r"##\s+Temas?\s*Tratados.*?\n(.+?)(?=\n##|\Z)",
        r"topics?[:\s]+\[?([^\]]+)\]?",
    ]
    for pattern in patterns:
        matches = re.findall(pattern, content, re.IGNORECASE | re.DOTALL)
        for m in matches:
            items = re.findall(r"[-*]\s*(.+?)(?:\n|$)", m)
            for item in items[:5]:
                topic = item.strip()[:50]
                if topic and topic not in topics:
                    topics.append(topic)
    return topics[:10]


def extract_files_modified(content: str) -> List[str]:
    """Extract file paths mentioned in session."""
    files = set()
    patterns = [
        r"`([^`]+\.(?:py|md|json|js|html|css|sh|bat|yaml|yml))`",
        r"(?:archivo|file|modificado)\s*:?\s*`?([^`\n]+\.(?:py|md|json|js|html|css|sh|bat))`?",
    ]
    for pattern in patterns:
        matches = re.findall(pattern, content, re.IGNORECASE)
        files.update(matches)
    return list(files)[:20]


def save_checkpoint(session_file: Path) -> bool:
    """
    Save a checkpoint of the current session state.
    Returns True if successful, False otherwise.
    """
    try:
        content = session_file.read_text(encoding="utf-8")
        now = datetime.now()

        checkpoint = {
            "timestamp": now.isoformat(),
            "date": now.strftime("%Y-%m-%d"),
            "time": now.strftime("%H:%M:%S"),
            "session_file": str(session_file.name),
            "pending_tasks": extract_pending_tasks(content),
            "decisions": extract_recent_decisions(content),
            "topics": extract_topics(content),
            "files_modified": extract_files_modified(content),
            "word_count": len(content.split()),
            "last_modified": None,
        }

        # Get last modified time of session file
        try:
            checkpoint["last_modified"] = datetime.fromtimestamp(
                session_file.stat().st_mtime
            ).isoformat()
        except Exception:
            pass

        # Save checkpoint
        checkpoint_file = CHECKPOINTS_DIR / f"checkpoint_{now.strftime('%Y%m%d_%H%M%S')}.json"
        checkpoint_file.write_text(
            json.dumps(checkpoint, indent=2, ensure_ascii=False),
            encoding="utf-8"
        )

        # Also save as "latest" checkpoint
        latest_file = CHECKPOINTS_DIR / "latest.json"
        latest_file.write_text(
            json.dumps(checkpoint, indent=2, ensure_ascii=False),
            encoding="utf-8"
        )

        return True
    except Exception as e:
        print(f"[ERROR] Failed to save checkpoint: {e}")
        return False


def get_checkpoint_status() -> Dict:
    """Get status of checkpoint system."""
    status = {
        "checkpoints_dir_exists": CHECKPOINTS_DIR.exists(),
        "checkpoint_count": 0,
        "latest_checkpoint": None,
        "today_session_exists": False,
        "today_checkpoint_exists": False,
    }

    if CHECKPOINTS_DIR.exists():
        checkpoints = sorted(CHECKPOINTS_DIR.glob("checkpoint_*.json"), reverse=True)
        status["checkpoint_count"] = len(checkpoints)
        if checkpoints:
            status["latest_checkpoint"] = checkpoints[0].name

    today = datetime.now().strftime("%Y-%m-%d")
    session_file = SESSIONS_DIR / f"{today}.md"
    status["today_session_exists"] = session_file.exists()

    latest_file = CHECKPOINTS_DIR / "latest.json"
    if latest_file.exists():
        try:
            latest = json.loads(latest_file.read_text(encoding="utf-8"))
            status["today_checkpoint_exists"] = latest.get("date") == today
        except Exception:
            pass

    return status


def verify_system():
    """Verify checkpoint system is working."""
    print("=" * 50)
    print("Session Saver - System Verification")
    print("=" * 50)

    status = get_checkpoint_status()

    print(f"\nCheckpoint Directory: {CHECKPOINTS_DIR}")
    print(f"  Exists: {status['checkpoints_dir_exists']}")
    print(f"  Total Checkpoints: {status['checkpoint_count']}")
    print(f"  Latest: {status['latest_checkpoint']}")

    print(f"\nToday's Session: ")
    print(f"  Exists: {status['today_session_exists']}")
    print(f"  Has Checkpoint: {status['today_checkpoint_exists']}")

    # Try to save a checkpoint if session exists
    session_file = get_today_session()
    if session_file:
        print(f"\nAttempting checkpoint save...")
        if save_checkpoint(session_file):
            print("[OK] Checkpoint saved successfully")
        else:
            print("[FAIL] Checkpoint save failed")
    else:
        print("\n[SKIP] No active session found for today")

    print("\n" + "=" * 50)
    print("Verification Complete")
    print("=" * 50)


def main():
    parser = argparse.ArgumentParser(description="PA Framework Session Saver")
    parser.add_argument("--check", action="store_true", help="Verify checkpoint system")
    parser.add_argument("--status", action="store_true", help="Show checkpoint status")
    parser.add_argument("--save", action="store_true", help="Force save checkpoint")

    args = parser.parse_args()

    ensure_dirs()

    if args.check:
        verify_system()
        return

    if args.status:
        status = get_checkpoint_status()
        print("Checkpoint Status:")
        for key, value in status.items():
            print(f"  {key}: {value}")
        return

    # Default: save checkpoint
    session_file = get_today_session()
    if session_file:
        if save_checkpoint(session_file):
            print(f"[OK] Checkpoint saved at {datetime.now().strftime('%H:%M:%S')}")
        else:
            print("[WARN] Failed to save checkpoint")
    else:
        print("[INFO] No active session found")


if __name__ == "__main__":
    main()
