# FeedbackForge - Improvement Plan & Suggestions

This document provides detailed analysis and actionable suggestions for improving FeedbackForge.

## Table of Contents

1. [Critical Security Issues](#critical-security-issues)
2. [Code Quality Improvements](#code-quality-improvements)
3. [Architecture Enhancements](#architecture-enhancements)
4. [Feature Additions](#feature-additions)
5. [Testing Strategy](#testing-strategy)
6. [Deployment & Operations](#deployment--operations)
7. [Performance Optimizations](#performance-optimizations)

---

## Critical Security Issues

### 🔴 Issue 1: Hardcoded API Credentials

**Location**: `src/feedbackforge/dashboard_agent.py:106-109`

**Problem**:
```python
apim_resource_gateway_url="https://apim-4v5u3tvfuhuo4.azure-api.net/"
inference_api_path="inference"
api_key="0d5695acb9a14a0da0064a604181e667"  # ⚠️ EXPOSED CREDENTIAL
inference_api_version="2025-11-13"
```

**Impact**:
- Security breach: API key exposed in source code
- If committed to public repository, immediate compromise
- Violation of security best practices

**Solution**:
```python
# In .env file:
AZURE_API_GATEWAY_ENDPOINT=https://apim-4v5u3tvfuhuo4.azure-api.net/inference
AZURE_API_GATEWAY_KEY=<secure-key-here>
AZURE_INFERENCE_API_VERSION=2025-11-13

# In code:
import os
from dotenv import load_dotenv

load_dotenv()

apim_endpoint = os.environ["AZURE_API_GATEWAY_ENDPOINT"]
api_key = os.environ["AZURE_API_GATEWAY_KEY"]
api_version = os.environ.get("AZURE_INFERENCE_API_VERSION", "2025-11-13")
```

**Action Items**:
- [ ] Immediately rotate the exposed API key
- [ ] Move all credentials to environment variables
- [ ] Add `.env` to `.gitignore` (verify it's there)
- [ ] Create `.env.example` template without real credentials
- [ ] Scan git history to remove any committed secrets
- [ ] Consider using Azure Key Vault for production

---

## Code Quality Improvements

### Issue 2: Extensive Commented Code

**Location**: `src/feedbackforge/dashboard_agent.py:104-175`

**Problem**:
- 70+ lines of commented/experimental code
- Multiple client initialization attempts
- Unclear which approach is correct
- Makes maintenance difficult

**Analysis**:
```python
# Multiple commented client initialization approaches:
# 1. AzureOpenAI with APIM gateway
# 2. Direct Azure OpenAI
# 3. agents library integration
# 4. Various credential methods
```

**Solution Options**:

**Option A: Clean Up (Recommended)**
```python
# Remove all commented code and keep only the working solution
def create_dashboard_agent() -> ChatAgent:
    """Create the Executive Dashboard Assistant using Azure OpenAI."""
    credential = AzureCliCredential()

    chat_client = AzureOpenAIChatClient(
        credential=credential,
        endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
        api_key=os.environ["AZURE_OPENAI_KEY"],
        deployment_name=os.environ["AZURE_AI_MODEL_DEPLOYMENT_NAME"]
    )

    agent = chat_client.create_agent(
        name="FeedbackForge",
        description="Executive Dashboard Assistant for customer feedback analysis",
        instructions=AGENT_INSTRUCTIONS,
        tools=TOOLS
    )

    return agent
```

**Option B: Document Experiments**
- Move experimental code to `docs/experiments/` or separate branch
- Document why each approach was tried/rejected
- Keep git history clean

**Action Items**:
- [ ] Choose one Azure client approach and stick with it
- [ ] Remove all unused imports
- [ ] Remove all commented code blocks
- [ ] Document the chosen approach
- [ ] Add inline comments only where necessary

### Issue 3: Duplicate Tool Definitions

**Location**: `src/feedbackforge/dashboard_agent.py:70-86`

**Problem**:
```python
# Original tools from chat_tools.py
TOOLS = [get_weekly_summary, get_issue_details, ...]

# Duplicate definition using different decorator
@function_tool
def get_weekly_summary2() -> str:
    # Same implementation
    ...

TOOLS2 = [get_weekly_summary2]
```

**Solution**:
- Remove duplicate `get_weekly_summary2` and `TOOLS2`
- Use consistent tool registration pattern
- Single source of truth for tools

---

## Architecture Enhancements

### Enhancement 1: Add Persistent Storage Layer

**Current State**: All data is in-memory (lost on restart)

**Proposed Architecture**:
```
┌─────────────────┐
│  Data Sources   │
│  (API/CSV/...)  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Ingestion Layer │
│  (Validation)   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Storage Layer  │
│  (PostgreSQL)   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Cache Layer    │
│     (Redis)     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Query Layer    │
│ (Data Store)    │
└─────────────────┘
```

**Implementation Steps**:

1. **Database Schema** (`migrations/001_initial.sql`):
```sql
CREATE TABLE feedback (
    id VARCHAR(50) PRIMARY KEY,
    text TEXT NOT NULL,
    sentiment VARCHAR(20),
    sentiment_score FLOAT,
    topics JSONB,
    customer_segment VARCHAR(50),
    customer_id VARCHAR(50),
    customer_name VARCHAR(100),
    rating INTEGER CHECK (rating >= 1 AND rating <= 5),
    timestamp TIMESTAMPTZ NOT NULL,
    product_version VARCHAR(20),
    platform VARCHAR(20),
    is_urgent BOOLEAN DEFAULT FALSE,
    competitor_mentions JSONB DEFAULT '[]',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_feedback_timestamp ON feedback(timestamp DESC);
CREATE INDEX idx_feedback_customer ON feedback(customer_id);
CREATE INDEX idx_feedback_topics ON feedback USING gin(topics);
CREATE INDEX idx_feedback_sentiment ON feedback(sentiment);
```

2. **Data Access Layer** (`src/feedbackforge/database.py`):
```python
from typing import List, Optional
from sqlalchemy import create_engine, Column, String, Float, Integer, Boolean, TIMESTAMP, JSON
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()

class FeedbackModel(Base):
    __tablename__ = 'feedback'

    id = Column(String(50), primary_key=True)
    text = Column(String, nullable=False)
    sentiment = Column(String(20))
    sentiment_score = Column(Float)
    topics = Column(JSON)
    customer_segment = Column(String(50))
    customer_id = Column(String(50))
    customer_name = Column(String(100))
    rating = Column(Integer)
    timestamp = Column(TIMESTAMP(timezone=True))
    product_version = Column(String(20))
    platform = Column(String(20))
    is_urgent = Column(Boolean, default=False)
    competitor_mentions = Column(JSON, default=[])

class FeedbackRepository:
    def __init__(self, database_url: str):
        self.engine = create_async_engine(database_url)
        self.SessionLocal = sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False
        )

    async def create(self, feedback: FeedbackItem) -> FeedbackItem:
        async with self.SessionLocal() as session:
            db_feedback = FeedbackModel(**feedback.__dict__)
            session.add(db_feedback)
            await session.commit()
            return feedback

    async def get_weekly_summary(self) -> Dict[str, Any]:
        # Implementation with efficient SQL queries
        pass
```

3. **Update DataStore** (`src/feedbackforge/data_store.py`):
```python
class FeedbackDataStore:
    def __init__(self, repository: Optional[FeedbackRepository] = None):
        self.repository = repository
        self.cache = {}  # Redis cache

    async def get_weekly_summary(self) -> Dict[str, Any]:
        cache_key = "weekly_summary"

        # Check cache
        if cache_key in self.cache:
            return self.cache[cache_key]

        # Query database
        if self.repository:
            summary = await self.repository.get_weekly_summary()
            self.cache[cache_key] = summary
            return summary

        # Fallback to in-memory
        return self._get_weekly_summary_memory()
```

**Action Items**:
- [ ] Choose database: PostgreSQL (recommended) or MongoDB
- [ ] Set up SQLAlchemy or motor (for MongoDB)
- [ ] Create migration system (Alembic)
- [ ] Implement repository pattern
- [ ] Add Redis for caching
- [ ] Update all data_store methods to use repository
- [ ] Add connection pooling
- [ ] Implement backup strategy

### Enhancement 2: Add Data Ingestion API

**Current State**: Only mock data, no real feedback ingestion

**Proposed Endpoints** (`src/feedbackforge/api/ingestion.py`):
```python
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, validator
from typing import List, Optional

router = APIRouter(prefix="/api/v1/feedback", tags=["ingestion"])

class FeedbackSubmission(BaseModel):
    text: str
    rating: Optional[int] = None
    customer_id: Optional[str] = None
    customer_segment: Optional[str] = None
    product_version: Optional[str] = None
    platform: Optional[str] = None

    @validator('rating')
    def validate_rating(cls, v):
        if v is not None and (v < 1 or v > 5):
            raise ValueError('Rating must be between 1 and 5')
        return v

@router.post("/submit")
async def submit_feedback(
    feedback: FeedbackSubmission,
    store: FeedbackDataStore = Depends(get_feedback_store)
):
    """Submit new feedback."""
    try:
        feedback_item = await store.create_feedback(feedback)
        return {"status": "success", "id": feedback_item.id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/bulk")
async def bulk_submit(
    feedbacks: List[FeedbackSubmission],
    store: FeedbackDataStore = Depends(get_feedback_store)
):
    """Bulk submit feedback (max 100 per request)."""
    if len(feedbacks) > 100:
        raise HTTPException(status_code=400, detail="Max 100 items per request")

    results = []
    for fb in feedbacks:
        item = await store.create_feedback(fb)
        results.append(item.id)

    return {"status": "success", "count": len(results), "ids": results}

@router.post("/webhook/{source}")
async def webhook_receiver(
    source: str,
    payload: dict,
    store: FeedbackDataStore = Depends(get_feedback_store)
):
    """Receive feedback from external sources (Typeform, SurveyMonkey, etc)."""
    parser = get_webhook_parser(source)
    feedback = parser.parse(payload)

    feedback_item = await store.create_feedback(feedback)
    return {"status": "success", "id": feedback_item.id}
```

**Webhook Parsers** (`src/feedbackforge/integrations/`):
```python
# typeform.py
class TypeformParser:
    def parse(self, payload: dict) -> FeedbackSubmission:
        # Parse Typeform webhook payload
        pass

# surveymonkey.py
class SurveyMonkeyParser:
    def parse(self, payload: dict) -> FeedbackSubmission:
        # Parse SurveyMonkey webhook payload
        pass
```

### Enhancement 3: Error Handling & Resilience

**Current State**: Minimal error handling, no retry logic

**Proposed Solution**:

1. **Retry Logic with Exponential Backoff**:
```python
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)
from azure.core.exceptions import ServiceRequestError, HttpResponseError

class ResilientExecutor(Executor):
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((ServiceRequestError, HttpResponseError)),
        reraise=True
    )
    async def call_agent_with_retry(self, prompt: str):
        try:
            result = await self.agent.run(prompt)
            return result
        except Exception as e:
            logger.error(f"Agent call failed: {e}")
            raise
```

2. **Circuit Breaker Pattern**:
```python
from pybreaker import CircuitBreaker

azure_ai_breaker = CircuitBreaker(
    fail_max=5,
    timeout_duration=60,
    name="azure_ai_service"
)

@azure_ai_breaker
async def call_azure_ai(self, prompt: str):
    return await self.agent.run(prompt)
```

3. **Graceful Degradation**:
```python
class SentimentAnalyzer(Executor):
    async def analyze(self, state: AnalysisState, ctx: WorkflowContext) -> None:
        try:
            result = await self.call_agent_with_retry(prompt)
            state.sentiment = parse_json_response(result.text)
        except Exception as e:
            logger.error(f"Sentiment analysis failed: {e}")
            # Fallback to simple rule-based sentiment
            state.sentiment = self._fallback_sentiment(state.surveys)
            state.sentiment["warning"] = "Using fallback analysis due to service error"

        await ctx.send_message(state)

    def _fallback_sentiment(self, surveys: List[SurveyResponse]) -> Dict:
        """Simple rule-based sentiment as fallback."""
        positive = sum(1 for s in surveys if s.rating and s.rating >= 4)
        negative = sum(1 for s in surveys if s.rating and s.rating <= 2)
        neutral = len(surveys) - positive - negative

        return {
            "overall_distribution": {
                "positive": round(positive / len(surveys) * 100),
                "negative": round(negative / len(surveys) * 100),
                "neutral": round(neutral / len(surveys) * 100)
            },
            "fallback": True
        }
```

4. **Comprehensive Error Types** (`src/feedbackforge/exceptions.py`):
```python
class FeedbackForgeException(Exception):
    """Base exception for FeedbackForge."""
    pass

class AzureAIServiceError(FeedbackForgeException):
    """Azure AI service error."""
    pass

class DataStoreError(FeedbackForgeException):
    """Data store error."""
    pass

class WorkflowExecutionError(FeedbackForgeException):
    """Workflow execution error."""
    pass

class ValidationError(FeedbackForgeException):
    """Data validation error."""
    pass
```

---

## Testing Strategy

### Current State: No tests implemented

### Proposed Test Structure:
```
tests/
├── unit/
│   ├── test_data_store.py
│   ├── test_models.py
│   ├── test_chat_tools.py
│   └── executors/
│       ├── test_sentiment_analyzer.py
│       ├── test_topic_extractor.py
│       └── ...
├── integration/
│   ├── test_workflow.py
│   ├── test_api.py
│   └── test_database.py
├── e2e/
│   ├── test_chat_mode.py
│   ├── test_serve_mode.py
│   └── test_workflow_mode.py
├── fixtures/
│   ├── sample_surveys.json
│   └── mock_responses.json
└── conftest.py
```

### Example Test Cases:

**Unit Test** (`tests/unit/test_data_store.py`):
```python
import pytest
from datetime import datetime, timedelta
from feedbackforge.data_store import FeedbackDataStore
from feedbackforge.models import FeedbackItem

@pytest.fixture
def data_store():
    store = FeedbackDataStore()
    return store

@pytest.fixture
def sample_feedback():
    return FeedbackItem(
        id="TEST001",
        text="Great product!",
        sentiment="positive",
        sentiment_score=0.8,
        topics=["product", "quality"],
        customer_segment="Enterprise",
        customer_id="ENT001",
        customer_name="Test Corp",
        rating=5,
        timestamp=datetime.now(),
        product_version="2.0.3"
    )

def test_get_weekly_summary_empty(data_store):
    summary = data_store.get_weekly_summary()
    assert summary["total_responses"] == 0

def test_get_weekly_summary_with_data(data_store, sample_feedback):
    data_store.feedback.append(sample_feedback)
    summary = data_store.get_weekly_summary()

    assert summary["total_responses"] == 1
    assert summary["sentiment"]["positive_pct"] == 100
    assert len(summary["top_issues"]) >= 1

def test_get_issue_details(data_store, sample_feedback):
    data_store.feedback.append(sample_feedback)
    details = data_store.get_issue_details("product")

    assert details["total_mentions"] == 1
    assert "product" in details["topic"]
```

**Integration Test** (`tests/integration/test_workflow.py`):
```python
import pytest
from feedbackforge.workflow import SurveyAnalysisWorkflow
from feedbackforge.models import SurveyResponse

@pytest.mark.asyncio
async def test_workflow_execution():
    """Test complete workflow execution."""
    surveys = [
        SurveyResponse(
            id="S001",
            text="App crashes on iOS",
            rating=1,
            timestamp=datetime.now().isoformat(),
            platform="iOS"
        ),
        # Add more samples
    ]

    workflow = SurveyAnalysisWorkflow()
    results = await workflow.analyze(surveys)

    assert results["analysis_complete"] == True
    assert "final_report" in results
    assert results["surveys_analyzed"] == len(surveys)
    assert "sentiment" in results["parallel_analysis"]
```

**API Test** (`tests/integration/test_api.py`):
```python
import pytest
from fastapi.testclient import TestClient
from feedbackforge.server import create_app

@pytest.fixture
def client():
    app = create_app()
    return TestClient(app)

def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_info_endpoint(client):
    response = client.get("/info")
    assert response.status_code == 200
    data = response.json()
    assert "capabilities" in data
    assert "weekly_summary" in data["capabilities"]
```

**Action Items**:
- [ ] Set up pytest configuration
- [ ] Create test fixtures
- [ ] Write unit tests for all modules (target: 80% coverage)
- [ ] Write integration tests for workflows
- [ ] Write E2E tests for all three modes
- [ ] Set up CI/CD with automated testing
- [ ] Add test coverage reporting
- [ ] Add performance/load tests

---

## Feature Additions

### Feature 1: Real-time Notifications

**Use Case**: Alert teams immediately when critical issues are detected

**Implementation**:
```python
# src/feedbackforge/notifications/notifier.py
from abc import ABC, abstractmethod
from typing import Dict, Any

class Notifier(ABC):
    @abstractmethod
    async def send(self, message: str, metadata: Dict[str, Any]) -> bool:
        pass

class SlackNotifier(Notifier):
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url

    async def send(self, message: str, metadata: Dict[str, Any]) -> bool:
        # Send to Slack webhook
        payload = {
            "text": message,
            "attachments": [{
                "color": "danger" if metadata.get("severity") == "CRITICAL" else "warning",
                "fields": [
                    {"title": "Priority", "value": metadata.get("priority", "P2"), "short": True},
                    {"title": "Affected", "value": str(metadata.get("affected_customers", 0)), "short": True}
                ]
            }]
        }
        # Send HTTP request
        pass

class EmailNotifier(Notifier):
    async def send(self, message: str, metadata: Dict[str, Any]) -> bool:
        # Send email via SendGrid/AWS SES
        pass

class NotificationService:
    def __init__(self):
        self.notifiers = []

    def register(self, notifier: Notifier):
        self.notifiers.append(notifier)

    async def notify_all(self, message: str, metadata: Dict[str, Any]):
        for notifier in self.notifiers:
            try:
                await notifier.send(message, metadata)
            except Exception as e:
                logger.error(f"Notification failed: {e}")
```

### Feature 2: Custom Reports & Dashboards

**Use Case**: Generate custom PDF/HTML reports for executives

**Implementation**:
```python
# src/feedbackforge/reporting/generator.py
from jinja2 import Template
import pdfkit
from datetime import datetime

class ReportGenerator:
    def __init__(self, template_path: str):
        self.template = self._load_template(template_path)

    def generate_html(self, data: Dict[str, Any]) -> str:
        return self.template.render(
            data=data,
            generated_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )

    def generate_pdf(self, data: Dict[str, Any], output_path: str):
        html = self.generate_html(data)
        pdfkit.from_string(html, output_path)

    def generate_executive_summary(self, analysis_results: Dict) -> str:
        # Format executive summary
        pass
```

### Feature 3: A/B Testing Support

**Use Case**: Compare feedback between different product versions or features

**Implementation**:
```python
# src/feedbackforge/analysis/ab_testing.py
from scipy import stats
from typing import List, Dict, Tuple

class ABTestAnalyzer:
    def analyze_variants(
        self,
        variant_a: List[FeedbackItem],
        variant_b: List[FeedbackItem]
    ) -> Dict[str, Any]:
        """Compare two variants using statistical tests."""

        # Sentiment comparison
        a_scores = [f.sentiment_score for f in variant_a]
        b_scores = [f.sentiment_score for f in variant_b]

        t_stat, p_value = stats.ttest_ind(a_scores, b_scores)

        # Rating comparison
        a_ratings = [f.rating for f in variant_a if f.rating]
        b_ratings = [f.rating for f in variant_b if f.rating]

        mann_whitney = stats.mannwhitneyu(a_ratings, b_ratings)

        return {
            "sample_sizes": {"a": len(variant_a), "b": len(variant_b)},
            "sentiment": {
                "variant_a_mean": sum(a_scores) / len(a_scores),
                "variant_b_mean": sum(b_scores) / len(b_scores),
                "t_statistic": t_stat,
                "p_value": p_value,
                "significant": p_value < 0.05
            },
            "rating": {
                "variant_a_median": sorted(a_ratings)[len(a_ratings)//2],
                "variant_b_median": sorted(b_ratings)[len(b_ratings)//2],
                "mann_whitney_u": mann_whitney.statistic,
                "p_value": mann_whitney.pvalue,
                "significant": mann_whitney.pvalue < 0.05
            },
            "recommendation": self._make_recommendation(p_value, mann_whitney.pvalue)
        }

    def _make_recommendation(self, sentiment_p: float, rating_p: float) -> str:
        if sentiment_p < 0.05 and rating_p < 0.05:
            return "Strong evidence of difference between variants"
        elif sentiment_p < 0.05 or rating_p < 0.05:
            return "Moderate evidence of difference between variants"
        else:
            return "No significant difference detected between variants"
```

---

## Deployment & Operations

### Containerization

**Dockerfile**:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY pyproject.toml .
RUN pip install --no-cache-dir .

# Copy application
COPY src/ ./src/

# Create non-root user
RUN useradd -m -u 1000 feedbackforge && chown -R feedbackforge:feedbackforge /app
USER feedbackforge

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Default command
CMD ["python", "-m", "feedbackforge", "serve", "--host", "0.0.0.0", "--port", "8080"]
```

**docker-compose.yml**:
```yaml
version: '3.8'

services:
  feedbackforge:
    build: .
    ports:
      - "8080:8080"
    environment:
      - AZURE_AI_PROJECT_ENDPOINT=${AZURE_AI_PROJECT_ENDPOINT}
      - AZURE_AI_MODEL_DEPLOYMENT_NAME=${AZURE_AI_MODEL_DEPLOYMENT_NAME}
      - DATABASE_URL=postgresql://postgres:password@db:5432/feedbackforge
      - REDIS_URL=redis://redis:6379
    depends_on:
      - db
      - redis
    restart: unless-stopped

  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=feedbackforge
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    restart: unless-stopped

  dashboard:
    build: ./dashboard
    ports:
      - "3000:3000"
    environment:
      - VITE_API_URL=http://localhost:8080
    depends_on:
      - feedbackforge
    restart: unless-stopped

volumes:
  postgres_data:
```

### Kubernetes Deployment

**k8s/deployment.yaml**:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: feedbackforge
  labels:
    app: feedbackforge
spec:
  replicas: 3
  selector:
    matchLabels:
      app: feedbackforge
  template:
    metadata:
      labels:
        app: feedbackforge
    spec:
      containers:
      - name: feedbackforge
        image: feedbackforge:latest
        ports:
        - containerPort: 8080
        env:
        - name: AZURE_AI_PROJECT_ENDPOINT
          valueFrom:
            secretKeyRef:
              name: azure-credentials
              key: endpoint
        - name: AZURE_AI_MODEL_DEPLOYMENT_NAME
          valueFrom:
            configMapKeyRef:
              name: feedbackforge-config
              key: model-deployment
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "2000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: feedbackforge-service
spec:
  selector:
    app: feedbackforge
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8080
  type: LoadBalancer
```

### Monitoring & Observability

**Application Insights Integration**:
```python
# src/feedbackforge/monitoring/telemetry.py
from opencensus.ext.azure.log_exporter import AzureLogHandler
from opencensus.ext.azure.trace_exporter import AzureExporter
from opencensus.trace.samplers import ProbabilitySampler
from opencensus.trace.tracer import Tracer
import logging

class TelemetryService:
    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self._setup_logging()
        self._setup_tracing()

    def _setup_logging(self):
        logger = logging.getLogger()
        logger.addHandler(AzureLogHandler(
            connection_string=self.connection_string
        ))
        logger.setLevel(logging.INFO)

    def _setup_tracing(self):
        self.tracer = Tracer(
            exporter=AzureExporter(
                connection_string=self.connection_string
            ),
            sampler=ProbabilitySampler(1.0)
        )

    def track_metric(self, name: str, value: float, properties: Dict = None):
        # Track custom metrics
        pass

    def track_event(self, name: str, properties: Dict = None):
        # Track custom events
        pass
```

---

## Performance Optimizations

### 1. Caching Strategy

```python
from functools import lru_cache
from datetime import datetime, timedelta
import hashlib

class CacheManager:
    def __init__(self, redis_client):
        self.redis = redis_client
        self.default_ttl = 300  # 5 minutes

    def cache_key(self, prefix: str, *args, **kwargs) -> str:
        """Generate cache key from arguments."""
        key_data = f"{prefix}:{args}:{kwargs}"
        return hashlib.md5(key_data.encode()).hexdigest()

    async def get_or_compute(
        self,
        key: str,
        compute_func,
        ttl: int = None
    ):
        """Get from cache or compute and cache."""
        cached = await self.redis.get(key)
        if cached:
            return json.loads(cached)

        result = await compute_func()
        await self.redis.setex(
            key,
            ttl or self.default_ttl,
            json.dumps(result)
        )
        return result
```

### 2. Connection Pooling

```python
# src/feedbackforge/database.py
from sqlalchemy.pool import QueuePool

engine = create_async_engine(
    database_url,
    poolclass=QueuePool,
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True,
    pool_recycle=3600
)
```

### 3. Batch Processing

```python
class BatchProcessor:
    def __init__(self, batch_size: int = 100):
        self.batch_size = batch_size

    async def process_in_batches(
        self,
        items: List[Any],
        process_func
    ) -> List[Any]:
        """Process items in batches to avoid memory issues."""
        results = []
        for i in range(0, len(items), self.batch_size):
            batch = items[i:i + self.batch_size]
            batch_results = await process_func(batch)
            results.extend(batch_results)
        return results
```

### 4. Async Operations

```python
import asyncio
from typing import List

async def parallel_analysis(surveys: List[SurveyResponse]) -> Dict:
    """Run all analyses in parallel."""
    tasks = [
        analyze_sentiment(surveys),
        extract_topics(surveys),
        detect_anomalies(surveys),
        analyze_competitors(surveys)
    ]

    results = await asyncio.gather(*tasks, return_exceptions=True)

    return {
        "sentiment": results[0] if not isinstance(results[0], Exception) else None,
        "topics": results[1] if not isinstance(results[1], Exception) else None,
        "anomalies": results[2] if not isinstance(results[2], Exception) else None,
        "competitive": results[3] if not isinstance(results[3], Exception) else None
    }
```

---

## Summary Checklist

### Immediate Actions (Week 1)
- [ ] **CRITICAL**: Rotate exposed API key
- [ ] **CRITICAL**: Move all credentials to environment variables
- [ ] Clean up commented code in dashboard_agent.py
- [ ] Remove duplicate tool definitions
- [ ] Add basic error handling to all executors
- [ ] Create .env.example file

### Short-term (Month 1)
- [ ] Implement persistent storage (PostgreSQL)
- [ ] Add comprehensive unit tests (80% coverage target)
- [ ] Implement retry logic and circuit breakers
- [ ] Add data ingestion API endpoints
- [ ] Set up logging and monitoring
- [ ] Create Docker containerization
- [ ] Add API documentation (OpenAPI/Swagger)

### Medium-term (Month 2-3)
- [ ] Complete dashboard integration
- [ ] Add Redis caching layer
- [ ] Implement notification system (Slack/Email)
- [ ] Add webhook support for survey platforms
- [ ] Create migration system
- [ ] Set up CI/CD pipeline
- [ ] Performance testing and optimization
- [ ] Security audit

### Long-term (Month 4+)
- [ ] A/B testing capabilities
- [ ] Custom report generation
- [ ] Multi-language support
- [ ] Advanced analytics dashboard
- [ ] Kubernetes deployment
- [ ] Multi-tenancy support
- [ ] API rate limiting
- [ ] Custom agent training

---

**Document Version**: 1.0
**Last Updated**: 2026-02-27
**Maintained By**: Development Team
