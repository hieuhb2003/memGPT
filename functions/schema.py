"""
Function/Tool schema definitions for MemGPT.
These schemas define the tools that the LLM can use.
"""
from typing import List, Dict, Any


FUNCTION_SCHEMAS: List[Dict[str, Any]] = [
    {
        "name": "send_message",
        "description": "Sends a message to the user. This yields control back to the user.",
        "parameters": {
            "type": "object",
            "properties": {
                "content": {
                    "type": "string",
                    "description": "The message content to send to the user"
                }
            },
            "required": ["content"]
        }
    },
    {
        "name": "core_memory_append",
        "description": "Append content to a specific section of core memory (working context). Use this to save important information for later retrieval.",
        "parameters": {
            "type": "object",
            "properties": {
                "section": {
                    "type": "string",
                    "description": "The section to append to (e.g., 'persona', 'human')",
                    "enum": ["persona", "human"]
                },
                "content": {
                    "type": "string",
                    "description": "The content to append to the section"
                }
            },
            "required": ["section", "content"]
        }
    },
    {
        "name": "core_memory_replace",
        "description": "Replace specific content in a section of core memory with new content. Use this to update outdated information.",
        "parameters": {
            "type": "object",
            "properties": {
                "section": {
                    "type": "string",
                    "description": "The section to modify (e.g., 'persona', 'human')",
                    "enum": ["persona", "human"]
                },
                "old_content": {
                    "type": "string",
                    "description": "The exact content to be replaced"
                },
                "new_content": {
                    "type": "string",
                    "description": "The new content to replace it with"
                }
            },
            "required": ["section", "old_content", "new_content"]
        }
    },
    {
        "name": "archival_memory_insert",
        "description": "Insert content into archival memory with embeddings for semantic search. Use this for storing large documents or information that doesn't fit in core memory.",
        "parameters": {
            "type": "object",
            "properties": {
                "content": {
                    "type": "string",
                    "description": "The content to store in archival memory"
                }
            },
            "required": ["content"]
        }
    },
    {
        "name": "archival_memory_search",
        "description": "Search archival memory using semantic similarity. Returns paginated results.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query"
                },
                "page": {
                    "type": "integer",
                    "description": "Page number for pagination (default: 0)",
                    "default": 0
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "conversation_search",
        "description": "Search through the conversation history (recall memory) using text-based search. Returns paginated results.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query"
                },
                "page": {
                    "type": "integer",
                    "description": "Page number for pagination (default: 0)",
                    "default": 0
                }
            },
            "required": ["query"]
        }
    }
]


def get_function_schemas() -> List[Dict[str, Any]]:
    """
    Get the function schemas in OpenAI function calling format.

    Returns:
        List of function schema dictionaries
    """
    return FUNCTION_SCHEMAS


def get_openai_tools() -> List[Dict[str, Any]]:
    """
    Get function schemas formatted for OpenAI's tools parameter.

    Returns:
        List of tool dictionaries
    """
    return [
        {
            "type": "function",
            "function": schema
        }
        for schema in FUNCTION_SCHEMAS
    ]
