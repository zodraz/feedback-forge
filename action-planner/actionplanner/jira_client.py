"""
Jira Integration Client
"""

import logging
import os
from datetime import datetime
from typing import Optional

from jira import JIRA
from jira.exceptions import JIRAError

from .models import IssueAnalysis, CreatedTicket, Priority, TicketingSystem

logger = logging.getLogger(__name__)


class JiraClient:
    """Client for creating and managing Jira tickets."""

    def __init__(self):
        """Initialize Jira client from environment variables."""
        self.jira_url = os.getenv("JIRA_URL")
        self.jira_email = os.getenv("JIRA_EMAIL")
        self.jira_token = os.getenv("JIRA_API_TOKEN")
        self.default_project = os.getenv("JIRA_PROJECT_KEY", "PROJ")
        self.default_assignee = os.getenv("JIRA_DEFAULT_ASSIGNEE", "unassigned")

        if not all([self.jira_url, self.jira_email, self.jira_token]):
            logger.warning("Jira credentials not configured")
            self.client = None
            return

        try:
            self.client = JIRA(
                server=self.jira_url,
                basic_auth=(self.jira_email, self.jira_token)
            )
            logger.info(f"Jira client initialized for {self.jira_url}")
        except JIRAError as e:
            logger.error(f"Failed to initialize Jira client: {e}")
            self.client = None

    def is_available(self) -> bool:
        """Check if Jira integration is available."""
        return self.client is not None

    async def create_ticket(
        self,
        analysis: IssueAnalysis,
        project_key: Optional[str] = None
    ) -> CreatedTicket:
        """
        Create a Jira ticket from issue analysis.

        Args:
            analysis: Issue analysis with details
            project_key: Jira project key (default from env)

        Returns:
            Created ticket information

        Raises:
            ValueError: If Jira is not configured
            JIRAError: If ticket creation fails
        """
        if not self.client:
            raise ValueError("Jira client not configured")

        project = project_key or self.default_project

        # Map priority
        priority_map = {
            Priority.LOW: "Low",
            Priority.MEDIUM: "Medium",
            Priority.HIGH: "High",
            Priority.CRITICAL: "Highest"
        }
        jira_priority = priority_map.get(analysis.priority, "Medium")

        # Map category to issue type
        issuetype_map = {
            "bug": "Bug",
            "feature": "Story",
            "improvement": "Improvement",
            "performance": "Task",
            "security": "Bug",
            "documentation": "Task"
        }
        issue_type = issuetype_map.get(analysis.category.value, "Task")

        # Build description with metadata
        description = f"""{analysis.description}

---
*Automated Issue from Action Planner*

*Affected Customers:* {analysis.affected_customers}
*Platform:* {analysis.platform.value}
*Estimated Effort:* {analysis.estimated_effort.value}
*Category:* {analysis.category.value}

*Related Feedback IDs:* {', '.join(analysis.feedback_ids) if analysis.feedback_ids else 'None'}
"""

        # Create issue fields
        issue_fields = {
            "project": {"key": project},
            "summary": analysis.summary[:255],  # Jira limit
            "description": description,
            "issuetype": {"name": issue_type},
            "priority": {"name": jira_priority},
            "labels": analysis.tags + [
                "automated",
                "feedback",
                analysis.platform.value,
                analysis.category.value
            ]
        }

        # Add assignee if specified
        if analysis.suggested_team and analysis.suggested_team != "unassigned":
            issue_fields["assignee"] = {"name": analysis.suggested_team}

        try:
            logger.info(f"Creating Jira ticket in project {project}: {analysis.summary}")
            new_issue = self.client.create_issue(fields=issue_fields)

            ticket_url = f"{self.jira_url}/browse/{new_issue.key}"

            logger.info(f"Created Jira ticket: {new_issue.key} - {ticket_url}")

            return CreatedTicket(
                system=TicketingSystem.JIRA,
                ticket_id=new_issue.key,
                ticket_url=ticket_url,
                title=analysis.summary,
                priority=analysis.priority,
                created_at=datetime.now(),
                assignee=analysis.suggested_team,
                status="To Do"
            )

        except JIRAError as e:
            logger.error(f"Failed to create Jira ticket: {e}")
            raise

    async def get_ticket_status(self, ticket_id: str) -> dict:
        """Get current status of a Jira ticket."""
        if not self.client:
            raise ValueError("Jira client not configured")

        try:
            issue = self.client.issue(ticket_id)
            return {
                "id": issue.key,
                "status": issue.fields.status.name,
                "assignee": issue.fields.assignee.displayName if issue.fields.assignee else "Unassigned",
                "updated": issue.fields.updated
            }
        except JIRAError as e:
            logger.error(f"Failed to get ticket status: {e}")
            raise
