"""
ChromaDB implementation for Archival Memory storage with embeddings.
"""
import chromadb
from chromadb.config import Settings
from typing import List, Dict, Any, Optional
from sentence_transformers import SentenceTransformer
import uuid
from .storage_interface import ArchivalStorage


class ChromaArchivalStorage(ArchivalStorage):
    """
    ChromaDB-based storage for archival memory with semantic search.
    Uses sentence-transformers for local embedding generation.
    """

    def __init__(self, persist_directory: str = "./data/chroma",
                 collection_name: str = "archival_memory",
                 embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"):
        """
        Initialize ChromaDB storage.

        Args:
            persist_directory: Directory to persist ChromaDB data
            collection_name: Name of the ChromaDB collection
            embedding_model: Name of the sentence-transformers model
        """
        self.persist_directory = persist_directory
        self.collection_name = collection_name

        # Initialize ChromaDB client with persistent storage
        try:
            # Try newer API (0.4.0+)
            self.client = chromadb.PersistentClient(path=persist_directory)
        except AttributeError:
            # Fallback for older API
            self.client = chromadb.Client(Settings(
                persist_directory=persist_directory,
                anonymized_telemetry=False
            ))

        # Initialize embedding model
        self.embedding_model = SentenceTransformer(embedding_model)

        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"description": "Archival memory for MemGPT"}
        )

    def _generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for a text using sentence-transformers.

        Args:
            text: Text to embed

        Returns:
            Embedding vector as a list of floats
        """
        embedding = self.embedding_model.encode(text, convert_to_numpy=True)
        return embedding.tolist()

    def insert(self, content: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Insert a document into archival storage with embedding.

        Args:
            content: Text content to store
            metadata: Optional metadata dictionary

        Returns:
            ID of the inserted document
        """
        # Generate unique ID
        doc_id = str(uuid.uuid4())

        # Generate embedding
        embedding = self._generate_embedding(content)

        # Prepare metadata
        if metadata is None:
            metadata = {}
        metadata['content_length'] = len(content)

        # Insert into ChromaDB
        self.collection.add(
            ids=[doc_id],
            embeddings=[embedding],
            documents=[content],
            metadatas=[metadata]
        )

        return doc_id

    def search(self, query: str, limit: int = 5, offset: int = 0) -> List[Dict[str, Any]]:
        """
        Search documents by semantic similarity.

        Args:
            query: Search query string
            limit: Maximum number of results to return (page size)
            offset: Number of results to skip (for pagination)

        Returns:
            List of matching document dictionaries with similarity scores
        """
        # Generate query embedding
        query_embedding = self._generate_embedding(query)

        # Calculate total results needed (offset + limit)
        n_results = offset + limit

        # Query ChromaDB
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=min(n_results, self.collection.count())
        )

        # Process results
        documents = []
        if results['ids'] and len(results['ids'][0]) > 0:
            ids = results['ids'][0]
            docs = results['documents'][0]
            metadatas = results['metadatas'][0]
            distances = results['distances'][0]

            # Apply pagination by slicing
            for i in range(offset, min(len(ids), offset + limit)):
                doc = {
                    'id': ids[i],
                    'content': docs[i],
                    'metadata': metadatas[i] if metadatas[i] else {},
                    'similarity': 1.0 - distances[i]  # Convert distance to similarity
                }
                documents.append(doc)

        return documents

    def get_all_documents(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Retrieve all documents from storage.

        Args:
            limit: Optional maximum number of documents to retrieve

        Returns:
            List of all document dictionaries
        """
        # Get all documents
        results = self.collection.get()

        documents = []
        if results['ids']:
            ids = results['ids']
            docs = results['documents']
            metadatas = results['metadatas']

            max_items = len(ids) if limit is None else min(limit, len(ids))

            for i in range(max_items):
                doc = {
                    'id': ids[i],
                    'content': docs[i],
                    'metadata': metadatas[i] if metadatas[i] else {}
                }
                documents.append(doc)

        return documents

    def delete(self, doc_id: str) -> bool:
        """
        Delete a document from storage.

        Args:
            doc_id: ID of the document to delete

        Returns:
            True if successful, False otherwise
        """
        try:
            self.collection.delete(ids=[doc_id])
            return True
        except Exception:
            return False

    def clear_all(self):
        """Delete all documents from the collection."""
        # Delete and recreate collection
        self.client.delete_collection(self.collection_name)
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"description": "Archival memory for MemGPT"}
        )

    def get_count(self) -> int:
        """
        Get the total number of documents in storage.

        Returns:
            Number of documents
        """
        return self.collection.count()
