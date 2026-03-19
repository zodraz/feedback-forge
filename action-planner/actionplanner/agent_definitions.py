# Copyright (c) Microsoft. All rights reserved.

"""Agent definitions and AgentCard factory for Action Planner A2A server.

Provides factory function to create the Action Planning Agent and its A2A AgentCard.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from a2a.types import AgentCapabilities, AgentCard, AgentSkill

if TYPE_CHECKING:
    from .agent import ActionPlanningAgent


# ---------------------------------------------------------------------------
# Agent card factory
# ---------------------------------------------------------------------------

_CAPABILITIES = AgentCapabilities(streaming=True, push_notifications=False)


def get_action_planner_card(url: str) -> AgentCard:
    """Return an A2A AgentCard for the Action Planning Agent.

    Args:
        url: Base URL where the agent is hosted (e.g., "http://localhost:8084/")

    Returns:
        AgentCard with metadata and capabilities
    """
    return AgentCard(
        name="ActionPlanningAgent",
        description="Converts customer feedback insights into trackable tickets in Jira",
        url=url,
        version="1.0.0",
        default_input_modes=["text"],
        default_output_modes=["text"],
        capabilities=_CAPABILITIES,
        skills=[
            AgentSkill(
                id="action_planner_ticket_creation",
                name="ActionPlanner",
                description=(
                    "Analyzes customer feedback issues and creates actionable tickets "
                    "with proper prioritization, categorization, and effort estimation. "
                    "Supports Jira."
                ),
                tags=["action-planning", "ticket-creation", "jira", "feedback", "agent-framework"],
                examples=[
                    "Create tickets for iOS crash issue affecting 45 users",
                    "Analyze payment failure feedback and create action plan",
                    "Generate tickets for login performance complaints",
                ],
            ),
        ],
    )
