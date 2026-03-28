import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.llm_helper import call_llm
from utils.audit_logger import log
import json
import re

SYSTEM_PROMPT = """You are an enterprise cost intelligence planner.
Analyze the user's request and decide which analysis tasks to run.

Available tasks:
- vendor_analysis: Detect duplicate/overlapping vendors, consolidation savings
- anomaly_detection: Detect cloud cost spikes, diagnose root cause, recommend fix
- sla_prevention: Detect SLA breach risk, calculate penalties, build recovery plan

Respond ONLY with a JSON array. Example: ["vendor_analysis", "anomaly_detection"]
No explanation. Only the JSON array."""


def plan_tasks(user_input: str) -> list:
    response = call_llm(
        system_prompt=SYSTEM_PROMPT,
        user_message=f"User request: {user_input}",
        max_tokens=100
    )

    tasks = []
    try:
        match = re.search(r'\[.*?\]', response, re.DOTALL)
        if match:
            tasks = json.loads(match.group())
    except Exception:
        pass

    # Fallback keyword matching
    if not tasks:
        user_lower = user_input.lower()
        if any(w in user_lower for w in ["vendor", "duplicate", "consolidat", "supplier"]):
            tasks.append("vendor_analysis")
        if any(w in user_lower for w in ["cost", "spike", "anomaly", "cloud", "spend", "infrastructure"]):
            tasks.append("anomaly_detection")
        if any(w in user_lower for w in ["sla", "breach", "deadline", "penalty", "task", "delivery"]):
            tasks.append("sla_prevention")
        if not tasks:
            tasks = ["vendor_analysis", "anomaly_detection", "sla_prevention"]

    log(
        agent="PlannerAgent",
        action="task_planning",
        input_summary=f"User query: '{user_input}'",
        output_summary=f"Tasks selected: {tasks}",
        reasoning="LLM analyzed the query and identified relevant cost intelligence modules"
    )
    return tasks