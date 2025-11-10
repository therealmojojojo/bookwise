"""
Simple OAuth 2.0 implementation for MCP Server
With NEVER-EXPIRING tokens for personal use
"""
import secrets
import hashlib
import time
import logging
from typing import Optional
from fastapi import Form, Request, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse, RedirectResponse

logger = logging.getLogger(__name__)

# OAuth storage (will be injected)
oauth_tokens = {}
authorization_codes = {}
registered_clients = {}
_oauth_store = None

# API key for login (will be set from env)
API_KEY = None


def initialize_oauth(store, api_key: str):
    """Initialize OAuth storage and API key"""
    global _oauth_store, oauth_tokens, authorization_codes, registered_clients, API_KEY

    _oauth_store = store
    API_KEY = api_key

    # Load persisted data
    oauth_tokens = _oauth_store.load_tokens()
    authorization_codes = _oauth_store.load_auth_codes()
    registered_clients = _oauth_store.load_clients()

    logger.info(f"OAuth initialized - {len(oauth_tokens)} tokens, {len(registered_clients)} clients")


def generate_token() -> str:
    """Generate a secure random token"""
    return secrets.token_urlsafe(32)


async def oauth_discovery(request: Request):
    """OAuth Protected Resource Metadata"""
    logger.info("OAuth discovery - returning resource metadata")
    base_url = f"{request.url.scheme}://{request.url.netloc}"

    return {
        "resource": f"{base_url}/",
        "authorization_servers": [f"{base_url}/"],
        "bearer_methods_supported": ["header"],
        "scopes_supported": ["mcp:read", "mcp:execute"]
    }


async def oauth_auth_server(request: Request):
    """OAuth Authorization Server Metadata"""
    logger.info("OAuth auth server metadata")
    base_url = f"{request.url.scheme}://{request.url.netloc}"

    return {
        "issuer": f"{base_url}/",
        "authorization_endpoint": f"{base_url}/authorize",
        "token_endpoint": f"{base_url}/token",
        "registration_endpoint": f"{base_url}/register",
        "token_endpoint_auth_methods_supported": ["none", "client_secret_post"],
        "grant_types_supported": ["authorization_code", "client_credentials"],
        "response_types_supported": ["code"],
        "scopes_supported": ["mcp:read", "mcp:execute"],
        "code_challenge_methods_supported": ["S256", "plain"]
    }


async def dynamic_client_registration(request: Request):
    """Dynamic Client Registration - Auto-approve all clients"""
    body = await request.json()
    logger.info(f"📝 DCR request - auto-approving client: {body.get('client_name', 'Unknown')}")

    client_id = f"bookwise-{secrets.token_urlsafe(16)}"
    client_secret = secrets.token_urlsafe(32)

    # Store client registration
    registered_clients[client_id] = {
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uris": body.get("redirect_uris", []),
        "grant_types": body.get("grant_types", ["authorization_code"]),
        "response_types": body.get("response_types", ["code"]),
        "scope": body.get("scope", "mcp:read mcp:execute"),
        "client_name": body.get("client_name", "Claude.ai"),
        "created_at": time.time()
    }

    # Persist to disk
    _oauth_store.save_clients(registered_clients)

    return JSONResponse({
        "client_id": client_id,
        "client_secret": client_secret,
        "client_secret_expires_at": 0,  # Never expires
        "redirect_uris": registered_clients[client_id]["redirect_uris"],
        "grant_types": registered_clients[client_id]["grant_types"],
        "response_types": registered_clients[client_id]["response_types"],
        "client_name": registered_clients[client_id].get("client_name", "Claude.ai"),
        "token_endpoint_auth_method": "client_secret_post"
    })


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
    """OAuth authorization endpoint - Show login form"""
    # Handle HEAD requests
    if request.method == "HEAD":
        from fastapi.responses import Response
        return Response(status_code=200)

    logger.info(f"OAuth authorize request: client_id={client_id}, PKCE={code_challenge is not None}")

    if response_type != "code":
        raise HTTPException(status_code=400, detail="Only 'code' response_type is supported")

    # Show login form
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>BookWise - Authorize</title>
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
            .form-group {{ margin-bottom: 18px; }}
            label {{ display: block; font-weight: 600; color: #2d3748; margin-bottom: 6px; font-size: 14px; }}
            input[type="password"] {{
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
        </style>
    </head>
    <body>
        <div class="container">
            <div class="icon">📚</div>
            <h1>BookWise Login</h1>
            <p class="subtitle">Authorize Claude.ai access</p>

            <form method="POST" action="/authorize_submit">
                <input type="hidden" name="client_id" value="{client_id}">
                <input type="hidden" name="redirect_uri" value="{redirect_uri}">
                <input type="hidden" name="response_type" value="{response_type}">
                <input type="hidden" name="scope" value="{scope or ''}">
                <input type="hidden" name="state" value="{state or ''}">
                <input type="hidden" name="code_challenge" value="{code_challenge or ''}">
                <input type="hidden" name="code_challenge_method" value="{code_challenge_method or ''}">

                <div class="form-group">
                    <label for="api_key">API Key</label>
                    <input type="password" id="api_key" name="api_key" required autofocus placeholder="Your BOOKWISE_API_KEY" value="{API_KEY}">
                </div>

                <button type="submit">🔐 Authorize & Continue</button>

                <div class="hint">
                    <strong>💡 Login Once:</strong><br>
                    Tokens never expire - you'll stay logged in forever!
                </div>
            </form>
        </div>
    </body>
    </html>
    """

    return HTMLResponse(content=html_content)


async def authorize_submit(
    api_key: str = Form(...),
    client_id: str = Form(...),
    redirect_uri: str = Form(...),
    response_type: str = Form(...),
    scope: str = Form(...),
    code_challenge: Optional[str] = Form(None),
    code_challenge_method: Optional[str] = Form(None),
    state: Optional[str] = Form(None)
):
    """Handle login form submission"""
    logger.info(f"🔍 Login attempt - client_id: {client_id}")

    # Validate API key
    if api_key != API_KEY:
        logger.warning(f"❌ Login failed - invalid API key")
        return HTMLResponse(content="""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Login Failed</title>
                <meta http-equiv="refresh" content="3;url=/authorize">
                <style>
                    body {{ font-family: sans-serif; display: flex; align-items: center; justify-content: center; min-height: 100vh; margin: 0; background: #f7fafc; }}
                    .error {{ background: white; padding: 40px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); text-align: center; }}
                    h1 {{ color: #e53e3e; }}
                </style>
            </head>
            <body>
                <div class="error">
                    <h1>❌ Invalid API Key</h1>
                    <p>Redirecting back to login...</p>
                </div>
            </body>
            </html>
        """, status_code=401)

    # Generate authorization code
    auth_code = secrets.token_urlsafe(32)

    # Store authorization code with PKCE challenge
    authorization_codes[auth_code] = {
        "client_id": str(client_id),
        "redirect_uri": str(redirect_uri),
        "scope": str(scope),
        "code_challenge": str(code_challenge) if code_challenge else None,
        "code_challenge_method": str(code_challenge_method) if code_challenge_method else None,
        "expires_at": time.time() + 600,  # 10 minutes
        "used": False
    }

    # Persist to disk
    _oauth_store.save_auth_codes(authorization_codes)

    # Build callback URL
    callback_url = f"{redirect_uri}?code={auth_code}"
    if state:
        callback_url += f"&state={state}"

    logger.info(f"✅ User authenticated, redirecting to: {callback_url}")

    return RedirectResponse(url=callback_url, status_code=302)


async def token_exchange(request: Request):
    """OAuth token endpoint with PKCE support - Returns NEVER-EXPIRING tokens"""
    form_data = await request.form()
    grant_type = form_data.get("grant_type")
    code = form_data.get("code")
    redirect_uri = form_data.get("redirect_uri")
    client_id = form_data.get("client_id")
    code_verifier = form_data.get("code_verifier")

    logger.info(f"OAuth token request: grant_type={grant_type}, client_id={client_id}, PKCE={code_verifier is not None}")

    if grant_type != "authorization_code":
        raise HTTPException(status_code=400, detail=f"Unsupported grant_type: {grant_type}")

    if not code or not redirect_uri:
        raise HTTPException(status_code=400, detail="Missing code or redirect_uri")

    # Verify authorization code
    auth_data = authorization_codes.get(code)
    if not auth_data:
        raise HTTPException(status_code=400, detail="Invalid authorization code")

    # Check if code is expired
    if time.time() > auth_data["expires_at"]:
        del authorization_codes[code]
        _oauth_store.save_auth_codes(authorization_codes)
        raise HTTPException(status_code=400, detail="Authorization code expired")

    # Check if code was already used
    if auth_data["used"]:
        raise HTTPException(status_code=400, detail="Authorization code already used")

    # Verify redirect_uri matches
    if auth_data["redirect_uri"] != redirect_uri:
        raise HTTPException(status_code=400, detail="Redirect URI mismatch")

    # Verify PKCE if code challenge was used
    if auth_data.get("code_challenge"):
        if not code_verifier:
            raise HTTPException(status_code=400, detail="code_verifier required for PKCE")

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
            raise HTTPException(status_code=400, detail="Invalid code_verifier")

        logger.info("✅ PKCE code challenge verified successfully")

    # Mark code as used
    auth_data["used"] = True
    _oauth_store.save_auth_codes(authorization_codes)

    # Generate access token - NEVER EXPIRES!
    access_token = generate_token()

    # Store access token (NEVER EXPIRES)
    oauth_tokens[access_token] = {
        "client_id": client_id or auth_data["client_id"],
        "scope": auth_data["scope"],
        "expires_at": None,  # NEVER EXPIRES!
        "user_id": "bookwise-user"
    }

    # Persist tokens to disk
    _oauth_store.save_tokens(oauth_tokens)

    logger.info(f"✅ Access token generated for client_id={client_id} - NEVER EXPIRES")

    return JSONResponse({
        "access_token": access_token,
        "token_type": "Bearer",
        "expires_in": 999999999,  # Effectively infinite
        "scope": auth_data["scope"]
    })


def verify_oauth_token(token: str) -> Optional[dict]:
    """Verify OAuth access token - No expiration check"""
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
    logger.info(f"[{timestamp}] 🔑 Verifying token: {token[:20]}... (have {len(oauth_tokens)} tokens in memory)")

    token_data = oauth_tokens.get(token)
    if not token_data:
        logger.warning(f"[{timestamp}] ❌ Token not found in memory")
        return None

    # No expiration check - tokens never expire!
    logger.info(f"[{timestamp}] ✅ Token valid (never expires)")
    return token_data
