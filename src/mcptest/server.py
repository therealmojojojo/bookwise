"""
MCP Test Server following "The Missing MCP Playbook" pattern

Key Requirements from the article:
1. Root path `/` endpoint (not /mcp or /sse)
2. HEAD endpoint for protocol discovery
3. Selective authentication:
   - initialize: NO auth
   - notifications/initialized: Session ID only
   - tools/list: FULL OAuth
   - tools/call: FULL OAuth
4. OAuth 2.1 with DCR support
5. MCP Protocol 2025-06-18
"""
import logging
import json
from datetime import datetime
from typing import Dict, Any, Optional
from fastapi import FastAPI, Request, Response, HTTPException, status
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager

from .config import config
from .oauth_utils import validate_bearer_token
from .mcp_tools import get_mcp_tools, call_mcp_tool

# Configure logging
logging.basicConfig(
    level=getattr(logging, config.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Session storage (in production, use Redis or similar)
sessions: Dict[str, Dict[str, Any]] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager for FastAPI app"""
    logger.info(f"🚀 Starting {config.mcp_server_name}")
    logger.info(f"   Auth0 Domain: {config.auth0_domain}")
    logger.info(f"   Server URL: {config.mcp_server_url}")
    logger.info(f"   MCP Protocol: 2025-06-18")
    yield
    logger.info(f"👋 Shutting down {config.mcp_server_name}")


app = FastAPI(
    title=config.mcp_server_name,
    version=config.mcp_server_version,
    lifespan=lifespan
)


# ============================================================================
# OAUTH DISCOVERY ENDPOINTS
# ============================================================================

@app.get("/.well-known/oauth-protected-resource")
async def oauth_metadata():
    """
    OAuth Protected Resource Metadata (RFC 9728)

    Required for Claude to discover Auth0 as the authorization server
    and initiate Dynamic Client Registration (DCR).

    This is the FIRST endpoint Claude.ai calls when adding custom connector.
    """
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    logger.info(f"[{timestamp}] 🔍 OAuth metadata requested (for DCR discovery)")

    metadata = {
        "resource": config.mcp_server_url,
        "authorization_servers": [f"https://{config.auth0_domain}"],
        "bearer_methods_supported": ["header"],
        "scopes_supported": [config.scopes_read, config.scopes_execute],
        "mcp_protocol_version": "2025-06-18",
        "mcp_endpoint": f"{config.mcp_server_url}/"
    }

    logger.debug(f"Returning metadata: {json.dumps(metadata, indent=2)}")
    return metadata


@app.get("/.well-known/oauth-authorization-server")
async def oauth_authorization_server():
    """
    OAuth Authorization Server Metadata (RFC 8414)

    Optional: Helps Claude discover Auth0 endpoints directly.
    """
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    logger.info(f"[{timestamp}] 🔍 Auth server metadata requested")

    return {
        "issuer": f"https://{config.auth0_domain}/",
        "authorization_endpoint": f"https://{config.auth0_domain}/authorize",
        "token_endpoint": f"https://{config.auth0_domain}/oauth/token",
        "userinfo_endpoint": f"https://{config.auth0_domain}/userinfo",
        "jwks_uri": f"https://{config.auth0_domain}/.well-known/jwks.json",
        "registration_endpoint": f"https://{config.auth0_domain}/oidc/register",
        "scopes_supported": [config.scopes_read, config.scopes_execute, "openid", "profile", "email"],
        "response_types_supported": ["code"],
        "grant_types_supported": ["authorization_code", "refresh_token"],
        "token_endpoint_auth_methods_supported": ["none", "client_secret_post"],
        "code_challenge_methods_supported": ["S256"]
    }


# ============================================================================
# MCP PROTOCOL ENDPOINTS (ROOT PATH)
# ============================================================================

@app.head("/")
async def mcp_head():
    """
    HEAD endpoint for MCP protocol discovery

    Claude.ai sends this FIRST to discover protocol version.
    Article: "HEAD request — Claude sends HEAD to / for protocol discovery"
    """
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    logger.info(f"[{timestamp}] 🔍 HEAD / - Protocol discovery")

    return Response(
        status_code=200,
        headers={
            "MCP-Protocol-Version": "2025-06-18",
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*"
        }
    )


@app.options("/")
async def mcp_options():
    """CORS preflight for MCP endpoint"""
    logger.info("OPTIONS / - CORS preflight")

    return Response(
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, HEAD, OPTIONS",
            "Access-Control-Allow-Headers": "Authorization, Content-Type, Mcp-Session-Id, MCP-Protocol-Version",
            "Access-Control-Max-Age": "3600",
            "MCP-Protocol-Version": "2025-06-18"
        }
    )


@app.post("/")
async def mcp_endpoint(request: Request):
    """
    Main MCP endpoint at root path (/)

    Handles JSON-RPC 2.0 messages with selective authentication:
    - initialize: NO auth required
    - notifications/initialized: Session ID only
    - tools/list: FULL OAuth validation
    - tools/call: FULL OAuth validation

    Article quote: "The MCP spec is precise about what gets authenticated when."
    """
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    try:
        # Parse JSON-RPC request
        body = await request.json()
        method = body.get("method")
        params = body.get("params", {})
        request_id = body.get("id")

        # Get session ID from header
        session_id = request.headers.get("Mcp-Session-Id")

        logger.info(f"[{timestamp}] 📨 MCP Request: {method} (session: {session_id})")
        logger.debug(f"   Params: {json.dumps(params, indent=2)}")

        # Validate JSON-RPC version
        if body.get("jsonrpc") != "2.0":
            return JSONResponse(
                status_code=200,
                content={
                    "jsonrpc": "2.0",
                    "error": {
                        "code": -32600,
                        "message": "Invalid Request: Only JSON-RPC 2.0 supported"
                    },
                    "id": request_id
                }
            )

        # ====================================================================
        # SELECTIVE AUTHENTICATION LOGIC
        # ====================================================================

        # Method: initialize - NO AUTHENTICATION REQUIRED
        if method == "initialize":
            logger.info("   ✅ initialize - NO AUTH REQUIRED")
            result = {
                "protocolVersion": "2025-06-18",
                "serverInfo": {
                    "name": config.mcp_server_name,
                    "version": config.mcp_server_version
                },
                "capabilities": {
                    "tools": {}
                }
            }

            return JSONResponse(
                status_code=200,
                content={
                    "jsonrpc": "2.0",
                    "result": result,
                    "id": request_id
                }
            )

        # Method: notifications/initialized - SESSION ID ONLY
        elif method == "notifications/initialized":
            logger.info("   ✅ notifications/initialized - SESSION ID ONLY")

            if not session_id:
                logger.warning("   ⚠️  Missing Mcp-Session-Id header")
                # Don't fail - just log warning
                session_id = f"session-{datetime.now().timestamp()}"

            # Store session
            sessions[session_id] = {
                "created_at": datetime.now().isoformat(),
                "initialized": True
            }

            logger.info(f"   Session created: {session_id}")

            # notifications/initialized doesn't expect a response
            return Response(status_code=204)

        # Method: tools/list - FULL OAUTH VALIDATION REQUIRED
        elif method == "tools/list":
            logger.info("   🔒 tools/list - FULL OAUTH REQUIRED")

            # Extract and validate OAuth token
            auth_header = request.headers.get("Authorization")
            token_data = await validate_bearer_token(auth_header)

            logger.info(f"   ✅ OAuth validated: {token_data.get('sub', 'unknown')}")

            # Get tools
            tools = get_mcp_tools()

            return JSONResponse(
                status_code=200,
                content={
                    "jsonrpc": "2.0",
                    "result": {
                        "tools": tools
                    },
                    "id": request_id
                }
            )

        # Method: tools/call - FULL OAUTH VALIDATION REQUIRED
        elif method == "tools/call":
            tool_name = params.get("name")
            tool_args = params.get("arguments", {})

            logger.info(f"   🔒 tools/call - FULL OAUTH REQUIRED (tool: {tool_name})")

            # Extract and validate OAuth token
            auth_header = request.headers.get("Authorization")
            token_data = await validate_bearer_token(auth_header)

            logger.info(f"   ✅ OAuth validated: {token_data.get('sub', 'unknown')}")

            # Call tool
            result_content = await call_mcp_tool(tool_name, tool_args)

            return JSONResponse(
                status_code=200,
                content={
                    "jsonrpc": "2.0",
                    "result": {
                        "content": result_content
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
                    "error": {
                        "code": -32601,
                        "message": f"Method not found: {method}"
                    },
                    "id": request_id
                }
            )

    except HTTPException as e:
        logger.error(f"   ❌ HTTP Exception: {e.detail}")
        return JSONResponse(
            status_code=200,
            content={
                "jsonrpc": "2.0",
                "error": {
                    "code": e.status_code,
                    "message": e.detail
                },
                "id": request_id if 'request_id' in locals() else None
            }
        )

    except Exception as e:
        logger.error(f"   ❌ Unexpected error: {e}", exc_info=True)
        return JSONResponse(
            status_code=200,
            content={
                "jsonrpc": "2.0",
                "error": {
                    "code": -32603,
                    "message": f"Internal error: {str(e)}"
                },
                "id": body.get("id") if 'body' in locals() else None
            }
        )


# Reject GET requests at root
@app.get("/")
async def reject_get():
    """
    Return 405 Method Not Allowed for GET requests

    Article: "Return 405 Method Not Allowed with Allow: POST header?
    Claude interprets: 'POST-only server by design, continue with POST.'"
    """
    logger.info("GET / - Returning 405 Method Not Allowed")

    return Response(
        status_code=405,
        headers={
            "Allow": "POST, HEAD, OPTIONS",
            "MCP-Protocol-Version": "2025-06-18"
        },
        content=json.dumps({
            "error": "Method Not Allowed",
            "message": "This MCP server only accepts POST requests. Use POST for JSON-RPC messages."
        })
    )


# Health check endpoint (not part of MCP protocol)
@app.get("/health")
async def health():
    """Health check endpoint for deployment monitoring"""
    return {
        "status": "healthy",
        "server": config.mcp_server_name,
        "version": config.mcp_server_version,
        "protocol": "2025-06-18",
        "auth0_configured": bool(config.auth0_domain)
    }
