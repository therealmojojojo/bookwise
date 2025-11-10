"""
MCP SERVER WITH OAUTH AUTHENTICATION
Never-expiring tokens for personal use
WITH STREAMABLE HTTP SESSION SUPPORT
"""
import logging
import asyncio
import os
import uuid
from datetime import datetime
from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from typing import Dict

# Load .env file
load_dotenv()

# Import OAuth components
from src.mcptest.oauth_store import OAuthStore
import src.mcptest.simple_oauth as oauth

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="BookWise MCP Server with OAuth")

# Initialize OAuth
API_KEY = os.getenv("BOOKWISE_API_KEY", "change-me-in-production")
oauth_store = OAuthStore()
oauth.initialize_oauth(oauth_store, API_KEY)
logger.info(f"✅ OAuth initialized with API key configured")

# Session storage for Streamable HTTP
mcp_sessions: Dict[str, dict] = {}

# Add CORS middleware to handle all responses
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://claude.ai", "https://api.claude.ai", "*"],  # Allow Claude.ai specifically
    allow_credentials=True,
    allow_methods=["GET", "POST", "HEAD", "OPTIONS", "DELETE"],
    allow_headers=["Content-Type", "Authorization", "Mcp-Session-Id", "mcp-session-id", "MCP-Protocol-Version", "mcp-protocol-version"],
    expose_headers=["MCP-Protocol-Version"],
    max_age=3600,
)

# Add middleware to log ALL requests
@app.middleware("http")
async def log_all_requests(request: Request, call_next):
    logger.info(f"🔍 {request.method} {request.url.path} - Headers: {dict(request.headers)}")
    response = await call_next(request)
    logger.info(f"   → Response: {response.status_code}")
    return response


def create_sse_response(data: dict):
    """
    Wrap JSON-RPC response in SSE format

    SSE format is:
    data: <json>\n\n
    """
    import json
    async def generate():
        yield f"data: {json.dumps(data)}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
        }
    )


@app.head("/")
async def mcp_head():
    """Protocol discovery"""
    logger.info("HEAD / - Protocol discovery")
    return Response(
        status_code=200,
        headers={
            "MCP-Protocol-Version": "2025-06-18",
            "Access-Control-Allow-Origin": "*"
        }
    )


@app.options("/")
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


@app.post("/")
async def mcp_endpoint(request: Request):
    """
    MCP endpoint with OAuth authentication and Streamable HTTP session support

    CRITICAL: Implements selective authentication per MCP spec:
    - initialize: NO token required (capability discovery)
    - notifications/initialized: Session ID only
    - tools/list, tools/call: REQUIRE OAuth token
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
        token_data = oauth.verify_oauth_token(token)
        if token_data:
            logger.info(f"[{timestamp}] ✅ Optional auth - user: {token_data.get('user_id')} for {method}")
        else:
            logger.info(f"[{timestamp}] ⚠️  Invalid token provided, but continuing without auth")
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
                "user_id": None,  # Will be set when tools/list is called with OAuth token
                "created_at": timestamp,
                "initialized": True
            }
            logger.info(f"   ✅ initialize - created session: {session_id} (no auth required per MCP spec)")

            response = JSONResponse(
                status_code=200,
                content={
                    "jsonrpc": "2.0",
                    "result": {
                        "protocolVersion": "2025-06-18",
                        "serverInfo": {
                            "name": "BookWise Simple",
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
            # Update session with user_id from OAuth token
            if token_data and session_id in mcp_sessions:
                mcp_sessions[session_id]["user_id"] = token_data.get("user_id")

            logger.info(f"   ✅ tools/list (session: {session_id}, user: {token_data.get('user_id') if token_data else None})")
            tools = [
                {
                    "name": "hello_world",
                    "description": "Simple greeting to test MCP connectivity",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "name": {
                                "type": "string",
                                "description": "Name to greet"
                            }
                        },
                        "required": ["name"]
                    }
                },
                {
                    "name": "get_time",
                    "description": "Get current server time",
                    "inputSchema": {
                        "type": "object"
                    }
                }
            ]

            response_payload = {
                "jsonrpc": "2.0",
                "result": {"tools": tools},
                "id": request_id
            }
            logger.info(f"      → Returning {len(tools)} tools: {[t['name'] for t in tools]}")
            logger.info(f"      → Full response: {response_payload}")

            return JSONResponse(
                status_code=200,
                content=response_payload
            )

        # Method: tools/call
        elif method == "tools/call":
            tool_name = params.get("name")
            tool_args = params.get("arguments", {})

            # Update session with user_id from OAuth token
            user_id = token_data.get("user_id") if token_data else None
            if token_data and session_id in mcp_sessions:
                mcp_sessions[session_id]["user_id"] = user_id

            logger.info(f"   ✅ tools/call: {tool_name} (session: {session_id}, user: {user_id})")
            logger.info(f"      → Tool arguments: {tool_args}")
            logger.info(f"      → Request ID: {request_id}")

            if tool_name == "hello_world":
                name = tool_args.get("name", "World")
                text = f"Hello, {name}! 👋\n\nThis MCP server has OAuth + Sessions working!\nUser: {user_id}\nSession: {session_id}\n\nIf you're seeing this, it worked!"

            elif tool_name == "get_time":
                text = f"Current time: {datetime.now().isoformat()}\nUser: {user_id}"

            else:
                text = f"Unknown tool: {tool_name}"

            response_content = {
                "jsonrpc": "2.0",
                "result": {
                    "content": [{"type": "text", "text": text}]
                },
                "id": request_id
            }
            logger.info(f"      → Response content: {response_content}")

            return JSONResponse(
                status_code=200,
                content=response_content
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


# OAuth Discovery Endpoints
@app.get("/.well-known/oauth-protected-resource")
async def oauth_discovery(request: Request):
    """OAuth Protected Resource Metadata (RFC 8414)"""
    return await oauth.oauth_discovery(request)


@app.get("/.well-known/oauth-authorization-server")
async def oauth_auth_server(request: Request):
    """OAuth Authorization Server Metadata (RFC 8414)"""
    return await oauth.oauth_auth_server(request)


# OAuth Flow Endpoints
@app.post("/register")
async def dynamic_client_registration(request: Request):
    """Dynamic Client Registration (RFC 7591)"""
    return await oauth.dynamic_client_registration(request)


@app.api_route("/authorize", methods=["GET", "HEAD"])
async def authorize(
    request: Request,
    response_type: str = None,
    client_id: str = None,
    redirect_uri: str = None,
    scope: str = None,
    state: str = None,
    code_challenge: str = None,
    code_challenge_method: str = None
):
    """OAuth Authorization Endpoint - Show login form"""
    return await oauth.authorize(
        request, response_type, client_id, redirect_uri,
        scope, state, code_challenge, code_challenge_method
    )


@app.post("/authorize_submit")
async def authorize_submit(request: Request):
    """Handle OAuth login form submission"""
    from fastapi import Form
    form = await request.form()
    return await oauth.authorize_submit(
        api_key=form.get("api_key"),
        client_id=form.get("client_id"),
        redirect_uri=form.get("redirect_uri"),
        response_type=form.get("response_type"),
        scope=form.get("scope", ""),
        code_challenge=form.get("code_challenge"),
        code_challenge_method=form.get("code_challenge_method"),
        state=form.get("state")
    )


@app.post("/token")
async def token_exchange(request: Request):
    """OAuth Token Endpoint - Exchange code for never-expiring token"""
    return await oauth.token_exchange(request)


@app.get("/")
async def mcp_sse_stream(request: Request):
    """
    GET / - Open SSE stream for MCP communication with OAuth

    Per MCP spec: "The client MAY issue an HTTP GET to the MCP endpoint.
    This can be used to open an SSE stream, allowing the server to communicate
    to the client, without the client first sending data via HTTP POST."

    CRITICAL: Must send server capabilities with requestEndpoint in first message!
    """
    # Validate OAuth token
    auth_header = request.headers.get("authorization", "")
    if not auth_header.startswith("Bearer "):
        logger.warning("GET / - Missing or invalid Authorization header")
        return JSONResponse(
            status_code=401,
            content={"error": "Unauthorized - Bearer token required"}
        )

    token = auth_header.replace("Bearer ", "")
    token_data = oauth.verify_oauth_token(token)
    if not token_data:
        logger.warning("GET / - Invalid OAuth token")
        return JSONResponse(
            status_code=401,
            content={"error": "Unauthorized - Invalid token"}
        )

    logger.info(f"GET / - Opening SSE stream for user: {token_data.get('user_id')}")

    async def event_generator():
        """Generate SSE events"""
        try:
            # Send server capabilities with requestEndpoint (CRITICAL FOR CLAUDE.AI)
            import json
            base_url = f"{request.url.scheme}://{request.url.netloc}"

            server_info = {
                "protocolVersion": "2025-06-18",
                "capabilities": {
                    "tools": {}
                },
                "serverInfo": {
                    "name": "BookWise Simple",
                    "version": "1.0.0"
                },
                "requestEndpoint": f"{base_url}/"  # Tell Claude where to POST!
            }

            logger.info(f"Sending server capabilities with requestEndpoint: {server_info['requestEndpoint']}")

            # SSE format: event + data
            yield f"event: message\n"
            yield f"data: {json.dumps({'jsonrpc': '2.0', 'result': server_info})}\n\n"

            # Keep connection alive with periodic pings
            while True:
                if await request.is_disconnected():
                    logger.info("SSE client disconnected")
                    break

                # Send keepalive every 30 seconds
                await asyncio.sleep(30)
                yield f": keepalive\n\n"

        except asyncio.CancelledError:
            logger.info("SSE stream cancelled")
        except Exception as e:
            logger.error(f"SSE error: {e}")

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
            "Access-Control-Allow-Origin": "*",
        }
    )


@app.delete("/")
async def mcp_delete_session(request: Request):
    """
    DELETE / - Close MCP session gracefully

    Per MCP spec, clients may send DELETE to close the session.
    """
    session_id = request.headers.get("mcp-session-id") or request.headers.get("Mcp-Session-Id")

    if session_id and session_id in mcp_sessions:
        del mcp_sessions[session_id]
        logger.info(f"DELETE / - Session closed: {session_id}")
    else:
        logger.info(f"DELETE / - No active session to close")

    return Response(status_code=204)


@app.get("/health")
async def health():
    """Health check"""
    return {"status": "healthy", "server": "Simple MCP", "protocol": "2025-06-18"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
