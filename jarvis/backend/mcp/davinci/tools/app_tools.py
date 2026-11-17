"""
App-level DaVinci Resolve MCP Tools for Project JARVIS.
Handles page navigation, version queries, and app status.
"""

from typing import Dict, Any
from jarvis.backend.mcp.davinci.connection import connection
from jarvis.backend.mcp.davinci.object_registry import registry


VALID_PAGES = ["media", "cut", "edit", "fusion", "color", "fairlight", "deliver"]


def switch_page(page_name: str) -> Dict[str, Any]:
    """Switch DaVinci Resolve to a specific page (edit, color, deliver, cut, fusion, fairlight, media)."""
    target_page = page_name.lower().strip()
    if target_page not in VALID_PAGES:
        return {
            "success": False,
            "error": f"Invalid page '{page_name}'. Valid pages are: {', '.join(VALID_PAGES)}"
        }

    resolve, status = connection.connect()
    if not resolve:
        return {
            "success": False,
            "error": "DaVinci Resolve is not running or accessible.",
            "status": status
        }

    try:
        success = resolve.OpenPage(target_page)
        return {
            "success": bool(success),
            "page": target_page,
            "message": f"Switched DaVinci Resolve to {target_page.capitalize()} page." if success else f"Failed to switch to {target_page} page."
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def get_current_page() -> Dict[str, Any]:
    """Get the currently open page in DaVinci Resolve."""
    resolve, status = connection.connect()
    if not resolve:
        return {
            "success": False,
            "error": "DaVinci Resolve is not running.",
            "status": status
        }

    try:
        current_page = resolve.GetCurrentPage()
        return {
            "success": True,
            "page": current_page,
            "message": f"Active DaVinci Resolve page: {current_page}"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def get_app_version() -> Dict[str, Any]:
    """Get DaVinci Resolve product version and edition."""
    resolve, status = connection.connect()
    if not resolve:
        return {
            "success": False,
            "error": "DaVinci Resolve is not running.",
            "status": status
        }

    try:
        version = resolve.GetVersionString() if hasattr(resolve, "GetVersionString") else "Unknown"
        product = resolve.GetProductName() if hasattr(resolve, "GetProductName") else "DaVinci Resolve"
        return {
            "success": True,
            "product_name": product,
            "version": version
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

