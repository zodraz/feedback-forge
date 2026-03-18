# FeedbackForge

Multi-Agent Feedback Survey Analyzer with Executive Dashboard

## Overview

FeedbackForge is an AI-powered feedback analysis system that uses multiple specialized agents to analyze customer surveys, extract insights, detect anomalies, and generate actionable recommendations. Built with Microsoft Agent Framework and Azure AI services.

### Key Features

- **Multi-Agent Workflow**: 11 specialized agents working in parallel for comprehensive analysis
- **Executive Dashboard**: Interactive chat interface for exploring feedback insights
- **Real-time Anomaly Detection**: Automatically detect unusual patterns and spikes
- **Competitive Intelligence**: Extract competitor mentions and churn risk analysis
- **RAG-Powered FAQ Generator**: Automatically generate FAQs from customer feedback using semantic search
- **MCP Server Integration**: Connect to external feedback sources (GitHub, Zendesk, Intercom) using Model Context Protocol
- **Five Operating Modes**: Development, Production, Batch processing, FAQ Generation, and MCP Server

## Architecture

### Five Operating Modes

#### 1. Chat Mode (DevUI) - Development Interface
- Interactive chat with the executive dashboard assistant
- Best for: Development, testing, interactive exploration
- Default port: 8090
- Command: `python -m feedbackforge` or `python -m feedbackforge chat`

#### 2. Serve Mode (AG-UI) - Production Server
- FastAPI server with AG-UI protocol (CopilotKit compatible)
- Best for: Production deployment with frontend integration
- Default port: 8081
- Command: `python -m feedbackforge serve --port 8081`

#### 3. Workflow Mode - Batch Analysis
- Full multi-agent analysis pipeline
- Best for: Batch processing of survey data
- Command: `python -m feedbackforge workflow`

#### 4. FAQ Mode - RAG-Powered FAQ Generation
- Automatically generate FAQs from customer feedback using Azure AI Search
- Uses hybrid search (keyword + vector + semantic) for intelligent theme clustering
- Best for: Creating customer-facing documentation, support knowledge bases
- Command: `python -m feedbackforge faq`

#### 5. MCP Server Mode - External Feedback Integration
- Model Context Protocol server for fetching real feedback from external sources
- Integrates with GitHub Issues, Zendesk Tickets, Intercom Conversations
- Best for: Replacing mock data with production feedback, CI/CD integration
- Command: `python -m feedbackforge mcp`
- See: [MCP_INTEGRATION.md](MCP_INTEGRATION.md) for detailed setup

### Multi-Agent Workflow Pipeline

The workflow uses a sophisticated DAG with parallel processing across 7 stages:

```
Stage 1: Initial Orchestrator
    ↓
Stage 2: Data Preprocessing
    ↓
Stage 3: Parallel Analysis (Fan-out)
    ├─ Sentiment Analyzer
    ├─ Topic Extractor
    ├─ Anomaly Detector
    └─ Competitive Intelligence
    ↓
Stage 4: Insight Mining (Fan-in Aggregator)
    ↓
Stage 5: Parallel Action Generation (Fan-out)
    ├─ Priority Ranker
    └─ Action Generator
    ↓
Stage 6: Report Generation (Fan-in Aggregator)
    ↓
Stage 7: Final Orchestrator Review
```

**Stage Details**:
1. **Initial Orchestrator**: Validates survey data, assesses quality, plans execution
2. **Data Preprocessing**: Cleans and prepares survey data
3. **Parallel Analysis**: Sentiment, topics, anomalies, and competitive intelligence
4. **Insight Mining**: Synthesizes all parallel results, identifies patterns and root causes
5. **Parallel Action Generation**: Priority ranking and action item generation
6. **Report Generation**: Creates executive summary with metrics and recommendations
7. **Final Orchestrator Review**: Quality assessment and confidence scoring

## Installation

### Prerequisites

- Python 3.11 or higher
- Azure AI Foundry project with model deployment
- Azure CLI (for authentication)

### Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd feedback-forge
```

2. Create and activate a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -e .
```

4. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your Azure credentials
```

Required environment variables:
```bash
# Azure AI Foundry
AZURE_AI_PROJECT_ENDPOINT=https://your-project.region.api.azureml.ms
AZURE_AI_MODEL_DEPLOYMENT_NAME=your-deployment-name

# Azure OpenAI (alternative)
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_KEY=your-key
```

## Usage

### Chat Mode (Development)

```bash
# Start DevUI on default port (8090)
python -m feedbackforge

# Custom port
python -m feedbackforge chat --port 9000
```

Try these queries in the chat:
- "Show me this week's feedback summary"
- "Tell me more about the iOS crashes"
- "What are customers saying about competitors?"
- "Check for any anomalies"

### Serve Mode (Production)

```bash
# Start AG-UI server on default port (8081)
python -m feedbackforge serve --port 8081

# Custom configuration
python -m feedbackforge serve --port 8081 --host 0.0.0.0 --port 5000 --reload
```

Endpoints:
- AG-UI Protocol: `http://localhost:8081/`
- Health Check: `http://localhost:8081/health`
- Service Info: `http://localhost:8081/info`

### Workflow Mode (Batch Analysis)

```bash
# Analyze up to 20 surveys (default)
python -m feedbackforge workflow

# Custom survey limit
python -m feedbackforge workflow --max-surveys 50
```

Output: JSON file `survey_analysis_<timestamp>.json` with complete analysis results.

### FAQ Mode (RAG-Powered FAQ Generation)

```bash
# Generate FAQs from last 30 days (default)
python -m feedbackforge faq

# Generate from last 7 days, minimum 5 mentions
python -m feedbackforge faq --days 7 --min-mentions 5

# Generate top 20 FAQs in friendly style
python -m feedbackforge faq --max-faqs 20 --style friendly

# Export only to HTML
python -m feedbackforge faq --formats html

# Advanced: Custom settings
python -m feedbackforge faq --days 14 --min-mentions 2 --style technical --max-faqs 25
```

Output: FAQ files in markdown, JSON, and/or HTML formats (e.g., `faq_generated_<timestamp>.md`)

**Prerequisites for FAQ Mode:**
- Azure AI Search resource (for semantic/vector search)
- Azure OpenAI embedding deployment (for vector embeddings)
- Feedback data indexed in Azure AI Search

See `FAQ_QUICKSTART.md` for setup instructions.

## Dashboard Agent Tools

The executive dashboard assistant has 8 specialized tools:

1. **get_weekly_summary**: Sentiment distribution, top issues, urgent items
2. **get_issue_details**: Deep-dive analysis with trends and recommendations
3. **get_competitor_insights**: Competitor analysis and churn risks
4. **get_customer_context**: Customer feedback history and escalation risk
5. **check_for_anomalies**: Detect unusual patterns in recent feedback
6. **set_alert**: Configure monitoring alerts
7. **generate_action_items**: Create prioritized action items
8. **escalate_to_team**: Escalate issues to specific teams

## Data Models

### SurveyResponse
Input data for workflow processing:
- `id`, `text`, `rating`, `timestamp`
- `customer_segment`, `product_version`, `platform`
- `customer_id`, `customer_name`

### FeedbackItem
Extended feedback for data store and chat queries:
- Includes sentiment analysis, topics, urgency flags
- Competitor mentions, platform/version tracking

### AnalysisState
State object passed through workflow pipeline:
- Tracks all stage outputs
- Manages parallel task completion

## Project Structure

```
feedback-forge/
├── feedbackforge/
│   ├── __main__.py           # CLI entry point
│   ├── workflow.py           # Multi-agent workflow orchestration
│   ├── executors.py          # 11 executor classes for workflow stages
│   ├── models.py             # Data models
│   ├── data_store.py         # Cosmos DB data store with mock data
│   ├── dashboard_agent.py    # Chat agent creation
│   ├── chat_tools.py         # AI function tools
│   ├── server.py             # FastAPI AG-UI server
│   └── faq_generator.py      # RAG-powered FAQ generation
├── dashboard/                # React + TypeScript executive dashboard
├── faqs/                     # React + TypeScript FAQ viewer
├── pyproject.toml           # Project configuration
└── README.md
```

## Development

### Running Tests

```bash
pytest
```

### Code Quality

```bash
# Type checking
pyright

# Linting
ruff check .
```

## Frontend Integration

The production server (serve mode) exposes an AG-UI compatible endpoint that can be consumed by:
- CopilotKit React/Angular frontends
- Any AG-UI protocol compatible client

### Executive Dashboard

Interactive chat interface for exploring feedback insights:

```bash
cd dashboard
npm install
npm run dev
```

Opens at http://localhost:3000/

### FAQ Viewer

Beautiful web interface for viewing auto-generated FAQs:

```bash
cd faqs
npm install
npm run dev
```

Opens at http://localhost:3002/

**Prerequisites**: Backend server must be running with FAQ data:
```bash
# Terminal 1: Start backend
python -m feedbackforge serve --port 8081 --port 8081

# Terminal 2: Generate FAQs
python -m feedbackforge faq

# Terminal 3: Start FAQ viewer
cd faqs && npm run dev
```

## Current Limitations & Known Issues

### 🔴 Critical Issues

1. **Security Vulnerability**: Hardcoded API credentials in `dashboard_agent.py:108`
   - **Risk**: Exposed API key in source code
   - **Fix Required**: Move to environment variables immediately
   ```python
   # REMOVE THIS:
   api_key="0d5695acb9a14a0da0064a604181e667"

   # USE INSTEAD:
   api_key=os.environ["AZURE_API_GATEWAY_KEY"]
   ```

### ⚠️ Code Quality Issues

2. **Extensive Commented Code**: Lines 104-175 in `dashboard_agent.py`
   - Contains experimental/debug code that should be cleaned up
   - Makes maintenance difficult
   - Should either be removed or moved to a separate branch

3. **Inconsistent Azure Client Usage**: Multiple client initialization attempts
   - Code shows experimentation with different client types
   - Should standardize on one approach

### 🟡 Functionality Gaps

4. **No Persistent Storage**: All data is in-memory
   - Feedback is lost on restart
   - No historical analysis capability
   - Consider adding database support (PostgreSQL, MongoDB)

5. **Limited Test Coverage**: No unit tests found
   - pytest is configured but no tests implemented
   - Critical for production readiness

6. **Frontend Incomplete**: Basic React setup without FeedbackForge integration
   - No connection to backend AG-UI endpoint
   - UI components not implemented

7. **No Error Handling**: Minimal error handling for Azure AI service failures
   - Network timeouts not handled
   - API rate limits not considered
   - Should add retry logic and circuit breakers

8. **Mock Data Only** ✅ SOLVED: MCP server integration available
   - ✅ MCP server provides integration with GitHub, Zendesk, Intercom
   - ✅ Fetch real feedback from external sources
   - ⚠️ Direct API endpoints to submit feedback (still needed)
   - See [MCP_INTEGRATION.md](MCP_INTEGRATION.md) for setup

## Improvement Roadmap

### Phase 1: Security & Stability (Priority: Critical)
- [ ] Remove hardcoded credentials
- [ ] Add comprehensive error handling
- [ ] Implement retry logic for Azure AI calls
- [ ] Add logging and monitoring

### Phase 2: Testing & Quality (Priority: High)
- [ ] Add unit tests for all executors
- [ ] Add integration tests for workflow
- [ ] Add API tests for server endpoints
- [ ] Clean up commented code
- [ ] Add code coverage reporting

### Phase 3: Data & Storage (Priority: High)
- [ ] Implement persistent storage layer
- [ ] Add feedback ingestion API
- [ ] Support multiple data sources (CSV, API, webhooks)
- [ ] Add data migration utilities

### Phase 4: Frontend & UX (Priority: Medium)
- [ ] Complete React frontend integration
- [ ] Implement dashboard visualizations
- [ ] Add real-time updates (WebSocket/SSE)
- [ ] Mobile responsive design

### Phase 5: Advanced Features (Priority: Low)
- [ ] Custom agent configuration
- [ ] Multi-language support
- [ ] Advanced analytics and reporting
- [ ] Email/Slack notifications
- [ ] Custom webhook integrations
- [ ] A/B testing framework

## Best Practices & Recommendations

### Configuration Management
- Always use environment variables for secrets
- Never commit `.env` files to version control
- Use Azure Key Vault for production secrets

### Agent Design
- Keep executor instructions clear and concise
- Use structured JSON outputs for consistency
- Implement proper fan-in/fan-out patterns
- Monitor token usage and costs

### Deployment

**Docker Deployment (Recommended)**

Complete Docker setup with production and development configurations:

```bash
# Production deployment
docker-compose up -d

# Development with hot reload
docker-compose -f docker-compose.dev.yml up -d
```

Services:
- Backend API: http://localhost:8081
- Dashboard: http://localhost:3000
- FAQ Viewer: http://localhost:3002
- Redis: localhost:6379

See [DOCKER_GUIDE.md](DOCKER_GUIDE.md) for complete documentation.

**CI/CD with GitHub Actions**

Automated builds push to Azure Container Registry on every commit:

```bash
# Automatically builds and pushes on push to main
git push origin main

# Create versioned release
git tag v1.0.0
git push origin v1.0.0
```

Setup:
1. Create Azure Container Registry
2. Add GitHub secrets: `ACR_REGISTRY`, `ACR_USERNAME`, `ACR_PASSWORD`
3. Push to main - images build automatically

See [GITHUB_ACTIONS_ACR_SETUP.md](GITHUB_ACTIONS_ACR_SETUP.md) for setup instructions.

**Best Practices**
- Use container orchestration (Docker/Kubernetes)
- Implement health checks and readiness probes
- Set up proper logging and monitoring
- Use Azure Application Insights

### Performance
- Cache frequently accessed data
- Use connection pooling for Azure clients
- Implement rate limiting
- Consider async processing for large batches

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

MIT License - see LICENSE file for details

## Support

- Documentation: [Link to docs]
- Issues: [GitHub Issues]
- Discussions: [GitHub Discussions]

## Acknowledgments

- Built with [Microsoft Agent Framework](https://github.com/microsoft/agent-framework)
- Powered by Azure AI services
- CopilotKit compatible via AG-UI protocol

---

**Status**: Beta - Active Development

**Last Updated**: 2026-02-28
