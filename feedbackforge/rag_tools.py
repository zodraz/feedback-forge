"""
RAG-Enhanced Chat Tools for FeedbackForge
==========================================

Enhanced versions of chat tools that use Azure AI Search for intelligent retrieval.
"""

import logging
import os
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta

from .rag_search import rag_search_client
from .data_store import feedback_store

logger = logging.getLogger(__name__)


def get_embeddings(text: str) -> List[float]:
    """
    Generate embeddings for text using Azure OpenAI.

    Args:
        text: Input text

    Returns:
        List of embedding values

    Raises:
        ValueError: If required environment variables are not set
    """
    try:
        from openai import AzureOpenAI

        # Validate required environment variables
        api_key = os.environ.get("AZURE_OPENAI_KEY")
        endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT")
        deployment = os.environ.get("AZURE_OPENAI_EMBEDDING_DEPLOYMENT", "text-embedding-3-small")
        api_version = os.environ.get("AZURE_AI_MODEL_DEPLOYMENT_VERSION", "2024-10-21")

        if not api_key or not endpoint:
            logger.error("Azure OpenAI credentials not configured")
            logger.error("Required: AZURE_OPENAI_KEY and AZURE_OPENAI_ENDPOINT")
            # Return zero vector as fallback
            return [0.0] * 1536

        client = AzureOpenAI(
            api_key=api_key,
            azure_endpoint=endpoint,
            api_version=api_version
        )

        response = client.embeddings.create(
            input=text,
            model=deployment
        )

        return response.data[0].embedding

    except Exception as e:
        logger.error(f"Failed to generate embeddings: {e}")
        # Return zero vector as fallback
        return [0.0] * 1536


def rag_search_feedback(
    query: str,
    search_type: str = "hybrid",
    top: int = 10,
    filters: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Search feedback using RAG with Azure AI Search.

    Args:
        query: Natural language search query
        search_type: Type of search - "semantic", "vector", or "hybrid"
        top: Number of results
        filters: OData filter expression

    Returns:
        List of relevant feedback items
    """
    if not rag_search_client:
        logger.warning("RAG search not available, falling back to database query")
        # Fallback to regular database search
        return []

    try:
        if search_type == "semantic":
            results = rag_search_client.semantic_search(
                query=query,
                top=top,
                filters=filters
            )
        elif search_type == "vector":
            results = rag_search_client.vector_search(
                query=query,
                get_embeddings_func=get_embeddings,
                top=top,
                filters=filters
            )
        else:  # hybrid (recommended)
            results = rag_search_client.hybrid_search(
                query=query,
                get_embeddings_func=get_embeddings,
                top=top,
                filters=filters
            )

        logger.info(f"RAG search for '{query}' returned {len(results)} results")
        return results

    except Exception as e:
        logger.error(f"RAG search failed: {e}")
        return []


def rag_get_weekly_summary() -> Dict[str, Any]:
    """
    Get weekly feedback summary using RAG for intelligent trend detection.

    Returns:
        Dictionary with weekly summary and RAG insights
    """
    try:
        # Use hybrid search to find most relevant recent feedback
        week_ago = datetime.now() - timedelta(days=7)
        filters = f"timestamp ge {week_ago.isoformat()}"

        # Search for different sentiment patterns
        positive_feedback = rag_search_feedback(
            query="positive experience great love satisfied",
            filters=f"{filters} and sentiment eq 'positive'",
            top=5
        )

        negative_feedback = rag_search_feedback(
            query="problem issue bug crash error frustrating",
            filters=f"{filters} and sentiment eq 'negative'",
            top=10
        )

        urgent_feedback = rag_search_feedback(
            query="urgent critical important immediate attention required",
            filters=f"{filters} and is_urgent eq true",
            top=5
        )

        # Get overall stats from database
        summary = feedback_store.get_weekly_summary()

        # Enhance with RAG insights
        enhanced_summary = {
            **summary,
            "rag_insights": {
                "top_positive_themes": [
                    {
                        "text": item.get("text", "")[:100],
                        "customer": item.get("customer_name"),
                        "score": item.get("reranker_score", item.get("search_score", 0))
                    }
                    for item in positive_feedback[:3]
                ],
                "critical_issues": [
                    {
                        "text": item.get("text", "")[:100],
                        "customer": item.get("customer_name"),
                        "platform": item.get("platform"),
                        "urgency": "HIGH" if item.get("is_urgent") else "MEDIUM",
                        "score": item.get("reranker_score", item.get("search_score", 0))
                    }
                    for item in negative_feedback[:5]
                ],
                "urgent_items": len(urgent_feedback),
            }
        }

        return enhanced_summary

    except Exception as e:
        logger.error(f"RAG weekly summary failed: {e}")
        # Fallback to regular summary
        return feedback_store.get_weekly_summary()


def rag_get_issue_details(topic: str) -> Dict[str, Any]:
    """
    Get detailed analysis for a specific issue using RAG.

    Args:
        topic: Issue/topic to analyze

    Returns:
        Detailed issue analysis
    """
    try:
        # Use semantic search to find related feedback
        results = rag_search_feedback(
            query=f"{topic} problem issue error",
            search_type="hybrid",
            top=20
        )

        if not results:
            return feedback_store.get_issue_details(topic)

        # Analyze results
        affected_customers = set()
        platforms = {}
        versions = {}
        sample_feedback = []

        for item in results:
            affected_customers.add(item.get("customer_id"))

            platform = item.get("platform")
            platforms[platform] = platforms.get(platform, 0) + 1

            version = item.get("product_version")
            versions[version] = versions.get(version, 0) + 1

            if len(sample_feedback) < 5:
                sample_feedback.append({
                    "text": item.get("text"),
                    "customer": item.get("customer_name"),
                    "rating": item.get("rating"),
                    "relevance_score": item.get("reranker_score", item.get("search_score", 0))
                })

        return {
            "topic": topic,
            "count": len(results),
            "affected_customers": len(affected_customers),
            "affected_platforms": list(platforms.keys()),
            "platform_distribution": platforms,
            "version_distribution": versions,
            "sample_feedback": sample_feedback,
            "search_method": "RAG with Azure AI Search"
        }

    except Exception as e:
        logger.error(f"RAG issue details failed for {topic}: {e}")
        return feedback_store.get_issue_details(topic)


def rag_get_competitor_insights() -> Dict[str, Any]:
    """
    Get competitive intelligence using RAG for better competitor mention detection.

    Returns:
        Competitor analysis with insights
    """
    try:
        # Search for competitor mentions
        competitor_feedback = rag_search_feedback(
            query="competitor alternative other product switch comparing better",
            search_type="hybrid",
            top=30
        )

        if not competitor_feedback:
            return feedback_store.get_competitor_analysis()

        # Extract competitor insights
        competitors = {}
        churn_risks = []

        for item in competitor_feedback:
            mentions = item.get("competitor_mentions", [])
            for comp in mentions:
                if comp not in competitors:
                    competitors[comp] = {
                        "name": comp,
                        "mention_count": 0,
                        "context": []
                    }
                competitors[comp]["mention_count"] += 1
                if len(competitors[comp]["context"]) < 3:
                    competitors[comp]["context"].append(item.get("text", "")[:100])

            # Check for churn risk
            sentiment = item.get("sentiment")
            rating = item.get("rating", 5)
            if sentiment == "negative" and rating <= 2:
                churn_risks.append({
                    "customer_id": item.get("customer_id"),
                    "customer_name": item.get("customer_name"),
                    "segment": item.get("customer_segment"),
                    "feedback": item.get("text", "")[:100],
                    "competitors_mentioned": mentions,
                    "relevance_score": item.get("reranker_score", item.get("search_score", 0))
                })

        return {
            "competitors": list(competitors.values()),
            "churn_risk_customers": churn_risks[:10],
            "total_churn_risks": len(churn_risks),
            "search_method": "RAG with Azure AI Search"
        }

    except Exception as e:
        logger.error(f"RAG competitor insights failed: {e}")
        return feedback_store.get_competitor_analysis()


def rag_detect_anomalies() -> List[Dict[str, Any]]:
    """
    Detect unusual patterns using RAG for intelligent anomaly detection.

    Returns:
        List of detected anomalies
    """
    try:
        # Use temporal filters
        now = datetime.now()
        two_hours_ago = now - timedelta(hours=2)
        filters = f"timestamp ge {two_hours_ago.isoformat()}"

        # Search for unusual patterns
        spike_patterns = [
            ("crash freeze hang unresponsive", "Performance Issues"),
            ("data loss deleted missing disappeared", "Data Loss"),
            ("security breach hack vulnerability", "Security Issues"),
            ("cannot login sign in authentication", "Auth Problems"),
            ("payment failed billing charge", "Payment Issues"),
        ]

        anomalies = []
        for query, category in spike_patterns:
            results = rag_search_feedback(
                query=query,
                filters=filters,
                top=50
            )

            if len(results) > 5:  # Threshold for anomaly
                affected_customers = len(set(r.get("customer_id") for r in results))
                negative_count = sum(1 for r in results if r.get("sentiment") == "negative")

                anomalies.append({
                    "category": category,
                    "count": len(results),
                    "severity": "CRITICAL" if len(results) > 20 else "HIGH",
                    "affected_customers": affected_customers,
                    "negative_pct": round(negative_count / len(results) * 100) if results else 0,
                    "sample_feedback": [r.get("text", "")[:100] for r in results[:3]],
                    "detection_method": "RAG Semantic Analysis"
                })

        # Fallback to regular anomaly detection if RAG found nothing
        if not anomalies:
            return feedback_store.detect_anomalies()

        return anomalies

    except Exception as e:
        logger.error(f"RAG anomaly detection failed: {e}")
        return feedback_store.detect_anomalies()


def rag_find_similar_feedback(feedback_text: str, top: int = 5) -> List[Dict[str, Any]]:
    """
    Find similar feedback using vector similarity search.

    Args:
        feedback_text: Reference feedback text
        top: Number of similar items to return

    Returns:
        List of similar feedback items
    """
    try:
        if not rag_search_client:
            return []

        results = rag_search_client.vector_search(
            query=feedback_text,
            get_embeddings_func=get_embeddings,
            top=top
        )

        return [{
            "id": r.get("id"),
            "text": r.get("text"),
            "customer": r.get("customer_name"),
            "sentiment": r.get("sentiment"),
            "similarity_score": r.get("similarity_score", 0),
            "timestamp": r.get("timestamp")
        } for r in results]

    except Exception as e:
        logger.error(f"Similar feedback search failed: {e}")
        return []


def rag_answer_question(question: str, context_window: int = 5) -> Dict[str, Any]:
    """
    Answer natural language questions about feedback using RAG.

    Args:
        question: User question
        context_window: Number of relevant documents to retrieve

    Returns:
        Dictionary with question, context, and relevant feedback
    """
    try:
        # Retrieve relevant context
        results = rag_search_feedback(
            query=question,
            search_type="hybrid",
            top=context_window
        )

        if not results:
            return {
                "question": question,
                "relevant_feedback_count": 0,
                "context": [],
                "message": "I couldn't find relevant feedback to answer that question."
            }

        # Build context from results
        context_docs = []
        for r in results:
            context_docs.append({
                "text": r.get("text"),
                "customer": r.get("customer_name"),
                "sentiment": r.get("sentiment"),
                "platform": r.get("platform"),
                "rating": r.get("rating")
            })

        return {
            "question": question,
            "relevant_feedback_count": len(results),
            "context": context_docs,
            "suggestion": "Use this context with your LLM to generate a comprehensive answer"
        }

    except Exception as e:
        logger.error(f"RAG question answering failed: {e}")
        return {
            "question": question,
            "relevant_feedback_count": 0,
            "context": [],
            "error": str(e)
        }
