import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from utils.llm_helper import call_llm
from utils.audit_logger import log

SYSTEM_PROMPT = """You are an enterprise procurement analyst AI agent.

You will receive vendor clusters found by ML analysis.
Each cluster contains vendors providing the same or overlapping services.

For each cluster:
1. Identify duplicate or overlapping vendors
2. Recommend which vendor(s) to keep and which to retire
3. Calculate realistic savings (10-15% negotiation leverage)
4. Create a prioritized action playbook

Use this format for each cluster:
---CLUSTER [N]---
Service: [service name]
Vendors Found: [list vendors]
Duplicate Risk: HIGH/MEDIUM/LOW
Recommended Action: [specific action]
Estimated Monthly Savings: $[amount]
Priority: HIGH/MEDIUM/LOW
Next Steps:
1. [step 1]
2. [step 2]
3. [step 3]
"""


def vendor_analysis() -> dict:
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    csv_path = os.path.join(base_dir, "data", "vendors.csv")
    df = pd.read_csv(csv_path)

    df['name_length'] = df['Vendor'].apply(len)
    df['service_encoded'] = pd.factorize(df['Service'])[0]

    features = df[['Monthly_Cost', 'name_length', 'service_encoded']].copy()
    scaler = StandardScaler()
    features_scaled = scaler.fit_transform(features)

    n_clusters = min(len(df) // 2, 8)
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    df['Cluster'] = kmeans.fit_predict(features_scaled)

    cluster_summary = []
    suspicious_clusters = []

    for cluster_id in df['Cluster'].unique():
        group = df[df['Cluster'] == cluster_id]
        if len(group) >= 2:
            services = group['Service'].value_counts()
            dominant_service = services.index[0]
            total_cost = group['Monthly_Cost'].sum()
            vendors_list = group['Vendor'].tolist()

            suspicious_clusters.append({
                "cluster_id": int(cluster_id),
                "service": dominant_service,
                "vendors": vendors_list,
                "total_monthly_cost": int(total_cost),
                "vendor_count": len(group)
            })
            cluster_summary.append(
                f"Cluster {cluster_id}: Service={dominant_service}, "
                f"Vendors={vendors_list}, Total Monthly Cost=${total_cost:,}"
            )

    llm_input = "Analyze these vendor clusters and generate a consolidation playbook:\n\n"
    llm_input += "\n".join(cluster_summary)

    llm_analysis = call_llm(
        system_prompt=SYSTEM_PROMPT,
        user_message=llm_input,
        max_tokens=2000
    )

    total_potential_savings = sum(c['total_monthly_cost'] * 0.12 for c in suspicious_clusters)

    log(
        agent="VendorAgent",
        action="duplicate_vendor_detection",
        input_summary=f"Analyzed {len(df)} vendors across {len(suspicious_clusters)} clusters",
        output_summary=f"Found {len(suspicious_clusters)} consolidation opportunities. "
                      f"Estimated savings: ${total_potential_savings:,.0f}/month",
        reasoning="KMeans clustering on cost + service features. "
                 "LLM generated prioritized consolidation playbook."
    )

    return {
        "raw_data": df,
        "clusters": suspicious_clusters,
        "llm_playbook": llm_analysis,
        "total_monthly_savings": total_potential_savings
    }