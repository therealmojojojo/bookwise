# BookWise Librarian API

MCP-compatible REST API for intelligent book recommendations from your Calibre library.

## Data Architecture

### Database-First Principle

**The Librarian API follows a strict database-first architecture:**

✅ **DO**: Use live databases for all book information
- **CalibreDB** (`metadata.db`) - Primary source for book metadata, authors, tags, formats
- **ChromaDB** (`book_vectors/`) - Source for quality scores, AI-generated tags/themes/descriptions, embeddings

❌ **DON'T**: Use CSV or JSON files for retrieving book information
- CSV/JSON files are only for **data import** during enrichment
- The API should never read from `output/*.csv` or `datasources/*.json`

### Why Database-First?

1. **Single Source of Truth**: Databases contain the enriched, up-to-date data
2. **Performance**: Direct database queries are faster than parsing CSV files
3. **Consistency**: All services query the same live data
4. **Scalability**: Databases handle concurrent access better

### Data Flow

```
Enrichment Pipeline (one-time):
datasources/*.json → generate_unified_scores.py → enrich_books.py → ChromaDB + CalibreDB

Librarian API (runtime):
User Query → API Endpoint → ChromaDB + CalibreDB → JSON Response
             (no CSV/JSON files)
```

### Service Data Sources

| Service | Primary Data Source | Purpose |
|---------|-------------------|---------|
| **VectorSearchService** | ChromaDB | Semantic search, quality scores, AI metadata |
| **CalibreService** | CalibreDB (SQLite) | Book metadata, authors, tags, formats |
| **DeliveryService** | `calibredb` CLI | Book export to e-reader |

---

## Quick Start

### 1. Install
```bash
cd /path/to/bookwise
pip install -r src/librarian/requirements.txt
```

### 2. Configure `.env`
```bash
# Required
CALIBRE_DB_PATH=/path/to/calibre/metadata.db
CHROMADB_PATH=/path/to/bookwise/book_vectors
EREADER_EXPORT_FOLDER=/path/to/export/folder
CALIBREDB_PATH=/Applications/calibre.app/Contents/MacOS/calibredb
OPENAI_API_KEY=sk-your-key

# Optional
CALIBRE_LIBRARY_PATH=/path/to/calibre
BOOKWISE_API_KEY=your-api-key
HOST=0.0.0.0
PORT=8000  # Default port, change as needed
```

### 3. Deploy

**Production (macOS service)**:
```bash
cd src/librarian/deployment
./service-start.sh  # Auto-start on boot, auto-restart on crash
./service-stop.sh   # Stop service
```

**Development**:
```bash
./dev-start.sh  # Manual run with auto-reload
```

**Test**:
```bash
./test-api.sh
```

Server: `http://localhost:{PORT}`  
Docs: `http://localhost:{PORT}/docs`

### 4. Export Folder Setup

Choose cloud storage or local folder:
- **Google Drive**: `~/Library/CloudStorage/GoogleDrive-.../Books`
- **iCloud**: `~/Library/Mobile Documents/com~apple~CloudDocs/Books`
- **Dropbox**: `~/Dropbox/Ebooks`
- **Local**: Any writable directory

## API Endpoints

### `POST /api/v1/search_library`
Multi-query semantic search with quality filtering.

```bash
curl -X POST http://localhost:{PORT}/api/v1/search_library \
  -H "Content-Type: application/json" \
  -d '{"queries": ["resilience", "economic hardship"], "filters": {"min_quality": 70}, "limit": 10}'
```

**Parameters**: `queries` (list[str]), `filters.min_quality` (int, 0-100), `limit` (int, 1-30)

### `POST /api/v1/get_book_details`
Get complete metadata for specific books.

```bash
curl -X POST http://localhost:{PORT}/api/v1/get_book_details \
  -H "Content-Type: application/json" \
  -d '{"book_ids": [1834, 17306]}'
```

**Parameters**: `book_ids` (list[int], 1-20)

### `POST /api/v1/get_top_quality_books`
Browse highest-rated books by genre.

```bash
curl -X POST http://localhost:{PORT}/api/v1/get_top_quality_books \
  -H "Content-Type: application/json" \
  -d '{"genre": "fiction", "min_quality": 85, "limit": 20}'
```

**Parameters**: `genre` (str, optional), `min_quality` (int, 70-100), `limit` (int, 1-50)

### `POST /api/v1/send_book_to_ereader`
Export book to shared folder.

```bash
curl -X POST http://localhost:{PORT}/api/v1/send_book_to_ereader \
  -H "Content-Type: application/json" \
  -d '{"book_id": 1834, "format": "epub"}'
```

**Parameters**: `book_id` (int), `format` (epub|mobi|azw3|pdf), `device_name` (str, optional)

## Claude.ai Integration

### Tool Definitions
```python
tools = [
    {
        "name": "search_library",
        "description": "Multi-query semantic search with quality filtering",
        "input_schema": {
            "type": "object",
            "properties": {
                "queries": {"type": "array", "items": {"type": "string"}},
                "filters": {"type": "object", "properties": {"min_quality": {"type": "integer"}}},
                "limit": {"type": "integer", "default": 15}
            },
            "required": ["queries"]
        }
    },
    {
        "name": "get_book_details",
        "description": "Get complete metadata by book ID",
        "input_schema": {
            "type": "object",
            "properties": {"book_ids": {"type": "array", "items": {"type": "integer"}}},
            "required": ["book_ids"]
        }
    },
    {
        "name": "get_top_quality_books",
        "description": "Browse highest-rated books by genre",
        "input_schema": {
            "type": "object",
            "properties": {
                "genre": {"type": "string"},
                "min_quality": {"type": "integer", "default": 85},
                "limit": {"type": "integer", "default": 20}
            }
        }
    },
    {
        "name": "send_book_to_ereader",
        "description": "Export book to e-reader folder",
        "input_schema": {
            "type": "object",
            "properties": {
                "book_id": {"type": "integer"},
                "format": {"type": "string", "enum": ["epub", "mobi", "azw3", "pdf"]},
                "device_name": {"type": "string"}
            },
            "required": ["book_id"]
        }
    }
]
```

### System Prompt
```
You are an expert librarian with access to the user's Calibre library.

Books are pre-scored 0-100:
- 85-100: Nobel, Booker, Pulitzer winners
- 70-85: Major nominees, national awards
- Below 70: Good books

Generate 2-5 varied semantic queries for serendipitous discovery.
Explain why each book matches. Offer to send books to e-reader.
```

## Security & Authentication

### MCP (Model Context Protocol) Security Considerations

The BookWise Librarian API follows **MCP security best practices** for integration with Claude.ai:

#### Current Implementation

**Authentication Method**: API Key (X-API-Key header)
- ✅ Simple and secure for local/private network deployments
- ✅ Compatible with MCP remote server specification
- ✅ No dependency on complex OAuth flows for personal use

**Current Security Features**:
```python
# In .env file
BOOKWISE_API_KEY=your-secure-api-key-here  # Optional, enables authentication
PORT={YOUR_PORT}                           # Non-standard port (e.g., {PORT})
HOST=0.0.0.0                               # Listen on all interfaces
```

#### Deployment Scenarios

**Scenario 1: Local Development (Current Setup)**
```bash
# .env configuration
BOOKWISE_API_KEY=          # Empty = dev mode (no auth)
HOST=0.0.0.0
PORT={YOUR_PORT}           # e.g., {PORT}
```

✅ **Pros**: Fast iteration, no authentication overhead  
⚠️ **Risks**: Anyone on local network can access  
📋 **Use when**: Developing locally, no sensitive data exposure

**Scenario 2: Private Network (Recommended for Personal Use)**
```bash
# .env configuration
BOOKWISE_API_KEY=randomly-generated-secure-key-here
HOST=0.0.0.0
PORT={YOUR_PORT}           # e.g., {PORT}
```

✅ **Pros**: Simple authentication, works with MCP  
✅ **Security**: API key prevents unauthorized access  
📋 **Use when**: Running on home network, accessing from Claude Desktop

**Scenario 3: Remote/Internet Access (Maximum Security)**
```bash
# .env configuration
BOOKWISE_API_KEY=strong-random-api-key
HOST=127.0.0.1              # Localhost only
PORT={YOUR_PORT}            # e.g., {PORT}

# Use Tailscale or ngrok for secure tunneling
```

✅ **Pros**: Encrypted tunnel, no public exposure  
✅ **Security**: Private VPN + API key  
📋 **Use when**: Accessing from remote locations

#### MCP Security Best Practices (Per Official Documentation)

**1. Authentication**
- [x] **API Key Authentication**: Implemented via `X-API-Key` header
- [ ] **OAuth 2.1**: Not implemented (optional for future enhancement)
- [x] **Token Storage**: Stored in `.env` (environment variables)
- [ ] **Token Rotation**: Manual (implement automated rotation for production)

**2. Communication Security**
- [ ] **HTTPS**: Not implemented (use reverse proxy for HTTPS)
- [x] **CORS**: Configured to allow Claude.ai domain
- [x] **Rate Limiting**: Basic protection via service design

**3. Access Control**
- [x] **Principle of Least Privilege**: API only reads from databases
- [x] **Read-Only Database Access**: CalibreDB opened in read-only mode
- [x] **No Write Operations**: Delivery uses `calibredb export` (safe)
- [x] **Resource Isolation**: ChromaDB and CalibreDB separate

**4. Monitoring & Auditing**
- [x] **Logging**: All requests logged to `~/Library/Logs/bookwise-librarian.log`
- [x] **Error Logging**: Separate error log for debugging
- [ ] **Audit Trail**: Basic logging (enhance with request metadata for production)

**5. Data Privacy**
- [x] **Local Execution**: All processing on local machine
- [x] **No External API Calls**: Except OpenAI for embeddings (query time only)
- [x] **Data Isolation**: Personal library data stays on device

#### Security Enhancements for Production

If exposing to the internet or untrusted networks:

**1. Add HTTPS with Reverse Proxy**
```nginx
# nginx configuration
server {
    listen 443 ssl;
    server_name bookwise.yourdomain.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    location / {
        proxy_pass http://127.0.0.1:{PORT};
        proxy_set_header X-API-Key $http_x_api_key;
    }
}
```

**2. Implement Rate Limiting**
```python
# Add to server.py
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@router.post("/search_library")
@limiter.limit("10/minute")  # 10 requests per minute
async def search_library(...):
    ...
```

**3. Add IP Whitelisting**
```python
# Add to dependencies.py
ALLOWED_IPS = ["127.0.0.1", "192.168.1.0/24"]  # Your home network

async def verify_ip(request: Request):
    client_ip = request.client.host
    if client_ip not in ALLOWED_IPS:
        raise HTTPException(403, "IP not allowed")
```

**4. Implement Token Rotation**
```bash
# Rotate API key monthly
NEW_API_KEY=$(openssl rand -hex 32)
sed -i '' "s/BOOKWISE_API_KEY=.*/BOOKWISE_API_KEY=$NEW_API_KEY/" .env
launchctl kickstart -k gui/$(id -u)/com.bookwise.librarian
```

#### Connecting to Claude.ai

**Method 1: Claude Desktop (Local)**
If BookWise is on same machine as Claude Desktop, use localhost:
```
http://localhost:{PORT}/api/v1/...
```

**Method 2: Tailscale (Private Network)**
```bash
# Install Tailscale
brew install tailscale
sudo tailscale up

# Access via Tailscale IP (replace {PORT} with your configured port)
http://100.x.x.x:{PORT}/api/v1/...
```

**Method 3: ngrok (Temporary Testing)**
```bash
# Replace {PORT} with your configured port
ngrok http {PORT}
# Use generated HTTPS URL: https://abc123.ngrok.io
```

#### Security Checklist

**Before Production Deployment:**
- [ ] Generate strong random API key (`openssl rand -hex 32`)
- [ ] Configure `BOOKWISE_API_KEY` in `.env`
- [ ] Enable HTTPS (reverse proxy or Tailscale)
- [ ] Set `HOST=127.0.0.1` (localhost only) if using tunnel
- [ ] Implement rate limiting
- [ ] Set up automated log rotation
- [ ] Configure IP whitelisting (if applicable)
- [ ] Test authentication with Claude.ai
- [ ] Document API key sharing with authorized users

**For Personal Use (Recommended Minimum):**
- [x] Service runs on non-standard port
- [ ] Generate and set `BOOKWISE_API_KEY`
- [x] Service auto-restarts on crash
- [x] Logs are written to dedicated files
- [ ] Rotate API key quarterly

---

## Service Management

```bash
# Status
launchctl list | grep bookwise
curl http://localhost:{PORT}/health

# Logs
tail -f ~/Library/Logs/bookwise-librarian.log
tail -f ~/Library/Logs/bookwise-librarian-error.log

# Restart
launchctl kickstart -k gui/$(id -u)/com.bookwise.librarian

# Uninstall
./service-stop.sh
rm ~/Library/LaunchAgents/com.bookwise.librarian.plist
```

## Remote Access

**ngrok** (testing):
```bash
./service-start.sh
ngrok http {PORT}
```

**Tailscale** (private network):
```bash
brew install tailscale
sudo tailscale up
```

## Troubleshooting

```bash
# Service won't start
tail -50 ~/Library/Logs/bookwise-librarian-error.log
./service-stop.sh && ./service-start.sh

# Check configuration
cat /path/to/bookwise/.env

# Test manually
cd src/librarian/deployment
./dev-start.sh
```

**Common Issues**:
- ChromaDB path must contain `chroma.sqlite3`
- Export folder must be writable
- OpenAI API key required for semantic search
- Calibredb path must point to executable

## Architecture

```
src/librarian/
├── server.py              # FastAPI app
├── config.py              # Settings
├── requirements.txt
├── deployment/
│   ├── service-start.sh   # Production
│   ├── service-stop.sh
│   ├── dev-start.sh       # Development
│   └── test-api.sh
├── api/
│   ├── routes.py          # Endpoints
│   ├── models.py          # Schemas
│   └── dependencies.py
├── services/
│   ├── vector_search.py   # ChromaDB
│   ├── calibre_db.py      # SQLite
│   └── delivery_service.py
└── middleware/
    └── auth.py
```
