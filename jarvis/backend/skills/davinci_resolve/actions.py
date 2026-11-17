"""Actions entry point for the DaVinci Resolve Skill in JARVIS."""

import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional
from jarvis.backend.skills.davinci_resolve.resolve_detector import resolve_detector
from jarvis.backend.skills.davinci_resolve.fcpxml_generator import fcpxml_generator, TIMELINES_DIR
from jarvis.backend.skills.davinci_resolve.bridge import davinci_bridge


def get_status() -> Dict[str, Any]:
    """Inspect local DaVinci Resolve health, installation, and scripting capability."""
    return resolve_detector.get_status()


def export_timeline_fcpxml(
    video_path: str,
    clips: List[Dict[str, Any]],
    timeline_name: str = "JARVIS_Vertical_Shorts"
) -> Dict[str, Any]:
    """Export an industry-standard 9:16 vertical FCPXML timeline for DaVinci Resolve (Free or Studio)."""
    res = fcpxml_generator.generate_timeline(
        video_path=video_path,
        clips=clips,
        timeline_name=timeline_name,
        width=1080,
        height=1920,
        fps=30
    )
    return res


def send_to_resolve(
    video_path: str,
    clips: List[Dict[str, Any]],
    project_name: str = "JARVIS_Shorts_Production"
) -> Dict[str, Any]:
    """Unified handler: Uses Live Studio Scripting API if connected, or exports FCPXML timeline."""
    status = resolve_detector.get_status()

    # Track A: Direct Studio Scripting
    if status["studio_scripting_available"]:
        try:
            live_res = davinci_bridge.create_shorts_project(project_name, video_path)
            # Also generate FCPXML for safe measure
            xml_res = fcpxml_generator.generate_timeline(video_path, clips, project_name)
            live_res["xml_backup"] = xml_res["xml_path"]
            return live_res
        except Exception as e:
            pass

    # Track B: Universal FCPXML Interchange (Resolve Free & Studio)
    xml_res = fcpxml_generator.generate_timeline(video_path, clips, project_name)
    xml_res["notice"] = (
        "DaVinci Resolve Studio external scripting is currently offline. "
        "Generated universal 9:16 vertical FCPXML timeline for 1-click import into DaVinci Resolve Free or Studio!"
    )
    return xml_res


def open_timelines_folder() -> Dict[str, Any]:
    """Open Windows File Explorer to the exported timelines directory."""
    if TIMELINES_DIR.exists():
        subprocess.Popen(["explorer.exe", str(TIMELINES_DIR)])
        return {"status": "OPENED", "path": str(TIMELINES_DIR)}
    return {"status": "DIRECTORY_NOT_FOUND"}

