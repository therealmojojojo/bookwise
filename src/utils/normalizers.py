"""
Text normalization utilities for matching book titles and author names
"""

import re
import unicodedata


def normalize_title(title: str, author: str) -> str:
    """
    Normalize title and author for matching
    
    Args:
        title: Book title
        author: Author name
    
    Returns:
        Normalized string combining title and author
    """
    # Remove articles, punctuation, make lowercase
    title = title.lower().strip()
    title = re.sub(r'^(the|a|an)\s+', '', title)
    title = re.sub(r'[^\w\s]', '', title)
    title = re.sub(r'\s+', ' ', title).strip()
    
    author = normalize_author(author)
    
    return f"{title}||{author}"


def normalize_author(author: str) -> str:
    """
    Normalize author name for matching
    
    Handles diacritics and encoding variations by converting to ASCII equivalents.
    For example: García -> Garcia, José -> Jose
    
    Args:
        author: Author name
    
    Returns:
        Normalized author name (ASCII, lowercase, no punctuation)
    """
    # First normalize unicode to decomposed form (NFD) to separate diacritics
    author = unicodedata.normalize('NFD', author)
    # Remove combining characters (diacritics)
    author = ''.join(char for char in author if unicodedata.category(char) != 'Mn')
    # Convert back to composed form (NFC) and make lowercase
    author = unicodedata.normalize('NFC', author).lower().strip()
    # Remove common suffixes
    author = re.sub(r'\s+(jr\.?|sr\.?|ii|iii|iv)$', '', author)
    # Remove punctuation
    author = re.sub(r'[^\w\s]', '', author)
    author = re.sub(r'\s+', ' ', author).strip()
    return author

