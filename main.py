#!/usr/bin/env python3
"""
MemGPT CLI - Interactive command-line interface for MemGPT.
"""
import os
import sys
import argparse
from typing import Optional
from agents.agent import MemGPTAgent


class MemGPTCLI:
    """Command-line interface for MemGPT."""

    def __init__(self, agent: MemGPTAgent):
        """
        Initialize the CLI.

        Args:
            agent: MemGPTAgent instance
        """
        self.agent = agent
        self.running = True

    def print_banner(self):
        """Print welcome banner."""
        print("=" * 70)
        print("  MemGPT - Memory-Enhanced GPT with Hierarchical Memory System")
        print("=" * 70)
        print("\nCommands:")
        print("  /help     - Show this help message")
        print("  /status   - Show memory status")
        print("  /memory   - Show core memory contents")
        print("  /reset    - Reset agent memory")
        print("  /quit     - Exit the program")
        print("\nType your message and press Enter to chat with MemGPT.\n")
        print("=" * 70)

    def print_status(self):
        """Print current memory status."""
        status = self.agent.get_queue_status()
        print("\n" + "=" * 70)
        print("Memory Status:")
        print(f"  Queue Length: {status['queue_length']} messages")
        print(f"  Token Usage: {status['token_count']}/{status['max_tokens']} "
              f"({status['usage_percentage']:.1f}%)")
        print(f"  Current Summary: {status['summary'][:100]}...")
        print("=" * 70 + "\n")

    def print_memory(self):
        """Print core memory contents."""
        memory = self.agent.get_core_memory()
        print("\n" + "=" * 70)
        print("Core Memory Contents:")
        for section, content in memory.items():
            print(f"\n[{section.upper()}]")
            print(content)
        print("=" * 70 + "\n")

    def handle_command(self, command: str) -> bool:
        """
        Handle special commands.

        Args:
            command: Command string starting with /

        Returns:
            True if should continue, False if should quit
        """
        command = command.lower().strip()

        if command == "/quit" or command == "/exit":
            print("\nGoodbye!")
            return False
        elif command == "/help":
            self.print_banner()
        elif command == "/status":
            self.print_status()
        elif command == "/memory":
            self.print_memory()
        elif command == "/reset":
            confirm = input("Are you sure you want to reset all memory? (yes/no): ")
            if confirm.lower() == "yes":
                self.agent.reset()
                print("Memory reset complete.\n")
            else:
                print("Reset cancelled.\n")
        else:
            print(f"Unknown command: {command}")
            print("Type /help to see available commands.\n")

        return True

    def run(self):
        """Run the interactive CLI loop."""
        self.print_banner()

        while self.running:
            try:
                # Get user input
                user_input = input("\nYou: ").strip()

                if not user_input:
                    continue

                # Check for commands
                if user_input.startswith("/"):
                    self.running = self.handle_command(user_input)
                    continue

                # Process message through agent
                print("\nMemGPT: ", end="", flush=True)
                response = self.agent.chat(user_input)
                print(response)

            except KeyboardInterrupt:
                print("\n\nInterrupted. Type /quit to exit.\n")
                continue
            except EOFError:
                print("\n\nGoodbye!")
                break
            except Exception as e:
                print(f"\nError: {e}")
                print("Continuing...\n")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="MemGPT - Memory-Enhanced GPT")
    parser.add_argument(
        "--api-key",
        type=str,
        default=None,
        help="OpenAI API key (defaults to OPENAI_API_KEY env var)"
    )
    parser.add_argument(
        "--model",
        type=str,
        default="gpt-4",
        help="OpenAI model to use (default: gpt-4)"
    )
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=8000,
        help="Maximum context window size (default: 8000)"
    )
    parser.add_argument(
        "--db-path",
        type=str,
        default="memgpt.db",
        help="Path to SQLite database (default: memgpt.db)"
    )
    parser.add_argument(
        "--chroma-path",
        type=str,
        default="./data/chroma",
        help="Path to ChromaDB storage (default: ./data/chroma)"
    )

    args = parser.parse_args()

    # Check for API key
    api_key = args.api_key or os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Error: OpenAI API key not found.")
        print("Please set OPENAI_API_KEY environment variable or use --api-key flag.")
        sys.exit(1)

    # Initialize agent
    print("Initializing MemGPT agent...")
    try:
        agent = MemGPTAgent(
            api_key=api_key,
            model=args.model,
            max_tokens=args.max_tokens,
            db_path=args.db_path,
            chroma_path=args.chroma_path
        )
    except Exception as e:
        print(f"Error initializing agent: {e}")
        sys.exit(1)

    # Run CLI
    cli = MemGPTCLI(agent)
    cli.run()


if __name__ == "__main__":
    main()
