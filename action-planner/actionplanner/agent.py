"""
Action Planning Agent

LLM-powered autonomous agent that converts feedback insights into trackable action items.
"""

import json
import logging
import os
from typing import Any, Dict, Optional

from agent_framework import ChatAgent
from agent_framework.azure import AzureAIAgentClient
from azure.identity.aio import DefaultAzureCredential

from .jira_client import JiraClient
from .models import (
    IssueAnalysis,
    IssueCategory,
    Priority,
    Platform,
    EffortSize,
    TicketingSystem,
    CreatedTicket,
    ActionPlanResult
)

logger = logging.getLogger(__name__)


# Agent Instructions
AGENT_INSTRUCTIONS = """You are the Action Planning Agent for FeedbackForge.

Your role is to convert customer feedback insights into concrete, trackable action items in Jira.

**Core Responsibilities:**

1. **Analyze Issues**
   - Extract key details from feedback summaries
   - Assess severity based on affected customer count and issue type
   - Categorize issues (bug, feature, improvement, performance, security)
   - Identify affected platforms (iOS, Android, Web, API)

2. **Prioritize Intelligently**
   - CRITICAL: >100 affected customers OR security issues OR data loss
   - HIGH: 50-100 affected customers OR crashes OR payment issues
   - MEDIUM: 10-50 affected customers OR usability problems
   - LOW: <10 affected customers OR cosmetic issues

3. **Estimate Effort**
   - XS: Simple fix, <2 hours (typo, config change)
   - S: Small fix, 2-8 hours (minor bug, UI tweak)
   - M: Medium task, 1-3 days (feature enhancement, moderate bug)
   - L: Large task, 1-2 weeks (new feature, major refactor)
   - XL: Extra large, >2 weeks (platform redesign, major system change)

4. **Assign Ownership**
   - Backend team: API, database, server issues
   - Mobile team: iOS, Android crashes/bugs
   - Frontend team: Web UI, UX issues
   - DevOps team: Infrastructure, deployment, performance
   - Security team: Security vulnerabilities, data breaches

5. **Create Tickets**
   - Use clear, actionable titles (max 100 chars)
   - Include affected customer count in description
   - Add relevant tags/labels for filtering
   - Link to original feedback IDs

**Available Tools:**
- analyze_issue: Analyze feedback and create structured issue
- create_jira_ticket: Create ticket in Jira
- get_available_systems: Check which ticketing systems are configured

**Decision Guidelines:**
- Always analyze the issue first before creating tickets
- Create tickets in the primary system only (don't duplicate)
- If no system is configured, return analysis without creating tickets
- For critical issues, recommend immediate escalation
- Group related feedback into single tickets to avoid duplication

**Communication Style:**
- Be concise and action-oriented
- Use clear, professional language
- Focus on impact and urgency
- Provide ticket links when created
"""


class ActionPlanningAgent:
    """
    LLM-powered agent for creating action plans from feedback.
    """

    def __init__(self):
        """Initialize the Action Planning Agent."""
        logger.info("Initializing Action Planning Agent...")

        # Check required environment variables
        self.endpoint = os.environ.get("AZURE_AI_PROJECT_ENDPOINT")
        self.deployment = os.environ.get("AZURE_OPENAI_RESPONSES_DEPLOYMENT_NAME")

        if not all([self.endpoint, self.deployment]):
            raise ValueError("Missing AZURE_AI_PROJECT_ENDPOINT or AZURE_OPENAI_RESPONSES_DEPLOYMENT_NAME")

        # Initialize ticketing system clients
        self.jira_client = JiraClient()

        # Create the underlying ChatAgent
        self._chat_agent: ChatAgent = self._create_chat_agent()

        logger.info("Action Planning Agent initialized")
        logger.info(f"Available systems: {self.get_available_systems()}")

    def _create_chat_agent(self) -> ChatAgent:
        """Create the underlying ChatAgent with LLM."""
        logger.info("Creating ChatAgent with Azure OpenAI...")

        credential = DefaultAzureCredential()

        chat_client = AzureAIAgentClient(
            project_endpoint=self.endpoint,
            model_deployment_name=self.deployment,
            credential=credential,
            agent_name="ActionPlanningAgent",
            agent_description="Converts feedback insights into trackable action items"
        )

        # Create agent with action planning tools
        agent = ChatAgent(
            chat_client=chat_client,
            instructions=AGENT_INSTRUCTIONS,
            name="ActionPlanningAgent",
            agent_id="ActionPlanningAgent:1",
            description="Autonomous action planning agent with multi-platform ticket creation",
            tools=[
                self.analyze_issue,
                self.create_jira_ticket,
                self.get_available_systems
            ]
        )

        logger.info(f"ChatAgent created: {agent.name}")
        return agent

    def get_available_systems(self) -> Dict[str, bool]:
        """
        Tool: Check which ticketing systems are configured and available.

        Returns:
            Dictionary mapping system names to availability status
        """
        return {
            "jira": self.jira_client.is_available()
        }

    async def analyze_issue(
        self,
        summary: str,
        description: str,
        affected_customers: int,
        feedback_ids: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Tool: Analyze a feedback issue and create structured issue analysis.

        This is typically the first tool called. It extracts key details and makes
        decisions about priority, category, platform, and effort.

        Args:
            summary: Brief issue summary (from dashboard agent)
            description: Detailed description of the issue
            affected_customers: Number of affected customers
            feedback_ids: Comma-separated feedback IDs (optional)

        Returns:
            Structured issue analysis as dictionary
        """
        logger.info(f"Analyzing issue: {summary} ({affected_customers} affected)")

        # Parse feedback IDs
        feedback_id_list = []
        if feedback_ids:
            feedback_id_list = [fid.strip() for fid in feedback_ids.split(",")]

        # Extract platform hints from description
        description_lower = description.lower()
        platform = Platform.UNKNOWN
        if "ios" in description_lower or "iphone" in description_lower:
            platform = Platform.IOS
        elif "android" in description_lower:
            platform = Platform.ANDROID
        elif "web" in description_lower or "browser" in description_lower:
            platform = Platform.WEB
        elif "api" in description_lower:
            platform = Platform.API

        # Determine category
        category = IssueCategory.BUG
        if "crash" in description_lower or "error" in description_lower:
            category = IssueCategory.BUG
        elif "slow" in description_lower or "performance" in description_lower:
            category = IssueCategory.PERFORMANCE
        elif "feature" in description_lower or "want" in description_lower:
            category = IssueCategory.FEATURE
        elif "improve" in description_lower or "better" in description_lower:
            category = IssueCategory.IMPROVEMENT

        # Determine priority based on affected customers
        if affected_customers > 100 or "security" in description_lower or "data loss" in description_lower:
            priority = Priority.CRITICAL
        elif affected_customers >= 50 or "crash" in description_lower or "payment" in description_lower:
            priority = Priority.HIGH
        elif affected_customers >= 10:
            priority = Priority.MEDIUM
        else:
            priority = Priority.LOW

        # Estimate effort
        if "crash" in description_lower:
            effort = EffortSize.M
        elif "feature" in description_lower:
            effort = EffortSize.L
        elif "typo" in description_lower or "text" in description_lower:
            effort = EffortSize.XS
        else:
            effort = EffortSize.M

        # Suggest team
        suggested_team = "unassigned"
        if platform in [Platform.IOS, Platform.ANDROID]:
            suggested_team = "mobile-team"
        elif platform == Platform.WEB:
            suggested_team = "frontend-team"
        elif platform == Platform.API or "backend" in description_lower:
            suggested_team = "backend-team"

        # Generate tags
        tags = [platform.value, category.value, priority.value]
        if "crash" in description_lower:
            tags.append("crash")
        if "payment" in description_lower:
            tags.append("payment")

        analysis = IssueAnalysis(
            summary=summary,
            description=description,
            category=category,
            priority=priority,
            platform=platform,
            affected_customers=affected_customers,
            estimated_effort=effort,
            suggested_team=suggested_team,
            tags=tags,
            feedback_ids=feedback_id_list
        )

        logger.info(f"Issue analysis complete: {priority.value} priority, {effort.value} effort")

        return analysis.model_dump()

    async def create_jira_ticket(self, analysis_json: str) -> Dict[str, Any]:
        """
        Tool: Create a Jira ticket from issue analysis.

        Args:
            analysis_json: JSON string of IssueAnalysis

        Returns:
            Created ticket information
        """
        if not self.jira_client.is_available():
            return {"error": "Jira is not configured"}

        try:
            analysis = IssueAnalysis(**json.loads(analysis_json))
            ticket = await self.jira_client.create_ticket(analysis)
            logger.info(f"Jira ticket created: {ticket.ticket_id}")
            return ticket.model_dump(mode='json')  # Use JSON mode to serialize datetime
        except Exception as e:
            logger.error(f"Failed to create Jira ticket: {e}")
            return {"error": str(e)}

    async def run(self, prompt: str) -> str:
        """
        Run the agent with a user prompt.

        Args:
            prompt: User request (typically from dashboard agent via A2A)

        Returns:
            Agent response with action plan results
        """
        logger.info(f"Running Action Planning Agent with prompt: {prompt[:100]}...")

        try:
            result = await self._chat_agent.run(prompt)
            logger.info("Action Planning Agent completed")
            # Extract text content from AgentRunResponse
            return result.text
        except Exception as e:
            logger.error(f"Agent execution failed: {e}", exc_info=True)
            return f"Error: {str(e)}"


def create_action_planning_agent() -> ActionPlanningAgent:
    """
    Factory function to create the Action Planning Agent.

    Returns:
        Configured ActionPlanningAgent instance
    """
    return ActionPlanningAgent()
