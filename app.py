import streamlit as st
import threading
import time
import json
import pandas as pd

# Import Person A & B functions
from src.simulator import run_simulation
from src.agent import run_agent_brain

st.set_page_config(page_title="Agentic Payment Ops AI", layout="wide")

# ---------------- Thread Start (only once) ----------------
if "started" not in st.session_state:
    sim_thread = threading.Thread(target=run_simulation, daemon=True)
    agent_thread = threading.Thread(target=run_agent_brain, daemon=True)

    sim_thread.start()
    agent_thread.start()

    st.session_state.started = True

# ---------------- Utility function ----------------
def read_json(path):
    try:
        with open(path, "r") as f:
            return json.load(f)
    except:
        return []

# ---------------- UI ----------------
st.title("💳 Agentic AI for Smart Payment Operations")
st.subheader("Team: Autonomous Payment Ops")

config = read_json("data/config.json")
logs = read_json("data/logs.json")
thoughts = read_json("data/agent_thoughts.json")

# ---------------- KPIs ----------------
col1, col2 = st.columns(2)

if len(logs) > 0:
    df = pd.DataFrame(logs)
    success_rate = round((df["status"] == "SUCCESS").mean() * 100, 2)
else:
    df = pd.DataFrame(columns=["status"])
    success_rate = 0

with col1:
    st.metric("✅ Success Rate (%)", success_rate)

with col2:
    st.metric("⚙️ Active Gateway", config.get("active_gateway", "Unknown"))

# ---------------- Chart ----------------
st.subheader("📊 Transaction Status Chart")

if len(df) > 0:
    chart_data = df["status"].value_counts()
    st.bar_chart(chart_data)
else:
    st.info("Waiting for transaction data...")

# ---------------- Agent Thoughts ----------------
st.subheader("🧠 Agent Thought Process")

if len(thoughts) > 0:
    for t in thoughts[-5:][::-1]:
        st.chat_message("assistant").write(t)
else:
    st.write("No agent decisions yet...")

# ---------------- Auto Refresh ----------------
time.sleep(2)
st.rerun()