"""
Remote MCP Server for BookWise
Implements Model Context Protocol for Claude.ai web, desktop, and mobile

This server exposes your 11,861-book library as MCP tools that Claude can use.
"""
import logging
from pathlib import Path
import sys
from typing import Any, List, Dict
from dataclasses import dataclass

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.librarian.config import settings
from src.librarian.services import (
    VectorSearchService,
    CalibreService,
    DeliveryService
)

logger = logging.getLogger(__name__)

# Define Tool and TextContent classes (replacing MCP SDK dependency)
@dataclass
class Tool:
    """MCP Tool definition"""
    name: str
    description: str
    inputSchema: dict

    def model_dump(self):
        return {
            "name": self.name,
            "description": self.description,
            "inputSchema": self.inputSchema
        }

@dataclass
class TextContent:
    """MCP Text Content response"""
    type: str = "text"
    text: str = ""

    def model_dump(self):
        return {
            "type": self.type,
            "text": self.text
        }


def get_capabilities():
    """Get MCP server capabilities for initialize request"""
    return {
        "protocolVersion": "2025-06-18",
        "capabilities": {
            "tools": {
                "listChanged": False
            },
            "resources": {},
            "prompts": {}
        },
        "serverInfo": {
            "name": "bookwise-library",
            "version": "1.0.0",
            "description": "AI-powered book recommendation system with 11,861+ books"
        }
    }

# Service instances (initialized on first request)
_services = {
    'vector': None,
    'calibre': None,
    'delivery': None
}


async def get_services():
    """Initialize and return services (lazy loading)"""
    if _services['vector'] is None:
        logger.info("Initializing BookWise services...")
        
        _services['vector'] = VectorSearchService(
            settings.CHROMADB_PATH,
            settings.OPENAI_API_KEY
        )
        
        _services['calibre'] = CalibreService(settings.CALIBRE_DB_PATH)
        
        _services['delivery'] = DeliveryService({
            'CALIBREDB_PATH': settings.CALIBREDB_PATH,
            'EREADER_EXPORT_FOLDER': settings.EREADER_EXPORT_FOLDER,
            'CALIBRE_LIBRARY_PATH': settings.CALIBRE_LIBRARY_PATH
        })
        
        logger.info("✅ BookWise services initialized")
    
    return _services


# Define MCP tools
async def list_tools() -> List[Tool]:
    """List available tools for Claude"""
    return [
        Tool(
            name="search_library",
            description=(
                "Semantic search across 11,861+ books in the personal Calibre library. "
                "Uses AI embeddings to find books by meaning, not keywords. "
                "\n\n"
                "Quality Score System:\n"
                "• 90-100: Legendary (Nobel, Pulitzer winners)\n"
                "• 80-89: Exceptional (Booker Prize)\n"
                "• 70-79: Outstanding (Major nominees)\n"
                "• 60-69: Excellent (Recognized works)\n"
                "\n"
                "Best practices:\n"
                "- Use 2-5 semantic variations for better discovery\n"
                "- Start with quality_threshold=70 for quality books\n"
                "- Example: ['resilience', 'overcoming adversity', 'human strength']"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "queries": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "1-5 semantic variations of the search topic",
                        "minItems": 1,
                        "maxItems": 5
                    },
                    "quality_threshold": {
                        "type": "integer",
                        "description": "Minimum quality score 0-100 (default: 70)",
                        "minimum": 0,
                        "maximum": 100,
                        "default": 70
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Max books to return 1-30 (default: 15)",
                        "minimum": 1,
                        "maximum": 30,
                        "default": 15
                    }
                },
                "required": ["queries"]
            }
        ),
        Tool(
            name="get_book_details",
            description=(
                "Get comprehensive details about a specific book. "
                "Returns metadata, quality score, awards, AI tags, themes, description, and available formats. "
                "Use this after search_library to get full information."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "book_id": {
                        "type": "integer",
                        "description": "Calibre book ID from search results"
                    }
                },
                "required": ["book_id"]
            }
        ),
        Tool(
            name="get_library_stats",
            description=(
                "Get statistics about the library: total books, authors, and tags. "
                "Quick overview of library size and content."
            ),
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="export_book_to_ereader",
            description=(
                "Export a book to the e-reader via Google Drive. "
                "Saves book in requested format (epub, mobi, pdf, etc.) to Google Drive folder. "
                "Use this when user wants to read a book on their e-reader."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "book_id": {
                        "type": "integer",
                        "description": "Calibre book ID to export"
                    },
                    "format": {
                        "type": "string",
                        "description": "Book format (default: epub)",
                        "enum": ["epub", "mobi", "pdf", "azw3"],
                        "default": "epub"
                    }
                },
                "required": ["book_id"]
            }
        )
    ]


async def call_tool(name: str, arguments: Any) -> List[TextContent]:
    """Handle tool calls from Claude"""
    services = await get_services()
    logger.info(f"MCP tool called: {name}")
    
    try:
        if name == "search_library":
            return await handle_search_library(services, arguments)
        elif name == "get_book_details":
            return await handle_get_book_details(services, arguments)
        elif name == "get_library_stats":
            return await handle_get_library_stats(services)
        elif name == "export_book_to_ereader":
            return await handle_export_book(services, arguments)
        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]
    except Exception as e:
        logger.error(f"Error in tool {name}: {e}", exc_info=True)
        return [TextContent(type="text", text=f"Error: {str(e)}")]


async def handle_search_library(services, args):
    """Handle search_library tool"""
    queries = args.get("queries", [])
    quality_threshold = args.get("quality_threshold", 70)
    max_results = args.get("max_results", 15)
    
    # Fetch more results than needed to allow filtering
    n_results_per_query = max(30, max_results * 2)
    
    results = await services['vector'].multi_query_search(
        queries=queries,
        n_results_per_query=n_results_per_query
    )
    
    # Filter by quality threshold and limit results
    filtered_results = []
    for book in results:
        # Get metadata to check quality
        metadata = book.get('metadata', {})
        quality_score = metadata.get('quality_score', 0)
        
        if isinstance(quality_score, str):
            try:
                quality_score = int(float(quality_score))
            except:
                quality_score = 0
        
        if quality_score >= quality_threshold:
            filtered_results.append({
                'id': book['book_id'],
                'title': book.get('title', 'Unknown'),
                'authors': book.get('author', 'Unknown'),
                'quality_score': quality_score,
                'relevance_score': 1.0 - book.get('distance', 0),  # Convert distance to similarity
                'metadata': metadata
            })
            
            if len(filtered_results) >= max_results:
                break
    
    if not filtered_results:
        text = f"No books found with quality score ≥{quality_threshold}. Try lowering the threshold or using different search terms."
    else:
        text = f"📚 Found {len(filtered_results)} books:\n\n"
        for i, book in enumerate(filtered_results, 1):
            text += f"**{i}. {book['title']}** by {book['authors']}\n"
            text += f"   • Book ID: `{book['id']}`\n"
            text += f"   • Quality: {book['quality_score']}/100"
            
            # Determine tier
            quality = book['quality_score']
            if quality >= 90:
                tier = "Legendary"
            elif quality >= 80:
                tier = "Exceptional"
            elif quality >= 70:
                tier = "Outstanding"
            elif quality >= 60:
                tier = "Excellent"
            else:
                tier = "Good"
            text += f" ({tier})\n"
            
            if book.get('relevance_score'):
                text += f"   • Relevance: {book['relevance_score']:.2f}\n"
            text += "\n"
        
        text += "\n💡 Use `get_book_details` with a book ID to see full information."
    
    return [TextContent(type="text", text=text)]


async def handle_get_book_details(services, args):
    """Handle get_book_details tool"""
    book_id = args.get("book_id")

    # Get basic info from Calibre
    book = await services['calibre'].get_book_details(book_id)
    if not book:
        return [TextContent(type="text", text=f"❌ Book ID {book_id} not found.")]
    
    # Get AI-enriched data from ChromaDB
    chroma_data = await services['vector'].get_book_metadata(book_id)
    
    # Build detailed response
    text = f"# {book['title']}\n\n"
    text += f"**By:** {book['authors']}\n"
    
    if book.get('publication_year'):
        text += f"**Published:** {book['publication_year']}\n"
    if book.get('publisher'):
        text += f"**Publisher:** {book['publisher']}\n"
    if book.get('isbn'):
        text += f"**ISBN:** {book['isbn']}\n"
    if book.get('series'):
        series_text = book['series']
        if book.get('series_index'):
            series_text += f" #{book['series_index']}"
        text += f"**Series:** {series_text}\n"
    if book.get('languages'):
        text += f"**Language:** {book['languages']}\n"
    
    # Quality info
    if chroma_data:
        quality_score = chroma_data.get('quality_score', 0)
        text += f"\n## Quality Assessment\n"
        text += f"**Score:** {quality_score}/100"
        
        # Get tier
        if quality_score >= 90:
            tier = "Legendary"
        elif quality_score >= 80:
            tier = "Exceptional"
        elif quality_score >= 70:
            tier = "Outstanding"
        elif quality_score >= 60:
            tier = "Excellent"
        else:
            tier = "Good"
        text += f" ({tier})\n"
        
        if chroma_data.get('awards'):
            text += f"**Recognition:** {chroma_data['awards']}\n"
        
        if chroma_data.get('themes'):
            themes = ', '.join(chroma_data['themes'][:5])
            text += f"\n**Themes:** {themes}\n"

        if chroma_data.get('tags'):
            tags = ', '.join(chroma_data['tags'][:10])
            text += f"**Tags:** {tags}\n"
        
        if chroma_data.get('description'):
            text += f"\n## Description\n{chroma_data['description']}\n"
    
    # Formats
    if book.get('formats'):
        formats = ', '.join(book['formats'])
        text += f"\n**Available Formats:** {formats}\n"
    
    text += f"\n**Book ID:** `{book_id}` (use for export)\n"
    
    return [TextContent(type="text", text=text)]


async def handle_get_library_stats(services):
    """Handle get_library_stats tool"""
    stats = await services['calibre'].get_library_stats()
    
    text = "📚 **Library Statistics**\n\n"
    text += f"• **Total Books:** {stats['total_books']:,}\n"
    text += f"• **Total Authors:** {stats['total_authors']:,}\n"
    text += f"• **Total Tags:** {stats['total_tags']:,}\n"
    
    return [TextContent(type="text", text=text)]


async def handle_export_book(services, args):
    """Handle export_book_to_ereader tool"""
    book_id = args.get("book_id")
    format_type = args.get("format", "epub").lower()

    # Get book info
    book = await services['calibre'].get_book_details(book_id)
    if not book:
        return [TextContent(type="text", text=f"❌ Book ID {book_id} not found.")]

    # Export using send_to_ereader method
    result = await services['delivery'].send_to_ereader(
        book_id=book_id,
        book_format=format_type,
        title=book['title'],
        author=book['authors']
    )

    if result.get('status') == 'sent':
        text = f"✅ **Book Exported Successfully!**\n\n"
        text += f"**Title:** {book['title']}\n"
        text += f"**Author:** {book['authors']}\n"
        text += f"**Format:** {format_type.upper()}\n"
        text += f"**Location:** {result.get('destination', 'Google Drive folder')}\n\n"
        text += "📖 The book is now available on your e-reader!"
    else:
        text = f"❌ **Export Failed**\n\n"
        text += f"**Error:** {result.get('message', 'Unknown error')}\n"

    return [TextContent(type="text", text=text)]
