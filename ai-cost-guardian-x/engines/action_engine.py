import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import datetime
from utils.audit_logger import log

APPROVED_ACTIONS = {}

ACTION_MAP = {
    "Over Provisioning": {
        "action": "Reduce instance count by 30%",
        "system": "AWS Console / Terraform",
        "urgency": "HIGH",
        "auto_executable": True
    },
    "Traffic Spike": {
        "action": "Enable predictive auto-scaling with 2x buffer",
        "system": "AWS Auto Scaling Groups",
        "urgency": "MEDIUM",
        "auto_executable": True
    },
    "Misconfiguration": {
        "action": "Audit and fix resource configuration",
        "system": "AWS Config / CloudTrail",
        "urgency": "CRITICAL",
        "auto_executable": False
    },
    "Auto-scaling Runaway": {
        "action": "Set max instance cap + cooldown period",
        "system": "AWS Auto Scaling",
        "urgency": "CRITICAL",
        "auto_executable": False
    }
}


def generate_action(cause: str) -> dict:
    action_details = ACTION_MAP.get(cause, {
        "action": f"Investigate and remediate: {cause}",
        "system": "Manual Review",
        "urgency": "MEDIUM",
        "auto_executable": False
    })
    log(
        agent="ActionEngine",
        action="action_generated",
        input_summary=f"Cause: {cause}",
        output_summary=f"Action: {action_details['action']} via {action_details['system']}",
        reasoning=f"Mapped root cause '{cause}' to standard enterprise remediation playbook"
    )
    return action_details


def request_approval(action_id: str, action_details: dict, requested_by: str = "AI Agent") -> dict:
    approval_request = {
        "action_id": action_id,
        "action": action_details.get("action"),
        "system": action_details.get("system"),
        "urgency": action_details.get("urgency"),
        "requested_by": requested_by,
        "requested_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "status": "PENDING_APPROVAL"
    }
    APPROVED_ACTIONS[action_id] = approval_request
    log(
        agent="ActionEngine",
        action="approval_requested",
        input_summary=f"Action: {action_details.get('action')}",
        output_summary=f"Approval request {action_id} created. Status: PENDING",
        reasoning="Enterprise policy requires human approval before executing infrastructure changes"
    )
    return approval_request


def approve_and_execute(action_id: str, approved_by: str = "Admin") -> dict:
    if action_id not in APPROVED_ACTIONS:
        return {"status": "ERROR", "message": "Action ID not found"}

    action = APPROVED_ACTIONS[action_id]
    action['status'] = "APPROVED"
    action['approved_by'] = approved_by
    action['approved_at'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    action['executed_at'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    action['execution_status'] = "SUCCESS"

    log(
        agent="ActionEngine",
        action="action_executed",
        input_summary=f"Action ID: {action_id} | Action: {action['action']}",
        output_summary=f"Executed successfully by {approved_by} at {action['executed_at']}",
        reasoning=f"Human approval received from {approved_by}. Full audit trail recorded."
    )
    return action


def reject_action(action_id: str, reason: str, rejected_by: str = "Manager") -> dict:
    if action_id not in APPROVED_ACTIONS:
        return {"status": "ERROR", "message": "Action ID not found"}

    action = APPROVED_ACTIONS[action_id]
    action['status'] = "REJECTED"
    action['rejected_by'] = rejected_by
    action['rejection_reason'] = reason
    action['rejected_at'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    log(
        agent="ActionEngine",
        action="action_rejected",
        input_summary=f"Action ID: {action_id}",
        output_summary=f"Rejected by {rejected_by}. Reason: {reason}",
        reasoning="Human override applied. Action will not be executed."
    )
    return action