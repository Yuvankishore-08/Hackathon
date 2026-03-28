import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from orchestrator import run_system
from engines.impact_engine import financial_model
from engines.action_engine import generate_action, request_approval, approve_and_execute
from utils.audit_logger import get_log, clear_log

st.set_page_config(
    page_title="AI Cost Guardian",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .stApp { background: #0a0e1a; }
    .hero { text-align: center; padding: 30px 0 10px 0; }
    .hero h1 {
        font-size: 2.8rem; font-weight: 800;
        background: linear-gradient(90deg, #60a5fa, #34d399);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    }
    .hero p { color: #94a3b8; font-size: 1.1rem; }
    .section-header {
        font-size: 1.2rem; font-weight: 700; color: #e2e8f0;
        padding: 10px 0 8px 0;
        border-bottom: 2px solid #1e3a5f;
        margin-bottom: 14px;
    }
    .llm-box {
        background: #0f1f35;
        border: 1px solid #1e3a5f;
        border-radius: 10px;
        padding: 16px;
        font-size: 0.87rem;
        color: #cbd5e1;
        line-height: 1.8;
        white-space: pre-wrap;
        font-family: monospace;
    }
    .audit-entry {
        background: #111827;
        border-left: 3px solid #3b82f6;
        padding: 10px 14px;
        margin: 6px 0;
        border-radius: 0 8px 8px 0;
        font-size: 0.82rem;
        font-family: monospace;
        color: #94a3b8;
    }
    div[data-testid="stMetric"] {
        background: #111827;
        border-radius: 10px;
        padding: 12px;
        border: 1px solid #1e3a5f;
    }
    .stButton>button {
        background: linear-gradient(135deg, #1d4ed8, #1e40af);
        color: white; border: none;
        border-radius: 8px; font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# ─── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🛡️ AI Cost Guardian")
    st.markdown("---")

    api_key = st.text_input(
        "🔑 Anthropic API Key",
        type="password",
        placeholder="sk-ant-...",
        help="Required for AI agent reasoning"
    )
    if api_key:
        st.session_state["anthropic_api_key"] = api_key
        st.success("✅ API key set")
    else:
        st.warning("⚠️ Enter API key to enable AI reasoning")

    st.markdown("---")
    st.markdown("### 📋 Quick Launch")

    if st.button("🏢 Vendor Analysis", use_container_width=True):
        st.session_state["quick_query"] = "analyze vendor duplicates and consolidation opportunities"
    if st.button("☁️ Cloud Anomalies", use_container_width=True):
        st.session_state["quick_query"] = "detect cloud cost anomalies and diagnose root cause"
    if st.button("⏰ SLA Prevention", use_container_width=True):
        st.session_state["quick_query"] = "check SLA breach risks and prevention plan"
    if st.button("🔍 Full Analysis", use_container_width=True):
        st.session_state["quick_query"] = "run full enterprise cost intelligence analysis on vendors cloud costs and sla risks"

    st.markdown("---")
    st.markdown("### 🏗️ Architecture")
    st.markdown("""
```
User Query
    ↓
PlannerAgent (LLM)
    ↓
┌──────────────────┐
│ VendorAgent      │
│ KMeans + Claude  │
├──────────────────┤
│ AnomalyAgent     │
│ IsoForest+Claude │
├──────────────────┤
│ SLAAgent         │
│ Velocity+Claude  │
└──────────────────┘
    ↓
ImpactEngine
    ↓
ActionEngine
    ↓
AuditLogger
```
""")
    st.markdown("---")
    if st.button("🗑️ Clear Audit Log", use_container_width=True):
        clear_log()
        st.success("Log cleared")

# ─── Hero ─────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero">
    <h1>🛡️ AI Cost Guardian</h1>
    <p>Multi-Agent Enterprise Cost Intelligence · Detect · Diagnose · Recommend · Execute</p>
</div>
""", unsafe_allow_html=True)

# ─── Input ────────────────────────────────────────────────────────────────────
default_query = st.session_state.pop("quick_query", "")
user_input = st.text_input(
    "💬 What would you like to analyze?",
    value=default_query,
    placeholder="e.g. 'Analyze vendor duplicates, detect cost spikes, and check SLA risks'"
)
run_clicked = st.button("🚀 Run AI Analysis", type="primary", use_container_width=True)

# ─── Run ──────────────────────────────────────────────────────────────────────
if run_clicked and user_input:
    clear_log()
    with st.spinner("🤖 AI agents analyzing enterprise data..."):
        progress = st.progress(0, text="Starting agents...")
        try:
            progress.progress(10, text="PlannerAgent: Selecting modules...")
            results = run_system(user_input)
            progress.progress(60, text="Computing financial impact...")
            impact = financial_model(
                vendor_result=results.get("vendor"),
                anomaly_result=results.get("anomaly"),
                sla_result=results.get("sla")
            )
            progress.progress(100, text="Done!")
            st.session_state["results"] = results
            st.session_state["impact"] = impact
        except Exception as e:
            st.error(f"System error: {e}")
            progress.empty()

# ─── Results ──────────────────────────────────────────────────────────────────
if "results" in st.session_state:
    results = st.session_state["results"]
    impact = st.session_state["impact"]

    if results.get("errors"):
        with st.expander("⚠️ Warnings", expanded=False):
            for err in results["errors"]:
                st.warning(err)

    # KPI Row
    st.markdown("---")
    st.markdown('<div class="section-header">💰 Financial Impact Summary</div>', unsafe_allow_html=True)
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.metric("Monthly Savings", f"${impact['total_savings']:,}")
    with k2:
        st.metric("Annual Projection", f"${impact['annual_projection']:,}")
    with k3:
        st.metric("Before Optimization", f"${impact['before_optimization']:,}")
    with k4:
        st.metric("ROI", f"{impact['roi_percentage']}%")

    # Before/After Chart
    if impact['breakdown']:
        categories = [b['category'] for b in impact['breakdown']]
        before_vals = [b['current_monthly'] for b in impact['breakdown']]
        after_vals  = [b['optimized_monthly'] for b in impact['breakdown']]

        fig = go.Figure()
        fig.add_trace(go.Bar(
            name='Before', x=categories, y=before_vals,
            marker_color="#ef4444",
            text=[f"${v:,}" for v in before_vals], textposition='outside'
        ))
        fig.add_trace(go.Bar(
            name='After', x=categories, y=after_vals,
            marker_color='#10b981',
            text=[f"${v:,}" for v in after_vals], textposition='outside'
        ))
        fig.update_layout(
            barmode='group',
            plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
            font_color='#94a3b8', height=300,
            margin=dict(t=30, b=10, l=10, r=10)
        )
        st.plotly_chart(fig, use_container_width=True)

        with st.expander("📊 Show the Math — Financial Model Assumptions"):
            for b in impact['breakdown']:
                st.markdown(f"""
**{b['category']}**
- Current monthly: `${b['current_monthly']:,}` → Optimized: `${b['optimized_monthly']:,}`
- Monthly savings: `${b['monthly_savings']:,}` | Annual: `${b['annual_savings']:,}`
- Assumption: _{b['assumption']}_
- Confidence: `{b['confidence']}`
---
""")

    st.markdown("---")

    tab1, tab2, tab3, tab4 = st.tabs([
        "🏢 Vendor Intelligence",
        "☁️ Cloud Anomalies",
        "⏰ SLA Prevention",
        "📋 Audit Trail"
    ])

    # ── TAB 1: VENDOR ─────────────────────────────────────────────────────────
    with tab1:
        vendor = results.get("vendor")
        if not vendor:
            st.info("Vendor analysis not run. Click '🏢 Vendor Analysis' or '🔍 Full Analysis'.")
        else:
            st.markdown('<div class="section-header">🏢 Vendor Duplication Intelligence</div>', unsafe_allow_html=True)
            v1, v2, v3 = st.columns(3)
            with v1:
                st.metric("Vendors Analyzed", len(vendor['raw_data']))
            with v2:
                st.metric("Duplicate Clusters Found", len(vendor['clusters']))
            with v3:
                st.metric("Est. Monthly Savings", f"${vendor['total_monthly_savings']:,.0f}")

            if vendor['clusters']:
                st.markdown("#### 🔍 Identified Duplicate Clusters")
                rows = []
                for c in vendor['clusters']:
                    rows.append({
                        "Service": c['service'],
                        "# Vendors": c['vendor_count'],
                        "Vendors": ", ".join(c['vendors']),
                        "Total Monthly Cost": f"${c['total_monthly_cost']:,}",
                        "Est. Savings (12%)": f"${int(c['total_monthly_cost'] * 0.12):,}"
                    })
                st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

            df_v = vendor['raw_data']
            if not df_v.empty:
                fig_v = px.treemap(
                    df_v, path=['Service', 'Vendor'], values='Monthly_Cost',
                    title="Vendor Spend by Service Category",
                    color='Monthly_Cost', color_continuous_scale='Blues'
                )
                fig_v.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)', font_color='#94a3b8', height=350
                )
                st.plotly_chart(fig_v, use_container_width=True)

            st.markdown("#### 🤖 AI-Generated Consolidation Playbook")
            st.markdown(f'<div class="llm-box">{vendor["llm_playbook"]}</div>', unsafe_allow_html=True)

    # ── TAB 2: ANOMALY ────────────────────────────────────────────────────────
    with tab2:
        anomaly = results.get("anomaly")
        if not anomaly:
            st.info("Anomaly detection not run. Click '☁️ Cloud Anomalies' or '🔍 Full Analysis'.")
        else:
            st.markdown('<div class="section-header">☁️ Cloud Cost Anomaly Detection</div>', unsafe_allow_html=True)
            a1, a2, a3 = st.columns(3)
            with a1:
                st.metric("Months Analyzed", len(anomaly['raw_data']))
            with a2:
                st.metric("Anomalies Detected", len(anomaly['anomalies']))
            with a3:
                st.metric("Potential Savings", f"${anomaly['estimated_savings']:,.0f}")

            df_a = anomaly['raw_data'].copy()
            fig_a = go.Figure()
            fig_a.add_trace(go.Scatter(
                x=df_a['Month'], y=df_a['Cost'],
                mode='lines+markers', name='Monthly Cost',
                line=dict(color='#60a5fa', width=2),
                marker=dict(
                    color=df_a['anomaly_score'].map({1: '#60a5fa', -1: '#ef4444'}),
                    size=df_a['anomaly_score'].map({1: 8, -1: 14}),
                    symbol=df_a['anomaly_score'].map({1: 'circle', -1: 'star'})
                )
            ))
            fig_a.add_hline(
                y=anomaly['baseline_avg_cost'], line_dash='dash', line_color='#34d399',
                annotation_text=f"Baseline: ${anomaly['baseline_avg_cost']:,.0f}"
            )
            fig_a.update_layout(
                title="Cloud Cost Timeline — ⭐ Red Stars = Anomalies",
                plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                font_color='#94a3b8', height=320, margin=dict(t=40, b=10)
            )
            st.plotly_chart(fig_a, use_container_width=True)

            if len(anomaly['anomalies']) > 0:
                st.markdown("#### 🚨 Detected Anomalies")
                anom_df = anomaly['anomalies'][['Month', 'Cost', 'Usage', 'Instances']].copy()
                anom_df['Cost'] = anom_df['Cost'].apply(lambda x: f"${x:,}")
                anom_df['vs Baseline'] = anomaly['anomalies']['Cost'].apply(
                    lambda x: f"+{((x - anomaly['baseline_avg_cost']) / anomaly['baseline_avg_cost'] * 100):.1f}%"
                )
                st.dataframe(anom_df, use_container_width=True, hide_index=True)

                st.markdown("#### ⚡ Corrective Actions")
                for _, row in anomaly['anomalies'].iterrows():
                    with st.expander(f"📍 {row['Month']} — Cost: ${row['Cost']:,}"):
                        if row['Instances'] > 10:
                            cause = "Over Provisioning"
                        elif row['Usage'] > 90:
                            cause = "Traffic Spike"
                        else:
                            cause = "Misconfiguration"

                        action_details = generate_action(cause)
                        st.info(f"**Root Cause:** {cause}")
                        st.success(f"**Recommended Action:** {action_details['action']}")
                        st.markdown(f"**System:** `{action_details['system']}` | **Urgency:** `{action_details['urgency']}`")

                        c1, c2 = st.columns(2)
                        action_id = f"action_{row['Month']}"
                        with c1:
                            if st.button("📋 Request Approval", key=f"req_{row['Month']}"):
                                request_approval(action_id, action_details)
                                st.warning(f"⏳ Approval pending | ID: `{action_id}`")
                        with c2:
                            if st.button("✅ Approve & Execute", key=f"exe_{row['Month']}"):
                                request_approval(action_id, action_details)
                                res = approve_and_execute(action_id)
                                st.success(f"✅ Executed at {res['executed_at']}")

            st.markdown("#### 🤖 AI Root Cause Diagnosis & Remediation")
            st.markdown(f'<div class="llm-box">{anomaly["llm_diagnosis"]}</div>', unsafe_allow_html=True)

    # ── TAB 3: SLA ────────────────────────────────────────────────────────────
    with tab3:
        sla = results.get("sla")
        if not sla:
            st.info("SLA analysis not run. Click '⏰ SLA Prevention' or '🔍 Full Analysis'.")
        else:
            st.markdown('<div class="section-header">⏰ SLA Breach Prevention</div>', unsafe_allow_html=True)
            s1, s2, s3, s4 = st.columns(4)
            with s1:
                st.metric("Tasks Monitored", len(sla['all_tasks']))
            with s2:
                st.metric("At Breach Risk", sla['breach_count'],
                          delta="🚨 Act Now" if sla['breach_count'] > 0 else "✅ Safe")
            with s3:
                st.metric("Penalty Exposure", f"${sla['total_penalty_at_risk']:,.0f}")
            with s4:
                st.metric("On Track", len(sla['all_tasks']) - sla['breach_count'])

            df_sla = sla['all_tasks'].copy()
            colors = ['#ef4444' if b else '#10b981' for b in df_sla['Will_Breach']]
            fig_sla = go.Figure()
            fig_sla.add_trace(go.Bar(
                x=df_sla['Task_Name'], y=df_sla['Completion_Pct'],
                marker_color=colors,
                text=[f"{p:.0f}%" for p in df_sla['Completion_Pct']],
                textposition='outside'
            ))
            fig_sla.add_hline(y=80, line_dash='dash', line_color='#f59e0b',
                              annotation_text="80% threshold")
            fig_sla.update_layout(
                title="Task Completion % — Red = SLA Breach Risk",
                yaxis_title="% Complete", yaxis_range=[0, 130],
                plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                font_color='#94a3b8', height=350,
                xaxis_tickangle=-30, margin=dict(t=50, b=60)
            )
            st.plotly_chart(fig_sla, use_container_width=True)

            if len(sla['at_risk_tasks']) > 0:
                st.markdown("#### 🚨 Tasks Requiring Immediate Action")
                at_risk_df = sla['at_risk_tasks'][[
                    'Task_Name', 'Assignee', 'Team', 'Priority',
                    'Completion_Pct', 'Days_Remaining', 'Penalty_At_Risk'
                ]].copy()
                at_risk_df.columns = ['Task', 'Assignee', 'Team', 'Priority', '% Done', 'Days Left', 'Penalty ($)']
                at_risk_df['% Done'] = at_risk_df['% Done'].apply(lambda x: f"{x:.1f}%")
                at_risk_df['Penalty ($)'] = at_risk_df['Penalty ($)'].apply(lambda x: f"${x:,.0f}")
                st.dataframe(at_risk_df, use_container_width=True, hide_index=True)

            with st.expander("📊 All Tasks Overview"):
                all_df = sla['all_tasks'][[
                    'Task_Name', 'Assignee', 'Team', 'Completion_Pct', 'Days_Remaining', 'Will_Breach'
                ]].copy()
                all_df['Will_Breach'] = all_df['Will_Breach'].map({True: '🚨 At Risk', False: '✅ On Track'})
                all_df['Completion_Pct'] = all_df['Completion_Pct'].apply(lambda x: f"{x:.1f}%")
                st.dataframe(all_df, use_container_width=True, hide_index=True)

            st.markdown("#### 🤖 AI Recovery Plan & Escalation")
            st.markdown(f'<div class="llm-box">{sla["llm_recovery_plan"]}</div>', unsafe_allow_html=True)

    # ── TAB 4: AUDIT TRAIL ────────────────────────────────────────────────────
    with tab4:
        st.markdown('<div class="section-header">📋 Agent Decision Audit Trail</div>', unsafe_allow_html=True)
        st.caption("Every decision made by every agent is logged here for enterprise compliance.")
        audit_entries = get_log()
        if not audit_entries:
            st.info("No decisions logged yet. Run an analysis first.")
        else:
            st.metric("Total Decisions Logged", len(audit_entries))
            for entry in audit_entries:
                st.markdown(f"""
<div class="audit-entry">
  <span style="color:#64748b">[{entry['timestamp']}]</span>
  <span style="color:#60a5fa; font-weight:700;"> {entry['agent']}</span>
  <span style="color:#64748b"> → </span>
  <span style="color:#34d399">{entry['action']}</span><br>
  <span style="color:#64748b">Input:</span> {entry['input']}<br>
  <span style="color:#64748b">Output:</span> {entry['output']}<br>
  <span style="color:#64748b">Reasoning:</span> <em>{entry['reasoning']}</em>
</div>
""", unsafe_allow_html=True)

            st.download_button(
                "📥 Export Audit Log (CSV)",
                data=pd.DataFrame(audit_entries).to_csv(index=False),
                file_name="audit_trail.csv",
                mime="text/csv"
            )

st.markdown("---")
st.markdown(
    '<p style="text-align:center; color:#475569; font-size:0.8rem;">'
    '🛡️ AI Cost Guardian · Multi-Agent Enterprise Cost Intelligence · '
    'Detect · Diagnose · Recommend · Execute · Audit'
    '</p>',
    unsafe_allow_html=True
)