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

    async def search_authors(self, search_term: str, limit: int = 20) -> List[Dict]:
        """
        Fuzzy search for authors by name.
        Splits search term into words and matches ALL words against name or sort fields.

        Args:
            search_term: Search string (e.g., "Ursula Le Guin" or "Fitzgerald")
            limit: Maximum results to return

        Returns:
            List of matching authors: [{id, name, sort}, ...]
        """
        async with aiosqlite.connect(f'file:{self.db_path}?mode=ro', uri=True) as db:
            db.row_factory = aiosqlite.Row

            # Split search term into words for fuzzy matching
            words = search_term.strip().split()

            if not words:
                return []

            # Build WHERE clause: all words must match in name OR sort
            conditions = []
            params = []
            for word in words:
                conditions.append("(name LIKE ? OR sort LIKE ?)")
                params.extend([f'%{word}%', f'%{word}%'])

            where_clause = " AND ".join(conditions)

            query = f"""
                SELECT id, name, sort
                FROM authors
                WHERE {where_clause}
                ORDER BY name
                LIMIT ?
            """
            params.append(limit)

            async with db.execute(query, params) as cursor:
                rows = await cursor.fetchall()
                return [{'id': row['id'], 'name': row['name'], 'sort': row['sort']} for row in rows]

    async def get_books_by_author_id(self, author_id: int, limit: int = 100) -> List[Dict]:
        """
        Get all books by an author using their Calibre author ID.

        Args:
            author_id: Calibre author ID
            limit: Maximum results to return

        Returns:
            List of books: [{id, title, series, series_index, formats}, ...]
        """
        async with aiosqlite.connect(f'file:{self.db_path}?mode=ro', uri=True) as db:
            db.row_factory = aiosqlite.Row

            query = """
                SELECT
                    b.id,
                    b.title,
                    s.name as series,
                    b.series_index,
                    GROUP_CONCAT(DISTINCT d.format) as formats
                FROM books b
                JOIN books_authors_link bal ON b.id = bal.book
                LEFT JOIN books_series_link bsl ON b.id = bsl.book
                LEFT JOIN series s ON bsl.series = s.id
                LEFT JOIN data d ON b.id = d.book
                WHERE bal.author = ?
                GROUP BY b.id
                ORDER BY s.name NULLS LAST, b.series_index, b.title
                LIMIT ?
            """

            async with db.execute(query, (author_id, limit)) as cursor:
                rows = await cursor.fetchall()
                return [
                    {
                        'id': row['id'],
                        'title': row['title'],
                        'series': row['series'],
                        'series_index': row['series_index'],
                        'formats': row['formats'].split(',') if row['formats'] else []
                    }
                    for row in rows
                ]

    async def get_books_by_author_name(self, author_name: str, limit: int = 100) -> Optional[Dict]:
        """
        Get all books by an author using their exact name.
        First looks up the author ID, then fetches their books.

        Args:
            author_name: Exact author name as stored in Calibre
            limit: Maximum results to return

        Returns:
            Dict with author info and books: {author_id, author_name, books: [...]}
            or None if author not found
        """
        async with aiosqlite.connect(f'file:{self.db_path}?mode=ro', uri=True) as db:
            db.row_factory = aiosqlite.Row

            # Look up author by exact name (case-insensitive due to COLLATE NOCASE)
            async with db.execute(
                "SELECT id, name FROM authors WHERE name = ?",
                (author_name,)
            ) as cursor:
                author_row = await cursor.fetchone()

            if not author_row:
                return None

            author_id = author_row['id']
            author_name_exact = author_row['name']

            # Get books using the author ID
            books = await self.get_books_by_author_id(author_id, limit)

            return {
                'author_id': author_id,
                'author_name': author_name_exact,
                'book_count': len(books),
                'books': books
            }

    async def find_book(self, title: str, author: Optional[str] = None, limit: int = 20) -> List[Dict]:
        """
        Find books by exact title match (case-insensitive).
        Optionally filter by author name.

        Args:
            title: Book title to search for (exact match, case-insensitive)
            author: Optional author name to filter by (exact match, case-insensitive)
            limit: Maximum results to return

        Returns:
            List of matching books: [{id, title, authors, series, series_index, formats}, ...]
        """
        async with aiosqlite.connect(f'file:{self.db_path}?mode=ro', uri=True) as db:
            db.row_factory = aiosqlite.Row

            if author:
                # Search with author filter
                query = """
                    SELECT
                        b.id,
                        b.title,
                        GROUP_CONCAT(DISTINCT a.name) as authors,
                        s.name as series,
                        b.series_index,
                        GROUP_CONCAT(DISTINCT d.format) as formats
                    FROM books b
                    JOIN books_authors_link bal ON b.id = bal.book
                    JOIN authors a ON bal.author = a.id
                    LEFT JOIN books_series_link bsl ON b.id = bsl.book
                    LEFT JOIN series s ON bsl.series = s.id
                    LEFT JOIN data d ON b.id = d.book
                    WHERE b.title = ? COLLATE NOCASE
                      AND a.name = ? COLLATE NOCASE
                    GROUP BY b.id
                    LIMIT ?
                """
                params = (title, author, limit)
            else:
                # Search without author filter
                query = """
                    SELECT
                        b.id,
                        b.title,
                        GROUP_CONCAT(DISTINCT a.name) as authors,
                        s.name as series,
                        b.series_index,
                        GROUP_CONCAT(DISTINCT d.format) as formats
                    FROM books b
                    LEFT JOIN books_authors_link bal ON b.id = bal.book
                    LEFT JOIN authors a ON bal.author = a.id
                    LEFT JOIN books_series_link bsl ON b.id = bsl.book
                    LEFT JOIN series s ON bsl.series = s.id
                    LEFT JOIN data d ON b.id = d.book
                    WHERE b.title = ? COLLATE NOCASE
                    GROUP BY b.id
                    LIMIT ?
                """
                params = (title, limit)

            async with db.execute(query, params) as cursor:
                rows = await cursor.fetchall()
                return [
                    {
                        'id': row['id'],
                        'title': row['title'],
                        'authors': row['authors'] or 'Unknown',
                        'series': row['series'],
                        'series_index': row['series_index'],
                        'formats': row['formats'].split(',') if row['formats'] else []
                    }
                    for row in rows
                ]

