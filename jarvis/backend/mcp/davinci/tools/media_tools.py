"""
Media Pool DaVinci Resolve MCP Tools for Project JARVIS.
Handles importing video/audio files, creating bins, and generating timelines from media items.
"""

import os
from typing import Dict, Any, List, Optional
from jarvis.backend.mcp.davinci.connection import connection
from jarvis.backend.mcp.davinci.object_registry import registry


def import_media(file_paths: List[str], bin_name: Optional[str] = "JARVIS Ingested") -> Dict[str, Any]:
    """Import media files into DaVinci Resolve Media Pool and register items."""
    resolve, status = connection.connect()
    if not resolve:
        return {
            "success": False,
            "error": "DaVinci Resolve is offline.",
            "status": status,
            "clip_ids": []
        }

    try:
        pm = resolve.GetProjectManager()
        project = pm.GetCurrentProject() if pm else None
        if not project:
            return {"success": False, "error": "No active project open in DaVinci Resolve.", "clip_ids": []}

        media_pool = project.GetMediaPool()
        if not media_pool:
            return {"success": False, "error": "Could not access MediaPool.", "clip_ids": []}

        # Filter to existing files
        valid_paths = [os.path.abspath(p) for p in file_paths if os.path.exists(p)]
        if not valid_paths:
            return {"success": False, "error": "None of the specified file paths exist.", "clip_ids": []}

        # Handle bin creation / navigation
        target_folder = media_pool.GetRootFolder()
        if bin_name:
            subfolders = target_folder.GetSubFolderList() or []
            existing_bin = next((f for f in subfolders if f.GetName() == bin_name), None)
            if existing_bin:
                target_folder = existing_bin
            else:
                new_bin = media_pool.AddSubFolder(target_folder, bin_name)
                if new_bin:
                    target_folder = new_bin
            media_pool.SetCurrentFolder(target_folder)

        # Import media items
        items = media_pool.ImportMedia(valid_paths) or []
        registered_clips = []

        for item in items:
            name = item.GetName() if hasattr(item, "GetName") else os.path.basename(valid_paths[0])
            clip_id = registry.register(item, "MediaPoolItem", {"name": name})
            registered_clips.append({"id": clip_id, "name": name})

        return {
            "success": True,
            "imported_count": len(items),
            "clips": registered_clips,
            "bin": bin_name,
            "message": f"Successfully imported {len(items)} clip(s) into bin '{bin_name}'."
        }
    except Exception as e:
        return {"success": False, "error": str(e), "clip_ids": []}


def create_bin(bin_name: str) -> Dict[str, Any]:
    """Create a new bin/folder inside the Media Pool."""
    resolve, status = connection.connect()
    if not resolve:
        return {"success": False, "error": "DaVinci Resolve is offline.", "status": status}

    try:
        pm = resolve.GetProjectManager()
        project = pm.GetCurrentProject() if pm else None
        if not project:
            return {"success": False, "error": "No active project open."}

        mp = project.GetMediaPool()
        root = mp.GetRootFolder()
        new_bin = mp.AddSubFolder(root, bin_name)
        if not new_bin:
            return {"success": False, "error": f"Failed to create bin '{bin_name}'."}

        bin_id = registry.register(new_bin, "Folder", {"name": bin_name})
        return {
            "success": True,
            "bin_id": bin_id,
            "name": bin_name,
            "message": f"Bin '{bin_name}' created in Media Pool."
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def create_timeline_from_clips(timeline_name: str, clip_ids: List[str]) -> Dict[str, Any]:
    """Create a new timeline populated with the specified registered clip items."""
    resolve, status = connection.connect()
    if not resolve:
        return {"success": False, "error": "DaVinci Resolve is offline.", "status": status}

    try:
        pm = resolve.GetProjectManager()
        project = pm.GetCurrentProject() if pm else None
        if not project:
            return {"success": False, "error": "No active project open."}

        mp = project.GetMediaPool()
        clip_objects = []
        for cid in clip_ids:
            obj = registry.get(cid)
            if obj:
                clip_objects.append(obj)

        if not clip_objects:
            return {"success": False, "error": "No valid clips found for the provided IDs."}

        timeline = mp.CreateTimelineFromClips(timeline_name, clip_objects)
        if not timeline:
            return {"success": False, "error": f"Failed to create timeline '{timeline_name}'."}

        tl_id = registry.register(timeline, "Timeline", {"name": timeline_name})
        return {
            "success": True,
            "timeline_id": tl_id,
            "name": timeline_name,
            "clip_count": len(clip_objects),
            "message": f"Timeline '{timeline_name}' created with {len(clip_objects)} clip(s)."
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

