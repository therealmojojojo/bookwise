"""
Configuration management for Librarian API
"""
from pydantic_settings import BaseSettings
from pathlib import Path
from typing import Optional

class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Paths
    CALIBRE_DB_PATH: str
    CALIBRE_LIBRARY_PATH: Optional[str] = None  # Optional: explicit library path for calibredb
    CHROMADB_PATH: str
    
    def __init__(self, **kwargs):
        """Initialize settings and clean up paths"""
        super().__init__(**kwargs)
        # Clean up paths (remove extra spaces and quotes)
        if self.CHROMADB_PATH:
            self.CHROMADB_PATH = self.CHROMADB_PATH.strip().strip("'").strip('"')
        if self.EREADER_EXPORT_FOLDER:
            self.EREADER_EXPORT_FOLDER = self.EREADER_EXPORT_FOLDER.strip().strip("'").strip('"')
    
    # API Security
    BOOKWISE_API_KEY: Optional[str] = None  # If None, auth is disabled (dev mode)
    
    # E-reader delivery via Calibre export
    CALIBREDB_PATH: str  # Path to calibredb executable
    EREADER_EXPORT_FOLDER: str  # Required: shared folder for exporting books
    AUTO_CLOSE_CALIBRE: bool = True  # Automatically close Calibre GUI if it interferes with export

    # API Keys for semantic search
    OPENAI_API_KEY: str  # Required: for generating query embeddings
    
    # Server
    PORT: int = 8000
    HOST: str = "0.0.0.0"
    RELOAD: bool = False  # Set to True for development

    # API Configuration
    CHARACTER_LIMIT: int = 10000  # For truncating large responses
    MAX_SEARCH_RESULTS: int = 30
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # Ignore extra fields in .env file


# Global settings instance
settings = Settings()

