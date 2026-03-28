import json, re, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.llm_helper import call_llm
from utils.audit_logger import log

SYSTEM_PROMPT = "Analyze user request. Respond ONLY with a JSON array of tasks: ['vendor_analysis', 'anomaly_detection', 'sla_prevention']"

def plan_tasks(user_input: str) -> list:
    response = call_llm(SYSTEM_PROMPT, f"User request: {user_input}", max_tokens=100)
    tasks = []
    try:
        match = re.search(r'\[.*?\]', response, re.DOTALL)
        if match: tasks = json.loads(match.group())
    except: pass
    
    if not tasks: # Fallback logic
        tasks = ["vendor_analysis", "anomaly_detection", "sla_prevention"]
        
    log("PlannerAgent", "task_planning", user_input, str(tasks), "Llama-3 routing")
    return tasks