"""
FeedbackForge CLI Entry Point
==============================

Main entry point for running FeedbackForge from command line.

Modes:
    chat     - Development UI using DevUI (default)
    serve    - Production server using AG-UI protocol (CopilotKit compatible)
    workflow - Full multi-agent analysis pipeline
"""

import sys
from pathlib import Path

# Support both `python -m feedbackforge` and direct script execution
if __name__ == "__main__" and __package__ is None:
    # Add src directory to path for direct execution
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import asyncio
import argparse
import json
import logging
from datetime import datetime

from feedbackforge.data_store import feedback_store
from feedbackforge.workflow import SurveyAnalysisWorkflow
from feedbackforge.dashboard_agent import create_dashboard_agent
from feedbackforge.faq_command import FAQCommand

# Configure logging to output to console
logging.basicConfig(
    level=logging.DEBUG,  # Changed to DEBUG for more detailed logging
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

# Set agent_framework to DEBUG to see more details
logging.getLogger('agent_framework').setLevel(logging.DEBUG)
logging.getLogger('agent_framework.azure').setLevel(logging.DEBUG)
logging.getLogger('azure').setLevel(logging.WARNING)  # Azure SDK is too verbose

logger = logging.getLogger(__name__)


async def run_workflow_in_background(max_surveys: int):
    """Background task to run workflow analysis."""
    surveys = feedback_store.get_surveys()[:max_surveys]

    logger.info(f"\n📊 Starting workflow with {len(surveys)} surveys from shared data store")

    workflow = SurveyAnalysisWorkflow()
    results = await workflow.analyze(surveys)

    logger.info("\n" + "=" * 60 + "\n📊 WORKFLOW COMPLETE\n" + "=" * 60)
    if results.get("final_report"):
        logger.info(json.dumps(results["final_report"], indent=2))

    logger.info("\n✅ Workflow results are now available in DevUI")

    return results


async def run_workflow_mode(max_surveys: int = 200, devui: bool = False, port: int = 8090):
    """Run the full multi-agent workflow analysis using shared data store."""

    # Launch DevUI first if requested
    if devui:
        logger.info("\n" + "=" * 60)
        logger.info("  Launching DevUI - workflow will run in background...")
        logger.info("=" * 60)
        logger.info(f"\n🌐 DevUI starting at http://localhost:{port}")
        logger.info(f"\n   👉 Open your browser to: http://localhost:{port}")
        logger.info("\nTry these queries:")
        logger.info("  - 'What's the status of the workflow?'")
        logger.info("  - 'Show me this week's feedback summary'")
        logger.info("  - 'Summarize the workflow analysis results' (after completion)")
        logger.info("  - 'What were the key themes identified?'")
        logger.info("=" * 60)

        from agent_framework.devui import serve

        # Create agent and start workflow in background
        agent = create_dashboard_agent()

        # Start workflow as background task
        asyncio.create_task(run_workflow_in_background(max_surveys))

        # Launch DevUI (this blocks)
        # Note: auto_open may not work in WSL2 or when debugging
        serve(entities=[agent], port=port, auto_open=True)
    else:
        # Run workflow without DevUI
        surveys = feedback_store.get_surveys()[:max_surveys]

        logger.info(f"\n📊 Using {len(surveys)} surveys from shared data store")

        workflow = SurveyAnalysisWorkflow()
        results = await workflow.analyze(surveys)

        logger.info("\n" + "=" * 60 + "\n📊 RESULTS\n" + "=" * 60)
        if results.get("final_report"):
            logger.info(json.dumps(results["final_report"], indent=2))

        return results


def run_chat_mode(port: int = 8090):
    """Launch the DevUI chat interface (development mode)."""
    from agent_framework.devui import serve

    logger.info("=" * 60)
    logger.info("  FeedbackForge - Development Mode (DevUI)")
    logger.info("=" * 60)
    logger.info(f"\n📊 Loaded {len(feedback_store.feedback)} feedback items")
    logger.info(f"\nStarting DevUI at http://localhost:{port}")
    logger.info("\nTry these queries:")
    logger.info("  - 'Show me this week's feedback summary'")
    logger.info("  - 'Tell me more about the iOS crashes'")
    logger.info("  - 'What are customers saying about competitors?'")
    logger.info("  - 'Check for any anomalies'")
    logger.info("=" * 60)

    agent = create_dashboard_agent()
    serve(entities=[agent], port=port, auto_open=True)


def run_serve_mode(host: str = "0.0.0.0", port: int = 8081, reload: bool = False):
    """Launch the AG-UI production server (CopilotKit compatible)."""
    from feedbackforge.server import run_server

    run_server(host=host, port=port, reload=reload)


def main():
    parser = argparse.ArgumentParser(
        description="FeedbackForge: Multi-Agent Feedback Analyzer",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m feedbackforge              # DevUI development mode
  python -m feedbackforge chat         # DevUI development mode
  python -m feedbackforge serve        # AG-UI production server
  python -m feedbackforge serve --port 5000 --reload
  python -m feedbackforge workflow     # Run full analysis pipeline
  python -m feedbackforge workflow --max-surveys 50
  python -m feedbackforge workflow --devui  # Run workflow then launch DevUI
  python -m feedbackforge faq          # Generate FAQs using RAG
  python -m feedbackforge faq --days 7 --max-faqs 20
        """
    )
    subparsers = parser.add_subparsers(dest="mode", help="Operating mode")

    # Chat mode (DevUI - development)
    chat_parser = subparsers.add_parser("chat", help="DevUI development interface")
    chat_parser.add_argument("--port", type=int, default=8090, help="Port for DevUI (default: 8090)")

    # Serve mode (AG-UI - production)
    serve_parser = subparsers.add_parser("serve", help="AG-UI production server (CopilotKit)")
    serve_parser.add_argument("--host", type=str, default="0.0.0.0", help="Host to bind (default: 0.0.0.0)")
    serve_parser.add_argument("--port", type=int, default=8081, help="Port for server (default: 8081)")
    serve_parser.add_argument("--reload", action="store_true", help="Enable auto-reload")

    # Workflow mode (batch analysis)
    workflow_parser = subparsers.add_parser("workflow", help="Run full analysis pipeline")
    workflow_parser.add_argument("--max-surveys", type=int, default=20, help="Max surveys to analyze (default: 20)")
    workflow_parser.add_argument("--devui", action="store_true", help="Launch DevUI after workflow completes")
    workflow_parser.add_argument("--port", type=int, default=8090, help="Port for DevUI (default: 8090)")

    # FAQ mode (RAG-based FAQ generation)
    faq_parser = subparsers.add_parser("faq", help="Generate FAQs from customer feedback using RAG")
    FAQCommand.setup_parser(faq_parser)

    args = parser.parse_args()

    if args.mode == "workflow":
        asyncio.run(run_workflow_mode(max_surveys=args.max_surveys, devui=args.devui, port=args.port))
    elif args.mode == "serve":
        run_serve_mode(host=args.host, port=args.port, reload=args.reload)
    elif args.mode == "faq":
        sys.exit(FAQCommand().execute(args))
    else:
        # Default to chat mode
        port = getattr(args, "port", 8090)
        run_chat_mode(port=port)


if __name__ == "__main__":
    main()
