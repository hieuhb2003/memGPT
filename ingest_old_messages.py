"""
Script to ingest old conversation messages into MemGPT's recall memory (SQLite database)
"""

import json
from datetime import datetime
from persistence.sqlite_store import SQLiteRecallStorage
from persistence.chroma_store import ChromaArchivalStorage


def ingest_messages_to_recall(old_sessions, db_path="memgpt.db"):
    """
    Ingest old messages into SQLite recall memory

    Args:
        old_sessions: List of message dictionaries with 'role', 'content', 'timestamp'
        db_path: Path to SQLite database file
    """
    print(f"Initializing SQLite recall storage at: {db_path}")
    recall_storage = SQLiteRecallStorage(db_path=db_path)

    print(f"\nIngesting {len(old_sessions)} messages...")
    for i, message in enumerate(old_sessions, 1):
        role = message.get("role", "user")
        content = message.get("content", "")
        timestamp_str = message.get("timestamp", None)

        # Parse timestamp if provided
        timestamp = None
        if timestamp_str:
            try:
                timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                print(f"Warning: Invalid timestamp format for message {i}: {timestamp_str}")
                timestamp = None

        # Add metadata if any additional fields exist
        metadata = {}
        for key, value in message.items():
            if key not in ["role", "content", "timestamp"]:
                metadata[key] = value

        # Insert message
        recall_storage.insert_message(
            role=role,
            content=content,
            timestamp=timestamp,
            metadata=metadata if metadata else None
        )
        print(f"  [{i}/{len(old_sessions)}] Inserted {role} message: {content[:50]}...")

    print(f"\n✓ Successfully ingested {len(old_sessions)} messages to recall memory")
    return recall_storage


def ingest_sessions_to_archival(old_sessions, chroma_path="./data/chroma", collection_name="archival_memory"):
    """
    Ingest old sessions as complete transcripts into ChromaDB archival memory

    Args:
        old_sessions: List of message dictionaries with 'role', 'content', 'timestamp'
        chroma_path: Path to ChromaDB persistent directory
        collection_name: Name of the ChromaDB collection
    """
    print(f"\nInitializing ChromaDB archival storage at: {chroma_path}")
    archival_storage = ChromaArchivalStorage(
        persist_directory=chroma_path,
        collection_name=collection_name
    )

    # Create a transcript of the entire session
    transcript_parts = []
    for message in old_sessions:
        role = message.get("role", "user")
        content = message.get("content", "")
        timestamp = message.get("timestamp", "")

        transcript_parts.append(f"[{timestamp}] {role.upper()}: {content}")

    transcript = "\n".join(transcript_parts)

    # Insert as a single document
    print(f"\nIngesting session transcript ({len(old_sessions)} messages) to archival memory...")
    doc_id = archival_storage.insert(
        content=transcript,
        metadata={
            "type": "old_session",
            "message_count": len(old_sessions),
            "imported_at": datetime.now().isoformat()
        }
    )

    print(f"✓ Successfully ingested session to archival memory (doc_id: {doc_id})")
    return archival_storage


def load_sessions_from_file(json_file_path):
    """
    Load old sessions from a JSON file

    Args:
        json_file_path: Path to JSON file containing sessions

    Returns:
        List of message dictionaries
    """
    with open(json_file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data


def main():
    """
    Main function to demonstrate ingestion of old messages
    """
    # Example old_sessions data
    old_sessions = [
        {
            "role": "user",
            "content": "Dự án MemGPT này cần chạy local hoàn toàn nhé.",
            "timestamp": "2024-01-15 09:00:00"
        },
        {
            "role": "assistant",
            "content": "Đã rõ. Tôi sẽ sử dụng SQLite và ChromaDB.",
            "timestamp": "2024-01-15 09:00:05"
        },
        {
            "role": "user",
            "content": "Nhớ là không dùng Docker.",
            "timestamp": "2024-01-15 09:01:00"
        }
    ]

    print("=" * 70)
    print("MemGPT Old Message Ingestion Script")
    print("=" * 70)

    # Option 1: Ingest to recall memory (SQLite - for searchable conversation history)
    print("\n[OPTION 1] Ingesting to Recall Memory (SQLite)")
    print("-" * 70)
    recall_storage = ingest_messages_to_recall(old_sessions, db_path="memgpt.db")

    # Verify ingestion
    print("\nVerifying ingestion...")
    all_messages = recall_storage.get_all_messages()
    print(f"Total messages in database: {len(all_messages)}")

    # Option 2: Ingest to archival memory (ChromaDB - for semantic search)
    print("\n" + "=" * 70)
    print("[OPTION 2] Ingesting to Archival Memory (ChromaDB)")
    print("-" * 70)
    archival_storage = ingest_sessions_to_archival(old_sessions)

    # Verify archival ingestion
    print("\nVerifying archival ingestion...")
    docs = archival_storage.get_all_documents(limit=5)
    print(f"Total documents in archival: {len(docs)}")

    print("\n" + "=" * 70)
    print("✓ Ingestion Complete!")
    print("=" * 70)
    print("\nNext steps:")
    print("1. Your old messages are now in the recall memory (SQLite)")
    print("2. Session transcripts are in archival memory (ChromaDB)")
    print("3. The agent can search these using conversation_search() and archival_memory_search()")
    print("\nYou can now run the agent with: python main.py")


if __name__ == "__main__":
    # You can modify this to load from a file instead:
    # old_sessions = load_sessions_from_file("path/to/your/sessions.json")

    main()
