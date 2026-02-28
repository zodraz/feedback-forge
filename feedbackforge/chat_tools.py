"""
FeedbackForge Chat Tools
========================

AI function tools for the chat mode executive dashboard.
"""

import json
from typing import Annotated

from agent_framework import ai_function

from .data_store import feedback_store


@ai_function
def get_weekly_summary() -> str:
    """Get weekly feedback summary with sentiment, top issues, and urgent items."""
    summary = feedback_store.get_weekly_summary()
    return json.dumps({
        "total_responses": summary["total_responses"],
        "sentiment": summary["sentiment"],
        "top_issues": [
            {"issue": i[0], "mentions": i[1], "priority": "P0" if i[1] > 40 else "P1" if i[1] > 25 else "P2"}
            for i in summary["top_issues"]
        ],
        "urgent_items": summary["urgent_count"],
    }, indent=2)


@ai_function
def get_issue_details(topic: Annotated[str, "The issue/topic to analyze (e.g., 'ios', 'pricing', 'support')"]) -> str:
    """Get detailed analysis for a specific issue including trend, severity, and recommendations."""
    return json.dumps(feedback_store.get_issue_details(topic), indent=2)


@ai_function
def get_competitor_insights() -> str:
    """Get competitive intelligence including competitor mentions, win reasons, and churn risks."""
    return json.dumps(feedback_store.get_competitor_analysis(), indent=2)


@ai_function
def get_customer_context(customer_id: Annotated[str, "Customer ID (e.g., 'ENT001', 'SMB002')"]) -> str:
    """Get context and feedback history for a specific customer."""
    return json.dumps(feedback_store.get_customer_context(customer_id), indent=2)


@ai_function
def check_for_anomalies() -> str:
    """Check for unusual patterns or spikes in recent feedback."""
    anomalies = feedback_store.detect_anomalies()
    if not anomalies:
        return json.dumps({"status": "normal", "message": "No anomalies detected"})
    return json.dumps({"status": "anomalies_detected", "anomalies": anomalies}, indent=2)


@ai_function
def set_alert(metric: Annotated[str, "Metric to monitor"], threshold: Annotated[float, "Threshold value"]) -> str:
    """Set up an alert for monitoring feedback metrics."""
    alert = feedback_store.set_alert(metric, threshold)
    return json.dumps({"status": "success", "alert": alert}, indent=2)


@ai_function
def generate_action_items(topic: Annotated[str, "Topic to generate action items for"]) -> str:
    """Generate recommended action items for a specific issue."""
    details = feedback_store.get_issue_details(topic)
    actions = [{
        "title": f"[{details.get('priority', 'P2')}] Address {topic} issue",
        "assignee": "Engineering" if "bug" in topic.lower() else "Product",
        "description": f"Issue with {details.get('total_mentions', 0)} mentions, {details.get('negative_sentiment_pct', 0)}% negative sentiment",
    }]
    return json.dumps({"topic": topic, "priority": details.get("priority", "P2"), "action_items": actions}, indent=2)


@ai_function
def escalate_to_team(team: Annotated[str, "Team to escalate to"], issue: Annotated[str, "Issue description"]) -> str:
    """Escalate an issue to a specific team."""
    return json.dumps({"status": "escalated", "team": team, "issue": issue, "channel": f"#{team.lower()}-alerts"}, indent=2)
