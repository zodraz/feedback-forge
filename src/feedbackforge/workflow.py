"""
FeedbackForge Workflow
======================

Survey analysis workflow with parallel execution.
"""

from typing import Any, Dict, List

from agent_framework import WorkflowBuilder, WorkflowOutputEvent
from agent_framework.azure import AzureOpenAIChatClient
from azure.identity import AzureCliCredential

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


class SurveyAnalysisWorkflow:
    """Main workflow with parallel execution."""

    def __init__(self):
        self.credential = AzureCliCredential()
        self.chat_client = AzureOpenAIChatClient(credential=self.credential)
        self.workflow = None
        self._setup_workflow()

    def _setup_workflow(self):
        """Build the workflow DAG with parallel branches."""
        orchestrator_init = InitialOrchestrator(self.chat_client)
        preprocessor = DataPreprocessor(self.chat_client)
        sentiment = SentimentAnalyzer(self.chat_client)
        topics = TopicExtractor(self.chat_client)
        anomaly = AnomalyDetector(self.chat_client)
        competitive = CompetitiveIntelligence(self.chat_client)
        insights = InsightMiner(self.chat_client)
        priorities = PriorityRanker(self.chat_client)
        actions = ActionGenerator(self.chat_client)
        reporter = ReportGenerator(self.chat_client)
        orchestrator_final = FinalOrchestrator(self.chat_client)

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

    async def analyze(self, surveys: List[SurveyResponse]) -> Dict[str, Any]:
        """Run the complete analysis workflow."""
        print(f"\n{'='*60}\n🚀 Starting Multi-Agent Analysis\n📊 Analyzing {len(surveys)} responses\n{'='*60}")

        if self.workflow is None:
            return {"error": "Workflow not initialized"}

        final_result = None
        async for event in self.workflow.run_stream(AnalysisState(surveys=surveys)):
            if isinstance(event, WorkflowOutputEvent):
                final_result = event.data
                print(f"\n{'='*60}\n✨ Analysis Complete!\n{'='*60}\n")

        return final_result if final_result else {"error": "Workflow failed"}
