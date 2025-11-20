"""
DataSource Management Service

Handles reading, writing, and updating JSON datasource files
(award lists, canonical authors, etc.)
"""
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
from copy import deepcopy

logger = logging.getLogger(__name__)


class DataSourceService:
    """Service for managing literary datasources (awards, canonical authors, etc.)"""
    
    def __init__(self, datasources_dir: str):
        self.datasources_dir = Path(datasources_dir)
        if not self.datasources_dir.exists():
            raise ValueError(f"Datasources directory not found: {datasources_dir}")
    
    def list_datasources(self) -> List[Dict[str, Any]]:
        """List all available datasources with their metadata"""
        datasources = []
        
        for file_path in self.datasources_dir.glob("*.json"):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    metadata = data.get('metadata', {})
                    
                    datasources.append({
                        'filename': file_path.name,
                        'source_name': metadata.get('source_name', file_path.stem),
                        'source_type': metadata.get('source_type', 'unknown'),
                        'total_entries': len(data.get('items', data.get('authors', data.get('canonical_authors', [])))),
                        'last_updated': metadata.get('last_updated', 'unknown'),
                        'category': metadata.get('category', metadata.get('scoring', {}).get('category', 'unknown'))
                    })
            except Exception as e:
                logger.warning(f"Error reading {file_path.name}: {e}")
                continue
        
        return sorted(datasources, key=lambda x: x['source_name'])
    
    def get_datasource_schemas(self) -> Dict[str, Any]:
        """Return JSON schemas for different datasource types"""
        return {
            "award_book": {
                "description": "Award that recognizes specific books (e.g., Pulitzer Fiction, Booker Prize)",
                "example_files": ["pulitzer_fiction.json", "booker_prize.json"],
                "schema": {
                    "metadata": {
                        "source_name": "string (e.g., 'Pulitzer Prize for Fiction')",
                        "source_type": "string (must be 'award_book')",
                        "version": "string (e.g., '1.0')",
                        "created_date": "string (YYYY-MM-DD)",
                        "last_updated": "string (YYYY-MM-DD)",
                        "scoring": {
                            "category": "string (fiction/nonfiction/mixed)",
                            "recognition_type": "string (must be 'award')",
                            "qualifier_for_author_bonus": "boolean"
                        },
                        "established": "integer (year)",
                        "prize_amount": "string (optional)",
                        "category": "string (e.g., 'Fiction')",
                        "award_type": "string (must be 'book-specific')",
                        "total_winners": "integer",
                        "no_award_years": "array of integers (optional)"
                    },
                    "items": [
                        {
                            "title": "string (book title)",
                            "author": "string (author name)",
                            "year_awarded": "integer (year won)",
                            "year_published": "integer or null",
                            "notes": "string (optional, e.g., 'Shared', 'Declined')"
                        }
                    ]
                }
            },
            "award_career": {
                "description": "Award that recognizes an author's entire career (e.g., Nobel Prize)",
                "example_files": ["nobel_literature.json"],
                "schema": {
                    "metadata": {
                        "source_name": "string (e.g., 'Nobel Prize in Literature')",
                        "source_type": "string (must be 'award_career')",
                        "version": "string (e.g., '1.0')",
                        "created_date": "string (YYYY-MM-DD)",
                        "last_updated": "string (YYYY-MM-DD)",
                        "scoring": {
                            "category": "string (mixed)",
                            "recognition_type": "string (must be 'award')",
                            "qualifier_for_author_bonus": "boolean"
                        },
                        "established": "integer (year)",
                        "awarding_body": "string (optional)",
                        "prize_amount": "string (optional)",
                        "category": "string (e.g., 'Literature (career achievement)')",
                        "award_type": "string (must be 'author-career')",
                        "total_laureates": "integer",
                        "no_award_years": "array of integers (optional)"
                    },
                    "authors": [
                        {
                            "author": "string (author name)",
                            "year_awarded": "integer (year won)",
                            "country": "string",
                            "notes": "string (optional)"
                        }
                    ]
                }
            },
            "canonical_authors": {
                "description": "Curated list of canonical authors with their major works",
                "example_files": ["canonical_authors_tier_a.json", "canonical_authors_tier_b.json"],
                "schema": {
                    "metadata": {
                        "source_name": "string (e.g., 'Canonical Authors - Tier B')",
                        "source_type": "string (must be 'canonical_authors')",
                        "version": "string (e.g., '1.0')",
                        "created_date": "string (YYYY-MM-DD)",
                        "last_updated": "string (YYYY-MM-DD)",
                        "tier": "string (S/A/B)",
                        "scoring": {
                            "category": "string (mixed)",
                            "recognition_type": "string (must be 'author_quality')",
                            "canonical_baseline_points": "integer (15 for tier B)",
                            "tier_minimum_score": "integer (60 for tier B)",
                            "qualifier_for_author_bonus": "boolean"
                        },
                        "description": "string",
                        "total_authors": "integer",
                        "total_works": "integer"
                    },
                    "canonical_authors": [
                        {
                            "author": "string (author name)",
                            "lived": "string (e.g., '1899-1977')",
                            "nationality": "string",
                            "tier": "string (S/A/B)",
                            "genre": "string or null",
                            "works": [
                                {
                                    "title": "string (book title)",
                                    "year_published": "integer",
                                    "genre": "string (Novel/Poetry/Drama/etc.)",
                                    "notes": "string (optional)"
                                }
                            ],
                            "nobel_prize": "integer (year won, optional)"
                        }
                    ]
                }
            }
        }
    
    def add_award_winner(
        self,
        datasource_file: str,
        title: Optional[str] = None,
        author: str = None,
        year_awarded: int = None,
        year_published: Optional[int] = None,
        country: Optional[str] = None,
        notes: Optional[str] = ""
    ) -> Dict[str, Any]:
        """
        Add a new award winner to an existing datasource
        
        Args:
            datasource_file: Filename of the datasource (e.g., 'pulitzer_fiction.json')
            title: Book title (for book-specific awards)
            author: Author name
            year_awarded: Year the award was won
            year_published: Year the book was published (optional)
            country: Author's country (for career awards)
            notes: Optional notes (e.g., 'Shared', 'Declined')
        
        Returns:
            Dict with status and message
        """
        file_path = self.datasources_dir / datasource_file
        
        if not file_path.exists():
            return {
                'status': 'error',
                'message': f"Datasource file not found: {datasource_file}"
            }
        
        try:
            # Read existing data
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            metadata = data.get('metadata', {})
            award_type = metadata.get('award_type')
            
            # Validate required fields based on award type
            if award_type == 'book-specific':
                if not title or not author or not year_awarded:
                    return {
                        'status': 'error',
                        'message': 'Book-specific awards require: title, author, year_awarded'
                    }
                
                # Create new entry
                new_entry = {
                    'title': title,
                    'author': author,
                    'year_awarded': year_awarded,
                    'year_published': year_published,
                    'notes': notes or ""
                }
                
                # Check for duplicates
                items = data.get('items', [])
                for item in items:
                    if (item.get('title') == title and 
                        item.get('author') == author and 
                        item.get('year_awarded') == year_awarded):
                        return {
                            'status': 'error',
                            'message': f"Entry already exists: {title} by {author} ({year_awarded})"
                        }
                
                # Add new entry (insert in chronological order)
                items.append(new_entry)
                items.sort(key=lambda x: x['year_awarded'])
                data['items'] = items
                
            elif award_type == 'author-career':
                if not author or not year_awarded:
                    return {
                        'status': 'error',
                        'message': 'Career awards require: author, year_awarded, country'
                    }
                
                # Create new entry
                new_entry = {
                    'author': author,
                    'year_awarded': year_awarded,
                    'country': country or "",
                    'notes': notes or ""
                }
                
                # Check for duplicates
                authors = data.get('authors', [])
                for item in authors:
                    if item.get('author') == author and item.get('year_awarded') == year_awarded:
                        return {
                            'status': 'error',
                            'message': f"Entry already exists: {author} ({year_awarded})"
                        }
                
                # Add new entry (insert in chronological order)
                authors.append(new_entry)
                authors.sort(key=lambda x: x['year_awarded'])
                data['authors'] = authors
                
            else:
                return {
                    'status': 'error',
                    'message': f"Unknown award_type: {award_type}"
                }
            
            # Update metadata
            metadata['last_updated'] = datetime.now().strftime('%Y-%m-%d')
            if award_type == 'book-specific':
                metadata['total_winners'] = len(data.get('items', []))
            else:
                metadata['total_laureates'] = len(data.get('authors', []))
            
            data['metadata'] = metadata
            
            # Write back to file
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Added entry to {datasource_file}: {author}")
            
            return {
                'status': 'success',
                'message': f"Successfully added {author} to {metadata.get('source_name')}",
                'entry': new_entry,
                'datasource': datasource_file
            }
            
        except Exception as e:
            logger.error(f"Error adding award winner: {e}", exc_info=True)
            return {
                'status': 'error',
                'message': f"Error: {str(e)}"
            }
    
    def add_canonical_author(
        self,
        tier: str,
        author: str,
        lived: str,
        nationality: str,
        works: List[Dict[str, Any]],
        genre: Optional[str] = None,
        nobel_prize: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Add a new canonical author to the appropriate tier file
        
        Args:
            tier: Author tier (S, A, or B)
            author: Author name
            lived: Life years (e.g., "1899-1977")
            nationality: Author's nationality
            works: List of works, each with: title, year_published, genre, notes (optional)
            genre: Primary genre (optional)
            nobel_prize: Year of Nobel Prize if applicable (optional)
        
        Returns:
            Dict with status and message
        """
        tier = tier.upper()
        if tier not in ['S', 'A', 'B']:
            return {
                'status': 'error',
                'message': f"Invalid tier: {tier}. Must be S, A, or B"
            }
        
        filename = f"canonical_authors_tier_{tier.lower()}.json"
        file_path = self.datasources_dir / filename
        
        if not file_path.exists():
            return {
                'status': 'error',
                'message': f"Canonical authors file not found: {filename}"
            }
        
        try:
            # Read existing data
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Check for duplicate
            canonical_authors = data.get('canonical_authors', [])
            for existing_author in canonical_authors:
                if existing_author.get('author') == author:
                    return {
                        'status': 'error',
                        'message': f"Author already exists in {filename}: {author}"
                    }
            
            # Validate works structure
            if not works or not isinstance(works, list):
                return {
                    'status': 'error',
                    'message': "Works must be a non-empty list"
                }
            
            for work in works:
                if 'title' not in work or 'year_published' not in work or 'genre' not in work:
                    return {
                        'status': 'error',
                        'message': "Each work must have: title, year_published, genre"
                    }
            
            # Create new author entry
            new_author = {
                'author': author,
                'lived': lived,
                'nationality': nationality,
                'tier': tier,
                'genre': genre,
                'works': works
            }
            
            if nobel_prize:
                new_author['nobel_prize'] = nobel_prize
            
            # Add to list (alphabetically by author name)
            canonical_authors.append(new_author)
            canonical_authors.sort(key=lambda x: x['author'])
            data['canonical_authors'] = canonical_authors
            
            # Update metadata
            metadata = data.get('metadata', {})
            metadata['last_updated'] = datetime.now().strftime('%Y-%m-%d')
            metadata['total_authors'] = len(canonical_authors)
            metadata['total_works'] = sum(len(a.get('works', [])) for a in canonical_authors)
            data['metadata'] = metadata
            
            # Write back to file
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Added canonical author to {filename}: {author}")
            
            return {
                'status': 'success',
                'message': f"Successfully added {author} to Tier {tier} canonical authors",
                'entry': new_author,
                'datasource': filename,
                'total_works': len(works)
            }
            
        except Exception as e:
            logger.error(f"Error adding canonical author: {e}", exc_info=True)
            return {
                'status': 'error',
                'message': f"Error: {str(e)}"
            }
    
    def get_datasource_info(self, datasource_file: str) -> Dict[str, Any]:
        """Get detailed information about a specific datasource"""
        file_path = self.datasources_dir / datasource_file
        
        if not file_path.exists():
            return {
                'status': 'error',
                'message': f"Datasource file not found: {datasource_file}"
            }
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            metadata = data.get('metadata', {})
            
            # Count entries
            if 'items' in data:
                entries = data['items']
                entry_type = 'books'
            elif 'authors' in data:
                entries = data['authors']
                entry_type = 'authors'
            elif 'canonical_authors' in data:
                entries = data['canonical_authors']
                entry_type = 'canonical_authors'
            else:
                entries = []
                entry_type = 'unknown'
            
            return {
                'status': 'success',
                'filename': datasource_file,
                'metadata': metadata,
                'entry_type': entry_type,
                'total_entries': len(entries),
                'recent_entries': entries[-5:] if len(entries) > 5 else entries
            }
            
        except Exception as e:
            logger.error(f"Error reading datasource: {e}", exc_info=True)
            return {
                'status': 'error',
                'message': f"Error: {str(e)}"
            }


