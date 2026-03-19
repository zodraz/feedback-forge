"""
Test Script for Action Planner Agent

Run this to test the agent locally without A2A integration.
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv

# Load environment
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logging.getLogger('azure').setLevel(logging.WARNING)
logging.getLogger('httpx').setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


async def test_action_planner():
    """Test the Action Planner agent with sample feedback."""

    from actionplanner.agent import create_action_planning_agent

    logger.info("=" * 60)
    logger.info("Testing Action Planner Agent")
    logger.info("=" * 60)

    # Create agent
    agent = create_action_planning_agent()

    # Show configured systems
    available_systems = agent.get_available_systems()
    logger.info(f"Available ticketing systems: {available_systems}")

    # Test prompt (similar to what dashboard agent would send)
    test_prompt = """Create an action plan for this customer feedback issue:

**Summary:** iOS app crashes on payment flow completion

**Description:**
Multiple users are reporting that the iOS app crashes immediately after completing
a payment transaction. The crash occurs on both iPhone and iPad devices running
iOS 16 and 17. Users lose their purchase and have to restart the payment process.

The crash seems to be related to the payment confirmation screen. Error logs show
a null pointer exception in the PaymentCompletionViewController.

**Impact:**
- Affected Customers: 45
- Platform: iOS
- Severity: High (payment flow affected)
- Related Feedback IDs: FB001, FB003, FB027, FB034, FB055

**Actions Needed:**
1. Analyze the issue and determine priority, category, and effort
2. Create appropriate tickets in the configured ticketing system
3. Return the ticket IDs and URLs

Please analyze this issue and create the necessary tickets."""

    logger.info("\n" + "=" * 60)
    logger.info("Sending test prompt to agent...")
    logger.info("=" * 60)

    try:
        # Run the agent
        result = await agent.run(test_prompt)

        logger.info("\n" + "=" * 60)
        logger.info("Agent Response:")
        logger.info("=" * 60)
        logger.info(result)

        return result

    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
        return None


async def test_individual_tools():
    """Test individual agent tools."""

    from actionplanner.agent import create_action_planning_agent

    logger.info("\n" + "=" * 60)
    logger.info("Testing Individual Tools")
    logger.info("=" * 60)

    agent = create_action_planning_agent()

    # Test 1: Check available systems
    logger.info("\n[Test 1] Available Systems:")
    systems = agent.get_available_systems()
    logger.info(systems)

    # Test 2: Analyze issue
    logger.info("\n[Test 2] Issue Analysis:")
    analysis = await agent.analyze_issue(
        summary="iOS payment crash",
        description="App crashes after payment completion on iOS devices. Affects checkout flow.",
        affected_customers=45,
        feedback_ids="FB001,FB003,FB027"
    )
    logger.info(f"Analysis result: {analysis}")

    # Test 3: Create ticket (if any system is configured)
    if any(systems.values()):
        import json

        logger.info("\n[Test 3] Creating Ticket:")
        analysis_json = json.dumps(analysis)

        if systems.get("jira"):
            logger.info("Creating Jira ticket...")
            ticket = await agent.create_jira_ticket(analysis_json)
            logger.info(f"Jira ticket result: {ticket}")
    else:
        logger.warning("\n[Test 3] Skipped - Jira not configured")


def main():
    """Run all tests."""
    import sys

    # Check environment
    required = ["AZURE_AI_PROJECT_ENDPOINT", "AZURE_OPENAI_RESPONSES_DEPLOYMENT_NAME"]
    missing = [v for v in required if not os.getenv(v)]

    if missing:
        logger.error("Missing required environment variables:")
        for var in missing:
            logger.error(f"  - {var}")
        logger.error("\nSet these in your .env file")
        sys.exit(1)

    # Run tests
    try:
        logger.info("Starting tests...\n")

        # Test individual tools first
        asyncio.run(test_individual_tools())

        # Then test full agent workflow
        asyncio.run(test_action_planner())

        logger.info("\n" + "=" * 60)
        logger.info("All tests completed!")
        logger.info("=" * 60)

    except KeyboardInterrupt:
        logger.info("\nTests interrupted by user")
    except Exception as e:
        logger.error(f"Tests failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
