"""DaVinci Resolve environment & process detector for JARVIS."""

import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional
import psutil

DEFAULT_SCRIPT_API = Path(r"C:\ProgramData\Blackmagic Design\DaVinci Resolve\Support\Developer\Scripting")
DEFAULT_RESOLVE_EXE = Path(r"C:\Program Files\Blackmagic Design\DaVinci Resolve\Resolve.exe")
DEFAULT_FUSION_DLL = Path(r"C:\Program Files\Blackmagic Design\DaVinci Resolve\fusionscript.dll")


class ResolveDetector:
    def __init__(self):
        self.script_api_path = DEFAULT_SCRIPT_API
        self.resolve_exe_path = DEFAULT_RESOLVE_EXE
        self.fusion_dll_path = DEFAULT_FUSION_DLL
        self._setup_env()

    def _setup_env(self):
        """Inject required environment paths for external DaVinci Resolve scripting if present."""
        if self.script_api_path.exists():
            os.environ["RESOLVE_SCRIPT_API"] = str(self.script_api_path)
            modules_path = str(self.script_api_path / "Modules")
            if modules_path not in sys.path:
                sys.path.append(modules_path)

        if self.fusion_dll_path.exists():
            os.environ["RESOLVE_SCRIPT_LIB"] = str(self.fusion_dll_path)

    def is_running(self) -> bool:
        """Check if DaVinci Resolve process is actively running."""
        for proc in psutil.process_iter(["name"]):
            try:
                name = proc.info.get("name")
                if name and "resolve.exe" in name.lower():
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return False

    def is_installed(self) -> bool:
        """Check if DaVinci Resolve is installed on the local system."""
        return self.resolve_exe_path.exists() or self.script_api_path.exists()

    def get_status(self) -> Dict[str, Any]:
        """Return diagnostic health and capability status."""
        installed = self.is_installed()
        running = self.is_running()
        scripting_available = False

        if running and installed:
            try:
                import DaVinciResolveScript as bmd
                resolve = bmd.scriptapp("Resolve")
                if resolve:
                    scripting_available = True
            except Exception:
                scripting_available = False

        return {
            "installed": installed,
            "running": running,
            "studio_scripting_available": scripting_available,
            "exe_path": str(self.resolve_exe_path) if installed else None,
            "script_api_path": str(self.script_api_path) if self.script_api_path.exists() else None,
            "fusion_dll_path": str(self.fusion_dll_path) if self.fusion_dll_path.exists() else None,
            "supported_modes": [
                "Universal FCPXML Timeline Interchange (Resolve Free & Pro)",
                *(["Live Studio Scripting Bridge"] if scripting_available else [])
            ]
        }


resolve_detector = ResolveDetector()

