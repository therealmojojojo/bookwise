"""
Parser for curated book list files
"""

import re
from typing import List, Tuple


def parse_curated_list(file_path: str) -> List[Tuple[int, str, str]]:
    """
    Parse curated fiction list to extract book IDs, titles, and authors
    
    Args:
        file_path: Path to the curated list file
    
    Returns:
        List of tuples containing (book_id, title, author)
    """
    books = []
    
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    current_title = None
    current_author = None
    
    for line in lines:
        line = line.strip()
        if not line or line.startswith("Fiction Books") or line.startswith("==="):
            continue
        
        # Check if this is a book entry line (starts with quote)
        if line.startswith('"'):
            # Extract title and author from quoted format
            # Format: "Title" by Author
            match = re.match(r'"([^"]+)"\s+by\s+(.+)', line)
            if match:
                current_title = match.group(1)
                current_author = match.group(2)
        
        # Check if this is a library match line
        elif line.strip().startswith('Library:') and current_title:
            # Extract book ID
            # Format: Library: "Title" by Author [ID: 12345]
            match = re.search(r'\[ID:\s*(\d+)\]', line)
            if match:
                book_id = int(match.group(1))
                books.append((book_id, current_title, current_author))
    
    return books

