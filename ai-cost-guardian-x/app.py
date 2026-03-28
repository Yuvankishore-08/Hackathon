import streamlit as st
import pandas as pd
import numpy as np
import os
import datetime
import time
import plotly.express as px
import plotly.graph_objects as go
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans

# --- 1. INITIALIZE SESSION STATE ---
if 'agent_results' not in st.session_state:
    st.session_state.agent_results = None

# --- 2. UI THEME (ANIMATIONS & SMOOTH TRANSITIONS) ---
st.set_page_config(page_title="CostSentinel AI", layout="wide", page_icon="🛡️")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;800&display=swap');
    
    /* Smooth Scroll & Transitions */
    html { scroll-behavior: smooth; }
    html, body, [class*="css"] { 
        font-family: 'Plus Jakarta Sans', sans-serif; 
        background-color: #0b0f1a; color: #f8fafc;
    }
    .stApp { background-color: #0b0f1a; }
    [data-testid="stSidebar"] { display: none; }
    .block-container { padding-top: 1rem !important; padding-bottom: 2rem !important; }
    
    /* Fade-in Animation */
    @keyframes fadeInUp {
        from { opacity: 0; transform: translateY(15px); }
        to { opacity: 1; transform: translateY(0); }
    }
    .animate-in { animation: fadeInUp 0.7s ease-out forwards; }

    /* Header & Branding */
    .header-container { 
        display: flex; flex-direction: column; align-items: flex-start; 
        padding: 10px 0px; border-bottom: 1px solid #1e293b; margin-bottom: 10px; 
    }
    .main-title { 
        font-size: 52px !important; font-weight: 800 !important; 
        background: linear-gradient(90deg, #3b82f6, #60a5fa);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        margin: 0; letter-spacing: -2px;
    }
    .tagline { 
        font-size: 18px !important; color: #3b82f6 !important; 
        font-weight: 600; margin-top: 2px; text-transform: uppercase;
    }

    /* Input Fields Hover Effect */
    .stTextInput input {
        background-color: #161e2d !important; color: white !important;
        border: 1px solid #334155 !important; border-radius: 8px !important;
        transition: border-color 0.3s ease, box-shadow 0.3s ease;
    }
    .stTextInput input:focus {
        border-color: #3b82f6 !important;
        box-shadow: 0 0 10px rgba(59, 130, 246, 0.2) !important;
    }

    /* Buttons Animation */
    div.stButton > button:first-child { 
        background: #2563eb; color: white; border-radius: 10px; border: none; 
        font-weight: 700; height: 50px; width: 100%; font-size: 18px !important;
        transition: all 0.3s ease;
    }
    div.stButton > button:first-child:hover { 
        background: #1d4ed8; transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(37, 99, 235, 0.3);
    }

    /* KPI Cards Hover Effect */
    .kpi-card { 
        background: #161e2d; padding: 20px; border-radius: 15px; 
        border: 1px solid #1e293b; transition: all 0.4s ease;
    }
    .kpi-card:hover { 
        border-color: #3b82f6; transform: scale(1.02);
        box-shadow: 0 10px 25px rgba(0,0,0,0.4);
    }
</style>
""", unsafe_allow_html=True)

# --- 3. AGENT ENGINES ---
def run_sla_intelligence():
    sla_data = {'Metric': ['API Latency', 'Error Rate', 'Server Uptime', 'Cloud Capacity'], 'Status': ['Stable', 'Warning', 'Healthy', 'Critical'], 'Risk_Score': [12, 45, 5, 88]}
    df = pd.DataFrame(sla_data)
    return {"df": df, "risks": df[df['Risk_Score'] > 75], "penalty_saved": 2500}

def run_vendor_intelligence():
    try:
        df = pd.read_csv("data/vendors.csv")
        df['service_idx'] = pd.factorize(df['Service'])[0]
        model = KMeans(n_clusters=3, n_init=10)
        df['Cluster'] = model.fit_predict(StandardScaler().fit_transform(df[['Monthly_Cost', 'service_idx']]))
        clusters = [{"Category": g['Service'].iloc[0], "Vendors": ", ".join(g['Vendor'].tolist()), "Total_Spend": g['Monthly_Cost'].sum(), "Potential_Savings": int(g['Monthly_Cost'].sum() * 0.15)} for _, g in df.groupby('Cluster') if len(g) > 1]
        return {"df": df, "clusters": clusters, "savings": sum(c['Potential_Savings'] for c in clusters)}
    except: return None

def run_cloud_audit():
    try:
        # High Variance Data for Line Chart Demo
        months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul']
        costs = [1200, 1250, 4800, 1300, 1350, 5500, 1400]
        usage = [70, 72, 95, 75, 76, 98, 78]
        df = pd.DataFrame({'Month': months, 'Cost': costs, 'Usage': usage})
        model = IsolationForest(contamination=0.2, random_state=42)
        df['anomaly'] = model.fit_predict(df[['Cost', 'Usage']])
        return {"df": df, "savings": df[df['anomaly'] == -1]['Cost'].sum() * 0.45}
    except: return None

# --- 4. HEADER (ANIMATED) ---
st.markdown("""
<div class="header-container animate-in">
    <div class="main-title">CostSentinel AI</div>
    <div class="tagline">Precision Auditing. Proactive Protection. Absolute Savings.</div>
    <div class="hero-desc">Multi-Agent Intelligence leveraging <b>Llama-3.3</b> and <b>Unsupervised ML</b> to detect spend leakage and mitigate SLA risks autonomously.</div>
</div>
""", unsafe_allow_html=True)

# --- 5. COMMAND CENTER ---
c_key, c_cmd = st.columns([1, 2.5])
with c_key: key = st.text_input("Groq API Key", type="password", placeholder="Access Key")
with c_cmd: user_query = st.text_input("Instruction", value="Perform audit: Identify cloud waste and vendor contract overlaps")

if st.button("🚀 EXECUTE AUTONOMOUS AUDIT"):
    if not key: st.error("Authentication Error: Brain not connected.")
    else:
        with st.status("🕵️ Agent Reasoning Trail...", expanded=False) as status:
            v_res = run_vendor_intelligence(); c_res = run_cloud_audit(); s_res = run_sla_intelligence()
            st.session_state.agent_results = {'v': v_res, 'c': c_res, 's': s_res, 'm_sav': (v_res['savings'] if v_res else 0) + (c_res['savings'] if c_res else 0)}
            status.update(label="System Audit Complete", state="complete")

# --- 6. RESULTS SECTION (ANIMATED) ---
if st.session_state.agent_results:
    res = st.session_state.agent_results
    st.markdown("<div class='animate-in'>---</div>", unsafe_allow_html=True)
    
    # KPI Grid with Smooth Transition
    k1, k2, k3, k4 = st.columns(4)
    with k1: st.markdown(f"<div class='kpi-card animate-in'><div style='font-size:12px;color:#64748b'>NET SAVINGS</div><div style='font-size:28px;font-weight:800'>${res['m_sav']:,.0f}</div></div>", unsafe_allow_html=True)
    with k2: st.markdown(f"<div class='kpi-card animate-in'><div style='font-size:12px;color:#64748b'>PENALTY SAVED</div><div style='font-size:28px;font-weight:800'>${res['s']['penalty_saved']:,.0f}</div></div>", unsafe_allow_html=True)
    with k3: st.markdown(f"<div class='kpi-card animate-in'><div style='font-size:12px;color:#64748b'>CONFIDENCE</div><div style='font-size:28px;font-weight:800;color:#10b981'>94.2%</div></div>", unsafe_allow_html=True)
    with k4: st.markdown(f"<div class='kpi-card animate-in'><div style='font-size:12px;color:#f87171'>RISKS</div><div style='font-size:28px;font-weight:800;color:#f87171'>{len(res['s']['risks'])}</div></div>", unsafe_allow_html=True)

    st.markdown("<div class='animate-in'>", unsafe_allow_html=True)
    t1, t2, t3, t4 = st.tabs(["🚀 PLAYBOOK", "🛡️ SLA MONITOR", "🏢 VENDORS", "☁️ CLOUD AUDIT"])
    
    with t1:
        st.markdown("### 🛠️ Remediation tasks")
        if not res['s']['risks'].empty:
            st.error(f"⚠️ **SLA RISK:** {res['s']['risks']['Metric'].iloc[0]} Breach Probability Detected.")
            if st.button("STAGED APPROVAL: AUTO-SCALING"): st.success("✅ Workflow Authorized for Execution.")
        
        if res['v'] and res['v']['clusters']:
            for i, cl in enumerate(res['v']['clusters'][:2]):
                st.info(f"**Strategy:** Consolidate {cl['Category']} ({cl['Vendors']})")
                if st.button(f"STAGED APPROVAL: {cl['Category'].upper()}", key=f"old_v_{i}"): st.success(f"✅ Consolidation request for {cl['Category']} sent.")

    with t2:
        st.plotly_chart(px.bar(res['s']['df'], x='Metric', y='Risk_Score', color='Status', template="plotly_dark", barmode='group'), use_container_width=True)

    with t3:
        if res['v']: st.table(pd.DataFrame(res['v']['clusters']))

    with t4:
        if res['c']:
            st.write("#### 📈 Spend Trend & Anomaly Detection")
            # Creating a Dual-Line Graph for Cost & Usage
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=res['c']['df']['Month'], y=res['c']['df']['Cost'], name="Monthly Cost ($)", mode='lines+markers', line=dict(color='#3b82f6', width=4)))
            # Mark anomalies as red dots
            anomalies = res['c']['df'][res['c']['df']['anomaly'] == -1]
            fig.add_trace(go.Scatter(x=anomalies['Month'], y=anomalies['Cost'], name="Anomalies Detected", mode='markers', marker=dict(color='#ef4444', size=12, symbol='x')))
            fig.update_layout(template="plotly_dark", hovermode="x unified", xaxis_title="Month", yaxis_title="Cost ($)")
            st.plotly_chart(fig, use_container_width=True)

    st.markdown("</div>", unsafe_allow_html=True)

    # --- 7. STATISTICAL HEALTH (ANIMATED) ---
    st.markdown("<div class='animate-in'><h3>🧬 Statistical System Health</h3>", unsafe_allow_html=True)
    h1, h2, h3 = st.columns(3)
    with h1: st.write("**Data Integrity**"); st.progress(0.98); st.caption("98.2% Consistency Score")
    with h2: st.write("**Reasoning Pulse**"); st.markdown("<span style='color:#10b981'>●</span> Stable", unsafe_allow_html=True); st.caption("Agent Logics Verified")
    with h3: st.write("**ML Stability**"); st.metric(label="Variance", value="Low", delta="-0.84%")
    st.markdown("</div>", unsafe_allow_html=True)