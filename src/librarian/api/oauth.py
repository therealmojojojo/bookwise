"""
OAuth 2.0 Implementation for Claude.ai Integration
Simple OAuth provider that allows Claude.ai custom connectors to authenticate
"""
from fastapi import APIRouter, HTTPException, status, Form, Request
from fastapi.responses import RedirectResponse, JSONResponse
from pydantic import BaseModel
from typing import Optional
import secrets
import hashlib
import time
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# Initialize persistent OAuth storage
from src.librarian.oauth_store import OAuthStore

_oauth_store = OAuthStore()

# Load persisted data from disk
oauth_tokens = _oauth_store.load_tokens()
authorization_codes = _oauth_store.load_auth_codes()
registered_clients = _oauth_store.load_clients()

# Pre-register default clients if none exist
if not registered_clients:
    registered_clients = {
    # Pre-register the bookwise client (used by Claude.ai)
    "bookwise": {
        "client_id": "bookwise",
        "client_secret": None,  # Will use BOOKWISE_API_KEY
        "redirect_uris": [
            "https://claude.ai/api/mcp/auth_callback",
            "https://claude.ai/callback",
            "https://example.com/callback"
        ],
        "grant_types": ["authorization_code"],
        "response_types": ["code"],
        "scope": "library:read library:write"
    },
    # Pre-register the bookwise-client for backward compatibility
    "bookwise-client": {
        "client_id": "bookwise-client",
        "client_secret": None,  # Will use BOOKWISE_API_KEY
        "redirect_uris": [
            "https://claude.ai/api/mcp/auth_callback",
            "https://claude.ai/callback",
            "https://example.com/callback"
        ],
        "grant_types": ["authorization_code"],
        "response_types": ["code"],
        "scope": "library:read library:write"
    }
}
    # Save default clients to disk
    _oauth_store.save_clients(registered_clients)

router = APIRouter(tags=["OAuth"])


class TokenResponse(BaseModel):
    """OAuth token response"""
    access_token: str
    token_type: str = "Bearer"
    expires_in: int = 3600  # 1 hour
    scope: Optional[str] = "library:read library:write"


class UserInfoResponse(BaseModel):
    """OAuth user info response"""
    sub: str  # Subject (user ID)
    name: str
    email: Optional[str] = None


def generate_token() -> str:
    """Generate a secure random token"""
    return secrets.token_urlsafe(32)


def hash_password(password: str) -> str:
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()


def verify_client(client_id: str, client_secret: Optional[str] = None) -> bool:
    """
    Verify OAuth client credentials
    For simplicity, we're using the API key as the client
    """
    from src.librarian.config import settings
    
    # Client ID should match a known identifier
    # Client secret should match the API key
    if client_secret:
        return client_secret == settings.BOOKWISE_API_KEY
    return True  # For auth code flow, we check later


@router.post("/register")
async def register_client(request: Request):
    """
    RFC 7591 OAuth 2.0 Dynamic Client Registration
    
    Allows Claude.ai to register itself as a client dynamically
    """
    try:
        data = await request.json()
        
        # Generate client credentials
        client_id = f"claude-{secrets.token_urlsafe(16)}"
        client_secret = secrets.token_urlsafe(32)
        
        # Store client registration
        registered_clients[client_id] = {
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uris": data.get("redirect_uris", []),
            "grant_types": data.get("grant_types", ["authorization_code"]),
            "response_types": data.get("response_types", ["code"]),
            "scope": data.get("scope", "library:read library:write"),
            "client_name": data.get("client_name", "Claude.ai"),
            "created_at": time.time()
        }
        
        logger.info(f"✅ Registered new client: {client_id} ({data.get('client_name', 'unknown')})")

        # Persist to disk
        _oauth_store.save_clients(registered_clients)

        # Return client registration response
        return {
            "client_id": client_id,
            "client_secret": client_secret,
            "client_secret_expires_at": 0,  # Never expires
            "redirect_uris": registered_clients[client_id]["redirect_uris"],
            "grant_types": registered_clients[client_id]["grant_types"],
            "response_types": registered_clients[client_id]["response_types"],
            "client_name": registered_clients[client_id].get("client_name", "Claude.ai"),
            "token_endpoint_auth_method": "client_secret_post"
        }
        
    except Exception as e:
        logger.error(f"Client registration failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Registration failed: {str(e)}"
        )


@router.api_route("/authorize", methods=["GET", "HEAD"])
async def authorize(
    request: Request,
    response_type: str = None,
    client_id: str = None,
    redirect_uri: str = None,
    scope: Optional[str] = None,
    state: Optional[str] = None,
    code_challenge: Optional[str] = None,
    code_challenge_method: Optional[str] = None
):
    """
    OAuth authorization endpoint with PKCE support

    Supports both standard OAuth and PKCE (Proof Key for Code Exchange)
    for enhanced security. Claude.ai uses PKCE by default.

    For personal use, we auto-approve the authorization.
    """
    # Handle HEAD requests
    if request.method == "HEAD":
        from fastapi.responses import Response
        return Response(status_code=200)

    logger.info(f"OAuth authorize request: client_id={client_id}, redirect_uri={redirect_uri}, PKCE={code_challenge is not None}")

    if response_type != "code":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only 'code' response_type is supported"
        )
    
    # Validate PKCE if present
    if code_challenge and code_challenge_method not in ["S256", "plain", None]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported code_challenge_method: {code_challenge_method}"
        )
    
    # Show login/authorization form (auth code will be generated after successful login)
    from fastapi.responses import HTMLResponse
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>BookWise - Authorize Claude.ai</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            * {{ box-sizing: border-box; margin: 0; padding: 0; }}
            body {{
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
                padding: 20px;
            }}
            .container {{
                background: white;
                border-radius: 16px;
                box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                padding: 40px;
                max-width: 420px;
                width: 100%;
            }}
            .icon {{ font-size: 56px; text-align: center; margin-bottom: 20px; }}
            h1 {{ font-size: 28px; color: #1a202c; margin-bottom: 8px; text-align: center; }}
            .subtitle {{ color: #718096; text-align: center; margin-bottom: 28px; font-size: 14px; }}
            .info-box {{
                background: #f7fafc;
                border-left: 4px solid #667eea;
                padding: 14px;
                border-radius: 8px;
                margin-bottom: 20px;
            }}
            .info-box p {{ color: #4a5568; font-size: 13px; line-height: 1.5; margin: 3px 0; }}
            .info-box strong {{ color: #2d3748; }}
            .form-group {{ margin-bottom: 18px; }}
            label {{ display: block; font-weight: 600; color: #2d3748; margin-bottom: 6px; font-size: 14px; }}
            input[type="text"], input[type="password"] {{
                width: 100%;
                padding: 12px 14px;
                border: 2px solid #e2e8f0;
                border-radius: 8px;
                font-size: 14px;
                transition: all 0.2s;
            }}
            input:focus {{
                outline: none;
                border-color: #667eea;
                box-shadow: 0 0 0 3px rgba(102,126,234,0.1);
            }}
            button {{
                width: 100%;
                padding: 14px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 15px;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.2s;
            }}
            button:hover {{ transform: translateY(-2px); box-shadow: 0 10px 20px rgba(0,0,0,0.15); }}
            .hint {{
                margin-top: 16px;
                padding: 12px;
                background: #edf2f7;
                border-radius: 6px;
                color: #4a5568;
                font-size: 12px;
                line-height: 1.5;
            }}
            code {{ background: #e2e8f0; padding: 2px 6px; border-radius: 4px; font-size: 11px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="icon">📚</div>
            <h1>BookWise Login</h1>
            <p class="subtitle">Authorize access to your library</p>
            
            <div class="info-box">
                <p><strong>Client:</strong> {client_id}</p>
                <p><strong>Permissions:</strong> Read & Write Library Access</p>
            </div>
            
            <form method="POST" action="/authorize_submit">
                <input type="hidden" name="client_id" value="{client_id}">
                <input type="hidden" name="redirect_uri" value="{redirect_uri}">
                <input type="hidden" name="response_type" value="{response_type}">
                <input type="hidden" name="scope" value="{scope or ''}">
                <input type="hidden" name="state" value="{state or ''}">
                <input type="hidden" name="code_challenge" value="{code_challenge or ''}">
                <input type="hidden" name="code_challenge_method" value="{code_challenge_method or ''}">
                
                <div class="form-group">
                    <label for="username">Username</label>
                    <input type="text" id="username" name="username" required autofocus placeholder="bookwise">
                </div>
                
                <div class="form-group">
                    <label for="password">Password</label>
                    <input type="password" id="password" name="password" required placeholder="Your API Key">
                </div>
                
                <button type="submit">🔐 Authorize & Continue</button>
                
                <div class="hint">
                    <strong>💡 Your Credentials:</strong><br>
                    Username: <code>bookwise</code><br>
                    Password: <code>BOOKWISE_API_KEY</code> from .env file
                </div>
            </form>
        </div>
    </body>
    </html>
    """
    
    return HTMLResponse(content=html_content)


@router.post("/authorize_submit")
async def authorize_submit(
    username: str = Form(...),
    password: str = Form(...),
    client_id: str = Form(...),
    redirect_uri: str = Form(...),
    response_type: str = Form(...),
    scope: str = Form(...),
    code_challenge: Optional[str] = Form(None),
    code_challenge_method: Optional[str] = Form(None),
    state: Optional[str] = Form(None)
):
    """
    Handle login form submission and authorize the client
    """
    from ..config import settings
    
    # Validate credentials
    logger.info(f"🔍 Login attempt - username: {username}, client_id: {client_id}")
    logger.info(f"🔍 Form data types: username={type(username)}, password={type(password)}, scope={type(scope)}, code_challenge={type(code_challenge)}")
    
    if username != "bookwise" or password != settings.BOOKWISE_API_KEY:
        from fastapi.responses import HTMLResponse
        logger.warning(f"❌ Login failed - invalid credentials for user: {username}")
        
        # Get the original authorize URL to redirect back to
        authorize_params = f"response_type={response_type}&client_id={client_id}&redirect_uri={redirect_uri}&scope={scope}"
        if code_challenge:
            authorize_params += f"&code_challenge={code_challenge}&code_challenge_method={code_challenge_method}"
        if state:
            authorize_params += f"&state={state}"
        authorize_url = f"/authorize?{authorize_params}"
        
        return HTMLResponse(content=f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Login Failed</title>
                <meta http-equiv="refresh" content="3;url={authorize_url}">
                <style>
                    body {{ font-family: sans-serif; display: flex; align-items: center; justify-content: center; min-height: 100vh; margin: 0; background: #f7fafc; }}
                    .error {{ background: white; padding: 40px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); text-align: center; max-width: 400px; }}
                    h1 {{ color: #e53e3e; margin-bottom: 16px; }}
                    p {{ color: #718096; margin: 8px 0; }}
                    .hint {{ margin-top: 16px; font-size: 13px; background: #fff5f5; padding: 12px; border-radius: 6px; color: #c53030; }}
                </style>
            </head>
            <body>
                <div class="error">
                    <h1>❌ Invalid Credentials</h1>
                    <p>Username or password incorrect.</p>
                    <div class="hint">
                        <strong>Expected:</strong><br>
                        Username: bookwise<br>
                        Password: BOOKWISE_API_KEY
                    </div>
                    <p style="margin-top: 16px; font-size: 12px;">Redirecting back to login...</p>
                </div>
            </body>
            </html>
        """, status_code=401)
    
    # User authenticated successfully - generate authorization code
    import secrets
    logger.info("🔍 Generating auth code...")
    auth_code = secrets.token_urlsafe(32)
    logger.info(f"🔍 Auth code generated: {auth_code[:10]}...")
    
    # Store authorization code with PKCE challenge
    logger.info(f"🔍 Storing auth code with scope={scope}, challenge={code_challenge}")
    try:
        authorization_codes[auth_code] = {
            "client_id": str(client_id),
            "redirect_uri": str(redirect_uri),
            "scope": str(scope),
            "code_challenge": str(code_challenge) if code_challenge else None,
            "code_challenge_method": str(code_challenge_method) if code_challenge_method else None,
            "expires_at": time.time() + 600,  # 10 minutes
            "used": False
        }
        logger.info("🔍 Auth code stored successfully")

        # Persist to disk
        _oauth_store.save_auth_codes(authorization_codes)
    except Exception as e:
        logger.error(f"❌ Error storing auth code: {e}")
        raise
    
    # Build callback URL
    callback_url = f"{redirect_uri}?code={auth_code}"
    if state:
        callback_url += f"&state={state}"
    
    logger.info(f"✅ User authenticated, authorizing client: {client_id}, redirecting to: {callback_url}")
    
    # HTTP 302 redirect - browser will convert POST to GET automatically
    logger.info("🔍 Creating redirect response...")
    return RedirectResponse(url=callback_url, status_code=302)


@router.post("/token", response_model=TokenResponse)
async def token(
    grant_type: str = Form(...),
    code: Optional[str] = Form(None),
    redirect_uri: Optional[str] = Form(None),
    client_id: Optional[str] = Form(None),
    client_secret: Optional[str] = Form(None),
    refresh_token: Optional[str] = Form(None),
    code_verifier: Optional[str] = Form(None)
):
    """
    OAuth token endpoint with PKCE support
    
    Exchanges authorization code for access token.
    Supports PKCE code verifier validation.
    """
    logger.info(f"OAuth token request: grant_type={grant_type}, client_id={client_id}, PKCE={code_verifier is not None}")
    
    if grant_type == "authorization_code":
        if not code or not redirect_uri:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing code or redirect_uri"
            )
        
        # Verify authorization code
        auth_data = authorization_codes.get(code)
        if not auth_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid authorization code"
            )
        
        # Check if code is expired
        if time.time() > auth_data["expires_at"]:
            del authorization_codes[code]
            _oauth_store.save_auth_codes(authorization_codes)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Authorization code expired"
            )
        
        # Check if code was already used
        if auth_data["used"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Authorization code already used"
            )
        
        # Verify redirect_uri matches
        if auth_data["redirect_uri"] != redirect_uri:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Redirect URI mismatch"
            )
        
        # Verify PKCE if code challenge was used
        if auth_data.get("code_challenge"):
            if not code_verifier:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="code_verifier required for PKCE"
                )
            
            # Verify code challenge
            challenge_method = auth_data.get("code_challenge_method", "plain")
            if challenge_method == "S256":
                # SHA256 hash of verifier
                import base64
                verifier_hash = hashlib.sha256(code_verifier.encode()).digest()
                computed_challenge = base64.urlsafe_b64encode(verifier_hash).decode().rstrip("=")
            else:
                # Plain method
                computed_challenge = code_verifier
            
            if computed_challenge != auth_data["code_challenge"]:
                logger.warning("PKCE code challenge verification failed")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid code_verifier"
                )
            
            logger.info("PKCE code challenge verified successfully")
        else:
            # No PKCE, verify client secret
            if client_secret and not verify_client(client_id, client_secret):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid client credentials"
                )
        
        # Mark code as used
        auth_data["used"] = True

        # Persist updated authorization codes
        _oauth_store.save_auth_codes(authorization_codes)

        # Generate access token
        access_token = generate_token()
        
        # Store access token (expires in 1 hour)
        oauth_tokens[access_token] = {
            "client_id": client_id or auth_data["client_id"],
            "scope": auth_data["scope"],
            "expires_at": time.time() + 3600,  # 1 hour
            "user_id": "bookwise-user"  # For personal use, single user
        }

        # Persist tokens to disk
        _oauth_store.save_tokens(oauth_tokens)

        logger.info(f"Access token generated for client_id={client_id}")
        
        return TokenResponse(
            access_token=access_token,
            token_type="Bearer",
            expires_in=3600,
            scope=auth_data["scope"]
        )
    
    elif grant_type == "refresh_token":
        # Refresh token support (optional)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Refresh tokens not yet implemented"
        )
    
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported grant_type: {grant_type}"
        )


@router.get("/userinfo", response_model=UserInfoResponse)
async def userinfo(request: Request):
    """
    OAuth user info endpoint
    
    Returns information about the authenticated user
    Required by some OAuth clients including Claude.ai
    """
    # Extract bearer token from Authorization header
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    access_token = auth_header.split(" ")[1]
    
    # Verify token
    token_data = oauth_tokens.get(access_token)
    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid access token",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    # Check if token is expired
    if time.time() > token_data["expires_at"]:
        del oauth_tokens[access_token]
        _oauth_store.save_tokens(oauth_tokens)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Access token expired",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    return UserInfoResponse(
        sub=token_data["user_id"],
        name="BookWise User",
        email=None  # Optional
    )


@router.get("/.well-known/openid-configuration")
async def openid_configuration(request: Request):
    """
    OpenID Connect discovery endpoint
    
    Provides metadata about the OAuth/OIDC configuration
    Helps Claude.ai auto-discover endpoints
    """
    base_url = f"{request.url.scheme}://{request.url.netloc}"
    
    return {
        "issuer": base_url,
        "authorization_endpoint": f"{base_url}/authorize",
        "token_endpoint": f"{base_url}/token",
        "userinfo_endpoint": f"{base_url}/userinfo",
        "response_types_supported": ["code"],
        "grant_types_supported": ["authorization_code"],
        "subject_types_supported": ["public"],
        "id_token_signing_alg_values_supported": ["RS256"],
        "scopes_supported": ["library:read", "library:write", "openid", "profile"],
        "token_endpoint_auth_methods_supported": ["client_secret_post", "client_secret_basic"],
        "claims_supported": ["sub", "name", "email"],
        "service_documentation": f"{base_url}/docs",
        "api_documentation": f"{base_url}/openapi.json"
    }


@router.get("/.well-known/oauth-authorization-server")
async def oauth_authorization_server(request: Request):
    """
    RFC 8414 OAuth 2.0 Authorization Server Metadata
    
    Claude.ai looks for this endpoint to discover OAuth configuration
    """
    base_url = f"{request.url.scheme}://{request.url.netloc}"
    
    return {
        "issuer": base_url,
        "authorization_endpoint": f"{base_url}/authorize",
        "token_endpoint": f"{base_url}/token",
        "userinfo_endpoint": f"{base_url}/userinfo",
        "jwks_uri": f"{base_url}/.well-known/jwks.json",
        "registration_endpoint": f"{base_url}/register",
        "scopes_supported": ["library:read", "library:write", "openid", "profile"],
        "response_types_supported": ["code"],
        "response_modes_supported": ["query", "fragment"],
        "grant_types_supported": ["authorization_code", "refresh_token"],
        "token_endpoint_auth_methods_supported": ["client_secret_post", "client_secret_basic"],
        "token_endpoint_auth_signing_alg_values_supported": ["RS256"],
        "service_documentation": f"{base_url}/docs",
        "ui_locales_supported": ["en-US"],
        "op_policy_uri": f"{base_url}/",
        "op_tos_uri": f"{base_url}/",
        "revocation_endpoint": f"{base_url}/revoke",
        "revocation_endpoint_auth_methods_supported": ["client_secret_post", "client_secret_basic"],
        "introspection_endpoint": f"{base_url}/introspect",
        "introspection_endpoint_auth_methods_supported": ["client_secret_post", "client_secret_basic"],
        "code_challenge_methods_supported": ["S256", "plain"],
        # MCP endpoint information for Claude.ai discovery
        "mcp_endpoint": f"{base_url}/mcp/sse",
        "mcp_protocol_version": "2025-06-18"
    }


@router.api_route("/.well-known/oauth-authorization-server/mcp/sse", methods=["GET", "HEAD"])
async def oauth_server_mcp_redirect(request: Request):
    """
    Redirect for Claude.ai's incorrect MCP discovery path

    Claude may look for MCP endpoint at authorization server path + /mcp/sse
    Redirect to the actual MCP endpoint
    """
    base_url = f"{request.url.scheme}://{request.url.netloc}"
    return RedirectResponse(
        url=f"{base_url}/mcp/sse",
        status_code=307  # Temporary redirect, preserves method and body
    )


@router.api_route("/.well-known/oauth-protected-resource/mcp/sse", methods=["GET", "HEAD"])
async def oauth_protected_resource_mcp_redirect(request: Request):
    """
    Redirect for Claude.ai's MCP discovery via protected resource path

    Claude.ai also checks the protected resource metadata path for MCP endpoint
    Redirect to the actual MCP endpoint
    """
    base_url = f"{request.url.scheme}://{request.url.netloc}"
    return RedirectResponse(
        url=f"{base_url}/mcp/sse",
        status_code=307  # Temporary redirect, preserves method and body
    )


@router.get("/.well-known/oauth-protected-resource")
async def oauth_protected_resource(request: Request):
    """
    RFC 8414 OAuth 2.0 Protected Resource Metadata

    Tells Claude.ai about the protected API resources available
    """
    base_url = f"{request.url.scheme}://{request.url.netloc}"

    # Include most recent token for Claude.ai to find (debugging workaround)
    latest_token = None
    if oauth_tokens:
        latest_token = max(oauth_tokens.items(), key=lambda x: x[1].get('expires_at', 0))[0]

    response = {
        "resource": base_url,
        "authorization_servers": [base_url],
        "scopes_supported": ["library:read", "library:write"],
        "bearer_methods_supported": ["header", "query"],
        "resource_signing_alg_values_supported": ["RS256"],
        "resource_documentation": f"{base_url}/docs",
        "resource_api_documentation": f"{base_url}/openapi.json",
        "resource_endpoints": {
            "search": f"{base_url}/api/v1/search_library",
            "book_details": f"{base_url}/api/v1/get_book_details",
            "stats": f"{base_url}/api/v1/stats",
            "export": f"{base_url}/api/v1/send_book_to_ereader",
            "mcp": f"{base_url}/mcp/sse"
        },
        "mcp_endpoint": f"{base_url}/mcp/sse",
        "mcp_protocol_version": "2025-06-18"
    }

    # Add token for Claude.ai debugging (TEMPORARY)
    if latest_token:
        response["access_token"] = latest_token
        response["mcp_endpoint_with_token"] = f"{base_url}/mcp/sse?access_token={latest_token}"

    return response


def verify_oauth_token(token: str) -> Optional[dict]:
    """
    Verify OAuth access token

    Args:
        token: Bearer access token

    Returns:
        Token data if valid, None otherwise
    """
    from datetime import datetime
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    logger.info(f"[{timestamp}] 🔑 Verifying token: {token[:20]}... (have {len(oauth_tokens)} tokens in memory)")

    token_data = oauth_tokens.get(token)
    if not token_data:
        logger.warning(f"[{timestamp}] ❌ Token not found in memory")
        return None
    
    # Check if expired
    if time.time() > token_data["expires_at"]:
        del oauth_tokens[token]
        _oauth_store.save_tokens(oauth_tokens)
        return None
    
    return token_data


# Cleanup task (should be run periodically)
async def cleanup_expired_tokens():
    """Remove expired tokens and authorization codes"""
    current_time = time.time()
    
    # Clean up expired tokens
    expired_tokens = [
        token for token, data in oauth_tokens.items()
        if current_time > data["expires_at"]
    ]
    for token in expired_tokens:
        del oauth_tokens[token]
    
    # Clean up expired authorization codes
    expired_codes = [
        code for code, data in authorization_codes.items()
        if current_time > data["expires_at"]
    ]
    for code in expired_codes:
        del authorization_codes[code]
    
    if expired_tokens or expired_codes:
        logger.info(f"Cleaned up {len(expired_tokens)} expired tokens and {len(expired_codes)} expired codes")

        # Persist cleanup to disk
        if expired_tokens:
            _oauth_store.save_tokens(oauth_tokens)
        if expired_codes:
            _oauth_store.save_auth_codes(authorization_codes)

