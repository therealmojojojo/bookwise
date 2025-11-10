"""
Pydantic models for API requests and responses
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


# ============================================================================
# Search Library
# ============================================================================

class SearchLibraryRequest(BaseModel):
    """Request model for search_library endpoint"""
    queries: List[str] = Field(
        ...,
        min_length=1,
        max_length=5,
        description="1-5 search terms for conceptual exploration",
        examples=[
            ["resilience during hardship", "economic depression fiction"],
            ["black holes physics", "cosmology popular science", "time dilation"]
        ]
    )
    quality_threshold: int = Field(
        default=1,
        ge=0,
        le=100,
        description="Minimum quality score (0-100). Recommended: 70+ for excellent books"
    )
    max_results: int = Field(
        default=15,
        ge=1,
        le=30,
        description="Maximum books to return"
    )


class BookResult(BaseModel):
    """A book search result"""
    book_id: int
    title: str
    author: str
    quality_score: int
    quality_tier: str
    similarity: float = Field(..., ge=0.0, le=1.0, description="Relevance score (0-1)")
    awards: List[str] = []
    lists: List[str] = []
    tags: List[str] = []
    recognition: Optional[str] = None


class SearchLibraryResponse(BaseModel):
    """Response model for search_library endpoint"""
    total_found: int
    books: List[BookResult]
    message: Optional[str] = None


# ============================================================================
# Get Book Details
# ============================================================================

class GetBookDetailsRequest(BaseModel):
    """Request model for get_book_details endpoint"""
    book_ids: List[int] = Field(
        ...,
        min_length=1,
        max_length=20,
        description="Calibre book IDs to fetch details for (1-20)",
        examples=[[1834, 17306, 2781]]
    )


class BookDetail(BaseModel):
    """Detailed book metadata"""
    id: int
    title: str
    authors: str
    pubdate: Optional[str] = None
    description: Optional[str] = None
    tags: List[str] = []
    formats: List[str] = []
    quality_score: Optional[int] = None
    quality_tier: Optional[str] = None
    awards: List[str] = []
    lists: List[str] = []
    recognition: Optional[str] = None


class GetBookDetailsResponse(BaseModel):
    """Response model for get_book_details endpoint"""
    books: List[BookDetail]
    message: Optional[str] = None


# ============================================================================
# Get Top Quality Books
# ============================================================================

class GetTopBooksRequest(BaseModel):
    """Request model for get_top_quality_books endpoint"""
    genre: Optional[str] = Field(
        default=None,
        description="Optional tag/genre to filter by (e.g., 'fiction', 'science fiction')"
    )
    min_quality: int = Field(
        default=85,
        ge=70,
        le=100,
        description="Minimum quality score (70-100)"
    )
    limit: int = Field(
        default=20,
        ge=1,
        le=50,
        description="Maximum results to return (1-50)"
    )


class GetTopBooksResponse(BaseModel):
    """Response model for get_top_quality_books endpoint"""
    total_found: int
    books: List[BookResult]
    filters: Dict[str, Any] = {}
    message: Optional[str] = None


# ============================================================================
# Send to E-reader
# ============================================================================

class SendBookRequest(BaseModel):
    """Request model for send_book_to_ereader endpoint"""
    book_id: int = Field(..., description="Calibre book ID to send")
    format: str = Field(
        default="epub",
        pattern="^(epub|mobi|azw3|pdf)$",
        description="File format to send (epub, mobi, azw3, pdf)"
    )
    device_name: Optional[str] = Field(
        default=None,
        description="Optional specific device name (for multi-device setups)"
    )


class SendBookResponse(BaseModel):
    """Response model for send_book_to_ereader endpoint"""
    status: str  # "sent", "error", "queued"
    message: str
    destination: Optional[str] = None
    format: str
    book_title: Optional[str] = None
    book_author: Optional[str] = None


# ============================================================================
# Error Response
# ============================================================================

class ErrorResponse(BaseModel):
    """Standard error response"""
    error: str
    detail: Optional[str] = None
    status_code: int

