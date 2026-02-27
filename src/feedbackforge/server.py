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
import os
from pathlib import Path
from typing import Optional, List, Dict

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from agent_framework.ag_ui import add_agent_framework_fastapi_endpoint

from .dashboard_agent import create_dashboard_agent
from .data_store import feedback_store
from .sessions import SessionManager, InMemorySessionManager
from .telemetry import setup_telemetry, instrument_app, create_custom_metrics

logger = logging.getLogger(__name__)

# Custom metrics (initialized after telemetry setup)
custom_metrics = {}

# Setup templates directory
TEMPLATES_DIR = Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# Session manager (global)
session_manager: Optional[SessionManager] = None


# Type annotation for union of store types
from typing import Union
FeedbackStoreType = Union["CosmosDBFeedbackStore", "InMemoryFeedbackStore"]


# Pydantic models for API
class SessionRequest(BaseModel):
    thread_id: str
    user_id: str
    messages: List[Dict]
    metadata: Optional[Dict] = None


class SessionMetadataUpdate(BaseModel):
    title: Optional[str] = None
    tags: Optional[List[str]] = None


async def init_session_manager():
    """Initialize session manager with Redis or fallback to in-memory."""
    global session_manager

    redis_url = os.environ.get("REDIS_URL")

    if redis_url:
        try:
            import redis.asyncio as redis
            redis_client = redis.from_url(redis_url, decode_responses=True)
            # Test connection
            await redis_client.ping()
            session_manager = SessionManager(redis_client, ttl=3600)
            logger.info("✅ Using Redis for session management")
        except Exception as e:
            logger.warning(f"⚠️ Redis connection failed: {e}. Using in-memory sessions.")
            session_manager = InMemorySessionManager(ttl=3600)
    else:
        logger.info("ℹ️ REDIS_URL not set. Using in-memory sessions.")
        session_manager = InMemorySessionManager(ttl=3600)


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

    # Setup OpenTelemetry before startup
    telemetry_enabled = setup_telemetry(service_name="feedbackforge", service_version="1.0.0")

    # Instrument the FastAPI app with OpenTelemetry
    if telemetry_enabled:
        instrument_app(app)

    # Initialize session manager and metrics on startup
    @app.on_event("startup")
    async def startup_event():
        global custom_metrics
        await init_session_manager()

        # Initialize custom metrics
        if telemetry_enabled:
            custom_metrics = create_custom_metrics()
            logger.info("✅ Custom metrics initialized")

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

    # Session management endpoints
    @app.post("/api/sessions/save")
    async def save_session(request: SessionRequest):
        """Save a conversation session."""
        if not session_manager:
            raise HTTPException(status_code=503, detail="Session manager not initialized")

        success = await session_manager.save_session(
            thread_id=request.thread_id,
            messages=request.messages,
            user_id=request.user_id,
            metadata=request.metadata
        )

        # Track metric for new sessions
        if success and custom_metrics and "sessions_created" in custom_metrics:
            custom_metrics["sessions_created"].add(1, {"user_id": request.user_id})

        if success:
            return {"status": "success", "thread_id": request.thread_id, "user_id": request.user_id}
        else:
            raise HTTPException(status_code=500, detail="Failed to save session")

    @app.get("/api/sessions/{thread_id}")
    async def load_session(thread_id: str, user_id: str):
        """Load a conversation session. Requires user_id for ownership verification."""
        if not session_manager:
            raise HTTPException(status_code=503, detail="Session manager not initialized")

        session = await session_manager.load_session(thread_id, user_id)

        if session:
            return session
        else:
            raise HTTPException(status_code=404, detail="Session not found or unauthorized")

    @app.get("/api/sessions")
    async def list_sessions(user_id: str, limit: int = 50):
        """List all active sessions for a specific user."""
        if not session_manager:
            raise HTTPException(status_code=503, detail="Session manager not initialized")

        sessions = await session_manager.list_sessions(user_id=user_id, limit=limit)
        return {"sessions": sessions, "count": len(sessions)}

    @app.delete("/api/sessions/{thread_id}")
    async def delete_session(thread_id: str, user_id: str):
        """Delete a conversation session. Requires user_id for ownership verification."""
        if not session_manager:
            raise HTTPException(status_code=503, detail="Session manager not initialized")

        success = await session_manager.delete_session(thread_id, user_id)

        if success:
            return {"status": "deleted", "thread_id": thread_id}
        else:
            raise HTTPException(status_code=404, detail="Session not found or unauthorized")

    @app.patch("/api/sessions/{thread_id}/metadata")
    async def update_session_metadata(thread_id: str, user_id: str, update: SessionMetadataUpdate):
        """Update session metadata (title, tags, etc.). Requires user_id for ownership verification."""
        if not session_manager:
            raise HTTPException(status_code=503, detail="Session manager not initialized")

        metadata = {}
        if update.title:
            metadata["title"] = update.title
        if update.tags:
            metadata["tags"] = update.tags

        success = await session_manager.update_metadata(thread_id, user_id, metadata)

        if success:
            return {"status": "updated", "thread_id": thread_id, "metadata": metadata}
        else:
            raise HTTPException(status_code=404, detail="Session not found or unauthorized")

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
