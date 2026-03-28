import os, sys
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.llm_helper import call_llm
from utils.audit_logger import log

def vendor_analysis() -> dict:
    df = pd.read_csv(os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "vendors.csv"))
    df['service_encoded'] = pd.factorize(df['Service'])[0]
    
    features = df[['Monthly_Cost', 'service_encoded']]
    scaler = StandardScaler()
    df['Cluster'] = KMeans(n_clusters=min(len(df)//2, 5), n_init=10).fit_predict(scaler.fit_transform(features))

    suspicious = []
    for cid in df['Cluster'].unique():
        group = df[df['Cluster'] == cid]
        if len(group) >= 2:
            suspicious.append({"service": group['Service'].iloc[0], "vendors": group['Vendor'].tolist(), "cost": int(group['Monthly_Cost'].sum())})

    llm_playbook = call_llm("Analyze vendor clusters and create a consolidation playbook.", str(suspicious))
    log("VendorAgent", "analysis", "CSV Data", "Clusters found", "KMeans + Llama-3")
    
    return {"clusters": suspicious, "llm_playbook": llm_playbook, "total_monthly_savings": sum(c['cost'] * 0.12 for c in suspicious)}