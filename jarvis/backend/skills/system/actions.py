"""System skill actions for JARVIS."""

from typing import Dict, Any
from jarvis.backend.core.state import state_manager
from jarvis.backend.automation.tool_registry import tool_registry
from jarvis.backend.automation.screen import screen_observer


def get_telemetry() -> Dict[str, Any]:
    state_manager.update_metrics()
    return state_manager.state.metrics.model_dump()


def lock_pc() -> Dict[str, Any]:
    return tool_registry.execute_tool("lock_pc", {})


def capture_screenshot() -> str:
    return screen_observer.capture_fullscreen(save_file=True)


def minimize_all() -> Dict[str, Any]:
    return tool_registry.execute_tool("minimize_all", {})

