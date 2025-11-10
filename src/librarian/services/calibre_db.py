"""
Calibre database service for read-only metadata access
"""
import aiosqlite
from typing import List, Dict, Optional
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class CalibreService:
    """Read-only access to Calibre database"""
    
    def __init__(self, db_path: str):
        """
        Initialize Calibre database service
        
        Args:
            db_path: Path to Calibre metadata.db
        """
        self.db_path = db_path
        
        if not Path(db_path).exists():
            raise FileNotFoundError(f"Calibre database not found at {db_path}")
        
        logger.info(f"Initialized Calibre service with database at {db_path}")
    
    async def get_book_details(self, book_id: int) -> Optional[Dict]:
        """
        Fetch complete metadata for a book by Calibre ID
        
        Args:
            book_id: Calibre book ID
            
        Returns:
            Dict with book metadata or None if not found
        """
        async with aiosqlite.connect(f'file:{self.db_path}?mode=ro', uri=True) as db:
            db.row_factory = aiosqlite.Row
            
            query = """
                SELECT 
                    b.id,
                    b.title,
                    b.pubdate,
                    b.path,
                    (SELECT GROUP_CONCAT(a2.name, ' & ')
                     FROM books_authors_link bal2
                     JOIN authors a2 ON bal2.author = a2.id
                     WHERE bal2.book = b.id
                     ORDER BY bal2.id) as authors,
                    c.text as description,
                    (SELECT GROUP_CONCAT(t2.name, ', ')
                     FROM books_tags_link btl2
                     JOIN tags t2 ON btl2.tag = t2.id
                     WHERE btl2.book = b.id) as tags
                FROM books b
                LEFT JOIN comments c ON b.id = c.book
                WHERE b.id = ?
            """
            
            async with db.execute(query, (book_id,)) as cursor:
                row = await cursor.fetchone()
                
                if row:
                    return {
                        'id': row['id'],
                        'title': row['title'],
                        'authors': row['authors'] or 'Unknown',
                        'pubdate': row['pubdate'],
                        'description': row['description'],
                        'tags': row['tags'].split(', ') if row['tags'] else [],
                        'path': row['path']
                    }
                
                return None
    
    async def get_book_formats(self, book_id: int) -> List[str]:
        """
        Get available file formats for a book
        
        Args:
            book_id: Calibre book ID
            
        Returns:
            List of available formats (e.g., ['epub', 'mobi', 'pdf'])
        """
        async with aiosqlite.connect(f'file:{self.db_path}?mode=ro', uri=True) as db:
            query = "SELECT format FROM data WHERE book = ?"
            
            async with db.execute(query, (book_id,)) as cursor:
                formats = await cursor.fetchall()
                return [f[0].lower() for f in formats]
    
    async def get_book_file_path(self, book_id: int, format: str) -> Optional[str]:
        """
        Get the file path for a specific book format
        
        Args:
            book_id: Calibre book ID
            format: File format (epub, mobi, etc.)
            
        Returns:
            Full path to book file or None if not found
        """
        async with aiosqlite.connect(f'file:{self.db_path}?mode=ro', uri=True) as db:
            db.row_factory = aiosqlite.Row
            
            query = """
                SELECT b.path, d.name, d.format
                FROM books b
                JOIN data d ON b.id = d.book
                WHERE b.id = ? AND LOWER(d.format) = ?
            """
            
            async with db.execute(query, (book_id, format.lower())) as cursor:
                row = await cursor.fetchone()
                
                if row:
                    # Calibre stores relative paths from library root
                    library_root = Path(self.db_path).parent
                    book_path = library_root / row['path'] / f"{row['name']}.{row['format'].lower()}"
                    return str(book_path)
                
                return None
    
    async def search_books_by_title(self, title_pattern: str, limit: int = 20) -> List[Dict]:
        """
        Search books by title pattern
        
        Args:
            title_pattern: SQL LIKE pattern (e.g., "%gatsby%")
            limit: Maximum results to return
            
        Returns:
            List of matching books
        """
        async with aiosqlite.connect(f'file:{self.db_path}?mode=ro', uri=True) as db:
            db.row_factory = aiosqlite.Row
            
            query = """
                SELECT 
                    b.id,
                    b.title,
                    GROUP_CONCAT(a.name, ' & ') as authors
                FROM books b
                LEFT JOIN books_authors_link bal ON b.id = bal.book
                LEFT JOIN authors a ON bal.author = a.id
                WHERE b.title LIKE ?
                GROUP BY b.id
                LIMIT ?
            """
            
            async with db.execute(query, (title_pattern, limit)) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]
    
    async def get_books_by_tag(self, tag: str, limit: int = 50) -> List[Dict]:
        """
        Get books with a specific tag
        
        Args:
            tag: Tag name to filter by
            limit: Maximum results
            
        Returns:
            List of books with the tag
        """
        async with aiosqlite.connect(f'file:{self.db_path}?mode=ro', uri=True) as db:
            db.row_factory = aiosqlite.Row
            
            query = """
                SELECT 
                    b.id,
                    b.title,
                    GROUP_CONCAT(a.name, ' & ') as authors
                FROM books b
                LEFT JOIN books_authors_link bal ON b.id = bal.book
                LEFT JOIN authors a ON bal.author = a.id
                JOIN books_tags_link btl ON b.id = btl.book
                JOIN tags t ON btl.tag = t.id
                WHERE t.name = ?
                GROUP BY b.id
                LIMIT ?
            """
            
            async with db.execute(query, (tag, limit)) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]
    
    async def get_library_stats(self) -> Dict:
        """
        Get basic statistics about the library
        
        Returns:
            Dict with stats (total_books, total_authors, total_tags)
        """
        async with aiosqlite.connect(f'file:{self.db_path}?mode=ro', uri=True) as db:
            stats = {}
            
            # Total books
            async with db.execute("SELECT COUNT(*) FROM books") as cursor:
                stats['total_books'] = (await cursor.fetchone())[0]
            
            # Total authors
            async with db.execute("SELECT COUNT(*) FROM authors") as cursor:
                stats['total_authors'] = (await cursor.fetchone())[0]
            
            # Total tags
            async with db.execute("SELECT COUNT(*) FROM tags") as cursor:
                stats['total_tags'] = (await cursor.fetchone())[0]
            
            return stats

