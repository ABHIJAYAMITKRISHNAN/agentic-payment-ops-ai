import time
import os
import openai
from src.utils import read_json, write_json

# -----------------------------
# Global Guardrails
# -----------------------------
LAST_SWITCH_TIME = 0
COOLDOWN_SECONDS = 5   # Minimal cooldown to prevent sub-second flapping
RECOVERY_COOLDOWN = 30 # How long to stay on Fast before probing Cheap

# OpenAI setup (optional, fallback if not set)
openai.api_key = os.getenv("OPENAI_API_KEY")

# -----------------------------
# LLM Reasoning (with fallback)
# -----------------------------
def ask_llm(recent_logs, failure_rate, current_gateway):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "user",
                    "content": f"""
You are a Payment Operations Manager AI.

Current gateway: {current_gateway}
Observed failure rate: {failure_rate:.2f}

Recent transaction logs:
{recent_logs}

Decide whether to Switch to Fast or Wait.
Explain your reasoning clearly and end with:

DECISION:
<Switch to Fast OR Wait>
"""
                }
            ],
            temperature=0.2,
        )

        return response["choices"][0]["message"]["content"]

    except Exception:
        # ✅ Graceful fallback (Mock LLM Logic)
        if failure_rate >= 0.2 and current_gateway == "PG_CHEAP":
            return f"""
REASONING:
The observed failure rate is {failure_rate:.2f} ({(failure_rate*100):.0f}%), which exceeds the 20% threshold.
This indicates significant instability in the {current_gateway}.
Immediate action is required to protect revenue.

DECISION:
Switch to Fast
"""
        else:
            return f"""
REASONING:
The observed failure rate is {failure_rate:.2f}, which is within acceptable limits.
Current gateway {current_gateway} is performing adequately.
No immediate intervention is required.

DECISION:
Wait
"""


# -----------------------------
# Agent Main Loop
# -----------------------------
def run_agent_brain():
    global LAST_SWITCH_TIME
    print("🧠 Agent started (Background Thread)...")

    while True:
        try:
            # 1. READ CONFIG FIRST
            config = read_json("data/config.json")
            
            # 🛑 STOP CHECK: Is the AI explicitly disabled?
            if config.get("ai_disabled", False):
                time.sleep(2)
                continue

            # 2. Read Logs
            logs = read_json("data/logs.json")

            if len(logs) < 5:
                time.sleep(3)
                continue

            # ✅ Look at last 20 logs for general stability
            recent_logs = logs[-20:]

            # 3. Calculate Failure Rate
            failures = [l for l in recent_logs if l.get("status", "").upper() == "FAILED"]
            
            if len(recent_logs) > 0:
                failure_rate = len(failures) / len(recent_logs)
            else:
                failure_rate = 0.0

            print(f"Stats: {len(failures)} failures in last {len(recent_logs)} txns -> Rate: {failure_rate:.2f}")

            # Get current gateway
            current_gateway = config.get("active_gateway", "PG_CHEAP")
            now = time.time()
            
            # ---------------------------------------------------------
            # 🚀 AUTO-RECOVERY LOGIC (The "Probing" Loop)
            # ---------------------------------------------------------
            # Rule 1: If on FAST for > 30s, try switching back to CHEAP
            if current_gateway == "PG_FAST" and (now - LAST_SWITCH_TIME > RECOVERY_COOLDOWN):
                print("🔄 Auto-Recovery: Probing PG_CHEAP to save costs...")
                
                config["active_gateway"] = "PG_CHEAP"
                write_json("data/config.json", config)
                LAST_SWITCH_TIME = now 
                
                thoughts = read_json("data/agent_thoughts.json")
                thoughts.append({
                    "timestamp": time.strftime("%H:%M:%S"),
                    "failure_rate": 0.0,
                    "gateway_before": "PG_FAST",
                    "final_decision": "AUTO_RECOVERY",
                    "agent_reasoning": "Testing primary gateway (PG_CHEAP) after 30s stability period."
                })
                write_json("data/agent_thoughts.json", thoughts)
                time.sleep(3) # Give it a moment to take effect
                continue 

            # Rule 2: INSTANT RETREAT (The Sensitivity Logic)
            # If we are on CHEAP and see ANY failure in the very recent logs (last 5), ABORT immediately.
            very_recent_logs = logs[-5:] # Look at just the last 5
            recent_failures = [l for l in very_recent_logs if l.get("status", "").upper() == "FAILED"]
            
            if current_gateway == "PG_CHEAP" and len(recent_failures) > 0:
                print("🚨 PROBE FAILED: Detected immediate failure on PG_CHEAP. Retreating to PG_FAST!")
                
                # Immediate Switch
                config["active_gateway"] = "PG_FAST"
                write_json("data/config.json", config)
                LAST_SWITCH_TIME = now  # <--- This RESETS the 30s timer!
                
                thoughts = read_json("data/agent_thoughts.json")
                thoughts.append({
                    "timestamp": time.strftime("%H:%M:%S"),
                    "failure_rate": failure_rate,
                    "gateway_before": "PG_CHEAP",
                    "final_decision": "INSTANT_RETREAT",
                    "agent_reasoning": f"Probe failed. Detected {len(recent_failures)} failures immediately after switching to Cheap. Reverting to Fast for 30s."
                })
                write_json("data/agent_thoughts.json", thoughts)
                time.sleep(3)
                continue
            # ---------------------------------------------------------

            # --- Normal Reasoning Flow (Fallback if no instant trigger) ---
            llm_response = ask_llm(recent_logs, failure_rate, current_gateway)
            
            # --- Decide ---
            decision = "WAIT"
            if "DECISION:" in llm_response and "Switch" in llm_response:
                decision = "SWITCH_TO_FAST"

            # --- Act ---
            if decision == "SWITCH_TO_FAST" and current_gateway == "PG_CHEAP":
                if now - LAST_SWITCH_TIME > COOLDOWN_SECONDS:
                    print("⚠️ ACTION: Switching gateway to PG_FAST")
                    config["active_gateway"] = "PG_FAST"
                    write_json("data/config.json", config)
                    LAST_SWITCH_TIME = now
                else:
                    print("⏸️ Action skipped (Cooldown active)")
            
            # --- Learn / Log ---
            thoughts = read_json("data/agent_thoughts.json")
            thoughts.append({
                "timestamp": time.strftime("%H:%M:%S"),
                "failure_rate": round(failure_rate, 2),
                "gateway_before": current_gateway,
                "final_decision": decision,
                "agent_reasoning": llm_response.strip()
            })
            write_json("data/agent_thoughts.json", thoughts)

            time.sleep(5)

        except Exception as e:
            print("Agent Error:", e)
            time.sleep(3)

if __name__ == "__main__":
    run_agent_brain()