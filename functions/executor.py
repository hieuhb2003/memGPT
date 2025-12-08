"""
Function executor for MemGPT.
Handles execution of function calls and manages the heartbeat mechanism.
"""
import json
from typing import Dict, Any, Optional, Tuple
from memory.core_memory import CoreMemory
from persistence.storage_interface import RecallStorage, ArchivalStorage


class FunctionExecutor:
    """
    Executes function calls from the LLM and returns results.
    Implements the heartbeat mechanism for function chaining.
    """

    def __init__(self,
                 core_memory: CoreMemory,
                 recall_storage: RecallStorage,
                 archival_storage: ArchivalStorage,
                 page_size: int = 5):
        """
        Initialize the function executor.

        Args:
            core_memory: CoreMemory instance
            recall_storage: RecallStorage instance for conversation history
            archival_storage: ArchivalStorage instance for document storage
            page_size: Number of results per page for search functions
        """
        self.core_memory = core_memory
        self.recall_storage = recall_storage
        self.archival_storage = archival_storage
        self.page_size = page_size

        # Map function names to methods
        self.function_map = {
            'send_message': self._send_message,
            'core_memory_append': self._core_memory_append,
            'core_memory_replace': self._core_memory_replace,
            'archival_memory_insert': self._archival_memory_insert,
            'archival_memory_search': self._archival_memory_search,
            'conversation_search': self._conversation_search,
        }

    def execute(self, function_name: str, arguments: Dict[str, Any]) -> Tuple[str, str, Any]:
        """
        Execute a function call.

        Args:
            function_name: Name of the function to execute
            arguments: Dictionary of function arguments

        Returns:
            Tuple of (status, message, output)
            - status: "success" or "error"
            - message: Human-readable status message
            - output: Function output data
        """
        if function_name not in self.function_map:
            return ("error", f"Unknown function: {function_name}", None)

        try:
            result = self.function_map[function_name](**arguments)
            return ("success", f"Function {function_name} executed successfully", result)
        except TypeError as e:
            return ("error", f"Invalid arguments for {function_name}: {str(e)}", None)
        except Exception as e:
            return ("error", f"Error executing {function_name}: {str(e)}", None)

    def _send_message(self, content: str) -> Dict[str, Any]:
        """
        Send a message to the user.

        Args:
            content: Message content

        Returns:
            Dictionary with message info
        """
        return {
            "status": "message_sent",
            "content": content
        }

    def _core_memory_append(self, section: str, content: str) -> Dict[str, Any]:
        """
        Append content to a core memory section.

        Args:
            section: Section name
            content: Content to append

        Returns:
            Dictionary with operation result
        """
        success = self.core_memory.append(section, content)

        if success:
            return {
                "status": "success",
                "message": f"Appended to {section}",
                "section": section
            }
        else:
            raise ValueError(f"Section '{section}' does not exist")

    def _core_memory_replace(self, section: str, old_content: str, new_content: str) -> Dict[str, Any]:
        """
        Replace content in a core memory section.

        Args:
            section: Section name
            old_content: Content to replace
            new_content: New content

        Returns:
            Dictionary with operation result
        """
        success = self.core_memory.replace(section, old_content, new_content)

        if success:
            return {
                "status": "success",
                "message": f"Replaced content in {section}",
                "section": section
            }
        else:
            raise ValueError(f"Could not find old_content in section '{section}'")

    def _archival_memory_insert(self, content: str) -> Dict[str, Any]:
        """
        Insert content into archival memory.

        Args:
            content: Content to insert

        Returns:
            Dictionary with insertion info
        """
        doc_id = self.archival_storage.insert(content)

        return {
            "status": "success",
            "message": "Content inserted into archival memory",
            "document_id": doc_id
        }

    def _archival_memory_search(self, query: str, page: int = 0) -> Dict[str, Any]:
        """
        Search archival memory.

        Args:
            query: Search query
            page: Page number for pagination

        Returns:
            Dictionary with search results
        """
        offset = page * self.page_size
        results = self.archival_storage.search(query, limit=self.page_size, offset=offset)

        return {
            "status": "success",
            "query": query,
            "page": page,
            "results_count": len(results),
            "results": [
                {
                    "content": r['content'],
                    "similarity": r.get('similarity', 0.0)
                }
                for r in results
            ]
        }

    def _conversation_search(self, query: str, page: int = 0) -> Dict[str, Any]:
        """
        Search conversation history.

        Args:
            query: Search query
            page: Page number for pagination

        Returns:
            Dictionary with search results
        """
        offset = page * self.page_size
        results = self.recall_storage.search_messages(query, limit=self.page_size, offset=offset)

        return {
            "status": "success",
            "query": query,
            "page": page,
            "results_count": len(results),
            "results": [
                {
                    "role": r['role'],
                    "content": r['content'],
                    "timestamp": str(r.get('timestamp', ''))
                }
                for r in results
            ]
        }

    def parse_function_call(self, response: Any) -> Optional[Tuple[str, Dict[str, Any]]]:
        """
        Parse a function call from the LLM response.

        Args:
            response: LLM response object (OpenAI format)

        Returns:
            Tuple of (function_name, arguments) or None if no function call
        """
        # Handle OpenAI chat completion format
        if hasattr(response, 'choices') and len(response.choices) > 0:
            choice = response.choices[0]
            message = choice.message

            # Check for function call in the message
            if hasattr(message, 'tool_calls') and message.tool_calls:
                tool_call = message.tool_calls[0]
                function_name = tool_call.function.name
                try:
                    arguments = json.loads(tool_call.function.arguments)
                except json.JSONDecodeError:
                    arguments = {}
                return (function_name, arguments)

            # Legacy function_call format
            if hasattr(message, 'function_call') and message.function_call:
                function_name = message.function_call.name
                try:
                    arguments = json.loads(message.function_call.arguments)
                except json.JSONDecodeError:
                    arguments = {}
                return (function_name, arguments)

        return None

    def should_continue_heartbeat(self, function_name: str) -> bool:
        """
        Determine if the heartbeat should continue after executing a function.

        Args:
            function_name: Name of the executed function

        Returns:
            True if heartbeat should continue, False if control should return to user
        """
        # Only stop the heartbeat for send_message
        return function_name != "send_message"

    def format_function_result(self, function_name: str, status: str,
                              message: str, output: Any) -> str:
        """
        Format function execution result for inclusion in context.

        Args:
            function_name: Name of the function
            status: Execution status
            message: Status message
            output: Function output

        Returns:
            Formatted string for context
        """
        result_str = f"Function: {function_name}\n"
        result_str += f"Status: {status}\n"
        result_str += f"Message: {message}\n"

        if output:
            # Format output nicely
            if isinstance(output, dict):
                result_str += f"Output: {json.dumps(output, indent=2)}"
            else:
                result_str += f"Output: {output}"

        return result_str
