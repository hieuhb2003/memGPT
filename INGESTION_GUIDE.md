# MemGPT Old Message Ingestion Guide

This guide explains how to ingest old conversation messages into your MemGPT agent's memory system.

## Overview

MemGPT has two types of memory storage:

1. **Recall Memory (SQLite)** - Stores individual messages for conversation search
2. **Archival Memory (ChromaDB)** - Stores full session transcripts for semantic search

## Scripts Available

### 1. `ingest_old_messages.py` - Simple Ingestion

Basic script for ingesting a single session of messages.

**Usage:**
```bash
python ingest_old_messages.py
```

**Features:**
- Ingests messages to both recall and archival memory
- Demonstrates basic ingestion workflow
- Good for testing and learning

### 2. `batch_ingest_sessions.py` - Advanced Batch Ingestion

Production-ready script for ingesting multiple sessions from JSON files.

**Usage:**
```bash
# Ingest from JSON file (both recall and archival)
python batch_ingest_sessions.py --file your_sessions.json

# Ingest only to recall memory (SQLite)
python batch_ingest_sessions.py --file your_sessions.json --mode recall

# Ingest only to archival memory (ChromaDB)
python batch_ingest_sessions.py --file your_sessions.json --mode archival

# Use custom database paths
python batch_ingest_sessions.py --file your_sessions.json \
  --db-path custom.db \
  --chroma-path ./custom/chroma
```

**Arguments:**
- `--file` - Path to JSON file containing sessions
- `--mode` - Ingestion mode: `recall`, `archival`, or `both` (default: `both`)
- `--db-path` - SQLite database path (default: `memgpt.db`)
- `--chroma-path` - ChromaDB directory path (default: `./data/chroma`)

## JSON Format

The batch ingestion script supports three formats:

### Format 1: Simple List
```json
[
  {
    "role": "user",
    "content": "Your message here",
    "timestamp": "2024-01-15 09:00:00"
  },
  {
    "role": "assistant",
    "content": "Response here",
    "timestamp": "2024-01-15 09:00:05"
  }
]
```

### Format 2: Multiple Sessions (Recommended)
```json
{
  "session_1": [
    {
      "role": "user",
      "content": "Message 1",
      "timestamp": "2024-01-15 09:00:00"
    }
  ],
  "session_2": [
    {
      "role": "user",
      "content": "Message 2",
      "timestamp": "2024-01-15 10:00:00"
    }
  ]
}
```

### Format 2: Multiple Sessions (Simple)
```json
{
  "session_1": [
    {
      "role": "user",
      "content": "Message 1",
      "timestamp": "2024-01-15 09:00:00"
    }
  ],
  "session_2": [
    {
      "role": "user",
      "content": "Message 2",
      "timestamp": "2024-01-15 10:00:00"
    }
  ]
}
```

### Format 3: Nested Conversations (Recommended)
Organize by conversation ID with multiple sessions:
```json
{
  "conv-26": {
    "session_1": [
      {
        "role": "user",
        "content": "Message 1",
        "timestamp": "2024-01-15 09:00:00"
      }
    ],
    "session_2": [
      {
        "role": "user",
        "content": "Message 2",
        "timestamp": "2024-01-15 10:00:00"
      }
    ]
  },
  "conv-27": {
    "session_1": [
      {
        "role": "user",
        "content": "Message 3",
        "timestamp": "2024-01-16 09:00:00"
      }
    ]
  }
}
```
This will create sessions named: `conv-26_session_1`, `conv-26_session_2`, `conv-27_session_1`

### Format 4: Complex Nested Format
```json
{
  "conv-26": {
    "conversation": {
      "session_1": [
        "First message",
        "Second message"
      ]
    }
  }
}
```

## Message Fields

### Required Fields
- `role` - Message sender: `"user"`, `"assistant"`, `"system"`, or `"function"`
- `content` - Message content (string)

### Optional Fields
- `timestamp` - Message timestamp (supports multiple formats)
- Any additional fields will be stored in metadata

### Timestamp Formats Supported
- `"2024-01-15 09:00:00"`
- `"2024-01-15T09:00:00"`
- `"2024-01-15 09:00:00.123456"`
- ISO 8601 format

## Step-by-Step Tutorial

### 1. Prepare Your Data

Create a JSON file with your old messages:

```json
{
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
```

Save this as `my_old_sessions.json`

### 2. Run the Ingestion Script

```bash
python batch_ingest_sessions.py --file my_old_sessions.json
```

### 3. Verify Ingestion

The script will show verification output:
```
VERIFICATION
======================================================================

✓ Recall Memory (SQLite): 2 total messages

Most recent messages:
  - [2024-01-15 09:00:05] assistant: Đã rõ. Tôi sẽ sử dụng SQLite và ChromaDB....

✓ Archival Memory (ChromaDB): 1 total documents
```

### 4. Use the Agent

Run the MemGPT agent:
```bash
python main.py
```

The agent can now search the ingested messages:
- Use `conversation_search("keyword")` to search recall memory
- Use `archival_memory_search("query")` to search archival memory

## Programmatic Usage

You can also use the `SessionIngester` class in your own Python code:

```python
from batch_ingest_sessions import SessionIngester

# Initialize
ingester = SessionIngester(
    db_path="memgpt.db",
    chroma_path="./data/chroma"
)
ingester.initialize_storages(use_recall=True, use_archival=True)

# Ingest from file
ingester.ingest_from_json_file("sessions.json", mode="both")

# Or ingest programmatically
messages = [
    {
        "role": "user",
        "content": "Hello!",
        "timestamp": "2024-01-15 09:00:00"
    }
]
ingester.ingest_to_recall(messages, session_id="my_session")
ingester.ingest_to_archival(messages, session_id="my_session")

# Verify
ingester.verify_ingestion()
```

## How It Works

### Recall Memory (SQLite)

Each message is stored individually in the `message_history` table:

| id | role | content | timestamp | metadata |
|----|------|---------|-----------|----------|
| 1 | user | "Message 1" | 2024-01-15 09:00:00 | {"session_id": "session_1"} |
| 2 | assistant | "Response" | 2024-01-15 09:00:05 | {"session_id": "session_1"} |

**Benefits:**
- Individual message retrieval
- Text-based search with SQL LIKE
- Chronological ordering
- Fast access to recent messages

### Archival Memory (ChromaDB)

Entire sessions are stored as transcript documents:

```
[2024-01-15 09:00:00] USER: Message 1
[2024-01-15 09:00:05] ASSISTANT: Response
```

**Benefits:**
- Semantic similarity search using embeddings
- Context-aware retrieval
- Efficient for long conversations
- Preserves conversation flow

## Best Practices

1. **Choose the Right Mode**
   - Use `--mode both` (default) for maximum flexibility
   - Use `--mode recall` for searchable message history only
   - Use `--mode archival` for semantic search only

2. **Session Organization**
   - Group related messages into sessions
   - Use descriptive session IDs (e.g., "2024-01-15_project_discussion")
   - Keep sessions focused on single topics

3. **Timestamps**
   - Always include timestamps for chronological ordering
   - Use consistent timestamp format
   - If missing, current time will be used

4. **Metadata**
   - Add custom fields for filtering (e.g., "topic", "project_id")
   - Metadata is stored and searchable

5. **Large Datasets**
   - Ingest in batches if you have thousands of messages
   - Monitor database size
   - Consider splitting into multiple ChromaDB collections

## Troubleshooting

### "ModuleNotFoundError: No module named 'persistence'"

Make sure you're running from the MemGPT root directory:
```bash
cd /path/to/memGPT
python batch_ingest_sessions.py --file sessions.json
```

### "Database is locked"

Close any other connections to the SQLite database:
```bash
# Check for running processes
ps aux | grep memgpt

# Kill if necessary
pkill -f memgpt
```

### "Invalid timestamp format"

Use one of the supported formats:
- `"2024-01-15 09:00:00"` (recommended)
- `"2024-01-15T09:00:00"`
- ISO 8601

### Messages not appearing in agent

1. Verify ingestion completed successfully
2. Check database files exist:
   ```bash
   ls -lh memgpt.db
   ls -lh data/chroma
   ```
3. Use the verification output to confirm message count

## Examples

### Example 1: Simple Session

```json
{
  "onboarding": [
    {
      "role": "user",
      "content": "What is MemGPT?",
      "timestamp": "2024-01-15 09:00:00"
    },
    {
      "role": "assistant",
      "content": "MemGPT is a system that enables LLMs with self-editing memory.",
      "timestamp": "2024-01-15 09:00:10"
    }
  ]
}
```

**Ingest:**
```bash
python batch_ingest_sessions.py --file onboarding.json
```

### Example 2: Multiple Projects

```json
{
  "project_alpha": [
    {"role": "user", "content": "Start project alpha", "timestamp": "2024-01-10 10:00:00"}
  ],
  "project_beta": [
    {"role": "user", "content": "Start project beta", "timestamp": "2024-01-12 14:00:00"}
  ]
}
```

**Ingest:**
```bash
python batch_ingest_sessions.py --file projects.json
```

### Example 3: Custom Database Path

```bash
python batch_ingest_sessions.py \
  --file sessions.json \
  --db-path ./databases/agent_1.db \
  --chroma-path ./databases/chroma_agent_1
```

## Additional Resources

- See `example_old_sessions.json` for a working example
- Run `python ingest_old_messages.py` for a simple demo
- Check `run_inference.py` for advanced usage patterns

## Support

For issues or questions:
1. Check the verification output after ingestion
2. Review error messages carefully
3. Ensure JSON format is valid (use a JSON validator)
4. Check that all required Python packages are installed
