import json
import os
import time

def load_json(filepath):
    """
    Safely reads a JSON file. Retries if the file is momentarily locked or empty.
    """
    attempts = 0
    while attempts < 3:
        try:
            if not os.path.exists(filepath):
                return {}
            
            with open(filepath, 'r') as f:
                data = json.load(f)
            return data
        except (json.JSONDecodeError, IOError):
            # If file is being written to, wait a tiny bit and retry
            time.sleep(0.1)
            attempts += 1
    return {} # Return empty dict/list if it keeps failing

def save_json(filepath, data):
    """
    Overwrites the JSON file completely.
    """
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=4)

def append_json_log(filepath, new_entry):
    """
    Specific helper to append a log entry safely.
    """
    # 1. Read existing
    data = load_json(filepath)
    if not isinstance(data, list):
        data = []
    
    # 2. Append
    data.append(new_entry)
    
    # 3. Limit size (Optional: Keep only last 100 to keep it fast)
    if len(data) > 100:
        data = data[-100:]
        
    # 4. Write back
    save_json(filepath, data)