#!/usr/bin/env python3
"""
Semantic Book Search
Search your enriched book library using natural language queries.

Usage:
    python3 src/dataenrichment/search_books.py "books about social justice"
"""

import sys
import chromadb
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from src.config.settings import settings


def search_books(query, n_results=5, min_quality_score=0):
    """
    Search books using semantic similarity.
    
    Args:
        query: Natural language search query
        n_results: Number of results to return
        min_quality_score: Minimum quality score filter
    """
    # Initialize OpenAI
    from openai import OpenAI
    
    if not settings.OPENAI_API_KEY:
        print("❌ OpenAI API key not found in .env file")
        return
    
    openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
    
    # Generate query embedding using same model as books
    print(f"🔍 Searching for: \"{query}\"")
    print("-" * 80)
    
    response = openai_client.embeddings.create(
        model="text-embedding-3-large",
        input=query
    )
    query_embedding = response.data[0].embedding
    
    # Search ChromaDB (expand ~ in path)
    import os
    chromadb_path = os.path.expanduser(settings.CHROMADB_PATH)
    client = chromadb.PersistentClient(path=chromadb_path)
    
    try:
        collection = client.get_collection("book_metadata_embeddings")
    except Exception:
        print("❌ ChromaDB collection not found")
        print("   Run enrichment first: python3 src/dataenrichment/enrich_books.py")
        return
    
    # Query with quality filter if specified
    where_filter = None
    if min_quality_score > 0:
        where_filter = {"quality_score": {"$gte": min_quality_score}}
    
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results,
        where=where_filter,
        include=['metadatas', 'distances']
    )
    
    if not results['metadatas'][0]:
        print("No results found.")
        return
    
    print(f"\nFound {len(results['metadatas'][0])} results:")
    print()
    
    for i, (meta, distance) in enumerate(zip(results['metadatas'][0], results['distances'][0]), 1):
        similarity = 1 - distance
        
        print(f"{i}. {meta['title']}")
        print(f"   by {meta['author']}")
        print(f"   Quality Score: {meta['quality_score']} | Similarity: {similarity:.3f}")
        print(f"   {meta.get('description', meta.get('enhanced_description', 'No description'))}")
        
        # Parse and display tags (pipe-separated format from ChromaDB)
        tags_str = meta.get('tags', '')
        if tags_str:
            tags = [t.strip() for t in tags_str.split('|') if t.strip()]
            if tags:
                print(f"   Tags: {', '.join(tags[:5])}{'...' if len(tags) > 5 else ''}")
        
        # Parse and display themes (pipe-separated format from ChromaDB)
        themes_str = meta.get('themes', '')
        if themes_str:
            themes = [t.strip() for t in themes_str.split('|') if t.strip()]
            if themes:
                print(f"   Themes: {', '.join(themes[:3])}")
        
        print()


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Search your book library using natural language",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 src/dataenrichment/search_books.py "books about social justice"
  python3 src/dataenrichment/search_books.py "romantic classics" --results 3
  python3 src/dataenrichment/search_books.py "war stories" --min-score 70
        """
    )
    
    parser.add_argument(
        'query',
        help='Natural language search query'
    )
    
    parser.add_argument(
        '-n', '--results',
        type=int,
        default=5,
        help='Number of results to return (default: 5)'
    )
    
    parser.add_argument(
        '--min-score',
        type=float,
        default=0,
        help='Minimum quality score filter (default: 0 = all)'
    )
    
    args = parser.parse_args()
    
    try:
        search_books(args.query, n_results=args.results, min_quality_score=args.min_score)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()

