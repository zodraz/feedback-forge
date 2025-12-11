"""
FeedbackForge Chat Agent
========================

ChatAgent creation for the executive dashboard assistant.
"""

from agent_framework import ChatAgent
from agent_framework_azure_ai import AzureAIClient
from azure.identity.aio import DefaultAzureCredential

from .chat_tools import (
    get_weekly_summary,
    get_issue_details,
    get_competitor_insights,
    get_customer_context,
    check_for_anomalies,
    set_alert,
    generate_action_items,
    escalate_to_team,
)

AGENT_INSTRUCTIONS = """You are FeedbackForge, an Executive Dashboard Assistant for analyzing customer feedback.

Capabilities:
- Weekly summaries with sentiment distribution and top issues
- Deep-dive into specific issues with trends and recommendations
- Competitive intelligence and churn risk analysis
- Customer context lookup
- Anomaly detection for emerging issues
- Action item generation and team escalation

Communication style:
- Be concise and data-driven
- Use clear formatting with bullet points
- Highlight priorities (P0=Critical, P1=High, P2=Medium)
- Always offer next steps or deeper analysis
- Proactively flag urgent issues"""

TOOLS = [
    get_weekly_summary,
    get_issue_details,
    get_competitor_insights,
    get_customer_context,
    check_for_anomalies,
    set_alert,
    generate_action_items,
    escalate_to_team,
]


def create_dashboard_agent() -> ChatAgent:
    """Create the Executive Dashboard Assistant using Azure AI Foundry.

    Uses environment variables for configuration:
        - AZURE_AI_PROJECT_ENDPOINT: Azure AI Foundry project endpoint
        - AZURE_AI_MODEL_DEPLOYMENT_NAME: Model deployment name (optional)
    """
    # AzureAIClient reads AZURE_AI_PROJECT_ENDPOINT and AZURE_AI_MODEL_DEPLOYMENT_NAME
    # from environment variables automatically
    chat_client = AzureAIClient(
        credential=DefaultAzureCredential(),
    )

    return ChatAgent(
        chat_client=chat_client,
        name="FeedbackForge",
        description="Executive Dashboard Assistant for customer feedback analysis",
        instructions=AGENT_INSTRUCTIONS,
        tools=TOOLS,
    )