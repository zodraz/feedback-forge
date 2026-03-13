"""
FeedbackForge Workflow
======================

Survey analysis workflow with parallel execution.
"""

import logging
import os
from typing import Any, Dict, List

from agent_framework import WorkflowBuilder, WorkflowOutputEvent
from azure.identity.aio import DefaultAzureCredential

from .executors import (
    InitialOrchestrator,
    DataPreprocessor,
    SentimentAnalyzer,
    TopicExtractor,
    AnomalyDetector,
    CompetitiveIntelligence,
    InsightMiner,
    PriorityRanker,
    ActionGenerator,
    ReportGenerator,
    FinalOrchestrator,
)
from .models import AnalysisState, SurveyResponse

logger = logging.getLogger(__name__)


class SurveyAnalysisWorkflow:
    """Main workflow with parallel execution."""

    def __init__(self):
        self.credential = DefaultAzureCredential()
        self.workflow = None
        self.executors = []  # Track executors for cleanup
        self._setup_workflow()

    def _setup_workflow(self):
        """Build the workflow DAG with parallel branches."""
        orchestrator_init = InitialOrchestrator(self.credential)
        preprocessor = DataPreprocessor(self.credential)
        sentiment = SentimentAnalyzer(self.credential)
        topics = TopicExtractor(self.credential)
        anomaly = AnomalyDetector(self.credential)
        competitive = CompetitiveIntelligence(self.credential)
        insights = InsightMiner(self.credential)
        priorities = PriorityRanker(self.credential)
        actions = ActionGenerator(self.credential)
        reporter = ReportGenerator(self.credential)
        orchestrator_final = FinalOrchestrator(self.credential)

        # Track all executors for cleanup
        self.executors = [
            orchestrator_init, preprocessor, sentiment, topics, anomaly,
            competitive, insights, priorities, actions, reporter, orchestrator_final
        ]

        builder = WorkflowBuilder()

        # Stage 1: Initial Orchestrator
        builder.set_start_executor(orchestrator_init)

        # Stage 2: Preprocessing
        builder.add_edge(orchestrator_init, preprocessor)

        # Stage 3: Fan-out to Parallel Analysis
        builder.add_fan_out_edges(preprocessor, [sentiment, topics, anomaly, competitive])

        # Stage 4: Fan-in to Insight Mining (aggregates all parallel results)
        builder.add_fan_in_edges([sentiment, topics, anomaly, competitive], insights)

        # Stage 5: Fan-out to Parallel Action Generation
        builder.add_fan_out_edges(insights, [priorities, actions])

        # Stage 6: Fan-in to Report Generation
        builder.add_fan_in_edges([priorities, actions], reporter)

        # Stage 7: Final Orchestrator
        builder.add_edge(reporter, orchestrator_final)

        self.workflow = builder.build()

    async def cleanup(self):
        """Close all HTTP sessions and cleanup resources."""
        try:
            # Close the credential's HTTP session
            if hasattr(self.credential, 'close'):
                await self.credential.close()
                logger.debug("✅ Credential sessions closed")

            # Close any client sessions in executors
            for executor in self.executors:
                if hasattr(executor, 'agent') and hasattr(executor.agent, 'chat_client'):
                    client = executor.agent.chat_client
                    if hasattr(client, 'close'):
                        await client.close()
                        logger.debug(f"✅ Closed session for {executor.id}")
        except Exception as e:
            logger.warning(f"⚠️ Error during cleanup: {e}")

    async def analyze(self, surveys: List[SurveyResponse]) -> Dict[str, Any]:
        """Run the complete analysis workflow."""
        logger.info(f"\n{'='*60}\n🚀 Starting Multi-Agent Analysis\n📊 Analyzing {len(surveys)} responses\n{'='*60}")

        if self.workflow is None:
            return {"error": "Workflow not initialized"}

        try:
            final_result = None
            async for event in self.workflow.run_stream(AnalysisState(surveys=surveys)):
                if isinstance(event, WorkflowOutputEvent):
                    final_result = event.data
                    logger.info(f"\n{'='*60}\n✨ Analysis Complete!\n{'='*60}\n")

            return final_result if final_result else {"error": "Workflow failed"}
        finally:
            # Always cleanup, even if workflow fails
            await self.cleanup()
