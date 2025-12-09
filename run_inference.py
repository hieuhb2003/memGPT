
import json
import os
import sys
import shutil

# Ensure we can import from the current directory
sys.path.append(os.getcwd())

from agents.agent import MemGPTAgent

def main():
    # Configuration
    data_file = 'processed_locomo.json'
    conversation_id = 'conv-26'
    db_path = 'test_memgpt.db'
    chroma_path = './data/test_chroma'

    # Clean up previous run
    if os.path.exists(db_path):
        os.remove(db_path)
    if os.path.exists(chroma_path):
        shutil.rmtree(chroma_path)

    # Load data
    print(f"Loading data from {data_file}...")
    with open(data_file, 'r') as f:
        data = json.load(f)
    
    if conversation_id not in data:
        print(f"Error: Conversation {conversation_id} not found.")
        return

    conv_data = data[conversation_id]
    sessions = conv_data['conversation']
    qa_list = conv_data['qa']

    # Initialize Agent
    print("Initializing MemGPT Agent...")
    # Ensure API key is set (using logic from main.py/example.py)
    if not os.getenv("OPENAI_API_KEY"):
        # For testing, you might need to set this. 
        # I'll assumme the environment has it or the user will run it with it.
        # If not, the agent init will fail/warn.
        pass

    try:
        agent = MemGPTAgent(
            model="gpt-4",
            max_tokens=8000,
            db_path=db_path,
            chroma_path=chroma_path
        )
    except Exception as e:
        print(f"Failed to initialize agent: {e}")
        return

    # Ingest History into Archival Memory
    print("Ingesting conversation history into Archival Memory...")
    
    # Sort sessions to ensure logical order (session_1, session_2, ..., session_10)
    def parse_session_key(key):
        if '_' in key:
            try:
                return int(key.split('_')[1])
            except:
                return 0
        return 0

    sorted_session_keys = sorted(sessions.keys(), key=parse_session_key)

    for session_key in sorted_session_keys:
        session_msgs = sessions[session_key]
        # Join messages into a single document for the session
        # Format: 
        # Session: session_1
        # <timestamp>
        # <Speaker>: <Message>
        
        transcript = f"Session: {session_key}\n\n" + "\n".join(session_msgs)
        
        print(f"  Ingesting {session_key} ({len(session_msgs)} messages)...")
        agent.archival_storage.insert(transcript, metadata={"session": session_key, "type": "conversation_history"})

    print("Ingestion complete.")

    # Run Inference (QA)
    print("\nStarting Inference...")
    
    # We will run a few questions to demonstrate
    # Asking all might take too long, let's do first 3 and maybe one specific one
    test_questions = qa_list[:3] 
    
    for i, qa_item in enumerate(test_questions):
        question = qa_item['question']
        ground_truth = qa_item['ans']
        
        print(f"\n[{i+1}] Question: {question}")
        print(f"    Expected Answer: {ground_truth}")
        
        # We instruct the agent to use its archival memory
        prompt = f"Please answer the following question based on the conversation history in your archival memory: {question}"
        
        response = agent.chat(prompt)
        print(f"    Agent Answer: {response}")

    print("\nInference demonstration finished.")

if __name__ == "__main__":
    main()
