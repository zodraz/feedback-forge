"""
Action Planner CLI Entry Point
"""

import argparse
import logging
import os
import sys
from pathlib import Path

# Support both `python -m actionplanner` and direct script execution
if __name__ == "__main__" and __package__ is None:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Configure logging
log_level = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

# Set specific log levels
logging.getLogger('agent_framework').setLevel(logging.INFO)
logging.getLogger('azure').setLevel(logging.WARNING)
logging.getLogger('httpx').setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


def main():
    """Main entry point for Action Planner CLI."""
    parser = argparse.ArgumentParser(
        description="Action Planner: Autonomous agent for converting feedback into action items",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m actionplanner                    # Start server on default port 8084
  python -m actionplanner --port 8084        # Start on custom port
  python -m actionplanner --host 0.0.0.0     # Bind to all interfaces

Environment Variables:
  See .env.example for required configuration:
  - AZURE_AI_PROJECT_ENDPOINT (required)
  - AZURE_OPENAI_RESPONSES_DEPLOYMENT_NAME (required)
  - JIRA_* (required)

A2A Integration:
  The Action Planner agent can be called by FeedbackForge dashboard agent:

  1. Start FeedbackForge: python -m feedbackforge serve
  2. Start Action Planner: python -m actionplanner
  3. Dashboard agent will call http://localhost:8084/agent via A2A protocol
        """
    )

    parser.add_argument(
        "--host",
        type=str,
        default=os.getenv("HOST", "0.0.0.0"),
        help="Host to bind (default: 0.0.0.0 or HOST env var)"
    )

    parser.add_argument(
        "--port",
        type=int,
        default=int(os.getenv("PORT", "8084")),
        help="Port to listen on (default: 8084 or PORT env var)"
    )

    args = parser.parse_args()

    # Check required environment variables
    required_vars = ["AZURE_AI_PROJECT_ENDPOINT", "AZURE_OPENAI_RESPONSES_DEPLOYMENT_NAME"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]

    if missing_vars:
        logger.error("Missing required environment variables:")
        for var in missing_vars:
            logger.error(f"  - {var}")
        logger.error("\nCopy .env.example to .env and configure your credentials")
        sys.exit(1)

    # Check Jira ticketing system is configured
    ticketing_systems = {
        "Jira": ["JIRA_URL", "JIRA_EMAIL", "JIRA_API_TOKEN"]
    }

    configured_systems = []
    for system_name, vars_needed in ticketing_systems.items():
        if all(os.getenv(var) for var in vars_needed):
            configured_systems.append(system_name)

    if not configured_systems:
        logger.warning("=" * 60)
        logger.warning("  WARNING: No ticketing systems configured!")
        logger.warning("=" * 60)
        logger.warning("\nThe agent will work but cannot create tickets.")
        logger.warning("Configure at least one system in .env:")
        for system_name, vars_needed in ticketing_systems.items():
            logger.warning(f"\n{system_name}:")
            for var in vars_needed:
                logger.warning(f"  - {var}")
        logger.warning("\n" + "=" * 60)
    else:
        logger.info(f"Configured ticketing systems: {', '.join(configured_systems)}")

    # Run the server
    from actionplanner.server import run_server
    run_server(host=args.host, port=args.port)


if __name__ == "__main__":
    main()
