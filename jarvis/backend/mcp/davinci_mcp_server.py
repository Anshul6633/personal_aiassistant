"""
Standalone Model Context Protocol (MCP) Server for DaVinci Resolve.
Implements standard JSON-RPC 2.0 stdio protocol for Claude Desktop, Claude Code, Cursor, and Antigravity.
"""

import sys
import json
import logging
from jarvis.backend.mcp.davinci.dispatcher import MCP_TOOLS_MANIFEST, execute_davinci_tool

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s", stream=sys.stderr)
logger = logging.getLogger("davinci_mcp_server")


def send_response(response: dict):
    """Serialize and write a JSON-RPC response to stdout followed by a newline."""
    data = json.dumps(response)
    sys.stdout.write(data + "\n")
    sys.stdout.flush()


def handle_request(req: dict) -> dict:
    """Process a single JSON-RPC request and return the response."""
    msg_id = req.get("id")
    method = req.get("method")
    params = req.get("params", {})

    # Protocol initialization
    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {}
                },
                "serverInfo": {
                    "name": "jarvis-davinci-resolve-mcp",
                    "version": "1.0.0"
                }
            }
        }

    # Ping
    elif method == "ping":
        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "result": {}
        }

    # List Available Tools
    elif method == "tools/list":
        try:
            from jarvis.backend.mcp.davinci.dispatcher import get_tools_catalog
            import asyncio
            catalog = asyncio.run(get_tools_catalog())
            all_tools = []
            for cat in catalog["categories"]:
                for t in cat["tools"]:
                    all_tools.append({
                        "name": t["name"],
                        "description": t["description"],
                        "inputSchema": t["inputSchema"]
                    })
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "tools": all_tools
                }
            }
        except Exception as e:
            logger.error(f"Error listing tools: {e}")
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "tools": MCP_TOOLS_MANIFEST
                }
            }

    # Execute Tool Call
    elif method == "tools/call":
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        logger.info(f"Executing tool '{tool_name}' with arguments: {arguments}")
        
        result_data = execute_davinci_tool(tool_name, arguments)
        
        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "result": {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps(result_data, indent=2)
                    }
                ],
                "isError": not result_data.get("success", True) if isinstance(result_data, dict) else False
            }
        }

    # Unknown method
    else:
        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "error": {
                "code": -32601,
                "message": f"Method not found: {method}"
            }
        }


def run_stdio_server():
    """Main stdio loop reading JSON-RPC lines from stdin."""
    logger.info("DaVinci Resolve MCP Server started on stdio...")
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
            # Notifications do not require a response (no id)
            if "id" not in req and req.get("method", "").startswith("notifications/"):
                continue

            response = handle_request(req)
            send_response(response)
        except json.JSONDecodeError as e:
            send_response({
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32700, "message": f"Parse error: {e}"}
            })
        except Exception as e:
            logger.error(f"Error handling request: {e}", exc_info=True)
            send_response({
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32603, "message": f"Internal server error: {e}"}
            })


if __name__ == "__main__":
    run_stdio_server()

