import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.audit_logger import log


def financial_model(vendor_result=None, anomaly_result=None, sla_result=None) -> dict:
    breakdown = []
    total_before = 0
    total_after = 0

    # Vendor Consolidation
    if vendor_result and vendor_result.get("clusters"):
        vendor_monthly_savings = vendor_result.get("total_monthly_savings", 0)
        current_vendor_spend = sum(c['total_monthly_cost'] for c in vendor_result['clusters'])
        optimized_vendor_spend = current_vendor_spend - vendor_monthly_savings

        breakdown.append({
            "category": "Vendor Consolidation",
            "current_monthly": int(current_vendor_spend),
            "optimized_monthly": int(optimized_vendor_spend),
            "monthly_savings": int(vendor_monthly_savings),
            "annual_savings": int(vendor_monthly_savings * 12),
            "assumption": "12% average savings via contract consolidation & renegotiation",
            "confidence": "HIGH"
        })
        total_before += current_vendor_spend
        total_after += optimized_vendor_spend

    # Cloud Anomaly
    if anomaly_result and anomaly_result.get("anomalies") is not None:
        anomaly_df = anomaly_result['anomalies']
        if len(anomaly_df) > 0:
            anomaly_cost = anomaly_df['Cost'].sum()
            baseline = anomaly_result.get("baseline_avg_cost", 0)
            excess_cost = max(0, anomaly_cost - (baseline * len(anomaly_df)))
            savings = excess_cost * 0.70
            n = len(anomaly_df)

            breakdown.append({
                "category": "Cloud Cost Anomalies",
                "current_monthly": int(anomaly_cost / n),
                "optimized_monthly": int(baseline),
                "monthly_savings": int(savings / n) if n > 0 else 0,
                "annual_savings": int(savings * (12 / n)),
                "assumption": "70% of excess spend recoverable via right-sizing + auto-scaling fixes",
                "confidence": "MEDIUM"
            })
            total_before += anomaly_cost
            total_after += anomaly_cost - savings

    # SLA Prevention
    if sla_result and sla_result.get("total_penalty_at_risk", 0) > 0:
        penalty = sla_result['total_penalty_at_risk']
        avoidable = penalty * 0.75

        breakdown.append({
            "category": "SLA Penalty Prevention",
            "current_monthly": int(penalty),
            "optimized_monthly": int(penalty - avoidable),
            "monthly_savings": int(avoidable),
            "annual_savings": int(avoidable * 12),
            "assumption": "75% of penalties avoidable with immediate resource reallocation",
            "confidence": "HIGH"
        })
        total_before += penalty
        total_after += penalty - avoidable

    total_savings = total_before - total_after
    roi_pct = ((total_savings / total_before) * 100) if total_before > 0 else 0

    result = {
        "before_optimization": int(total_before),
        "after_optimization": int(total_after),
        "total_savings": int(total_savings),
        "annual_projection": int(total_savings * 12),
        "roi_percentage": round(roi_pct, 1),
        "breakdown": breakdown
    }

    log(
        agent="ImpactEngine",
        action="financial_model_computation",
        input_summary=f"Vendor clusters: {len(vendor_result.get('clusters', [])) if vendor_result else 0}, "
                     f"Anomalies: {len(anomaly_result.get('anomalies', [])) if anomaly_result else 0}, "
                     f"SLA risks: {sla_result.get('breach_count', 0) if sla_result else 0}",
        output_summary=f"Total savings: ${total_savings:,.0f}/month | "
                      f"Annual: ${total_savings*12:,.0f} | ROI: {roi_pct:.1f}%",
        reasoning="Aggregated savings from vendor consolidation (12%), "
                 "cloud right-sizing (70% excess recovery), SLA penalty avoidance (75%)"
    )

    return result