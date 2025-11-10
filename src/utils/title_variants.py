"""
Title variant extraction utilities
Handles alternate titles, translations, and editions
"""

import re
from typing import List, Dict


def extract_english_title_from_notes(notes: str) -> List[str]:
    """
    Extract English title(s) from notes field
    
    Handles formats like:
    - "English: The Lover"
    - "English: The Perfect Nanny / Lullaby"
    - "English: Within a Budding Grove"
    
    Args:
        notes: The notes field from a book entry
    
    Returns:
        List of English titles found (may be empty)
    """
    if not notes or "English:" not in notes:
        return []
    
    # Extract the part after "English:"
    try:
        english_part = notes.split("English:")[1]
        # Take everything up to a period, newline, or parenthesis
        english_part = re.split(r'[.\n(]', english_part)[0]
        english_part = english_part.strip()
        
        # Split on "/" or "or" for multiple translations
        titles = re.split(r'\s*/\s*|\s+or\s+', english_part)
        
        # Clean up each title
        cleaned_titles = []
        for title in titles:
            title = title.strip()
            if title:
                cleaned_titles.append(title)
        
        return cleaned_titles
    except Exception:
        return []


def get_all_title_variants(title: str, alternate_titles: List[str] = None, notes: str = "") -> List[str]:
    """
    Get all title variants for matching
    
    Args:
        title: Primary title
        alternate_titles: Optional list of alternate titles from JSON
        notes: Notes field (may contain English translations)
    
    Returns:
        List of all title variants (original + alternates + from notes)
    """
    variants = [title]
    
    # Add explicit alternate titles
    if alternate_titles:
        variants.extend(alternate_titles)
    
    # Add English translations from notes
    english_titles = extract_english_title_from_notes(notes)
    variants.extend(english_titles)
    
    # Remove duplicates while preserving order
    seen = set()
    unique_variants = []
    for variant in variants:
        variant_lower = variant.lower()
        if variant_lower not in seen:
            seen.add(variant_lower)
            unique_variants.append(variant)
    
    return unique_variants


def test_extraction():
    """Test the extraction logic"""
    test_cases = [
        ("English: The Lover", ["The Lover"]),
        ("English: The Perfect Nanny / Lullaby", ["The Perfect Nanny", "Lullaby"]),
        ("English: In the Shadow of Young Girls in Flower / Within a Budding Grove", 
         ["In the Shadow of Young Girls in Flower", "Within a Budding Grove"]),
        ("Won Nobel Prize 2014. English: Missing Person", ["Missing Person"]),
        ("No English title here", []),
        ("", []),
    ]
    
    print("Testing title extraction:")
    for notes, expected in test_cases:
        result = extract_english_title_from_notes(notes)
        status = "✓" if result == expected else "✗"
        print(f"{status} '{notes}' → {result}")
        if result != expected:
            print(f"  Expected: {expected}")


if __name__ == "__main__":
    test_extraction()

