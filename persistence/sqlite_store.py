"""
SQLite implementation for Recall Memory storage.
"""
import sqlite3
from typing import List, Dict, Any, Optional
from datetime import datetime
import json
from .storage_interface import RecallStorage


class SQLiteRecallStorage(RecallStorage):
    """
    SQLite-based storage for conversation history and recall memory.
    """

    def __init__(self, db_path: str = "memgpt.db"):
        """
        Initialize SQLite storage.

        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._initialize_database()

    def _initialize_database(self):
        """Create the necessary tables if they don't exist."""
        cursor = self.conn.cursor()

        # Create message_history table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS message_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                summary_id INTEGER,
                metadata TEXT
            )
        """)

        # Create index for faster searches
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_timestamp
            ON message_history(timestamp DESC)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_role
            ON message_history(role)
        """)

        self.conn.commit()

    def insert_message(self, role: str, content: str, timestamp: Optional[datetime] = None,
                      summary_id: Optional[int] = None, metadata: Optional[Dict[str, Any]] = None) -> int:
        """
        Insert a message into the recall storage.

        Args:
            role: Role of the message sender (user, assistant, system, function)
            content: Content of the message
            timestamp: Message timestamp (defaults to now)
            summary_id: Optional ID linking to a summary
            metadata: Optional metadata dictionary

        Returns:
            ID of the inserted message
        """
        cursor = self.conn.cursor()

        metadata_json = json.dumps(metadata) if metadata else None

        if timestamp is None:
            cursor.execute("""
                INSERT INTO message_history (role, content, summary_id, metadata)
                VALUES (?, ?, ?, ?)
            """, (role, content, summary_id, metadata_json))
        else:
            cursor.execute("""
                INSERT INTO message_history (role, content, timestamp, summary_id, metadata)
                VALUES (?, ?, ?, ?, ?)
            """, (role, content, timestamp, summary_id, metadata_json))

        self.conn.commit()
        return cursor.lastrowid

    def search_messages(self, query: str, limit: int = 10, offset: int = 0) -> List[Dict[str, Any]]:
        """
        Search messages by text content using LIKE query.

        Args:
            query: Search query string
            limit: Maximum number of results to return
            offset: Number of results to skip (for pagination)

        Returns:
            List of message dictionaries matching the query
        """
        cursor = self.conn.cursor()

        cursor.execute("""
            SELECT id, role, content, timestamp, summary_id, metadata
            FROM message_history
            WHERE content LIKE ?
            ORDER BY timestamp DESC
            LIMIT ? OFFSET ?
        """, (f"%{query}%", limit, offset))

        results = []
        for row in cursor.fetchall():
            message = dict(row)
            if message['metadata']:
                message['metadata'] = json.loads(message['metadata'])
            results.append(message)

        return results

    def get_recent_messages(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Retrieve the most recent messages.

        Args:
            limit: Maximum number of messages to retrieve

        Returns:
            List of recent message dictionaries
        """
        cursor = self.conn.cursor()

        cursor.execute("""
            SELECT id, role, content, timestamp, summary_id, metadata
            FROM message_history
            ORDER BY timestamp DESC
            LIMIT ?
        """, (limit,))

        results = []
        for row in cursor.fetchall():
            message = dict(row)
            if message['metadata']:
                message['metadata'] = json.loads(message['metadata'])
            results.append(message)

        # Reverse to get chronological order
        return list(reversed(results))

    def get_all_messages(self) -> List[Dict[str, Any]]:
        """
        Retrieve all messages from storage.

        Returns:
            List of all message dictionaries
        """
        cursor = self.conn.cursor()

        cursor.execute("""
            SELECT id, role, content, timestamp, summary_id, metadata
            FROM message_history
            ORDER BY timestamp ASC
        """)

        results = []
        for row in cursor.fetchall():
            message = dict(row)
            if message['metadata']:
                message['metadata'] = json.loads(message['metadata'])
            results.append(message)

        return results

    def delete_message(self, message_id: int) -> bool:
        """
        Delete a specific message.

        Args:
            message_id: ID of the message to delete

        Returns:
            True if successful, False otherwise
        """
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM message_history WHERE id = ?", (message_id,))
        self.conn.commit()
        return cursor.rowcount > 0

    def clear_all(self):
        """Delete all messages from storage."""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM message_history")
        self.conn.commit()

    def close(self):
        """Close the database connection."""
        if self.conn:
            self.conn.close()

    def __del__(self):
        """Ensure connection is closed on deletion."""
        self.close()
