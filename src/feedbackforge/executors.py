"""
FeedbackForge Workflow Executors
================================

Executor classes for the multi-agent workflow pipeline.
"""

import json
from dataclasses import asdict
from datetime import datetime
from typing import Any, Dict, List

from agent_framework import Executor, WorkflowContext, handler
from agent_framework.azure import AzureOpenAIChatClient

from .models import AnalysisState


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

    def __init__(self, chat_client: AzureOpenAIChatClient, id: str = "orchestrator_initial"):
        self.agent = chat_client.create_agent(
            name="InitialOrchestrator",
            instructions="""You are the Initial Orchestrator Agent. Validate survey data, assess quality, plan analysis.
Return JSON: {"proceed": true/false, "survey_count": N, "quality_assessment": "good/fair/poor", "summary": "..."}"""
        )
        super().__init__(id=id)

    @handler
    async def orchestrate_initial(self, state: AnalysisState, ctx: WorkflowContext[AnalysisState]) -> None:
        print(f"\n{'='*60}\n🎼 Initial Orchestrator: Planning Analysis\n{'='*60}")
        survey_data = json.dumps([asdict(s) for s in state.surveys], indent=2)
        result = await self.agent.run(f"Analyze this survey batch:\n\n{survey_data}")
        state.orchestrator_initial = parse_json_response(result.text)
        print(f"✅ Plan: {state.orchestrator_initial.get('summary', 'Ready')}")
        await ctx.send_message(state)


# ============================================================================
# STAGE 2: DATA PREPROCESSING
# ============================================================================

class DataPreprocessor(Executor):
    """Executor for data preprocessing."""

    def __init__(self, chat_client: AzureOpenAIChatClient, id: str = "preprocessor"):
        self.agent = chat_client.create_agent(
            name="DataPreprocessor",
            instructions="""Clean and prepare survey data. Return JSON: {"cleaned_count": N, "spam_count": N, "summary": "..."}"""
        )
        super().__init__(id=id)

    @handler
    async def preprocess(self, state: AnalysisState, ctx: WorkflowContext[AnalysisState]) -> None:
        print(f"\n📊 Data Preprocessing")
        result = await self.agent.run(f"Preprocess:\n{json.dumps([asdict(s) for s in state.surveys], indent=2)}")
        state.preprocessing = parse_json_response(result.text)
        print(f"✅ {state.preprocessing.get('summary', 'Done')}")
        await ctx.send_message(state)


# ============================================================================
# STAGE 3: PARALLEL ANALYSIS EXECUTORS
# ============================================================================

class SentimentAnalyzer(Executor):
    """Sentiment analysis executor."""

    def __init__(self, chat_client: AzureOpenAIChatClient, id: str = "sentiment"):
        self.agent = chat_client.create_agent(
            name="SentimentAnalyzer",
            instructions="""Analyze sentiment. Return JSON: {"overall_distribution": {"positive": %, "negative": %, "neutral": %}, "urgent_flags": [], "summary": "..."}"""
        )
        super().__init__(id=id)

    @handler
    async def analyze(self, state: AnalysisState, ctx: WorkflowContext[AnalysisState]) -> None:
        print(f"🎭 Sentiment Analysis (Parallel)")
        result = await self.agent.run(f"Analyze sentiment:\n{json.dumps([asdict(s) for s in state.surveys], indent=2)}")
        state.sentiment = parse_json_response(result.text)
        print(f"✅ Sentiment complete")
        await ctx.send_message(state)


class TopicExtractor(Executor):
    """Topic extraction executor."""

    def __init__(self, chat_client: AzureOpenAIChatClient, id: str = "topics"):
        self.agent = chat_client.create_agent(
            name="TopicExtractor",
            instructions="""Extract topics. Return JSON: {"topic_distribution": {}, "emerging_themes": [], "summary": "..."}"""
        )
        super().__init__(id=id)

    @handler
    async def extract(self, state: AnalysisState, ctx: WorkflowContext[AnalysisState]) -> None:
        print(f"🏷️  Topic Extraction (Parallel)")
        result = await self.agent.run(f"Extract topics:\n{json.dumps([asdict(s) for s in state.surveys], indent=2)}")
        state.topics = parse_json_response(result.text)
        print(f"✅ Topics complete")
        await ctx.send_message(state)


class AnomalyDetector(Executor):
    """Anomaly detection executor."""

    def __init__(self, chat_client: AzureOpenAIChatClient, id: str = "anomaly"):
        self.agent = chat_client.create_agent(
            name="AnomalyDetector",
            instructions="""Detect anomalies. Return JSON: {"anomalies_detected": [], "crisis_indicators": [], "summary": "..."}"""
        )
        super().__init__(id=id)

    @handler
    async def detect(self, state: AnalysisState, ctx: WorkflowContext[AnalysisState]) -> None:
        print(f"🔍 Anomaly Detection (Parallel)")
        result = await self.agent.run(f"Detect anomalies:\n{json.dumps([asdict(s) for s in state.surveys], indent=2)}")
        state.anomalies = parse_json_response(result.text)
        print(f"✅ Anomalies complete")
        await ctx.send_message(state)


class CompetitiveIntelligence(Executor):
    """Competitive intelligence executor."""

    def __init__(self, chat_client: AzureOpenAIChatClient, id: str = "competitive"):
        self.agent = chat_client.create_agent(
            name="CompetitiveIntelligence",
            instructions="""Extract competitor info. Return JSON: {"competitor_mentions": [], "win_loss_analysis": {}, "summary": "..."}"""
        )
        super().__init__(id=id)

    @handler
    async def analyze_competitive(self, state: AnalysisState, ctx: WorkflowContext[AnalysisState]) -> None:
        print(f"🏆 Competitive Intelligence (Parallel)")
        result = await self.agent.run(f"Analyze competitors:\n{json.dumps([asdict(s) for s in state.surveys], indent=2)}")
        state.competitive = parse_json_response(result.text)
        print(f"✅ Competitive complete")
        await ctx.send_message(state)


# ============================================================================
# STAGE 4: INSIGHT MINING (AGGREGATOR)
# ============================================================================

class InsightMiner(Executor):
    """Aggregates parallel results and mines insights (fan-in aggregator)."""

    def __init__(self, chat_client: AzureOpenAIChatClient, id: str = "insights"):
        self.agent = chat_client.create_agent(
            name="InsightMiner",
            instructions="""Synthesize analyses. Return JSON: {"key_insights": [], "patterns": [], "root_causes": [], "summary": "..."}"""
        )
        super().__init__(id=id)

    @handler
    async def mine(self, states: List[AnalysisState], ctx: WorkflowContext[AnalysisState]) -> None:
        """Fan-in handler: receives list of states from all parallel analyzers."""
        print(f"\n💡 Insight Mining (aggregating {len(states)} parallel results)")

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
        print(f"✅ Insights mined")
        await ctx.send_message(merged)


# ============================================================================
# STAGE 5: PARALLEL ACTION GENERATION
# ============================================================================

class PriorityRanker(Executor):
    """Priority ranking executor."""

    def __init__(self, chat_client: AzureOpenAIChatClient, id: str = "priority"):
        self.agent = chat_client.create_agent(
            name="PriorityRanker",
            instructions="""Rank priorities. Return JSON: {"priority_matrix": [], "quick_wins": [], "churn_risks": [], "summary": "..."}"""
        )
        super().__init__(id=id)

    @handler
    async def rank(self, state: AnalysisState, ctx: WorkflowContext[AnalysisState]) -> None:
        print(f"🎯 Priority Ranking (Parallel)")
        result = await self.agent.run(f"Insights: {json.dumps(state.insights)}\n\nRank priorities.")
        state.priorities = parse_json_response(result.text)
        print(f"✅ Priorities ranked")
        await ctx.send_message(state)


class ActionGenerator(Executor):
    """Action item generator executor."""

    def __init__(self, chat_client: AzureOpenAIChatClient, id: str = "actions"):
        self.agent = chat_client.create_agent(
            name="ActionGenerator",
            instructions="""Generate actions. Return JSON: {"action_items": [], "success_metrics": [], "summary": "..."}"""
        )
        super().__init__(id=id)

    @handler
    async def generate(self, state: AnalysisState, ctx: WorkflowContext[AnalysisState]) -> None:
        print(f"📋 Action Generation (Parallel)")
        result = await self.agent.run(f"Insights: {json.dumps(state.insights)}\n\nGenerate actions.")
        state.actions = parse_json_response(result.text)
        print(f"✅ Actions generated")
        await ctx.send_message(state)


# ============================================================================
# STAGE 6: REPORT GENERATION
# ============================================================================

class ReportGenerator(Executor):
    """Final report generator (fan-in aggregator)."""

    def __init__(self, chat_client: AzureOpenAIChatClient, id: str = "reporter"):
        self.agent = chat_client.create_agent(
            name="ReportGenerator",
            instructions="""Generate report. Return JSON: {"executive_summary": "", "key_metrics": {}, "critical_issues": [], "recommendations": []}"""
        )
        super().__init__(id=id)

    @handler
    async def generate_report(self, states: List[AnalysisState], ctx: WorkflowContext[AnalysisState]) -> None:
        """Fan-in handler: receives list of states from priorities and actions."""
        print(f"\n📄 Report Generation (aggregating {len(states)} parallel results)")

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
        print(f"✅ Report generated")
        await ctx.send_message(merged)


# ============================================================================
# STAGE 7: FINAL ORCHESTRATOR REVIEW
# ============================================================================

class FinalOrchestrator(Executor):
    """Final orchestrator review."""

    def __init__(self, chat_client: AzureOpenAIChatClient, id: str = "orchestrator_final"):
        self.agent = chat_client.create_agent(
            name="FinalOrchestrator",
            instructions="""Review results. Return JSON: {"quality_assessment": "", "confidence_score": 0.0-1.0, "final_recommendations": [], "next_steps": []}"""
        )
        super().__init__(id=id)

    @handler
    async def orchestrate_final(self, state: AnalysisState, ctx: WorkflowContext[AnalysisState, Dict[str, Any]]) -> None:
        print(f"\n{'='*60}\n🎼 Final Orchestrator Review\n{'='*60}")
        all_results = {"preprocessing": state.preprocessing, "sentiment": state.sentiment, "topics": state.topics,
                       "anomalies": state.anomalies, "competitive": state.competitive, "insights": state.insights,
                       "priorities": state.priorities, "actions": state.actions, "report": state.report}
        result = await self.agent.run(f"Review:\n{json.dumps(all_results, indent=2)}")
        state.orchestrator_final = parse_json_response(result.text)
        print(f"✅ Review Complete")
        await ctx.yield_output({
            "analysis_complete": True, "timestamp": datetime.now().isoformat(),
            "surveys_analyzed": len(state.surveys), "parallel_analysis": {"sentiment": state.sentiment, "topics": state.topics, "anomalies": state.anomalies, "competitive": state.competitive},
            "insights": state.insights, "priorities": state.priorities, "actions": state.actions,
            "final_report": state.report, "orchestrator_final": state.orchestrator_final
        })
