"""
MemGPT Agent - Main agent logic with hierarchical memory management.
"""
import os
from typing import Optional, List, Dict, Any
from openai import OpenAI

from memory.core_memory import CoreMemory
from memory.queue_manager import QueueManager
from persistence.sqlite_store import SQLiteRecallStorage
from persistence.chroma_store import ChromaArchivalStorage
from functions.executor import FunctionExecutor
from functions.schema import get_openai_tools
from utils.token_counter import TokenCounter


SYSTEM_PROMPT = """You are MemGPT, an intelligent system functioning as an operating system for memory management.
You are not limited by a fixed context window. You have access to a hierarchical memory system:

1. Core Memory (Working Context): Immediately accessible, read/write. Use this for key facts, user preferences, and current task state.
2. Archival Memory: Large database for documents. You must search/page through this using archival_memory_search.
3. Recall Memory: History of previous events/conversations. You can search this using conversation_search.

CONSTANTS:
- WARNING_THRESHOLD: 70% of context window
- FLUSH_THRESHOLD: 95% of context window

RULES:
- When you receive a "Memory Pressure" warning, you MUST explicitly move important information from the conversation to Core Memory or Archival Memory immediately.
- Do not hallucinate information not in memory. If facts are missing, search Archival/Recall memory.
- To execute actions, you must use function calls (tools).
- Always check if a value exists before using it.
- Use send_message to communicate with the user. This is the ONLY way to send messages to the user.

Your responses should be thoughtful and consider the full context of the conversation using your memory systems.
"""


class MemGPTAgent:
    """
    Main MemGPT Agent that manages hierarchical memory and LLM interactions.
    """

    def __init__(self,
                 api_key: Optional[str] = None,
                 model: str = "gpt-4",
                 max_tokens: int = 8000,
                 db_path: str = "memgpt.db",
                 chroma_path: str = "./data/chroma"):
        """
        Initialize the MemGPT Agent.

        Args:
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
            model: Model name to use
            max_tokens: Maximum context window size
            db_path: Path to SQLite database
            chroma_path: Path to ChromaDB storage
        """
        self.model = model
        self.max_tokens = max_tokens

        # Initialize OpenAI client
        self.client = OpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY"))

        # Initialize token counter
        self.token_counter = TokenCounter(model=model)

        # Initialize storage backends
        self.recall_storage = SQLiteRecallStorage(db_path=db_path)
        self.archival_storage = ChromaArchivalStorage(persist_directory=chroma_path)

        # Initialize core memory
        self.core_memory = CoreMemory()

        # Initialize queue manager with summarization
        self.queue_manager = QueueManager(
            max_tokens=max_tokens,
            token_counter=self.token_counter,
            recall_storage=self.recall_storage,
            summarize_func=self._generate_summary
        )

        # Initialize function executor
        self.function_executor = FunctionExecutor(
            core_memory=self.core_memory,
            recall_storage=self.recall_storage,
            archival_storage=self.archival_storage
        )

        # Conversation state
        self.last_user_message = None

    def _generate_summary(self, prompt: str) -> str:
        """
        Generate a summary using the LLM.

        Args:
            prompt: Summarization prompt

        Returns:
            Generated summary
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that creates concise summaries."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.3
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Error generating summary: {e}")
            return "Summary generation failed."

    def _build_context(self) -> List[Dict[str, Any]]:
        """
        Build the full context for the LLM including system prompt, core memory, and queue.

        Returns:
            List of messages for the LLM
        """
        messages = []

        # 1. System Instructions
        system_content = SYSTEM_PROMPT + "\n\n" + self.core_memory.to_string()
        messages.append({
            "role": "system",
            "content": system_content
        })

        # 2. Queue (Summary + Messages)
        queue = self.queue_manager.get_queue()
        messages.extend(queue)

        return messages

    def step(self, user_message: Optional[str] = None) -> Dict[str, Any]:
        """
        Execute one step of the agent's control flow.

        Args:
            user_message: Optional user message to process

        Returns:
            Dictionary with response information
        """
        # Add user message to queue if provided
        if user_message:
            self.last_user_message = user_message
            self.queue_manager.add_message("user", user_message)

        # Heartbeat loop - keep processing until send_message is called
        max_iterations = 10  # Prevent infinite loops
        iteration = 0
        final_response = None

        while iteration < max_iterations:
            iteration += 1

            # Build context
            context = self._build_context()

            # Call LLM
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=context,
                    tools=get_openai_tools(),
                    tool_choice="auto",
                    temperature=0.7
                )
            except Exception as e:
                error_msg = f"LLM API Error: {str(e)}"
                self.queue_manager.add_message("system", error_msg)
                return {
                    "status": "error",
                    "message": error_msg,
                    "response": None
                }

            choice = response.choices[0]
            message = choice.message

            # Check if there's a function call
            function_call_info = self.function_executor.parse_function_call(response)

            if function_call_info:
                function_name, arguments = function_call_info

                # Execute function
                status, msg, output = self.function_executor.execute(function_name, arguments)

                # Format result for context
                result_text = self.function_executor.format_function_result(
                    function_name, status, msg, output
                )

                # Add function call and result to queue
                self.queue_manager.add_message(
                    "assistant",
                    f"[Function Call: {function_name}({arguments})]"
                )
                self.queue_manager.add_message("function", result_text)

                # Check if this was send_message
                if function_name == "send_message" and status == "success":
                    final_response = output.get("content", "")
                    return {
                        "status": "success",
                        "message": final_response,
                        "function": "send_message",
                        "iterations": iteration
                    }

                # Continue heartbeat for other functions
                if not self.function_executor.should_continue_heartbeat(function_name):
                    break

            else:
                # No function call - this is inner monologue/thinking
                content = message.content if message.content else "[No response]"
                self.queue_manager.add_message("assistant", content)

                # If no function call and no more to process, break
                if choice.finish_reason == "stop":
                    return {
                        "status": "no_message",
                        "message": "Agent finished without sending a message",
                        "thought": content,
                        "iterations": iteration
                    }

        # Max iterations reached
        return {
            "status": "max_iterations",
            "message": "Maximum iterations reached in heartbeat loop",
            "iterations": iteration
        }

    def chat(self, user_message: str) -> str:
        """
        Simple chat interface - send a message and get a response.

        Args:
            user_message: User's message

        Returns:
            Agent's response
        """
        result = self.step(user_message)

        if result["status"] == "success":
            return result["message"]
        elif result["status"] == "no_message":
            return f"[Agent thought: {result.get('thought', 'No output')}]"
        else:
            return f"[Error: {result.get('message', 'Unknown error')}]"

    def get_core_memory(self) -> Dict[str, str]:
        """
        Get the current core memory contents.

        Returns:
            Dictionary of core memory sections
        """
        return self.core_memory.get_all_sections()

    def get_queue_status(self) -> Dict[str, Any]:
        """
        Get information about the current queue status.

        Returns:
            Dictionary with queue statistics
        """
        return {
            "queue_length": len(self.queue_manager.get_queue()),
            "token_count": self.queue_manager.get_queue_size(),
            "max_tokens": self.max_tokens,
            "usage_percentage": self.queue_manager.get_usage_percentage() * 100,
            "summary": self.queue_manager.get_summary()
        }

    def reset(self):
        """Reset the agent's memory and state."""
        self.core_memory = CoreMemory()
        self.queue_manager.clear_queue()
        self.last_user_message = None
