"""
Queue Manager for FIFO message history with eviction and summarization.
"""
from typing import List, Dict, Any, Optional, Callable
from utils.token_counter import TokenCounter
from persistence.storage_interface import RecallStorage


class QueueManager:
    """
    Manages the FIFO queue of messages with memory pressure detection
    and automatic eviction/summarization when context limit is reached.
    """

    def __init__(self,
                 max_tokens: int,
                 token_counter: TokenCounter,
                 recall_storage: RecallStorage,
                 summarize_func: Optional[Callable[[str], str]] = None,
                 warning_threshold: float = 0.7,
                 flush_threshold: float = 0.95):
        """
        Initialize the Queue Manager.

        Args:
            max_tokens: Maximum token limit for the context window
            token_counter: TokenCounter instance for counting tokens
            recall_storage: Storage backend for persisting evicted messages
            summarize_func: Function to call LLM for summarization
            warning_threshold: Percentage of max_tokens to trigger warning (default 0.7)
            flush_threshold: Percentage of max_tokens to trigger eviction (default 0.95)
        """
        self.max_tokens = max_tokens
        self.token_counter = token_counter
        self.recall_storage = recall_storage
        self.summarize_func = summarize_func
        self.warning_threshold = warning_threshold
        self.flush_threshold = flush_threshold

        # The queue: [Summary (index 0), Message1, Message2, ...]
        self.queue: List[Dict[str, Any]] = [
            {
                'role': 'system',
                'content': 'Conversation summary: No previous interactions.'
            }
        ]

    def add_message(self, role: str, content: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Add a message to the queue and check for memory pressure.

        Args:
            role: Role of the message (user, assistant, system, function)
            content: Content of the message
            metadata: Optional metadata dictionary

        Returns:
            True if memory pressure warning was triggered
        """
        message = {
            'role': role,
            'content': content
        }
        if metadata:
            message['metadata'] = metadata

        self.queue.append(message)

        # Check for memory pressure
        return self._check_memory_pressure()

    def _check_memory_pressure(self) -> bool:
        """
        Check if context is approaching limit and inject warning if needed.

        Returns:
            True if warning was injected, False otherwise
        """
        current_tokens = self.token_counter.count_message_tokens(self.queue)

        # Check if we need to inject a warning
        if current_tokens > self.max_tokens * self.warning_threshold:
            # Check if the last message is already a memory pressure warning
            if not (self.queue and self.queue[-1].get('role') == 'system' and
                   'Memory pressure' in self.queue[-1].get('content', '')):
                # Inject memory pressure warning
                warning_msg = {
                    'role': 'system',
                    'content': 'System Alert: Memory pressure detected. Save important data immediately.'
                }
                self.queue.append(warning_msg)
                return True

        # Check if we need to evict
        if current_tokens >= self.max_tokens * self.flush_threshold:
            self._evict_messages()

        return False

    def _evict_messages(self):
        """
        Evict old messages from the queue and update the summary.
        This is the core logic for maintaining long-term memory.
        """
        if len(self.queue) <= 1:
            # Nothing to evict (only summary remains)
            return

        # Calculate how many messages to evict (evict oldest 1/3 of messages)
        num_to_evict = max(1, (len(self.queue) - 1) // 3)

        # Extract the current summary (index 0)
        current_summary = self.queue[0]['content']

        # Extract messages to evict (skip index 0 which is the summary)
        evicted_messages = self.queue[1:num_to_evict + 1]

        # Create a text representation of evicted messages
        evicted_text = self._format_messages_for_summary(evicted_messages)

        # Generate new summary
        new_summary = self._generate_summary(current_summary, evicted_text)

        # Persist evicted messages to Recall Storage
        for msg in evicted_messages:
            self.recall_storage.insert_message(
                role=msg['role'],
                content=msg['content'],
                metadata=msg.get('metadata')
            )

        # Update the queue: [New Summary, Remaining Messages...]
        self.queue = [
            {'role': 'system', 'content': new_summary}
        ] + self.queue[num_to_evict + 1:]

    def _format_messages_for_summary(self, messages: List[Dict[str, Any]]) -> str:
        """
        Format messages into a readable text for summarization.

        Args:
            messages: List of message dictionaries

        Returns:
            Formatted text representation
        """
        lines = []
        for msg in messages:
            role = msg['role']
            content = msg['content']
            lines.append(f"{role.upper()}: {content}")
        return "\n".join(lines)

    def _generate_summary(self, current_summary: str, evicted_text: str) -> str:
        """
        Generate a new summary by combining the current summary with evicted messages.

        Args:
            current_summary: The existing summary
            evicted_text: Formatted text of evicted messages

        Returns:
            New summary text
        """
        if self.summarize_func:
            # Use LLM to generate a recursive summary
            prompt = f"""Summarize the following interaction based on the previous summary.
Focus on key facts, decisions, and important information.

Previous Summary:
{current_summary}

New Interactions to Incorporate:
{evicted_text}

Generate a concise updated summary:"""

            try:
                new_summary = self.summarize_func(prompt)
                return new_summary
            except Exception as e:
                # Fallback: concatenate summaries
                return f"{current_summary}\n\nRecent activity: {evicted_text[:500]}..."
        else:
            # Simple concatenation fallback
            return f"{current_summary}\n\nRecent activity: {evicted_text[:500]}..."

    def get_queue(self) -> List[Dict[str, Any]]:
        """
        Get the current queue.

        Returns:
            List of message dictionaries
        """
        return self.queue.copy()

    def get_queue_size(self) -> int:
        """
        Get current token count of the queue.

        Returns:
            Number of tokens in the queue
        """
        return self.token_counter.count_message_tokens(self.queue)

    def clear_queue(self, keep_summary: bool = True):
        """
        Clear the queue, optionally keeping the summary.

        Args:
            keep_summary: If True, keep the summary message at index 0
        """
        if keep_summary and self.queue:
            self.queue = [self.queue[0]]
        else:
            self.queue = [
                {
                    'role': 'system',
                    'content': 'Conversation summary: No previous interactions.'
                }
            ]

    def set_summary(self, summary: str):
        """
        Manually set the summary.

        Args:
            summary: New summary text
        """
        if self.queue:
            self.queue[0] = {'role': 'system', 'content': summary}
        else:
            self.queue = [{'role': 'system', 'content': summary}]

    def get_summary(self) -> str:
        """
        Get the current summary.

        Returns:
            Current summary text
        """
        if self.queue:
            return self.queue[0]['content']
        return ""

    def get_usage_percentage(self) -> float:
        """
        Get the current context usage as a percentage.

        Returns:
            Usage percentage (0.0 to 1.0)
        """
        current_tokens = self.token_counter.count_message_tokens(self.queue)
        return min(1.0, current_tokens / self.max_tokens)
