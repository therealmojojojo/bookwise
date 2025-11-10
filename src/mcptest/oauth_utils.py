"""
OAuth 2.1 utilities for Auth0 integration
Handles JWT/JWE token validation and Dynamic Client Registration (DCR)
"""
import logging
import httpx
from typing import Optional, Dict, Any
from jose import jwt, JWTError
from fastapi import HTTPException, status

from .config import config

logger = logging.getLogger(__name__)


class Auth0Client:
    """
    Auth0 OAuth client with support for:
    - JWT token validation with JWKS
    - JWE token validation via /userinfo
    - Dynamic Client Registration (DCR)
    """

    def __init__(self):
        self.domain = config.auth0_domain
        self.audience = config.auth0_audience
        self.jwks_client = None
        self._jwks_cache: Optional[Dict] = None

    async def get_jwks(self) -> Dict:
        """Fetch JWKS (JSON Web Key Set) from Auth0"""
        if self._jwks_cache:
            return self._jwks_cache

        jwks_url = f"https://{self.domain}/.well-known/jwks.json"
        logger.info(f"Fetching JWKS from: {jwks_url}")

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(jwks_url, timeout=10.0)
                response.raise_for_status()
                self._jwks_cache = response.json()
                logger.info(f"JWKS fetched successfully: {len(self._jwks_cache.get('keys', []))} keys")
                return self._jwks_cache
        except Exception as e:
            logger.error(f"Failed to fetch JWKS: {e}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Failed to fetch JWKS from Auth0: {str(e)}"
            )

    async def validate_jwt_token(self, token: str) -> Dict[str, Any]:
        """
        Validate JWT token using JWKS

        This handles standard JWT tokens with 'kid' field.
        """
        try:
            # Get JWKS
            jwks = await self.get_jwks()

            # Decode header to get kid
            unverified_header = jwt.get_unverified_header(token)
            kid = unverified_header.get("kid")

            if not kid:
                logger.warning("Token missing 'kid' field - might be JWE format")
                return None

            # Find the key
            key = None
            for k in jwks.get("keys", []):
                if k.get("kid") == kid:
                    key = k
                    break

            if not key:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=f"Unable to find key with kid: {kid}"
                )

            # Validate token
            payload = jwt.decode(
                token,
                key,
                algorithms=["RS256"],
                audience=self.audience,
                issuer=f"https://{self.domain}/"
            )

            logger.info(f"✅ JWT token validated: {payload.get('sub', 'unknown')}")
            return payload

        except JWTError as e:
            logger.error(f"JWT validation error: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Token validation error: {e}")
            return None

    async def validate_via_userinfo(self, token: str) -> Dict[str, Any]:
        """
        Validate token via Auth0 /userinfo endpoint

        This handles JWE tokens (encrypted) that don't have 'kid' field.
        Fallback method when JWKS validation fails.
        """
        userinfo_url = f"https://{self.domain}/userinfo"
        logger.info("Validating token via /userinfo endpoint (JWE format)")

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    userinfo_url,
                    headers={"Authorization": f"Bearer {token}"},
                    timeout=10.0
                )

                if response.status_code == 401:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Invalid or expired token"
                    )

                response.raise_for_status()
                user_info = response.json()
                logger.info(f"✅ Token validated via /userinfo: {user_info.get('sub', 'unknown')}")
                return user_info

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Userinfo validation error: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Failed to validate token: {str(e)}"
            )

    async def validate_token(self, token: str) -> Dict[str, Any]:
        """
        Validate Auth0 token with dual-format support

        Tries JWT validation first (with kid field).
        Falls back to /userinfo validation for JWE tokens.

        This defensive pattern handles Auth0's two token formats:
        - JWT tokens (with kid field for JWKS validation)
        - JWE tokens (encrypted, no kid field)
        """
        # Try JWT validation first
        payload = await self.validate_jwt_token(token)
        if payload:
            return payload

        # Fallback to userinfo validation for JWE tokens
        logger.info("JWT validation failed, trying /userinfo endpoint")
        return await self.validate_via_userinfo(token)


# Global Auth0 client instance
auth0_client = Auth0Client()


async def validate_bearer_token(authorization: Optional[str]) -> Dict[str, Any]:
    """
    Extract and validate Bearer token from Authorization header

    Args:
        authorization: Authorization header value (e.g., "Bearer abc123...")

    Returns:
        Token payload with user claims and scopes

    Raises:
        HTTPException: If token is missing, malformed, or invalid
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header",
            headers={"WWW-Authenticate": "Bearer"}
        )

    parts = authorization.split(" ")
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Authorization header format. Expected: 'Bearer <token>'",
            headers={"WWW-Authenticate": "Bearer"}
        )

    token = parts[1]
    return await auth0_client.validate_token(token)
