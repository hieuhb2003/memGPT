"""
Abstract base classes for storage backends.
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime


class RecallStorage(ABC):
    """
    Abstract interface for Recall Memory storage.
    Stores the complete history of messages for text-based search.
    """

    @abstractmethod
    def insert_message(self, role: str, content: str, timestamp: Optional[datetime] = None,
                      summary_id: Optional[int] = None) -> int:
        """
        Insert a message into the recall storage.

        Args:
            role: Role of the message sender (user, assistant, system, function)
            content: Content of the message
            timestamp: Message timestamp (defaults to now)
            summary_id: Optional ID linking to a summary

        Returns:
            ID of the inserted message
        """
        pass

    @abstractmethod
    def search_messages(self, query: str, limit: int = 10, offset: int = 0) -> List[Dict[str, Any]]:
        """
        Search messages by text content.

        Args:
            query: Search query string
            limit: Maximum number of results to return
            offset: Number of results to skip (for pagination)

        Returns:
            List of message dictionaries matching the query
        """
        pass

    @abstractmethod
    def get_recent_messages(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Retrieve the most recent messages.

        Args:
            limit: Maximum number of messages to retrieve

        Returns:
            List of recent message dictionaries
        """
        pass

    @abstractmethod
    def get_all_messages(self) -> List[Dict[str, Any]]:
        """
        Retrieve all messages from storage.

        Returns:
            List of all message dictionaries
        """
        pass


class ArchivalStorage(ABC):
    """
    Abstract interface for Archival Memory storage.
    Stores documents with embeddings for semantic search (RAG).
    """

    @abstractmethod
    def insert(self, content: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Insert a document into archival storage with embedding.

        Args:
            content: Text content to store
            metadata: Optional metadata dictionary

        Returns:
            ID of the inserted document
        """
        pass

    @abstractmethod
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
        pass

    @abstractmethod
    def get_all_documents(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Retrieve all documents from storage.

        Args:
            limit: Optional maximum number of documents to retrieve

        Returns:
            List of all document dictionaries
        """
        pass

    @abstractmethod
    def delete(self, doc_id: str) -> bool:
        """
        Delete a document from storage.

        Args:
            doc_id: ID of the document to delete

        Returns:
            True if successful, False otherwise
        """
        pass
