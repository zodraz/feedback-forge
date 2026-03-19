"""
Data Models for Action Planner
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class Priority(str, Enum):
    """Issue priority levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class IssueCategory(str, Enum):
    """Issue categories."""
    BUG = "bug"
    FEATURE = "feature"
    IMPROVEMENT = "improvement"
    PERFORMANCE = "performance"
    SECURITY = "security"
    DOCUMENTATION = "documentation"


class Platform(str, Enum):
    """Platform types."""
    IOS = "ios"
    ANDROID = "android"
    WEB = "web"
    API = "api"
    DESKTOP = "desktop"
    UNKNOWN = "unknown"


class EffortSize(str, Enum):
    """T-shirt sizing for effort estimation."""
    XS = "extra_small"
    S = "small"
    M = "medium"
    L = "large"
    XL = "extra_large"


class TicketingSystem(str, Enum):
    """Supported ticketing systems."""
    JIRA = "jira"


class IssueAnalysis(BaseModel):
    """Analysis of a feedback issue."""
    summary: str = Field(description="Brief issue summary (max 100 chars)")
    description: str = Field(description="Detailed issue description")
    category: IssueCategory = Field(description="Issue category")
    priority: Priority = Field(description="Priority level")
    platform: Platform = Field(description="Affected platform")
    affected_customers: int = Field(description="Number of affected customers", ge=0)
    estimated_effort: EffortSize = Field(description="Effort estimation")
    suggested_team: Optional[str] = Field(None, description="Suggested team owner")
    tags: List[str] = Field(default_factory=list, description="Issue tags/labels")
    feedback_ids: List[str] = Field(default_factory=list, description="Related feedback IDs")


class TicketCreationRequest(BaseModel):
    """Request to create a ticket."""
    system: TicketingSystem = Field(description="Target ticketing system")
    analysis: IssueAnalysis = Field(description="Issue analysis")
    project_key: Optional[str] = Field(None, description="Project identifier (Jira key, ADO project, etc)")


class CreatedTicket(BaseModel):
    """Information about a created ticket."""
    system: TicketingSystem
    ticket_id: str = Field(description="Ticket ID (e.g., FEED-123, #456)")
    ticket_url: str = Field(description="Direct URL to the ticket")
    title: str
    priority: Priority
    created_at: datetime
    assignee: Optional[str] = None
    status: str = "open"


class ActionPlanResult(BaseModel):
    """Result of creating an action plan."""
    success: bool
    tickets: List[CreatedTicket] = Field(default_factory=list)
    summary: str = Field(description="Summary of actions taken")
    errors: List[str] = Field(default_factory=list, description="Any errors encountered")
