"""
MCP Test Server

A reference implementation following "The Missing MCP Playbook" by George Vetticaden.

Key Features:
- OAuth 2.1 with Auth0 integration
- Dynamic Client Registration (DCR) support
- MCP Protocol 2025-06-18 compliance
- Root path endpoint (/)
- Selective authentication pattern
- Comprehensive logging for debugging

This implementation demonstrates the correct architecture for deploying
custom MCP servers that successfully connect to Claude.ai and Claude Mobile.
"""

__version__ = "1.0.0"
