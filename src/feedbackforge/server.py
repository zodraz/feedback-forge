"""
FeedbackForge AG-UI Server
==========================

Production server using AG-UI protocol for CopilotKit integration.

Usage:
    python -m feedbackforge serve           # Start AG-UI server on port 8080
    python -m feedbackforge serve --port 5000  # Custom port

The server exposes an AG-UI compatible endpoint that can be consumed by:
- CopilotKit React/Angular frontends
- Any AG-UI protocol compatible client
"""

import logging
from typing import Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from agent_framework.ag_ui import add_agent_framework_fastapi_endpoint

from .dashboard_agent import create_dashboard_agent
from .data_store import feedback_store

logger = logging.getLogger(__name__)


def create_app(cors_origins: Optional[list[str]] = None) -> FastAPI:
    """Create FastAPI app with AG-UI endpoint for FeedbackForge agent.

    Args:
        cors_origins: List of allowed CORS origins. Defaults to ["*"] for development.

    Returns:
        Configured FastAPI application.
    """
    app = FastAPI(
        title="FeedbackForge",
        description="Executive Dashboard Assistant for customer feedback analysis - AG-UI Protocol",
        version="1.0.0",
    )

    # Configure CORS for frontend access
    origins = cors_origins or ["*"]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Create the dashboard agent and register AG-UI endpoint
    agent = create_dashboard_agent()
    add_agent_framework_fastapi_endpoint(app, agent, "/")

    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        return {
            "status": "healthy",
            "service": "feedbackforge",
            "feedback_count": len(feedback_store.feedback),
        }

    @app.get("/info")
    async def info():
        """Service information endpoint."""
        return {
            "name": "FeedbackForge",
            "description": "Executive Dashboard Assistant for customer feedback analysis",
            "protocol": "AG-UI",
            "capabilities": [
                "weekly_summary",
                "issue_details",
                "competitor_insights",
                "customer_context",
                "anomaly_detection",
                "alert_management",
                "action_generation",
                "team_escalation",
            ],
            "data": {
                "feedback_items": len(feedback_store.feedback),
                "active_alerts": len(feedback_store.alerts),
            },
        }

    return app


def run_server(host: str = "0.0.0.0", port: int = 8080, reload: bool = False):
    """Run the AG-UI server.

    Args:
        host: Host to bind to.
        port: Port to listen on.
        reload: Enable auto-reload for development.
    """
    import uvicorn

    print("=" * 60)
    print("  FeedbackForge - AG-UI Production Server")
    print("=" * 60)
    print(f"\n📊 Loaded {len(feedback_store.feedback)} feedback items")
    print(f"\n🚀 Starting AG-UI server at http://{host}:{port}")
    print("\nEndpoints:")
    print(f"  - AG-UI Protocol: http://{host}:{port}/")
    print(f"  - Health Check:   http://{host}:{port}/health")
    print(f"  - Service Info:   http://{host}:{port}/info")
    print("\nConnect with CopilotKit or any AG-UI compatible client.")
    print("=" * 60)

    uvicorn.run(
        "feedbackforge.server:create_app",
        factory=True,
        host=host,
        port=port,
        reload=reload,
        log_level="info",
    )
