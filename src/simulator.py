import time
import random
import uuid
from datetime import datetime
from src.utils import load_json, append_json_log

# Configuration
CONFIG_PATH = 'data/config.json'
LOGS_PATH = 'data/logs.json'

def generate_transaction(gateway):
    """
    Creates a single fake transaction.
    Logic: 
    - PG_CHEAP: High failure rate (simulating a bad server)
    - PG_FAST: Low failure rate (simulating a premium server)
    """
    txn_id = str(uuid.uuid4())[:8]
    timestamp = datetime.now().strftime("%H:%M:%S")
    amount = random.randint(10, 500)
    
    status = "SUCCESS"
    error_code = None
    error_message = None

    # --- THE CHAOS LOGIC ---
    if gateway == "PG_CHEAP":
        # 40% chance of failure
        if random.random() < 0.4: 
            status = "FAILED"
            error_code = "503_SERVICE_UNAVAILABLE"
            error_message = "Upstream provider timed out after 3000ms"
            
    elif gateway == "PG_FAST":
        # 99% Success (Premium service)
        if random.random() < 0.01:
            status = "FAILED"
            error_code = "402_INSUFFICIENT_FUNDS" # User error, not system error
            error_message = "Card declined by issuer"

    return {
        "id": txn_id,
        "timestamp": timestamp,
        "amount": amount,
        "gateway": gateway,
        "status": status,
        "error_code": error_code,
        "error_message": error_message
    }

def run_simulation():
    """
    The main loop that Person C will run in a background thread.
    """
    print("🚀 Simulator Thread Started...")
    
    while True:
        try:
            # 1. Read the current configuration
            config = load_json(CONFIG_PATH)
            current_gateway = config.get("active_gateway", "PG_CHEAP")
            
            # 2. Generate a transaction
            txn = generate_transaction(current_gateway)
            
            # 3. Log it
            append_json_log(LOGS_PATH, txn)
            
            # 4. Debug print (so you can see it in terminal)
            print(f"[{txn['timestamp']}] {txn['gateway']} -> {txn['status']}")

            # 5. Wait (Don't spam! 1 txn every 2 seconds is enough for a demo)
            time.sleep(2)
            
        except Exception as e:
            print(f"Simulator Error: {e}")
            time.sleep(1)

# This allows you to run this file directly to test it without Person C
if __name__ == "__main__":
    run_simulation()