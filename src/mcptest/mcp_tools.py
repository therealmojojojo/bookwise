"""
MCP Tools for test server

Simple tools to demonstrate MCP protocol compliance.
"""
import logging
from datetime import datetime
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


def get_mcp_tools() -> List[Dict[str, Any]]:
    """
    Return list of available MCP tools

    MCP Tool Schema:
    - name: Tool identifier
    - description: What the tool does
    - inputSchema: JSON Schema for tool parameters
    """
    return [
        {
            "name": "hello_world",
            "description": "Simple greeting tool to test MCP connectivity. Returns a personalized greeting.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Name of the person to greet"
                    }
                },
                "required": ["name"]
            }
        },
        {
            "name": "get_server_time",
            "description": "Get current server time. Useful for testing OAuth and MCP connection.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "timezone": {
                        "type": "string",
                        "description": "Timezone name (e.g., 'UTC', 'US/Pacific'). Optional, defaults to server timezone.",
                        "default": "UTC"
                    }
                }
            }
        },
        {
            "name": "echo",
            "description": "Echo back the input message. Useful for debugging MCP tool calls.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "message": {
                        "type": "string",
                        "description": "Message to echo back"
                    }
                },
                "required": ["message"]
            }
        }
    ]


async def call_mcp_tool(tool_name: str, arguments: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Execute MCP tool and return results

    MCP Response Format:
    - content: List of content blocks
    - Each block has:
      - type: "text" | "image" | "resource"
      - text: Content text (for type="text")

    Args:
        tool_name: Name of tool to call
        arguments: Tool arguments

    Returns:
        List of MCP content blocks

    Raises:
        ValueError: If tool not found
    """
    logger.info(f"Calling tool: {tool_name} with args: {arguments}")

    if tool_name == "hello_world":
        name = arguments.get("name", "World")
        response_text = f"Hello, {name}! 👋\n\nThis is a test MCP server following the pattern from 'The Missing MCP Playbook'.\n\nYour connection is working correctly!"

        return [
            {
                "type": "text",
                "text": response_text
            }
        ]

    elif tool_name == "get_server_time":
        timezone = arguments.get("timezone", "UTC")
        current_time = datetime.now().isoformat()

        response_text = f"Current server time: {current_time}\n"
        response_text += f"Timezone: {timezone}\n"
        response_text += f"Timestamp: {datetime.now().timestamp()}"

        return [
            {
                "type": "text",
                "text": response_text
            }
        ]

    elif tool_name == "echo":
        message = arguments.get("message", "")

        response_text = f"Echo: {message}\n\n"
        response_text += f"Received at: {datetime.now().isoformat()}\n"
        response_text += f"Message length: {len(message)} characters"

        return [
            {
                "type": "text",
                "text": response_text
            }
        ]

    else:
        raise ValueError(f"Unknown tool: {tool_name}")
