"""
FastAPI server for BookWise Librarian
Intelligent book recommendation system with semantic search and quality filtering
"""
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import logging
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.librarian.config import settings
from src.librarian.services import (
    VectorSearchService,
    CalibreService,
    DeliveryService
)
from src.librarian.api import router
from src.librarian.api.oauth import router as oauth_router
from src.librarian.api.mcp import router as mcp_router  # OLD - deprecated
from src.librarian.api.mcp_root import router as mcp_root_router  # NEW - working pattern

# Configure logging with timestamps
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI(
    title="BookWise Librarian API",
    description="""
    Intelligent book recommendation system for your personal Calibre library.
    
    Features:
    - Multi-query semantic search with quality filtering
    - Pre-computed quality scores (0-100) based on comprehensive award hierarchy
    - Complete book metadata access
    - E-reader delivery integration
    
    All books are scored using era-neutral methodology covering:
    - 25 major literary awards (Nobel, Pulitzer, Booker, etc.)
    - 13 best-of lists (Modern Library, NYTimes, etc.)
    - Educational canons and classic series
    - 874 canonical authors across 3 tiers
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    servers=[
        {
            "url": "https://your-server.example.com",
            "description": "BookWise Production Server"
        }
    ]
)

# CORS middleware (allow Claude.ai and Anthropic API to call)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://claude.ai",
        "https://api.anthropic.com",
        "http://localhost:3000",  # For local development
        "http://localhost:8000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors with detailed messages"""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Validation Error",
            "detail": exc.errors()
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected errors gracefully"""
    logger.error(f"Unexpected error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal Server Error",
            "detail": str(exc)
        }
    )


# Startup event - Initialize services
@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    try:
        logger.info("Starting BookWise Librarian API...")
        logger.info(f"Configuration: CALIBRE_DB={settings.CALIBRE_DB_PATH}")
        logger.info(f"Configuration: CHROMADB={settings.CHROMADB_PATH}")
        logger.info(f"Configuration: AUTH={'enabled' if settings.BOOKWISE_API_KEY else 'disabled'}")
        
        # Initialize Vector Search Service
        logger.info("Initializing Vector Search Service...")
        app.state.vector_service = VectorSearchService(
            settings.CHROMADB_PATH,
            settings.OPENAI_API_KEY
        )
        
        # Initialize Calibre Service
        logger.info("Initializing Calibre Service...")
        app.state.calibre_service = CalibreService(settings.CALIBRE_DB_PATH)
        
        # Get library stats
        stats = await app.state.calibre_service.get_library_stats()
        logger.info(f"Library stats: {stats}")
        
        # Initialize Delivery Service
        logger.info("Initializing Delivery Service...")
        app.state.delivery_service = DeliveryService({
            'CALIBREDB_PATH': settings.CALIBREDB_PATH,
            'EREADER_EXPORT_FOLDER': settings.EREADER_EXPORT_FOLDER,
            'CALIBRE_LIBRARY_PATH': settings.CALIBRE_LIBRARY_PATH,
            'AUTO_CLOSE_CALIBRE': settings.AUTO_CLOSE_CALIBRE
        })
        
        logger.info("✅ All services initialized successfully")
        
    except Exception as e:
        logger.error(f"❌ Startup failed: {e}", exc_info=True)
        raise


# CRITICAL: MCP routes MUST be registered FIRST (uses root path)
app.include_router(mcp_root_router, tags=["MCP"])

# Include API routes (with prefix)
app.include_router(router, prefix="/api/v1", tags=["API"])

# Include OAuth routes (no prefix, no auth required for OAuth endpoints)
app.include_router(oauth_router)

# OLD MCP routes (deprecated - kept for reference)
# app.include_router(mcp_router, tags=["MCP-OLD"])


# Root endpoint - DISABLED (conflicts with MCP at root path)
# Moved to /api-info if needed
@app.get("/api-info", tags=["Health"])
async def server_info():
    """Server information (moved from root to avoid conflict with MCP)"""
    return {
        "service": "BookWise Librarian API",
        "version": "1.0.0",
        "status": "operational",
        "docs": "/docs",
        "openapi": "/openapi.json",
        "mcp_endpoint": "/"  # Updated from "/mcp/sse"
    }


# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint for monitoring"""
    try:
        # Check if services are initialized
        has_vector = hasattr(app.state, 'vector_service')
        has_calibre = hasattr(app.state, 'calibre_service')
        has_delivery = hasattr(app.state, 'delivery_service')
        
        healthy = all([has_vector, has_calibre, has_delivery])
        
        return {
            "status": "healthy" if healthy else "degraded",
            "services": {
                "vector_search": "ok" if has_vector else "not initialized",
                "calibre_db": "ok" if has_calibre else "not initialized",
                "delivery": "ok" if has_delivery else "not initialized"
            }
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "unhealthy",
                "error": str(e)
            }
        )

# Library stats endpoint
@app.get("/api/v1/stats", tags=["Info"])
async def get_library_stats(request: Request):
    """Get library statistics"""
    try:
        stats = await request.app.state.calibre_service.get_library_stats()
        return stats
    except Exception as e:
        logger.error(f"Failed to get stats: {e}")
        raise


# Main entry point
if __name__ == "__main__":
    import uvicorn
    
    logger.info(f"Starting server on {settings.HOST}:{settings.PORT}")
    
    uvicorn.run(
        app,  # Pass app instance directly instead of string import
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.RELOAD,
        log_level="info"
    )

