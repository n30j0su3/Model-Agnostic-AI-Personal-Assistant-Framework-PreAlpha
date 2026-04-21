#!/usr/bin/env python3
"""
Phase 4 Metrics Test Suite
==========================
Measures missing Phase 4 validation metrics:
1. Recovery rate across 8 playbooks (target ≥80%)
2. Memory benchmark (RSS before/during/after session-start)
3. Auth playbook validation

Author: Dozer QA
Version: 1.0.0
"""

import json
import os
import sys
import time
import tempfile
import tracemalloc
from pathlib import Path
from typing import Dict, List, Any, Tuple

# Add project root to path
_PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from core.recovery.orchestrator import RecoveryOrchestrator, CATEGORY_TO_PLAYBOOKS
from core.recovery.triggers import detect_error_type, should_trigger_recovery

# =============================================================================
# METRICS COLLECTION
# =============================================================================

class Phase4Metrics:
    """Collects and reports Phase 4 validation metrics."""
    
    def __init__(self):
        self.results: Dict[str, Any] = {
            "recovery_rate": {},
            "memory_benchmark": {},
            "auth_validation": {},
            "gaps": []
        }
        self.playbook_dir = _PROJECT_ROOT / "core" / ".context" / "knowledge" / "playbooks"
        
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all Phase 4 metric tests."""
        print("=" * 60)
        print("PHASE 4 METRICS TEST SUITE")
        print("=" * 60)
        
        # 1. Recovery Rate Test
        print("\n[1/3] Running Recovery Rate Test...")
        self.results["recovery_rate"] = self.test_recovery_rate()
        
        # 2. Memory Benchmark
        print("\n[2/3] Running Memory Benchmark...")
        self.results["memory_benchmark"] = self.test_memory_benchmark()
        
        # 3. Auth Playbook Validation
        print("\n[3/3] Running Auth Playbook Validation...")
        self.results["auth_validation"] = self.test_auth_playbook()
        
        # Identify gaps
        self._identify_gaps()
        
        return self.results
    
    def test_recovery_rate(self) -> Dict[str, Any]:
        """
        Test recovery rate across all 8 playbooks.
        Target: ≥80% success rate
        """
        orchestrator = RecoveryOrchestrator(playbooks_dir=self.playbook_dir)
        
        # Test cases for each playbook
        test_cases = {
            "PB-001": {  # Encoding errors
                "contexts": [
                    {"file_path": str(tempfile.mktemp(suffix=".txt"))},
                    {"file_path": os.path.join(tempfile.gettempdir(), "test_encoding.txt")},
                ],
                "setup": lambda ctx: self._create_test_file(ctx.get("file_path"), "hello", "utf-8")
            },
            "PB-002": {  # File not found
                "contexts": [
                    {"file_path": str(tempfile.mktemp(suffix=".txt"))},
                    {"file_path": os.path.join(tempfile.gettempdir(), "new_file.txt")},
                ],
                "setup": None
            },
            "PB-003": {  # JSON parsing
                "contexts": [
                    {"raw_content": '\ufeff{"a": 1,}'},
                    {"raw_content": '{"b": 2,}'},
                ],
                "setup": None
            },
            "PB-004": {  # Subprocess timeout
                "contexts": [
                    {"retry_count": 0, "max_retries": 3},
                    {"retry_count": 1, "max_retries": 3},
                ],
                "setup": None
            },
            "PB-005": {  # Path resolution
                "contexts": [
                    {"file_path": "test.txt", "base_dir": "/tmp"},
                    {"file_path": "subdir/file.txt", "base_dir": str(tempfile.gettempdir())},
                ],
                "setup": lambda ctx: self._create_test_file(
                    os.path.join(ctx.get("base_dir", "/tmp"), ctx.get("file_path", "")), 
                    "test", "utf-8"
                )
            },
            "PB-006": {  # YAML parse fallback
                "contexts": [
                    {"fallback_defaults": {"key": "value"}},
                    {"fallback_defaults": {"default": True}},
                ],
                "setup": None
            },
            "PB-007": {  # Git sync
                "contexts": [
                    {"retry_count": 0},
                    {"retry_count": 1},
                ],
                "setup": None
            },
            "PB-008": {  # Multi-CLI conflict
                "contexts": [
                    {"retry_count": 0},
                    {"retry_count": 2},
                ],
                "setup": None
            },
        }
        
        results = {
            "playbooks": {},
            "total_tests": 0,
            "total_success": 0,
            "success_rate": 0.0,
            "target": 0.80,
            "pass": False
        }
        
        for pb_id, test_config in test_cases.items():
            successes = 0
            total = len(test_config["contexts"])
            results["total_tests"] += total
            
            for ctx in test_config["contexts"]:
                # Setup if needed
                if test_config["setup"]:
                    try:
                        test_config["setup"](ctx)
                    except Exception:
                        pass
                
                result = orchestrator.execute_playbook(pb_id, ctx)
                if result["status"] == "success":
                    successes += 1
                    results["total_success"] += 1
            
            rate = successes / total if total > 0 else 0
            results["playbooks"][pb_id] = {
                "successes": successes,
                "total": total,
                "rate": rate,
                "pass": rate >= 0.80
            }
        
        results["success_rate"] = results["total_success"] / results["total_tests"] if results["total_tests"] > 0 else 0
        results["pass"] = results["success_rate"] >= results["target"]
        
        # Print summary
        print(f"  Total tests: {results['total_tests']}")
        print(f"  Total successes: {results['total_success']}")
        print(f"  Success rate: {results['success_rate']*100:.1f}%")
        print(f"  Target: {results['target']*100:.0f}%")
        print(f"  Status: {'✅ PASS' if results['pass'] else '❌ FAIL'}")
        
        return results
    
    def test_memory_benchmark(self) -> Dict[str, Any]:
        """
        Measure memory usage (RSS) before/during/after session-start.
        """
        import subprocess
        import resource
        
        results = {
            "before_kb": 0,
            "peak_kb": 0,
            "after_kb": 0,
            "delta_kb": 0,
            "session_start_time_s": 0,
            "pass": True  # No specific target, just measuring
        }
        
        # Get baseline memory
        process = subprocess.Popen(
            [sys.executable, "-c", "import time; time.sleep(0.1)"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        try:
            # Measure baseline
            results["before_kb"] = self._get_process_rss_kb(process.pid)
            process.wait(timeout=2)
        except Exception as e:
            results["before_kb"] = 0
        
        # Run session-start and measure
        session_start_script = _PROJECT_ROOT / "core" / "scripts" / "session_start.py"
        
        if session_start_script.exists():
            start_time = time.time()
            tracemalloc.start()
            
            try:
                # Run session-start with timeout
                process = subprocess.Popen(
                    [sys.executable, str(session_start_script), "--skip-context"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    cwd=str(_PROJECT_ROOT)
                )
                
                # Sample memory during execution
                peak_kb = 0
                for _ in range(10):  # Sample 10 times
                    time.sleep(0.3)
                    try:
                        current_kb = self._get_process_rss_kb(process.pid)
                        peak_kb = max(peak_kb, current_kb)
                    except Exception:
                        break
                
                process.wait(timeout=30)
                results["peak_kb"] = peak_kb
                
            except subprocess.TimeoutExpired:
                process.kill()
                results["pass"] = False
            except Exception as e:
                results["pass"] = False
            finally:
                current, peak = tracemalloc.get_traced_memory()
                tracemalloc.stop()
                results["after_kb"] = peak // 1024  # Convert to KB
                results["session_start_time_s"] = time.time() - start_time
        else:
            results["pass"] = False
        
        results["delta_kb"] = results["peak_kb"] - results["before_kb"] if results["peak_kb"] > 0 else 0
        
        # Print summary
        print(f"  Memory before: {results['before_kb']} KB")
        print(f"  Memory peak: {results['peak_kb']} KB")
        print(f"  Memory delta: {results['delta_kb']} KB")
        print(f"  Session start time: {results['session_start_time_s']:.2f}s")
        print(f"  Status: {'✅ PASS' if results['pass'] else '❌ FAIL'}")
        
        return results
    
    def test_auth_playbook(self) -> Dict[str, Any]:
        """
        Validate auth-related playbook handling.
        Check if authentication errors are properly mapped to playbooks.
        """
        orchestrator = RecoveryOrchestrator(playbooks_dir=self.playbook_dir)
        
        results = {
            "auth_category_mapped": False,
            "auth_playbook_exists": False,
            "auth_errors_detected": [],
            "auth_recovery_possible": False,
            "gaps": [],
            "pass": False
        }
        
        # Check if authentication category has playbooks mapped
        auth_playbooks = CATEGORY_TO_PLAYBOOKS.get("authentication", [])
        results["auth_category_mapped"] = len(auth_playbooks) > 0
        
        # Test auth error detection
        auth_test_errors = [
            {"type": "AuthenticationError", "message": "Invalid credentials"},
            {"type": "PermissionDenied", "message": "Access denied"},
            {"type": "UnauthorizedError", "message": "401 Unauthorized"},
            {"type": "TokenExpiredError", "message": "Token has expired"},
            "authentication failed",
            "invalid token provided",
            "login failed",
        ]
        
        for error in auth_test_errors:
            category = detect_error_type(error)
            if category == "authentication":
                results["auth_errors_detected"].append(str(error)[:50])
                
                # Try to match a playbook
                playbook = orchestrator.match_playbook(error)
                if playbook:
                    results["auth_playbook_exists"] = True
                    
                    # Try to execute
                    result = orchestrator.execute_playbook(playbook, {})
                    if result["status"] == "success":
                        results["auth_recovery_possible"] = True
        
        # Identify gaps
        if not results["auth_category_mapped"]:
            results["gaps"].append("Authentication category has no playbooks mapped in CATEGORY_TO_PLAYBOOKS")
        if not results["auth_playbook_exists"]:
            results["gaps"].append("No playbook exists for authentication errors")
        if not results["auth_recovery_possible"]:
            results["gaps"].append("Auth error recovery actions not implemented")
        
        results["pass"] = results["auth_playbook_exists"] and results["auth_recovery_possible"]
        
        # Print summary
        print(f"  Auth category mapped: {results['auth_category_mapped']}")
        print(f"  Auth playbook exists: {results['auth_playbook_exists']}")
        print(f"  Auth errors detected: {len(results['auth_errors_detected'])}")
        print(f"  Auth recovery possible: {results['auth_recovery_possible']}")
        if results["gaps"]:
            print(f"  Gaps found: {len(results['gaps'])}")
            for gap in results["gaps"]:
                print(f"    - {gap}")
        print(f"  Status: {'✅ PASS' if results['pass'] else '❌ FAIL'}")
        
        return results
    
    def _identify_gaps(self):
        """Identify any gaps found during testing."""
        gaps = []
        
        # Recovery rate gaps
        rr = self.results.get("recovery_rate", {})
        if not rr.get("pass", False):
            gaps.append(f"Recovery rate {rr.get('success_rate', 0)*100:.1f}% below target {rr.get('target', 0)*100:.0f}%")
        
        for pb_id, pb_data in rr.get("playbooks", {}).items():
            if not pb_data.get("pass", True):
                gaps.append(f"Playbook {pb_id} success rate {pb_data.get('rate', 0)*100:.1f}% below 80% target")
        
        # Auth gaps
        auth = self.results.get("auth_validation", {})
        gaps.extend(auth.get("gaps", []))
        
        self.results["gaps"] = gaps
    
    def _get_process_rss_kb(self, pid: int) -> int:
        """Get RSS memory in KB for a process."""
        try:
            import resource
            # Try to read from /proc on Linux
            proc_path = f"/proc/{pid}/status"
            if os.path.exists(proc_path):
                with open(proc_path, 'r') as f:
                    for line in f:
                        if line.startswith("VmRSS:"):
                            return int(line.split()[1])
            
            # Fallback: use resource module (only works for current process)
            usage = resource.getrusage(resource.RUSAGE_CHILDREN)
            return int(usage.ru_maxrss)
        except Exception:
            return 0
    
    def _create_test_file(self, path: str, content: str, encoding: str) -> bool:
        """Create a test file with given content."""
        try:
            p = Path(path)
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(content, encoding=encoding)
            return True
        except Exception:
            return False
    
    def print_summary(self):
        """Print a formatted summary of all results."""
        print("\n" + "=" * 60)
        print("PHASE 4 METRICS SUMMARY")
        print("=" * 60)
        
        # Recovery Rate Table
        print("\n📊 RECOVERY RATE TEST")
        print("-" * 60)
        rr = self.results.get("recovery_rate", {})
        print(f"{'Playbook':<12} {'Success':<10} {'Total':<10} {'Rate':<10} {'Status':<10}")
        print("-" * 60)
        for pb_id, data in rr.get("playbooks", {}).items():
            status = "✅ PASS" if data.get("pass", False) else "❌ FAIL"
            print(f"{pb_id:<12} {data.get('successes', 0):<10} {data.get('total', 0):<10} {data.get('rate', 0)*100:>5.1f}%     {status:<10}")
        print("-" * 60)
        overall = "✅ PASS" if rr.get("pass", False) else "❌ FAIL"
        print(f"{'OVERALL':<12} {rr.get('total_success', 0):<10} {rr.get('total_tests', 0):<10} {rr.get('success_rate', 0)*100:>5.1f}%     {overall:<10}")
        
        # Memory Benchmark
        print("\n📈 MEMORY BENCHMARK")
        print("-" * 60)
        mem = self.results.get("memory_benchmark", {})
        print(f"  Before: {mem.get('before_kb', 0)} KB")
        print(f"  Peak:   {mem.get('peak_kb', 0)} KB")
        print(f"  Delta:  {mem.get('delta_kb', 0)} KB")
        print(f"  Time:   {mem.get('session_start_time_s', 0):.2f}s")
        print(f"  Status: {'✅ PASS' if mem.get('pass', False) else '❌ FAIL'}")
        
        # Auth Validation
        print("\n🔐 AUTH PLAYBOOK VALIDATION")
        print("-" * 60)
        auth = self.results.get("auth_validation", {})
        print(f"  Auth category mapped:    {auth.get('auth_category_mapped', False)}")
        print(f"  Auth playbook exists:    {auth.get('auth_playbook_exists', False)}")
        print(f"  Auth errors detected:    {len(auth.get('auth_errors_detected', []))}")
        print(f"  Auth recovery possible:  {auth.get('auth_recovery_possible', False)}")
        print(f"  Status: {'✅ PASS' if auth.get('pass', False) else '❌ FAIL'}")
        
        # Gaps
        gaps = self.results.get("gaps", [])
        if gaps:
            print("\n⚠️  IDENTIFIED GAPS")
            print("-" * 60)
            for i, gap in enumerate(gaps, 1):
                print(f"  {i}. {gap}")
        else:
            print("\n✅ No gaps identified")
        
        print("\n" + "=" * 60)


def main():
    """Main entry point."""
    metrics = Phase4Metrics()
    results = metrics.run_all_tests()
    metrics.print_summary()
    
    # Save results to JSON
    output_path = _PROJECT_ROOT / "logs" / "phase4_metrics.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\n📁 Results saved to: {output_path}")
    
    # Return exit code based on pass/fail
    all_pass = (
        results.get("recovery_rate", {}).get("pass", False) and
        results.get("memory_benchmark", {}).get("pass", False) and
        results.get("auth_validation", {}).get("pass", False)
    )
    return 0 if all_pass else 1


if __name__ == "__main__":
    sys.exit(main())
