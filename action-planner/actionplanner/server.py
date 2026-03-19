"""
Action Planner A2A Server

Exposes the Action Planning Agent via A2A protocol using the a2a-sdk.
"""

import logging
import os
from typing import Optional

import uvicorn
from a2a.server.apps.jsonrpc.starlette_app import A2AStarletteApplication
from a2a.server.request_handlers.default_request_handler import DefaultRequestHandler
from a2a.server.tasks.inmemory_task_store import InMemoryTaskStore
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .agent import create_action_planning_agent
from .agent_definitions import get_action_planner_card
from .agent_executor import AgentFrameworkExecutor

logger = logging.getLogger(__name__)

# Global agent instance (initialized on startup)
action_planning_agent = None


def create_app(host: str = "localhost", port: int = 8084, cors_origins: Optional[list[str]] = None) -> FastAPI:
    """
    Create FastAPI app with AG-UI endpoint for Action Planning Agent.

    Args:
        cors_origins: List of allowed CORS origins. Defaults to ["*"] for development.

    Returns:
        Configured FastAPI application.
    """
    app = FastAPI(
        title="Action Planner",
        description="Autonomous Action Planning Agent - Converts feedback insights into trackable action items",
        version="1.0.0",
    )

    # Configure CORS for A2A communication
    origins = cors_origins or ["*"]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.on_event("startup")
    async def startup_event():
        """Initialize the agent on startup."""
        global action_planning_agent
        logger.info("=== Action Planner Server Starting ===")

        try:
            # Create the Action Planning Agent
            action_planning_agent = create_action_planning_agent()

            # Build A2A server components
            url = f"http://{host}:{port}/"
            agent_card = get_action_planner_card(url)
            executor = AgentFrameworkExecutor(action_planning_agent._chat_agent)
            task_store = InMemoryTaskStore()
            request_handler = DefaultRequestHandler(
                agent_executor=executor,
                task_store=task_store,
            )

            # Create and mount A2A Starlette application
            a2a_app = A2AStarletteApplication(
                agent_card=agent_card,
                http_handler=request_handler,
            )

            # Mount A2A app at root to serve /.well-known/agent.json
            app.mount("/", a2a_app.build())

            available_systems = action_planning_agent.get_available_systems()
            configured_systems = [k for k, v in available_systems.items() if v]

            logger.info(f"Action Planning Agent initialized")
            logger.info(f"Configured ticketing systems: {configured_systems or 'None'}")
            logger.info(f"A2A endpoint ready at {url}")
            logger.info(f"AgentCard served at {url}.well-known/agent.json")
            logger.info("=== Server Ready ===")

        except Exception as e:
            logger.error(f"Failed to initialize agent: {e}", exc_info=True)
            raise

    @app.get("/api")
    async def root():
        """Welcome endpoint with service information."""
        return {
            "service": "Action Planner",
            "version": "1.0.0",
            "description": "Autonomous agent that converts feedback insights into trackable action items",
            "protocol": "A2A (Agent-to-Agent)",
            "endpoints": {
                "agent_card": "/.well-known/agent.json (GET) - A2A AgentCard discovery",
                "health": "/api/health (GET) - Health check",
                "info": "/api/info (GET) - Detailed service information",
                "systems": "/api/systems (GET) - Available ticketing systems"
            },
            "documentation": "/docs (Swagger UI)"
        }

    @app.get("/api/health")
    async def health_check():
        """Health check endpoint."""
        if not action_planning_agent:
            return JSONResponse(
                status_code=503,
                content={"status": "unhealthy", "reason": "Agent not initialized"}
            )

        return {
            "status": "healthy",
            "service": "action-planner",
            "agent": "ActionPlanningAgent",
            "protocol": "A2A"
        }

    @app.get("/api/info")
    async def info():
        """Detailed service information endpoint."""
        if not action_planning_agent:
            return JSONResponse(
                status_code=503,
                content={"error": "Agent not initialized"}
            )

        available_systems = action_planning_agent.get_available_systems()

        return {
            "name": "Action Planner",
            "description": "Autonomous Action Planning Agent for FeedbackForge",
            "protocol": "A2A (Agent-to-Agent)",
            "capabilities": [
                "Issue analysis and prioritization",
                "Multi-platform ticket creation (Jira)",
                "Intelligent effort estimation",
                "Team assignment suggestions",
                "Progress tracking"
            ],
            "ticketing_systems": {
                "jira": {
                    "available": available_systems["jira"],
                    "features": ["Bug tracking", "User stories", "Sprint management"]
                }
            },
            "agent": {
                "name": "ActionPlanningAgent",
                "endpoint": os.environ.get("AZURE_AI_PROJECT_ENDPOINT", "Not configured"),
                "model": os.environ.get("AZURE_OPENAI_RESPONSES_DEPLOYMENT_NAME", "Not configured")
            }
        }

    @app.get("/api/systems")
    async def systems():
        """Get available ticketing systems."""
        if not action_planning_agent:
            return JSONResponse(
                status_code=503,
                content={"error": "Agent not initialized"}
            )

        available = action_planning_agent.get_available_systems()
        return {
            "systems": available,
            "configured_count": sum(1 for v in available.values() if v)
        }

    return app


def run_server(host: str = "0.0.0.0", port: int = 8084):
    """
    Run the Action Planner A2A server.

    Args:
        host: Host to bind to.
        port: Port to listen on.
    """
    logger.info("=" * 60)
    logger.info("  Action Planner - A2A Server")
    logger.info("=" * 60)
    logger.info(f"\nStarting server at http://{host}:{port}")
    logger.info("\nEndpoints:")
    logger.info(f"  - A2A AgentCard:  http://{host}:{port}/.well-known/agent.json")
    logger.info(f"  - API Info:       http://{host}:{port}/api")
    logger.info(f"  - Health Check:   http://{host}:{port}/api/health")
    logger.info(f"  - Service Info:   http://{host}:{port}/api/info")
    logger.info(f"  - API Docs:       http://{host}:{port}/docs")
    logger.info("\nA2A Usage:")
    logger.info(f"  Dashboard Agent can discover and call this agent at http://{host}:{port}/")
    logger.info("  Example: 'Create tickets for iOS crash issues affecting 45 users'")
    logger.info("=" * 60)

    # Create app with host and port for A2A setup
    app = create_app(host=host, port=port)

    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level=os.getenv("LOG_LEVEL", "info").lower(),
    )
