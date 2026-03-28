import sys
import os
from typing import Optional
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agents.planner_agent import plan_tasks
from agents.vendor_agent import vendor_analysis
from agents.anomaly_agent import anomaly_detection
from agents.sla_agent import sla_prevention
from utils.audit_logger import log

def run_system(user_input: Optional[str]) -> dict:
    if not user_input or not str(user_input).strip():
        raise ValueError("user_input must be a non-empty string")
    user_input = str(user_input).strip()
    results = {"tasks_planned": [], "vendor": None, "anomaly": None, "sla": None, "errors": []}

    # Step 1: Planning
    try:
        tasks = plan_tasks(user_input)
        results["tasks_planned"] = tasks
    except Exception as e:
        tasks = ["vendor_analysis", "anomaly_detection", "sla_prevention"]
        results["errors"].append(f"Planner Error: {e}")

    # Step 2: Execute Agents
    if "vendor_analysis" in tasks:
        try: results["vendor"] = vendor_analysis()
        except Exception as e: results["errors"].append(f"Vendor Error: {e}")

    if "anomaly_detection" in tasks:
        try: results["anomaly"] = anomaly_detection()
        except Exception as e: results["errors"].append(f"Anomaly Error: {e}")

    if "sla_prevention" in tasks:
        try: results["sla"] = sla_prevention()
        except Exception as e: results["errors"].append(f"SLA Error: {e}")

    return results