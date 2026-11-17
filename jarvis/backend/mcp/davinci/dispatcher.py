"""
Master Tool Dispatcher and Schema Registry for DaVinci Resolve MCP.
Integrates 440+ tools across 11 functional categories from lordhoell/davinci-resolve-mcp.
"""

import json
import logging
import asyncio
from typing import Dict, Any, List, Optional

from davinci_resolve_mcp.server import mcp
from jarvis.backend.mcp.davinci.connection import connection
from jarvis.backend.mcp.davinci.object_registry import registry
from jarvis.backend.mcp.davinci.tools import (
    app_tools,
    project_tools,
    media_tools,
    timeline_tools,
    color_audio_tools,
    render_tools
)
from jarvis.backend.skills.davinci_resolve.fcpxml_generator import fcpxml_generator

logger = logging.getLogger("davinci_dispatcher")

CATEGORY_METADATA: Dict[str, Dict[str, Any]] = {
    "Project Management": {
        "description": "Create/load/export projects, manage databases, cloud projects",
        "icon": "FolderKanban"
    },
    "Timeline Editing": {
        "description": "Add/remove tracks, insert titles & generators, manage markers, export timelines",
        "icon": "Layers"
    },
    "Media Pool": {
        "description": "Import media, create timelines from clips, organize folders, sync audio",
        "icon": "Film"
    },
    "Clip Operations": {
        "description": "Set clip properties, manage Fusion comps, color versions, takes, CDL, stabilize, smart reframe",
        "icon": "Scissors"
    },
    "Color Grading": {
        "description": "Node graph control, LUT management, grade application, color groups",
        "icon": "Palette"
    },
    "Rendering": {
        "description": "Configure render settings, formats/codecs, add render jobs, start/stop renders",
        "icon": "PlayCircle"
    },
    "Fusion Compositing": {
        "description": "Add/connect nodes, set inputs, keyframe animation, expressions, render comps",
        "icon": "Workflow"
    },
    "Gallery & Stills": {
        "description": "Manage still albums, PowerGrade albums, import/export stills",
        "icon": "Image"
    },
    "Media Storage": {
        "description": "Browse volumes, import from disk, manage clip/timeline mattes",
        "icon": "HardDrive"
    },
    "Captions & Audio": {
        "description": "Generate subtitles from audio, voice isolation, Fairlight presets, transcription",
        "icon": "Mic"
    },
    "App Control": {
        "description": "Page navigation, layout presets, version info, keyframe modes",
        "icon": "Sliders"
    }
}


def categorize_tool(name: str) -> str:
    """Categorize a tool name into one of the 11 user categories."""
    n = name.lower()
    if any(w in n for w in ["subtitle", "transcribe", "voice_isolation", "fairlight"]) or (n.startswith("timeline_") and "audio" in n):
        return "Captions & Audio"
    if n.startswith(("gallery_", "still_")) or "export_current_frame" in n:
        return "Gallery & Stills"
    if n.startswith("media_storage_"):
        return "Media Storage"
    if n.startswith(("graph_", "color_group_")) or "lut" in n or "grade" in n or "color" in n:
        return "Color Grading"
    if any(w in n for w in ["render", "deliver", "export_project"]):
        return "Rendering"
    if n.startswith(("fusion_", "comp_", "flow_", "input_", "output_", "spline_", "tool_", "polyline_")):
        return "Fusion Compositing"
    if n.startswith(("resolve_", "clear_object_cache", "get_object_cache_info", "initialize")):
        return "App Control"
    if n.startswith(("folder_", "media_pool_")) and not n.startswith("media_pool_item_"):
        return "Media Pool"
    if n.startswith(("project_manager_", "project_save", "project_get_name", "project_load", "project_create", "project_set_name", "project_get_setting", "project_set_setting", "project_get_preset", "project_set_preset")):
        return "Project Management"
    if n.startswith(("timeline_item_", "media_pool_item_")) or any(w in n for w in ["clip", "reframe", "stabilize", "cdl", "take", "version"]):
        return "Clip Operations"
    if n.startswith("timeline_") or any(w in n for w in ["track", "marker", "generator"]):
        return "Timeline Editing"
    if n.startswith("project_"):
        return "Project Management"
    return "App Control"


# Cached tools catalog
_TOOLS_CATALOG_CACHE: Optional[Dict[str, Any]] = None
MCP_TOOLS_MANIFEST: List[Dict[str, Any]] = []


async def get_tools_catalog() -> Dict[str, Any]:
    """Retrieve full catalog of 440+ tools grouped into the 11 categories."""
    global _TOOLS_CATALOG_CACHE
    if _TOOLS_CATALOG_CACHE is not None:
        return _TOOLS_CATALOG_CACHE

    mcp_tools = await mcp.list_tools()
    grouped: Dict[str, List[Dict[str, Any]]] = {cat: [] for cat in CATEGORY_METADATA.keys()}

    for t in mcp_tools:
        cat = categorize_tool(t.name)
        if cat not in grouped:
            grouped[cat] = []
        
        grouped[cat].append({
            "name": t.name,
            "description": t.description or "",
            "category": cat,
            "inputSchema": t.inputSchema
        })

    categories_summary = []
    total_tools = 0
    for cat_name, meta in CATEGORY_METADATA.items():
        tools_in_cat = grouped.get(cat_name, [])
        count = len(tools_in_cat)
        total_tools += count
        categories_summary.append({
            "category": cat_name,
            "count": count,
            "description": meta["description"],
            "icon": meta["icon"],
            "tools": tools_in_cat
        })

    _TOOLS_CATALOG_CACHE = {
        "total_tools": total_tools,
        "categories_count": len(categories_summary),
        "categories": categories_summary,
        "grouped": grouped
    }
    return _TOOLS_CATALOG_CACHE


async def execute_davinci_tool_async(tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Execute any DaVinci tool (FastMCP 440+ tools or JARVIS high-level helpers)."""
    try:
        # 1. JARVIS High-level convenience tools
        if tool_name == "davinci_get_status":
            return connection.get_status()

        elif tool_name == "davinci_switch_page":
            return app_tools.switch_page(arguments.get("page", "edit"))

        elif tool_name == "davinci_get_current_page":
            return app_tools.get_current_page()

        elif tool_name == "davinci_list_projects":
            return project_tools.list_projects()

        elif tool_name == "davinci_create_project":
            return project_tools.create_project(
                name=arguments.get("name", "JARVIS Project"),
                vertical_shorts=arguments.get("vertical_shorts", True)
            )

        elif tool_name == "davinci_load_project":
            return project_tools.load_project(arguments.get("name", ""))

        elif tool_name == "davinci_save_project":
            return project_tools.save_project()

        elif tool_name == "davinci_set_resolution":
            return project_tools.set_resolution(
                width=arguments.get("width", 1080),
                height=arguments.get("height", 1920)
            )

        elif tool_name == "davinci_import_media":
            return media_tools.import_media(
                file_paths=arguments.get("file_paths", []),
                bin_name=arguments.get("bin_name", "JARVIS Ingested")
            )

        elif tool_name == "davinci_create_bin":
            return media_tools.create_bin(arguments.get("name", "New Bin"))

        elif tool_name == "davinci_create_timeline":
            return timeline_tools.create_empty_timeline(arguments.get("name", "JARVIS Timeline"))

        elif tool_name == "davinci_get_timeline_info":
            return timeline_tools.get_timeline_info()

        elif tool_name == "davinci_add_track":
            return timeline_tools.add_track(arguments.get("track_type", "video"))

        elif tool_name == "davinci_add_marker":
            return timeline_tools.add_marker(
                frame=arguments.get("frame", 0),
                color=arguments.get("color", "Blue"),
                name=arguments.get("name", "Marker"),
                note=arguments.get("note", "")
            )

        elif tool_name == "davinci_apply_lut":
            return color_audio_tools.apply_lut(arguments.get("lut_name", "Rec.709"))

        elif tool_name == "davinci_enable_smart_reframe":
            return color_audio_tools.enable_smart_reframe()

        elif tool_name == "davinci_configure_render":
            preset = arguments.get("preset", "YouTube - 1080p")
            render_tools.configure_render_preset(preset)
            target_dir = arguments.get("target_dir")
            file_name = arguments.get("file_name")
            if target_dir:
                return render_tools.set_render_destination(target_dir, file_name)
            return {"success": True, "preset": preset}

        elif tool_name == "davinci_start_render":
            render_tools.add_render_job()
            return render_tools.start_render()

        elif tool_name == "davinci_get_render_status":
            return render_tools.get_render_status()

        elif tool_name == "davinci_list_registry_objects":
            return {"success": True, "objects": registry.list_objects()}

        elif tool_name == "davinci_clear_registry":
            cleared = registry.clear()
            return {"success": True, "cleared_count": cleared}

        elif tool_name == "davinci_export_fcpxml_fallback":
            from jarvis.backend.database.db import get_db_connection
            from jarvis.backend.config.settings import WORKSPACE_ROOT
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM clips ORDER BY created_at DESC LIMIT 10")
            clips = [dict(r) for r in cursor.fetchall()]
            conn.close()
            v_path = arguments.get("video_path") or (clips[0].get("source_file") if clips else str(WORKSPACE_ROOT / "jarvis" / "tests" / "sample_podcast.mp4"))
            xml_result = fcpxml_generator.generate_timeline(
                video_path=v_path,
                clips=clips,
                timeline_name=arguments.get("timeline_name", "Shorts_Timeline")
            )
            return xml_result

        # 2. FastMCP 440+ tools direct invocation
        raw_result = await mcp.call_tool(tool_name, arguments or {})
        content_items, meta = raw_result
        if content_items and hasattr(content_items[0], "text"):
            text_val = content_items[0].text
            try:
                parsed = json.loads(text_val)
                return parsed
            except Exception:
                return {"success": True, "output": text_val}
        return {"success": True, "result": meta}

    except Exception as e:
        logger.error(f"Error executing tool '{tool_name}': {e}")
        return {
            "success": False,
            "error": str(e),
            "tool": tool_name,
            "fallback_available": True,
            "fallback_hint": "If DaVinci Resolve is offline or Free edition, use FCPXML generator."
        }


def execute_davinci_tool(tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Synchronous bridge for tool execution."""
    try:
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                return pool.submit(lambda: asyncio.run(execute_davinci_tool_async(tool_name, arguments))).result()
        else:
            return asyncio.run(execute_davinci_tool_async(tool_name, arguments))
    except Exception as e:
        return {"success": False, "error": str(e), "tool": tool_name}
