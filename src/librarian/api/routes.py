"""
API route definitions for Librarian service
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict
import logging

from .models import (
    SearchLibraryRequest, SearchLibraryResponse,
    GetBookDetailsRequest, GetBookDetailsResponse,
    GetTopBooksRequest, GetTopBooksResponse,
    SendBookRequest, SendBookResponse,
    BookResult, BookDetail
)
from .dependencies import get_services, verify_api_key

logger = logging.getLogger(__name__)

# Create router with authentication dependency
# ⚠️ TEMPORARILY NO AUTH - testing with ChatGPT Custom GPTs
router = APIRouter()
# router = APIRouter(dependencies=[Depends(verify_api_key)])  # Restore this when done testing


def get_quality_tier(score: int) -> str:
    """
    Get human-readable tier label for a quality score
    
    Args:
        score: Quality score (0-100)
        
    Returns:
        Tier label
    """
    if score >= 90:
        return "Legendary"
    elif score >= 80:
        return "Exceptional"
    elif score >= 70:
        return "Outstanding"
    elif score >= 60:
        return "Excellent"
    elif score >= 50:
        return "Very Good"
    elif score >= 40:
        return "Good"
    elif score >= 30:
        return "Solid"
    elif score >= 20:
        return "Notable"
    elif score >= 10:
        return "Recognized"
    else:
        return "Limited"


@router.post(
    "/search_library",
    response_model=SearchLibraryResponse,
    summary="Multi-query semantic search with quality filtering",
    description="""
    Intelligent semantic search across the user's personal Calibre library (11,861+ books).
    Uses AI embeddings to find books by meaning, not just keywords.
    
    **How it works:**
    1. Takes 1-5 semantic queries (varied phrasings of the user's interest)
    2. Searches ChromaDB vector database with 3072-dimension embeddings
    3. Filters results by quality score (0-100, based on literary awards)
    4. Returns top matches sorted by quality and relevance
    
    **Quality Score System:**
    - 90-100: Legendary (Nobel Prize, Pulitzer winners)
    - 80-89: Exceptional (Major award winners, Booker Prize)
    - 70-79: Outstanding (Major award nominees, national awards)
    - 60-69: Excellent (Recognized works, best-of lists)
    - Below 60: Good books without major awards
    
    **Best Practices:**
    - Use 2-5 varied semantic queries for serendipitous discovery
    - Start with quality_threshold=70 for high-quality recommendations
    - Try conceptual variations: "resilience", "overcoming adversity", "human strength"
    - Don't just repeat keywords - explore semantic variations
    
    **Example queries for "books about resilience":**
    - "resilience during hardship"
    - "overcoming adversity and survival"
    - "human strength in difficult times"
    - "stories of perseverance"
    """,
    tags=["Search"]
)
async def search_library(
    request: SearchLibraryRequest,
    services: Dict = Depends(get_services)
) -> SearchLibraryResponse:
    """
    SEMANTIC SEARCH - Find books by meaning, not just keywords
    
    REQUEST PARAMETERS:
    - queries: list[str] - 1-5 semantic variations of user's interest
    - quality_threshold: int (0-100) - Minimum quality score (default: 70)
    - max_results: int (1-30) - Maximum books to return (default: 15)
    
    RESPONSE:
    - total_found: Number of books matching criteria
    - books: List of book results with:
      * book_id: Calibre ID for fetching full details
      * title, author: Basic metadata
      * quality_score: 0-100 literary quality rating
      * quality_tier: Human-readable tier (Legendary, Exceptional, etc.)
      * similarity: 0-1 relevance score (higher = better match)
      * recognition: Brief awards/lists summary (truncated to 200 chars)
    
    STRATEGY FOR SERENDIPITOUS DISCOVERY:
    1. Generate 3-5 semantic variations of the user's interest
    2. Include both concrete and abstract phrasings
    3. Consider different aspects: theme, emotion, setting, style
    4. Filter by quality_threshold=70+ for excellent books
    5. Present top 3-5 results with explanations of why they match
    
    EXAMPLE WORKFLOW:
    User asks: "I'm interested in stories about economic hardship"
    
    Your queries should explore:
    - Direct: "economic hardship", "poverty and survival"
    - Thematic: "great depression era", "working class struggle"
    - Emotional: "resilience during adversity", "human dignity in hardship"
    - Contextual: "dust bowl migration", "social justice economic"
    
    Returns books like: The Grapes of Wrath (quality: 105, Nobel + Pulitzer)
    """
    try:
        logger.info(f"Search request: {len(request.queries)} queries, threshold={request.quality_threshold}")
        
        # 1. Query ChromaDB with multi-query search
        search_results = await services['vector'].multi_query_search(
            request.queries,
            n_results_per_query=20
        )
        
        if not search_results:
            return SearchLibraryResponse(
                total_found=0,
                books=[],
                message="No books found matching your queries."
            )
        
        # 2. Filter by quality threshold (quality_score is already in ChromaDB metadata)
        filtered = [
            book for book in search_results 
            if book.get('quality_score', 0) >= request.quality_threshold
        ]
        
        if not filtered:
            return SearchLibraryResponse(
                total_found=0,
                books=[],
                message=f"No books found with quality score ≥ {request.quality_threshold}. Try lowering the threshold."
            )
        
        # 3. Sort by quality score DESC, then similarity DESC
        sorted_results = sorted(
            filtered,
            key=lambda x: (x.get('quality_score', 0), x['similarity']),
            reverse=True
        )[:request.max_results]
        
        # 4. Convert to response models
        book_results = []
        for book in sorted_results:
            quality_score = int(book.get('quality_score', 0))
            book_results.append(BookResult(
                book_id=book['book_id'],
                title=book['title'],
                author=book['author'],
                quality_score=quality_score,
                quality_tier=get_quality_tier(quality_score),
                similarity=book['similarity'],
                awards=[],  # Awards in ChromaDB are in single string, not list
                lists=[],
                tags=[],
                recognition=str(book.get('awards', ''))[:200] if book.get('awards') else ''
            ))
        
        return SearchLibraryResponse(
            total_found=len(book_results),
            books=book_results
        )
        
    except Exception as e:
        logger.error(f"Search library error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}"
        )


@router.post(
    "/get_book_details",
    response_model=GetBookDetailsResponse,
    summary="Get complete metadata for specific books",
    description="""
    Fetch comprehensive metadata for books by their Calibre IDs.
    
    **Use this after search_library to get full details about interesting books.**
    
    **What you get:**
    - Complete bibliographic metadata (title, author, publication date)
    - Full description/summary from Calibre
    - All Calibre tags (genres, awards, AI-generated topics)
    - Available formats (epub, mobi, pdf, etc.)
    - Quality scores and literary recognition
    - AI-generated tags, themes, and enhanced description
    
    **Quality Metadata Includes:**
    - quality_score: 0-100 rating based on literary awards
    - quality_tier: Human-readable tier label
    - recognition: Awards and lists (Nobel, Pulitzer, Booker, etc.)
    - ai_tags: AI-detected topics (e.g., "Great Depression", "social justice")
    - ai_themes: Thematic elements identified by AI
    - ai_description: Content-focused summary (not marketing copy)
    
    **When to use:**
    1. After search_library returns interesting book_ids
    2. When user asks "tell me more about that book"
    3. Before recommending a book to provide full context
    4. To check available formats before sending to e-reader
    """,
    tags=["Details"]
)
async def get_book_details(
    request: GetBookDetailsRequest,
    services: Dict = Depends(get_services)
) -> GetBookDetailsResponse:
    """
    GET FULL METADATA - Retrieve complete book information
    
    REQUEST PARAMETERS:
    - book_ids: list[int] - 1-20 Calibre book IDs from search results
    
    RESPONSE FOR EACH BOOK:
    - id: Calibre book ID
    - title: Book title
    - authors: Author name(s)
    - pubdate: Publication date (may be original or edition date)
    - description: Full description/summary from Calibre
    - tags: All Calibre tags (genres, awards, lists, AI topics)
    - formats: Available file formats [epub, mobi, pdf, azw3, etc.]
    - quality_score: 0-100 literary quality rating
    - quality_tier: Tier label (Legendary/Exceptional/Outstanding/etc.)
    - recognition: Awards summary (Nobel Prize 1962, Pulitzer 1940, etc.)
    - ai_tags: AI-generated topic tags (if book is enriched)
    - ai_themes: Thematic elements (if book is enriched)
    - ai_description: Enhanced AI summary (if book is enriched)
    
    INTERPRETING QUALITY SCORES:
    - 90-100 (Legendary): Nobel/Pulitzer winners, canonical classics
    - 80-89 (Exceptional): Booker Prize, major award winners
    - 70-79 (Outstanding): National Book Award, major nominees
    - 60-69 (Excellent): Recognized in best-of lists
    - Below 60: Good books without major literary awards
    - 0 (Not Scored): Book not yet enriched with quality data
    
    USE CASE EXAMPLE:
    1. User searches for "resilience" → get book_id 1834
    2. Call get_book_details([1834]) to get full info
    3. Present: "The Grapes of Wrath by John Steinbeck
       - Quality: 105 (Legendary)
       - Recognition: Nobel Prize 1962, Pulitzer 1940, Modern Library #10
       - AI Topics: Great Depression, Migrant Workers, Social Justice
       - Available in: epub format"
    4. Ask if user wants it sent to their e-reader
    
    NOTES:
    - Books with quality_score=0 are in the library but not yet enriched
    - Not all books have AI-generated metadata (only 553/11,861 currently enriched)
    - Some books may not have descriptions in Calibre
    """
    try:
        logger.info(f"Fetching details for {len(request.book_ids)} books")
        
        books = []
        for book_id in request.book_ids:
            # Get Calibre metadata
            details = await services['calibre'].get_book_details(book_id)
            
            if not details:
                logger.warning(f"Book ID {book_id} not found")
                continue
            
            # Get available formats
            formats = await services['calibre'].get_book_formats(book_id)
            details['formats'] = formats
            
            # Enrich with quality data from ChromaDB
            chroma_data = await services['vector'].get_book_metadata(book_id)
            
            if chroma_data:
                details['quality_score'] = chroma_data['quality_score']
                details['quality_tier'] = get_quality_tier(chroma_data['quality_score'])
                details['awards'] = []  # Awards are stored as string in ChromaDB
                details['lists'] = []
                details['recognition'] = chroma_data.get('awards', '')
                # Add AI-generated metadata
                details['ai_tags'] = chroma_data.get('tags', [])
                details['ai_themes'] = chroma_data.get('themes', [])
                details['ai_description'] = chroma_data.get('description', '')
            else:
                # Book not enriched yet
                details['quality_score'] = 0
                details['quality_tier'] = 'Not Scored'
                details['awards'] = []
                details['lists'] = []
                details['recognition'] = ''
            
            books.append(BookDetail(**details))
        
        return GetBookDetailsResponse(
            books=books,
            message=f"Found {len(books)} of {len(request.book_ids)} requested books"
        )
        
    except Exception as e:
        logger.error(f"Get book details error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch book details: {str(e)}"
        )


@router.post(
    "/send_book_to_ereader",
    response_model=SendBookResponse,
    summary="Export book to e-reader shared folder",
    description="""
    Export a book from the Calibre library to the user's configured e-reader shared folder.
    
    **Current implementation:** Exports via `calibredb export` to Google Drive Books folder
    
    **How it works:**
    1. Validates book exists and requested format is available
    2. Uses Calibre's `calibredb export` command (safe, read-only)
    3. Exports to configured folder (typically Google Drive for cloud sync)
    4. File is named: "{title} - {author}.{format}"
    
    **Supported formats:** epub, mobi, azw3, pdf (if available for that book)
    
    **User's setup:**
    - Export folder: Google Drive Books-share (syncs to all devices)
    - Most books available in: epub format
    - Some books have multiple formats
    
    **When to use:**
    1. After user confirms they want to read a recommended book
    2. When user says "send that to my e-reader" or "I want to read that"
    3. Always check available formats first using get_book_details
    """,
    tags=["Delivery"]
)
async def send_book_to_ereader(
    request: SendBookRequest,
    services: Dict = Depends(get_services)
) -> SendBookResponse:
    """
    EXPORT BOOK - Send book file to user's e-reader folder
    
    REQUEST PARAMETERS:
    - book_id: int - Calibre book ID to export
    - format: str - File format (epub, mobi, azw3, pdf)
    - device_name: str (optional) - Not currently used, kept for future compatibility
    
    RESPONSE:
    - status: "sent" (success) or "error" (failure)
    - message: Human-readable status message
    - destination: Full path where book was exported
    - format: Confirmed export format
    - book_title: Book title (added to response)
    - book_author: Book author (added to response)
    
    WORKFLOW:
    1. Check if book exists → 404 if not found
    2. Check if format is available → 400 if format not available
    3. Export using calibredb to configured folder
    4. Return success with file location
    
    ERROR HANDLING:
    - 404: Book ID not found in library
    - 400: Requested format not available for this book
      → Response includes list of available formats
    - 500: Export failed (check logs for details)
    
    EXAMPLE CONVERSATION FLOW:
    User: "I'd like to read The Grapes of Wrath"
    
    1. You: Call search_library to find it → get book_id 1834
    2. You: Call get_book_details([1834]) → formats: ["epub"]
    3. You: "I found it! Available in epub format. Send it to your e-reader?"
    4. User: "Yes please"
    5. You: Call send_book_to_ereader(book_id=1834, format="epub")
    6. You: "✓ Sent 'The Grapes of Wrath' by John Steinbeck to your Google Drive Books folder in epub format. It should sync to your devices shortly."
    
    BEST PRACTICES:
    - Always get book_details first to check available formats
    - Prefer "epub" format (most widely supported)
    - Confirm export with user before sending
    - Provide full path in confirmation so user knows where to find it
    - If format not available, offer alternatives from formats list
    
    TECHNICAL NOTES:
    - Uses calibredb CLI (safe, respects Calibre's database integrity)
    - Exports to: ~/Library/CloudStorage/GoogleDrive-.../Books-share/
    - Files named as: "{title} - {author}.{format}"
    - Original files in Calibre library remain untouched (read-only operation)
    - Export typically takes 1-3 seconds
    """
    try:
        logger.info(f"Sending book {request.book_id} in {request.format} format")
        
        # 1. Validate book exists
        book_details = await services['calibre'].get_book_details(request.book_id)
        if not book_details:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Book ID {request.book_id} not found in library"
            )
        
        # 2. Check format availability
        formats = await services['calibre'].get_book_formats(request.book_id)
        if request.format.lower() not in formats:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Format '{request.format}' not available. Available formats: {', '.join(formats)}"
            )
        
        # 3. Export book to shared folder using calibredb
        result = await services['delivery'].send_to_ereader(
            book_id=request.book_id,
            book_format=request.format,
            title=book_details['title'],
            author=book_details['authors'],
            device_name=request.device_name
        )
        
        # 5. Format response
        result['book_title'] = book_details['title']
        result['book_author'] = book_details['authors']
        
        return SendBookResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Send to e-reader error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send book: {str(e)}"
        )

