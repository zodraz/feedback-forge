"""
FeedbackForge Chat Agent
========================

ChatAgent creation for the executive dashboard assistant.
"""

import os

from agent_framework import ChatAgent
from agent_framework_devui import register_cleanup
from agent_framework_azure_ai import AzureAIClient
# from agent_framework_azure_ai import AzureOpenAIClient
from azure.identity import AzureCliCredential
# Microsoft Agent Framework with native Azure OpenAI support  
from agent_framework.azure import AzureOpenAIChatClient
from azure.ai.projects.aio import AIProjectClient
from azure.identity.aio import DefaultAzureCredential

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




from agents import Agent, Runner, function_tool
import json
from typing import Annotated

from agent_framework import ai_function

from .data_store import feedback_store

@function_tool
def get_weekly_summary2() -> str:
    """Get weekly feedback summary with sentiment, top issues, and urgent items."""
    summary = feedback_store.get_weekly_summary()
    return json.dumps({
        "total_responses": summary["total_responses"],
        "sentiment": summary["sentiment"],
        "top_issues": [
            {"issue": i[0], "mentions": i[1], "priority": "P0" if i[1] > 40 else "P1" if i[1] > 25 else "P2"}
            for i in summary["top_issues"]
        ],
        "urgent_items": summary["urgent_count"],
    }, indent=2)
    
TOOLS2 = [
    get_weekly_summary2
]


def create_dashboard_agent() -> ChatAgent:
    """Create the Executive Dashboard Assistant using Azure AI Foundry.

    Uses environment variables for configuration:
        - AZURE_AI_PROJECT_ENDPOINT: Azure AI Foundry project endpoint
        - AZURE_AI_MODEL_DEPLOYMENT_NAME: Model deployment name
    """
    # Create credential and project client
    credential = DefaultAzureCredential()
    project_client = AIProjectClient(
        endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
        credential=credential,
    )
    

    from openai import AzureOpenAI
    
    apim_resource_gateway_url="https://apim-4v5u3tvfuhuo4.azure-api.net/"
    inference_api_path="inference"
    api_key="0d5695acb9a14a0da0064a604181e667"
    inference_api_version="2025-11-13"

    # may change in the future
    # https://learn.microsoft.com/en-us/azure/ai-services/openai/reference#rest-api-versioning
    api_version = "2023-07-01-preview"

    # gets the API Key from environment variable AZURE_OPENAI_API_KEY
    # client = AzureOpenAI(
    #     api_version=api_version,
    #     # https://learn.microsoft.com/en-us/azure/cognitive-services/openai/how-to/create-resource?pivots=web-portal#create-a-resource
    #     azure_endpoint="https://example-endpoint.openai.azure.com",
    # )

    credential = AzureCliCredential()
    chat_client = AzureOpenAIChatClient(credential=credential,
            endpoint=os.environ["AZURE_API_GATEWAY_ENDPOINT"],
            api_key=os.environ["AZURE_API_GATEWAY_KEY"],
            deployment_name=os.environ["AZURE_AI_MODEL_DEPLOYMENT_NAME"])
            # api_version=os.environ["AZURE_AI_MODEL_DEPLOYMENT_VERSION"])
    
    chat_client = AzureOpenAIChatClient(credential=credential,
            endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
            api_key=os.environ["AZURE_OPENAI_KEY"],
            deployment_name=os.environ["AZURE_AI_MODEL_DEPLOYMENT_NAME"])
            # api_version=os.environ["AZURE_AI_MODEL_DEPLOYMENT_VERSION"])
    
    # chat_client = AzureOpenAIChatClient(credential=credential,
    #         endpoint=f"{apim_resource_gateway_url}/{inference_api_path}",
    #         api_key=api_key,
    #         # api_version=inference_api_version
    #         deployment_name=os.environ["AZURE_AI_MODEL_DEPLOYMENT_NAME"])
    #         # api_version=os.environ["AZURE_AI_MODEL_DEPLOYMENT_VERSION"])
    
    # chat_client = AzureOpenAIChatClient(credential=credential)
    
    
   

    # # client2 = AzureOpenAI(
    # #     azure_endpoint=f"{apim_resource_gateway_url}/{inference_api_path}",
    # #     api_key=api_key,
    # #     api_version=inference_api_version
    # # )
    # # response = client2.chat.completions.create(model="gpt-5.1-chat", messages=[
    # #                 {"role": "system", "content": "You are a sarcastic, unhelpful assistant."},
    # #                 {"role": "user", "content": "Can you tell me the time, please?"}
    # # ])
    # # print("💬 ",response.choices[0].message.content)
    
    
    # # from openai import AzureOpenAI
    # # from agents import Agent, Runner, set_default_openai_client, set_default_openai_api, set_tracing_disabled
    # # # import nest_asyncio
    # # # nest_asyncio.apply()

    # # client = AzureOpenAI(azure_endpoint=f"{apim_resource_gateway_url}/{inference_api_path}",
    # #                             api_key=api_key,
    # #                             api_version=inference_api_version)
    # # # set_default_openai_client(client)
    # # # set_default_openai_api("chat_completions")
    # # agent = Agent(name="Sarcastic Assistant", 
    # #               instructions=AGENT_INSTRUCTIONS, 
    # #               model="gpt-5.1-chat",
    # #               tools=[get_weekly_summary2])

    # # # result = Runner.run_sync(agent, "Can you tell me the time, please?")
    # # # print("💬", result.final_output)
    
    
    
    #Create the agent
    agent = chat_client.create_agent(
             name="FeedbackForge",
             description="Executive Dashboard Assistant for customer feedback analysis",
             instructions=AGENT_INSTRUCTIONS,
             tools=TOOLS) 

    return agent