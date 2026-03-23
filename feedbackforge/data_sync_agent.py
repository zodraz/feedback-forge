"""
FeedbackForge Data Sync Agent
==============================

Autonomous LLM-powered agent that intelligently syncs external feedback sources (Zendesk)
into the data store. Makes decisions about what to fetch, when to sync, and how to handle errors.

This agent runs before the dashboard agent to ensure fresh data is available.
Uses MCP (Model Context Protocol) with SSE transport to communicate with the MCP server over HTTP.
"""

import json
import logging
import os
from typing import Any, Dict

from agent_framework import ChatAgent
from azure.identity.aio import DefaultAzureCredential
from azure.ai.projects.aio import AIProjectClient
from azure.ai.projects.models import PromptAgentDefinition
from .azure_client_adapter import AIProjectChatClient

logger = logging.getLogger(__name__)


class DataSyncAgent:
    """
    LLM-powered autonomous agent for intelligent data synchronization.

    This agent uses Azure OpenAI (LLM) to make intelligent decisions about:
    - When to sync data
    - What parameters to use (days, status, priority)
    - How to handle errors
    - What insights to provide

    The agent has access to tools for checking data store state and syncing via MCP.

    Use the async factory method: agent = await DataSyncAgent.create()
    """

    def __init__(self, chat_agent: ChatAgent, endpoint: str, deployment: str):
        """Private init - use DataSyncAgent.create() factory method instead."""
        self._chat_agent = chat_agent
        self.endpoint = endpoint
        self.deployment = deployment

    @classmethod
    async def create(cls):
        """
        Async factory method to create DataSyncAgent.

        Usage:
            agent = await DataSyncAgent.create()
        """
        logger.info("🤖 Creating DataSyncAgent with Azure AI Projects SDK...")

        # Check required environment variables
        endpoint = os.environ.get("AZURE_AI_PROJECT_ENDPOINT")
        deployment = os.environ.get("AZURE_OPENAI_RESPONSES_DEPLOYMENT_NAME")

        if not all([endpoint, deployment]):
            raise ValueError("Missing AZURE_AI_PROJECT_ENDPOINT or AZURE_OPENAI_RESPONSES_DEPLOYMENT_NAME")

        # Assert non-None for type checker (already validated above)
        assert endpoint is not None
        assert deployment is not None

        # Create chat agent
        chat_agent = await cls._create_chat_agent_static(endpoint, deployment)

        logger.info(f"✅ DataSyncAgent initialized with LLM backend: {deployment}")
        return cls(chat_agent, endpoint, deployment)

    @staticmethod
    async def _create_chat_agent_static(endpoint: str, deployment: str) -> ChatAgent:
        """Create the underlying ChatAgent with LLM using AIProjectClient."""
        logger.info("🧠 Creating ChatAgent with Azure AI Projects SDK...")

        credential = DefaultAzureCredential()

        # Create AI Project client using new AIProjectClient pattern
        project = AIProjectClient(
            endpoint=endpoint,
            credential=credential
        )
        logger.info("✅ AIProjectClient created")

        # Create agent version
        agent_version = await project.agents.create_version(
            agent_name="DataSyncAgent",
            definition=PromptAgentDefinition(
                model=deployment,
                instructions=SYNC_AGENT_INSTRUCTIONS,
            ),
        )
        logger.info(f"✅ Agent created (id: {agent_version.id}, name: {agent_version.name}, version: {agent_version.version})")

        # Create adapter to bridge AIProjectClient with ChatClientProtocol
        chat_client = AIProjectChatClient(project=project, agent_version=agent_version)

        # Create ChatAgent with LLM intelligence and tools
        agent = ChatAgent(
            chat_client=chat_client,
            instructions=SYNC_AGENT_INSTRUCTIONS,
            name="DataSyncAgent",
            agent_id=agent_version.id,
            description="Autonomous data synchronization agent with LLM intelligence",
            tools=[sync_zendesk_via_mcp, check_sync_status]
        )

        logger.info(f"✅ ChatAgent created with LLM: {agent.name}")
        return agent

    async def run_autonomous_sync(self) -> Dict[str, Any]:
        """
        Run autonomous sync using LLM to make intelligent decisions.

        The LLM will:
        1. Analyze current data store state
        2. Decide optimal sync parameters
        3. Execute sync via tools
        4. Provide insights

        Returns:
            Sync results and LLM insights
        """
        logger.info("💭 LLM Agent: Analyzing situation and making decisions...")

        prompt = """Analyze the current data store state and perform an intelligent sync of Zendesk tickets.

Tasks:
1. Check the current sync status to understand what data we have
2. Decide on the optimal sync parameters (days, status, priority, limit)
3. Execute the sync via MCP server
4. Report statistics and insights about the operation

Be autonomous - make decisions based on the data store state."""

        # Call the LLM agent - it will use tools to complete the task
        result = await self._chat_agent.run(prompt)

        logger.info("✅ LLM Agent completed autonomous sync")

        return {
            "success": True,
            "agent_response": result,
            "message": "Sync completed with LLM agent intelligence"
        }

logger = logging.getLogger(__name__)

SYNC_AGENT_INSTRUCTIONS = """You are the FeedbackForge Data Sync Agent.

Your role is to autonomously manage the synchronization of external feedback from Zendesk into the FeedbackForge data store.

Responsibilities:
- Assess what data needs to be synced based on the current state
- Determine the optimal time range and filters for fetching tickets
- Handle sync errors gracefully and decide on retry strategies
- Report clear statistics about the sync operation
- Provide insights about data freshness and quality

Tools available:
- sync_zendesk_via_mcp: Connect to MCP server and sync Zendesk tickets
- check_sync_status: Check last sync time and data store status

Decision-making guidelines:
1. Always check the current data store state before syncing
2. For initial sync or empty store: fetch last 30 days, all priorities
3. For incremental sync: fetch only recent tickets (last 7 days)
4. If sync fails, analyze the error and suggest corrective action
5. Report statistics clearly: fetched count, ingested count, skipped duplicates

Be autonomous but transparent - explain your decisions and actions."""


async def sync_zendesk_data_via_mcp_sse(mcp_url: str = "http://127.0.0.1:8085") -> Dict[str, Any]:
    """
    Autonomous sync workflow using MCP protocol with SSE transport.

    Connects to MCP server over HTTP using Server-Sent Events.

    Args:
        mcp_url: Base URL of the MCP server

    Returns:
        Sync statistics and status
    """
    logger.info(f"🔄 Starting autonomous data sync via MCP (SSE) at {mcp_url}...")

    try:
        import asyncio
        from mcp import ClientSession
        from mcp.client.sse import sse_client

        logger.info(f"📡 Connecting to MCP server at {mcp_url}...")

        # First, check if the MCP server is actually responding
        try:
            import httpx
            async with httpx.AsyncClient(timeout=5.0) as client:
                health_check = await client.get(f"{mcp_url}/health")
                logger.info(f"✅ MCP server health check: {health_check.status_code}")
        except Exception as health_error:
            logger.error(f"❌ MCP server health check failed: {health_error}")
            raise ValueError(f"MCP server not responding at {mcp_url}/health")

        # Connect to MCP server via SSE with timeout
        logger.info(f"🔌 Creating SSE client connection to {mcp_url}/sse...")
        sse_connection = sse_client(f"{mcp_url}/sse")
        if sse_connection is None:
            raise ValueError(f"Failed to create SSE client connection to {mcp_url}/sse")

        async with sse_connection as streams:
            if streams is None or len(streams) != 2:
                raise ValueError(f"Invalid SSE connection streams: {streams}")

            read, write = streams

            if read is None or write is None:
                raise ValueError(f"SSE streams are None - read: {read}, write: {write}")

            logger.info("📡 SSE streams created, initializing MCP session...")

            logger.info("🔄 Creating ClientSession...")
            session = ClientSession(read, write)
            logger.info("✅ ClientSession created")

            async with session:
                # Initialize the session with timeout
                logger.info("⏳ Calling session.initialize()...")
                logger.info(f"   Session object: {type(session)}")
                logger.info(f"   Read stream: {type(read)}")
                logger.info(f"   Write stream: {type(write)}")

                try:
                    # Add more granular timeout and logging
                    logger.info("   Starting initialize with 10s timeout...")
                    init_result = await asyncio.wait_for(session.initialize(), timeout=10.0)
                    logger.info(f"✅ MCP session initialized successfully: {init_result}")
                except asyncio.TimeoutError:
                    logger.error("❌ MCP session initialization timed out after 10 seconds")
                    logger.error("   This usually means the MCP server is not responding to initialize request")
                    raise ValueError("MCP session initialization timed out - server not responding")
                except Exception as init_error:
                    logger.error(f"❌ MCP session initialization failed with error: {init_error}")
                    logger.error(f"   Error type: {type(init_error).__name__}")
                    raise

                # List available tools (for debugging)
                tools_response = await session.list_tools()
                tools = tools_response.tools
                logger.debug(f"Available MCP tools: {[t.name for t in tools]}")

                # Step 1: Fetch Zendesk tickets
                logger.info("📥 Calling MCP tool: fetch_zendesk_tickets...")
                fetch_args = {
                    "status": "all",
                    "priority": "all",
                    "days": 30,
                    "limit": 100
                }

                fetch_result = await session.call_tool("fetch_zendesk_tickets", arguments=fetch_args)

                # Extract text from TextContent
                from mcp.types import TextContent as MCPTextContent

                if not fetch_result or not fetch_result.content:
                    raise ValueError("Empty response from MCP server for fetch_zendesk_tickets")

                fetch_text = None
                for content in fetch_result.content:
                    if isinstance(content, MCPTextContent):
                        fetch_text = content.text
                        break

                if not fetch_text:
                    logger.error(f"No text content in MCP response. Content types: {[type(c).__name__ for c in fetch_result.content]}")
                    raise ValueError("No text content in MCP response")

                fetch_data = json.loads(fetch_text)

                if "error" in fetch_data:
                    logger.error(f"❌ Fetch failed: {fetch_data['error']}")
                    return {
                        "success": False,
                        "reason": "fetch_error",
                        "error": fetch_data["error"]
                    }

                fetched_count = fetch_data.get("fetched_count", 0)
                logger.info(f"✅ Fetched {fetched_count} tickets via MCP")

                if fetched_count == 0:
                    logger.info("ℹ️  No tickets to sync")
                    return {
                        "success": True,
                        "fetched_count": 0,
                        "ingested_count": 0,
                        "skipped_count": 0,
                        "message": "No tickets found in the specified time range"
                    }

                # Step 2: Ingest with deduplication
                logger.info("💾 Calling MCP tool: ingest_feedback_to_store...")
                ingest_args = {
                    "feedback_items": fetch_data["feedback_items"],
                    "source": "zendesk"
                }

                ingest_result = await session.call_tool("ingest_feedback_to_store", arguments=ingest_args)

                # Extract text from TextContent
                from mcp.types import TextContent as MCPTextContent

                if not ingest_result or not ingest_result.content:
                    raise ValueError("Empty response from MCP server for ingest_feedback_to_store")

                ingest_text = None
                for content in ingest_result.content:
                    if isinstance(content, MCPTextContent):
                        ingest_text = content.text
                        break

                if not ingest_text:
                    logger.error(f"No text content in MCP response. Content types: {[type(c).__name__ for c in ingest_result.content]}")
                    raise ValueError("No text content in MCP response")

                ingest_data = json.loads(ingest_text)

                if not ingest_data.get("success"):
                    logger.error(f"❌ Ingest failed: {ingest_data.get('error')}")
                    return {
                        "success": False,
                        "reason": "ingest_error",
                        "error": ingest_data.get("error")
                    }

                ingested = ingest_data.get("ingested_count", 0)
                skipped = ingest_data.get("skipped_count", 0)

                logger.info(f"✅ Sync complete via MCP: {ingested} new, {skipped} duplicates skipped")

                return {
                    "success": True,
                    "fetched_count": fetched_count,
                    "ingested_count": ingested,
                    "skipped_count": skipped,
                    "message": f"Successfully synced {ingested} new tickets from Zendesk via MCP (SSE)"
                }

    except Exception as e:
        logger.error(f"❌ MCP SSE sync error: {e}", exc_info=True)
        return {
            "success": False,
            "reason": "mcp_error",
            "error": str(e)
        }


async def sync_zendesk_data_direct() -> Dict[str, Any]:
    """
    Direct sync workflow - used when MCP server is not running.
    Calls MCP functions directly (fallback mode).
    """
    logger.info("🔄 Starting autonomous data sync (direct mode)...")

    # Check credentials
    zendesk_subdomain = os.environ.get("ZENDESK_SUBDOMAIN")
    zendesk_token = os.environ.get("ZENDESK_API_TOKEN")
    zendesk_email = os.environ.get("ZENDESK_EMAIL")

    if not all([zendesk_subdomain, zendesk_token, zendesk_email]):
        logger.info("ℹ️  Zendesk credentials not configured - skipping sync")
        return {
            "success": False,
            "reason": "credentials_missing",
            "message": "Set ZENDESK_SUBDOMAIN, ZENDESK_API_TOKEN, ZENDESK_EMAIL to enable Zendesk sync"
        }

    try:
        # Import MCP functions
        from .mcp_server import fetch_zendesk_tickets, ingest_feedback_to_store

        # Step 1: Fetch tickets
        logger.info("📥 Fetching Zendesk tickets from last 30 days...")
        fetch_args = {
            "status": "all",
            "priority": "all",
            "days": 30,
            "limit": 100
        }

        fetch_result = await fetch_zendesk_tickets(fetch_args)
        fetch_data = json.loads(fetch_result[0].text)

        if "error" in fetch_data:
            logger.error(f"❌ Fetch failed: {fetch_data['error']}")
            return {
                "success": False,
                "reason": "fetch_error",
                "error": fetch_data["error"]
            }

        fetched_count = fetch_data.get("fetched_count", 0)
        logger.info(f"✅ Fetched {fetched_count} tickets")

        if fetched_count == 0:
            logger.info("ℹ️  No tickets to sync")
            return {
                "success": True,
                "fetched_count": 0,
                "ingested_count": 0,
                "skipped_count": 0,
                "message": "No tickets found in the specified time range"
            }

        # Step 2: Ingest with deduplication
        logger.info("💾 Ingesting tickets into data store...")
        ingest_args = {
            "feedback_items": fetch_data["feedback_items"],
            "source": "zendesk"
        }

        ingest_result = await ingest_feedback_to_store(ingest_args)
        ingest_data = json.loads(ingest_result[0].text)

        if not ingest_data.get("success"):
            logger.error(f"❌ Ingest failed: {ingest_data.get('error')}")
            return {
                "success": False,
                "reason": "ingest_error",
                "error": ingest_data.get("error")
            }

        ingested = ingest_data.get("ingested_count", 0)
        skipped = ingest_data.get("skipped_count", 0)

        logger.info(f"✅ Sync complete: {ingested} new, {skipped} duplicates skipped")

        return {
            "success": True,
            "fetched_count": fetched_count,
            "ingested_count": ingested,
            "skipped_count": skipped,
            "message": f"Successfully synced {ingested} new tickets from Zendesk"
        }

    except Exception as e:
        logger.error(f"❌ Sync error: {e}", exc_info=True)
        return {
            "success": False,
            "reason": "exception",
            "error": str(e)
        }


async def sync_zendesk_data() -> Dict[str, Any]:
    """
    Autonomous sync workflow - fetch and ingest Zendesk tickets.

    Attempts to use MCP protocol via SSE/HTTP. If MCP server is not available,
    falls back to direct function calls.

    Returns:
        Sync statistics and status
    """
    # Check if MCP server is available
    mcp_url = os.environ.get("FEEDBACKFORGE_MCP_URL", "http://127.0.0.1:8085")
    use_mcp = os.environ.get("FEEDBACKFORGE_USE_MCP", "true").lower() == "true"

    if use_mcp:
        try:
            import httpx
            # Check if MCP server is running
            async with httpx.AsyncClient(timeout=5.0) as client:
                health_response = await client.get(f"{mcp_url}/health")
                if health_response.status_code == 200:
                    logger.info(f"✅ MCP server detected at {mcp_url}, attempting SSE connection...")
                    try:
                        return await sync_zendesk_data_via_mcp_sse(mcp_url)
                    except Exception as mcp_error:
                        logger.error(f"❌ MCP SSE connection failed: {mcp_error}")
                        logger.warning("⚠️  Falling back to direct mode due to MCP connection failure")
                        # Fallback to direct mode
                        return await sync_zendesk_data_direct()
        except Exception as e:
            logger.warning(f"⚠️  MCP server not available: {e}, falling back to direct calls")

    # Fallback to direct function calls
    logger.info("ℹ️  Using direct function calls (no MCP)")
    return await sync_zendesk_data_direct()


async def sync_zendesk_via_mcp(
    days: int = 30,
    status: str = "all",
    priority: str = "all",
    limit: int = 100
) -> Dict[str, Any]:
    """
    Tool: Sync Zendesk tickets via MCP server.

    Args:
        days: Number of days to look back for tickets (default: 30)
        status: Ticket status filter (new, open, pending, solved, all)
        priority: Priority filter (low, normal, high, urgent, all)
        limit: Maximum tickets to fetch (default: 100)

    Returns:
        Sync statistics and status
    """
    logger.info(f"🔧 Tool called: sync_zendesk_via_mcp(days={days}, status={status}, priority={priority}, limit={limit})")

    # Call the async sync directly (we're already in an event loop)
    mcp_url = os.environ.get("FEEDBACKFORGE_MCP_URL", "http://127.0.0.1:8085")
    result = await sync_zendesk_data_via_mcp_sse(mcp_url=mcp_url)

    logger.info(f"✅ Tool result: fetched={result.get('fetched_count', 0)}, ingested={result.get('ingested_count', 0)}")

    return result


async def check_sync_status() -> Dict[str, Any]:
    """
    Tool: Check data store sync status.

    Returns:
        Information about last sync and current data store state
    """
    logger.info("🔧 Tool called: check_sync_status()")

    from .data_store import feedback_store

    feedback_items = feedback_store.feedback

    # Find Zendesk items
    zendesk_items = [f for f in feedback_items if f.platform == "Zendesk"]

    # Get timestamps
    if zendesk_items:
        timestamps = [f.timestamp for f in zendesk_items if f.timestamp]
        latest_timestamp = max(timestamps) if timestamps else None
        oldest_timestamp = min(timestamps) if timestamps else None
    else:
        latest_timestamp = None
        oldest_timestamp = None

    result = {
        "total_feedback_items": len(feedback_items),
        "zendesk_items": len(zendesk_items),
        "latest_zendesk_timestamp": latest_timestamp.isoformat() if latest_timestamp else None,
        "oldest_zendesk_timestamp": oldest_timestamp.isoformat() if oldest_timestamp else None,
        "has_data": len(feedback_items) > 0,
        "needs_initial_sync": len(zendesk_items) == 0
    }

    logger.info(f"✅ Tool result: {result['zendesk_items']} Zendesk items, needs_initial_sync={result['needs_initial_sync']}")

    return result


async def create_sync_agent() -> ChatAgent:
    """
    Create the autonomous Data Sync Agent with LLM intelligence using AIProjectClient.

    Returns:
        Configured ChatAgent for data synchronization
    """
    logger.info("🤖 Creating Data Sync Agent with Azure AI Projects SDK...")

    # Check required environment variables
    endpoint = os.environ.get("AZURE_AI_PROJECT_ENDPOINT")
    deployment = os.environ.get("AZURE_OPENAI_RESPONSES_DEPLOYMENT_NAME")

    if not all([endpoint, deployment]):
        raise ValueError("Missing AZURE_AI_PROJECT_ENDPOINT or AZURE_OPENAI_RESPONSES_DEPLOYMENT_NAME")

    # Assert non-None for type checker (already validated above)
    assert endpoint is not None
    assert deployment is not None

    try:
        credential = DefaultAzureCredential()

        # Create AI Project client
        project = AIProjectClient(
            endpoint=endpoint,
            credential=credential
        )
        logger.info("✅ AIProjectClient created")

        # Create agent version
        agent_version = await project.agents.create_version(
            agent_name="DataSyncAgent",
            definition=PromptAgentDefinition(
                model=deployment,
                instructions=SYNC_AGENT_INSTRUCTIONS,
            ),
        )
        logger.info(f"✅ Agent created (id: {agent_version.id}, name: {agent_version.name}, version: {agent_version.version})")

        # Create adapter
        chat_client = AIProjectChatClient(project=project, agent_version=agent_version)

        # Create agent with sync tools
        agent = ChatAgent(
            chat_client=chat_client,
            instructions=SYNC_AGENT_INSTRUCTIONS,
            name="DataSyncAgent",
            agent_id=agent_version.id,
            description="Autonomous data synchronization agent with LLM intelligence",
            tools=[sync_zendesk_via_mcp, check_sync_status]
        )

        logger.info("✅ Data Sync Agent created with LLM")
        return agent

    except Exception as e:
        logger.error(f"❌ Failed to create sync agent: {e}", exc_info=True)
        raise


async def run_sync_with_agent() -> Dict[str, Any]:
    """
    Run data sync using the autonomous LLM-powered DataSyncAgent.

    The agent uses Azure OpenAI LLM to assess the situation and make intelligent decisions.

    Returns:
        Sync results and agent insights
    """
    logger.info("🚀 Running autonomous data sync with LLM-powered DataSyncAgent...")

    try:
        # Create the DataSyncAgent using async factory (wraps ChatAgent + LLM)
        sync_agent = await DataSyncAgent.create()

        logger.info(f"🧠 LLM Backend: Azure OpenAI at {sync_agent.endpoint}")
        logger.info(f"🤖 Model: {sync_agent.deployment}")
        logger.info(f"🔧 Agent Tools: sync_zendesk_via_mcp, check_sync_status")

        # Run autonomous sync - LLM will make intelligent decisions
        result = await sync_agent.run_autonomous_sync()

        logger.info("✅ LLM-powered autonomous sync complete")
        logger.info(f"📊 Agent response: {str(result.get('agent_response', ''))[:200]}...")

        return result

    except Exception as e:
        logger.error(f"❌ Agent sync error: {e}", exc_info=True)
        return {
            "success": False,
            "reason": "agent_error",
            "error": str(e)
        }


async def run_sync_before_dashboard() -> Dict[str, Any]:
    """
    Run the data sync workflow before starting the dashboard.
    This is called automatically during dashboard initialization.

    Uses the autonomous LLM agent for intelligent sync decisions.

    Returns:
        Dict with sync status and statistics
    """
    logger.info("🚀 Running pre-dashboard data sync with LLM agent...")

    # Check if we should use the LLM agent
    use_agent = os.environ.get("FEEDBACKFORGE_USE_SYNC_AGENT", "true").lower() == "true"

    if use_agent:
        try:
            return await run_sync_with_agent()
        except Exception as e:
            logger.warning(f"⚠️  Agent mode failed: {e}, falling back to direct sync")

    # Fallback to direct sync without agent
    logger.info("ℹ️  Using direct sync (no LLM agent)")
    result = await sync_zendesk_data()

    if result.get("success"):
        logger.info(f"✅ Data sync complete: {result.get('message')}")
    else:
        logger.warning(f"⚠️  Data sync incomplete: {result.get('reason', 'unknown')}")

    return result
