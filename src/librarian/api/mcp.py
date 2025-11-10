"""
MCP (Model Context Protocol) API endpoints
Implements SSE transport for Remote MCP Servers
"""
from fastapi import APIRouter, Request, Depends
from sse_starlette import EventSourceResponse
import logging
import json
from typing import AsyncIterator

from src.librarian.api.dependencies import verify_api_key
from src.librarian.mcp_server import get_capabilities

logger = logging.getLogger(__name__)

router = APIRouter()


async def mcp_message_stream(request: Request) -> AsyncIterator[dict]:
    """
    SSE message stream for MCP protocol
    
    This handles the bidirectional JSON-RPC communication over SSE.
    Claude.ai will send requests and we'll stream responses back.
    """
    try:
        # Send initial server info with endpoint information
        server_info = get_capabilities()
        
        # Add the POST endpoint URL for Claude.ai to send requests to
        base_url = f"{request.url.scheme}://{request.url.netloc}"
        server_info["requestEndpoint"] = f"{base_url}/mcp/message"
        
        logger.info(f"Sending MCP capabilities: {server_info}")
        yield {
            "event": "message",
            "data": json.dumps({
                "jsonrpc": "2.0",
                "result": server_info
            })
        }
        
        # Keep connection alive and handle incoming messages
        while True:
            # Check if client disconnected
            if await request.is_disconnected():
                logger.info("MCP client disconnected")
                break
            
            # In a real implementation, this would read from a message queue
            # populated by POST requests from Claude.ai
            # For now, we just keep the connection alive
            yield {
                "event": "ping",
                "data": ""
            }
            
            # Sleep to prevent busy loop
            import asyncio
            await asyncio.sleep(30)  # Keep-alive every 30 seconds
            
    except Exception as e:
        logger.error(f"MCP stream error: {e}", exc_info=True)
        yield {
            "event": "error",
            "data": json.dumps({"error": str(e)})
        }


@router.options("/mcp/sse")
async def mcp_sse_options():
    """
    CORS preflight for MCP endpoint
    
    Required for browser-based clients like Claude.ai web
    """
    from fastapi import Response
    
    logger.info("MCP SSE OPTIONS request (CORS preflight)")
    
    return Response(
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, HEAD, OPTIONS",
            "Access-Control-Allow-Headers": "Authorization, Content-Type, MCP-Protocol-Version, Accept",
            "Access-Control-Max-Age": "3600",
            "MCP-Protocol-Version": "2025-06-18",
            "Content-Type": "text/event-stream"
        }
    )


@router.head("/mcp/sse")
async def mcp_sse_head():
    """
    MCP protocol discovery endpoint (HEAD request)
    
    Claude.ai uses this to discover the MCP protocol version.
    Does NOT require authentication - this is critical for discovery.
    """
    from fastapi.responses import Response
    
    logger.info("🔍🔍🔍 MCP SSE HEAD request (protocol discovery) 🔍🔍🔍")
    
    headers = {
        "MCP-Protocol-Version": "2025-06-18",
        "Content-Type": "text/event-stream",
        "Access-Control-Allow-Origin": "*",
        "Cache-Control": "no-cache"
    }
    logger.info(f"🔍 Returning headers: {headers}")
    
    return Response(
        status_code=200,
        headers=headers
    )


async def mcp_handle_post_message(request: Request):
    """Handle POST JSON-RPC messages for Streamable HTTP"""
    try:
        # Parse JSON-RPC request
        body = await request.json()
        logger.info(f"MCP POST message received: {body.get('method', 'unknown')}")

        jsonrpc_version = body.get("jsonrpc")
        method = body.get("method")
        params = body.get("params", {})
        request_id = body.get("id")

        if jsonrpc_version != "2.0":
            return {
                "jsonrpc": "2.0",
                "error": {
                    "code": -32600,
                    "message": "Invalid Request: Only JSON-RPC 2.0 supported"
                },
                "id": request_id
            }

        # Handle MCP methods
        if method == "initialize":
            result = get_capabilities()

        elif method == "tools/list":
            from src.librarian.mcp_server import list_tools
            tools = await list_tools()
            result = {"tools": [tool.model_dump() for tool in tools]}

        elif method == "tools/call":
            from src.librarian.mcp_server import call_tool
            tool_name = params.get("name")
            tool_args = params.get("arguments", {})
            result_content = await call_tool(tool_name, tool_args)
            result = {"content": [item.model_dump() for item in result_content]}

        else:
            return {
                "jsonrpc": "2.0",
                "error": {
                    "code": -32601,
                    "message": f"Method not found: {method}"
                },
                "id": request_id
            }

        # Return success response
        return {
            "jsonrpc": "2.0",
            "result": result,
            "id": request_id
        }

    except Exception as e:
        logger.error(f"MCP POST message error: {e}", exc_info=True)
        return {
            "jsonrpc": "2.0",
            "error": {
                "code": -32603,
                "message": f"Internal error: {str(e)}"
            },
            "id": body.get("id") if 'body' in locals() else None
        }


@router.api_route("/mcp/sse", methods=["GET", "POST"])
async def mcp_streamable_http_endpoint(
    request: Request
):
    """
    MCP Streamable HTTP endpoint (Protocol 2025-06-18)

    This is the main entry point for Remote MCP connections from Claude.ai.
    Supports both GET (SSE streaming) and POST (JSON-RPC messages).

    ⚠️ TEMPORARILY NO AUTH - debugging Claude.ai connection issues
    """
    from datetime import datetime
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    auth_header = request.headers.get("Authorization", "NONE")
    logger.info(f"[{timestamp}] ✅ MCP {request.method} NO AUTH - auth header: {auth_header[:50] if auth_header != 'NONE' else 'NONE'}")

    # GET request: Return SSE stream
    if request.method == "GET":
        logger.info("Returning SSE stream for MCP connection")
        return EventSourceResponse(
            mcp_message_stream(request),
            media_type="text/event-stream",
            headers={
                "MCP-Protocol-Version": "2025-06-18",
                "Access-Control-Allow-Origin": "*",
                "Cache-Control": "no-cache"
            }
        )

    # POST request: Handle JSON-RPC message
    else:
        return await mcp_handle_post_message(request)


@router.post("/mcp/message")
async def mcp_message_endpoint(
    request: Request
):
    """
    MCP message endpoint for JSON-RPC requests

    Claude.ai sends JSON-RPC requests here, and we respond with tool results.

    ⚠️ TEMPORARILY NO AUTH - debugging Claude.ai connection issues
    """
    try:
        # Parse JSON-RPC request
        body = await request.json()
        logger.info(f"MCP message received: {body.get('method', 'unknown')}")
        
        jsonrpc_version = body.get("jsonrpc")
        method = body.get("method")
        params = body.get("params", {})
        request_id = body.get("id")
        
        if jsonrpc_version != "2.0":
            return {
                "jsonrpc": "2.0",
                "error": {
                    "code": -32600,
                    "message": "Invalid Request: Only JSON-RPC 2.0 supported"
                },
                "id": request_id
            }
        
        # Handle MCP methods
        if method == "initialize":
            result = get_capabilities()
        
        elif method == "tools/list":
            # Import the handlers
            from src.librarian.mcp_server import list_tools, call_tool
            
            # Get list of tools
            tools = await list_tools()
            result = {"tools": [tool.model_dump() for tool in tools]}
        
        elif method == "tools/call":
            # Import the handlers
            from src.librarian.mcp_server import call_tool
            
            # Call a tool
            tool_name = params.get("name")
            tool_args = params.get("arguments", {})
            
            result_content = await call_tool(tool_name, tool_args)
            result = {"content": [item.model_dump() for item in result_content]}
        
        else:
            return {
                "jsonrpc": "2.0",
                "error": {
                    "code": -32601,
                    "message": f"Method not found: {method}"
                },
                "id": request_id
            }
        
        # Return success response
        return {
            "jsonrpc": "2.0",
            "result": result,
            "id": request_id
        }
        
    except Exception as e:
        logger.error(f"MCP message error: {e}", exc_info=True)
        return {
            "jsonrpc": "2.0",
            "error": {
                "code": -32603,
                "message": f"Internal error: {str(e)}"
            },
            "id": body.get("id") if body else None
        }

