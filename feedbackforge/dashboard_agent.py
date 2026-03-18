"""
FeedbackForge Chat Agent
========================

ChatAgent creation for the executive dashboard assistant.
"""

import asyncio
import os

from agent_framework import ChatAgent
from azure.identity.aio import DefaultAzureCredential
from agent_framework.azure import AzureAIAgentClient
from .data_store import feedback_store
from agent_framework.microsoft import PurviewPolicyMiddleware, PurviewSettings
from azure.identity import InteractiveBrowserCredential

from .chat_tools import (
    get_weekly_summary,
    get_issue_details,
    get_competitor_insights,
    get_customer_context,
    check_for_anomalies,
    set_alert,
    generate_action_items,
    escalate_to_team,
)

AGENT_INSTRUCTIONS = """You are FeedbackForge, an Executive Dashboard Assistant for analyzing customer feedback.

Capabilities:
- Weekly summaries with sentiment distribution and top issues
- Deep-dive into specific issues with trends and recommendations
- Competitive intelligence and churn risk analysis
- Customer context lookup
- Anomaly detection for emerging issues
- Action item generation and team escalation

Communication style:
- Be concise and data-driven
- Use clear formatting with bullet points
- Highlight priorities (P0=Critical, P1=High, P2=Medium)
- Always offer next steps or deeper analysis
- Proactively flag urgent issues"""

TOOLS = [
    get_weekly_summary,
    get_issue_details,
    get_competitor_insights,
    get_customer_context,
    check_for_anomalies,
    set_alert,
    generate_action_items,
    escalate_to_team,
]


def validate_tools():
    """Validate that all tools are properly registered and data store is accessible."""
    import logging
    logger = logging.getLogger(__name__)

    logger.info("🔍 Validating data store and tools...")

    # Check data store
    try:
        feedback_count = len(feedback_store.feedback)
        logger.info(f"   ✅ Data store initialized: {feedback_count} feedback items")
    except Exception as e:
        logger.error(f"   ❌ Data store not initialized: {e}", exc_info=True)
        raise

    # Verify tools are callable
    try:
        logger.info(f"   ✅ Tools registered: {len(TOOLS)}")
        for tool in TOOLS:
            tool_name = getattr(tool, '__name__', str(tool))
            logger.debug(f"      - {tool_name}")
    except Exception as e:
        logger.error(f"   ❌ Tools validation failed: {e}", exc_info=True)
        raise

    logger.info("✅ Validation complete")


def create_dashboard_agent() -> ChatAgent:
    """Create the Executive Dashboard Assistant using Azure AI Foundry.

    Uses environment variables for configuration:
        - AZURE_AI_PROJECT_ENDPOINT: Azure AI Foundry project endpoint
        - AZURE_OPENAI_RESPONSES_DEPLOYMENT_NAME: Model deployment name
    """
    import logging
    logger = logging.getLogger(__name__)

    # Check required environment variables
    required_env_vars = {
        "AZURE_AI_PROJECT_ENDPOINT": os.environ.get("AZURE_AI_PROJECT_ENDPOINT"),
        "AZURE_OPENAI_RESPONSES_DEPLOYMENT_NAME": os.environ.get("AZURE_OPENAI_RESPONSES_DEPLOYMENT_NAME"),
    }

    missing_vars = [k for k, v in required_env_vars.items() if not v]
    if missing_vars:
        error_msg = f"Missing required environment variables: {', '.join(missing_vars)}"
        logger.error(f"❌ {error_msg}")
        raise ValueError(error_msg)

    try:
        #Create the agent
        logger.info("🔧 Creating dashboard agent...")
        logger.info(f"   Project endpoint: {required_env_vars['AZURE_AI_PROJECT_ENDPOINT']}")
        logger.info(f"   Model deployment: {required_env_vars['AZURE_OPENAI_RESPONSES_DEPLOYMENT_NAME']}")

        purview_middleware = PurviewPolicyMiddleware(
            credential=InteractiveBrowserCredential(
                client_id="required_env_vars['AZURE_CLIENT_ID']",
            ),
            settings=PurviewSettings(app_name="FeedbackForge")
        )
        
        credential = DefaultAzureCredential()
        chat_client = AzureAIAgentClient(
            project_endpoint=required_env_vars["AZURE_AI_PROJECT_ENDPOINT"],
            model_deployment_name=required_env_vars["AZURE_OPENAI_RESPONSES_DEPLOYMENT_NAME"],
            credential=credential,
            agent_name="FeedbackForge",
            agent_description="Executive Dashboard Assistant for customer feedback analysis",
            middleware=[purview_middleware]
        )
        logger.info("✅ Chat client created successfully")
    except Exception as e:
        logger.error(f"❌ Failed to create chat client: {e}", exc_info=True)
        raise
    
    # agent = await check_agent("FeedbackForgev2", chat_client)

    # if agent is not None:
    #     print(f"✅ Found existing agent: {agent.name} (ID: {agent.id})")
    #     return agent
    # else:
    #     print("⚠️ Agent not found. Creating new agent...")

    try:
        # Run autonomous data sync agent before creating dashboard
        from .data_sync_agent import run_sync_before_dashboard

        sync_result = asyncio.run(run_sync_before_dashboard())
        if sync_result.get("success"):
            ingested = sync_result.get("ingested_count", 0)
            skipped = sync_result.get("skipped_count", 0)
            logger.info(f"✅ Data sync complete: {ingested} new tickets, {skipped} duplicates")
        else:
            logger.warning(f"⚠️  Data sync incomplete: {sync_result.get('reason', 'unknown')}")

        # Validate tools before creating agent
        validate_tools()

        logger.info("🤖 Creating ChatAgent with tools...")
        logger.info(f"   Registering {len(TOOLS)} tools")
        for tool in TOOLS:
            tool_name = getattr(tool, '__name__', getattr(tool, 'name', str(tool)))
            logger.info(f"      - {tool_name}")

        agent = ChatAgent(
            chat_client=chat_client,
            instructions=AGENT_INSTRUCTIONS,
            name="FeedbackForge",
            agent_id="FeedbackForge:1",
            description="Executive Dashboard Assistant for customer feedback analysis",
            tools=TOOLS
        )
        logger.info(f"✅ ChatAgent created successfully: {agent.name}")

        # Wrap the agent's run method to catch errors
        original_run = agent.run

        async def wrapped_run(*args, **kwargs):
            try:
                logger.debug(f"🏃 Agent run called with args: {args[:50] if args else 'none'}...")
                result = await original_run(*args, **kwargs)
                logger.debug(f"✅ Agent run completed successfully")
                return result
            except Exception as e:
                logger.error(f"❌ Error in agent.run(): {type(e).__name__}: {e}", exc_info=True)
                raise

        agent.run = wrapped_run

        return agent
    except Exception as e:
        logger.error(f"❌ Failed to create ChatAgent: {e}", exc_info=True)
        raise

    #     agent = chat_client.agents_client.update_agent(
    #     assistant_id=found_agent.id,
    #     model=found_agent.model,
    #     instructions=found_agent.instructions,
    #     tools=TOOLS,
    # )
    #print(f"✅ Created new agent: {agent.name}")

# async def check_agent(agent_name: str, chat_client: AzureAIAgentClient) -> Optional[Agent]:
#     found_agent = None
#     all_agents_list = chat_client.agents_client.list_agents()
#     async for a in all_agents_list:
#         if a.name == agent_name:
#             found_agent = a
#             break
#     return found_agent