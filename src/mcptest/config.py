"""
Configuration for MCP Test Server
Following the pattern from "The Missing MCP Playbook"
"""
import os
from typing import Optional
from pydantic_settings import BaseSettings


class Config(BaseSettings):
    """
    Configuration for MCP server with Auth0 integration

    Required environment variables:
    - AUTH0_DOMAIN: Your Auth0 tenant domain (e.g., 'your-tenant.us.auth0.com')
    - AUTH0_AUDIENCE: API identifier in Auth0 (typically your MCP server URL)
    - MCP_SERVER_URL: Public URL where this server is deployed

    Optional:
    - AUTH0_CLIENT_ID: Pre-configured client ID (optional, DCR creates dynamically)
    - AUTH0_CLIENT_SECRET: Pre-configured client secret (optional)
    """

    # Auth0 Configuration
    auth0_domain: str = os.getenv("AUTH0_DOMAIN", "dev-example.us.auth0.com")
    auth0_audience: str = os.getenv("AUTH0_AUDIENCE", "https://bookwise.mjjj.space")
    auth0_client_id: Optional[str] = os.getenv("AUTH0_CLIENT_ID")
    auth0_client_secret: Optional[str] = os.getenv("AUTH0_CLIENT_SECRET")

    # MCP Server Configuration
    mcp_server_url: str = os.getenv("MCP_SERVER_URL", "https://bookwise.mjjj.space")
    mcp_server_name: str = "BookWise MCP Test"
    mcp_server_version: str = "1.0.0"

    # Scopes for MCP operations
    scopes_read: str = "bookwise:read"
    scopes_execute: str = "bookwise:execute"

    # Server settings
    port: int = int(os.getenv("PORT", "8766"))  # Using same port as main server
    host: str = "0.0.0.0"
    log_level: str = os.getenv("LOG_LEVEL", "INFO")

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # Ignore extra fields from main .env file


# Global config instance
config = Config()
