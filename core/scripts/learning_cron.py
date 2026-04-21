#!/usr/bin/env python3
"""
PA Framework — Learning Cron
============================
Standalone cron script that periodically checks for active session
and runs knowledge mining if there's new content.

Designed to run every N minutes during active sessions.

Usage:
    python core/scripts/learning-cron.py              # Run once
    python core/scripts/learning-cron.py --watch      # Watch mode (loop)
    python core/scripts/learning-cron.py --interval N # Watch mode with N minutes interval

Autor: FreakingJSON-PA Framework
Version: 1.0.0
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

# Paths
SCRIPT_DIR = Path(__file__).resolve().parent
CORE_DIR = SCRIPT_DIR.parent
REPO_ROOT = CORE_DIR.parent
CONTEXT_DIR = CORE_DIR / ".context"
SESSIONS_DIR = CONTEXT_DIR / "sessions"
CHECKPOINTS_DIR = CONTEXT_DIR / "checkpoints"
KNOWLEDGE_DIR = CONTEXT_DIR / "knowledge"


def get_today_session() -> Optional[Path]:
    """Get today's session file path."""
    today = datetime.now().strftime("%Y-%m-%d")
    session_file = SESSIONS_DIR / f"{today}.md"
    return session_file if session_file.exists() else None


def get_last_checkpoint() -> Optional[Path]:
    """Get the latest checkpoint file."""
    if not CHECKPOINTS_DIR.exists():
        return None
    checkpoints = sorted(CHECKPOINTS_DIR.glob("checkpoint_*.json"), reverse=True)
    return checkpoints[0] if checkpoints else None


def get_session_modified_time(session_file: Path) -> float:
    """Get session file last modified time."""
    try:
        return session_file.stat().st_mtime
    except Exception:
        return 0


def has_new_content(session_file: Path) -> bool:
    """
    Check if session has new content since last checkpoint.
    Returns True if there's new content, False otherwise.
    """
    last_checkpoint = get_last_checkpoint()
    if last_checkpoint is None:
        return True  # No checkpoint yet, assume new content

    try:
        checkpoint_data = json.loads(last_checkpoint.read_text(encoding="utf-8"))
        last_modified = checkpoint_data.get("last_modified", "")

        if not last_modified:
            # Fallback: compare modification times
            checkpoint_mtime = last_checkpoint.stat().st_mtime
            session_mtime = get_session_modified_time(session_file)
            return session_mtime > checkpoint_mtime

        # Parse checkpoint last_modified
        from datetime import datetime as dt
        checkpoint_time = dt.fromisoformat(last_modified)
        session_time = dt.fromtimestamp(get_session_modified_time(session_file))

        return session_time > checkpoint_time
    except Exception:
        return True  # If we can't determine, assume new content


def run_knowledge_miner() -> bool:
    """Run knowledge miner script."""
    try:
        import subprocess
        result = subprocess.run(
            [sys.executable, str(SCRIPT_DIR / "knowledge_miner.py"), "--quiet"],
            capture_output=True,
            text=True,
            timeout=60,
            cwd=REPO_ROOT,
        )
        return result.returncode == 0
    except Exception as e:
        print(f"[WARN] Knowledge miner failed: {e}")
        return False


def run_wiki_autopopulate() -> bool:
    """Run wiki autopopulate script."""
    try:
        import subprocess
        result = subprocess.run(
            [sys.executable, str(SCRIPT_DIR / "wiki_autopopulate.py")],
            capture_output=True,
            text=True,
            timeout=60,
            cwd=REPO_ROOT,
        )
        return result.returncode == 0
    except Exception as e:
        print(f"[WARN] Wiki autopopulate failed: {e}")
        return False


def run_kb_updater() -> bool:
    """Run KB updater script."""
    try:
        import subprocess
        result = subprocess.run(
            [sys.executable, str(SCRIPT_DIR / "kb_updater.py")],
            capture_output=True,
            text=True,
            timeout=60,
            cwd=REPO_ROOT,
        )
        return result.returncode == 0
    except Exception as e:
        print(f"[WARN] KB updater failed: {e}")
        return False


def run_session_saver() -> bool:
    """Run session saver script."""
    try:
        import subprocess
        result = subprocess.run(
            [sys.executable, str(SCRIPT_DIR / "session_saver.py")],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=REPO_ROOT,
        )
        return result.returncode == 0
    except Exception as e:
        print(f"[WARN] Session saver failed: {e}")
        return False


def run_learning_cycle() -> bool:
    """
    Run a complete learning cycle:
    1. Check for new content
    2. Save checkpoint
    3. Mine knowledge
    4. Update wiki
    5. Update KB
    """
    session_file = get_today_session()
    if session_file is None:
        print("[INFO] No active session found")
        return False

    # Check for new content
    if not has_new_content(session_file):
        print(f"[INFO] No new content in session (last checkpoint is current)")
        return False

    print(f"[{datetime.now().strftime('%H:%M:%S')}] Running learning cycle...")

    # Run all steps
    results = {
        "checkpoint": run_session_saver(),
        "miner": run_knowledge_miner(),
        "wiki": run_wiki_autopopulate(),
        "kb": run_kb_updater(),
    }

    # Summary
    successful = sum(1 for v in results.values() if v)
    print(f"[OK] Learning cycle complete: {successful}/4 steps successful")

    return successful > 0


def watch_mode(interval_minutes: int = 5):
    """
    Run in watch mode, checking for new content periodically.
    """
    print(f"Starting learning cron in watch mode (interval: {interval_minutes} min)")
    print("Press Ctrl+C to stop")

    while True:
        try:
            run_learning_cycle()
            time.sleep(interval_minutes * 60)
        except KeyboardInterrupt:
            print("\n[INFO] Stopping learning cron")
            break
        except Exception as e:
            print(f"[ERROR] Watch loop error: {e}")
            time.sleep(60)  # Wait before retrying


def main():
    parser = argparse.ArgumentParser(
        description="PA Framework Learning Cron - Periodic session learning"
    )
    parser.add_argument(
        "--watch",
        action="store_true",
        help="Run continuously in watch mode"
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=5,
        help="Watch mode interval in minutes (default: 5)"
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Show current learning cron status"
    )

    args = parser.parse_args()

    if args.status:
        # Show status
        session_file = get_today_session()
        last_checkpoint = get_last_checkpoint()

        print("Learning Cron Status:")
        print(f"  Active session: {session_file.name if session_file else 'None'}")

        if last_checkpoint:
            checkpoint_data = json.loads(last_checkpoint.read_text(encoding="utf-8"))
            print(f"  Last checkpoint: {last_checkpoint.name}")
            print(f"  Checkpoint date: {checkpoint_data.get('date', 'unknown')}")
        else:
            print("  Last checkpoint: None")

        if session_file and last_checkpoint:
            if has_new_content(session_file):
                print("  New content: YES")
            else:
                print("  New content: NO")
        return

    if args.watch:
        watch_mode(args.interval)
    else:
        # Run once
        run_learning_cycle()


if __name__ == "__main__":
    main()
