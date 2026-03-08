"""
FeedbackForge Workflow Executors
================================

Executor classes for the multi-agent workflow pipeline.
"""

import json
import logging
import os
from dataclasses import asdict
from datetime import datetime
from typing import Any, Dict, List

from agent_framework import Executor, WorkflowContext, handler, ChatAgent
from agent_framework.azure import AzureAIAgentClient
from azure.identity.aio import DefaultAzureCredential

from .models import AnalysisState

logger = logging.getLogger(__name__)


def parse_json_response(text: str) -> Dict[str, Any]:
    """Parse JSON from agent response."""
    try:
        if '{' in text and '}' in text:
            return json.loads(text[text.find('{'):text.rfind('}') + 1])
        return {"raw_response": text, "status": "completed"}
    except Exception:
        return {"raw_response": text, "status": "completed"}


# ============================================================================
# STAGE 1: INITIAL ORCHESTRATOR
# ============================================================================

class InitialOrchestrator(Executor):
    """Initial orchestrator that analyzes input and plans execution."""

    def __init__(self, credential: DefaultAzureCredential, id: str = "orchestrator_initial"):
        chat_client = AzureAIAgentClient(
            project_endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            model_deployment_name=os.environ["AZURE_OPENAI_RESPONSES_DEPLOYMENT_NAME"],
            credential=credential,
            agent_name="InitialOrchestrator",
            agent_description="Initial orchestrator for workflow planning"
        )
        self.agent = ChatAgent(
            chat_client=chat_client,
            name="InitialOrchestrator",
            agent_id="InitialOrchestrator:1",
            instructions="""You are the Initial Orchestrator Agent. Validate survey data, assess quality, plan analysis.
Return JSON: {"proceed": true/false, "survey_count": N, "quality_assessment": "good/fair/poor", "summary": "..."}"""
        )
        super().__init__(id=id)

    @handler
    async def orchestrate_initial(self, state: AnalysisState, ctx: WorkflowContext[AnalysisState]) -> None:
        logger.info("="*60)
        logger.info("🎼 Initial Orchestrator: Planning Analysis")
        logger.info("="*60)
        survey_data = json.dumps([asdict(s) for s in state.surveys], indent=2)
        result = await self.agent.run(f"Analyze this survey batch:\n\n{survey_data}")
        state.orchestrator_initial = parse_json_response(result.text)
        logger.info(f"✅ Plan: {state.orchestrator_initial.get('summary', 'Ready')}")
        await ctx.send_message(state)


# ============================================================================
# STAGE 2: DATA PREPROCESSING
# ============================================================================

class DataPreprocessor(Executor):
    """Executor for data preprocessing."""

    def __init__(self, credential: DefaultAzureCredential, id: str = "preprocessor"):
        chat_client = AzureAIAgentClient(
            project_endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            model_deployment_name=os.environ["AZURE_OPENAI_RESPONSES_DEPLOYMENT_NAME"],
            credential=credential,
            agent_name="DataPreprocessor",
            agent_description="Data preprocessing agent"
        )
        self.agent = ChatAgent(
            chat_client=chat_client,
            name="DataPreprocessor",
            agent_id="asst_xXHIE4eAiMcRCO2XU98pdVyw",
            instructions="""Clean and prepare survey data. Return JSON: {"cleaned_count": N, "spam_count": N, "summary": "..."}"""
        )
        super().__init__(id=id)

    @handler
    async def preprocess(self, state: AnalysisState, ctx: WorkflowContext[AnalysisState]) -> None:
        logger.info(f"\n📊 Data Preprocessing")
        result = await self.agent.run(f"Preprocess:\n{json.dumps([asdict(s) for s in state.surveys], indent=2)}")
        state.preprocessing = parse_json_response(result.text)
        logger.info(f"✅ {state.preprocessing.get('summary', 'Done')}")
        await ctx.send_message(state)


# ============================================================================
# STAGE 3: PARALLEL ANALYSIS EXECUTORS
# ============================================================================

class SentimentAnalyzer(Executor):
    """Sentiment analysis executor."""

    def __init__(self, credential: DefaultAzureCredential, id: str = "sentiment"):
        chat_client = AzureAIAgentClient(
            project_endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            model_deployment_name=os.environ["AZURE_OPENAI_RESPONSES_DEPLOYMENT_NAME"],
            credential=credential,
            agent_name="SentimentAnalyzer",
            agent_description="Sentiment analysis agent"
        )
        self.agent = ChatAgent(
            chat_client=chat_client,
            name="SentimentAnalyzer",
            agent_id="SentimentAnalyzer:1",
            instructions="""Analyze sentiment. Return JSON: {"overall_distribution": {"positive": %, "negative": %, "neutral": %}, "urgent_flags": [], "summary": "..."}"""
        )
        super().__init__(id=id)

    @handler
    async def analyze(self, state: AnalysisState, ctx: WorkflowContext[AnalysisState]) -> None:
        logger.info(f"🎭 Sentiment Analysis (Parallel)")
        result = await self.agent.run(f"Analyze sentiment:\n{json.dumps([asdict(s) for s in state.surveys], indent=2)}")
        state.sentiment = parse_json_response(result.text)
        logger.info(f"✅ Sentiment complete")
        await ctx.send_message(state)


class TopicExtractor(Executor):
    """Topic extraction executor."""

    def __init__(self, credential: DefaultAzureCredential, id: str = "topics"):
        chat_client = AzureAIAgentClient(
            project_endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            model_deployment_name=os.environ["AZURE_OPENAI_RESPONSES_DEPLOYMENT_NAME"],
            credential=credential,
            agent_name="TopicExtractor",
            agent_description="Topic extraction agent"
        )
        self.agent = ChatAgent(
            chat_client=chat_client,
            name="TopicExtractor",
            agent_id="TopicExtractor:3",
            instructions="""Extract topics. Return JSON: {"topic_distribution": {}, "emerging_themes": [], "summary": "..."}"""
        )
        super().__init__(id=id)

    @handler
    async def extract(self, state: AnalysisState, ctx: WorkflowContext[AnalysisState]) -> None:
        logger.info(f"🏷️  Topic Extraction (Parallel)")
        result = await self.agent.run(f"Extract topics:\n{json.dumps([asdict(s) for s in state.surveys], indent=2)}")
        state.topics = parse_json_response(result.text)
        logger.info(f"✅ Topics complete")
        await ctx.send_message(state)


class AnomalyDetector(Executor):
    """Anomaly detection executor."""

    def __init__(self, credential: DefaultAzureCredential, id: str = "anomaly"):
        chat_client = AzureAIAgentClient(
            project_endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            model_deployment_name=os.environ["AZURE_OPENAI_RESPONSES_DEPLOYMENT_NAME"],
            credential=credential,
            agent_name="AnomalyDetector",
            agent_description="Anomaly detection agent"
        )
        self.agent = ChatAgent(
            chat_client=chat_client,
            name="AnomalyDetector",
            agent_id="AnomalyDetector:2",
            instructions="""Detect anomalies. Return JSON: {"anomalies_detected": [], "crisis_indicators": [], "summary": "..."}"""
        )
        super().__init__(id=id)

    @handler
    async def detect(self, state: AnalysisState, ctx: WorkflowContext[AnalysisState]) -> None:
        logger.info(f"🔍 Anomaly Detection (Parallel)")
        result = await self.agent.run(f"Detect anomalies:\n{json.dumps([asdict(s) for s in state.surveys], indent=2)}")
        state.anomalies = parse_json_response(result.text)
        logger.info(f"✅ Anomalies complete")
        await ctx.send_message(state)


class CompetitiveIntelligence(Executor):
    """Competitive intelligence executor."""

    def __init__(self, credential: DefaultAzureCredential, id: str = "competitive"):
        chat_client = AzureAIAgentClient(
            project_endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            model_deployment_name=os.environ["AZURE_OPENAI_RESPONSES_DEPLOYMENT_NAME"],
            credential=credential,
            agent_name="CompetitiveIntelligence",
            agent_description="Competitive intelligence agent"
        )
        self.agent = ChatAgent(
            chat_client=chat_client,
            name="CompetitiveIntelligence",
            instructions="""Extract competitor info. Return JSON: {"competitor_mentions": [], "win_loss_analysis": {}, "summary": "..."}"""
        )
        super().__init__(id=id)

    @handler
    async def analyze_competitive(self, state: AnalysisState, ctx: WorkflowContext[AnalysisState]) -> None:
        logger.info(f"🏆 Competitive Intelligence (Parallel)")
        result = await self.agent.run(f"Analyze competitors:\n{json.dumps([asdict(s) for s in state.surveys], indent=2)}")
        state.competitive = parse_json_response(result.text)
        logger.info(f"✅ Competitive complete")
        await ctx.send_message(state)


# ============================================================================
# STAGE 4: INSIGHT MINING (AGGREGATOR)
# ============================================================================

class InsightMiner(Executor):
    """Aggregates parallel results and mines insights (fan-in aggregator)."""

    def __init__(self, credential: DefaultAzureCredential, id: str = "insights"):
        chat_client = AzureAIAgentClient(
            project_endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            model_deployment_name=os.environ["AZURE_OPENAI_RESPONSES_DEPLOYMENT_NAME"],
            credential=credential,
            agent_name="InsightMiner",
            agent_description="Insight mining agent"
        )
        self.agent = ChatAgent(
            chat_client=chat_client,
            name="InsightMiner",
            instructions="""Synthesize analyses. Return JSON: {"key_insights": [], "patterns": [], "root_causes": [], "summary": "..."}"""
        )
        super().__init__(id=id)

    @handler
    async def mine(self, states: List[AnalysisState], ctx: WorkflowContext[AnalysisState]) -> None:
        """Fan-in handler: receives list of states from all parallel analyzers."""
        logger.info(f"\n💡 Insight Mining (aggregating {len(states)} parallel results)")

        # Merge all parallel analysis results into one state
        merged = states[0]
        for state in states[1:]:
            if state.sentiment:
                merged.sentiment = state.sentiment
            if state.topics:
                merged.topics = state.topics
            if state.anomalies:
                merged.anomalies = state.anomalies
            if state.competitive:
                merged.competitive = state.competitive

        context = f"Sentiment: {json.dumps(merged.sentiment)}\nTopics: {json.dumps(merged.topics)}\nAnomalies: {json.dumps(merged.anomalies)}\nCompetitive: {json.dumps(merged.competitive)}"
        result = await self.agent.run(context)
        merged.insights = parse_json_response(result.text)
        logger.info(f"✅ Insights mined")
        await ctx.send_message(merged)


# ============================================================================
# STAGE 5: PARALLEL ACTION GENERATION
# ============================================================================

class PriorityRanker(Executor):
    """Priority ranking executor."""

    def __init__(self, credential: DefaultAzureCredential, id: str = "priority"):
        chat_client = AzureAIAgentClient(
            project_endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            model_deployment_name=os.environ["AZURE_OPENAI_RESPONSES_DEPLOYMENT_NAME"],
            credential=credential,
            agent_name="PriorityRanker",
            agent_description="Priority ranking agent"
        )
        self.agent = ChatAgent(
            chat_client=chat_client,
            name="PriorityRanker",
            instructions="""Rank priorities. Return JSON: {"priority_matrix": [], "quick_wins": [], "churn_risks": [], "summary": "..."}"""
        )
        super().__init__(id=id)

    @handler
    async def rank(self, state: AnalysisState, ctx: WorkflowContext[AnalysisState]) -> None:
        logger.info(f"🎯 Priority Ranking (Parallel)")
        result = await self.agent.run(f"Insights: {json.dumps(state.insights)}\n\nRank priorities.")
        state.priorities = parse_json_response(result.text)
        logger.info(f"✅ Priorities ranked")
        await ctx.send_message(state)


class ActionGenerator(Executor):
    """Action item generator executor."""

    def __init__(self, credential: DefaultAzureCredential, id: str = "actions"):
        chat_client = AzureAIAgentClient(
            project_endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            model_deployment_name=os.environ["AZURE_OPENAI_RESPONSES_DEPLOYMENT_NAME"],
            credential=credential,
            agent_name="ActionGenerator",
            agent_description="Action generation agent"
        )
        self.agent = ChatAgent(
            chat_client=chat_client,
            name="ActionGenerator",
            instructions="""Generate actions. Return JSON: {"action_items": [], "success_metrics": [], "summary": "..."}"""
        )
        super().__init__(id=id)

    @handler
    async def generate(self, state: AnalysisState, ctx: WorkflowContext[AnalysisState]) -> None:
        logger.info(f"📋 Action Generation (Parallel)")
        result = await self.agent.run(f"Insights: {json.dumps(state.insights)}\n\nGenerate actions.")
        state.actions = parse_json_response(result.text)
        logger.info(f"✅ Actions generated")
        await ctx.send_message(state)


# ============================================================================
# STAGE 6: REPORT GENERATION
# ============================================================================

class ReportGenerator(Executor):
    """Final report generator (fan-in aggregator)."""

    def __init__(self, credential: DefaultAzureCredential, id: str = "reporter"):
        chat_client = AzureAIAgentClient(
            project_endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            model_deployment_name=os.environ["AZURE_OPENAI_RESPONSES_DEPLOYMENT_NAME"],
            credential=credential,
            agent_name="ReportGenerator",
            agent_description="Report generation agent"
        )
        self.agent = ChatAgent(
            chat_client=chat_client,
            name="ReportGenerator",
            instructions="""Generate report. Return JSON: {"executive_summary": "", "key_metrics": {}, "critical_issues": [], "recommendations": []}"""
        )
        super().__init__(id=id)

    @handler
    async def generate_report(self, states: List[AnalysisState], ctx: WorkflowContext[AnalysisState]) -> None:
        """Fan-in handler: receives list of states from priorities and actions."""
        logger.info(f"\n📄 Report Generation (aggregating {len(states)} parallel results)")

        # Merge priorities and actions from parallel executors
        merged = states[0]
        for state in states[1:]:
            if state.priorities:
                merged.priorities = state.priorities
            if state.actions:
                merged.actions = state.actions

        context = f"All Results:\n{json.dumps({'sentiment': merged.sentiment, 'topics': merged.topics, 'insights': merged.insights, 'priorities': merged.priorities, 'actions': merged.actions})}"
        result = await self.agent.run(context)
        merged.report = parse_json_response(result.text)
        logger.info(f"✅ Report generated")
        await ctx.send_message(merged)


# ============================================================================
# STAGE 7: FINAL ORCHESTRATOR REVIEW
# ============================================================================

class FinalOrchestrator(Executor):
    """Final orchestrator review."""

    def __init__(self, credential: DefaultAzureCredential, id: str = "orchestrator_final"):
        chat_client = AzureAIAgentClient(
            project_endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            model_deployment_name=os.environ["AZURE_OPENAI_RESPONSES_DEPLOYMENT_NAME"],
            credential=credential,
            agent_name="FinalOrchestrator",
            agent_description="Final orchestrator review agent"
        )
        self.agent = ChatAgent(
            chat_client=chat_client,
            name="FinalOrchestrator",
            instructions="""Review results. Return JSON: {"quality_assessment": "", "confidence_score": 0.0-1.0, "final_recommendations": [], "next_steps": []}"""
        )
        super().__init__(id=id)

    @handler
    async def orchestrate_final(self, state: AnalysisState, ctx: WorkflowContext[AnalysisState, Dict[str, Any]]) -> None:
        logger.info(f"\n{'='*60}\n🎼 Final Orchestrator Review\n{'='*60}")
        all_results = {"preprocessing": state.preprocessing, "sentiment": state.sentiment, "topics": state.topics,
                       "anomalies": state.anomalies, "competitive": state.competitive, "insights": state.insights,
                       "priorities": state.priorities, "actions": state.actions, "report": state.report}
        result = await self.agent.run(f"Review:\n{json.dumps(all_results, indent=2)}")
        state.orchestrator_final = parse_json_response(result.text)
        logger.info(f"✅ Review Complete")
        await ctx.yield_output({
            "analysis_complete": True, "timestamp": datetime.now().isoformat(),
            "surveys_analyzed": len(state.surveys), "parallel_analysis": {"sentiment": state.sentiment, "topics": state.topics, "anomalies": state.anomalies, "competitive": state.competitive},
            "insights": state.insights, "priorities": state.priorities, "actions": state.actions,
            "final_report": state.report, "orchestrator_final": state.orchestrator_final
        })
