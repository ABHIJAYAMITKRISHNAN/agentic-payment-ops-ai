import time
import os
import openai
from utils import read_json, write_json

# -----------------------------
# Global Guardrails
# -----------------------------
LAST_SWITCH_TIME = 0
COOLDOWN_SECONDS = 60  # seconds

# OpenAI setup (LLM-capable, with fallback)
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
You are a Payment Operations Manager.

Current gateway: {current_gateway}
Observed failure rate (last 10 txns): {failure_rate:.2f}

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
        # ✅ Graceful fallback (mock LLM)
        if failure_rate >= 0.3 and current_gateway == "PG_CHEAP":
            return f"""
REASONING:
The observed failure rate is {failure_rate:.2f}, which is significantly above the
acceptable threshold. This suggests sustained degradation on the cheap gateway.
Continuing to route traffic here may lead to further payment failures and revenue loss.

DECISION:
Switch to Fast
"""
        else:
            return f"""
REASONING:
The observed failure rate is {failure_rate:.2f}, which does not indicate
persistent degradation requiring immediate intervention.

DECISION:
Wait
"""


# -----------------------------
# Agent Main Loop
# -----------------------------
def run_agent_brain():
    global LAST_SWITCH_TIME
    print("🧠 Agent started...")

    while True:
        logs = read_json("data/logs.json")

        # Not enough data yet
        if len(logs) < 5:
            time.sleep(3)
            continue

        recent_logs = logs[-10:]
        failures = [l for l in recent_logs if l.get("status") == "FAILURE"]
        failure_rate = len(failures) / len(recent_logs)

        print(f"Observed failure rate: {failure_rate:.2f}")

        config = read_json("data/config.json")
        current_gateway = config.get("active_gateway")

        # --- Reason ---
        llm_response = ask_llm(recent_logs, failure_rate, current_gateway)
        print("\n🧠 AGENT THINKING:\n", llm_response)

        # --- Decide ---
        decision = "WAIT"
        if "DECISION:" in llm_response and "Switch" in llm_response:
            decision = "SWITCH_TO_FAST"

        # --- Act (with cooldown guardrail) ---
        now = time.time()

        if decision == "SWITCH_TO_FAST" and current_gateway == "PG_CHEAP":
            if now - LAST_SWITCH_TIME > COOLDOWN_SECONDS:
                print("⚠️ Switching gateway to PG_FAST (cooldown passed)")
                config["active_gateway"] = "PG_FAST"
                write_json("data/config.json", config)
                LAST_SWITCH_TIME = now
            else:
                print("⏸️ Switch skipped due to cooldown")
        else:
            print("✅ Decision: WAIT")

        # --- Learn / Log ---
        thoughts = read_json("data/agent_thoughts.json")

        thoughts.append({
            "timestamp": time.time(),
            "failure_rate": round(failure_rate, 2),
            "gateway_before": current_gateway,
            "final_decision": decision,
            "agent_reasoning": llm_response.strip()
        })

        write_json("data/agent_thoughts.json", thoughts)

        time.sleep(5)


# -----------------------------
# Entry Point
# -----------------------------
if __name__ == "__main__":
    run_agent_brain()
