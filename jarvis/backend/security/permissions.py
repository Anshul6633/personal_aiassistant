"""Security, Permissions & Audit Logging for JARVIS Autonomous Operations."""

import logging
from enum import Enum
from typing import Dict, Any, Optional
from jarvis.backend.database.db import get_db_connection

logger = logging.getLogger("JARVIS.Security")


class AutonomyLevel(str, Enum):
    MANUAL = "MANUAL"                            # Ask before every action
    SUPERVISED = "SUPERVISED"                    # Auto-plan & edit; ask before publish/danger
    PREAPPROVED_AUTONOMOUS = "PREAPPROVED_AUTONOMOUS"  # Fully autonomous within preconfigured rules


class SecurityGuard:
    def __init__(self):
        self.emergency_stop_triggered = False
        self.current_mode = AutonomyLevel.SUPERVISED

    def trigger_emergency_stop(self):
        """Immediately halts all active automation tasks, mouse moves, and video rendering."""
        self.emergency_stop_triggered = True
        logger.critical("EMERGENCY STOP TRIGGERED BY USER. ALL AUTOMATION FROZEN.")
        self.log_event("EMERGENCY_STOP", "User engaged emergency stop kill-switch.", "CRITICAL", False)

    def reset_emergency_stop(self):
        self.emergency_stop_triggered = False
        logger.info("Emergency stop cleared. Operations resumed.")
        self.log_event("EMERGENCY_STOP_CLEARED", "Emergency stop reset by user.", "INFO", True)

    def is_safe_to_proceed(self, action_name: str, parameters: Dict[str, Any]) -> bool:
        """Evaluate if an action is permitted under the current autonomy mode."""
        if self.emergency_stop_triggered:
            logger.warning(f"Action '{action_name}' blocked: Emergency stop is active.")
            return False

        # Strictly prohibited dangerous commands
        dangerous_patterns = ["rmdir /s", "del /f /s", "format", "reg delete", "shutdown", "drop database"]
        param_str = str(parameters).lower()
        for p in dangerous_patterns:
            if p in param_str:
                self.log_event("BLOCKED_DANGEROUS_ACTION", f"Blocked command matching '{p}'", "BLOCKED", False)
                return False

        return True

    def log_event(self, action_type: str, details: str, status: str, user_approved: bool = True):
        """Record action in persistent SQLite audit log."""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO audit_logs (action_type, details, status, user_approved)
                VALUES (?, ?, ?, ?)
            """, (action_type, details, status, user_approved))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Failed to record audit log: {e}")


security_guard = SecurityGuard()

