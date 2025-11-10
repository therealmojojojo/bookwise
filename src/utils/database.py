"""
Calibre database access utilities
"""

import sqlite3
from typing import Optional, Tuple


def get_book_from_database(calibre_db_path: str, book_id: int) -> Optional[Tuple[str, str]]:
    """
    Retrieve book title and author from Calibre database
    
    Args:
        calibre_db_path: Path to Calibre metadata.db file
        book_id: Calibre book ID
    
    Returns:
        Tuple of (title, author) or None if not found
    """
    try:
        conn = sqlite3.connect(f"file:{calibre_db_path}?mode=ro", uri=True)
        cursor = conn.cursor()
        
        # Query to get book title and authors
        query = """
            SELECT b.title, 
                   GROUP_CONCAT(a.name, ' & ') as authors
            FROM books b
            LEFT JOIN books_authors_link bal ON b.id = bal.book
            LEFT JOIN authors a ON bal.author = a.id
            WHERE b.id = ?
            GROUP BY b.id
        """
        
        cursor.execute(query, (book_id,))
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return result[0], result[1]
        return None
        
    except Exception as e:
        print(f"Error querying database for book {book_id}: {e}")
        return None

