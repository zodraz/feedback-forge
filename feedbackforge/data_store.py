"""
FeedbackForge Data Store
========================

Data store for feedback items with Cosmos DB backend and in-memory fallback.
"""

import logging
import os
import random
from dataclasses import asdict
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from azure.cosmos import CosmosClient, PartitionKey, exceptions
from azure.identity import DefaultAzureCredential

from .models import FeedbackItem, SurveyResponse
from .telemetry import trace_operation

logger = logging.getLogger(__name__)


class CosmosDBFeedbackStore:
    """Cosmos DB-backed feedback data store with auto-initialization."""

    def __init__(
        self,
        endpoint: str,
        key: Optional[str] = None,
        database_name: str = "feedbackforge",
        container_name: str = "feedback"
    ):
        """
        Initialize Cosmos DB feedback store.

        Args:
            endpoint: Cosmos DB endpoint URL
            key: Optional primary key. If not provided, uses DefaultAzureCredential
            database_name: Database name
            container_name: Container name
        """
        self.endpoint = endpoint
        self.database_name = database_name
        self.container_name = container_name
        self.alerts_container_name = "alerts"
        self.faqs_container_name = "faqs"

        # Initialize client with key or DefaultAzureCredential
        if key:
            logger.info("🔑 Using primary key authentication for Cosmos DB")
            # Strip any whitespace from the key (common issue with .env files)
            key = key.strip()
            self.client = CosmosClient(endpoint, credential=key)
        else:
            logger.info("🔐 Using DefaultAzureCredential for Cosmos DB")
            credential = DefaultAzureCredential()
            self.client = CosmosClient(endpoint, credential=credential)

        # Initialize database and containers
        self._initialize_database()

        # Auto-populate mock data if empty
        self._ensure_data_exists()

    def _initialize_database(self):
        """Create database and containers if they don't exist."""
        try:
            # Create database
            self.database = self.client.create_database_if_not_exists(id=self.database_name)
            logger.info(f"✅ Database '{self.database_name}' ready")

            # Create feedback container with partition key
            # Note: Don't set offer_throughput for serverless accounts
            self.container = self.database.create_container_if_not_exists(
                id=self.container_name,
                partition_key=PartitionKey(path="/customer_segment")
            )
            logger.info(f"✅ Container '{self.container_name}' ready")

            # Create alerts container
            self.alerts_container = self.database.create_container_if_not_exists(
                id=self.alerts_container_name,
                partition_key=PartitionKey(path="/status")
            )
            logger.info(f"✅ Container '{self.alerts_container_name}' ready")

            # Create FAQs container
            self.faqs_container = self.database.create_container_if_not_exists(
                id=self.faqs_container_name,
                partition_key=PartitionKey(path="/id")
            )
            logger.info(f"✅ Container '{self.faqs_container_name}' ready")

        except exceptions.CosmosHttpResponseError as e:
            logger.error(f"Failed to initialize Cosmos DB: {e}")
            raise

    def _ensure_data_exists(self):
        """Check if data exists, if not, populate with mock data."""
        try:
            # Query to count items
            query = "SELECT VALUE COUNT(1) FROM c"
            items = list(self.container.query_items(query=query, enable_cross_partition_query=True))
            count = items[0] if items else 0

            if count == 0:
                logger.info("📊 No data found in Cosmos DB. Initializing with mock data...")
                self.load_mock_data()
                logger.info(f"✅ Initialized with {len(self._generate_mock_feedback())} mock feedback items")
            else:
                logger.info(f"✅ Found {count} existing feedback items in Cosmos DB")

        except Exception as e:
            logger.error(f"Error checking data existence: {e}")

    def _generate_mock_feedback(self) -> List[FeedbackItem]:
        """Generate realistic mock feedback data."""
        platforms = ["iOS", "Android", "Web", "Desktop"]
        versions = ["2.0.3", "2.0.2", "2.0.1", "1.9.5"]

        enterprise_customers = [
            ("ENT001", "GlobalCorp Inc"), ("ENT002", "TechGiant Ltd"),
            ("ENT003", "Acme Corporation"), ("ENT004", "MegaSystems"), ("ENT005", "DataFlow Inc"),
        ]
        smb_customers = [
            ("SMB001", "TechStart"), ("SMB002", "GrowthCo"),
            ("SMB003", "InnovateLab"), ("SMB004", "SmallBiz Pro"), ("SMB005", "LocalTech"),
        ]
        individual_customers = [
            ("IND001", "John Smith"), ("IND002", "Jane Doe"),
            ("IND003", "Bob Wilson"), ("IND004", "Alice Brown"), ("IND005", "Charlie Davis"),
        ]
        all_customers = enterprise_customers + smb_customers + individual_customers

        feedback_list = []
        feedback_id = 1
        now = datetime.now()

        # iOS crash spike (recent)
        for _ in range(47):
            customer = random.choice(all_customers)
            segment = "Enterprise" if customer[0].startswith("ENT") else ("SMB" if customer[0].startswith("SMB") else "Individual")
            feedback_list.append(FeedbackItem(
                id=f"FB{feedback_id:04d}",
                text=random.choice([
                    "App crashes every time I open settings on iOS.",
                    "iOS app crashed again. This is unacceptable!",
                    "Can't use the app on my iPhone - keeps crashing.",
                    "iOS 17 update broke the app completely.",
                ]),
                sentiment="negative", sentiment_score=-0.85,
                topics=["bugs", "mobile", "ios", "crash"],
                customer_segment=segment, customer_id=customer[0], customer_name=customer[1],
                rating=1, timestamp=now - timedelta(hours=random.randint(1, 72)),
                product_version="2.0.3", platform="iOS", is_urgent=True,
            ))
            feedback_id += 1

        # Pricing complaints (SMB)
        for _ in range(31):
            customer = random.choice(smb_customers)
            competitors = random.choice([["Competitor X"], ["Competitor Y"], ["Competitor X", "Competitor Z"]])
            feedback_list.append(FeedbackItem(
                id=f"FB{feedback_id:04d}",
                text=random.choice([
                    f"Pricing is too expensive for SMBs. {competitors[0]} offers better value.",
                    "Can't justify the cost for a small team. Need SMB pricing.",
                    f"Switching to {competitors[0]} - they have a startup plan.",
                ]),
                sentiment="negative", sentiment_score=-0.6,
                topics=["pricing", "competitive"],
                customer_segment="SMB", customer_id=customer[0], customer_name=customer[1],
                rating=2, timestamp=now - timedelta(days=random.randint(1, 30)),
                product_version=random.choice(versions), competitor_mentions=competitors,
            ))
            feedback_id += 1

        # Support complaints
        for _ in range(28):
            customer = random.choice(enterprise_customers + smb_customers)
            segment = "Enterprise" if customer[0].startswith("ENT") else "SMB"
            feedback_list.append(FeedbackItem(
                id=f"FB{feedback_id:04d}",
                text=random.choice([
                    "Support team takes too long to respond. Waited 3 days.",
                    "Still waiting for a response after 48 hours.",
                    "Enterprise support SLA not being met.",
                ]),
                sentiment="negative", sentiment_score=-0.5,
                topics=["support", "response_time"],
                customer_segment=segment, customer_id=customer[0], customer_name=customer[1],
                rating=2, timestamp=now - timedelta(days=random.randint(1, 30)),
                product_version=random.choice(versions),
            ))
            feedback_id += 1

        # Positive feedback
        positive_texts = [
            ("The product is amazing! Customer support was incredibly helpful.", ["support", "product"], 5),
            ("Love the new features! Much better than Company Y's offering.", ["features", "competitive"], 5),
            ("Excellent dashboard - exactly what we needed.", ["features", "usability"], 5),
            ("Integration was seamless, great documentation.", ["integration", "documentation"], 4),
        ]
        for _ in range(40):
            for text, topics, rating in positive_texts:
                customer = random.choice(all_customers)
                segment = "Enterprise" if customer[0].startswith("ENT") else ("SMB" if customer[0].startswith("SMB") else "Individual")
                feedback_list.append(FeedbackItem(
                    id=f"FB{feedback_id:04d}",
                    text=text, sentiment="positive", sentiment_score=0.8,
                    topics=topics, customer_segment=segment,
                    customer_id=customer[0], customer_name=customer[1],
                    rating=rating, timestamp=now - timedelta(days=random.randint(1, 30)),
                    product_version=random.choice(versions), platform=random.choice(platforms),
                ))
                feedback_id += 1

        # Checkout issues (recent outage simulation)
        for _ in range(23):
            customer = random.choice(enterprise_customers + smb_customers)
            segment = "Enterprise" if customer[0].startswith("ENT") else "SMB"
            feedback_list.append(FeedbackItem(
                id=f"FB{feedback_id:04d}",
                text=random.choice([
                    "Checkout not working! Can't complete my purchase.",
                    "Payment page returns error 500.",
                    "Credit card payment failing repeatedly.",
                ]),
                sentiment="negative", sentiment_score=-0.9,
                topics=["bugs", "checkout", "payment"],
                customer_segment=segment, customer_id=customer[0], customer_name=customer[1],
                rating=1, timestamp=now - timedelta(hours=random.randint(1, 4)),
                product_version="2.0.3", is_urgent=True,
            ))
            feedback_id += 1

        return feedback_list

    def load_mock_data(self) -> None:
        """Load mock feedback data into Cosmos DB."""
        feedback_list = self._generate_mock_feedback()

        for feedback in feedback_list:
            self._upsert_feedback(feedback)

        logger.info(f"✅ Loaded {len(feedback_list)} mock feedback items")

    def _upsert_feedback(self, feedback: FeedbackItem):
        """Insert or update a feedback item."""
        try:
            item = asdict(feedback)
            # Convert datetime to ISO string
            item['timestamp'] = feedback.timestamp.isoformat()
            self.container.upsert_item(body=item)
        except exceptions.CosmosHttpResponseError as e:
            logger.error(f"Failed to upsert feedback {feedback.id}: {e}")

    @property
    def feedback(self) -> List[FeedbackItem]:
        """Get all feedback items (for compatibility with old interface)."""
        try:
            query = "SELECT * FROM c"
            items = list(self.container.query_items(query=query, enable_cross_partition_query=True))
            return [self._item_to_feedback(item) for item in items]
        except Exception as e:
            logger.error(f"Failed to fetch feedback: {e}")
            return []

    @property
    def alerts(self) -> List[Dict[str, Any]]:
        """Get all alerts."""
        try:
            query = "SELECT * FROM c"
            return list(self.alerts_container.query_items(query=query, enable_cross_partition_query=True))
        except Exception as e:
            logger.error(f"Failed to fetch alerts: {e}")
            return []

    def _item_to_feedback(self, item: Dict) -> FeedbackItem:
        """Convert Cosmos DB item to FeedbackItem."""
        # Filter out Cosmos DB system fields (they start with underscore)
        clean_item = {k: v for k, v in item.items() if not k.startswith('_')}

        # Convert ISO string back to datetime
        if isinstance(clean_item.get('timestamp'), str):
            clean_item['timestamp'] = datetime.fromisoformat(clean_item['timestamp'])

        return FeedbackItem(**clean_item)

    @trace_operation("cosmos.get_weekly_summary")
    def get_weekly_summary(self) -> Dict[str, Any]:
        """Get summary statistics for the past week."""
        try:
            now = datetime.now()
            week_ago = now - timedelta(days=7)

            query = f"""
            SELECT * FROM c
            WHERE c.timestamp >= '{week_ago.isoformat()}'
            """
            items = list(self.container.query_items(query=query, enable_cross_partition_query=True))

            if not items:
                return {"total_responses": 0, "sentiment": {}, "top_issues": [], "urgent_count": 0}

            total = len(items)
            positive = len([i for i in items if i.get('sentiment') == "positive"])
            negative = len([i for i in items if i.get('sentiment') == "negative"])
            neutral = total - positive - negative

            # Count topics
            topic_counts: Dict[str, int] = {}
            for item in items:
                for topic in item.get('topics', []):
                    topic_counts[topic] = topic_counts.get(topic, 0) + 1

            top_issues = sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)[:5]

            return {
                "total_responses": total,
                "sentiment": {
                    "positive_pct": round(positive / total * 100),
                    "negative_pct": round(negative / total * 100),
                    "neutral_pct": round(neutral / total * 100),
                },
                "top_issues": top_issues,
                "urgent_count": len([i for i in items if i.get('is_urgent')]),
            }
        except Exception as e:
            logger.error(f"Failed to get weekly summary: {e}")
            return {"total_responses": 0, "sentiment": {}, "top_issues": [], "urgent_count": 0}

    @trace_operation("cosmos.get_issue_details")
    def get_issue_details(self, topic: str) -> Dict[str, Any]:
        """Get detailed analysis for a specific issue/topic."""
        try:
            now = datetime.now()
            week_ago = now - timedelta(days=7)

            query = f"""
            SELECT * FROM c
            WHERE ARRAY_CONTAINS(c.topics, '{topic.lower()}', true)
            AND c.timestamp >= '{week_ago.isoformat()}'
            """
            items = list(self.container.query_items(query=query, enable_cross_partition_query=True))

            if not items:
                return {"topic": topic, "total_mentions": 0, "message": "No recent data for this topic"}

            negative_pct = round(len([i for i in items if i.get('sentiment') == "negative"]) / len(items) * 100)

            versions: Dict[str, int] = {}
            platforms: Dict[str, int] = {}
            for item in items:
                version = item.get('product_version', 'Unknown')
                versions[version] = versions.get(version, 0) + 1
                platform = item.get('platform')
                if platform:
                    platforms[platform] = platforms.get(platform, 0) + 1

            priority = "P0 - Critical" if len(items) > 30 and negative_pct > 80 else \
                       "P1 - High" if len(items) > 20 and negative_pct > 60 else \
                       "P2 - Medium" if len(items) > 10 else "P3 - Low"

            return {
                "topic": topic,
                "total_mentions": len(items),
                "negative_sentiment_pct": negative_pct,
                "affected_versions": versions,
                "affected_platforms": platforms,
                "sample_feedback": [i.get('text') for i in items[:3]],
                "priority": priority,
            }
        except Exception as e:
            logger.error(f"Failed to get issue details for {topic}: {e}")
            return {"topic": topic, "error": str(e)}

    @trace_operation("cosmos.get_competitor_analysis")
    def get_competitor_analysis(self) -> Dict[str, Any]:
        """Get competitive intelligence from feedback."""
        try:
            now = datetime.now()
            month_ago = now - timedelta(days=30)

            query = f"""
            SELECT * FROM c
            WHERE c.timestamp >= '{month_ago.isoformat()}'
            AND ARRAY_LENGTH(c.competitor_mentions) > 0
            """
            items = list(self.container.query_items(query=query, enable_cross_partition_query=True))

            competitor_data: Dict[str, Dict[str, Any]] = {}
            for item in items:
                for comp in item.get('competitor_mentions', []):
                    if comp not in competitor_data:
                        competitor_data[comp] = {"mentions": 0, "reasons": {}}
                    competitor_data[comp]["mentions"] += 1
                    for topic in item.get('topics', []):
                        if topic != "competitive":
                            competitor_data[comp]["reasons"][topic] = competitor_data[comp]["reasons"].get(topic, 0) + 1

            competitors = [
                {
                    "name": name,
                    "mentions": data["mentions"],
                    "win_reason": max(data["reasons"], key=data["reasons"].get) if data["reasons"] else "Unknown"
                }
                for name, data in sorted(competitor_data.items(), key=lambda x: x[1]["mentions"], reverse=True)
            ]

            churn_risks = [
                {
                    "customer_id": item.get('customer_id'),
                    "customer_name": item.get('customer_name'),
                    "segment": item.get('customer_segment'),
                    "competitor": item.get('competitor_mentions', [])[0] if item.get('competitor_mentions') else "Unknown"
                }
                for item in items if item.get('sentiment') == "negative"
            ][:12]

            return {
                "competitors": competitors,
                "churn_risk_customers": churn_risks,
                "total_churn_risks": len(churn_risks)
            }
        except Exception as e:
            logger.error(f"Failed to get competitor analysis: {e}")
            return {"competitors": [], "churn_risk_customers": [], "total_churn_risks": 0}

    @trace_operation("cosmos.get_customer_context")
    def get_customer_context(self, customer_id: str) -> Dict[str, Any]:
        """Get context for a specific customer."""
        try:
            query = f"SELECT * FROM c WHERE c.customer_id = '{customer_id}' ORDER BY c.timestamp DESC"
            items = list(self.container.query_items(query=query, enable_cross_partition_query=True))[:5]

            if not items:
                return {"error": f"No feedback found for {customer_id}"}

            negative_count = len([i for i in items if i.get('sentiment') == "negative"])
            segment = items[0].get('customer_segment', 'Unknown')

            return {
                "customer_id": customer_id,
                "customer_name": items[0].get('customer_name', 'Unknown'),
                "segment": segment,
                "account_value": f"${random.randint(50, 150)}K ARR" if segment == "Enterprise" else f"${random.randint(5, 25)}K ARR",
                "escalation_risk": "HIGH" if negative_count >= 3 else "MEDIUM" if negative_count >= 1 else "LOW",
                "recent_feedback": [
                    {
                        "text": i.get('text'),
                        "sentiment": i.get('sentiment'),
                        "days_ago": (datetime.now() - datetime.fromisoformat(str(i.get('timestamp')))).days if i.get('timestamp') else 0
                    }
                    for i in items
                ],
            }
        except Exception as e:
            logger.error(f"Failed to get customer context for {customer_id}: {e}")
            return {"error": str(e)}

    @trace_operation("cosmos.detect_anomalies")
    def detect_anomalies(self) -> List[Dict[str, Any]]:
        """Detect unusual patterns in recent feedback."""
        try:
            now = datetime.now()
            two_hours_ago = now - timedelta(hours=2)

            query = f"""
            SELECT * FROM c
            WHERE c.timestamp >= '{two_hours_ago.isoformat()}'
            """
            items = list(self.container.query_items(query=query, enable_cross_partition_query=True))

            topic_counts: Dict[str, int] = {}
            for item in items:
                for topic in item.get('topics', []):
                    topic_counts[topic] = topic_counts.get(topic, 0) + 1

            anomalies = []
            for topic, count in topic_counts.items():
                if count > 10:
                    affected = [i for i in items if topic in i.get('topics', [])]
                    negative_count = len([i for i in affected if i.get('sentiment') == "negative"])
                    anomalies.append({
                        "topic": topic,
                        "count": count,
                        "severity": "CRITICAL" if count > 20 else "HIGH",
                        "affected_customers": len(affected),
                        "negative_pct": round(negative_count / len(affected) * 100) if affected else 0,
                    })

            return anomalies
        except Exception as e:
            logger.error(f"Failed to detect anomalies: {e}")
            return []

    @trace_operation("cosmos.set_alert")
    def set_alert(self, condition: str, threshold: float) -> Dict[str, Any]:
        """Set up an alert for monitoring."""
        try:
            alert = {
                "id": f"ALERT{datetime.now().timestamp()}",
                "condition": condition,
                "threshold": threshold,
                "status": "active",
                "created_at": datetime.now().isoformat()
            }
            self.alerts_container.create_item(body=alert)
            return alert
        except Exception as e:
            logger.error(f"Failed to set alert: {e}")
            return {"error": str(e)}

    def ingest_feedback_item(self, feedback: FeedbackItem) -> bool:
        """
        Ingest a feedback item with idempotency check.
        Returns True if ingested, False if already exists.
        """
        try:
            # Check if item already exists
            query = f"SELECT c.id FROM c WHERE c.id = '{feedback.id}'"
            existing = list(self.container.query_items(query=query, enable_cross_partition_query=True))

            if existing:
                logger.debug(f"Feedback item {feedback.id} already exists, skipping")
                return False

            # Insert new item
            self._upsert_feedback(feedback)
            logger.debug(f"Ingested new feedback item {feedback.id}")
            return True
        except Exception as e:
            logger.error(f"Failed to ingest feedback {feedback.id}: {e}")
            return False

    @trace_operation("cosmos.get_surveys")
    def get_surveys(self) -> List[SurveyResponse]:
        """Convert feedback items to SurveyResponse for workflow mode."""
        try:
            feedback_items = self.feedback
            return [
                SurveyResponse(
                    id=f.id,
                    text=f.text,
                    rating=f.rating,
                    timestamp=f.timestamp.isoformat(),
                    customer_segment=f.customer_segment,
                    product_version=f.product_version,
                    customer_id=f.customer_id,
                    customer_name=f.customer_name,
                    platform=f.platform,
                )
                for f in feedback_items
            ]
        except Exception as e:
            logger.error(f"Failed to get surveys: {e}")
            return []

    @trace_operation("cosmos.save_faq")
    def save_faq(self, faq_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Save FAQ generation result to Cosmos DB.

        Args:
            faq_data: FAQ data containing generated_at, faq_count, and faqs list

        Returns:
            Saved document with ID
        """
        try:
            # Create unique ID from timestamp
            faq_id = faq_data.get('generated_at', datetime.now().isoformat()).replace(':', '-').replace('.', '-')

            # Prepare document
            document = {
                'id': faq_id,
                'generated_at': faq_data.get('generated_at', datetime.now().isoformat()),
                'faq_count': faq_data.get('faq_count', 0),
                'theme_count': faq_data.get('theme_count', 0),
                'faqs': faq_data.get('faqs', [])
            }

            # Save to Cosmos DB
            result = self.faqs_container.upsert_item(body=document)
            logger.info(f"✅ Saved {document['faq_count']} FAQs to Cosmos DB (ID: {faq_id})")

            return result
        except exceptions.CosmosHttpResponseError as e:
            logger.error(f"Failed to save FAQs to Cosmos DB: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error saving FAQs: {e}")
            raise

    @trace_operation("cosmos.get_faqs")
    def get_faqs(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Retrieve saved FAQs from Cosmos DB.

        Args:
            limit: Maximum number of FAQ documents to return (default: 10)

        Returns:
            List of FAQ documents, sorted by generated_at (most recent first)
        """
        try:
            query = "SELECT * FROM c ORDER BY c.generated_at DESC"
            items = list(self.faqs_container.query_items(
                query=query,
                enable_cross_partition_query=True
            ))

            # Limit results
            return items[:limit] if limit else items
        except Exception as e:
            logger.error(f"Failed to retrieve FAQs from Cosmos DB: {e}")
            return []


class InMemoryFeedbackStore:
    """In-memory fallback data store."""

    def __init__(self):
        self.feedback_list: List[FeedbackItem] = []
        self.analysis_results: Optional[Dict[str, Any]] = None
        self.alerts_list: List[Dict[str, Any]] = []
        self.faqs_list: List[Dict[str, Any]] = []
        self.load_mock_data()

    def load_mock_data(self) -> None:
        """Generate realistic mock feedback data."""
        # Use the same mock data generation as Cosmos
        cosmos_store = CosmosDBFeedbackStore.__new__(CosmosDBFeedbackStore)
        self.feedback_list = cosmos_store._generate_mock_feedback()

    @property
    def feedback(self) -> List[FeedbackItem]:
        return self.feedback_list

    @property
    def alerts(self) -> List[Dict[str, Any]]:
        return self.alerts_list

    @trace_operation("memory.get_weekly_summary")
    def get_weekly_summary(self) -> Dict[str, Any]:
        """Get summary statistics for the past week."""
        now = datetime.now()
        week_ago = now - timedelta(days=7)
        weekly = [f for f in self.feedback if f.timestamp >= week_ago]
        total = len(weekly)
        if total == 0:
            return {"total_responses": 0, "sentiment": {}, "top_issues": [], "urgent_count": 0}

        positive = len([f for f in weekly if f.sentiment == "positive"])
        negative = len([f for f in weekly if f.sentiment == "negative"])
        neutral = total - positive - negative

        topic_counts: Dict[str, int] = {}
        for f in weekly:
            for t in f.topics:
                topic_counts[t] = topic_counts.get(t, 0) + 1
        top_issues: List[tuple[str, int]] = sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)[:5]

        return {
            "total_responses": total,
            "sentiment": {
                "positive_pct": round(positive / total * 100),
                "negative_pct": round(negative / total * 100),
                "neutral_pct": round(neutral / total * 100),
            },
            "top_issues": top_issues,
            "urgent_count": len([f for f in weekly if f.is_urgent]),
        }

    def get_issue_details(self, topic: str) -> Dict[str, Any]:
        """Get detailed analysis for a specific issue/topic."""
        now = datetime.now()
        week_ago = now - timedelta(days=7)
        relevant = [f for f in self.feedback if topic.lower() in [t.lower() for t in f.topics]]
        recent = [f for f in relevant if f.timestamp >= week_ago]

        if not recent:
            return {"topic": topic, "total_mentions": 0, "message": "No recent data for this topic"}

        negative_pct = round(len([f for f in recent if f.sentiment == "negative"]) / len(recent) * 100)
        versions: Dict[str, int] = {}
        platforms: Dict[str, int] = {}
        for f in recent:
            versions[f.product_version] = versions.get(f.product_version, 0) + 1
            if f.platform:
                platforms[f.platform] = platforms.get(f.platform, 0) + 1

        priority = "P0 - Critical" if len(recent) > 30 and negative_pct > 80 else \
                   "P1 - High" if len(recent) > 20 and negative_pct > 60 else \
                   "P2 - Medium" if len(recent) > 10 else "P3 - Low"

        return {
            "topic": topic, "total_mentions": len(recent), "negative_sentiment_pct": negative_pct,
            "affected_versions": versions, "affected_platforms": platforms,
            "sample_feedback": [f.text for f in recent[:3]], "priority": priority,
        }

    def get_competitor_analysis(self) -> Dict[str, Any]:
        """Get competitive intelligence from feedback."""
        now = datetime.now()
        month_ago = now - timedelta(days=30)
        recent = [f for f in self.feedback if f.timestamp >= month_ago]

        competitor_data: Dict[str, Dict[str, Any]] = {}
        for f in recent:
            for comp in f.competitor_mentions:
                if comp not in competitor_data:
                    competitor_data[comp] = {"mentions": 0, "reasons": {}}
                competitor_data[comp]["mentions"] += 1
                for t in f.topics:
                    if t != "competitive":
                        competitor_data[comp]["reasons"][t] = competitor_data[comp]["reasons"].get(t, 0) + 1

        competitors = [
            {"name": name, "mentions": data["mentions"],
             "win_reason": max(data["reasons"], key=data["reasons"].get) if data["reasons"] else "Unknown"}
            for name, data in sorted(competitor_data.items(), key=lambda x: x[1]["mentions"], reverse=True)
        ]

        churn_risks = [
            {"customer_id": f.customer_id, "customer_name": f.customer_name, "segment": f.customer_segment,
             "competitor": f.competitor_mentions[0] if f.competitor_mentions else "Unknown"}
            for f in recent if f.competitor_mentions and f.sentiment == "negative"
        ][:12]

        return {"competitors": competitors, "churn_risk_customers": churn_risks, "total_churn_risks": len(churn_risks)}

    def get_customer_context(self, customer_id: str) -> Dict[str, Any]:
        """Get context for a specific customer."""
        customer_feedback = sorted([f for f in self.feedback if f.customer_id == customer_id],
                                   key=lambda x: x.timestamp, reverse=True)
        if not customer_feedback:
            return {"error": f"No feedback found for {customer_id}"}

        recent = customer_feedback[:5]
        negative_count = len([f for f in recent if f.sentiment == "negative"])
        segment = recent[0].customer_segment

        return {
            "customer_id": customer_id, "customer_name": recent[0].customer_name, "segment": segment,
            "account_value": f"${random.randint(50, 150)}K ARR" if segment == "Enterprise" else f"${random.randint(5, 25)}K ARR",
            "escalation_risk": "HIGH" if negative_count >= 3 else "MEDIUM" if negative_count >= 1 else "LOW",
            "recent_feedback": [{"text": f.text, "sentiment": f.sentiment, "days_ago": (datetime.now() - f.timestamp).days} for f in recent],
        }

    def detect_anomalies(self) -> List[Dict[str, Any]]:
        """Detect unusual patterns in recent feedback."""
        now = datetime.now()
        two_hours_ago = now - timedelta(hours=2)
        recent = [f for f in self.feedback if f.timestamp >= two_hours_ago]

        topic_counts: Dict[str, int] = {}
        for f in recent:
            for t in f.topics:
                topic_counts[t] = topic_counts.get(t, 0) + 1

        anomalies: List[Dict[str, Any]] = []
        for topic, count in topic_counts.items():
            if count > 10:
                affected = [f for f in recent if topic in f.topics]
                anomalies.append({
                    "topic": topic, "count": count,
                    "severity": "CRITICAL" if count > 20 else "HIGH",
                    "affected_customers": len(affected),
                    "negative_pct": round(len([f for f in affected if f.sentiment == "negative"]) / len(affected) * 100),
                })
        return anomalies

    def set_alert(self, condition: str, threshold: float) -> Dict[str, Any]:
        """Set up an alert for monitoring."""
        alert = {"id": f"ALERT{len(self.alerts) + 1:03d}", "condition": condition, "threshold": threshold, "status": "active"}
        self.alerts_list.append(alert)
        return alert

    def ingest_feedback_item(self, feedback: FeedbackItem) -> bool:
        """
        Ingest a feedback item with idempotency check.
        Returns True if ingested, False if already exists.
        """
        # Check if item already exists
        if any(f.id == feedback.id for f in self.feedback_list):
            logger.debug(f"Feedback item {feedback.id} already exists, skipping")
            return False

        # Add new item
        self.feedback_list.append(feedback)
        logger.debug(f"Ingested new feedback item {feedback.id}")
        return True

    def get_surveys(self) -> List[SurveyResponse]:
        """Convert feedback items to SurveyResponse for workflow mode."""
        return [
            SurveyResponse(
                id=f.id,
                text=f.text,
                rating=f.rating,
                timestamp=f.timestamp.isoformat(),
                customer_segment=f.customer_segment,
                product_version=f.product_version,
                customer_id=f.customer_id,
                customer_name=f.customer_name,
                platform=f.platform,
            )
            for f in self.feedback
        ]

    def save_faq(self, faq_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Save FAQ generation result to in-memory storage.

        Args:
            faq_data: FAQ data containing generated_at, faq_count, and faqs list

        Returns:
            Saved document with ID
        """
        try:
            # Create unique ID from timestamp
            faq_id = faq_data.get('generated_at', datetime.now().isoformat()).replace(':', '-').replace('.', '-')

            # Prepare document
            document = {
                'id': faq_id,
                'generated_at': faq_data.get('generated_at', datetime.now().isoformat()),
                'faq_count': faq_data.get('faq_count', 0),
                'theme_count': faq_data.get('theme_count', 0),
                'faqs': faq_data.get('faqs', [])
            }

            # Save to in-memory list
            self.faqs_list.append(document)
            logger.info(f"✅ Saved {document['faq_count']} FAQs to in-memory storage (ID: {faq_id})")

            return document
        except Exception as e:
            logger.error(f"Unexpected error saving FAQs: {e}")
            raise

    def get_faqs(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Retrieve saved FAQs from in-memory storage.

        Args:
            limit: Maximum number of FAQ documents to return (default: 10)

        Returns:
            List of FAQ documents, sorted by generated_at (most recent first)
        """
        try:
            # Sort by generated_at descending
            sorted_faqs = sorted(
                self.faqs_list,
                key=lambda x: x.get('generated_at', ''),
                reverse=True
            )
            logger.info(f"Retrieved {len(sorted_faqs)} FAQs from in-memory storage")

            # Limit results
            return sorted_faqs[:limit] if limit else sorted_faqs
        except Exception as e:
            logger.error(f"Failed to retrieve FAQs from in-memory storage: {e}")
            return []


# Initialize global data store
def create_feedback_store():
    """Create feedback store with Cosmos DB or fall back to in-memory."""
    cosmos_endpoint = os.environ.get("COSMOS_DB_ENDPOINT")
    cosmos_key = os.environ.get("COSMOS_DB_KEY")  # Primary key (optional)
    auth_method = os.environ.get("COSMOS_DB_AUTH_METHOD", "auto").lower()

    if cosmos_endpoint:
        try:
            logger.info("🚀 Initializing Cosmos DB feedback store...")

            # Determine which credential to use based on auth_method
            if auth_method == "default_credential":
                # Force DefaultAzureCredential
                logger.info("🔐 Auth method: DefaultAzureCredential (forced by COSMOS_DB_AUTH_METHOD)")
                key_to_use = None
            elif auth_method == "primary_key":
                # Force primary key
                if not cosmos_key:
                    raise ValueError("COSMOS_DB_AUTH_METHOD=primary_key but COSMOS_DB_KEY is not set")
                logger.info("🔑 Auth method: Primary key (forced by COSMOS_DB_AUTH_METHOD)")
                key_to_use = cosmos_key
            else:
                # Auto mode: use key if provided, otherwise DefaultAzureCredential
                logger.info("⚙️ Auth method: Auto (will use key if set, otherwise DefaultAzureCredential)")
                key_to_use = cosmos_key

            store = CosmosDBFeedbackStore(
                endpoint=cosmos_endpoint,
                key=key_to_use,
                database_name=os.environ.get("COSMOS_DB_DATABASE", "feedbackforge"),
                container_name=os.environ.get("COSMOS_DB_CONTAINER", "feedback")
            )
            logger.info("✅ Using Cosmos DB for feedback storage")
            return store
        except Exception as e:
            logger.error(f"⚠️ Failed to initialize Cosmos DB: {type(e).__name__}: {e}")
            logger.error(f"   Endpoint: {cosmos_endpoint}")
            logger.error(f"   Auth method: {auth_method}")
            if "padding" in str(e).lower():
                logger.error("   💡 Hint: The COSMOS_DB_KEY may have invalid characters or whitespace.")
                logger.error("   Try: 1) Copy the key again from Azure Portal")
                logger.error("        2) Ensure no extra spaces in .env file")
                logger.error("        3) Or use COSMOS_DB_AUTH_METHOD=default_credential with 'az login'")
            logger.warning("   Falling back to in-memory storage (data will not persist across restarts)")
            return InMemoryFeedbackStore()
    else:
        logger.info("ℹ️ COSMOS_DB_ENDPOINT not set. Using in-memory feedback storage.")
        return InMemoryFeedbackStore()


# Global data store instance
feedback_store = create_feedback_store()
