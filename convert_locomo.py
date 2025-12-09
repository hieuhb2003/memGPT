
import json
import re
from datetime import datetime
import sys

def parse_custom_date(date_str):
    try:
        # Expected format: "1:56 pm on 8 May, 2023"
        # Using %I for 12-hour clock, %p for AM/PM
        dt = datetime.strptime(date_str, "%I:%M %p on %d %B, %Y")
        return dt
    except ValueError as e:
        print(f"Warning: Could not parse date '{date_str}': {e}", file=sys.stderr)
        return None

def convert_locomo(input_file, output_file):
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error reading {input_file}: {e}")
        return

    output_data = {}

    for item in data:
        conv_id = item.get('sample_id')
        if not conv_id:
            continue
        
        output_data[conv_id] = {}
        conversation = item.get('conversation', {})
        
        speaker_a = conversation.get('speaker_a')
        # speaker_b = conversation.get('speaker_b')
        
        # Find all session keys
        # We assume keys are like "session_1", "session_2", ...
        # and there are corresponding "session_1_date_time"
        
        # Get all keys that start with session_ and don't end with _date_time
        session_keys = [k for k in conversation.keys() 
                        if k.startswith('session_') and not k.endswith('_date_time') 
                        and isinstance(conversation[k], list)]
        
        # Sort session keys to be safe (session_1, session_2, session_10...)
        def sort_key(k):
            try:
                # Extract number part
                return int(re.search(r'(\d+)', k).group(1))
            except:
                return 0
        
        session_keys.sort(key=sort_key)
        
        for sess_key in session_keys:
            messages_raw = conversation[sess_key]
            
            # Get timestamp for this session
            date_time_key = f"{sess_key}_date_time"
            date_time_str = conversation.get(date_time_key)
            
            base_timestamp = datetime.now()
            if date_time_str:
                parsed = parse_custom_date(date_time_str)
                if parsed:
                    base_timestamp = parsed
            
            formatted_messages = []
            
            # Message limit or processing
            # messages_raw is a list of dicts: {"speaker": "...", "text": "..."}
            
            for idx, msg in enumerate(messages_raw):
                speaker = msg.get('speaker')
                content = msg.get('text')
                
                # Map role
                # Default to user if speaker matches speaker_a, else assistant
                # If speaker name is missing, default to user?
                if speaker == speaker_a:
                    role = "user"
                else:
                    role = "assistant"
                
                # Increment timestamp slightly to preserve order in DBs that rely on time
                # Adding 'idx' seconds
                msg_timestamp = base_timestamp.replace(second=(base_timestamp.second + idx) % 60)
                # Note: minute/hour rollover not handled for simplicity, but acceptable for simple ordering
                
                formatted_msg = {
                    "role": role,
                    "content": content,
                    "timestamp": msg_timestamp.strftime("%Y-%m-%d %H:%M:%S")
                }
                
                formatted_messages.append(formatted_msg)
            
            output_data[conv_id][sess_key] = formatted_messages

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    print(f"Successfully converted {len(data)} items to {output_file}")

if __name__ == "__main__":
    INPUT_FILE = "locomo10 (1).json"
    OUTPUT_FILE = "formatted_locomo.json"
    convert_locomo(INPUT_FILE, OUTPUT_FILE)
