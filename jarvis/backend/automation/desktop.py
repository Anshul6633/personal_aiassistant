"""Desktop Automation, Mouse & Keyboard Controller, and Application Manager.

Controls Windows desktop actions with permission guards and emergency kill-switch protection.
"""

import os
import time
import subprocess
import logging
from typing import Dict, Any, Optional, List
import pyautogui
from jarvis.backend.security.permissions import security_guard
from jarvis.backend.core.state import state_manager, AssistantState

logger = logging.getLogger("JARVIS.Desktop")

# Configure PyAutoGUI safety boundaries
pyautogui.FAILSAFE = True  # Moving mouse to corner triggers PyAutoGUI FailSafeException
pyautogui.PAUSE = 0.2


class DesktopController:
    def __init__(self):
        self.screen_width, self.screen_height = pyautogui.size()

    # --- Mouse Controls ---
    def move_mouse(self, x: int, y: int, duration: float = 0.5) -> bool:
        if not security_guard.is_safe_to_proceed("move_mouse", {"x": x, "y": y}):
            return False
        pyautogui.moveTo(x, y, duration=duration)
        security_guard.log_event("MOUSE_MOVE", f"Moved mouse to ({x}, {y})", "SUCCESS")
        return True

    def click(self, x: Optional[int] = None, y: Optional[int] = None, button: str = "left", clicks: int = 1) -> bool:
        if not security_guard.is_safe_to_proceed("click", {"x": x, "y": y, "button": button}):
            return False
        if x is not None and y is not None:
            pyautogui.click(x=x, y=y, clicks=clicks, button=button)
        else:
            pyautogui.click(clicks=clicks, button=button)
        security_guard.log_event("MOUSE_CLICK", f"Clicked {button} at ({x}, {y}) count={clicks}", "SUCCESS")
        return True

    def double_click(self, x: Optional[int] = None, y: Optional[int] = None) -> bool:
        return self.click(x, y, button="left", clicks=2)

    def right_click(self, x: Optional[int] = None, y: Optional[int] = None) -> bool:
        return self.click(x, y, button="right", clicks=1)

    def scroll(self, amount: int) -> bool:
        if not security_guard.is_safe_to_proceed("scroll", {"amount": amount}):
            return False
        pyautogui.scroll(amount)
        security_guard.log_event("MOUSE_SCROLL", f"Scrolled {amount}", "SUCCESS")
        return True

    # --- Keyboard Controls ---
    def type_text(self, text: str, interval: float = 0.05) -> bool:
        if not security_guard.is_safe_to_proceed("type_text", {"text_length": len(text)}):
            return False
        pyautogui.write(text, interval=interval)
        security_guard.log_event("KEYBOARD_TYPE", f"Typed string of length {len(text)}", "SUCCESS")
        return True

    def press_key(self, key: str) -> bool:
        if not security_guard.is_safe_to_proceed("press_key", {"key": key}):
            return False
        pyautogui.press(key)
        security_guard.log_event("KEY_PRESS", f"Pressed key '{key}'", "SUCCESS")
        return True

    def hotkey(self, *keys) -> bool:
        if not security_guard.is_safe_to_proceed("hotkey", {"keys": keys}):
            return False
        pyautogui.hotkey(*keys)
        security_guard.log_event("HOTKEY", f"Triggered hotkey {keys}", "SUCCESS")
        return True

    # --- Application Control ---
    def launch_app(self, app_name: str) -> bool:
        """Launch authorized Windows applications cleanly."""
        if not security_guard.is_safe_to_proceed("launch_app", {"app_name": app_name}):
            return False

        app_map = {
            "chrome": "start chrome",
            "browser": "start chrome",
            "vscode": "code",
            "code": "code",
            "notepad": "notepad.exe",
            "explorer": "explorer.exe",
            "files": "explorer.exe",
            "calculator": "calc.exe",
            "calc": "calc.exe",
            "taskmanager": "taskmgr.exe",
            "taskmgr": "taskmgr.exe",
            "spotify": "start spotify:",
            "discord": "start discord:",
            "whatsapp": "start whatsapp:",
            "telegram": "start telegram:",
            "settings": "start ms-settings:",
            "cmd": "start cmd.exe",
            "terminal": "start wt.exe",
            "powershell": "start powershell.exe",
            "paint": "mspaint.exe",
            "edge": "start msedge",
            "brave": "start brave",
            "camera": "start microsoft.windows.camera:",
            "controlpanel": "control.exe"
        }

        cmd = app_map.get(app_name.lower())
        if cmd:
            subprocess.Popen(cmd, shell=True)
            security_guard.log_event("LAUNCH_APP", f"Launched {app_name} via {cmd}", "SUCCESS")
            return True
        else:
            # Safe direct executable start
            try:
                subprocess.Popen(app_name, shell=True)
                security_guard.log_event("LAUNCH_APP", f"Started application {app_name}", "SUCCESS")
                return True
            except Exception as e:
                logger.error(f"Failed to launch app {app_name}: {e}")
                return False

    def minimize_all_windows(self):
        """Show Windows Desktop (Win+D)."""
        return self.hotkey("win", "d")

    def lock_workstation(self):
        """Lock Windows PC (Win+L)."""
        if os.name != "nt":
            logger.info("Lock workstation invoked in cloud container.")
            return True
        import ctypes
        ctypes.windll.user32.LockWorkStation()
        security_guard.log_event("SYSTEM_LOCK", "Locked Windows Workstation", "SUCCESS")
        return True

    def control_volume(self, action: str = "mute") -> bool:
        """Adjust system volume (up, down, mute) safely using Windows keybd_event."""
        if os.name != "nt":
            logger.info(f"Volume control ({action}) invoked in cloud container.")
            return True
        import ctypes
        VK_VOLUME_MUTE = 0xAD
        VK_VOLUME_DOWN = 0xAE
        VK_VOLUME_UP = 0xAF

        def tap_key(vk):
            ctypes.windll.user32.keybd_event(vk, 0, 0, 0)
            ctypes.windll.user32.keybd_event(vk, 0, 2, 0)

        if action == "mute":
            tap_key(VK_VOLUME_MUTE)
        elif action == "up":
            for _ in range(5):
                tap_key(VK_VOLUME_UP)
        elif action == "down":
            for _ in range(5):
                tap_key(VK_VOLUME_DOWN)
        return True


desktop_controller = DesktopController()

