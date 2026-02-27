# FeedbackForge Features

## Core Features

### 🤖 Multi-Agent Feedback Analysis
- **Weekly Summary Agent**: Aggregates feedback trends and sentiment
- **Issue Details Agent**: Deep-dives into specific topics
- **Competitor Analysis Agent**: Identifies competitor mentions and comparisons
- **Customer Context Agent**: Provides customer history and insights
- **Anomaly Detection Agent**: Detects unusual patterns in feedback
- **Action Generator Agent**: Creates actionable recommendations
- **Parallel Execution**: Agents run concurrently for fast responses

### 📊 Data Storage

#### Dual Storage Architecture
- **Cosmos DB**: Production-grade persistent storage with partition keys
- **In-Memory**: Fast fallback for development with mock data
- **Auto-initialization**: Populates 289 realistic feedback items on first run
- **Seamless switching**: Same API for both storage types

#### Cosmos DB Features
- ✅ Automatic database/container creation
- ✅ Two authentication methods (Primary Key or DefaultAzureCredential)
- ✅ Partition key optimization (`/customer_segment`)
- ✅ SQL query support with cross-partition queries
- ✅ Auto-population of mock data if empty

### 💬 Session Management

#### User Isolation
- **Device-based user IDs**: Automatically generated per browser
- **Session isolation**: Users cannot access each other's sessions
- **Ownership verification**: All operations verify user identity
- **Privacy**: Complete separation between users

#### Session Persistence
- **Redis Backend**: Production-grade session storage
- **In-Memory Fallback**: Works without Redis for development
- **Auto-save**: Sessions saved automatically on message changes
- **Auto-load**: Previous conversations restored on page refresh
- **Thread ID persistence**: Conversations survive page reloads

### 📈 Observability (OpenTelemetry + Azure Application Insights)

#### Distributed Tracing
- ✅ End-to-end request tracing
- ✅ Database query tracing (Cosmos DB)
- ✅ Redis operation tracing
- ✅ HTTP client tracing
- ✅ Custom business logic spans
- ✅ Exception tracking with stack traces

#### Metrics
- ✅ Request rates and durations
- ✅ Error rates and failure patterns
- ✅ Custom business metrics:
  - Feedback items processed
  - Sessions created
  - Agent workflow executions
  - Agent execution duration

#### Automatic Instrumentation
- ✅ FastAPI (all endpoints)
- ✅ Redis operations
- ✅ HTTPX HTTP clients
- ✅ Zero-configuration for standard operations

#### Application Insights Integration
- ✅ Live metrics (real-time)
- ✅ Application map (dependency visualization)
- ✅ Transaction search
- ✅ Performance analytics
- ✅ Failure analysis
- ✅ Custom dashboards

### 🔒 Security

#### Authentication
- **No passwords required**: Device-based identification
- **Cosmos DB**: Primary key or Azure AD (DefaultAzureCredential)
- **Redis**: Connection URL with optional password
- **Session isolation**: Users can only access their own data

#### Best Practices
- ✅ Environment variables for secrets
- ✅ `.env` files excluded from git
- ✅ Primary keys documented as development-only
- ✅ DefaultAzureCredential recommended for production

### 🎨 User Interface

#### Dashboard Features
- **Chat Interface**: Natural language conversation with AI agent
- **Quick Actions**: Pre-defined queries for common tasks
- **Real-time Streaming**: SSE for incremental responses
- **Tool Visibility**: Shows which tools the agent is using
- **Session Persistence**: Conversations saved automatically
- **New Conversation**: Start fresh anytime

#### Capabilities
- Weekly summaries
- Issue deep-dives
- Competitor analysis
- Customer context
- Anomaly detection
- Alert management
- Action generation
- Team escalation

### 🔧 Developer Experience

#### Zero-Configuration Development
- ✅ Works out-of-the-box with in-memory storage
- ✅ Mock data auto-populated (289 realistic items)
- ✅ No database setup required to start
- ✅ Graceful degradation for all optional services

#### Optional Production Features
- Cosmos DB for persistence
- Redis for session management
- Application Insights for observability
- All features work without these services

#### Easy Deployment
```bash
# Development
python -m feedbackforge serve

# Production (with all features)
export COSMOS_DB_ENDPOINT=...
export COSMOS_DB_KEY=...
export REDIS_URL=...
export APPLICATIONINSIGHTS_CONNECTION_STRING=...
python -m feedbackforge serve
```

### 📦 Technologies

#### Backend
- **Agent Framework**: Microsoft Agent Framework (v1.0.0b251209)
- **API**: FastAPI with AG-UI protocol
- **Database**: Azure Cosmos DB (SQL API)
- **Cache/Sessions**: Redis
- **Telemetry**: OpenTelemetry + Azure Monitor

#### Frontend
- **Framework**: React 18 + TypeScript
- **Build**: Vite
- **Styling**: CSS modules
- **Protocol**: AG-UI (SSE streaming)

#### Infrastructure
- **Azure AI**: LLM inference
- **Azure Cosmos DB**: Document storage
- **Azure Application Insights**: Observability
- **Azure Redis**: Session cache (optional)

---

## Feature Matrix

| Feature | Development | Production |
|---------|-------------|------------|
| **Multi-Agent Workflow** | ✅ | ✅ |
| **Data Storage** | In-Memory | Cosmos DB |
| **Session Persistence** | In-Memory | Redis |
| **User Isolation** | ✅ | ✅ |
| **Telemetry** | Optional | Recommended |
| **Authentication** | Device-based | Device-based or Azure AD |
| **Auto-save Sessions** | ✅ | ✅ |
| **Mock Data** | ✅ | ✅ (initial) |

---

## Coming Soon

- [ ] Export feedback to CSV/JSON
- [ ] Custom date range filters
- [ ] Email notifications for alerts
- [ ] Multi-language support
- [ ] Sentiment trend charts
- [ ] A/B test result tracking
- [ ] Integration with Slack/Teams
- [ ] Role-based access control (RBAC)
- [ ] Session sharing and collaboration

---

## Documentation

- **[README.md](./README.md)**: Getting started and overview
- **[TELEMETRY_GUIDE.md](./TELEMETRY_GUIDE.md)**: Complete observability setup
- **[TELEMETRY_QUICKSTART.md](./TELEMETRY_QUICKSTART.md)**: 5-minute telemetry setup
- **[COSMOS_DB_INTEGRATION.md](./COSMOS_DB_INTEGRATION.md)**: Database setup and usage
- **[COSMOS_AUTH_GUIDE.md](./COSMOS_AUTH_GUIDE.md)**: Authentication methods
- **[USER_ISOLATION.md](./USER_ISOLATION.md)**: Session security and isolation
- **[SESSION_MANAGEMENT.md](./SESSION_MANAGEMENT.md)**: Session architecture
- **[SESSION_IMPLEMENTATION.md](./SESSION_IMPLEMENTATION.md)**: Implementation details

---

**Last Updated**: 2026-02-27
**Version**: 1.0.0
