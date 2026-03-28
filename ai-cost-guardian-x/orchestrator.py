import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agents.planner_agent import plan_tasks
from agents.vendor_agent import vendor_analysis
from agents.anomaly_agent import anomaly_detection
from agents.sla_agent import sla_prevention
from utils.audit_logger import log


def run_system(user_input: str) -> dict:
    results = {
        "tasks_planned": [],
        "vendor": None,
        "anomaly": None,
        "sla": None,
        "errors": []
    }

    # Step 1: Plan
    try:
        tasks = plan_tasks(user_input)
        results["tasks_planned"] = tasks
        log(
            agent="Orchestrator",
            action="pipeline_started",
            input_summary=f"User query: '{user_input}'",
            output_summary=f"Planned tasks: {tasks}",
            reasoning="Delegated to PlannerAgent for task selection"
        )
    except Exception as e:
        tasks = ["vendor_analysis", "anomaly_detection", "sla_prevention"]
        results["errors"].append(f"PlannerAgent error (running all): {str(e)}")

    # Step 2: Execute agents
    if "vendor_analysis" in tasks:
        try:
            results["vendor"] = vendor_analysis()
            log(
                agent="Orchestrator",
                action="vendor_analysis_complete",
                input_summary="vendors.csv",
                output_summary=f"{len(results['vendor']['clusters'])} clusters found",
                reasoning="VendorAgent completed successfully"
            )
        except Exception as e:
            results["errors"].append(f"VendorAgent error: {str(e)}")
            log(
                agent="Orchestrator",
                action="vendor_analysis_failed",
                input_summary="vendors.csv",
                output_summary=f"Error: {str(e)}",
                reasoning="Graceful degradation — other agents continue"
            )

    if "anomaly_detection" in tasks:
        try:
            results["anomaly"] = anomaly_detection()
            log(
                agent="Orchestrator",
                action="anomaly_detection_complete",
                input_summary="cloud_cost.csv",
                output_summary=f"{len(results['anomaly']['anomalies'])} anomalies found",
                reasoning="AnomalyAgent completed successfully"
            )
        except Exception as e:
            results["errors"].append(f"AnomalyAgent error: {str(e)}")
            log(
                agent="Orchestrator",
                action="anomaly_detection_failed",
                input_summary="cloud_cost.csv",
                output_summary=f"Error: {str(e)}",
                reasoning="Graceful degradation — other agents continue"
            )

    if "sla_prevention" in tasks:
        try:
            results["sla"] = sla_prevention()
            log(
                agent="Orchestrator",
                action="sla_prevention_complete",
                input_summary="sla_tasks.csv",
                output_summary=f"{results['sla']['breach_count']} tasks at risk",
                reasoning="SLAAgent completed successfully"
            )
        except Exception as e:
            results["errors"].append(f"SLAAgent error: {str(e)}")
            log(
                agent="Orchestrator",
                action="sla_prevention_failed",
                input_summary="sla_tasks.csv",
                output_summary=f"Error: {str(e)}",
                reasoning="Graceful degradation — other agents continue"
            )

    log(
        agent="Orchestrator",
        action="pipeline_complete",
        input_summary=f"Tasks: {tasks}",
        output_summary=f"Completed. Errors: {len(results['errors'])}",
        reasoning="All agents executed. Results ready for financial impact modeling."
    )

    return results