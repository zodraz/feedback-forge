"""
RAG Setup and Indexing Utilities
=================================

Manages Azure AI Search index creation and feedback data indexing.
"""

import logging
import os
from dataclasses import asdict
from typing import Optional, TYPE_CHECKING, cast

if TYPE_CHECKING:
    from .rag_search import FeedbackRAGSearch

from .data_store import feedback_store
from .rag_tools import get_embeddings

logger = logging.getLogger(__name__)


class RAGSetup:
    """Manages RAG search index setup and data indexing."""

    # Class-level type annotations for instance variables
    search_endpoint: str
    search_key: Optional[str]
    index_name: str
    embedding_dimensions: int
    _rag_client: Optional["FeedbackRAGSearch"]

    def __init__(
        self,
        search_endpoint: Optional[str] = None,
        search_key: Optional[str] = None,
        index_name: Optional[str] = None,
        embedding_dimensions: int = 1536
    ):
        """Initialize RAG setup manager.

        Args:
            search_endpoint: Azure AI Search endpoint (from env if not provided)
            search_key: Azure AI Search key (from env if not provided)
            index_name: Index name (default: feedback-index)
            embedding_dimensions: Vector embedding dimensions (default: 1536)
        """
        # Get values from parameters or environment
        endpoint = search_endpoint or os.environ.get("AZURE_SEARCH_ENDPOINT")
        if not endpoint:
            raise ValueError("AZURE_SEARCH_ENDPOINT not set. Please configure environment variables.")

        # Assign to instance variables (types declared at class level)
        # Use cast() to narrow type after validation
        self.search_endpoint = cast(str, endpoint)
        self.search_key = search_key or os.environ.get("AZURE_SEARCH_KEY")
        # Ensure index_name is always a string with fallback
        self.index_name = cast(str, index_name or os.environ.get("AZURE_SEARCH_INDEX_NAME") or "feedback-index")
        self.embedding_dimensions = embedding_dimensions
        self._rag_client = None

    @property
    def rag_client(self) -> "FeedbackRAGSearch":
        """Get or create RAG client instance."""
        if not self._rag_client:
            from .rag_search import FeedbackRAGSearch
            self._rag_client = FeedbackRAGSearch(
                search_endpoint=self.search_endpoint,
                index_name=self.index_name,
                api_key=self.search_key
            )
        return self._rag_client

    def index_exists(self) -> bool:
        """Check if the search index exists.

        Returns:
            True if index exists, False otherwise
        """
        try:
            # Try to get the index
            self.rag_client.index_client.get_index(self.index_name)
            return True
        except Exception:
            return False

    def is_data_indexed(self) -> bool:
        """Check if data is already indexed.

        Returns:
            True if index has documents, False otherwise
        """
        try:
            # Try a simple search to check if index has data
            results = self.rag_client.search_client.search(
                search_text="*",
                top=1
            )
            # Check if any results exist
            for _ in results:
                return True
            return False
        except Exception:
            return False

    def ensure_index_exists(self) -> None:
        """Create the index if it doesn't exist."""
        if self.index_exists():
            logger.info(f"✅ Index '{self.index_name}' already exists")
            return

        logger.info(f"🔧 Creating index '{self.index_name}'...")
        try:
            self.rag_client.create_index(embedding_dimensions=self.embedding_dimensions)
            logger.info(f"✅ Index '{self.index_name}' created successfully!")
        except Exception as e:
            logger.error(f"❌ Failed to create index: {e}")
            raise

    def ensure_data_indexed(self, force: bool = False) -> None:
        """Index feedback data if not already indexed.

        Args:
            force: If True, re-index data even if already indexed
        """
        if not force and self.is_data_indexed():
            logger.info("✅ Data already indexed")
            return

        logger.info("📊 Loading feedback data from store...")

        # Get all feedback items
        feedback_items = feedback_store.feedback

        if not feedback_items:
            logger.warning("⚠️ No feedback data found in store")
            return

        logger.info(f"Found {len(feedback_items)} feedback items to index")

        # Convert to dictionaries
        feedback_dicts = []
        for item in feedback_items:
            item_dict = asdict(item)
            # Convert datetime to ISO string with timezone (Azure Search requires timezone)
            if item_dict.get('timestamp'):
                ts = item_dict['timestamp']
                if isinstance(ts, str):
                    # Already a string, ensure it has timezone
                    if not ts.endswith('Z') and '+' not in ts and ts.count(':') == 2:
                        ts += 'Z'
                    item_dict['timestamp'] = ts
                else:
                    # datetime object - add UTC timezone if naive
                    from datetime import timezone
                    if ts.tzinfo is None:
                        ts = ts.replace(tzinfo=timezone.utc)
                    item_dict['timestamp'] = ts.isoformat()
            feedback_dicts.append(item_dict)

        logger.info("🔄 Generating embeddings and indexing...")
        logger.info("⏳ This may take several minutes for large datasets...")

        try:
            # Index with embeddings
            self.rag_client.index_feedback(
                feedback_items=feedback_dicts,
                get_embeddings_func=get_embeddings
            )
            logger.info(f"✅ Successfully indexed {len(feedback_dicts)} feedback items!")
        except Exception as e:
            logger.error(f"❌ Failed to index feedback: {e}")
            raise

    def setup(self, force_reindex: bool = False) -> "FeedbackRAGSearch":
        """Perform complete RAG setup: create index and index data.

        Args:
            force_reindex: If True, re-index data even if already indexed

        Returns:
            Configured FeedbackRAGSearch client
        """
        logger.info("=" * 70)
        logger.info("FeedbackForge RAG Setup")
        logger.info("=" * 70)

        # Step 1: Ensure index exists
        logger.info("\n📋 Step 1: Ensuring search index exists...")
        self.ensure_index_exists()

        # Step 2: Ensure data is indexed
        logger.info("\n📋 Step 2: Ensuring feedback data is indexed...")
        self.ensure_data_indexed(force=force_reindex)

        logger.info("\n" + "=" * 70)
        logger.info("✅ RAG setup completed successfully!")
        logger.info("=" * 70)

        return self.rag_client


# Convenience function for simple setup
def setup_rag() -> Optional["FeedbackRAGSearch"]:
    """Quick setup function that creates index and indexes data if needed.

    Returns:
        FeedbackRAGSearch client or None if setup fails
    """
    try:
        setup = RAGSetup()
        return setup.setup()
    except ValueError as e:
        logger.warning(f"⚠️ RAG setup skipped: {e}")
        return None
    except Exception as e:
        logger.error(f"❌ RAG setup failed: {e}")
        return None
