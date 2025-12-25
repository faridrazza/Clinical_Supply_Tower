"""
ChromaDB Schema Manager with OpenAI Embeddings.

Uses OpenAI's embedding model to convert table schemas to vectors
and store them in ChromaDB for semantic search.
"""
import os
import logging
from typing import Dict, List, Any, Optional
import chromadb
from openai import OpenAI

from src.utils.schema_registry import TABLE_SCHEMAS, get_all_table_names
from src.config.settings import settings

logger = logging.getLogger(__name__)


class ChromaSchemaManagerOpenAI:
    """
    ChromaDB Schema Manager using OpenAI embeddings.
    
    Features:
    - Uses OpenAI's text-embedding-3-small model
    - Converts table schemas to embedding vectors
    - Stores embeddings in ChromaDB
    - Enables semantic search across all 40 tables
    """
    
    def __init__(
        self,
        persist_dir: str = "./chroma_db",
        openai_api_key: Optional[str] = None,
        embedding_model: str = "text-embedding-3-small"
    ):
        """
        Initialize ChromaDB with OpenAI embeddings.
        
        Args:
            persist_dir: Directory to persist ChromaDB data
            openai_api_key: OpenAI API key (uses env var if not provided)
            embedding_model: OpenAI embedding model to use
        """
        self.persist_dir = persist_dir
        self.collection_name = "table_schemas_openai"
        self.embedding_model = embedding_model
        
        # Initialize OpenAI client
        # Priority: explicit parameter > settings > environment variable
        api_key = openai_api_key or settings.openai_api_key or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError(
                "OpenAI API key not found. Set OPENAI_API_KEY in .env file or environment variable."
            )
        
        self.openai_client = OpenAI(api_key=api_key)
        logger.info(f"OpenAI client initialized with model: {embedding_model}")
        logger.info(f"API key loaded from: {'parameter' if openai_api_key else 'settings' if settings.openai_api_key else 'environment'}")
        
        # Initialize ChromaDB with new API (no Settings needed)
        self.client = chromadb.PersistentClient(path=persist_dir)
        self.collection = None
        self._initialize_collection()
    
    def _initialize_collection(self):
        """Initialize or get ChromaDB collection."""
        try:
            # Try to get existing collection
            self.collection = self.client.get_collection(
                name=self.collection_name
            )
            logger.info(
                f"Loaded existing ChromaDB collection with "
                f"{self.collection.count()} embeddings"
            )
        except Exception as e:
            logger.info(f"Creating new ChromaDB collection: {e}")
            # Create new collection
            self.collection = self.client.create_collection(
                name=self.collection_name
            )
            # Populate with table schemas
            self._populate_schemas()
    
    def _populate_schemas(self):
        """Populate ChromaDB with all table schemas using OpenAI embeddings."""
        logger.info("Populating ChromaDB with table schemas (OpenAI embeddings)...")
        
        documents = []
        metadatas = []
        ids = []
        
        # Create documents for all tables
        for table_name, schema_info in TABLE_SCHEMAS.items():
            doc = self._create_schema_document(table_name, schema_info)
            documents.append(doc)
            
            metadata = {
                "table_name": table_name,
                "business_purpose": schema_info.get("business_purpose", ""),
                "workflow": ",".join(schema_info.get("workflow", [])),
                "column_count": len(schema_info.get("key_columns", []))
            }
            metadatas.append(metadata)
            ids.append(table_name)
        
        logger.info(f"Created {len(documents)} schema documents")
        
        # Generate embeddings using OpenAI
        logger.info("Generating OpenAI embeddings...")
        embeddings = self._generate_embeddings(documents)
        
        if not embeddings:
            raise ValueError("Failed to generate embeddings")
        
        logger.info(f"Generated {len(embeddings)} embeddings")
        
        # Add to ChromaDB with embeddings
        self.collection.add(
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas,
            ids=ids
        )
        
        logger.info(f"✓ Populated ChromaDB with {len(documents)} table schemas")
    
    def _create_schema_document(self, table_name: str, schema_info: Dict) -> str:
        """
        Create a comprehensive document for a table schema.
        
        This document is converted to embeddings for semantic search.
        
        Args:
            table_name: Name of the table
            schema_info: Schema information dictionary
            
        Returns:
            Formatted document string
        """
        parts = [
            f"Table: {table_name}",
            f"Purpose: {schema_info.get('business_purpose', '')}",
            "Columns:"
        ]
        
        # Add column information
        for col in schema_info.get("key_columns", []):
            parts.append(f"  {col['name']} ({col['type']}): {col['description']}")
        
        # Add workflow context
        workflows = schema_info.get("workflow", [])
        if workflows:
            parts.append(f"Used in workflows: {', '.join(workflows)}")
        
        return "\n".join(parts)
    
    def _generate_embeddings(self, documents: List[str]) -> List[List[float]]:
        """
        Generate embeddings for documents using OpenAI.
        
        Args:
            documents: List of text documents
            
        Returns:
            List of embedding vectors
        """
        try:
            logger.info(f"Generating embeddings for {len(documents)} documents...")
            
            # Call OpenAI embedding API
            response = self.openai_client.embeddings.create(
                model=self.embedding_model,
                input=documents
            )
            
            # Extract embeddings
            embeddings = [item.embedding for item in response.data]
            
            logger.info(
                f"✓ Generated {len(embeddings)} embeddings "
                f"(dimension: {len(embeddings[0])})"
            )
            
            return embeddings
        except Exception as e:
            logger.error(f"Failed to generate embeddings: {e}")
            raise
    
    def find_relevant_tables(
        self,
        query: str,
        n_results: int = 5,
        workflow: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Find relevant tables for a query using semantic search.
        
        Args:
            query: Natural language query
            n_results: Number of results to return
            workflow: Optional workflow filter ("A" or "B")
            
        Returns:
            List of relevant tables with scores
        """
        try:
            # Generate embedding for query
            logger.info(f"Generating embedding for query: {query[:50]}...")
            query_embedding = self._generate_embeddings([query])[0]
            
            # Query ChromaDB
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where=self._build_where_clause(workflow) if workflow else None
            )
            
            # Format results
            tables = []
            if results and results["ids"] and len(results["ids"]) > 0:
                for i, table_id in enumerate(results["ids"][0]):
                    distance = results["distances"][0][i] if results["distances"] else 0
                    # Convert distance to similarity score (0-1, higher is better)
                    similarity = 1 - (distance / 2)  # Normalize for cosine distance
                    
                    metadata = results["metadatas"][0][i] if results["metadatas"] else {}
                    
                    tables.append({
                        "table_name": table_id,
                        "similarity_score": max(0, similarity),
                        "business_purpose": metadata.get("business_purpose", ""),
                        "workflow": metadata.get("workflow", ""),
                        "column_count": metadata.get("column_count", 0)
                    })
            
            logger.info(f"Found {len(tables)} relevant tables")
            return tables
        
        except Exception as e:
            logger.error(f"Error querying ChromaDB: {e}")
            raise
    
    def _build_where_clause(self, workflow: str) -> Dict[str, Any]:
        """Build ChromaDB where clause for workflow filtering."""
        return {
            "workflow": {"$in": [workflow]}
        }
    
    def get_table_schema_document(self, table_name: str) -> Optional[str]:
        """
        Get the schema document for a specific table.
        
        Args:
            table_name: Name of the table
            
        Returns:
            Schema document or None if not found
        """
        try:
            result = self.collection.get(ids=[table_name])
            if result and result["documents"] and len(result["documents"]) > 0:
                return result["documents"][0]
            return None
        except Exception as e:
            logger.error(f"Error retrieving schema document for {table_name}: {e}")
            return None
    
    def refresh_schemas(self):
        """Refresh ChromaDB with latest schemas from registry."""
        try:
            logger.info("Refreshing ChromaDB schemas...")
            # Delete existing collection
            self.client.delete_collection(name=self.collection_name)
            logger.info("Deleted existing ChromaDB collection")
            
            # Reinitialize
            self._initialize_collection()
            logger.info("✓ Refreshed ChromaDB with latest schemas")
        except Exception as e:
            logger.error(f"Error refreshing schemas: {e}")
            raise
    
    def get_all_tables(self) -> List[str]:
        """Get all table names in ChromaDB."""
        try:
            result = self.collection.get()
            return result["ids"] if result and result["ids"] else []
        except Exception as e:
            logger.error(f"Error getting all tables: {e}")
            return []
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the ChromaDB collection."""
        try:
            count = self.collection.count()
            return {
                "collection_name": self.collection_name,
                "total_tables": count,
                "persist_directory": self.persist_dir,
                "embedding_model": self.embedding_model,
                "embedding_dimension": 1536  # text-embedding-3-small dimension
            }
        except Exception as e:
            logger.error(f"Error getting collection stats: {e}")
            return {}


# Global instance
_chroma_manager_openai: Optional[ChromaSchemaManagerOpenAI] = None


def get_chroma_manager_openai(
    persist_dir: str = "./chroma_db",
    openai_api_key: Optional[str] = None
) -> ChromaSchemaManagerOpenAI:
    """
    Get or create global ChromaDB manager instance with OpenAI embeddings.
    
    Args:
        persist_dir: Directory to persist ChromaDB data
        openai_api_key: OpenAI API key (uses env var if not provided)
        
    Returns:
        ChromaSchemaManagerOpenAI instance
    """
    global _chroma_manager_openai
    
    if _chroma_manager_openai is None:
        _chroma_manager_openai = ChromaSchemaManagerOpenAI(
            persist_dir=persist_dir,
            openai_api_key=openai_api_key
        )
    
    return _chroma_manager_openai
