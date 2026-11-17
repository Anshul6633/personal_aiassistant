"""
Render and Delivery DaVinci Resolve MCP Tools for Project JARVIS.
Handles render presets, destinations, render job queue, and export progress.
"""

import os
from typing import Dict, Any, List, Optional
from jarvis.backend.mcp.davinci.connection import connection
from jarvis.backend.mcp.davinci.object_registry import registry


def get_active_project(project_id: Optional[str] = None):
    """Retrieve active project or fetch from registry/connection."""
    if project_id:
        proj = registry.get(project_id)
        if proj:
            return proj

    resolve, _ = connection.connect()
    if not resolve:
        return None

    pm = resolve.GetProjectManager()
    return pm.GetCurrentProject() if pm else None


def configure_render_preset(preset_name: str = "YouTube - 1080p", project_id: Optional[str] = None) -> Dict[str, Any]:
    """Load a render preset (e.g. 'YouTube - 1080p', 'H.264 Master', 'ProRes 422')."""
    proj = get_active_project(project_id)
    if not proj:
        return {"success": False, "error": "No active project found or Resolve is offline."}

    try:
        success = proj.LoadRenderPreset(preset_name)
        return {
            "success": bool(success),
            "preset": preset_name,
            "message": f"Render preset '{preset_name}' applied." if success else f"Preset '{preset_name}' not found."
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def set_render_destination(target_dir: str, file_name: Optional[str] = None, project_id: Optional[str] = None) -> Dict[str, Any]:
    """Set export directory and custom file name for the render."""
    proj = get_active_project(project_id)
    if not proj:
        return {"success": False, "error": "No active project found or Resolve is offline."}

    abs_dir = os.path.abspath(target_dir)
    os.makedirs(abs_dir, exist_ok=True)

    settings = {"TargetDir": abs_dir}
    if file_name:
        settings["CustomName"] = file_name

    try:
        success = proj.SetRenderSettings(settings)
        return {
            "success": bool(success),
            "target_dir": abs_dir,
            "file_name": file_name,
            "message": f"Render destination set to '{abs_dir}'."
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def add_render_job(project_id: Optional[str] = None) -> Dict[str, Any]:
    """Add the current timeline configuration to the DaVinci Resolve render queue."""
    proj = get_active_project(project_id)
    if not proj:
        return {"success": False, "error": "No active project found or Resolve is offline."}

    try:
        job_id = proj.AddRenderJob()
        if not job_id:
            return {"success": False, "error": "Failed to add render job to queue."}

        return {
            "success": True,
            "job_id": job_id,
            "message": f"Render job added to queue with ID '{job_id}'."
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def start_render(project_id: Optional[str] = None) -> Dict[str, Any]:
    """Start rendering jobs in the DaVinci Resolve render queue."""
    proj = get_active_project(project_id)
    if not proj:
        return {"success": False, "error": "No active project found or Resolve is offline."}

    try:
        started = proj.StartRendering()
        return {
            "success": bool(started),
            "message": "Render queue started." if started else "Failed to start render queue."
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def stop_render(project_id: Optional[str] = None) -> Dict[str, Any]:
    """Stop any active rendering process."""
    proj = get_active_project(project_id)
    if not proj:
        return {"success": False, "error": "No active project found or Resolve is offline."}

    try:
        proj.StopRendering()
        return {"success": True, "message": "Render stopped."}
    except Exception as e:
        return {"success": False, "error": str(e)}


def get_render_status(project_id: Optional[str] = None) -> Dict[str, Any]:
    """Check if rendering is currently in progress and get job statuses."""
    proj = get_active_project(project_id)
    if not proj:
        return {"success": False, "error": "No active project found or Resolve is offline.", "is_rendering": False}

    try:
        is_rendering = proj.IsRenderingInProgress()
        job_list = proj.GetRenderJobList() or []
        jobs = []

        for job in job_list:
            jid = job.get("JobId", "")
            status_info = proj.GetRenderJobStatus(jid) if jid else {}
            jobs.append({
                "job_id": jid,
                "render_status": status_info.get("JobStatus", "Unknown"),
                "completion_percentage": status_info.get("CompletionPercentage", 0),
                "estimated_time_remaining": status_info.get("EstimatedTimeRemainingInMs", 0) / 1000.0
            })

        return {
            "success": True,
            "is_rendering": bool(is_rendering),
            "jobs_count": len(jobs),
            "jobs": jobs
        }
    except Exception as e:
        return {"success": False, "error": str(e), "is_rendering": False}

