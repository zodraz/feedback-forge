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
import os
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

# Suppress SSL shutdown timeout errors from Application Insights telemetry
logging.getLogger('asyncio').setLevel(logging.CRITICAL)
logging.getLogger('urllib3.connectionpool').setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


def write_workflow_report_to_volume(results: dict, output_dir: str = "/mnt/reports"):
    """
    Write workflow final_report to mounted volume for persistence.

    Args:
        results: Workflow results dictionary
        output_dir: Directory path for mounted volume (default: /mnt/reports)
    """
    from pathlib import Path

    if not results.get("final_report"):
        logger.warning("⚠️  No final_report in results, skipping file write")
        return

    try:
        # Create output directory if it doesn't exist
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"workflow_report_{timestamp}.json"
        filepath = output_path / filename

        # Write JSON report
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(results["final_report"], f, indent=2, ensure_ascii=False)

        logger.info(f"✅ Workflow report written to: {filepath}")
        logger.info(f"   File size: {filepath.stat().st_size / 1024:.2f} KB")

        # Also write a "latest" symlink/copy for easy access
        latest_path = output_path / "latest_report.json"
        with open(latest_path, 'w', encoding='utf-8') as f:
            json.dump(results["final_report"], f, indent=2, ensure_ascii=False)

        logger.info(f"✅ Latest report symlink: {latest_path}")

    except Exception as e:
        logger.error(f"❌ Failed to write workflow report: {e}", exc_info=True)


async def run_workflow_in_background(max_surveys: int):
    """Background task to run workflow analysis."""
    surveys = feedback_store.get_surveys()[:max_surveys]

    logger.info(f"\n📊 Starting workflow with {len(surveys)} surveys from shared data store")

    workflow = SurveyAnalysisWorkflow()
    results = await workflow.analyze(surveys)

    logger.info("\n" + "=" * 60 + "\n📊 WORKFLOW COMPLETE\n" + "=" * 60)
    if results.get("final_report"):
        logger.info(json.dumps(results["final_report"], indent=2))

    # Write report to mounted volume (configurable via WORKFLOW_REPORT_PATH env var)
    report_path = os.getenv("WORKFLOW_REPORT_PATH", "/mnt/reports")
    write_workflow_report_to_volume(results, report_path)

    # Save to CosmosDB for dashboard access
    try:
        report_id = feedback_store.save_workflow_report(results)
        logger.info(f"✅ Workflow report saved to CosmosDB: {report_id}")
    except Exception as e:
        logger.error(f"⚠️  Failed to save workflow report to CosmosDB: {e}")

    logger.info("\n✅ Workflow results are now available in DevUI and dashboard")

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

        # Write report to mounted volume (configurable via WORKFLOW_REPORT_PATH env var)
        report_path = os.getenv("WORKFLOW_REPORT_PATH", "/mnt/reports")
        write_workflow_report_to_volume(results, report_path)

        # Save to CosmosDB for dashboard access
        try:
            report_id = feedback_store.save_workflow_report(results)
            logger.info(f"✅ Workflow report saved to CosmosDB: {report_id}")
        except Exception as e:
            logger.error(f"⚠️  Failed to save workflow report to CosmosDB: {e}")

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

    # Create agent (now async, so use asyncio.run in this sync context)
    agent = asyncio.run(create_dashboard_agent())
    serve(entities=[agent], port=port, auto_open=True)


def run_serve_mode(host: str = "0.0.0.0", port: int = 8081, reload: bool = False):
    """Launch the AG-UI production server (CopilotKit compatible)."""
    from feedbackforge.server import run_server

    run_server(host=host, port=port, reload=reload)


def run_mcp_mode(transport: str = "stdio", host: str = "127.0.0.1", port: int = 8085):
    """Launch the MCP server for external feedback integration."""
    from feedbackforge.mcp_server import run_sse_server, main

    logger.info("=" * 60)
    logger.info("  FeedbackForge - MCP Server Mode")
    logger.info("=" * 60)

    if transport == "sse":
        logger.info(f"\nStarting MCP server with SSE transport at http://{host}:{port}")
        logger.info("\nEndpoints:")
        logger.info(f"  - SSE:    http://{host}:{port}/sse")
        logger.info(f"  - POST:   http://{host}:{port}/messages")
        logger.info(f"  - Health: http://{host}:{port}/health")
    else:
        logger.info("\nStarting MCP server with stdio transport...")
        logger.info("(for Claude Desktop / VS Code integration)")

    logger.info("\nAvailable tools:")
    logger.info("  - fetch_zendesk_tickets")
    logger.info("  - ingest_feedback_to_store")
    logger.info("  - analyze_sentiment_batch")
    logger.info("  - create_zendesk_ticket")
    logger.info("\nResources:")
    logger.info("  - feedbackforge://feedback/recent")
    logger.info("  - feedbackforge://feedback/urgent")
    logger.info("  - feedbackforge://analytics/summary")
    logger.info("=" * 60)

    # Run the MCP server (blocks until stopped)
    if transport == "sse":
        run_sse_server(host=host, port=port)
    else:
        asyncio.run(main())


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
  python -m feedbackforge mcp          # Run MCP server for external integrations
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

    # MCP mode (Model Context Protocol server)
    mcp_parser = subparsers.add_parser("mcp", help="Run MCP server for external feedback integration")
    mcp_parser.add_argument("--transport", choices=["stdio", "sse"], default="stdio",
                           help="Transport protocol (default: stdio)")
    mcp_parser.add_argument("--host", type=str, default="127.0.0.1",
                           help="Host for SSE transport (default: 127.0.0.1)")
    mcp_parser.add_argument("--port", type=int, default=8085,
                           help="Port for SSE transport (default: 8085)")

    args = parser.parse_args()

    if args.mode == "workflow":
        asyncio.run(run_workflow_mode(max_surveys=args.max_surveys, devui=args.devui, port=args.port))
    elif args.mode == "serve":
        run_serve_mode(host=args.host, port=args.port, reload=args.reload)
    elif args.mode == "faq":
        sys.exit(FAQCommand().execute(args))
    elif args.mode == "mcp":
        run_mcp_mode(transport=args.transport, host=args.host, port=args.port)
    else:
        # Default to chat mode
        port = getattr(args, "port", 8090)
        run_chat_mode(port=port)


if __name__ == "__main__":
    main()
