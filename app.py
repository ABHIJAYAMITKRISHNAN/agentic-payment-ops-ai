import streamlit as st
import threading
import time
import json
import pandas as pd

# Import logic from your other modules (Functionality remains 100% same)
from src.simulator import run_simulation
from src.agent import run_agent_brain
from src.utils import read_json, write_json 

# ---------------------------------------------------------
# STARTUP CLEANUP Logic (Unchanged)
# ---------------------------------------------------------
if "initialized" not in st.session_state:
    # 1. Reset Config to Default
    write_json("data/config.json", {
        "active_gateway": "PG_CHEAP",
        "status": "running",
        "ai_disabled": True
    })
    # 2. Clear History
    write_json("data/logs.json", [])
    write_json("data/agent_thoughts.json", [])
    
    st.session_state.initialized = True
    st.session_state.ai_enabled = False 

# ---------------- Page Config & Custom CSS ----------------
st.set_page_config(
    page_title="Nexus Operations Console",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 🎨 PROFESSIONAL CSS STYLING
st.markdown("""
<style>
    /* Global Settings */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    .stApp {
        background-color: #0b0c10; /* Ultra Dark Background */
        color: #c5c6c7;
    }

    /* Metric Cards - Sleek & Minimal */
    [data-testid="stMetric"] {
        background-color: #1f2833;
        border-left: 4px solid #45a29e;
        padding: 15px 20px;
        border-radius: 4px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.2);
    }
    [data-testid="stMetricLabel"] {
        color: #66fcf1;
        font-size: 0.85rem;
        letter-spacing: 0.05em;
        text-transform: uppercase;
        font-weight: 600;
    }
    [data-testid="stMetricValue"] {
        color: #ffffff;
        font-weight: 700;
        font-size: 1.8rem;
    }

    /* Custom Alert Boxes (Replacing standard st.error/warning) */
    .status-box {
        padding: 16px;
        border-radius: 4px;
        margin-bottom: 20px;
        font-size: 0.95rem;
        border: 1px solid;
        display: flex;
        align-items: center;
    }
    .status-critical {
        background-color: #2c0b0e;
        border-color: #842029;
        color: #ea868f;
    }
    .status-warning {
        background-color: #2c220b;
        border-color: #997404;
        color: #ffda6a;
    }
    .status-healthy {
        background-color: #0f291e;
        border-color: #0f5132;
        color: #75b798;
    }
    .status-neutral {
        background-color: #1f2833;
        border-color: #45a29e;
        color: #66fcf1;
    }

    /* Financial Card Styling */
    .finance-card {
        background-color: #1f2833;
        padding: 20px;
        border-radius: 6px;
        border: 1px solid #2d3342;
        text-align: center;
    }
    .finance-label {
        color: #8892b0;
        font-size: 0.8rem;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 8px;
    }
    .finance-value {
        color: #fff;
        font-size: 1.6rem;
        font-weight: 700;
    }
    .finance-sub {
        font-size: 0.8rem;
        color: #45a29e;
        margin-top: 5px;
    }

    /* Headers */
    .main-title {
        font-size: 2rem;
        font-weight: 700;
        color: #ffffff;
        letter-spacing: -0.5px;
        margin-bottom: 0px;
    }
    .sub-title {
        font-size: 1rem;
        color: #8892b0;
        margin-bottom: 30px;
        font-weight: 400;
    }
    
    /* Clean Logs */
    .log-entry {
        border-left: 2px solid #444;
        padding-left: 15px;
        margin-bottom: 20px;
    }
    .log-time { color: #45a29e; font-size: 0.85rem; font-family: monospace; }
    .log-action { color: #fff; font-weight: 600; font-size: 1rem; margin: 4px 0; }
    .log-reason { color: #aaa; font-size: 0.9rem; line-height: 1.4; }

    /* Hide Streamlit Elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    [data-testid="stSidebarNav"] {display: none;}
</style>
""", unsafe_allow_html=True)

# ---------------- Start Threads ----------------
if "started" not in st.session_state:
    threading.Thread(target=run_simulation, daemon=True).start()
    threading.Thread(target=run_agent_brain, daemon=True).start()
    st.session_state.started = True

# ---------------- Sidebar ----------------
st.sidebar.markdown("### Control Panel")
st.sidebar.markdown("---")

# --- TOGGLE SWITCH LOGIC ---
if "ai_enabled" not in st.session_state:
    st.session_state.ai_enabled = False

# Plain text toggle
ai_mode = st.sidebar.toggle("Autonomous Agent", value=st.session_state.ai_enabled)

# Read config once
current_config = read_json("data/config.json")

if ai_mode != st.session_state.ai_enabled:
    st.session_state.ai_enabled = ai_mode
    
    if not ai_mode:
        # Deactivation Logic
        st.sidebar.markdown("<span style='color:#ff6b6b'>Deactivating...</span>", unsafe_allow_html=True)
        current_config["active_gateway"] = "PG_CHEAP"
        current_config["status"] = "running"
        current_config["ai_disabled"] = True  
        write_json("data/config.json", current_config)
        write_json("data/logs.json", [])
        write_json("data/agent_thoughts.json", [])
        time.sleep(0.5)
        st.rerun()
    else:
        # Activation Logic
        st.sidebar.markdown("<span style='color:#4CAF50'>System Active</span>", unsafe_allow_html=True)
        current_config["ai_disabled"] = False
        write_json("data/config.json", current_config)

st.sidebar.markdown("---")
auto_refresh = st.sidebar.checkbox("Real-time Data Feed", value=True)

st.sidebar.markdown("<br><br><br>", unsafe_allow_html=True)
st.sidebar.caption("Nexus Console v2.4.0")

# ---------------- Main Header ----------------
st.markdown('<div class="main-title">NEXUS OPERATIONS CONSOLE</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Autonomous Payment Orchestration & Recovery System</div>', unsafe_allow_html=True)

# ---------------- Read Data ----------------
config = read_json("data/config.json")
logs = read_json("data/logs.json")
thoughts = read_json("data/agent_thoughts.json")

# ---------------- TABS LAYOUT ----------------
tab1, tab2 = st.tabs(["Dashboard", "Decision Audit"])

# ==========================================
# TAB 1: DASHBOARD
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
    col1.metric("Success Velocity", f"{success_rate}%")
    col2.metric("Failure Rate", f"{failure_rate}%")
    col3.metric("Throughput", total_txns)
    
    # Clean up Gateway Name
    gw_name = config.get("active_gateway", "Unknown").replace("PG_", "")
    col4.metric("Active Route", gw_name)
    
    status_text = "ENGAGED" if ai_mode else "STANDBY"
    col5.metric("Agent State", status_text)

    # --- 2. Custom Status Banner (No Emojis) ---
    st.markdown("<br>", unsafe_allow_html=True)
    if failure_rate > 30:
        st.markdown(f"""
        <div class="status-box status-critical">
            <strong>CRITICAL ALERT &nbsp;|&nbsp;</strong> 
            High failure rate ({failure_rate}%) detected. Autonomous intervention active.
        </div>
        """, unsafe_allow_html=True)
    elif failure_rate > 15:
        st.markdown(f"""
        <div class="status-box status-warning">
            <strong>WARNING &nbsp;|&nbsp;</strong> 
            Elevated failure rate ({failure_rate}%). Monitoring system engaged.
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="status-box status-healthy">
            <strong>SYSTEM NORMAL &nbsp;|&nbsp;</strong> 
            Payment velocity optimal. No anomalies detected.
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # --- 3. Financial Impact Section ---
    st.markdown("### Financial Impact Analysis")
    
    if len(df) > 0 and "amount" in df.columns:
        fast_success = df[(df["gateway"] == "PG_FAST") & (df["status"] == "SUCCESS")]
        
        rescued_revenue = fast_success["amount"].sum()
        num_fast_txns = len(df[df["gateway"] == "PG_FAST"])
        
        optimization_cost = num_fast_txns * 0.40 
        net_value = rescued_revenue - optimization_cost
        
        # Custom HTML Cards for "Classy" look
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(f"""
            <div class="finance-card">
                <div class="finance-label">Revenue Protected</div>
                <div class="finance-value">${rescued_revenue:,.2f}</div>
                <div class="finance-sub">via Autonomous Routing</div>
            </div>
            """, unsafe_allow_html=True)
        with c2:
            st.markdown(f"""
            <div class="finance-card">
                <div class="finance-label">Optimization Cost</div>
                <div class="finance-value">${optimization_cost:,.2f}</div>
                <div class="finance-sub">Premium Route Fees</div>
            </div>
            """, unsafe_allow_html=True)
        with c3:
            st.markdown(f"""
            <div class="finance-card" style="border-color: #45a29e;">
                <div class="finance-label" style="color:#66fcf1;">Net Value Created</div>
                <div class="finance-value" style="color:#66fcf1;">${net_value:,.2f}</div>
                <div class="finance-sub">ROI Positive</div>
            </div>
            """, unsafe_allow_html=True)
            
    else:
        st.markdown("""<div class="status-box status-neutral">Awaiting transaction data for analysis...</div>""", unsafe_allow_html=True)

    st.markdown("---")

    # --- 4. Charts ---
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Transaction Distribution**")
        if len(df) > 0:
            st.bar_chart(df["status"].value_counts(), color="#45a29e")
        else:
            st.caption("No data available")

    with c2:
        st.markdown("**Real-time Throughput**")
        if len(df) > 0:
            df_time = df.copy()
            df_time["time"] = pd.to_datetime(df_time["timestamp"], format="%H:%M:%S", errors="coerce")
            df_time = df_time.dropna(subset=["time"])
            df_time["bucket"] = df_time["time"].dt.floor("5S")
            chart_data = df_time.pivot_table(index="bucket", columns="status", aggfunc="size", fill_value=0)
            st.line_chart(chart_data)
        else:
            st.caption("No data available")

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### Transaction Ledger")
    if len(df) > 0:
        st.dataframe(
            df.tail(10)[["timestamp", "gateway", "amount", "status", "error_code"]], 
            use_container_width=True,
            hide_index=True
        )
    else:
        st.caption("Ledger empty.")


# ==========================================
# TAB 2: AUDIT LOG (Detailed View Restored)
# ==========================================
with tab2:
    st.markdown("### Decision Logic Audit")
    
    # 1. VISUAL TIMELINE (Recent events)
    if len(thoughts) > 0:
        # Show only last 3 decisions visually
        recent_thoughts = thoughts[-3:]
        
        for log in reversed(recent_thoughts):
            decision = log.get('final_decision')
            timestamp = log.get('timestamp')
            reason = log.get('agent_reasoning')
            
            # Styling based on decision type
            border_color = "#444"
            if decision == "AUTO_RECOVERY":
                action_display = "SYSTEM AUTO RECOVERY"
                border_color = "#45a29e" # Teal
            elif decision == "INSTANT_RETREAT":
                action_display = "IMMEDIATE RETREAT PROTOCOL"
                border_color = "#ff6b6b" # Red
            elif decision == "SWITCH_TO_FAST":
                action_display = "ROUTING CHANGE: PREMIUM"
                border_color = "#feca57" # Yellow
            else:
                action_display = "MONITORING / WAIT"
            
            st.markdown(f"""
            <div class="log-entry" style="border-left-color: {border_color};">
                <div class="log-time">{timestamp}</div>
                <div class="log-action">{action_display}</div>
                <div class="log-reason">{reason}</div>
            </div>
            """, unsafe_allow_html=True)
            
    else:
        st.markdown("""<div class="status-box status-neutral">No autonomous decisions recorded yet.</div>""", unsafe_allow_html=True)

    st.markdown("---")
    
    # 2. DETAILED DATA TABLE (RESTORED!)
    st.markdown("### Detailed Error Report History")
    
    if len(thoughts) > 0:
        audit_df = pd.DataFrame(thoughts)
        
        # Select and Rename columns for better readability
        cols_to_show = ["timestamp", "gateway_before", "failure_rate", "final_decision", "agent_reasoning"]
        # Ensure columns exist before selecting
        existing_cols = [c for c in cols_to_show if c in audit_df.columns]
        audit_df = audit_df[existing_cols]
        
        # Rename for display
        audit_df.columns = [c.replace("_", " ").title() for c in audit_df.columns]
        
        st.dataframe(
            audit_df.sort_values(by="Timestamp", ascending=False), 
            use_container_width=True, 
            height=500
        )
    else:
        st.info("No detailed logs available.")


# ---------------- Auto Refresh ----------------
if auto_refresh:
    time.sleep(2)
    st.rerun()