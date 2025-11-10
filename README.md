# BookWise - Personal Library Intelligence System

**An intelligent book recommendation and discovery system powered by AI, combining quality scoring, semantic search, and natural language interaction.**

---

## Overview

BookWise is a comprehensive personal library management system that combines traditional bibliographic data with modern AI capabilities to enable intelligent book discovery and recommendations. The system provides multiple interaction methods, from command-line tools to natural language conversations with AI assistants.

### Key Capabilities

#### 1. **Quality-Based Book Discovery**
- Objective quality scoring based on literary awards, canonical lists, and expert curation
- Coverage of major international awards (Nobel, Pulitzer, Booker, etc.)
- Best-of lists from major publications and institutions
- Curated collections of significant authors and classic series

#### 2. **Semantic Search**
- AI-powered semantic understanding of book content
- Vector embeddings for conceptual similarity matching
- Multi-query search for nuanced topic exploration
- Quality-filtered results to surface excellent books

#### 3. **AI-Enhanced Metadata**
- Intelligent descriptions focusing on content rather than marketing
- Automatically generated themes and topic tags
- Historical context and publication information
- Award and recognition tracking with hierarchical importance

#### 4. **Natural Language Interaction**
- Conversational interface through Claude AI integration
- Intent interpretation for vague or exploratory queries
- Contextual recommendations based on implicit interests
- Follow-up questions to refine discovery

#### 5. **E-Reader Integration**
- Direct book delivery to reading devices
- Multiple format support (EPUB, MOBI, PDF, AZW3)
- Cloud-based file sharing for wireless transfer

#### 6. **Interactive Excel Workbook**
- Comprehensive library analysis in a single file
- Interactive dashboards with charts and statistics
- Curated shopping lists with top unowned books
- Filter and sort capabilities for easy book discovery
- Print-ready formats for offline use
- Calibre import sheets for metadata integration

---

## BookWise Librarian API

The BookWise Librarian provides an MCP (Model Context Protocol) server that enables AI assistants like Claude to interact naturally with your personal library.

### Conversational Capabilities

When integrated with Claude AI, you can:

**Explore by Interest:**
- "Find books about resilience and overcoming adversity"
- "I'm interested in the history of scientific discovery"
- "Show me novels dealing with social justice themes"

**Get Detailed Information:**
- Request comprehensive book details including quality scores, awards, themes, and descriptions
- View available formats and metadata
- Understand why a book is considered significant

**Discover Quality Literature:**
- Search filtered by quality threshold (Nobel Prize winners, Pulitzer winners, etc.)
- Explore award-winning books by theme or topic
- Find canonical works and critically acclaimed literature

**Send to E-Reader:**
- Export books directly to your reading device
- Choose preferred format
- Automatic delivery to configured location

### Technical Features

#### Authentication & Security
- OAuth 2.0 with PKCE support for secure access
- Configurable authentication (can run in development mode without auth)
- Session management for multi-turn conversations
- OpenID Connect discovery for easy client integration

#### Protocol Support
- MCP (Model Context Protocol) 2025-06-18
- Streamable HTTP transport
- JSON-RPC 2.0 message format
- CORS support for web-based clients

#### Search & Discovery
- Multi-query semantic search combining conceptual variations
- Quality threshold filtering (0-100 scale)
- Configurable result limits
- Relevance scoring with distance metrics
- AI-detected themes and topics

#### Library Management
- Read-only access to library metadata
- Real-time statistics (books, authors, tags)
- Book format detection and availability
- Award and recognition tracking
- Publication history and dates

---

## System Architecture

### Data Pipeline

**Quality Scoring Layer:**
- Analyzes 25+ major literary awards
- Evaluates 13 best-of lists from publications
- Incorporates educational canon selections
- Tracks 800+ significant authors
- Generates objective quality scores (0-100 scale)

**AI Enrichment Layer:**
- Claude AI for intelligent content analysis
- OpenAI embeddings (3072-dimensional vectors)
- Automatic theme and topic detection
- Publication year resolution with fallback sources
- Semantic search index in vector database

**API Integration Layer:**
- FastAPI server with async request handling
- OAuth authentication and authorization
- MCP protocol implementation for AI assistants
- RESTful endpoints for programmatic access

**Delivery Layer:**
- Library management integration
- Multi-format book export
- Cloud storage synchronization
- E-reader file transfer

---

## Use Cases

### Serendipitous Discovery
Find books you wouldn't think to search for by describing abstract interests or moods. The AI interprets your intent and bridges conceptual domains to surface relevant quality literature.

### Quality Filtering
Focus on excellent books by filtering search results based on objective quality scores derived from prestigious awards and expert curation.

### Research & Exploration
Investigate themes, topics, and concepts across your library using semantic search that understands meaning rather than just keywords.

### Reading List Management
Discover what award-winning or canonical books you already own, track your coverage of major literary prizes, and identify gaps in your collection.

### Convenient Reading
Send books directly to your e-reader with a simple conversational command, choosing the format that works best for your device.

---

## Getting Started

### Prerequisites
- Personal library managed in Calibre
- Python 3.10 or higher
- API keys for AI services (if using enrichment features)
- Cloud storage for e-reader delivery (optional)

### Configuration
Copy `.env.example` to `.env` and configure your environment:
- Library database location
- AI service API keys (for enrichment)
- E-reader export destination
- Server settings (port, host)
- Optional: Authentication credentials

### Running the System

**Quality Scoring:**
Generate objective quality scores for your library based on awards, lists, and curated authors.

**AI Enrichment:**
Enhance books with AI-generated themes, topics, descriptions, and semantic embeddings for intelligent search.

**Excel Workbook Generation:**
Create a comprehensive Excel workbook with interactive dashboards, shopping lists, and analysis sheets for easy library management and book discovery.

**API Server:**
Start the BookWise Librarian API to enable natural language interaction through Claude AI or other MCP-compatible clients.

---

## Integration with Claude AI

### Features Available Through Conversation

- **Search Your Library:** Describe what you're interested in using natural language
- **Get Book Details:** Ask for comprehensive information about any book
- **View Library Stats:** Check total books, authors, and content coverage
- **Export to E-Reader:** Request books be sent to your reading device
- **Quality Insights:** Understand why books are considered significant based on awards and recognition

### Interaction Examples

**Discovery:**
```
You: I'm looking for books about perseverance and human strength
Claude: [Searches library semantically and returns quality-filtered results with scores and context]
```

**Details:**
```
You: Tell me about book ID 1234
Claude: [Provides title, author, publication info, quality score, awards, themes, description, available formats]
```

**Statistics:**
```
You: What's in my library?
Claude: [Returns total books, authors, tags with counts]
```

**Export:**
```
You: Send book ID 5678 to my e-reader in EPUB format
Claude: [Exports book and confirms successful delivery]
```

---

## Excel Workbook - Comprehensive Library Analysis

BookWise can generate a single Excel workbook (`bookwise_library.xlsx`) that consolidates your entire library analysis into an easy-to-use, interactive format.

### What's Included

**📊 Dashboard Sheet**
- Interactive overview with key metrics and statistics
- Score distribution charts
- Quick navigation links to other sheets
- Auto-calculated library coverage percentage

**📚 All Books Sheet (Master Database)**
- Complete library with 4,400+ scored books
- Color-coded quality scores (green for 90+, yellow for 70-79)
- Filterable and sortable columns
- Frozen headers for easy scrolling
- Owned status tracking

**✅ Owned Books Sheet**
- Your personal collection sorted by quality score
- Shows your best books at the top
- Summary statistics (total count, average score)

**❌ Missing Books Sheet**
- High-quality books you don't own yet
- Sorted by score to prioritize acquisitions
- Priority markers (Must Buy, High, Medium, Low)
- Shows awards and recognition for each book

**🛒 Shopping List Sheet**
- Top 50 unowned books ready to acquire
- Ranked by quality score
- Auto-generated "Why Buy" reasons
- Top 10 highlighted in gold
- Print-ready format for bookstore visits

**📈 Statistics Sheet**
- Overall library metrics
- Score distribution breakdown
- Coverage analysis
- All formulas auto-calculated

**📥 Import Sheets (2 sheets)**
- Calibre-ready metadata import format
- Tag import for quick updates
- Instructions included in sheets

### Benefits

- **One File vs 13 CSVs**: Everything in a single, organized workbook
- **Interactive**: Filter, sort, and analyze without programming
- **Visual**: Color coding and formatting for quick insights
- **Shareable**: Easy to email or share with friends
- **Print-Ready**: Shopping list designed for printing
- **Auto-Updated**: Statistics recalculate as you mark books as owned

### Use Cases

**Book Shopping**
Open the Shopping List sheet to see the top 50 highest-quality books you don't own yet, complete with reasons why each book is significant.

**Collection Analysis**
Use the Statistics sheet to understand your library's quality distribution and identify gaps in coverage.

**Finding Books**
Filter the All Books sheet by author, score, or owned status to quickly locate specific books or categories.

**Calibre Integration**
Export the Import_Metadata sheet as CSV and use Calibre's import tools to add quality scores and tags to your library.

### File Details
- **Size**: ~300 KB (vs 8+ MB for multiple CSVs)
- **Compatibility**: Excel 2013+, LibreOffice Calc, Google Sheets, Numbers
- **Format**: .xlsx with multiple worksheets
- **Location**: `output/bookwise_library.xlsx`

For detailed usage instructions, see `EXCEL_FILE_GUIDE.md`.

---

## Documentation

- **Setup Guide:** See `.env.example` for configuration options
- **API Documentation:** Interactive docs available at `/docs` when server is running
- **Quality Methodology:** Detailed award hierarchy and scoring system
- **Enrichment Pipeline:** AI metadata generation and semantic indexing
- **Excel Workbook Guide:** See `EXCEL_FILE_GUIDE.md` for detailed usage instructions

---

## System Requirements

### Storage
- Calibre library with metadata database
- Vector database storage for embeddings
- Cloud storage for e-reader delivery (optional)

### Processing
- Python runtime environment
- Access to AI services (for enrichment)
- Network connectivity (for API access)

### Integration
- MCP-compatible AI assistant (e.g., Claude)
- OAuth-capable authentication flow (for production use)
- Web browser (for OAuth consent flow)

---

## Privacy & Security

- **Local Processing:** Library analysis runs on your machine
- **API Keys:** Stored in environment variables, never in code
- **OAuth Security:** Industry-standard authentication with PKCE
- **Read-Only Access:** Server only reads library data, never modifies
- **Optional Authentication:** Can run without auth for personal use

---

## License & Attribution

This project was developed using AI assistance (Claude Sonnet 4.5) in collaboration with human oversight. All code, documentation, and methodologies are the result of human-AI collaboration.

The quality scoring system is based on publicly available information about literary awards, best-of lists, and canonical literature collections. Award data is used for objective quality assessment in a personal library context.

---

**For questions, issues, or contributions, please refer to project documentation and contribution guidelines.**
