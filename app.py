import streamlit as st
import threading
import time
import json
import pandas as pd

# Import logic from your other modules
from src.simulator import run_simulation
from src.agent import run_agent_brain
from src.utils import read_json, write_json 

# ---------------------------------------------------------
# 🚀 NEW: HARD RESET ON STARTUP
# This runs only once when you first open the app to clear old data.
# ---------------------------------------------------------
if "initialized" not in st.session_state:
    print("🧹 Performing Startup Cleanup...")
    
    # 1. Reset Config to Default (PG_CHEAP)
    write_json("data/config.json", {
        "active_gateway": "PG_CHEAP",
        "status": "running",
        "ai_disabled": True,       # Start with AI Disabled
        "risk_sensitivity": 20     # Default sensitivity
    })
    
    # 2. Clear all History
    write_json("data/logs.json", [])
    write_json("data/agent_thoughts.json", [])
    
    # 3. Mark as initialized so we don't reset again while using the app
    st.session_state.initialized = True
    st.session_state.ai_enabled = False # Ensure UI Toggle starts OFF

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

# ---------------- Sidebar ----------------
st.sidebar.title("⚙️ AI Control Panel")

# --- TOGGLE SWITCH LOGIC ---
if "ai_enabled" not in st.session_state:
    st.session_state.ai_enabled = False

ai_mode = st.sidebar.toggle("🧠 AI Agent Enabled", value=st.session_state.ai_enabled)

if ai_mode != st.session_state.ai_enabled:
    st.session_state.ai_enabled = ai_mode
    current_config = read_json("data/config.json")
    
    if not ai_mode:
        # ❌ TOGGLE OFF
        st.sidebar.warning("AI Deactivated. Resetting to Standard Gateway...")
        current_config["active_gateway"] = "PG_CHEAP"
        current_config["status"] = "running"
        current_config["ai_disabled"] = True  
        write_json("data/config.json", current_config)
        write_json("data/logs.json", [])
        write_json("data/agent_thoughts.json", [])
        time.sleep(1)
        st.rerun()
    else:
        # ✅ TOGGLE ON
        st.sidebar.success("AI Activated! Monitoring for failures...")
        current_config["ai_disabled"] = False
        write_json("data/config.json", current_config)

# --- Auto Refresh ---
st.sidebar.markdown("---")
auto_refresh = st.sidebar.toggle("Auto Refresh Dashboard", value=True)

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

# ---------------- TABS LAYOUT ----------------
tab1, tab2 = st.tabs(["📊 Live Monitor & Business Impact", "🧠 AI Audit Log"])

# ==========================================
# TAB 1: LIVE MONITORING
# ==========================================
with tab1:
    if len(logs) > 0:
        df = pd.DataFrame(logs)
    else:
        df = pd.DataFrame(columns=["timestamp", "gateway", "status", "error_code", "amount"])

    # --- 1. System Metrics ---
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
    col5.metric("🧠 Agent Status", "ACTIVE" if ai_mode else "STANDBY")

    # --- 2. Alert Banner ---
    if failure_rate > 30:
        st.error("🚨 CRITICAL ALERT: High payment failure rate detected. AI intervention active.")
    elif failure_rate > 15:
        st.warning("⚠️ Warning: Elevated failure rate. Monitoring closely.")
    else:
        st.success("🟢 System Healthy")

    st.markdown("---")

    # --- 3. BUSINESS IMPACT SCOREBOARD ---
    st.subheader("💰 Business Impact Analysis")
    
    if len(df) > 0 and "amount" in df.columns:
        fast_success = df[(df["gateway"] == "PG_FAST") & (df["status"] == "SUCCESS")]
        
        rescued_revenue = fast_success["amount"].sum()
        num_fast_txns = len(df[df["gateway"] == "PG_FAST"])
        
        # Cost Logic: Extra $0.40 per txn for using Fast
        optimization_cost = num_fast_txns * 0.40 
        
        b_col1, b_col2, b_col3 = st.columns(3)
        b_col1.metric("🛡️ Revenue Protected (via AI)", f"${rescued_revenue:,.2f}")
        b_col2.metric("💸 Optimization Cost", f"${optimization_cost:,.2f}")
        b_col3.metric("📈 Net Value Created", f"${(rescued_revenue - optimization_cost):,.2f}", delta_color="normal")
        
        st.caption("*Metrics calculated based on successful interventions routed to Premium Gateway.*")
    else:
        st.info("Waiting for AI intervention data...")

    st.markdown("---")

    # --- 4. Charts ---
    chart_col1, chart_col2 = st.columns(2)
    with chart_col1:
        st.markdown("#### Transaction Status Distribution")
        if len(df) > 0:
            st.bar_chart(df["status"].value_counts())
        else:
            st.info("Waiting for data...")

    with chart_col2:
        st.markdown("#### 📉 Success vs Failure Trend")
        if len(df) > 0:
            df_time = df.copy()
            df_time["time"] = pd.to_datetime(df_time["timestamp"], format="%H:%M:%S", errors="coerce")
            df_time = df_time.dropna(subset=["time"])
            df_time["bucket"] = df_time["time"].dt.floor("5S")
            success_series = df_time[df_time["status"] == "SUCCESS"].groupby("bucket").size()
            failed_series = df_time[df_time["status"] == "FAILED"].groupby("bucket").size()
            chart_df = pd.DataFrame({"Success": success_series, "Failed": failed_series}).fillna(0)
            st.line_chart(chart_df)
        else:
            st.info("Waiting for data...")

    st.markdown("---")
    st.subheader("📋 Live Transaction Logs")
    if len(df) > 0:
        st.dataframe(df.tail(10), use_container_width=True)
    else:
        st.write("No transactions yet.")


# ==========================================
# TAB 2: AI AUDIT LOG
# ==========================================
with tab2:
    st.subheader("🧠 AI Decision History (Audit Log)")
    
    if len(thoughts) > 0:
        st.markdown("### 🔍 Most Recent Analysis")
        latest = thoughts[-1]
        
        # Check if it was an Auto-Recovery decision
        if latest.get("final_decision") in ["AUTO_RECOVERY", "INSTANT_RETREAT"]:
             # Special highlighting for automated system actions
             icon = "🔄" if latest.get("final_decision") == "AUTO_RECOVERY" else "🚨"
             st.info(f"{icon} **{latest.get('final_decision')} ACTIVATED at {latest.get('timestamp')}**\n\nReasoning: {latest.get('agent_reasoning')}")
        else:
            with st.container(border=True):
                cols = st.columns([1, 4])
                with cols[0]:
                    st.markdown(f"**⏱️ Time:** {latest.get('timestamp')}")
                    st.markdown(f"**🤖 Decision:** `{latest.get('final_decision')}`")
                with cols[1]:
                    st.markdown("**🧠 Reasoning Trace:**")
                    st.info(latest.get('agent_reasoning'))

        st.markdown("---")
        
        st.markdown("### 📜 Decision History")
        audit_df = pd.DataFrame(thoughts)
        if not audit_df.empty:
            cols = ["timestamp", "gateway_before", "failure_rate", "final_decision", "agent_reasoning"]
            audit_df = audit_df[[c for c in cols if c in audit_df.columns]]
            st.dataframe(audit_df.sort_values(by="timestamp", ascending=False), use_container_width=True, height=400)
    else:
        st.info("ℹ️ No AI decisions recorded yet.")


# ---------------- Footer ----------------
st.markdown("---")
st.markdown(
    "<center>⚡ Agentic AI for Smart Payment Operations | Team Autonomous Payment Ops</center>",
    unsafe_allow_html=True
)

# ---------------- Auto Refresh ----------------
if auto_refresh:
    time.sleep(2)
    st.rerun()