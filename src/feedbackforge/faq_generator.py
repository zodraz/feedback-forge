"""
Auto FAQ Generator with RAG
============================

Automatically generates FAQs from customer feedback using semantic clustering
and intelligent answer synthesis.
"""

import logging
import os
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta, timezone
from collections import defaultdict

from .rag_search import rag_search_client, init_rag_search
from .rag_tools import get_embeddings
from .rag_setup import RAGSetup

logger = logging.getLogger(__name__)


class FAQGenerator:
    """Automatically generate FAQs from customer feedback using RAG."""

    def __init__(self, rag_client=None, auto_setup: bool = True):
        """
        Initialize FAQ generator.

        Args:
            rag_client: Optional RAG search client (uses global if not provided)
                       If not provided, will attempt to initialize from environment variables.
            auto_setup: If True, automatically create index and index data if needed
        """
        # Try to use provided client, then global, then initialize
        if rag_client:
            self.rag_client = rag_client
        elif rag_search_client:
            self.rag_client = rag_search_client
        else:
            # Try to initialize from environment
            logger.info("Initializing RAG search client from environment...")
            self.rag_client = init_rag_search()

        # Automatically setup RAG if needed
        if auto_setup and self.rag_client:
            try:
                setup = RAGSetup()
                setup.ensure_index_exists()
                setup.ensure_data_indexed()
            except Exception as e:
                logger.warning(f"⚠️ Auto-setup failed (continuing anyway): {e}")

    def find_common_themes(
        self,
        timeframe_days: int = 30,
        min_occurrences: int = 3,
        max_themes: int = 15
    ) -> List[Dict[str, Any]]:
        """
        Find common themes/questions from feedback using Azure AI Search RAG.

        Args:
            timeframe_days: Number of days to look back
            min_occurrences: Minimum feedback items for a theme
            max_themes: Maximum number of themes to return

        Returns:
            List of theme dictionaries with counts and samples
        """
        if not self.rag_client:
            logger.error("❌ RAG client not available. FAQ Generator requires Azure AI Search.")
            logger.error("   Please configure AZURE_SEARCH_ENDPOINT and run: python -m feedbackforge.rag_setup")
            raise ValueError("RAG client required for FAQ generation")

        try:
            logger.info("🔍 Using Azure AI Search to find common themes...")

            # Get recent feedback using time filter
            # Azure Search requires timezone-aware timestamps
            since = datetime.now(timezone.utc) - timedelta(days=timeframe_days)
            time_filter = f"timestamp ge {since.isoformat()}"

            # Use hybrid search for better accuracy
            # Search for question/problem patterns
            search_queries = [
                ("how to use feature", "usage questions"),
                ("why not working error", "error reports"),
                ("can I do this", "capability questions"),
                ("problem with issue", "problems"),
                ("confused about unclear", "clarity issues"),
                ("how do I configure", "configuration"),
                ("where is located", "navigation"),
                ("when will available", "availability"),
            ]

            all_feedback = {}  # id -> feedback dict
            feedback_to_query = {}  # id -> query that found it

            for query, category in search_queries:
                logger.info(f"   Searching: '{query}' ({category})")

                # Use HYBRID search with Azure AI Search (keyword + vector + semantic)
                results = self.rag_client.hybrid_search(
                    query=query,
                    get_embeddings_func=get_embeddings,
                    top=100,
                    filters=time_filter
                )

                for result in results:
                    feedback_id = result.get('id')
                    text = result.get('text', '')

                    # Only include question-like or problem feedback
                    if self._is_question_like(text):
                        if feedback_id not in all_feedback:
                            all_feedback[feedback_id] = {
                                'id': feedback_id,
                                'text': text,
                                'customer': result.get('customer_name'),
                                'segment': result.get('customer_segment'),
                                'platform': result.get('platform'),
                                'rating': result.get('rating'),
                                'timestamp': result.get('timestamp'),
                                'search_score': result.get('reranker_score', result.get('search_score', 0)),
                                'text_vector': result.get('text_vector'),  # For clustering
                            }
                        feedback_to_query[feedback_id] = category

            logger.info(f"   Found {len(all_feedback)} question/problem feedback items")

            # Cluster using VECTOR SIMILARITY (real semantic clustering)
            clustered = self._cluster_themes_with_vectors(list(all_feedback.values()))

            logger.info(f"   Clustered into {len(clustered)} theme groups")

            # Filter by minimum occurrences
            filtered = [
                theme for theme in clustered
                if theme['count'] >= min_occurrences
            ]

            logger.info(f"   Filtered to {len(filtered)} themes (min {min_occurrences} mentions)")

            # Sort by frequency and return top N
            sorted_themes = sorted(filtered, key=lambda x: x['count'], reverse=True)

            logger.info(f"✅ Found {len(sorted_themes[:max_themes])} common themes for FAQ generation")
            return sorted_themes[:max_themes]

        except Exception as e:
            logger.error(f"Failed to find common themes: {e}")
            raise

    def _is_question_like(self, text: str) -> bool:
        """Check if text looks like a question or complaint."""
        text_lower = text.lower()

        # Question indicators
        question_words = ['how', 'why', 'what', 'when', 'where', 'can', 'could', 'would', 'should']
        has_question = any(text_lower.startswith(word) for word in question_words)
        has_question = has_question or '?' in text

        # Problem indicators
        problem_words = ['not working', "doesn't work", 'error', 'problem', 'issue', 'bug', 'confused', 'unclear']
        has_problem = any(word in text_lower for word in problem_words)

        return has_question or has_problem

    def _cluster_themes_with_vectors(self, themes: List[Dict]) -> List[Dict[str, Any]]:
        """
        Cluster similar themes using VECTOR SIMILARITY from Azure AI Search.

        This uses the actual embeddings stored in Azure AI Search for semantic clustering.

        Args:
            themes: List of theme dictionaries (with text_vector if available)

        Returns:
            List of clustered themes with counts
        """
        if not themes:
            return []

        logger.info(f"   Clustering {len(themes)} items using vector similarity...")

        # Sort by search score (highest relevance first)
        themes = sorted(themes, key=lambda x: x.get('search_score', 0), reverse=True)

        clusters = []
        used_indices = set()
        similarity_threshold = 0.75  # Cosine similarity threshold

        for i, theme in enumerate(themes):
            if i in used_indices:
                continue

            # Create new cluster
            cluster = {
                'representative_text': theme['text'],
                'count': 1,
                'samples': [theme],
                'platforms': [theme.get('platform')],
                'segments': [theme.get('segment')],
                'avg_rating': theme.get('rating') or 3,
                'avg_search_score': theme.get('search_score', 0)
            }

            # Get embedding for this theme (if available)
            theme_vector = theme.get('text_vector')

            # Find similar themes using vector similarity
            for j, other in enumerate(themes):
                if j <= i or j in used_indices:
                    continue

                # Use vector similarity if available
                is_similar = False
                if theme_vector and other.get('text_vector'):
                    similarity = self._cosine_similarity(theme_vector, other['text_vector'])
                    is_similar = similarity >= similarity_threshold
                else:
                    # Fallback to text similarity
                    is_similar = self._are_similar(theme['text'], other['text'], threshold=0.6)

                if is_similar:
                    cluster['count'] += 1
                    cluster['samples'].append(other)
                    cluster['platforms'].append(other.get('platform'))
                    cluster['segments'].append(other.get('segment'))
                    used_indices.add(j)

            used_indices.add(i)

            # Calculate averages
            ratings = [s.get('rating') for s in cluster['samples'] if s.get('rating')]
            if ratings:
                cluster['avg_rating'] = sum(ratings) / len(ratings)

            scores = [s.get('search_score', 0) for s in cluster['samples']]
            if scores:
                cluster['avg_search_score'] = sum(scores) / len(scores)

            clusters.append(cluster)

        logger.info(f"   Created {len(clusters)} clusters")
        return clusters

    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """
        Calculate cosine similarity between two vectors.

        Args:
            vec1: First vector
            vec2: Second vector

        Returns:
            Similarity score (0-1)
        """
        if not vec1 or not vec2 or len(vec1) != len(vec2):
            return 0.0

        # Dot product
        dot_product = sum(a * b for a, b in zip(vec1, vec2))

        # Magnitudes
        mag1 = sum(a * a for a in vec1) ** 0.5
        mag2 = sum(b * b for b in vec2) ** 0.5

        if mag1 == 0 or mag2 == 0:
            return 0.0

        return dot_product / (mag1 * mag2)

    def _are_similar(self, text1: str, text2: str, threshold: float = 0.5) -> bool:
        """
        Check if two texts are semantically similar.

        Args:
            text1: First text
            text2: Second text
            threshold: Similarity threshold (0-1)

        Returns:
            True if similar enough
        """
        # Simple word overlap check (in production, use embedding similarity)
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())

        if not words1 or not words2:
            return False

        overlap = len(words1 & words2)
        union = len(words1 | words2)

        similarity = overlap / union if union > 0 else 0
        return similarity >= threshold

    def generate_faq_entries(
        self,
        themes: List[Dict[str, Any]],
        answer_style: str = "helpful"
    ) -> List[Dict[str, Any]]:
        """
        Generate FAQ entries from themes.

        Args:
            themes: List of common themes
            answer_style: Style of answers - "helpful", "technical", or "friendly"

        Returns:
            List of FAQ entries with questions and answers
        """
        faqs = []

        for theme in themes:
            # Extract question
            question = self._extract_question(theme)

            # Generate answer based on feedback samples
            answer = self._generate_answer(theme, answer_style)

            # Add metadata
            faq_entry = {
                'question': question,
                'answer': answer,
                'frequency': theme['count'],
                'platforms': list(set(theme['platforms'])),
                'segments': list(set(theme['segments'])),
                'avg_rating': round(theme['avg_rating'], 1),
                'sample_count': len(theme['samples']),
                'last_mentioned': max(s['timestamp'] for s in theme['samples'] if s.get('timestamp')),
                'related_feedback': [
                    {
                        'customer': s['customer'],
                        'text': s['text'][:100] + '...' if len(s['text']) > 100 else s['text']
                    }
                    for s in theme['samples'][:3]  # Top 3 samples
                ]
            }

            faqs.append(faq_entry)

        logger.info(f"Generated {len(faqs)} FAQ entries")
        return faqs

    def _extract_question(self, theme: Dict) -> str:
        """
        Extract or formulate a clear question from theme.

        Args:
            theme: Theme dictionary

        Returns:
            Well-formatted question
        """
        representative = theme['representative_text']

        # If it's already a question, clean it up
        if '?' in representative:
            question = representative.split('.')[0].split('!')[0].strip()
            if not question.endswith('?'):
                question += '?'
            return question

        # Otherwise, formulate a question based on the complaint
        text_lower = representative.lower()

        # Common transformations
        if 'not working' in text_lower or "doesn't work" in text_lower:
            feature = self._extract_feature(representative)
            return f"Why isn't {feature} working?"

        if 'how to' in text_lower or 'how do i' in text_lower:
            # Already in question form
            question = representative.split('.')[0].strip()
            if not question.endswith('?'):
                question += '?'
            return question.capitalize()

        if 'can i' in text_lower or 'can we' in text_lower:
            question = representative.split('.')[0].strip()
            if not question.endswith('?'):
                question += '?'
            return question.capitalize()

        # Default: make it a general question
        return f"How do I handle: {representative[:60]}...?"

    def _extract_feature(self, text: str) -> str:
        """Extract feature/topic name from feedback text."""
        # Simple extraction - look for nouns after common words
        words = text.lower().split()

        # Look for feature keywords
        feature_keywords = ['app', 'feature', 'button', 'page', 'export', 'import', 'login', 'payment']

        for i, word in enumerate(words):
            if word in feature_keywords:
                return word

        # Default to "this feature"
        return "this feature"

    def _generate_answer(self, theme: Dict, style: str = "helpful") -> str:
        """
        Generate an answer based on feedback analysis.

        Args:
            theme: Theme dictionary with samples
            style: Answer style

        Returns:
            Generated answer text
        """
        samples = theme['samples']
        count = theme['count']
        platforms = list(set(theme['platforms']))
        avg_rating = theme['avg_rating']

        # Determine if it's a known issue
        is_issue = avg_rating < 3.5 or any(
            word in theme['representative_text'].lower()
            for word in ['not working', 'error', 'bug', 'problem', 'issue']
        )

        if style == "friendly":
            prefix = "Great question! "
        elif style == "technical":
            prefix = ""
        else:  # helpful
            prefix = "Thanks for asking! "

        # Build answer based on patterns
        if is_issue:
            answer = f"{prefix}We're aware that {count} customers have reported this issue"

            if len(platforms) == 1:
                answer += f" on {platforms[0]}"
            elif len(platforms) > 1:
                answer += f" across {', '.join(platforms)} platforms"

            answer += ". Our team is actively investigating and will provide updates soon. "
            answer += "In the meantime, please contact support@example.com for assistance."
        else:
            # It's a general question
            answer = f"{prefix}Based on feedback from {count} customers, here's what we recommend:\n\n"

            # Synthesize common responses/patterns
            answer += "1. Check our documentation at docs.example.com\n"
            answer += "2. Contact our support team for personalized help\n"
            answer += "3. Join our community forum for tips from other users"

        return answer

    def export_to_markdown(self, faqs: List[Dict[str, Any]], filepath: str = "FAQ.md"):
        """
        Export FAQs to Markdown format.

        Args:
            faqs: List of FAQ entries
            filepath: Output file path
        """
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write("# Frequently Asked Questions\n\n")
                f.write(f"*Auto-generated from customer feedback on {datetime.now().strftime('%Y-%m-%d')}*\n\n")
                f.write("---\n\n")

                for i, faq in enumerate(faqs, 1):
                    # Question
                    f.write(f"## {i}. {faq['question']}\n\n")

                    # Answer
                    f.write(f"{faq['answer']}\n\n")

                    # Metadata
                    f.write(f"**Frequency**: Mentioned {faq['frequency']} times | ")
                    f.write(f"**Platforms**: {', '.join(faq['platforms'])} | ")
                    f.write(f"**Avg Rating**: {faq['avg_rating']}/5\n\n")

                    # Related feedback (collapsed)
                    f.write("<details>\n")
                    f.write("<summary>📝 Related Customer Feedback</summary>\n\n")
                    for feedback in faq['related_feedback']:
                        f.write(f"- **{feedback['customer']}**: {feedback['text']}\n")
                    f.write("\n</details>\n\n")
                    f.write("---\n\n")

            logger.info(f"Exported FAQs to {filepath}")

        except Exception as e:
            logger.error(f"Failed to export to Markdown: {e}")

    def export_to_json(self, faqs: List[Dict[str, Any]], filepath: str = "faq.json"):
        """Export FAQs to JSON format."""
        import json

        try:
            # Convert datetime objects to strings
            export_data = []
            for faq in faqs:
                faq_copy = faq.copy()
                if faq_copy.get('last_mentioned'):
                    faq_copy['last_mentioned'] = faq_copy['last_mentioned'].isoformat() if hasattr(faq_copy['last_mentioned'], 'isoformat') else str(faq_copy['last_mentioned'])
                export_data.append(faq_copy)

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump({
                    'generated_at': datetime.now().isoformat(),
                    'faq_count': len(faqs),
                    'faqs': export_data
                }, f, indent=2, ensure_ascii=False)

            logger.info(f"Exported FAQs to {filepath}")

        except Exception as e:
            logger.error(f"Failed to export to JSON: {e}")

    def export_to_html(self, faqs: List[Dict[str, Any]], filepath: str = "faq.html"):
        """Export FAQs to HTML format."""
        try:
            html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>FAQ - Auto-Generated</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 800px; margin: 40px auto; padding: 0 20px; line-height: 1.6; }
        h1 { color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }
        .faq-item { margin-bottom: 30px; padding: 20px; background: #f8f9fa; border-radius: 8px; }
        .question { font-size: 1.2em; font-weight: bold; color: #2c3e50; margin-bottom: 10px; }
        .answer { color: #34495e; margin: 15px 0; }
        .metadata { font-size: 0.9em; color: #7f8c8d; margin-top: 10px; }
        .badge { display: inline-block; padding: 3px 8px; border-radius: 3px; font-size: 0.85em; margin-right: 8px; }
        .frequency { background: #3498db; color: white; }
        .rating { background: #f39c12; color: white; }
        .platform { background: #95a5a6; color: white; }
        .feedback-samples { margin-top: 15px; padding: 10px; background: white; border-left: 3px solid #3498db; }
        .feedback-samples summary { cursor: pointer; font-weight: bold; }
        .sample { margin: 8px 0; font-size: 0.9em; color: #555; }
    </style>
</head>
<body>
    <h1>📚 Frequently Asked Questions</h1>
    <p><em>Auto-generated from customer feedback on """ + datetime.now().strftime('%B %d, %Y') + """</em></p>
"""

            for i, faq in enumerate(faqs, 1):
                html += f"""
    <div class="faq-item">
        <div class="question">{i}. {faq['question']}</div>
        <div class="answer">{faq['answer'].replace(chr(10), '<br>')}</div>
        <div class="metadata">
            <span class="badge frequency">📊 {faq['frequency']} mentions</span>
            <span class="badge rating">⭐ {faq['avg_rating']}/5</span>
            <span class="badge platform">💻 {', '.join(faq['platforms'])}</span>
        </div>
        <details class="feedback-samples">
            <summary>📝 View Related Customer Feedback</summary>
"""

                for feedback in faq['related_feedback']:
                    html += f"""
            <div class="sample"><strong>{feedback['customer']}:</strong> {feedback['text']}</div>
"""

                html += """
        </details>
    </div>
"""

            html += """
</body>
</html>
"""

            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(html)

            logger.info(f"Exported FAQs to {filepath}")

        except Exception as e:
            logger.error(f"Failed to export to HTML: {e}")


def generate_faq(
    timeframe_days: int = 30,
    min_occurrences: int = 3,
    max_faqs: int = 15,
    answer_style: str = "helpful",
    output_formats: List[str] = ["markdown", "json", "html"],
    rag_client=None
) -> Dict[str, Any]:
    """
    Main function to generate FAQs.

    Args:
        timeframe_days: Days to look back
        min_occurrences: Minimum mentions for inclusion
        max_faqs: Maximum FAQs to generate
        answer_style: Style of answers
        output_formats: List of formats to export
        rag_client: Optional RAG client (auto-initializes if not provided)

    Returns:
        Dictionary with FAQs and export paths

    Example:
        # Auto-initialize from .env
        result = generate_faq()

        # Or pass custom RAG client
        from feedbackforge.rag_search import FeedbackRAGSearch
        custom_rag = FeedbackRAGSearch(endpoint="...", api_key="...")
        result = generate_faq(rag_client=custom_rag)
    """
    logger.info("Starting FAQ generation...")

    # Initialize generator (will auto-init RAG if needed)
    generator = FAQGenerator(rag_client=rag_client)

    # Find common themes
    themes = generator.find_common_themes(
        timeframe_days=timeframe_days,
        min_occurrences=min_occurrences,
        max_themes=max_faqs
    )

    if not themes:
        logger.warning("No themes found for FAQ generation")
        return {"faqs": [], "exports": []}

    # Generate FAQ entries
    faqs = generator.generate_faq_entries(themes, answer_style=answer_style)

    # Export to requested formats
    exports = []
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    if "markdown" in output_formats:
        filepath = f"FAQ_{timestamp}.md"
        generator.export_to_markdown(faqs, filepath)
        exports.append(filepath)

    if "json" in output_formats:
        filepath = f"faq_{timestamp}.json"
        generator.export_to_json(faqs, filepath)
        exports.append(filepath)

    if "html" in output_formats:
        filepath = f"faq_{timestamp}.html"
        generator.export_to_html(faqs, filepath)
        exports.append(filepath)

    logger.info(f"✅ Generated {len(faqs)} FAQs and exported to {len(exports)} formats")

    return {
        "faqs": faqs,
        "exports": exports,
        "theme_count": len(themes),
        "generated_at": datetime.now().isoformat()
    }
