"""
Mock Auth0 Server for Testing

Simulates Auth0 OAuth 2.1 endpoints:
- Dynamic Client Registration (DCR)
- Token issuance (JWT format)
- JWKS endpoint for token validation
- /userinfo endpoint
"""
import logging
import secrets
import time
from datetime import datetime, timedelta
from typing import Dict, Optional
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import JSONResponse, HTMLResponse
import jwt

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Mock Auth0 Server")

# ============================================================================
# MOCK DATA STORES
# ============================================================================

# Registered clients (via DCR)
clients: Dict[str, Dict] = {}

# Authorization codes
auth_codes: Dict[str, Dict] = {}

# Access tokens
access_tokens: Dict[str, Dict] = {}

# Mock user database
users = {
    "test@bookwise.com": {
        "sub": "auth0|mock123456",
        "email": "test@bookwise.com",
        "email_verified": True,
        "name": "Test User"
    }
}

# ============================================================================
# JWT SIGNING (Simplified - uses HS256 for demo)
# ============================================================================

# In production, Auth0 uses RS256 with RSA keys
# For simplicity, we'll use HS256 (symmetric) for this mock
JWT_SECRET = "mock-auth0-secret-key-DO-NOT-USE-IN-PRODUCTION"
JWT_ALGORITHM = "HS256"

# Mock "kid" (key ID) for JWKS
MOCK_KID = "mock-key-1"

def create_jwt_token(user_sub: str, audience: str, scopes: list) -> str:
    """Create a JWT access token"""
    now = datetime.utcnow()

    payload = {
        "iss": "https://localhost:8768/",  # Mock Auth0 issuer
        "sub": user_sub,
        "aud": audience,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(hours=24)).timestamp()),
        "scope": " ".join(scopes),
        "azp": "mock-client-id"  # Authorized party
    }

    # For mock purposes, include kid in header
    token = jwt.encode(
        payload,
        JWT_SECRET,
        algorithm=JWT_ALGORITHM,
        headers={"kid": MOCK_KID}
    )

    return token


# ============================================================================
# OAUTH DISCOVERY ENDPOINTS
# ============================================================================

@app.get("/.well-known/openid-configuration")
async def openid_configuration():
    """OpenID Connect Discovery endpoint"""
    logger.info("📋 OpenID Configuration requested")

    return {
        "issuer": "https://localhost:8768/",
        "authorization_endpoint": "http://localhost:8768/authorize",
        "token_endpoint": "http://localhost:8768/oauth/token",
        "userinfo_endpoint": "http://localhost:8768/userinfo",
        "jwks_uri": "http://localhost:8768/.well-known/jwks.json",
        "registration_endpoint": "http://localhost:8768/oidc/register",
        "scopes_supported": ["openid", "profile", "email", "bookwise:read", "bookwise:execute"],
        "response_types_supported": ["code"],
        "grant_types_supported": ["authorization_code", "refresh_token"],
        "token_endpoint_auth_methods_supported": ["none", "client_secret_post"],
        "code_challenge_methods_supported": ["S256"]
    }


@app.get("/.well-known/jwks.json")
async def jwks():
    """
    JWKS (JSON Web Key Set) endpoint

    Provides public keys for JWT validation.
    In production Auth0, this would be RSA public keys.
    For our mock, we return a simplified version.
    """
    logger.info("🔑 JWKS requested")

    # Note: In production, this would be RSA public key
    # For HS256 (symmetric), we don't expose the secret
    # But we need to return a JWKS structure for compatibility
    return {
        "keys": [
            {
                "kty": "oct",  # Key type: octet (symmetric)
                "kid": MOCK_KID,
                "use": "sig",
                "alg": "HS256"
                # Note: We don't expose 'k' (the secret) in real JWKS
            }
        ]
    }


# ============================================================================
# DYNAMIC CLIENT REGISTRATION (DCR)
# ============================================================================

@app.post("/oidc/register")
async def dynamic_client_registration(request: Request):
    """
    Dynamic Client Registration (RFC 7591)

    Claude.ai calls this to register as an OAuth client.
    """
    body = await request.json()
    logger.info(f"📝 DCR request received")
    logger.info(f"   Client metadata: {body}")

    # Generate client credentials
    client_id = f"dcr-{secrets.token_urlsafe(16)}"
    client_secret = secrets.token_urlsafe(32)

    # Store client
    clients[client_id] = {
        "client_id": client_id,
        "client_secret": client_secret,
        "client_name": body.get("client_name", "Unknown Client"),
        "redirect_uris": body.get("redirect_uris", []),
        "grant_types": body.get("grant_types", ["authorization_code"]),
        "response_types": body.get("response_types", ["code"]),
        "scope": body.get("scope", "openid profile email"),
        "created_at": datetime.utcnow().isoformat()
    }

    logger.info(f"   ✅ Client registered: {client_id}")

    # Return client credentials
    return {
        "client_id": client_id,
        "client_secret": client_secret,
        "client_name": clients[client_id]["client_name"],
        "redirect_uris": clients[client_id]["redirect_uris"],
        "grant_types": clients[client_id]["grant_types"],
        "response_types": clients[client_id]["response_types"],
        "token_endpoint_auth_method": "none"  # Public client (mobile)
    }


# ============================================================================
# OAUTH AUTHORIZATION FLOW
# ============================================================================

@app.get("/authorize")
async def authorize(
    client_id: str,
    redirect_uri: str,
    response_type: str,
    scope: str,
    state: Optional[str] = None,
    code_challenge: Optional[str] = None,
    code_challenge_method: Optional[str] = None
):
    """
    OAuth authorization endpoint

    In production, this would show a login page.
    For our mock, we auto-approve with a test user.
    """
    logger.info(f"🔐 Authorization request")
    logger.info(f"   Client: {client_id}")
    logger.info(f"   Redirect: {redirect_uri}")
    logger.info(f"   Scope: {scope}")

    # Verify client exists
    if client_id not in clients:
        return HTMLResponse(
            content=f"<h1>Error</h1><p>Unknown client_id: {client_id}</p>",
            status_code=400
        )

    # Generate authorization code
    code = f"code-{secrets.token_urlsafe(32)}"

    # Store code with PKCE challenge
    auth_codes[code] = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "scope": scope,
        "user_sub": users["test@bookwise.com"]["sub"],
        "code_challenge": code_challenge,
        "code_challenge_method": code_challenge_method,
        "created_at": time.time()
    }

    logger.info(f"   ✅ Authorization code generated: {code[:20]}...")

    # Build redirect URL
    redirect_params = f"code={code}"
    if state:
        redirect_params += f"&state={state}"

    redirect_url = f"{redirect_uri}?{redirect_params}"

    # Auto-approve and redirect
    return HTMLResponse(
        content=f"""
        <html>
        <head><title>Mock Auth0 - Authorization</title></head>
        <body>
            <h1>✅ Authorization Successful</h1>
            <p>User: test@bookwise.com</p>
            <p>Scopes: {scope}</p>
            <p>Redirecting to: {redirect_uri}</p>
            <script>
                setTimeout(function() {{
                    window.location.href = "{redirect_url}";
                }}, 2000);
            </script>
            <p><a href="{redirect_url}">Click here if not redirected</a></p>
        </body>
        </html>
        """,
        status_code=200
    )


@app.post("/oauth/token")
async def token(request: Request):
    """
    OAuth token endpoint

    Exchanges authorization code for access token.
    """
    form_data = await request.form()
    logger.info(f"🎫 Token request")
    logger.info(f"   Grant type: {form_data.get('grant_type')}")

    grant_type = form_data.get("grant_type")

    if grant_type == "authorization_code":
        code = form_data.get("code")
        redirect_uri = form_data.get("redirect_uri")
        client_id = form_data.get("client_id")
        code_verifier = form_data.get("code_verifier")

        # Verify code exists
        if code not in auth_codes:
            logger.error(f"   ❌ Invalid authorization code")
            raise HTTPException(status_code=400, detail="Invalid authorization code")

        code_data = auth_codes[code]

        # Verify client
        if code_data["client_id"] != client_id:
            logger.error(f"   ❌ Client ID mismatch")
            raise HTTPException(status_code=400, detail="Client ID mismatch")

        # Verify redirect URI
        if code_data["redirect_uri"] != redirect_uri:
            logger.error(f"   ❌ Redirect URI mismatch")
            raise HTTPException(status_code=400, detail="Redirect URI mismatch")

        # TODO: Verify PKCE code_verifier if code_challenge was used
        # For simplicity, we'll skip PKCE verification in this mock

        # Generate access token
        scopes = code_data["scope"].split()
        access_token = create_jwt_token(
            user_sub=code_data["user_sub"],
            audience="https://your-server.example.com",
            scopes=scopes
        )

        # Store token
        access_tokens[access_token] = {
            "user_sub": code_data["user_sub"],
            "scope": code_data["scope"],
            "client_id": client_id,
            "created_at": time.time()
        }

        # Delete used code
        del auth_codes[code]

        logger.info(f"   ✅ Access token issued: {access_token[:20]}...")

        return {
            "access_token": access_token,
            "token_type": "Bearer",
            "expires_in": 86400,  # 24 hours
            "scope": code_data["scope"]
        }

    else:
        raise HTTPException(status_code=400, detail=f"Unsupported grant_type: {grant_type}")


@app.get("/userinfo")
async def userinfo(request: Request):
    """
    UserInfo endpoint (for JWE token validation fallback)
    """
    auth_header = request.headers.get("Authorization")

    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")

    token = auth_header.split(" ")[1]

    # Check if token exists in our store
    if token not in access_tokens:
        # Try to decode JWT (might be valid but not in store)
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM], audience="https://your-server.example.com")
            user_sub = payload.get("sub")
        except:
            raise HTTPException(status_code=401, detail="Invalid token")
    else:
        user_sub = access_tokens[token]["user_sub"]

    # Find user
    user = None
    for email, user_data in users.items():
        if user_data["sub"] == user_sub:
            user = user_data
            break

    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    logger.info(f"👤 UserInfo request for: {user['email']}")

    return user


# ============================================================================
# HELPER ENDPOINTS
# ============================================================================

@app.get("/")
async def root():
    """Mock Auth0 server info"""
    return {
        "name": "Mock Auth0 Server",
        "version": "1.0.0",
        "endpoints": {
            "discovery": "/.well-known/openid-configuration",
            "jwks": "/.well-known/jwks.json",
            "register": "/oidc/register",
            "authorize": "/authorize",
            "token": "/oauth/token",
            "userinfo": "/userinfo"
        },
        "test_user": {
            "email": "test@bookwise.com",
            "sub": "auth0|mock123456"
        },
        "registered_clients": len(clients),
        "active_tokens": len(access_tokens)
    }


@app.get("/health")
async def health():
    """Health check"""
    return {
        "status": "healthy",
        "clients": len(clients),
        "tokens": len(access_tokens)
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8768)
