# MemGPT Quick Start Guide

Get up and running with MemGPT in 5 minutes!

## Step 1: Install Dependencies

```bash
# Option A: Use the setup script (recommended)
./setup.sh

# Option B: Manual setup
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Step 2: Set Your API Key

```bash
# Set environment variable
export OPENAI_API_KEY="your-api-key-here"

# Or create a .env file
echo "OPENAI_API_KEY=your-api-key-here" > .env
```

## Step 3: Run MemGPT

### Interactive CLI

```bash
python main.py
```

You'll see:
```
======================================================================
  MemGPT - Memory-Enhanced GPT with Hierarchical Memory System
======================================================================

Commands:
  /help     - Show this help message
  /status   - Show memory status
  /memory   - Show core memory contents
  /reset    - Reset agent memory
  /quit     - Exit the program
...
```

### Try These Commands

1. Have a conversation:
```
You: Hello! My name is Alice and I'm a software engineer.
```

2. Check memory:
```
You: /memory
```

3. Check status:
```
You: /status
```

4. Ask the agent to recall information:
```
You: What's my name and profession?
```

## Step 4: Try Examples

Run the example script to see different features:

```bash
python example.py
```

This demonstrates:
- Basic chat
- Memory management
- Archival memory (document storage)
- Conversation search
- Long conversations (memory pressure)

## Understanding MemGPT

### Core Concepts

**Three Memory Tiers:**

1. **Core Memory** - Like RAM, small but fast
   - Stores key facts about you and current context
   - Always accessible in every message
   - Modified via `core_memory_append` and `core_memory_replace`

2. **Archival Memory** - Like a hard drive, large but needs search
   - Stores documents and large amounts of information
   - Uses embeddings for semantic search
   - Modified via `archival_memory_insert` and `archival_memory_search`

3. **Recall Memory** - Like a log file
   - Complete conversation history
   - Searchable with text queries
   - Accessed via `conversation_search`

### How Memory Management Works

1. **Normal Operation** (<70% capacity)
   - Messages flow normally
   - All recent context available

2. **Memory Pressure** (70-95% capacity)
   - System alerts the agent
   - Agent should save important info to Core/Archival memory

3. **Eviction** (>95% capacity)
   - Oldest messages automatically evicted
   - LLM generates a summary
   - Evicted messages stored in Recall Memory
   - Summary kept in the queue

## Example Session

```
You: Hi! I'm working on a Python project using FastAPI.
MemGPT: Hello! I've noted that you're working on a Python project
        with FastAPI. I'll remember this. How can I help you today?

You: /memory
[HUMAN]
Working on a Python project using FastAPI.

You: Can you store the FastAPI documentation summary in archival memory?
MemGPT: I've stored the FastAPI documentation in archival memory.
        You can search for it later if needed.

You: /status
Memory Status:
  Queue Length: 6 messages
  Token Usage: 450/8000 (5.6%)
  Current Summary: Conversation summary: No previous interactions.
```

## Common Commands

### CLI Commands
- `/help` - Show help
- `/status` - Memory usage
- `/memory` - View core memory
- `/reset` - Clear all memory
- `/quit` - Exit

### Agent Functions (Automatic)
The agent can use these tools automatically:

- `send_message(content)` - Talk to you
- `core_memory_append(section, content)` - Add to core memory
- `core_memory_replace(section, old, new)` - Update core memory
- `archival_memory_insert(content)` - Store documents
- `archival_memory_search(query, page)` - Search documents
- `conversation_search(query, page)` - Search history

## Tips

1. **Tell the agent to remember important things:**
   - "Remember that I prefer detailed explanations"
   - "Save this information about my project"

2. **Use archival memory for documents:**
   - "Store this API documentation in archival memory"
   - "Insert this code snippet into archival memory"

3. **Search when needed:**
   - "Search archival memory for information about X"
   - "Search our conversation for when I mentioned Y"

4. **Monitor memory:**
   - Use `/status` to see usage
   - Agent will warn you at 70% capacity
   - Reset with `/reset` if needed

## Troubleshooting

### "Error: OpenAI API key not found"
Set your API key:
```bash
export OPENAI_API_KEY="your-key"
```

### "ImportError" or "ModuleNotFoundError"
Install dependencies:
```bash
pip install -r requirements.txt
```

### Slow responses
- Use `gpt-3.5-turbo` instead of `gpt-4`:
  ```bash
  python main.py --model gpt-3.5-turbo
  ```

### High token usage
- Reduce context size:
  ```bash
  python main.py --max-tokens 4000
  ```

## Next Steps

- Read the full [README.md](README.md) for detailed documentation
- Explore [example.py](example.py) for programmatic usage
- Check [project.md](project.md) for architecture details
- Experiment with different models and settings

## Need Help?

- Check the README.md for full documentation
- Review example.py for code examples
- Read project.md for technical details

Enjoy using MemGPT!
