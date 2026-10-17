#!/usr/bin/env python3
"""
Cron Setup — Cross-platform scheduled task configuration.
Supports: Windows (Task Scheduler), macOS (launchd), Linux (cron)

Uses tempfile.gettempdir() for cross-platform temp paths.
"""
"""
Cron Setup - Cross-platform scheduled tasks for PA Framework

This solves the "Crons automáticos" problem - no crons were scheduled.
Now works on Windows (Task Scheduler), Linux (crontab), macOS (launchd).

Usage:
    python cron-setup.py --setup          # Setup all crons
    python cron-setup.py --status         # Check cron status
    python cron-setup.py --remove         # Remove all crons
    python cron-setup.py --test           # Test run all scripts

Crons created:
    - PA-Learning-Cron (5 min): Extracts patterns from recent sessions
    - PA-Memory-Sync (15 min): Syncs wiki and validates structure
    - PA-Self-Healing-Check (30 min): Detects and fixes errors

Cross-platform: Windows, Linux, macOS
"""

import sys
import os
import platform
import shlex
import subprocess
import tempfile
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

# Framework root
FRAMEWORK_ROOT = Path(__file__).parent.parent
SCRIPTS_DIR = FRAMEWORK_ROOT / "scripts"

# Cron definitions
CRON_JOBS = [
    {
        "name": "PA-Learning-Cron",
        "script": SCRIPTS_DIR / "learning_cron.py",
        "interval_minutes": 5,
        "description": "Extract patterns from recent sessions"
    },
    {
        "name": "PA-Memory-Sync",
        "script": SCRIPTS_DIR / "memory_sync.py",
        "interval_minutes": 15,
        "description": "Sync wiki and validate structure"
    },
    {
        "name": "PA-Self-Healing-Check",
        "script": SCRIPTS_DIR / "self_healing_check.py",
        "interval_minutes": 30,
        "description": "Detect and fix errors"
    },
    {
        "name": "PA-Wiki-Populate",
        "script": SCRIPTS_DIR / "wiki_populate.py",
        "interval_minutes": 60,
        "description": "Populate wiki with new content"
    }
]

CRON_BLOCK_BEGIN = "# >>> PA Framework managed jobs >>>"
CRON_BLOCK_END = "# <<< PA Framework managed jobs <<<"


def _strip_pa_managed_cron(current: str) -> str:
    """Remove only PA-owned marked or legacy cron entries."""
    lines = current.splitlines(keepends=True)
    kept = []
    in_managed_block = False
    index = 0
    job_scripts = {job["name"]: Path(job["script"]).name for job in CRON_JOBS}

    while index < len(lines):
        line = lines[index]
        stripped = line.strip()
        if stripped == CRON_BLOCK_BEGIN:
            in_managed_block = True
            index += 1
            continue
        if in_managed_block:
            if stripped == CRON_BLOCK_END:
                in_managed_block = False
            index += 1
            continue
        if stripped == "# PA Framework Crons":
            index += 1
            continue

        matched_legacy = False
        for job_name, script_name in job_scripts.items():
            if stripped != f"# {job_name}" or index + 1 >= len(lines):
                continue
            next_line = lines[index + 1]
            if script_name in next_line and "--run" in next_line:
                index += 2
                matched_legacy = True
                break
        if matched_legacy:
            continue

        kept.append(line)
        index += 1

    return "".join(kept)


class CronSetup:
    """Cross-platform cron setup manager"""
    
    def __init__(self):
        self.platform = platform.system()
        self.python_path = sys.executable
        
    def setup_all(self) -> Dict:
        """Setup all cron jobs based on platform"""
        
        results = {}
        
        if self.platform == "Windows":
            results = self._setup_windows()
        elif self.platform == "Linux":
            results = self._setup_linux()
        elif self.platform == "Darwin":
            results = self._setup_macos()
        else:
            print(f"[CRON] Unsupported platform: {self.platform}")
            return {"success": False, "platform": self.platform}
        
        # Save setup info
        self._save_setup_info(results)
        
        return results
    
    def _setup_windows(self) -> Dict:
        """Configure Windows Task Scheduler"""
        
        results = {"platform": "Windows", "tasks": []}
        
        for job in CRON_JOBS:
            task_name = job["name"]
            script_path = str(job["script"])
            interval = job["interval_minutes"]
            
            # Create scheduled task using schtasks
            # Note: Requires admin privileges for some operations
            
            cmd = [
                "schtasks", "/create",
                "/tn", task_name,
                "/tr", f'"{self.python_path}" "{script_path}" --run',
                "/sc", "minute",
                "/mo", str(interval),
                "/f"  # Force overwrite if exists
            ]
            
            try:
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                if result.returncode == 0:
                    print(f"[CRON] ✓ Created: {task_name} (every {interval} min)")
                    results["tasks"].append({
                        "name": task_name,
                        "status": "created",
                        "interval": interval
                    })
                else:
                    # Try without /f flag
                    cmd_no_f = cmd[:-1]
                    result2 = subprocess.run(cmd_no_f, capture_output=True, text=True)
                    
                    if "already exists" in result2.stderr.lower():
                        print(f"[CRON] ✓ Already exists: {task_name}")
                        results["tasks"].append({
                            "name": task_name,
                            "status": "existing",
                            "interval": interval
                        })
                    else:
                        print(f"[CRON] ✗ Failed: {task_name} - {result.stderr}")
                        results["tasks"].append({
                            "name": task_name,
                            "status": "failed",
                            "error": result.stderr
                        })
                        
            except Exception as e:
                print(f"[CRON] ✗ Error: {task_name} - {e}")
                results["tasks"].append({
                    "name": task_name,
                    "status": "error",
                    "error": str(e)
                })
        
        results["success"] = all(t["status"] in ["created", "existing"] for t in results["tasks"])
        return results
    
    def _setup_linux(self) -> Dict:
        """Configure one exact PA-owned crontab block."""
        results = {"platform": "Linux", "tasks": []}
        current_result = subprocess.run(
            ["crontab", "-l"],
            capture_output=True,
            text=True,
        )
        if current_result.returncode not in (0, 1):
            return {
                "platform": "Linux",
                "tasks": [],
                "success": False,
                "error": current_result.stderr or "unable to read crontab",
            }
        current_crontab = current_result.stdout if current_result.returncode == 0 else ""
        unmanaged = _strip_pa_managed_cron(current_crontab)
        if unmanaged and not unmanaged.endswith("\n"):
            unmanaged += "\n"

        block_lines = [CRON_BLOCK_BEGIN]
        for job in CRON_JOBS:
            script_path = shlex.quote(str(job["script"]))
            python_path = shlex.quote(self.python_path)
            interval = job["interval_minutes"]
            cron_entry = f"*/{interval} * * * * {python_path} {script_path} --run"
            block_lines.extend((f"# {job['name']}", cron_entry))
            results["tasks"].append({
                "name": job["name"],
                "status": "created",
                "entry": cron_entry,
            })
        block_lines.append(CRON_BLOCK_END)
        new_crontab = unmanaged + "\n".join(block_lines) + "\n"

        if new_crontab != current_crontab:
            write_result = subprocess.run(
                ["crontab", "-"],
                input=new_crontab,
                capture_output=True,
                text=True,
            )
            if write_result.returncode != 0:
                return {
                    "platform": "Linux",
                    "tasks": results["tasks"],
                    "success": False,
                    "error": write_result.stderr or "crontab rejected update",
                }
        else:
            for task in results["tasks"]:
                task["status"] = "existing"

        results["success"] = True
        return results
    
    def _setup_macos(self) -> Dict:
        """Configure macOS launchd"""
        
        results = {"platform": "Darwin", "tasks": []}
        
        launch_agents_dir = Path.home() / "Library" / "LaunchAgents"
        launch_agents_dir.mkdir(parents=True, exist_ok=True)
        
        for job in CRON_JOBS:
            script_path = str(job["script"])
            interval = job["interval_minutes"]
            interval_seconds = interval * 60
            
            plist_name = f"com.pa-framework.{job['name'].lower().replace('-', '')}.plist"
            plist_path = launch_agents_dir / plist_name
            
            # Cross-platform temp paths
            temp_dir = tempfile.gettempdir()
            log_file = os.path.join(temp_dir, f"pa-{job['name'].lower().replace('-', '')}.log")
            error_file = os.path.join(temp_dir, f"pa-{job['name'].lower().replace('-', '')}-error.log")
            
            # Create plist content
            plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.pa-framework.{job['name'].lower().replace('-', '')}</string>
    <key>ProgramArguments</key>
    <array>
        <string>{self.python_path}</string>
        <string>{script_path}</string>
        <string>--run</string>
    </array>
    <key>StartInterval</key>
    <integer>{interval_seconds}</integer>
    <key>RunAtLoad</key>
    <true/>
    <key>StandardOutPath</key>
    <string>{log_file}</string>
    <key>StandardErrorPath</key>
    <string>{error_file}</string>
</dict>
</plist>
"""
            
            # Write plist
            plist_path.write_text(plist_content)
            
            # Load with launchctl
            try:
                subprocess.run(
                    ["launchctl", "load", str(plist_path)],
                    capture_output=True
                )
                print(f"[CRON] ✓ Created: {job['name']} (every {interval} min)")
                results["tasks"].append({
                    "name": job["name"],
                    "status": "created",
                    "plist": str(plist_path)
                })
            except Exception as e:
                print(f"[CRON] ✗ Failed: {job['name']} - {e}")
                results["tasks"].append({
                    "name": job["name"],
                    "status": "error",
                    "error": str(e)
                })
        
        results["success"] = True
        return results
    
    def _save_setup_info(self, results: Dict):
        """Save setup info to file"""
        
        info_path = Path.home() / ".pa-framework" / "cron-setup.json"
        info_path.parent.mkdir(parents=True, exist_ok=True)
        
        info = {
            "last_setup": datetime.now().isoformat(),
            "platform": self.platform,
            "python_path": self.python_path,
            "results": results
        }
        
        info_path.write_text(json.dumps(info, indent=2))
    
    def get_status(self) -> Dict:
        """Get current cron status"""
        
        status = {
            "platform": self.platform,
            "jobs": []
        }
        
        if self.platform == "Windows":
            for job in CRON_JOBS:
                result = subprocess.run(
                    ["schtasks", "/query", "/tn", job["name"]],
                    capture_output=True,
                    text=True
                )
                
                if result.returncode == 0:
                    status["jobs"].append({
                        "name": job["name"],
                        "status": "active",
                        "output": result.stdout[:200]
                    })
                else:
                    status["jobs"].append({
                        "name": job["name"],
                        "status": "not_found"
                    })
                    
        elif self.platform == "Linux":
            current_crontab = subprocess.run(
                ["crontab", "-l"],
                capture_output=True,
                text=True
            ).stdout
            
            for job in CRON_JOBS:
                if job["name"] in current_crontab or str(job["script"]) in current_crontab:
                    status["jobs"].append({
                        "name": job["name"],
                        "status": "active"
                    })
                else:
                    status["jobs"].append({
                        "name": job["name"],
                        "status": "not_found"
                    })
                    
        elif self.platform == "Darwin":
            for job in CRON_JOBS:
                plist_name = f"com.pa-framework.{job['name'].lower().replace('-', '')}"
                
                result = subprocess.run(
                    ["launchctl", "list", plist_name],
                    capture_output=True,
                    text=True
                )
                
                if result.returncode == 0:
                    status["jobs"].append({
                        "name": job["name"],
                        "status": "active",
                        "plist": plist_name
                    })
                else:
                    status["jobs"].append({
                        "name": job["name"],
                        "status": "not_found"
                    })
        
        return status
    
    def remove_all(self) -> Dict:
        """Remove all cron jobs"""
        
        results = {"platform": self.platform, "removed": []}
        
        if self.platform == "Windows":
            for job in CRON_JOBS:
                subprocess.run(
                    ["schtasks", "/delete", "/tn", job["name"], "/f"],
                    capture_output=True
                )
                print(f"[CRON] Removed: {job['name']}")
                results["removed"].append(job["name"])
                
        elif self.platform == "Linux":
            current_result = subprocess.run(
                ["crontab", "-l"],
                capture_output=True,
                text=True,
            )
            if current_result.returncode not in (0, 1):
                return {
                    "platform": "Linux",
                    "removed": [],
                    "success": False,
                    "error": current_result.stderr or "unable to read crontab",
                }
            current_crontab = current_result.stdout if current_result.returncode == 0 else ""
            filtered = _strip_pa_managed_cron(current_crontab)
            if filtered != current_crontab:
                write_result = subprocess.run(
                    ["crontab", "-"],
                    input=filtered,
                    capture_output=True,
                    text=True,
                )
                if write_result.returncode != 0:
                    return {
                        "platform": "Linux",
                        "removed": [],
                        "success": False,
                        "error": write_result.stderr or "crontab rejected update",
                    }
                results["removed"] = [job["name"] for job in CRON_JOBS]
            results["success"] = True
        elif self.platform == "Darwin":
            launch_agents_dir = Path.home() / "Library" / "LaunchAgents"
            
            for job in CRON_JOBS:
                plist_name = f"com.pa-framework.{job['name'].lower().replace('-', '')}.plist"
                plist_path = launch_agents_dir / plist_name
                
                if plist_path.exists():
                    subprocess.run(["launchctl", "unload", str(plist_path)])
                    plist_path.unlink()
                    print(f"[CRON] Removed: {job['name']}")
                    results["removed"].append(job["name"])
        
        return results
    
    def test_all(self) -> Dict:
        """Test run all cron scripts"""
        
        results = {"tested": []}
        
        for job in CRON_JOBS:
            script_path = job["script"]
            
            if script_path.exists():
                try:
                    result = subprocess.run(
                        [self.python_path, str(script_path), "--help"],
                        capture_output=True,
                        text=True,
                        timeout=10
                    )
                    
                    print(f"[CRON] ✓ Tested: {job['name']}")
                    results["tested"].append({
                        "name": job["name"],
                        "status": "ok",
                        "help": result.stdout[:100] if result.stdout else "no output"
                    })
                except Exception as e:
                    print(f"[CRON] ✗ Test failed: {job['name']} - {e}")
                    results["tested"].append({
                        "name": job["name"],
                        "status": "error",
                        "error": str(e)
                    })
            else:
                print(f"[CRON] ✗ Script not found: {job['name']}")
                results["tested"].append({
                    "name": job["name"],
                    "status": "not_found"
                })
        
        return results


def main():
    """CLI interface"""
    
    setup = CronSetup()
    
    if len(sys.argv) < 2:
        print(__doc__)
        print("\nCurrent platform:", setup.platform)
        return
    
    arg = sys.argv[1]
    
    if arg == "--setup":
        print("[CRON] Setting up scheduled tasks...")
        results = setup.setup_all()
        print(json.dumps(results, indent=2))
        
    elif arg == "--status":
        print("[CRON] Checking cron status...")
        status = setup.get_status()
        print(json.dumps(status, indent=2))
        
    elif arg == "--remove":
        print("[CRON] Removing scheduled tasks...")
        results = setup.remove_all()
        print(json.dumps(results, indent=2))
        
    elif arg == "--test":
        print("[CRON] Testing cron scripts...")
        results = setup.test_all()
        print(json.dumps(results, indent=2))
        
    else:
        print(__doc__)


if __name__ == "__main__":
    import json
    main()