import streamlit as st
import threading
import time
import json
import pandas as pd

from src.simulator import run_simulation
from src.agent import run_agent_brain

# ---------------- Page Config ----------------
st.set_page_config(
    page_title="Agentic Payment Ops AI",
    page_icon="🤖",
    layout="wide"
)

# ---------------- Start Threads ----------------
if "started" not in st.session_state:
    threading.Thread(target=run_simulation, daemon=True).start()
    threading.Thread(target=run_agent_brain, daemon=True).start()
    st.session_state.started = True

# ---------------- Utils ----------------
def read_json(path):
    try:
        with open(path, "r") as f:
            return json.load(f)
    except:
        return []

# ---------------- Sidebar ----------------
st.sidebar.title("⚙️ AI Control Panel")
st.sidebar.markdown("### System Mode")
st.sidebar.selectbox("Mode", ["Autonomous", "Advisory"])
st.sidebar.slider("Risk Sensitivity", 0, 100, 40)
st.sidebar.toggle("Auto Refresh", True)

st.sidebar.markdown("---")
st.sidebar.markdown("### Manual Override")
st.sidebar.selectbox("Force Gateway", ["AUTO", "PG_CHEAP", "PG_FAST"])

st.sidebar.markdown("---")
st.sidebar.info("This AI monitors live payments and autonomously optimizes routing.")

# ---------------- Header ----------------
st.markdown("""
<h1 style='text-align:center;'>🤖 Agentic AI Payment Operations Control Center</h1>
<p style='text-align:center;color:gray;'>Real-time autonomous monitoring & decision system</p>
""", unsafe_allow_html=True)

st.markdown("---")

# ---------------- Read Data ----------------
config = read_json("data/config.json")
logs = read_json("data/logs.json")
thoughts = read_json("data/agent_thoughts.json")

if len(logs) > 0:
    df = pd.DataFrame(logs)
else:
    df = pd.DataFrame(columns=["timestamp","gateway","status","error_code"])

# ---------------- Metrics ----------------
if len(df) > 0:
    success_rate = round((df["status"] == "SUCCESS").mean() * 100, 2)
    failure_rate = round((df["status"] == "FAILED").mean() * 100, 2)
    total_txns = len(df)
else:
    success_rate = 0
    failure_rate = 0
    total_txns = 0

col1, col2, col3, col4, col5 = st.columns(5)

col1.metric("✅ Success Rate", f"{success_rate}%")
col2.metric("❌ Failure Rate", f"{failure_rate}%")
col3.metric("📦 Total Txns", total_txns)
col4.metric("⚙️ Active Gateway", config.get("active_gateway", "Unknown"))
col5.metric("🧠 Agent Status", "RUNNING")

# ---------------- Alert Banner ----------------
if failure_rate > 30:
    st.error("🚨 CRITICAL ALERT: High payment failure rate detected. AI intervention active.")
elif failure_rate > 15:
    st.warning("⚠️ Warning: Elevated failure rate. Monitoring closely.")
else:
    st.success("🟢 System Healthy")

st.markdown("---")

# ---------------- Charts ----------------
st.subheader("📈 Payment Performance Analytics")

chart_col1, chart_col2 = st.columns(2)

with chart_col1:
    st.markdown("#### Transaction Status Distribution")
    if len(df) > 0:
        st.bar_chart(df["status"].value_counts())
    else:
        st.info("Waiting for data...")

with chart_col2:
    st.markdown("#### 📉 Success vs Failure Trend (last 5-sec windows)")

    if len(df) > 0:
        df_time = df.copy()

        # Convert timestamp string to datetime (today’s date + time)
        df_time["time"] = pd.to_datetime(df_time["timestamp"], format="%H:%M:%S", errors="coerce")

        # Drop bad rows
        df_time = df_time.dropna(subset=["time"])

        # Create time bucket (5 second window)
        df_time["bucket"] = df_time["time"].dt.floor("5S")

        # Count success & failed per bucket
        success_series = df_time[df_time["status"] == "SUCCESS"].groupby("bucket").size()
        failed_series = df_time[df_time["status"] == "FAILED"].groupby("bucket").size()

        chart_df = pd.DataFrame({
            "Success": success_series,
            "Failed": failed_series
        }).fillna(0)

        st.line_chart(chart_df)

    else:
        st.info("Waiting for data...")

st.markdown("---")

# ---------------- AI Reasoning ----------------
st.subheader("🧠 AI Decision Engine")

if len(thoughts) > 0:
    for t in thoughts[-5:][::-1]:
        with st.expander(f"Decision @ {t.get('timestamp')}"):
            st.markdown(f"""
**Gateway Before:** {t.get('gateway_before')}  
**Failure Rate:** {t.get('failure_rate')}  
**Final Decision:** `{t.get('final_decision')}`  

**AI Reasoning:**  
{t.get('agent_reasoning')}
""")
else:
    st.info("AI is observing transactions...")

st.markdown("---")

# ---------------- Transaction Table ----------------
st.subheader("📋 Live Transaction Logs")

if len(df) > 0:
    st.dataframe(df.tail(20), use_container_width=True)
else:
    st.write("No transactions yet.")

# ---------------- Footer ----------------
st.markdown("---")
st.markdown(
    "<center>⚡ Agentic AI for Smart Payment Operations | Team Autonomous Payment Ops</center>",
    unsafe_allow_html=True
)

# ---------------- Auto Refresh ----------------
time.sleep(2)
st.rerun()