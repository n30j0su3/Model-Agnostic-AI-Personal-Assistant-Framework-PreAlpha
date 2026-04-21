#!/usr/bin/env python3
"""
Self-Healing Check - Periodic error detection and recovery

This solves the "Self-Healing pasivo" problem - the loop wasn't active.
Now runs periodically to detect errors and trigger recovery playbooks.

Usage:
    python self-healing-check.py --run         # Run check now
    python self-healing-check.py --status      # Show error status
    python self-healing-check.py --fix ERR-ID  # Fix specific error
    python self-healing-check.py --list        # List all errors

Cross-platform: Works on Windows, Linux, macOS
"""

import sys
import os
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional

# Framework paths
FRAMEWORK_ROOT = Path(__file__).parent.parent
ERROR_LOG_PATH = FRAMEWORK_ROOT / ".context" / "knowledge" / "errors" / "error-log.json"
PLAYBOOKS_DIR = FRAMEWORK_ROOT.parent / "playbooks"

# Playbook mapping
PLAYBOOK_MAP = {
    "FileNotFoundError": "PB-002-file-not-found",
    "KeyError": "PB-003-key-error",
    "ValueError": "PB-004-value-error",
    "ModuleNotFoundError": "PB-005-module-not-found",
    "ImportError": "PB-006-import-error",
    "PermissionError": "PB-007-permission-error",
    "ConnectionError": "PB-008-connection-error",
    "TimeoutError": "PB-009-timeout-error",
    "Unknown": "PB-001-general"
}

# Known fixes for common errors
KNOWN_FIXES = {
    "ERR-20260311": {
        "error": "config/user-settings.json not found",
        "fix": "Create config/user-settings.json with default settings",
        "script": "mkdir -p config && echo '{}' > config/user-settings.json"
    },
    "ERR-20260416": {
        "error": "triggers.py logging issue",
        "fix": "Improve logging in core/recovery/triggers.py",
        "resolved": True
    }
}


class SelfHealingCheck:
    """Periodic self-healing error detection and recovery"""
    
    def __init__(self):
        self.error_log_path = ERROR_LOG_PATH
        self.playbooks_dir = PLAYBOOKS_DIR
        
        # Ensure error log exists
        self.error_log_path.parent.mkdir(parents=True, exist_ok=True)
        
        if not self.error_log_path.exists():
            self._create_error_log()
    
    def _create_error_log(self):
        """Create empty error log"""
        initial = {
            "created": datetime.now().isoformat(),
            "errors": [],
            "healing_history": []
        }
        self.error_log_path.write_text(json.dumps(initial, indent=2))
    
    def run_check(self) -> Dict:
        """Run periodic healing check"""
        
        print("[HEALING] Running self-healing check...")
        
        # 1. Load errors
        errors = self._load_errors()
        
        # 2. Find unresolved recent errors
        recent_errors = self._find_recent_errors(errors, hours=24)
        
        # 3. Check known fixes
        auto_fixed = self._apply_known_fixes(recent_errors)
        
        # 4. Trigger playbooks for remaining
        playbook_triggered = []
        for error in recent_errors:
            if error.get("id") not in [f["error_id"] for f in auto_fixed]:
                playbook = self._trigger_playbook(error)
                playbook_triggered.append(playbook)
        
        # 5. Log healing action
        self._log_healing_action({
            "timestamp": datetime.now().isoformat(),
            "errors_found": len(recent_errors),
            "auto_fixed": len(auto_fixed),
            "playbooks_triggered": len(playbook_triggered)
        })
        
        results = {
            "success": True,
            "errors_found": len(recent_errors),
            "auto_fixed": auto_fixed,
            "playbooks_triggered": playbook_triggered
        }
        
        print(f"[HEALING] ✓ Check complete: {len(recent_errors)} errors, {len(auto_fixed)} auto-fixed")
        
        return results
    
    def _load_errors(self) -> List[Dict]:
        """Load errors from log"""
        
        if not self.error_log_path.exists():
            return []
        
        try:
            data = json.loads(self.error_log_path.read_text())
            return data.get("errors", [])
        except json.JSONDecodeError:
            return []
    
    def _find_recent_errors(self, errors: List[Dict], hours: int = 24) -> List[Dict]:
        """Find unresolved errors from recent time window"""
        
        cutoff = datetime.now() - timedelta(hours=hours)
        
        recent = []
        for error in errors:
            if error.get("status") != "resolved":
                try:
                    error_time = datetime.fromisoformat(error.get("timestamp", ""))
                    if error_time > cutoff:
                        recent.append(error)
                except:
                    # Include if timestamp invalid
                    recent.append(error)
        
        return recent
    
    def _apply_known_fixes(self, errors: List[Dict]) -> List[Dict]:
        """Apply known automatic fixes"""
        
        fixed = []
        
        for error in errors:
            error_id = error.get("id")
            
            if error_id in KNOWN_FIXES:
                fix_info = KNOWN_FIXES[error_id]
                
                if fix_info.get("resolved"):
                    # Mark as resolved
                    self._mark_error_resolved(error_id)
                    fixed.append({
                        "error_id": error_id,
                        "fix": fix_info["fix"],
                        "status": "already_resolved"
                    })
                else:
                    # Apply fix
                    try:
                        # Execute fix script
                        import subprocess
                        result = subprocess.run(
                            fix_info["script"],
                            shell=True,
                            capture_output=True,
                            cwd=str(FRAMEWORK_ROOT.parent)
                        )
                        
                        if result.returncode == 0:
                            self._mark_error_resolved(error_id)
                            fixed.append({
                                "error_id": error_id,
                                "fix": fix_info["fix"],
                                "status": "fixed"
                            })
                            print(f"[HEALING] ✓ Auto-fixed: {error_id}")
                        else:
                            fixed.append({
                                "error_id": error_id,
                                "fix": fix_info["fix"],
                                "status": "failed",
                                "error": result.stderr.decode()
                            })
                            
                    except Exception as e:
                        fixed.append({
                            "error_id": error_id,
                            "fix": fix_info["fix"],
                            "status": "error",
                            "error": str(e)
                        })
        
        return fixed
    
    def _trigger_playbook(self, error: Dict) -> Dict:
        """Trigger appropriate recovery playbook"""
        
        error_type = error.get("type", "Unknown")
        playbook_id = PLAYBOOK_MAP.get(error_type, "PB-001-general")
        
        playbook_path = self.playbooks_dir / f"{playbook_id}.md"
        
        result = {
            "error_id": error.get("id"),
            "error_type": error_type,
            "playbook_id": playbook_id,
            "playbook_path": str(playbook_path),
            "status": "triggered"
        }
        
        if playbook_path.exists():
            playbook_content = playbook_path.read_text()
            print(f"[HEALING] Triggering playbook: {playbook_id}")
            
            # Parse playbook steps
            steps = self._parse_playbook_steps(playbook_content)
            
            result["steps"] = steps
            result["status"] = "loaded"
        else:
            print(f"[HEALING] Playbook not found: {playbook_id}")
            result["status"] = "not_found"
        
        return result
    
    def _parse_playbook_steps(self, content: str) -> List[str]:
        """Parse playbook steps from markdown"""
        
        steps = []
        for line in content.split("\n"):
            if line.startswith("1.") or line.startswith("2.") or line.startswith("3."):
                steps.append(line.strip())
        
        return steps
    
    def _mark_error_resolved(self, error_id: str):
        """Mark error as resolved in log"""
        
        data = json.loads(self.error_log_path.read_text())
        
        for error in data.get("errors", []):
            if error.get("id") == error_id:
                error["status"] = "resolved"
                error["resolved_at"] = datetime.now().isoformat()
        
        self.error_log_path.write_text(json.dumps(data, indent=2))
    
    def _log_healing_action(self, action: Dict):
        """Log healing action to history"""
        
        data = json.loads(self.error_log_path.read_text())
        
        if "healing_history" not in data:
            data["healing_history"] = []
        
        data["healing_history"].append(action)
        
        self.error_log_path.write_text(json.dumps(data, indent=2))
    
    def get_status(self) -> Dict:
        """Get current error status"""
        
        errors = self._load_errors()
        
        unresolved = [e for e in errors if e.get("status") != "resolved"]
        resolved = [e for e in errors if e.get("status") == "resolved"]
        
        return {
            "total_errors": len(errors),
            "unresolved": len(unresolved),
            "resolved": len(resolved),
            "recent_unresolved": len(self._find_recent_errors(errors, hours=24)),
            "last_healing": self._get_last_healing()
        }
    
    def _get_last_healing(self) -> Optional[Dict]:
        """Get last healing action"""
        
        data = json.loads(self.error_log_path.read_text())
        history = data.get("healing_history", [])
        
        if history:
            return history[-1]
        
        return None
    
    def list_errors(self) -> List[Dict]:
        """List all errors"""
        
        return self._load_errors()
    
    def fix_specific(self, error_id: str) -> Dict:
        """Fix specific error"""
        
        errors = self._load_errors()
        
        for error in errors:
            if error.get("id") == error_id:
                # Apply known fix if exists
                auto_fixed = self._apply_known_fixes([error])
                
                if auto_fixed:
                    return {
                        "error_id": error_id,
                        "status": "fixed",
                        "details": auto_fixed[0]
                    }
                
                # Trigger playbook
                playbook = self._trigger_playbook(error)
                
                return {
                    "error_id": error_id,
                    "status": "playbook_triggered",
                    "playbook": playbook
                }
        
        return {
            "error_id": error_id,
            "status": "not_found"
        }
    
    def add_error(self, error_type: str, error_message: str, context: Optional[str] = None) -> str:
        """Add new error to log"""
        
        error_id = f"ERR-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        
        error = {
            "id": error_id,
            "type": error_type,
            "message": error_message,
            "context": context,
            "timestamp": datetime.now().isoformat(),
            "status": "unresolved"
        }
        
        data = json.loads(self.error_log_path.read_text())
        data["errors"].append(error)
        self.error_log_path.write_text(json.dumps(data, indent=2))
        
        print(f"[HEALING] Logged error: {error_id}")
        
        return error_id


def main():
    """CLI interface"""
    
    healing = SelfHealingCheck()
    
    if len(sys.argv) < 2:
        print(__doc__)
        healing.run_check()
        return
    
    arg = sys.argv[1]
    
    if arg == "--run":
        results = healing.run_check()
        print(json.dumps(results, indent=2))
        
    elif arg == "--status":
        status = healing.get_status()
        print("[HEALING] Error Status:")
        print(json.dumps(status, indent=2))
        
    elif arg == "--list":
        errors = healing.list_errors()
        print(f"[HEALING] {len(errors)} errors logged:")
        for e in errors:
            print(f"\n  {e.get('id')}: {e.get('type')}")
            print(f"    Status: {e.get('status')}")
            print(f"    Message: {e.get('message', '')[:50]}...")
        
    elif arg == "--fix" and len(sys.argv) > 2:
        error_id = sys.argv[2]
        result = healing.fix_specific(error_id)
        print(f"[HEALING] Fix result:")
        print(json.dumps(result, indent=2))
        
    elif arg == "--add" and len(sys.argv) >= 4:
        error_type = sys.argv[2]
        error_message = sys.argv[3]
        context = sys.argv[4] if len(sys.argv) > 4 else None
        
        error_id = healing.add_error(error_type, error_message, context)
        print(f"[HEALING] Error added: {error_id}")
        
    else:
        print(__doc__)


if __name__ == "__main__":
    main()