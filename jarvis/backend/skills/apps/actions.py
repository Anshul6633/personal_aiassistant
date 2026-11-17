"""App management skill actions for JARVIS."""

from typing import Dict, Any
from jarvis.backend.automation.tool_registry import tool_registry


def launch(app_name: str) -> Dict[str, Any]:
    return tool_registry.execute_tool("launch_application", {"app_name": app_name})

