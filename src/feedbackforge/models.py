"""
FeedbackForge Data Models
=========================

Data classes for survey responses, analysis state, and feedback items.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class SurveyResponse:
    """Individual survey response for workflow processing."""
    id: str
    text: str
    rating: Optional[int]
    timestamp: str
    customer_segment: Optional[str] = None
    product_version: Optional[str] = None
    customer_id: Optional[str] = None
    customer_name: Optional[str] = None
    platform: Optional[str] = None


@dataclass
class AnalysisState:
    """State object passed through the workflow pipeline."""
    surveys: List[SurveyResponse]

    # Stage 1: Orchestrator decides to proceed
    orchestrator_initial: Optional[Dict[str, Any]] = None

    # Stage 2: Preprocessing
    preprocessing: Optional[Dict[str, Any]] = None

    # Stage 3: Parallel Analysis (after preprocessing)
    sentiment: Optional[Dict[str, Any]] = None
    topics: Optional[Dict[str, Any]] = None
    anomalies: Optional[Dict[str, Any]] = None
    competitive: Optional[Dict[str, Any]] = None

    # Stage 4: Insight Mining (after parallel analysis)
    insights: Optional[Dict[str, Any]] = None

    # Stage 5: Parallel Action Generation
    priorities: Optional[Dict[str, Any]] = None
    actions: Optional[Dict[str, Any]] = None

    # Stage 6: Final Report
    report: Optional[Dict[str, Any]] = None

    # Stage 7: Final Orchestrator Review
    orchestrator_final: Optional[Dict[str, Any]] = None

    # Tracking which parallel tasks are complete
    parallel_stage1_complete: List[str] = field(default_factory=lambda: [])
    parallel_stage2_complete: List[str] = field(default_factory=lambda: [])


@dataclass
class FeedbackItem:
    """Extended feedback item for data store and chat queries."""
    id: str
    text: str
    sentiment: str  # positive, negative, neutral
    sentiment_score: float  # -1.0 to 1.0
    topics: List[str]
    customer_segment: str  # Enterprise, SMB, Individual
    customer_id: str
    customer_name: str
    rating: int  # 1-5
    timestamp: datetime
    product_version: str
    platform: Optional[str] = None
    is_urgent: bool = False
    competitor_mentions: List[str] = field(default_factory=lambda: [])
