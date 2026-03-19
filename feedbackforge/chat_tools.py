"""
FeedbackForge Chat Tools
========================

AI function tools for the chat mode executive dashboard.
"""

import json
import logging
from typing import Annotated

from agent_framework import ai_function

from .data_store import feedback_store

logger = logging.getLogger(__name__)


@ai_function
def get_weekly_summary() -> str:
    """Get weekly feedback summary with sentiment, top issues, and urgent items."""
    try:
        logger.debug("📊 Calling get_weekly_summary tool")
        summary = feedback_store.get_weekly_summary()
        result = json.dumps({
            "total_responses": summary["total_responses"],
            "sentiment": summary["sentiment"],
            "top_issues": [
                {"issue": i[0], "mentions": i[1], "priority": "P0" if i[1] > 40 else "P1" if i[1] > 25 else "P2"}
                for i in summary["top_issues"]
            ],
            "urgent_items": summary["urgent_count"],
        }, indent=2)
        logger.debug("✅ get_weekly_summary completed")
        return result
    except Exception as e:
        logger.error(f"❌ Error in get_weekly_summary: {e}", exc_info=True)
        return json.dumps({"error": str(e), "message": "Failed to retrieve weekly summary"}, indent=2)


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


@ai_function
async def run_workflow_analysis(max_surveys: Annotated[int, "Maximum number of surveys to analyze (default: 20)"] = 20) -> str:
    """
    Run the complete multi-agent workflow analysis to generate a comprehensive executive summary.

    This triggers a full parallel analysis pipeline that:
    - Analyzes sentiment across all feedback
    - Extracts topics and themes
    - Detects anomalies
    - Performs competitive analysis
    - Generates insights and recommendations
    - Creates prioritized action items
    - Produces an executive report

    The report is saved to CosmosDB and accessible via get_latest_workflow_report().
    This is a more comprehensive analysis than individual tools and takes 30-60 seconds.
    """
    try:
        logger.info(f"🚀 Starting workflow analysis with {max_surveys} surveys")

        from .workflow import SurveyAnalysisWorkflow

        # Get surveys from data store
        surveys = feedback_store.get_surveys()[:max_surveys]

        if not surveys:
            return json.dumps({
                "error": "No surveys available",
                "message": "The data store is empty. Please ensure feedback data is loaded."
            }, indent=2)

        # Run workflow
        workflow = SurveyAnalysisWorkflow()
        results = await workflow.analyze(surveys)

        # Save to CosmosDB
        report_id = feedback_store.save_workflow_report(results)

        # Return summary
        final_report = results.get("final_report", {})
        return json.dumps({
            "status": "complete",
            "report_id": report_id,
            "surveys_analyzed": results.get("surveys_analyzed", 0),
            "executive_summary": final_report.get("executive_summary", "Analysis complete"),
            "key_metrics": final_report.get("key_metrics", {}),
            "critical_issues_count": len(final_report.get("critical_issues", [])),
            "recommendations_count": len(final_report.get("recommendations", [])),
            "message": "Full workflow report saved to database. Use get_latest_workflow_report() for complete details."
        }, indent=2)

    except Exception as e:
        logger.error(f"❌ Workflow analysis failed: {e}", exc_info=True)
        return json.dumps({
            "error": str(e),
            "message": "Workflow analysis failed. Please check the logs for details."
        }, indent=2)


@ai_function
def get_latest_workflow_report() -> str:
    """
    Retrieve the most recent comprehensive workflow analysis report.

    Returns the complete executive report including:
    - Executive summary covering all findings
    - Key metrics and sentiment breakdown
    - Critical issues with priorities
    - Detailed recommendations
    - Analysis metadata (surveys analyzed, timestamp)

    Use this to get the full detailed report after running run_workflow_analysis().
    """
    try:
        logger.debug("📊 Retrieving latest workflow report")
        report = feedback_store.get_latest_workflow_report()

        if not report:
            return json.dumps({
                "error": "No workflow reports found",
                "message": "No workflow analysis has been run yet. Use run_workflow_analysis() to generate a report."
            }, indent=2)

        return json.dumps({
            "report_id": report.get("id"),
            "generated_at": report.get("generated_at"),
            "surveys_analyzed": report.get("surveys_analyzed"),
            "final_report": report.get("final_report"),
            "insights": report.get("insights"),
            "priorities": report.get("priorities"),
            "actions": report.get("actions")
        }, indent=2)

    except Exception as e:
        logger.error(f"❌ Error retrieving workflow report: {e}", exc_info=True)
        return json.dumps({
            "error": str(e),
            "message": "Failed to retrieve workflow report"
        }, indent=2)


@ai_function
def get_workflow_reports_history(limit: Annotated[int, "Number of reports to retrieve (default: 5)"] = 5) -> str:
    """
    Get a list of historical workflow analysis reports.

    Returns metadata for recent workflow analyses including:
    - Report ID and timestamp
    - Number of surveys analyzed
    - Executive summary excerpt

    Use this to browse past analyses and compare trends over time.
    """
    try:
        logger.debug(f"📊 Retrieving {limit} workflow reports")
        reports = feedback_store.get_workflow_reports(limit=limit)

        if not reports:
            return json.dumps({
                "reports": [],
                "message": "No workflow reports found. Run run_workflow_analysis() to generate reports."
            }, indent=2)

        # Return condensed version for history view
        history = [
            {
                "report_id": r.get("id"),
                "generated_at": r.get("generated_at"),
                "surveys_analyzed": r.get("surveys_analyzed"),
                "executive_summary_excerpt": r.get("final_report", {}).get("executive_summary", "")[:200] + "..."
            }
            for r in reports
        ]

        return json.dumps({
            "total_reports": len(history),
            "reports": history,
            "message": f"Retrieved {len(history)} workflow reports. Use get_latest_workflow_report() for full details."
        }, indent=2)

    except Exception as e:
        logger.error(f"❌ Error retrieving workflow reports history: {e}", exc_info=True)
        return json.dumps({
            "error": str(e),
            "message": "Failed to retrieve workflow reports history"
        }, indent=2)
