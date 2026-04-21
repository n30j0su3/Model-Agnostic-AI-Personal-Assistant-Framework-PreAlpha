"""
PA Framework - Self-Healing Engine (Recovery System)
=====================================================

Phase 3 Item 3: Automated error recovery using ADR-004 taxonomy
and playbook-based remediation.

Modules:
    triggers    - Error detection and classification
    orchestrator - Playbook matching and execution
"""

from core.recovery.orchestrator import RecoveryOrchestrator
from core.recovery.triggers import detect_error_type, should_trigger_recovery

__all__ = ["RecoveryOrchestrator", "detect_error_type", "should_trigger_recovery"]
__version__ = "1.0.0"
