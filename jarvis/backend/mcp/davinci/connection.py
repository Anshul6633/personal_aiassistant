"""
DaVinci Resolve Connection Manager for Project JARVIS MCP Server.
Handles environment detection, fusionscript library loading, and root object acquisition.
"""

import os
import sys
import psutil
from typing import Optional, Tuple, Dict, Any
from jarvis.backend.mcp.davinci.object_registry import registry


def get_default_resolve_paths() -> Dict[str, str]:
    """Return default platform paths for DaVinci Resolve scripting."""
    if sys.platform.startswith("win"):
        return {
            "exe": r"C:\Program Files\Blackmagic Design\DaVinci Resolve\Resolve.exe",
            "lib": r"C:\Program Files\Blackmagic Design\DaVinci Resolve\fusionscript.dll",
            "api": r"C:\ProgramData\Blackmagic Design\DaVinci Resolve\Support\Developer\Scripting",
            "modules": r"C:\ProgramData\Blackmagic Design\DaVinci Resolve\Support\Developer\Scripting\Modules"
        }
    elif sys.platform == "darwin":
        return {
            "exe": "/Applications/DaVinci Resolve/DaVinci Resolve.app/Contents/MacOS/Resolve",
            "lib": "/Applications/DaVinci Resolve/DaVinci Resolve.app/Contents/Libraries/Fusion/fusionscript.so",
            "api": "/Library/Application Support/Blackmagic Design/DaVinci Resolve/Developer/Scripting",
            "modules": "/Library/Application Support/Blackmagic Design/DaVinci Resolve/Developer/Scripting/Modules"
        }
    else:  # Linux
        return {
            "exe": "/opt/resolve/bin/resolve",
            "lib": "/opt/resolve/libs/Fusion/fusionscript.so",
            "api": "/opt/resolve/Developer/Scripting",
            "modules": "/opt/resolve/Developer/Scripting/Modules"
        }


def is_resolve_running() -> bool:
    """Check if DaVinci Resolve process is running."""
    target = "resolve.exe" if sys.platform.startswith("win") else "resolve"
    for proc in psutil.process_iter(['name']):
        try:
            if proc.info['name'] and proc.info['name'].lower() == target:
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return False


def is_resolve_installed() -> bool:
    """Check if DaVinci Resolve binary is present on the filesystem."""
    paths = get_default_resolve_paths()
    return os.path.exists(paths["exe"])


def configure_environment() -> Dict[str, str]:
    """Ensure environment variables and sys.path are configured for fusionscript."""
    paths = get_default_resolve_paths()
    
    if "RESOLVE_SCRIPT_API" not in os.environ:
        os.environ["RESOLVE_SCRIPT_API"] = paths["api"]
    if "RESOLVE_SCRIPT_LIB" not in os.environ:
        os.environ["RESOLVE_SCRIPT_LIB"] = paths["lib"]
        
    modules_path = paths["modules"]
    if os.path.exists(modules_path) and modules_path not in sys.path:
        sys.path.insert(0, modules_path)

    return {
        "RESOLVE_SCRIPT_API": os.environ["RESOLVE_SCRIPT_API"],
        "RESOLVE_SCRIPT_LIB": os.environ["RESOLVE_SCRIPT_LIB"],
        "modules_path": modules_path
    }


class ResolveConnection:
    """Manages the connection to the live DaVinci Resolve instance."""

    def __init__(self):
        self._resolve = None
        self._root_ids: Dict[str, str] = {}

    def get_status(self) -> Dict[str, Any]:
        """Query complete status of DaVinci Resolve on this host."""
        installed = is_resolve_installed()
        running = is_resolve_running()
        connected = self._resolve is not None

        return {
            "installed": installed,
            "running": running,
            "connected": connected,
            "root_ids": self._root_ids,
            "registry_count": len(registry),
            "fallback_available": True,
            "fallback_mode": "fcpxml_v1.9"
        }

    def connect(self, force_refresh: bool = False) -> Tuple[Optional[Any], Dict[str, Any]]:
        """Connect to live DaVinci Resolve and populate root registry entries."""
        if self._resolve is not None and not force_refresh:
            return self._resolve, {"status": "already_connected", **self.get_status()}

        if not is_resolve_running():
            return None, {
                "status": "offline",
                "message": "DaVinci Resolve is not running. Live MCP commands require Resolve to be running.",
                "fallback_mode": "fcpxml",
                **self.get_status()
            }

        configure_environment()

        try:
            import DaVinciResolveScript as bmd
            resolve = bmd.scriptapp("Resolve")
            if not resolve:
                return None, {
                    "status": "connection_failed",
                    "message": "Failed to connect to Resolve scripting interface. (May require DaVinci Resolve Studio).",
                    "fallback_mode": "fcpxml",
                    **self.get_status()
                }

            self._resolve = resolve
            registry.clear()

            # Register Root Resolve Object
            resolve_id = registry.register(resolve, "Resolve", {"version": resolve.GetVersionString() if hasattr(resolve, "GetVersionString") else "Unknown"})
            self._root_ids["resolve_id"] = resolve_id

            # Register Project Manager
            pm = resolve.GetProjectManager()
            if pm:
                pm_id = registry.register(pm, "ProjectManager")
                self._root_ids["project_manager_id"] = pm_id

                # Register Current Project if loaded
                current_project = pm.GetCurrentProject()
                if current_project:
                    proj_name = current_project.GetName() if hasattr(current_project, "GetName") else "Untitled"
                    proj_id = registry.register(current_project, "Project", {"name": proj_name})
                    self._root_ids["project_id"] = proj_id

                    # Register Current Timeline
                    current_timeline = current_project.GetCurrentTimeline()
                    if current_timeline:
                        tl_name = current_timeline.GetName() if hasattr(current_timeline, "GetName") else "Untitled"
                        tl_id = registry.register(current_timeline, "Timeline", {"name": tl_name})
                        self._root_ids["timeline_id"] = tl_id

                    # Register Media Pool
                    media_pool = current_project.GetMediaPool()
                    if media_pool:
                        mp_id = registry.register(media_pool, "MediaPool")
                        self._root_ids["media_pool_id"] = mp_id

            return self._resolve, {
                "status": "connected",
                "message": "Successfully connected to DaVinci Resolve.",
                **self.get_status()
            }

        except Exception as e:
            return None, {
                "status": "error",
                "error": str(e),
                "message": f"Exception connecting to DaVinci Resolve: {e}",
                "fallback_mode": "fcpxml",
                **self.get_status()
            }

    def disconnect(self):
        """Reset connection and clear registry."""
        self._resolve = None
        self._root_ids = {}
        registry.clear()


# Global singleton connection
connection = ResolveConnection()

