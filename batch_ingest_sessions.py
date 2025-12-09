"""
Advanced batch ingestion script for multiple conversation sessions
Supports various JSON formats and provides flexible ingestion options
"""

import json
import argparse
import os
from datetime import datetime
from typing import List, Dict, Any
from persistence.sqlite_store import SQLiteRecallStorage
from persistence.chroma_store import ChromaArchivalStorage


class SessionIngester:
    """
    Flexible ingestion class for old conversation sessions
    """

    def __init__(self, db_path="memgpt.db", chroma_path="./data/chroma"):
        self.db_path = db_path
        self.chroma_path = chroma_path
        self.recall_storage = None
        self.archival_storage = None

    def initialize_storages(self, use_recall=True, use_archival=True):
        """Initialize storage backends"""
        if use_recall:
            print(f"Initializing SQLite recall storage: {self.db_path}")
            # Ensure directory exists for db_path
            db_dir = os.path.dirname(self.db_path)
            if db_dir:
                os.makedirs(db_dir, exist_ok=True)
                
            self.recall_storage = SQLiteRecallStorage(db_path=self.db_path)

        if use_archival:
            print(f"Initializing ChromaDB archival storage: {self.chroma_path}")
            self.archival_storage = ChromaArchivalStorage(
                persist_directory=self.chroma_path,
                collection_name="archival_memory"
            )

    def ingest_to_recall(self, messages: List[Dict[str, Any]], session_id=None):
        """
        Ingest messages to recall memory (SQLite)

        Args:
            messages: List of message dicts with 'role', 'content', 'timestamp'
            session_id: Optional session identifier for metadata
        """
        if not self.recall_storage:
             # Just return if not initialized (e.g. mode=archival)
             return

        print(f"\nIngesting {len(messages)} messages to recall memory...")
        for i, msg in enumerate(messages, 1):
            role = msg.get("role", "user")
            content = msg.get("content", "")
            timestamp_str = msg.get("timestamp")

            # Parse timestamp
            timestamp = self._parse_timestamp(timestamp_str)

            # Build metadata
            metadata = {"session_id": session_id} if session_id else {}
            for key, value in msg.items():
                if key not in ["role", "content", "timestamp"]:
                    metadata[key] = value

            # Insert message
            self.recall_storage.insert_message(
                role=role,
                content=content,
                timestamp=timestamp,
                metadata=metadata if metadata else None
            )

            if i % 10 == 0 or i == len(messages):
                print(f"  Progress: {i}/{len(messages)} messages inserted")

        print(f"✓ Completed recall ingestion for session: {session_id or 'default'}")

    def ingest_to_archival(self, messages: List[Dict[str, Any]], session_id=None):
        """
        Ingest messages as a transcript to archival memory (ChromaDB)

        Args:
            messages: List of message dicts
            session_id: Optional session identifier
        """
        if not self.archival_storage:
            return

        # Build transcript
        transcript_lines = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            timestamp = msg.get("timestamp", "")

            transcript_lines.append(f"[{timestamp}] {role.upper()}: {content}")

        transcript = "\n".join(transcript_lines)

        # Insert to archival
        print(f"\nIngesting session transcript to archival memory...")
        doc_id = self.archival_storage.insert(
            content=transcript,
            metadata={
                "session_id": session_id or "default",
                "message_count": len(messages),
                "imported_at": datetime.now().isoformat(),
                "type": "imported_session"
            }
        )

        print(f"✓ Completed archival ingestion (doc_id: {doc_id})")
        return doc_id

    def ingest_from_json_file(self, json_path: str, mode="both"):
        """
        Load and ingest sessions from JSON file

        Supported formats:
        1. Simple list: [{"role": "user", "content": "...", "timestamp": "..."}, ...]
        2. Multiple sessions: {"session1": [...], "session2": [...]}
        3. Complex format: {"conv-id": {"conversation": {"session1": [...]}}}
        4. Nested format: {"conv-id": {"session1": [...], "session2": [...]}}

        Args:
            json_path: Path to JSON file
            mode: "recall", "archival", or "both"
        """
        print(f"\nLoading sessions from: {json_path}")
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        is_nested_storage = False
        if isinstance(data, dict):
            sample_key = next(iter(data)) if data else None
            if sample_key:
                sample_val = data[sample_key]
                if isinstance(sample_val, dict):
                    if "conversation" in sample_val:
                        is_nested_storage = True
                    else:
                        inner_sample = next(iter(sample_val.values())) if sample_val else None
                        if isinstance(inner_sample, list):
                            is_nested_storage = True
        
        if is_nested_storage:
            self._ingest_nested_storage(data, mode)
        else:
            sessions = self._parse_json_format(data)
            print(f"Found {len(sessions)} session(s) to ingest (Global Storage)")
            
            if mode in ["recall", "both"] and not self.recall_storage:
                 raise RuntimeError("Recall storage not initialized for global mode")
            if mode in ["archival", "both"] and not self.archival_storage:
                 raise RuntimeError("Archival storage not initialized for global mode")

            self._ingest_sessions_batch(sessions, mode)

    def _ingest_nested_storage(self, data: Dict, mode: str):
        """Handle ingestion for nested formats with per-conversation storage"""
        
        print(f"Detected nested format. Creating per-conversation storage directories under root paths...")
        
        # Determine the root directory to store conversation folders
        # If the user passed "memgpt.db", we assume they want to store in CWD or relative path
        # If they passed "/path/to/memgpt.db", we might want "/path/to/conv-ID/memgpt.db"
        # However, cleaner logic: Just use command line --db-path arg as the "Base Root" if it is a directory. 
        # But commonly --db-path is a file path. 
        # Let's assume we take the dirname of the db_path to be the root.
        
        root_parent_dir = os.path.dirname(os.path.abspath(self.db_path))
        
        # If usage was just "python script.py --db-path memgpt.db", root_parent_dir is CWD.
        
        print(f"Root Parent Directory: {root_parent_dir}")
        
        for conv_id, content in data.items():
            print(f"\n{'#' * 50}")
            print(f"Processing Conversation Group: {conv_id}")
            print(f"{'#' * 50}")
            
            # Create folder for this conversation: root_parent_dir/conv_id/
            target_folder = os.path.join(root_parent_dir, conv_id)
            os.makedirs(target_folder, exist_ok=True)
            
            conv_db_path = os.path.join(target_folder, "memgpt.db")
            conv_chroma_path = os.path.join(target_folder, "chroma")
            
            # Normalize content
            conv_sessions = {}
            if isinstance(content, dict) and "conversation" in content:
                raw_sessions = content["conversation"]
            elif isinstance(content, dict):
                raw_sessions = content
            else:
                 print(f"Skipping {conv_id}: Invalid content format")
                 continue
                 
            for sess_key, msgs in raw_sessions.items():
                # We prefix session ID with conversation ID just in case, but within isolated DB it's fine.
                full_session_id = f"{sess_key}" 
                if isinstance(msgs, list):
                    if msgs and isinstance(msgs[0], str):
                        conv_sessions[full_session_id] = self._convert_strings_to_messages(msgs)
                    else:
                        conv_sessions[full_session_id] = msgs
            
            print(f"Found {len(conv_sessions)} session(s) for {conv_id}")
            print(f"Storage: {conv_db_path}")
            
            # Initialize isolated storage
            local_ingester = SessionIngester(db_path=conv_db_path, chroma_path=conv_chroma_path)
            local_ingester.initialize_storages(
                use_recall=(mode in ["recall", "both"]), 
                use_archival=(mode in ["archival", "both"])
            )
            
            local_ingester._ingest_sessions_batch(conv_sessions, mode)

    def _ingest_sessions_batch(self, sessions: Dict[str, List[Dict]], mode: str):
        """Internal helper to ingest a batch of sessions to initialized storage"""
        for session_id, messages in sessions.items():
            print(f"\nProcessing session: {session_id} ({len(messages)} messages)")
            
            if mode in ["recall", "both"]:
                self.ingest_to_recall(messages, session_id=session_id)

            if mode in ["archival", "both"]:
                self.ingest_to_archival(messages, session_id=session_id)

    def _parse_json_format(self, data) -> Dict[str, List[Dict]]:
        """
        Parse various JSON formats into normalized session format (Global Mode)
        """
        sessions = {}

        if isinstance(data, list):
            sessions["default"] = data

        elif isinstance(data, dict):
            # Try to grab the first key to guess format
            first_key = next(iter(data)) if data else None
            if not first_key:
                return sessions
                
            first_value = data[first_key]
            
            # Format 2: {"session1": [...]}
            if isinstance(first_value, list):
                 for session_id, messages in data.items():
                    if isinstance(messages, list):
                        sessions[session_id] = messages
            else:
                # Fallback for nested formats if they somehow reach here (should be handled by nested_storage logic)
                # But just in case, do a best effort flatten
                if isinstance(first_value, dict):
                     for conv_id, content in data.items():
                        if isinstance(content, dict):
                             # Check for "conversation" key or direct sessions
                             raw_sessions = content.get("conversation", content)
                             for sess_key, msgs in raw_sessions.items():
                                 if isinstance(msgs, list):
                                     sessions[f"{conv_id}_{sess_key}"] = msgs

        return sessions

    def _convert_strings_to_messages(self, string_messages: List[str]) -> List[Dict]:
        """
        Convert list of string messages to message format with role alternation
        """
        messages = []
        for i, content in enumerate(string_messages):
            role = "user" if i % 2 == 0 else "assistant"
            messages.append({
                "role": role,
                "content": content,
                "timestamp": datetime.now().isoformat()
            })
        return messages

    def _parse_timestamp(self, timestamp_str):
        """Parse timestamp string to datetime object"""
        if not timestamp_str:
            return None

        formats = [
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%d %H:%M:%S.%f",
            "%Y-%m-%dT%H:%M:%S.%f",
        ]

        for fmt in formats:
            try:
                return datetime.strptime(timestamp_str, fmt)
            except ValueError:
                continue

        try:
            return datetime.fromisoformat(timestamp_str)
        except:
            print(f"Warning: Could not parse timestamp: {timestamp_str}")
            return None

    def verify_ingestion(self):
        """Verify data was ingested correctly"""
        print("\n" + "=" * 70)
        print("VERIFICATION")
        print("=" * 70)

        if self.recall_storage:
            all_messages = self.recall_storage.get_all_messages()
            print(f"\n✓ Recall Memory (SQLite): {len(all_messages)} total messages")

            recent = self.recall_storage.get_recent_messages(limit=3)
            print("\nMost recent messages:")
            for msg in recent:
                print(f"  - [{msg['timestamp']}] {msg['role']}: {msg['content'][:60]}...")

        if self.archival_storage:
            docs = self.archival_storage.get_all_documents(limit=100)
            print(f"\n✓ Archival Memory (ChromaDB): {len(docs)} total documents")

            if docs:
                print("\nSample document:")
                doc = docs[0]
                print(f"  ID: {doc.get('id')}")
                print(f"  Content preview: {doc.get('content', '')[:100]}...")
                print(f"  Metadata: {doc.get('metadata', {})}")


def main():
    """
    Command-line interface for batch ingestion
    """
    parser = argparse.ArgumentParser(
        description="Ingest old conversation sessions into MemGPT database"
    )
    parser.add_argument(
        "--file",
        type=str,
        help="Path to JSON file containing sessions"
    )
    parser.add_argument(
        "--mode",
        type=str,
        choices=["recall", "archival", "both"],
        default="both",
        help="Ingestion mode: recall (SQLite), archival (ChromaDB), or both"
    )
    parser.add_argument(
        "--db-path",
        type=str,
        default="memgpt.db",
        help="Path to SQLite database (Acts as root parent directory for nested format)"
    )
    parser.add_argument(
        "--chroma-path",
        type=str,
        default="./data/chroma",
        help="Path to ChromaDB directory"
    )

    args = parser.parse_args()

    print("=" * 70)
    print("MemGPT Batch Session Ingestion")
    print("=" * 70)

    ingester = SessionIngester(
        db_path=args.db_path,
        chroma_path=args.chroma_path
    )

    # Note: initialization is now handled dynamically inside ingest_from_json_file for nested mode
    # But for default example usage, we run it here if no file provided
    
    if args.file:
        # File based ingestion (handles both normal and nested)
        ingester.ingest_from_json_file(args.file, mode=args.mode)
    else:
        # Example data usage (Global mode)
        use_recall = args.mode in ["recall", "both"]
        use_archival = args.mode in ["archival", "both"]
        ingester.initialize_storages(use_recall=use_recall, use_archival=use_archival)
        
        print("\nNo file specified, using example data...")
        example_sessions = {
            "session_1": [
                {
                    "role": "user",
                    "content": "Dự án MemGPT này cần chạy local hoàn toàn nhé.",
                    "timestamp": "2024-01-15 09:00:00"
                },
                {
                    "role": "assistant",
                    "content": "Đã rõ. Tôi sẽ sử dụng SQLite và ChromaDB.",
                    "timestamp": "2024-01-15 09:00:05"
                }
            ]
        }

        for session_id, messages in example_sessions.items():
            if use_recall:
                ingester.ingest_to_recall(messages, session_id=session_id)
            if use_archival:
                ingester.ingest_to_archival(messages, session_id=session_id)

    # Verify global storage if used
    if ingester.recall_storage or ingester.archival_storage:
        ingester.verify_ingestion()

    print("\n" + "=" * 70)
    print("✓ Ingestion Complete!")
    print("=" * 70)


if __name__ == "__main__":
    main()
