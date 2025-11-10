"""
MCP Protocol at Root Path
Implements working pattern from simple_server.py for Claude.ai integration
"""
import uuid
import logging
from datetime import datetime
from typing import Dict
from fastapi import APIRouter, Request, Response
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)

# Create router
router = APIRouter()

# Session storage for Streamable HTTP
mcp_sessions: Dict[str, dict] = {}


@router.head("/")
async def mcp_head():
    """Protocol discovery - Claude.ai's first request"""
    logger.info("HEAD / - Protocol discovery")
    return Response(
        status_code=200,
        headers={
            "MCP-Protocol-Version": "2025-06-18",
            "Access-Control-Allow-Origin": "*"
        }
    )


@router.options("/")
async def mcp_options():
    """CORS preflight"""
    logger.info("OPTIONS / - CORS preflight")
    return Response(
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, HEAD, OPTIONS, DELETE",
            "Access-Control-Allow-Headers": "Content-Type, Authorization, Mcp-Session-Id",
            "MCP-Protocol-Version": "2025-06-18"
        }
    )


@router.post("/")
async def mcp_endpoint(request: Request):
    """
    Main MCP endpoint - handles all JSON-RPC methods

    Implements exact pattern from simple_server.py that works with Claude.ai
    """
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # Parse body FIRST to determine method (for selective auth)
    try:
        body = await request.json()
        method = body.get("method")
        params = body.get("params", {})
        request_id = body.get("id")
    except Exception as e:
        logger.error(f"[{timestamp}] ❌ Failed to parse request body: {e}")
        return JSONResponse(
            status_code=400,
            content={
                "jsonrpc": "2.0",
                "error": {"code": -32700, "message": "Parse error"},
                "id": None
            }
        )

    logger.info(f"[{timestamp}] 📨 POST / - method={method}")

    # NO AUTHENTICATION - Development/Testing mode for Claude.ai
    # All methods work without OAuth
    token_data = None
    auth_header = request.headers.get("authorization", "")

    # Try to get token if provided (optional)
    if auth_header.startswith("Bearer "):
        token = auth_header.replace("Bearer ", "")
        # Could verify token here if needed, but continue anyway
        logger.info(f"[{timestamp}] ℹ️  Token provided (optional)")
    else:
        logger.info(f"[{timestamp}] ℹ️  {method} - no auth provided (dev mode allows this)")

    # Check for session ID (Streamable HTTP)
    session_id = request.headers.get("mcp-session-id") or request.headers.get("Mcp-Session-Id")

    try:
        # Validate JSON-RPC
        if body.get("jsonrpc") != "2.0":
            return JSONResponse(
                status_code=200,
                content={
                    "jsonrpc": "2.0",
                    "error": {"code": -32600, "message": "Invalid Request"},
                    "id": request_id
                }
            )

        # Handle initialize - creates new session if no session_id
        if method == "initialize" and not session_id:
            session_id = str(uuid.uuid4())
            mcp_sessions[session_id] = {
                "user_id": None,
                "created_at": timestamp,
                "initialized": True
            }
            logger.info(f"   ✅ initialize - created session: {session_id}")

            response = JSONResponse(
                status_code=200,
                content={
                    "jsonrpc": "2.0",
                    "result": {
                        "protocolVersion": "2025-06-18",
                        "serverInfo": {
                            "name": "BookWise Library",
                            "version": "1.0.0"
                        },
                        "capabilities": {"tools": {}}
                    },
                    "id": request_id
                }
            )
            response.headers["Mcp-Session-Id"] = session_id
            return response

        # All other requests require valid session
        if not session_id or session_id not in mcp_sessions:
            logger.warning(f"   ❌ Invalid or missing session ID: {session_id}")
            return JSONResponse(
                status_code=400,
                content={
                    "jsonrpc": "2.0",
                    "error": {"code": -32000, "message": "Invalid or missing session ID"},
                    "id": request_id
                }
            )

        # Method: notifications/initialized
        if method == "notifications/initialized":
            logger.info(f"   ✅ notifications/initialized (session: {session_id})")
            return Response(status_code=204)

        # Method: tools/list
        elif method == "tools/list":
            from src.librarian.mcp_server import list_tools

            logger.info(f"   ✅ tools/list (session: {session_id})")
            tools = await list_tools()

            response_payload = {
                "jsonrpc": "2.0",
                "result": {"tools": [tool.model_dump() for tool in tools]},
                "id": request_id
            }
            logger.info(f"      → Returning {len(tools)} tools: {[t.name for t in tools]}")

            return JSONResponse(
                status_code=200,
                content=response_payload
            )

        # Method: tools/call
        elif method == "tools/call":
            from src.librarian.mcp_server import call_tool

            tool_name = params.get("name")
            tool_args = params.get("arguments", {})

            logger.info(f"   ✅ tools/call: {tool_name} (session: {session_id})")
            logger.info(f"      → Tool arguments: {tool_args}")

            try:
                result_content = await call_tool(tool_name, tool_args)

                response_content = {
                    "jsonrpc": "2.0",
                    "result": {
                        "content": [item.model_dump() for item in result_content]
                    },
                    "id": request_id
                }
                logger.info(f"      → Tool executed successfully")

                return JSONResponse(
                    status_code=200,
                    content=response_content
                )
            except Exception as e:
                logger.error(f"      ❌ Tool execution error: {e}", exc_info=True)
                return JSONResponse(
                    status_code=200,
                    content={
                        "jsonrpc": "2.0",
                        "error": {
                            "code": -32603,
                            "message": f"Tool execution failed: {str(e)}"
                        },
                        "id": request_id
                    }
                )

        # Unknown method
        else:
            logger.warning(f"   ❌ Unknown method: {method}")
            return JSONResponse(
                status_code=200,
                content={
                    "jsonrpc": "2.0",
                    "error": {"code": -32601, "message": f"Method not found: {method}"},
                    "id": request_id
                }
            )

    except Exception as e:
        logger.error(f"   ❌ Error: {e}", exc_info=True)
        return JSONResponse(
            status_code=200,
            content={
                "jsonrpc": "2.0",
                "error": {"code": -32603, "message": f"Internal error: {str(e)}"},
                "id": body.get("id") if 'body' in locals() else None
            }
        )
