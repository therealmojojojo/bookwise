"""
Vector search service using ChromaDB for semantic book search
"""
import chromadb
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class VectorSearchService:
    """Handles ChromaDB interactions for semantic search"""
    
    def __init__(self, chromadb_path: str, openai_api_key: str):
        """
        Initialize ChromaDB client and OpenAI for embedding generation
        
        Args:
            chromadb_path: Path to ChromaDB persistent storage
            openai_api_key: OpenAI API key for generating query embeddings
        """
        self.client = chromadb.PersistentClient(path=chromadb_path)
        
        # Initialize OpenAI client for embedding generation
        try:
            from openai import OpenAI
            self.openai_client = OpenAI(api_key=openai_api_key)
            logger.info("✓ OpenAI client initialized for embedding generation")
        except ImportError:
            logger.error("openai package not installed")
            raise
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {e}")
            raise
        
        try:
            # Get the collection (no embedding function - we'll generate embeddings manually)
            self.collection = self.client.get_collection("book_metadata_embeddings")
            logger.info(f"Connected to ChromaDB collection with {self.collection.count()} books")
        except Exception as e:
            logger.error(f"Failed to connect to ChromaDB: {e}")
            raise
    
    def _generate_query_embedding(self, query_text: str) -> List[float]:
        """
        Generate embedding for a query using OpenAI API
        
        Args:
            query_text: The search query text
            
        Returns:
            3072-dimensional embedding vector
        """
        try:
            response = self.openai_client.embeddings.create(
                model="text-embedding-3-large",  # Same model as enrichment
                input=query_text
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Failed to generate embedding for query: {e}")
            raise
    
    async def multi_query_search(
        self, 
        queries: List[str], 
        n_results_per_query: int = 20
    ) -> List[Dict]:
        """
        Execute multiple semantic queries and combine results with OR logic
        
        Args:
            queries: List of search queries (1-5 recommended)
            n_results_per_query: Number of results to fetch per query
            
        Returns:
            List of dicts with book_id, title, author, similarity, distance
        """
        all_results = {}
        
        logger.info(f"Executing multi-query search with {len(queries)} queries")
        
        for query in queries:
            try:
                # Generate embedding for this query
                logger.debug(f"Generating embedding for query: '{query}'")
                query_embedding = self._generate_query_embedding(query)
                
                # Query using pre-computed embedding
                results = self.collection.query(
                    query_embeddings=[query_embedding],  # Use pre-computed embeddings
                    n_results=n_results_per_query,
                    include=['metadatas', 'distances']
                )
                
                # Extract results
                if results['ids'] and len(results['ids']) > 0:
                    for book_id, metadata, distance in zip(
                        results['ids'][0],
                        results['metadatas'][0],
                        results['distances'][0]
                    ):
                        # Keep best similarity score per book (lowest distance)
                        if book_id not in all_results or distance < all_results[book_id]['distance']:
                            all_results[book_id] = {
                                'book_id': int(book_id),
                                'title': metadata.get('title', 'Unknown'),
                                'author': metadata.get('author', 'Unknown'),
                                'quality_score': metadata.get('quality_score', 0),
                                'awards': metadata.get('awards', ''),
                                'distance': distance,
                                'similarity': 1 - min(distance, 1.0)  # Convert to similarity [0-1]
                            }
                
                logger.debug(f"Query '{query}' returned {len(results['ids'][0]) if results['ids'] else 0} results")
                
            except Exception as e:
                logger.error(f"Error executing query '{query}': {e}")
                continue
        
        # Sort by similarity (highest first)
        sorted_results = sorted(
            all_results.values(), 
            key=lambda x: x['similarity'], 
            reverse=True
        )
        
        logger.info(f"Multi-query search found {len(sorted_results)} unique books")
        return sorted_results
    
    async def simple_search(self, query: str, n_results: int = 20) -> List[Dict]:
        """
        Execute a single semantic query
        
        Args:
            query: Search query
            n_results: Number of results to return
            
        Returns:
            List of book results
        """
        return await self.multi_query_search([query], n_results_per_query=n_results)
    
    async def get_book_metadata(self, book_id: int) -> Optional[Dict]:
        """
        Get book metadata from ChromaDB by book ID
        
        Args:
            book_id: Calibre book ID
            
        Returns:
            Dict with quality_score, awards, tags, themes, description, or None if not found
        """
        try:
            result = self.collection.get(
                ids=[str(book_id)],
                include=['metadatas']
            )
            
            if result['ids'] and len(result['ids']) > 0:
                metadata = result['metadatas'][0]

                # Convert pipe-separated strings back to lists
                tags_str = metadata.get('tags', '')
                themes_str = metadata.get('themes', '')

                return {
                    'quality_score': int(metadata.get('quality_score', 0)),
                    'awards': metadata.get('awards', ''),
                    'tags': tags_str.split('|') if tags_str else [],
                    'themes': themes_str.split('|') if themes_str else [],
                    'description': metadata.get('description', ''),
                    'publication_year': metadata.get('publication_year', '')
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error fetching metadata for book {book_id}: {e}")
            return None

