# MCP Test Server

A reference implementation following **"The Missing MCP Playbook"** by George Vetticaden.

This demonstrates the **correct architecture** for deploying custom MCP servers that successfully integrate with **Claude.ai Web** and **Claude Mobile**.

## 🎯 What This Solves

Most MCP tutorials show local servers with stdio transport. This implementation shows:

✅ **OAuth 2.1 with Auth0** - Secure authentication for remote servers
✅ **Dynamic Client Registration (DCR)** - Claude.ai auto-registers as OAuth client
✅ **MCP Protocol 2025-06-18** - Latest spec with Streamable HTTP
✅ **Root Path Endpoint** - `/` (not `/mcp` or `/sse`)
✅ **Selective Authentication** - Different auth requirements per MCP method
✅ **Comprehensive Logging** - Debug OAuth + MCP handshake sequences

## 🏗️ Architecture Overview

```
Claude.ai/Mobile → OAuth Discovery → Auth0 (DCR) → User Login → JWT Token → MCP Server
```

### Four-Step Handshake

1. **OAuth Discovery** - Claude queries `/.well-known/oauth-protected-resource`
2. **Dynamic Client Registration** - Claude POSTs to Auth0 `/oidc/register`
3. **User Authentication** - Auth0 login → JWT token issued
4. **MCP Protocol Handshake** - `HEAD /` → `initialize` → `tools/list` → `tools/call`

### Selective Authentication Pattern

| MCP Method | Auth Required | Why |
|-----------|--------------|-----|
| `initialize` | ❌ NO | Clients discover capabilities before authenticating |
| `notifications/initialized` | ⚠️ Session ID only | Session validation during handshake |
| `tools/list` | ✅ FULL OAuth | Security: Prevent unauthorized tool discovery |
| `tools/call` | ✅ FULL OAuth | Security: Enforce authorization for operations |

## 📋 Prerequisites

1. **Auth0 Account** (free tier works)
2. **Python 3.10+**
3. **Public URL** (Cloudflare Tunnel, ngrok, or Cloud Run)

## 🚀 Setup Instructions

### Step 1: Create Auth0 API

1. **Go to Auth0 Dashboard** → APIs → Create API

2. **Configure API:**
   - Name: `BookWise MCP Test`
   - Identifier: `https://your-server.example.com` (your public URL)
   - Signing Algorithm: RS256

3. **Enable Dynamic Client Registration:**
   - Settings → Advanced Settings → OAuth
   - Enable: "Allow Dynamic Client Registration"
   - Save changes

4. **Add Scopes:**
   - Settings → Permissions
   - Add scopes:
     - `bookwise:read` - "Read access to BookWise library"
     - `bookwise:execute` - "Execute BookWise tools"

5. **Configure Token Settings:**
   - Settings → Token Settings
   - Token Expiration: 24 hours (86400 seconds)
   - Enable: "Add Permissions in the Access Token"

### Step 2: Create Auth0 Application (for testing)

While Claude.ai will register dynamically, create an app for testing:

1. **Applications** → Create Application
2. **Type:** Single Page Application
3. **Name:** "BookWise MCP Test"
4. **Settings:**
   - Allowed Callback URLs: `https://your-server.example.com/callback`
   - Allowed Logout URLs: `https://your-server.example.com`
   - Allowed Web Origins: `https://your-server.example.com`
5. **Advanced Settings** → Grant Types:
   - ✅ Authorization Code
   - ✅ Refresh Token
6. **Save Changes**

### Step 3: Create Auth0 User

1. **User Management** → Users → Create User
2. **Email:** your-test@email.com
3. **Password:** (set secure password)
4. **Connection:** Username-Password-Authentication

### Step 4: Configure Environment Variables

Create `.env` file in project root:

```bash
# Auth0 Configuration
AUTH0_DOMAIN=your-tenant.us.auth0.com
AUTH0_AUDIENCE=https://your-server.example.com
AUTH0_CLIENT_ID=your_client_id_here (optional, for testing)
AUTH0_CLIENT_SECRET=your_client_secret_here (optional, for testing)

# MCP Server Configuration
MCP_SERVER_URL=https://your-server.example.com
PORT=8767
LOG_LEVEL=INFO
```

### Step 5: Install Dependencies

```bash
cd /path/to/bookwise

# Install Python dependencies
pip3 install fastapi uvicorn python-jose[cryptography] httpx pydantic-settings
```

### Step 6: Run the Server

```bash
# Development (local testing)
uvicorn src.mcptest.server:app --host 0.0.0.0 --port 8767 --reload

# Production (with log file)
uvicorn src.mcptest.server:app --host 0.0.0.0 --port 8767 > ~/Library/Logs/mcp-test.log 2>&1 &
```

### Step 7: Verify Endpoints

```bash
# Test OAuth discovery
curl https://your-server.example.com/.well-known/oauth-protected-resource | jq

# Expected response:
{
  "resource": "https://your-server.example.com",
  "authorization_servers": ["https://your-tenant.us.auth0.com"],
  "bearer_methods_supported": ["header"],
  "scopes_supported": ["bookwise:read", "bookwise:execute"]
}

# Test HEAD endpoint
curl -I https://your-server.example.com/ | grep MCP-Protocol-Version

# Expected: MCP-Protocol-Version: 2025-06-18

# Test initialize (no auth)
curl -X POST https://your-server.example.com/ \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "initialize",
    "params": {},
    "id": 1
  }' | jq

# Expected:
{
  "jsonrpc": "2.0",
  "result": {
    "protocolVersion": "2025-06-18",
    "serverInfo": {
      "name": "BookWise MCP Test",
      "version": "1.0.0"
    },
    "capabilities": {
      "tools": {}
    }
  },
  "id": 1
}
```

## 🔗 Adding to Claude.ai

### Step 1: Add Custom Connector

1. Go to **Claude.ai** → **Settings** → **Connectors**
2. Click **"Add custom connector"**
3. Enter URL: `https://your-server.example.com`
4. Click **"Connect"**

### Step 2: OAuth Flow

1. Claude.ai will redirect to Auth0 login
2. Login with your Auth0 test user credentials
3. Authorize the application
4. Claude.ai should show **"Connected"** with green indicator

### Step 3: Test Tools

In Claude.ai chat:
```
Can you call the hello_world tool with my name?
```

Claude should execute the tool and return the greeting.

## 📱 Adding to Claude Mobile

Same process as Claude.ai:

1. Open Claude Mobile app
2. Settings → Connectors → Add custom connector
3. Enter URL: `https://your-server.example.com`
4. Complete OAuth flow
5. Test tools via voice or text

## 🐛 Debugging

### Enable Comprehensive Logging

```bash
# Watch logs in real-time
tail -f ~/Library/Logs/mcp-test.log

# Filter for OAuth events
tail -f ~/Library/Logs/mcp-test.log | grep -E "OAuth|DCR|token"

# Filter for MCP protocol events
tail -f ~/Library/Logs/mcp-test.log | grep -E "MCP|initialize|tools"
```

### Common Issues

#### 1. "Disconnected" Status in Claude.ai

**Symptoms:** Connector shows gray/disconnected status

**Debug steps:**
```bash
# Check OAuth discovery
curl https://your-server.example.com/.well-known/oauth-protected-resource

# Check HEAD response
curl -I https://your-server.example.com/

# Check server logs for errors
tail -50 ~/Library/Logs/mcp-test.log
```

**Common causes:**
- Auth0 domain mismatch in `.env`
- DCR not enabled in Auth0 API
- Wrong MCP server URL in metadata
- Missing HEAD endpoint support

#### 2. OAuth "Invalid Token" Errors

**Symptoms:** 401 Unauthorized on tools/list or tools/call

**Debug:**
```bash
# Check logs for JWT validation errors
tail -f ~/Library/Logs/mcp-test.log | grep -E "JWT|JWE|token"
```

**Common causes:**
- Auth0 audience mismatch
- JWKS fetch failure
- Token format (JWT vs JWE) not handled
- Token expired (check expiration settings)

#### 3. MCP Protocol Errors

**Symptoms:** Tools not appearing in Claude.ai

**Debug:**
```bash
# Test tools/list with valid token
# (Get token from Auth0 test application first)

curl -X POST https://your-server.example.com/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/list",
    "params": {},
    "id": 2
  }' | jq
```

**Common causes:**
- Endpoint not at root path `/`
- Missing selective authentication
- Wrong MCP protocol version
- Tools schema format incorrect

## 📚 Key Insights from the Article

### 1. Protocol Compliance as Semantic Signaling

> "MCP clients interpret HTTP status codes as semantic signals, not just errors."

- 501 Not Implemented → "Server broken, terminate"
- 405 Method Not Allowed → "POST-only by design, continue"

### 2. Dual-Format Token Validation

> "Auth0 issues TWO formats... Your validation must handle both."

- JWT tokens (with `kid` field → JWKS validation)
- JWE tokens (encrypted → /userinfo fallback)

This implementation handles both automatically in `oauth_utils.py`.

### 3. Selective Authentication Pattern

> "The MCP spec is precise about what gets authenticated when."

Not all methods need OAuth:
- Discovery methods (initialize) = NO auth
- Session methods (notifications) = ID only
- Operation methods (tools/*) = FULL auth

### 4. Root Path Requirement

> "root path / endpoint (not /sse or custom paths—Claude assumes root)"

Don't use `/mcp/sse` or `/mcp`. Claude.ai expects MCP at `/`.

## 🔄 Differences from BookWise Main Server

| Feature | Main Server (`/mcp/sse`) | Test Server (`/`) |
|---------|-------------------------|-------------------|
| **Endpoint Path** | `/mcp/sse` | `/` (root) |
| **OAuth** | Custom implementation | Auth0 with DCR |
| **Authentication** | Removed temporarily | Selective pattern |
| **Token Validation** | Basic Bearer | JWT + JWE support |
| **Session Management** | Partial | Full Mcp-Session-Id |
| **Protocol Discovery** | HEAD supported | HEAD + OPTIONS |
| **DCR Support** | ❌ None | ✅ Full RFC 7591 |

## 🎓 Learning Resources

- **Original Article:** [The Missing MCP Playbook](https://medium.com/@george.vetticaden/the-missing-mcp-playbook-deploying-custom-agents-on-claude-ai-and-claude-mobile-part-2) by George Vetticaden
- **MCP Specification:** [Model Context Protocol Docs](https://modelcontextprotocol.io)
- **Auth0 DCR Guide:** [Dynamic Client Registration](https://auth0.com/docs/get-started/applications/dynamic-client-registration)
- **OAuth 2.1:** [RFC 9110](https://datatracker.ietf.org/doc/html/rfc9110)

## 📝 Next Steps

To adapt this for production BookWise deployment:

1. **Copy patterns to main server:**
   - Move MCP endpoint to root `/`
   - Add Auth0 integration
   - Implement selective authentication
   - Add comprehensive logging

2. **Update Cloudflare routing:**
   - Route `/` → MCP server
   - Keep `/api/v1/*` → REST API

3. **Test with Claude.ai:**
   - Add custom connector
   - Complete OAuth flow
   - Verify tools work
   - Test on mobile

4. **Monitor and debug:**
   - Watch logs for OAuth failures
   - Track MCP handshake sequences
   - Measure token validation performance

## 🙏 Credits

This implementation follows the architecture documented in:

**"The Missing MCP Playbook: Deploying Custom Agents on Claude.ai and Claude Mobile"**
By George Vetticaden
Published: November 2025

The article filled a critical gap in MCP documentation - how to actually deploy remote MCP servers that work with Claude.ai and Claude Mobile. This reference implementation demonstrates those patterns.

## 📄 License

Same as main BookWise project.
