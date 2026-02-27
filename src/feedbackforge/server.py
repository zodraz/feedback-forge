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
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from agent_framework.ag_ui import add_agent_framework_fastapi_endpoint

from .dashboard_agent import create_dashboard_agent
from .data_store import feedback_store

logger = logging.getLogger(__name__)

# Setup templates directory
TEMPLATES_DIR = Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


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

    # Create the dashboard agent and register AG-UI endpoint at /agent
    agent = create_dashboard_agent()
    add_agent_framework_fastapi_endpoint(app, agent, "/agent")

    @app.get("/", response_class=HTMLResponse)
    async def root(request: Request):
        """Welcome page with API information."""
        return templates.TemplateResponse(
            "welcome.html",
            {
                "request": request,
                "base_url": str(request.base_url).rstrip('/'),
                "feedback_count": len(feedback_store.feedback),
                "alerts_count": len(feedback_store.alerts),
            }
        )

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
    print(f"  - Welcome Page:   http://{host}:{port}/")
    print(f"  - AG-UI Protocol: http://{host}:{port}/agent (POST)")
    print(f"  - Health Check:   http://{host}:{port}/health")
    print(f"  - Service Info:   http://{host}:{port}/info")
    print(f"  - API Docs:       http://{host}:{port}/docs")
    print("\n💡 Open http://{host}:{port}/ in your browser for API information")
    print("   Connect CopilotKit to http://{host}:{port}/agent")
    print("=" * 60)

    uvicorn.run(
        "feedbackforge.server:create_app",
        factory=True,
        host=host,
        port=port,
        reload=reload,
        log_level="info",
    )
