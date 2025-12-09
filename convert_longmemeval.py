
import json
import sys
from datetime import datetime

def parse_longmemeval_date(date_str):
    """
    Parses date string from longmemeval format: "2023/05/20 (Sat) 02:21"
    """
    try:
        # %Y/%m/%d (%a) %H:%M
        # Note: (%a) matches the abbreviated weekday (Sat, Sun, etc.)
        return datetime.strptime(date_str, "%Y/%m/%d (%a) %H:%M")
    except ValueError as e:
        print(f"Warning: Could not parse date '{date_str}': {e}", file=sys.stderr)
        return datetime.now()

def convert_longmemeval(input_file, output_file):
    print(f"Reading {input_file}...")
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error reading {input_file}: {e}")
        return

    output_data = {}
    
    print(f"Processing {len(data)} items...")
    
    for item in data:
        question_id = item.get('question_id')
        if not question_id:
            continue
            
        # Use question_id as the conversation ID, e.g., "conv-e47becba"
        conv_key = f"{question_id}"
        
        output_data[conv_key] = {}
        
        haystack_sessions = item.get('haystack_sessions', [])
        haystack_dates = item.get('haystack_dates', [])
        
        # Verify alignment
        if len(haystack_sessions) != len(haystack_dates):
            print(f"Warning: Mismatch in sessions ({len(haystack_sessions)}) and dates ({len(haystack_dates)}) for {conv_key}. Using minimum length.")
        
        count = min(len(haystack_sessions), len(haystack_dates))
        
        for idx in range(count):
            session_msgs_raw = haystack_sessions[idx]
            date_str = haystack_dates[idx]
            
            base_timestamp = parse_longmemeval_date(date_str)
            
            formatted_messages = []
            
            for msg_idx, msg in enumerate(session_msgs_raw):
                role = msg.get('role')
                content = msg.get('content')
                
                # Increment timestamp slightly to preserve order
                # msg_timestamp = base_timestamp + timedelta(seconds=msg_idx)
                msg_timestamp = base_timestamp.replace(second=(base_timestamp.second + msg_idx) % 60)
                
                formatted_msg = {
                    "role": role,
                    "content": content,
                    "timestamp": msg_timestamp.strftime("%Y-%m-%d %H:%M:%S")
                }
                
                formatted_messages.append(formatted_msg)
            
            # Use session_{idx+1} to be 1-based like locomo
            session_key = f"session_{idx + 1}"
            output_data[conv_key][session_key] = formatted_messages

    print(f"Writing output to {output_file}...")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    print(f"Successfully converted {len(output_data)} conversations to {output_file}")

if __name__ == "__main__":
    INPUT_FILE = "longmemeval_s_cleaned.json"
    OUTPUT_FILE = "formatted_longmemeval.json"
    convert_longmemeval(INPUT_FILE, OUTPUT_FILE)
