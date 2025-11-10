"""
Dependency injection and authentication for API
"""
from fastapi import Security, HTTPException, status, Request
from fastapi.security import APIKeyHeader
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)

# API key header security scheme
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def verify_api_key(
    request: Request,
    api_key: Optional[str] = Security(api_key_header)
) -> Dict:
    """
    Verify API key or OAuth bearer token for authentication

    Supports both:
    - X-API-Key header (for direct API access)
    - Authorization: Bearer <token> header (for OAuth/Claude.ai)

    Args:
        request: FastAPI request object
        api_key: API key from X-API-Key header

    Returns:
        Dict with auth_type and optional auth_data

    Raises:
        HTTPException: If authentication fails
    """
    from ..config import settings

    # If no API key is configured, allow all requests (dev mode)
    if not settings.BOOKWISE_API_KEY:
        logger.warning("API key authentication disabled (dev mode)")
        return {"auth_type": "dev", "auth_data": {}}

    # Check for OAuth bearer token in multiple locations
    # (Cloudflare may strip tokens from Authorization header)
    auth_header = request.headers.get("Authorization")
    from datetime import datetime
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    logger.info(f"[{timestamp}] 🔍 Auth check for {request.url.path} - Authorization header present: {bool(auth_header)}")

    bearer_token = None

    # Try Authorization header first
    if auth_header and auth_header.startswith("Bearer "):
        parts = auth_header.split(" ", 1)  # Split only on first space
        if len(parts) > 1 and parts[1]:  # Check if token exists after "Bearer "
            bearer_token = parts[1]
            logger.info(f"[{timestamp}] 🔍 Bearer token found in Authorization header: {bearer_token[:20]}...")

    # If Authorization header is present but token is missing, check query params
    if not bearer_token and auth_header:
        logger.info(f"[{timestamp}] 🔍 Authorization header malformed ('{auth_header[:50]}'), checking alternatives...")

        # Check query parameters
        token_from_query = request.query_params.get("access_token") or request.query_params.get("token")
        if token_from_query:
            bearer_token = token_from_query
            logger.info(f"[{timestamp}] 🔍 Token found in query params: {bearer_token[:20]}...")

        # Check cookies
        if not bearer_token:
            token_from_cookie = request.cookies.get("access_token") or request.cookies.get("oauth_token")
            if token_from_cookie:
                bearer_token = token_from_cookie
                logger.info(f"[{timestamp}] 🔍 Token found in cookies: {bearer_token[:20]}...")

        # Check alternative headers (Cloudflare, X-Auth-Token, etc.)
        if not bearer_token:
            for header_name in ["CF-Access-Token", "X-Auth-Token", "X-Access-Token"]:
                token_from_header = request.headers.get(header_name)
                if token_from_header:
                    bearer_token = token_from_header
                    logger.info(f"[{timestamp}] 🔍 Token found in {header_name} header: {bearer_token[:20]}...")
                    break

    if bearer_token:
        from datetime import datetime
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # Verify OAuth token
        from .oauth import verify_oauth_token
        token_data = verify_oauth_token(bearer_token)

        if token_data:
            from datetime import datetime
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            logger.info(f"[{timestamp}] ✅ OAuth token verified for user: {token_data.get('user_id')}")
            # Store token data in request state for later use
            request.state.auth_type = "oauth"
            request.state.auth_data = token_data
            return {"auth_type": "oauth", "auth_data": token_data}
        else:
            from datetime import datetime
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            logger.warning(f"[{timestamp}] ❌ Invalid OAuth bearer token: {bearer_token[:20]}...")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired OAuth token",
                headers={"WWW-Authenticate": "Bearer"}
            )

    # Log all request details for debugging if we couldn't find a token
    if not bearer_token and auth_header:
        logger.warning(f"[{timestamp}] ❌ No valid token found. Auth header: '{auth_header[:50]}', Query params: {dict(request.query_params)}, Cookies: {list(request.cookies.keys())}, Headers: {dict(request.headers)}")

    # Fall back to API key authentication
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Include 'X-API-Key' header or 'Authorization: Bearer <token>' header."
        )

    if api_key != settings.BOOKWISE_API_KEY:
        logger.warning(f"Invalid API key attempted: {api_key[:10]}...")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API key"
        )

    logger.info("API key verified")
    request.state.auth_type = "api_key"
    return {"auth_type": "api_key", "auth_data": {}}


async def get_services(request: Request) -> Dict:
    """
    Dependency injection for services
    
    Args:
        request: FastAPI request object
        
    Returns:
        Dict of service instances
    """
    return {
        'vector': request.app.state.vector_service,
        'calibre': request.app.state.calibre_service,
        'delivery': request.app.state.delivery_service
    }

