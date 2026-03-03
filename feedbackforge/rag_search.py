"""
FeedbackForge RAG with Azure AI Search
=======================================

Provides semantic search and retrieval augmented generation (RAG) capabilities
for feedback data using Azure AI Search with vector embeddings.
"""

import logging
import os
from typing import Any, Dict, List, Optional
from datetime import datetime

from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchIndex,
    SimpleField,
    SearchableField,
    SearchField,
    SearchFieldDataType,
    VectorSearch,
    HnswAlgorithmConfiguration,
    HnswParameters,
    VectorSearchProfile,
    SemanticConfiguration,
    SemanticField,
    SemanticPrioritizedFields,
    SemanticSearch,
)
from azure.search.documents.models import VectorizedQuery
from azure.core.credentials import AzureKeyCredential
from azure.identity import DefaultAzureCredential

logger = logging.getLogger(__name__)


class FeedbackRAGSearch:
    """Azure AI Search integration for RAG over feedback data."""

    def __init__(
        self,
        search_endpoint: str,
        index_name: str = "feedback-index",
        api_key: Optional[str] = None,
        embedding_model: str = "text-embedding-3-small"
    ):
        """
        Initialize Azure AI Search client.

        Args:
            search_endpoint: Azure AI Search endpoint URL
            index_name: Name of the search index
            api_key: API key (optional, uses DefaultAzureCredential if not provided)
            embedding_model: Azure OpenAI embedding model to use
        """
        self.search_endpoint = search_endpoint
        self.index_name = index_name
        self.embedding_model = embedding_model

        # Initialize credentials
        if api_key:
            credential = AzureKeyCredential(api_key)
            logger.info("🔑 Using API key authentication for Azure AI Search")
        else:
            credential = DefaultAzureCredential()
            logger.info("🔐 Using DefaultAzureCredential for Azure AI Search")

        # Initialize clients
        self.index_client = SearchIndexClient(
            endpoint=search_endpoint,
            credential=credential
        )
        self.search_client = SearchClient(
            endpoint=search_endpoint,
            index_name=index_name,
            credential=credential
        )

        logger.info(f"✅ Azure AI Search client initialized for index: {index_name}")

    def create_index(self, embedding_dimensions: int = 1536):
        """
        Create the feedback search index with vector and semantic search capabilities.

        Args:
            embedding_dimensions: Dimensionality of embeddings (1536 for text-embedding-3-small)
        """
        try:
            # Define index fields
            fields = [
                SimpleField(name="id", type=SearchFieldDataType.String, key=True, filterable=True),
                SearchableField(name="text", type=SearchFieldDataType.String, analyzer_name="en.microsoft"),
                SearchableField(name="sentiment", type=SearchFieldDataType.String, filterable=True, facetable=True),
                SimpleField(name="sentiment_score", type=SearchFieldDataType.Double, filterable=True, sortable=True),
                SearchField(name="topics", type=SearchFieldDataType.Collection(SearchFieldDataType.String), filterable=True, facetable=True),
                SimpleField(name="customer_segment", type=SearchFieldDataType.String, filterable=True, facetable=True),
                SimpleField(name="customer_id", type=SearchFieldDataType.String, filterable=True),
                SearchableField(name="customer_name", type=SearchFieldDataType.String),
                SimpleField(name="rating", type=SearchFieldDataType.Int32, filterable=True, sortable=True),
                SimpleField(name="timestamp", type=SearchFieldDataType.DateTimeOffset, filterable=True, sortable=True),
                SearchableField(name="product_version", type=SearchFieldDataType.String, filterable=True, facetable=True),
                SearchableField(name="platform", type=SearchFieldDataType.String, filterable=True, facetable=True),
                SimpleField(name="is_urgent", type=SearchFieldDataType.Boolean, filterable=True),
                SearchField(name="competitor_mentions", type=SearchFieldDataType.Collection(SearchFieldDataType.String), filterable=True),
                # Vector field for semantic search
                SearchField(
                    name="text_vector",
                    type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
                    searchable=True,
                    vector_search_dimensions=embedding_dimensions,
                    vector_search_profile_name="feedback-vector-profile"
                ),
            ]

            # Configure vector search
            vector_search = VectorSearch(
                algorithms=[
                    HnswAlgorithmConfiguration(
                        name="feedback-hnsw",
                        parameters=HnswParameters(
                            m=4,
                            ef_construction=400,
                            ef_search=500,
                            metric="cosine"
                        )
                    )
                ],
                profiles=[
                    VectorSearchProfile(
                        name="feedback-vector-profile",
                        algorithm_configuration_name="feedback-hnsw"
                    )
                ]
            )

            # Configure semantic search
            semantic_config = SemanticConfiguration(
                name="feedback-semantic-config",
                prioritized_fields=SemanticPrioritizedFields(
                    title_field=SemanticField(field_name="id"),
                    content_fields=[SemanticField(field_name="text")],
                    keywords_fields=[
                        SemanticField(field_name="topics"),
                        SemanticField(field_name="sentiment"),
                        SemanticField(field_name="platform")
                    ]
                )
            )

            semantic_search = SemanticSearch(configurations=[semantic_config])

            # Create index
            index = SearchIndex(
                name=self.index_name,
                fields=fields,
                vector_search=vector_search,
                semantic_search=semantic_search
            )

            self.index_client.create_or_update_index(index)
            logger.info(f"✅ Created search index: {self.index_name}")

        except Exception as e:
            logger.error(f"Failed to create search index: {e}")
            raise

    def index_feedback(self, feedback_items: List[Dict[str, Any]], get_embeddings_func):
        """
        Index feedback items with embeddings.

        Args:
            feedback_items: List of feedback item dictionaries
            get_embeddings_func: Function that takes text and returns embeddings
                                 Example: lambda text: openai.embeddings.create(input=text, model="...").data[0].embedding
        """
        try:
            documents = []
            for idx, item in enumerate(feedback_items):
                # Get embedding for the feedback text
                embedding = get_embeddings_func(item.get("text", ""))

                # Validate embedding is a flat list of numbers
                if embedding and isinstance(embedding, list) and len(embedding) > 0:
                    if isinstance(embedding[0], list):
                        # Nested array - flatten it
                        logger.warning(f"⚠️ Flattening nested embedding for item {item.get('id')}")
                        embedding = embedding[0]

                # Prepare document with type validation
                # Ensure topics and competitor_mentions are lists (Collection fields)
                topics = item.get("topics", [])
                if topics is None:
                    topics = []
                elif not isinstance(topics, list):
                    topics = [topics]
                # Ensure all items in topics are strings
                topics = [str(t) for t in topics if t is not None]

                competitor_mentions = item.get("competitor_mentions", [])
                if competitor_mentions is None:
                    competitor_mentions = []
                elif not isinstance(competitor_mentions, list):
                    competitor_mentions = [competitor_mentions]
                # Ensure all items are strings
                competitor_mentions = [str(c) for c in competitor_mentions if c is not None]

                # Helper function to ensure single value (not array)
                def ensure_single_value(value, default=None):
                    if isinstance(value, list):
                        return value[0] if value else default
                    return value if value is not None else default

                # Ensure ALL string fields are not lists
                doc_id = ensure_single_value(item.get("id"))
                text = ensure_single_value(item.get("text"))
                sentiment = ensure_single_value(item.get("sentiment"))
                customer_segment = ensure_single_value(item.get("customer_segment"))
                customer_id = ensure_single_value(item.get("customer_id"))
                customer_name = ensure_single_value(item.get("customer_name"))
                product_version = ensure_single_value(item.get("product_version"))
                platform = ensure_single_value(item.get("platform"))

                # Numeric fields
                rating = ensure_single_value(item.get("rating"))
                if rating is not None:
                    rating = int(rating)

                sentiment_score = ensure_single_value(item.get("sentiment_score"), 0.0)
                if sentiment_score is not None:
                    sentiment_score = float(sentiment_score)

                # Boolean field
                is_urgent = ensure_single_value(item.get("is_urgent"), False)
                if not isinstance(is_urgent, bool):
                    is_urgent = bool(is_urgent)

                # Timestamp field
                timestamp = ensure_single_value(item.get("timestamp"))
                if timestamp is not None and not isinstance(timestamp, str):
                    timestamp = str(timestamp)

                doc = {
                    "id": doc_id,
                    "text": text,
                    "sentiment": sentiment,
                    "sentiment_score": sentiment_score,
                    "topics": topics,
                    "customer_segment": customer_segment,
                    "customer_id": customer_id,
                    "customer_name": customer_name,
                    "rating": rating,
                    "timestamp": timestamp,
                    "product_version": product_version,
                    "platform": platform,
                    "is_urgent": is_urgent,
                    "competitor_mentions": competitor_mentions,
                    "text_vector": embedding,
                }

                # Validate the final document structure
                # Check each field to ensure proper types
                for key, value in doc.items():
                    if key in ['topics', 'competitor_mentions', 'text_vector']:
                        # These should be lists
                        if not isinstance(value, list):
                            logger.error(f"❌ Field '{key}' should be a list but is {type(value)}: {value}")
                            raise ValueError(f"Collection field '{key}' must be a list, got {type(value)}")
                    elif key in ['rating', 'sentiment_score']:
                        # These should be numbers
                        if value is not None and not isinstance(value, (int, float)):
                            logger.error(f"❌ Field '{key}' should be numeric but is {type(value)}: {value}")
                            raise ValueError(f"Numeric field '{key}' must be int or float, got {type(value)}")
                    elif key == 'is_urgent':
                        # This should be boolean
                        if not isinstance(value, bool):
                            logger.error(f"❌ Field '{key}' should be bool but is {type(value)}: {value}")
                            raise ValueError(f"Boolean field '{key}' must be bool, got {type(value)}")
                    else:
                        # All other fields should be strings or None
                        if value is not None and isinstance(value, list):
                            logger.error(f"❌ Field '{key}' should NOT be a list but is: {value}")
                            raise ValueError(f"Primitive field '{key}' must not be a list, got {type(value)}")

                # Debug logging for first item
                if idx == 0:
                    logger.info(f"✅ Sample document validated: id={doc['id']}, "
                               f"topics={len(topics)} items, "
                               f"rating={rating}, "
                               f"timestamp={timestamp}, "
                               f"embedding={len(embedding) if embedding else 0} dims")

                documents.append(doc)

            # Upload documents in batches
            batch_size = 100
            for i in range(0, len(documents), batch_size):
                batch = documents[i:i + batch_size]
                try:
                    result = self.search_client.upload_documents(documents=batch)
                    logger.info(f"Indexed {len(batch)} feedback items (batch {i // batch_size + 1})")
                except Exception as batch_error:
                    logger.error(f"Failed to index batch {i // batch_size + 1}: {batch_error}")
                    # Log the structure of the first doc in the failed batch for debugging
                    if batch:
                        sample_doc = batch[0]
                        logger.error(f"Sample doc from failed batch: {sample_doc.get('id')}")
                        for key, value in sample_doc.items():
                            if key != 'text_vector':  # Skip large embedding array
                                logger.error(f"  {key}: {type(value).__name__} = {value}")
                    raise

            logger.info(f"✅ Successfully indexed {len(documents)} feedback items")

        except Exception as e:
            logger.error(f"Failed to index feedback: {e}")
            raise

    def semantic_search(
        self,
        query: str,
        top: int = 5,
        filters: Optional[str] = None,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Perform semantic search (keyword-based with semantic ranking).

        Args:
            query: Search query text
            top: Number of results to return
            filters: OData filter expression (e.g., "sentiment eq 'negative' and rating le 2")
            **kwargs: Additional search parameters

        Returns:
            List of search results with relevance scores
        """
        try:
            results = self.search_client.search(
                search_text=query,
                top=top,
                filter=filters,
                query_type="semantic",
                semantic_configuration_name="feedback-semantic-config",
                **kwargs
            )

            items = []
            for result in results:
                item = dict(result)
                # Add reranker score if available
                if hasattr(result, '@search.reranker_score'):
                    item['reranker_score'] = result['@search.reranker_score']
                if hasattr(result, '@search.score'):
                    item['search_score'] = result['@search.score']
                items.append(item)

            logger.info(f"Semantic search for '{query}' returned {len(items)} results")
            return items

        except Exception as e:
            logger.error(f"Semantic search failed: {e}")
            return []

    def vector_search(
        self,
        query: str,
        get_embeddings_func,
        top: int = 5,
        filters: Optional[str] = None,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Perform vector similarity search.

        Args:
            query: Search query text
            get_embeddings_func: Function to generate query embedding
            top: Number of results to return
            filters: OData filter expression
            **kwargs: Additional search parameters

        Returns:
            List of search results with similarity scores
        """
        try:
            # Generate query embedding
            query_vector = get_embeddings_func(query)

            # Perform vector search
            results = self.search_client.search(
                search_text=None,
                vector_queries=[
                    VectorizedQuery(
                        vector=query_vector,
                        k=top,
                        fields="text_vector"
                    )
                ],
                filter=filters,
                **kwargs
            )

            items = []
            for result in results:
                item = dict(result)
                if hasattr(result, '@search.score'):
                    item['similarity_score'] = result['@search.score']
                items.append(item)

            logger.info(f"Vector search for '{query}' returned {len(items)} results")
            return items

        except Exception as e:
            logger.error(f"Vector search failed: {e}")
            return []

    def hybrid_search(
        self,
        query: str,
        get_embeddings_func,
        top: int = 5,
        filters: Optional[str] = None,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Perform hybrid search (combines keyword, vector, and semantic ranking).

        This provides the best results by combining multiple search techniques.

        Args:
            query: Search query text
            get_embeddings_func: Function to generate query embedding
            top: Number of results to return
            filters: OData filter expression
            **kwargs: Additional search parameters

        Returns:
            List of search results with hybrid scores
        """
        try:
            # Generate query embedding
            query_vector = get_embeddings_func(query)

            # Perform hybrid search
            results = self.search_client.search(
                search_text=query,
                vector_queries=[
                    VectorizedQuery(
                        vector=query_vector,
                        k=top * 2,  # Retrieve more for reranking
                        fields="text_vector"
                    )
                ],
                filter=filters,
                query_type="semantic",
                semantic_configuration_name="feedback-semantic-config",
                top=top,
                **kwargs
            )

            items = []
            for result in results:
                item = dict(result)
                # Collect all available scores
                if hasattr(result, '@search.score'):
                    item['search_score'] = result['@search.score']
                if hasattr(result, '@search.reranker_score'):
                    item['reranker_score'] = result['@search.reranker_score']
                items.append(item)

            logger.info(f"Hybrid search for '{query}' returned {len(items)} results")
            return items

        except Exception as e:
            logger.error(f"Hybrid search failed: {e}")
            return []

    def get_facets(self, facet_fields: List[str]) -> Dict[str, List[Dict]]:
        """
        Get facet counts for specified fields.

        Args:
            facet_fields: List of field names to get facets for

        Returns:
            Dictionary mapping field names to facet counts
        """
        try:
            results = self.search_client.search(
                search_text="*",
                facets=facet_fields,
                top=0  # Only need facets, not documents
            )

            # get_facets() is a method that returns Optional[Dict]
            facets_result = results.get_facets()
            facets = facets_result if facets_result is not None else {}

            logger.info(f"Retrieved facets for {len(facet_fields)} fields")
            return facets

        except Exception as e:
            logger.error(f"Failed to get facets: {e}")
            return {}


def create_rag_search_client() -> Optional[FeedbackRAGSearch]:
    """
    Create RAG search client from environment variables.

    Environment Variables:
        AZURE_SEARCH_ENDPOINT: Azure AI Search endpoint
        AZURE_SEARCH_API_KEY: API key (optional, uses DefaultAzureCredential if not set)
        AZURE_SEARCH_INDEX_NAME: Index name (default: feedback-index)

    Returns:
        FeedbackRAGSearch instance or None if not configured
    """
    search_endpoint = os.environ.get("AZURE_SEARCH_ENDPOINT")

    if not search_endpoint:
        logger.info("ℹ️ Azure AI Search not configured. Set AZURE_SEARCH_ENDPOINT to enable RAG.")
        return None

    try:
        search_key = os.environ.get("AZURE_SEARCH_API_KEY")
        index_name = os.environ.get("AZURE_SEARCH_INDEX_NAME", "feedback-index")

        rag_client = FeedbackRAGSearch(
            search_endpoint=search_endpoint,
            index_name=index_name,
            api_key=search_key
        )

        logger.info("✅ RAG search client created successfully")
        return rag_client

    except Exception as e:
        logger.warning(f"⚠️ Failed to create RAG search client: {e}")
        return None


# Global RAG client instance
rag_search_client: Optional[FeedbackRAGSearch] = None


def init_rag_search():
    """Initialize global RAG search client."""
    global rag_search_client
    if not rag_search_client:
        rag_search_client = create_rag_search_client()
    return rag_search_client
