import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from datetime import datetime, date
from utils.llm_helper import call_llm
from utils.audit_logger import log

SYSTEM_PROMPT = """You are an enterprise SLA breach prevention agent.

You will receive tasks that are at risk of breaching their SLA deadlines.
For each at-risk task:

1. DETECT: Calculate completion % and hours remaining
2. PROJECT: Will this task breach the SLA at current velocity?
3. DIAGNOSE: Why is it falling behind?
4. QUANTIFY: Financial penalty if breach occurs
5. RECOVER: Specific recovery plan with reprioritization

Format each task as:
---SLA RISK: [Task Name]---
Assignee: [name]
Current Progress: [X]% complete
Hours Remaining to Deadline: [N] hours
Projected Completion: [ON TIME / BREACH BY N hours]
Financial Penalty at Risk: $[amount]
Breach Probability: CRITICAL/HIGH/MEDIUM
Root Cause: [specific reason]
Recovery Plan:
1. IMMEDIATE (next 4 hours): [specific action]
2. RESOURCE: [who to pull in]
3. REPRIORITIZE: [what to pause]
4. ESCALATION: [who and when to escalate]

End with a SUMMARY:
- Total penalties at risk: $[amount]
- Tasks that WILL breach without intervention: [list]
- Recommended emergency resource allocation: [plan]
"""


def sla_prevention() -> dict:
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    csv_path = os.path.join(base_dir, "data", "sla_tasks.csv")
    df = pd.read_csv(csv_path)

    today = date.today()
    df['Deadline'] = pd.to_datetime(df['Deadline']).dt.date
    df['Days_Remaining'] = df['Deadline'].apply(lambda d: (d - today).days)
    df['Completion_Pct'] = (df['Completed_Hours'] / df['Planned_Hours'] * 100).round(1)
    df['Hours_Remaining_Work'] = df['Planned_Hours'] - df['Completed_Hours']
    df['Daily_Velocity'] = (df['Completed_Hours'] / 5).clip(lower=0.1)
    df['Days_Needed_At_Current_Pace'] = df['Hours_Remaining_Work'] / df['Daily_Velocity']
    df['Will_Breach'] = df['Days_Needed_At_Current_Pace'] > df['Days_Remaining']
    df['Breach_Delay_Days'] = (df['Days_Needed_At_Current_Pace'] - df['Days_Remaining']).clip(lower=0)
    df['Penalty_At_Risk'] = df['Will_Breach'] * df['Breach_Delay_Days'] * df['SLA_Penalty_Per_Day']

    at_risk = df[df['Will_Breach'] | (df['Days_Remaining'] <= 1)].copy()
    total_penalty_at_risk = df['Penalty_At_Risk'].sum()

    llm_context = f"Current Date: {today}\n\nAt-Risk Tasks:\n"
    for _, row in at_risk.iterrows():
        llm_context += f"""
Task: {row['Task_Name']} (ID: {row['Task_ID']})
Assignee: {row['Assignee']} | Team: {row['Team']} | Priority: {row['Priority']}
Progress: {row['Completion_Pct']}% ({row['Completed_Hours']}/{row['Planned_Hours']} hours)
Deadline: {row['Deadline']} ({row['Days_Remaining']} days remaining)
Days needed at current pace: {row['Days_Needed_At_Current_Pace']:.1f}
Penalty per day of delay: ${row['SLA_Penalty_Per_Day']:,}
Estimated penalty if no action: ${row['Penalty_At_Risk']:,.0f}
"""
    llm_context += f"\nTotal financial exposure: ${total_penalty_at_risk:,.0f}"

    llm_analysis = call_llm(
        system_prompt=SYSTEM_PROMPT,
        user_message=llm_context,
        max_tokens=2500
    )

    log(
        agent="SLAPreventionAgent",
        action="sla_breach_detection",
        input_summary=f"Monitored {len(df)} tasks across {df['Team'].nunique()} teams",
        output_summary=f"{len(at_risk)} tasks at breach risk. "
                      f"Total penalty exposure: ${total_penalty_at_risk:,.0f}",
        reasoning="Calculated real-time velocity per task, projected completion dates, "
                 "compared against deadlines. LLM generated specific recovery plans."
    )

    return {
        "raw_data": df,
        "at_risk_tasks": at_risk,
        "all_tasks": df,
        "llm_recovery_plan": llm_analysis,
        "total_penalty_at_risk": total_penalty_at_risk,
        "breach_count": len(at_risk)
    }