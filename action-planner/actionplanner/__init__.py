"""
Action Planner Agent
====================

Autonomous agent that converts feedback insights into trackable action items.

Features:
- A2A protocol for agent-to-agent communication
- Jira ticket creation
- Intelligent prioritization and assignment
- Effort estimation
"""

__version__ = "1.0.0"

from .jira_client import JiraClient
from .agent import ActionPlanningAgent, create_action_planning_agent

__all__ = ["JiraClient", "ActionPlanningAgent", "create_action_planning_agent"]
