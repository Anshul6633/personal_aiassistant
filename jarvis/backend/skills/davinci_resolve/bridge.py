"""Direct DaVinci Resolve Studio Scripting API Bridge.

Implements the official Blackmagic Design DaVinciResolveScript Python API.
Requires DaVinci Resolve Studio running with external scripting enabled.
"""

import os
import sys
import time
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from jarvis.backend.skills.davinci_resolve.resolve_detector import resolve_detector

logger = logging.getLogger("JARVIS.Skill.DaVinciBridge")


class DaVinciStudioBridge:
    def __init__(self):
        self._resolve = None

    def connect(self) -> Optional[Any]:
        """Attempt connection to active DaVinci Resolve Studio instance."""
        if not resolve_detector.is_running():
            logger.info("DaVinci Resolve is not actively running.")
            return None

        try:
            import DaVinciResolveScript as bmd
            self._resolve = bmd.scriptapp("Resolve")
            if self._resolve:
                logger.info(f"Connected to DaVinci Resolve: {self._resolve.GetProductName()} (v{self._resolve.GetVersionString()})")
            return self._resolve
        except Exception as e:
            logger.warning(f"Failed to connect to DaVinciResolveScript: {e}")
            return None

    def create_shorts_project(
        self,
        project_name: str = "JARVIS_Shorts_Production",
        source_media_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create or open project and prepare 9:16 vertical workspace in DaVinci Resolve Studio."""
        resolve = self.connect()
        if not resolve:
            raise RuntimeError("DaVinci Resolve Studio is not running or external scripting is unavailable.")

        pm = resolve.GetProjectManager()
        project = pm.LoadProject(project_name) or pm.CreateProject(project_name)
        if not project:
            raise RuntimeError(f"Could not initialize DaVinci Resolve project '{project_name}'")

        # Configure timeline resolution to vertical 9:16
        project.SetSetting("timelineResolutionWidth", "1080")
        project.SetSetting("timelineResolutionHeight", "1920")
        project.SetSetting("timelineFrameRate", "30")

        # Color science best practice for Web / Social Deliverables (from SKILL.md)
        project.SetSetting("colorScienceMode", "davinciYRGB")
        project.SetSetting("timelineColorSpace", "Rec.709 (Scene)")

        media_pool = project.GetMediaPool()
        root_folder = media_pool.GetRootFolder()

        imported_items = []
        if source_media_path and Path(source_media_path).exists():
            # Create JARVIS Bins
            sub_folder = media_pool.AddSubFolder(root_folder, "JARVIS_AI_Sources")
            media_pool.SetCurrentFolder(sub_folder)
            imported_items = media_pool.ImportMedia([str(Path(source_media_path).resolve())])

        return {
            "status": "PROJECT_READY",
            "project_name": project.GetName(),
            "timeline_resolution": "1080x1920 (9:16 Vertical)",
            "imported_items_count": len(imported_items) if imported_items else 0
        }

    def queue_render_job(
        self,
        target_dir: str,
        custom_name: str,
        timeline_index: int = 1
    ) -> Dict[str, Any]:
        """Configure H.264 master render preset and dispatch to Deliver queue."""
        resolve = self.connect()
        if not resolve:
            raise RuntimeError("DaVinci Resolve Studio not connected.")

        pm = resolve.GetProjectManager()
        project = pm.GetCurrentProject()
        if not project:
            raise RuntimeError("No active project found in DaVinci Resolve.")

        timeline = project.GetTimelineByIndex(timeline_index)
        if not timeline:
            raise RuntimeError(f"Timeline at index {timeline_index} not found.")

        project.SetCurrentTimeline(timeline)
        project.LoadRenderPreset("H.264 Master")
        project.SetRenderSettings({
            "TargetDir": target_dir,
            "CustomName": custom_name,
            "ExportVideo": True,
            "ExportAudio": True
        })

        job_id = project.AddRenderJob()
        project.StartRendering()

        return {
            "status": "RENDER_QUEUED",
            "job_id": job_id,
            "target_dir": target_dir,
            "custom_name": custom_name
        }


davinci_bridge = DaVinciStudioBridge()

