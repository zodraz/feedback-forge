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
from datetime import datetime

from feedbackforge.data_store import feedback_store
from feedbackforge.workflow import SurveyAnalysisWorkflow
from feedbackforge.dashboard_agent import create_dashboard_agent


async def run_workflow_mode(max_surveys: int = 20):
    """Run the full multi-agent workflow analysis using shared data store."""
    surveys = feedback_store.get_surveys()[:max_surveys]

    print(f"\n📊 Using {len(surveys)} surveys from shared data store")

    workflow = SurveyAnalysisWorkflow()
    results = await workflow.analyze(surveys)

    print("\n" + "=" * 60 + "\n📊 RESULTS\n" + "=" * 60)
    if results.get("final_report"):
        print(json.dumps(results["final_report"], indent=2))

    output_file = f"survey_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\n✅ Saved to: {output_file}")

    return results


def run_chat_mode(port: int = 8090):
    """Launch the DevUI chat interface (development mode)."""
    from agent_framework.devui import serve

    print("=" * 60)
    print("  FeedbackForge - Development Mode (DevUI)")
    print("=" * 60)
    print(f"\n📊 Loaded {len(feedback_store.feedback)} feedback items")
    print(f"\nStarting DevUI at http://localhost:{port}")
    print("\nTry these queries:")
    print("  - 'Show me this week's feedback summary'")
    print("  - 'Tell me more about the iOS crashes'")
    print("  - 'What are customers saying about competitors?'")
    print("  - 'Check for any anomalies'")
    print("=" * 60)

    agent = create_dashboard_agent()
    serve(entities=[agent], port=port, auto_open=True)


def run_serve_mode(host: str = "0.0.0.0", port: int = 8080, reload: bool = False):
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
        """
    )
    subparsers = parser.add_subparsers(dest="mode", help="Operating mode")

    # Chat mode (DevUI - development)
    chat_parser = subparsers.add_parser("chat", help="DevUI development interface")
    chat_parser.add_argument("--port", type=int, default=8090, help="Port for DevUI (default: 8090)")

    # Serve mode (AG-UI - production)
    serve_parser = subparsers.add_parser("serve", help="AG-UI production server (CopilotKit)")
    serve_parser.add_argument("--host", type=str, default="0.0.0.0", help="Host to bind (default: 0.0.0.0)")
    serve_parser.add_argument("--port", type=int, default=8080, help="Port for server (default: 8080)")
    serve_parser.add_argument("--reload", action="store_true", help="Enable auto-reload")

    # Workflow mode (batch analysis)
    workflow_parser = subparsers.add_parser("workflow", help="Run full analysis pipeline")
    workflow_parser.add_argument("--max-surveys", type=int, default=20, help="Max surveys to analyze (default: 20)")

    args = parser.parse_args()

    if args.mode == "workflow":
        asyncio.run(run_workflow_mode(max_surveys=args.max_surveys))
    elif args.mode == "serve":
        run_serve_mode(host=args.host, port=args.port, reload=args.reload)
    else:
        # Default to chat mode
        port = getattr(args, "port", 8090)
        run_chat_mode(port=port)


if __name__ == "__main__":
    main()
