import datetime

_audit_log = []


def log(agent: str, action: str, input_summary: str, output_summary: str, reasoning: str = ""):
    entry = {
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "agent": agent,
        "action": action,
        "input": input_summary,
        "output": output_summary,
        "reasoning": reasoning
    }
    _audit_log.append(entry)
    return entry


def get_log():
    return list(_audit_log)


def clear_log():
    _audit_log.clear()
