"""Unified Controlled Tool Registry for JARVIS Autonomous Operations."""

import os
import glob
from pathlib import Path
from typing import Dict, Any, List, Optional
from jarvis.backend.automation.desktop import desktop_controller
from jarvis.backend.automation.screen import screen_observer
from jarvis.backend.core.state import state_manager
from jarvis.backend.security.permissions import security_guard


class ToolRegistry:
    def __init__(self):
        self.tools = {
            "capture_screen": self.capture_screen,
            "click_mouse": self.click_mouse,
            "type_text": self.type_text,
            "press_shortcut": self.press_shortcut,
            "launch_application": self.launch_application,
            "minimize_all": self.minimize_all,
            "lock_pc": self.lock_pc,
            "control_volume": self.control_volume,
            "search_files": self.search_files,
            "get_system_status": self.get_system_status,
        }

    def capture_screen(self, **kwargs) -> Dict[str, Any]:
        """Capture screenshot of the desktop screen."""
        return screen_observer.capture_fullscreen(save_file=True)

    def click_mouse(self, x: int = None, y: int = None, button: str = "left", clicks: int = 1, **kwargs) -> Dict[str, Any]:
        """Click mouse at specified coordinates or current position."""
        success = desktop_controller.click(x=x, y=y, button=button, clicks=clicks)
        return {"success": success, "x": x, "y": y, "button": button}

    def type_text(self, text: str, **kwargs) -> Dict[str, Any]:
        """Type text via keyboard simulation."""
        success = desktop_controller.type_text(text)
        return {"success": success, "typed_length": len(text)}

    def press_shortcut(self, keys: List[str], **kwargs) -> Dict[str, Any]:
        """Press key combination e.g. ['ctrl', 'c'] or ['win', 'd']."""
        success = desktop_controller.hotkey(*keys)
        return {"success": success, "keys": keys}

    def launch_application(self, app_name: str, **kwargs) -> Dict[str, Any]:
        """Open a desktop application (chrome, notepad, vscode, explorer, etc.)."""
        success = desktop_controller.launch_app(app_name)
        return {"success": success, "app": app_name}

    def minimize_all(self, **kwargs) -> Dict[str, Any]:
        """Show desktop (Win+D)."""
        success = desktop_controller.minimize_all_windows()
        return {"success": success}

    def lock_pc(self, **kwargs) -> Dict[str, Any]:
        """Lock the Windows workstation."""
        success = desktop_controller.lock_workstation()
        return {"success": success}

    def control_volume(self, action: str = "mute", **kwargs) -> Dict[str, Any]:
        """Adjust system volume (up, down, mute)."""
        success = desktop_controller.control_volume(action=action)
        return {"success": success, "action": action}

    def search_files(self, query: str, root_folder: Optional[str] = None, extension: Optional[str] = None, **kwargs) -> List[str]:
        """Search for files by name/pattern on local drives."""
        if not root_folder:
            root_folder = str(Path.home() / "Videos")

        pattern = f"*{query}*"
        if extension:
            pattern += f".{extension.lstrip('.')}"

        results = []
        try:
            for p in Path(root_folder).rglob(pattern):
                results.append(str(p))
                if len(results) >= 50:
                    break
        except Exception:
            pass
        return results

    def get_system_status(self, **kwargs) -> Dict[str, Any]:
        """Return current CPU, RAM, Disk and GPU metrics."""
        state_manager.update_metrics()
        return state_manager.state.metrics.model_dump()

    def execute_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool safely through the permission check."""
        if tool_name not in self.tools:
            return {"error": f"Unknown tool '{tool_name}'"}

        if not security_guard.is_safe_to_proceed(tool_name, parameters):
            return {"error": f"Permission denied for tool '{tool_name}'"}

        try:
            handler = self.tools[tool_name]
            result = handler(**parameters)
            return {"success": True, "result": result}
        except Exception as e:
            return {"error": str(e)}


tool_registry = ToolRegistry()

