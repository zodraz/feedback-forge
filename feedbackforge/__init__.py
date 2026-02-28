"""
FeedbackForge: Multi-Agent Feedback Survey Analyzer
====================================================

Two modes of operation:
1. WORKFLOW MODE: Full multi-agent parallel analysis pipeline
2. CHAT MODE: Interactive chat UI for querying feedback data
3. SERVE MODE: AG-UI production server

Usage:
    feedbackforge workflow    # Run full analysis pipeline
    feedbackforge chat        # Launch DevUI (development)
    feedbackforge serve       # Launch AG-UI server (production)
    feedbackforge             # Default: chat mode with mock data

Installation:
    pip install -e .
    az login  # Authenticate with Azure CLI
"""

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

from .models import SurveyResponse, AnalysisState, FeedbackItem
from .data_store import feedback_store, CosmosDBFeedbackStore, InMemoryFeedbackStore
from .workflow import SurveyAnalysisWorkflow
from .dashboard_agent import create_dashboard_agent
from .server import create_app, run_server
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

__all__ = [
    # Models
    "SurveyResponse",
    "AnalysisState",
    "FeedbackItem",
    # Data Store
    "CosmosDBFeedbackStore",
    "InMemoryFeedbackStore",
    "feedback_store",
    # Workflow
    "SurveyAnalysisWorkflow",
    # Chat Agent
    "create_dashboard_agent",
    # AG-UI Server
    "create_app",
    "run_server",
    # Chat Tools
    "get_weekly_summary",
    "get_issue_details",
    "get_competitor_insights",
    "get_customer_context",
    "check_for_anomalies",
    "set_alert",
    "generate_action_items",
    "escalate_to_team",
]
