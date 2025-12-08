"""
Token counting utility for managing context window limits.
"""
import tiktoken
from typing import List, Dict, Any


class TokenCounter:
    """Handles token counting for messages and text using tiktoken."""

    def __init__(self, model: str = "gpt-4"):
        """
        Initialize the token counter with a specific model encoding.

        Args:
            model: The OpenAI model name (e.g., "gpt-4", "gpt-3.5-turbo")
        """
        try:
            self.encoding = tiktoken.encoding_for_model(model)
        except KeyError:
            # Fallback to cl100k_base for unknown models (GPT-4 encoding)
            self.encoding = tiktoken.get_encoding("cl100k_base")
        self.model = model

    def count_tokens(self, text: str) -> int:
        """
        Count tokens in a text string.

        Args:
            text: The text to count tokens for

        Returns:
            Number of tokens
        """
        if not text:
            return 0
        return len(self.encoding.encode(text))

    def count_message_tokens(self, messages: List[Dict[str, Any]]) -> int:
        """
        Count tokens in a list of messages following OpenAI's format.

        Args:
            messages: List of message dictionaries with 'role' and 'content' keys

        Returns:
            Total number of tokens including message formatting overhead
        """
        if not messages:
            return 0

        num_tokens = 0

        for message in messages:
            # Every message follows <|im_start|>{role}\n{content}<|im_end|>\n
            num_tokens += 4  # Base overhead per message

            for key, value in message.items():
                if isinstance(value, str):
                    num_tokens += self.count_tokens(value)
                elif isinstance(value, list):
                    # Handle function calls with multiple arguments
                    for item in value:
                        if isinstance(item, str):
                            num_tokens += self.count_tokens(item)
                        elif isinstance(item, dict):
                            num_tokens += self.count_tokens(str(item))
                elif isinstance(value, dict):
                    num_tokens += self.count_tokens(str(value))

        # Every reply is primed with <|im_start|>assistant
        num_tokens += 2

        return num_tokens

    def estimate_tokens_remaining(self, messages: List[Dict[str, Any]],
                                 max_tokens: int) -> int:
        """
        Estimate how many tokens are remaining in the context window.

        Args:
            messages: Current message list
            max_tokens: Maximum context window size

        Returns:
            Estimated remaining tokens
        """
        used = self.count_message_tokens(messages)
        return max(0, max_tokens - used)

    def truncate_text(self, text: str, max_tokens: int) -> str:
        """
        Truncate text to fit within a token limit.

        Args:
            text: Text to truncate
            max_tokens: Maximum number of tokens

        Returns:
            Truncated text
        """
        if not text:
            return ""

        tokens = self.encoding.encode(text)
        if len(tokens) <= max_tokens:
            return text

        truncated_tokens = tokens[:max_tokens]
        return self.encoding.decode(truncated_tokens)
