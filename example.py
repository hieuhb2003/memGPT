#!/usr/bin/env python3
"""
Example usage of MemGPT programmatically.
Demonstrates various features and capabilities.
"""
import os
from agents.agent import MemGPTAgent


def example_basic_chat():
    """Example: Basic chat interaction."""
    print("=" * 70)
    print("Example 1: Basic Chat Interaction")
    print("=" * 70)

    # Initialize agent
    agent = MemGPTAgent(
        api_key=os.getenv("OPENAI_API_KEY"),
        model="gpt-4",
        max_tokens=8000
    )

    # Simple conversation
    print("\nUser: Hello! What can you do?")
    response = agent.chat("Hello! What can you do?")
    print(f"Agent: {response}\n")

    # Check memory status
    status = agent.get_queue_status()
    print(f"Memory usage: {status['usage_percentage']:.1f}%")
    print(f"Queue length: {status['queue_length']} messages\n")


def example_memory_management():
    """Example: Demonstrate memory management features."""
    print("=" * 70)
    print("Example 2: Memory Management")
    print("=" * 70)

    agent = MemGPTAgent(
        api_key=os.getenv("OPENAI_API_KEY"),
        model="gpt-4",
        max_tokens=8000
    )

    # Ask agent to remember information
    print("\nUser: My name is Alice and I love programming in Python.")
    response = agent.chat("My name is Alice and I love programming in Python.")
    print(f"Agent: {response}\n")

    # Check core memory
    memory = agent.get_core_memory()
    print("Core Memory Contents:")
    for section, content in memory.items():
        print(f"\n[{section}]")
        print(content)
    print()


def example_archival_memory():
    """Example: Using archival memory for documents."""
    print("=" * 70)
    print("Example 3: Archival Memory")
    print("=" * 70)

    agent = MemGPTAgent(
        api_key=os.getenv("OPENAI_API_KEY"),
        model="gpt-4",
        max_tokens=8000
    )

    # Store a document
    document = """
    Python is a high-level, interpreted programming language.
    It was created by Guido van Rossum and first released in 1991.
    Python's design philosophy emphasizes code readability with significant indentation.
    """

    print("\nUser: Store this information about Python in archival memory:")
    print(document)
    response = agent.chat(f"Store this information in archival memory: {document}")
    print(f"Agent: {response}\n")

    # Search archival memory
    print("\nUser: Search archival memory for information about Python's creator.")
    response = agent.chat("Search archival memory for information about Python's creator.")
    print(f"Agent: {response}\n")


def example_conversation_search():
    """Example: Search conversation history."""
    print("=" * 70)
    print("Example 4: Conversation Search")
    print("=" * 70)

    agent = MemGPTAgent(
        api_key=os.getenv("OPENAI_API_KEY"),
        model="gpt-4",
        max_tokens=8000
    )

    # Have a conversation
    messages = [
        "I just finished a great book about machine learning.",
        "What are your thoughts on neural networks?",
        "I'm particularly interested in transformers."
    ]

    for msg in messages:
        print(f"\nUser: {msg}")
        response = agent.chat(msg)
        print(f"Agent: {response}")

    # Search conversation
    print("\n\nUser: What did I mention about transformers earlier?")
    response = agent.chat("Search our conversation history for what I said about transformers.")
    print(f"Agent: {response}\n")


def example_long_conversation():
    """Example: Demonstrate memory pressure and eviction."""
    print("=" * 70)
    print("Example 5: Long Conversation (Memory Pressure)")
    print("=" * 70)

    # Use smaller max_tokens to trigger memory pressure faster
    agent = MemGPTAgent(
        api_key=os.getenv("OPENAI_API_KEY"),
        model="gpt-4",
        max_tokens=2000  # Small context to demo eviction
    )

    # Simulate a long conversation
    for i in range(5):
        msg = f"Tell me an interesting fact about topic number {i+1}."
        print(f"\nUser: {msg}")
        response = agent.chat(msg)
        print(f"Agent: {response}")

        # Show memory status
        status = agent.get_queue_status()
        print(f"[Memory: {status['usage_percentage']:.1f}%]")

    print("\n\nFinal memory status:")
    status = agent.get_queue_status()
    print(f"Usage: {status['usage_percentage']:.1f}%")
    print(f"Summary: {status['summary'][:200]}...\n")


def main():
    """Run all examples."""
    # Check for API key
    if not os.getenv("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY environment variable not set.")
        print("Please set it before running examples.")
        return

    examples = [
        ("Basic Chat", example_basic_chat),
        ("Memory Management", example_memory_management),
        ("Archival Memory", example_archival_memory),
        ("Conversation Search", example_conversation_search),
        ("Long Conversation", example_long_conversation),
    ]

    print("\nMemGPT Examples")
    print("=" * 70)
    print("\nAvailable examples:")
    for i, (name, _) in enumerate(examples, 1):
        print(f"  {i}. {name}")
    print(f"  {len(examples) + 1}. Run all examples")
    print("  0. Exit")

    while True:
        try:
            choice = input("\nSelect an example (0-6): ").strip()

            if choice == "0":
                print("Goodbye!")
                break
            elif choice == str(len(examples) + 1):
                # Run all examples
                for name, func in examples:
                    try:
                        func()
                        input("\nPress Enter to continue to next example...")
                    except Exception as e:
                        print(f"Error in example: {e}")
                        continue
            elif choice.isdigit() and 1 <= int(choice) <= len(examples):
                idx = int(choice) - 1
                try:
                    examples[idx][1]()
                except Exception as e:
                    print(f"Error: {e}")
            else:
                print("Invalid choice. Please try again.")

        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    main()
