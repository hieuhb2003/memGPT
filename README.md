# MemGPT - Memory-Enhanced GPT

An implementation of MemGPT, an OS-inspired system for Large Language Models (LLMs) that manages a hierarchical memory system to provide the illusion of "infinite context" through autonomous memory management.

## Overview

MemGPT uses a three-tier memory hierarchy inspired by operating systems:

1. **Core Memory (Working Context)**: A fixed-size, read/write block for immediately accessible information like key facts, user preferences, and current task state.

2. **Archival Memory**: A vector database for storing large documents with semantic search capabilities (RAG).

3. **Recall Memory**: Complete conversation history stored in SQLite with text-based search.

The system automatically manages memory pressure, evicts old messages, and creates recursive summaries to maintain long-term context.

## Features

- **Hierarchical Memory Management**: Automatic memory paging and eviction
- **Memory Pressure Detection**: Alerts at 70% capacity, evicts at 95%
- **Recursive Summarization**: LLM-generated summaries of evicted conversations
- **Function Chaining (Heartbeat)**: Execute multiple function calls in sequence
- **Local Storage**: No Docker required - uses SQLite and ChromaDB
- **Semantic Search**: Embeddings-based search using sentence-transformers

## Architecture

```
Main Context (Sent to LLM):
┌─────────────────────────────────────┐
│ 1. System Instructions (Static)    │
│    - MemGPT persona                 │
│    - Memory hierarchy description   │
│    - Function schemas               │
├─────────────────────────────────────┤
│ 2. Working Context (Read/Write)     │
│    - Core Memory sections           │
│    - Updated via function calls     │
├─────────────────────────────────────┤
│ 3. FIFO Queue (Rolling History)     │
│    - [0] Recursive Summary          │
│    - [1+] Recent messages           │
│    - Auto-eviction when full        │
└─────────────────────────────────────┘
```

## Installation

### Prerequisites

- Python 3.8 or higher
- OpenAI API key

### Setup

1. Clone the repository:
```bash
cd /Users/hieunguyenmanh/Desktop/memGPT
```

2. Create a virtual environment (recommended):
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set your OpenAI API key:
```bash
export OPENAI_API_KEY="your-api-key-here"
```

Or create a `.env` file:
```
OPENAI_API_KEY=your-api-key-here
```

## Usage

### Basic Usage

Run the interactive CLI:

```bash
python main.py
```

### Command-Line Options

```bash
python main.py --help

Options:
  --api-key API_KEY        OpenAI API key (defaults to OPENAI_API_KEY env var)
  --model MODEL            OpenAI model to use (default: gpt-4)
  --max-tokens MAX_TOKENS  Maximum context window size (default: 8000)
  --db-path DB_PATH        Path to SQLite database (default: memgpt.db)
  --chroma-path CHROMA_PATH Path to ChromaDB storage (default: ./data/chroma)
```

Example:
```bash
python main.py --model gpt-3.5-turbo --max-tokens 4000
```


### Ingestion

```bash
# This will create folders ./memgpt_data/conv-XX/memgpt.db etc.
python batch_ingest_sessions.py \
  --file formatted_longmemeval.json \
  --db-path ./memgpt_data/memgpt.db \
  --chroma-path ./memgpt_data/chroma
```

### CLI Commands

While running the interactive CLI:

- `/help` - Show help message
- `/status` - Show memory usage and statistics
- `/memory` - Display core memory contents
- `/reset` - Reset all agent memory
- `/quit` - Exit the program

### Available Functions

The agent can use the following tools:

1. **send_message(content)**: Send a message to the user
2. **core_memory_append(section, content)**: Add information to core memory
3. **core_memory_replace(section, old_content, new_content)**: Update core memory
4. **archival_memory_insert(content)**: Store documents in archival memory
5. **archival_memory_search(query, page)**: Search archival memory semantically
6. **conversation_search(query, page)**: Search conversation history

## Programmatic Usage

You can also use MemGPT as a library:

```python
from agents.agent import MemGPTAgent

# Initialize agent
agent = MemGPTAgent(
    api_key="your-api-key",
    model="gpt-4",
    max_tokens=8000
)

# Simple chat
response = agent.chat("Hello! Tell me about yourself.")
print(response)

# Get memory status
status = agent.get_queue_status()
print(f"Token usage: {status['usage_percentage']:.1f}%")

# Get core memory
memory = agent.get_core_memory()
print(memory)

# Reset memory
agent.reset()
```

## Project Structure

```
/memgpt/
  /agents/
    agent.py          # Main agent logic and control flow
  /memory/
    core_memory.py    # Working context manager
    queue_manager.py  # FIFO queue with eviction logic
  /persistence/
    storage_interface.py # Abstract storage interfaces
    sqlite_store.py      # SQLite for conversation history
    chroma_store.py      # ChromaDB for vector embeddings
  /functions/
    executor.py       # Function execution engine
    schema.py         # Tool/function definitions
  /utils/
    token_counter.py  # Token counting utilities
  main.py             # CLI entry point
  requirements.txt    # Python dependencies
```

## How It Works

### Memory Management Flow

1. **User sends message** → Added to FIFO queue
2. **Token counter checks usage** → If >70%, inject memory pressure warning
3. **Agent processes message** → May use functions to manage memory
4. **If usage >95%** → Automatic eviction triggered:
   - Extract oldest messages
   - Generate recursive summary with LLM
   - Persist evicted messages to SQLite
   - Update queue with new summary

### Heartbeat Mechanism

The agent can chain multiple function calls:

```
1. User: "Remember that my favorite color is blue"
2. Agent calls: core_memory_append("human", "Favorite color: blue")
3. Agent calls: send_message("I've saved that information!")
4. Return to user
```

The loop continues until `send_message` is called or max iterations reached.

## Technical Details

### Storage

- **Recall Memory**: SQLite database (`memgpt.db`)
  - Table: `message_history` with full-text search
  - Stores all evicted messages with timestamps

- **Archival Memory**: ChromaDB (local folder: `./data/chroma`)
  - Embeddings: `sentence-transformers/all-MiniLM-L6-v2`
  - Runs locally on CPU (no GPU required)
  - Persistent storage with automatic indexing

### Token Management

- Uses `tiktoken` for accurate token counting
- Warning threshold: 70% of max_tokens
- Flush threshold: 95% of max_tokens
- Evicts oldest 1/3 of messages when threshold reached

### Error Handling

- Function execution errors are caught and fed back to the LLM
- LLM can self-correct based on error messages
- Parsing failures inject system alerts

## Limitations

- Maximum 10 iterations per user message (prevents infinite loops)
- Embedding model runs on CPU (may be slow for large documents)
- Summary quality depends on LLM capabilities
- No built-in conversation branching

## Troubleshooting

### API Key Issues
```bash
Error: OpenAI API key not found.
```
Solution: Set `OPENAI_API_KEY` environment variable or use `--api-key` flag.

### ChromaDB Errors
```bash
Error initializing agent: ...
```
Solution: Ensure `./data/chroma` directory exists and is writable.

### Token Limit Errors
If you get token limit errors, try:
- Using a smaller `--max-tokens` value
- Using `gpt-3.5-turbo` instead of `gpt-4`
- Manually resetting memory with `/reset`

## Contributing

This is an implementation based on the MemGPT research paper. Contributions are welcome!

## License

MIT License

## References

Based on the MemGPT paper and architecture described in `project.md`.

## Acknowledgments

- OpenAI for GPT models and API
- ChromaDB for vector storage
- sentence-transformers for embeddings
- Original MemGPT research team
