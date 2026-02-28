# OpenTelemetry & Azure Application Insights Integration

## Overview

FeedbackForge includes **OpenTelemetry instrumentation** that exports traces, metrics, and logs to **Azure Application Insights** for comprehensive observability.

---

## 🎯 What You Get

### 1. **Distributed Tracing**
- ✅ Request/response tracing for all API endpoints
- ✅ Database query tracing (Cosmos DB)
- ✅ Redis operation tracing
- ✅ HTTP client call tracing
- ✅ Custom business logic spans
- ✅ End-to-end transaction tracking

### 2. **Metrics**
- ✅ Request rates and durations
- ✅ Error rates
- ✅ Custom business metrics:
  - Feedback items processed
  - Sessions created
  - Agent workflow executions
  - Agent execution duration

### 3. **Automatic Instrumentation**
- ✅ FastAPI (all endpoints)
- ✅ Redis operations
- ✅ HTTPX HTTP clients
- ✅ Exception tracking

---

## 🚀 Setup Instructions

### Step 1: Create Application Insights Resource

#### Option A: Azure Portal

1. Go to [Azure Portal](https://portal.azure.com)
2. Click **"Create a resource"**
3. Search for **"Application Insights"**
4. Fill in:
   - **Resource Name**: `feedbackforge-insights`
   - **Region**: Same as your other resources (e.g., `eastus`)
   - **Resource Group**: Use existing (e.g., `feedbackforge-rg`)
   - **Workspace**: Create new or use existing Log Analytics workspace
5. Click **"Review + create"**

#### Option B: Azure CLI

```bash
# Create Log Analytics workspace (if needed)
az monitor log-analytics workspace create \
  --resource-group feedbackforge-rg \
  --workspace-name feedbackforge-workspace \
  --location eastus

# Get workspace ID
WORKSPACE_ID=$(az monitor log-analytics workspace show \
  --resource-group feedbackforge-rg \
  --workspace-name feedbackforge-workspace \
  --query id -o tsv)

# Create Application Insights
az monitor app-insights component create \
  --app feedbackforge-insights \
  --location eastus \
  --resource-group feedbackforge-rg \
  --workspace $WORKSPACE_ID
```

### Step 2: Get Connection String

#### Azure Portal
1. Navigate to your Application Insights resource
2. Click **"Overview"** in left menu
3. Copy the **"Connection String"** (looks like: `InstrumentationKey=...;IngestionEndpoint=...`)

#### Azure CLI
```bash
az monitor app-insights component show \
  --app feedbackforge-insights \
  --resource-group feedbackforge-rg \
  --query connectionString \
  --output tsv
```

### Step 3: Configure Environment

Add to your `.env` file:

```bash
# OpenTelemetry & Application Insights
APPLICATIONINSIGHTS_CONNECTION_STRING=InstrumentationKey=12345678-1234-1234-1234-123456789012;IngestionEndpoint=https://eastus-8.in.applicationinsights.azure.com/;LiveEndpoint=https://eastus.livediagnostics.monitor.azure.com/

# Optional configuration
OTEL_SERVICE_NAME=feedbackforge       # Override service name
DISABLE_TELEMETRY=false               # Set to "true" to disable
```

### Step 4: Install Dependencies

```bash
# Install OpenTelemetry packages
pip install -e .

# Or update existing installation
pip install --upgrade opentelemetry-api opentelemetry-sdk \
  opentelemetry-instrumentation-fastapi \
  opentelemetry-instrumentation-redis \
  opentelemetry-instrumentation-httpx \
  azure-monitor-opentelemetry-exporter
```

### Step 5: Start the Server

```bash
python -m feedbackforge serve --port 8080

# You should see:
# ✅ OpenTelemetry configured for Azure Application Insights
#    Service: feedbackforge v1.0.0
#    Connection: InstrumentationKey=...
# ✅ FastAPI auto-instrumentation enabled
# ✅ Redis auto-instrumentation enabled
# ✅ HTTPX client auto-instrumentation enabled
```

---

## 📊 Viewing Telemetry in Azure Portal

### 1. **Live Metrics** (Real-time)

1. Go to Application Insights resource
2. Click **"Live Metrics"** in left menu
3. See real-time:
   - Incoming requests
   - Request duration
   - Failure rates
   - Server CPU/memory

### 2. **Application Map** (Dependencies)

1. Click **"Application Map"**
2. Visualize:
   - API endpoints
   - Database calls
   - Redis operations
   - External HTTP calls
   - Performance bottlenecks

### 3. **Transaction Search**

1. Click **"Transaction search"**
2. Search for specific requests:
   - Filter by endpoint (e.g., `/agent`)
   - Filter by response time
   - Filter by result code
3. Click on a transaction to see:
   - End-to-end trace
   - All dependencies
   - Timing breakdown

### 4. **Performance**

1. Click **"Performance"** → **"Operations"**
2. See:
   - Average duration per endpoint
   - 95th/99th percentile
   - Failure rates
   - Call counts

### 5. **Failures**

1. Click **"Failures"**
2. See:
   - Exception details
   - Stack traces
   - Affected endpoints
   - Error trends

### 6. **Metrics Explorer** (Custom Metrics)

1. Click **"Metrics"**
2. Select metrics:
   - `feedbackforge.feedback.processed`
   - `feedbackforge.sessions.created`
   - `feedbackforge.agent.executions`
   - `feedbackforge.agent.duration`
3. Create charts and dashboards

---

## 🔍 Understanding Traces

### Example: Agent Workflow Execution

When a user asks a question, you'll see a trace like this:

```
POST /agent (200 OK, 2.5s)
├── cosmos.get_weekly_summary (250ms)
│   └── Cosmos DB query
├── cosmos.get_issue_details (180ms)
│   └── Cosmos DB query
├── agent.workflow.execute (1.8s)
│   ├── Tool: get_weekly_summary
│   ├── Tool: get_issue_details
│   └── LLM call (1.2s)
└── session.save (50ms)
    └── Redis SET
```

### Trace Attributes

Each span includes:
- **Operation name**: `cosmos.get_weekly_summary`
- **Duration**: 250ms
- **Status**: success/error
- **Custom attributes**:
  - `success`: true
  - `error.type`: (if failed)
  - `error.message`: (if failed)

---

## 📈 Custom Metrics

### Built-in Metrics

FeedbackForge tracks these custom metrics:

| Metric | Type | Description | Dimensions |
|--------|------|-------------|------------|
| `feedbackforge.feedback.processed` | Counter | Number of feedback items processed | - |
| `feedbackforge.sessions.created` | Counter | Number of sessions created | `user_id` |
| `feedbackforge.agent.executions` | Counter | Number of agent workflow runs | - |
| `feedbackforge.agent.duration` | Histogram | Agent execution time | - |

### Viewing Custom Metrics

```kusto
// In Application Insights > Logs
customMetrics
| where name == "feedbackforge.sessions.created"
| summarize count() by bin(timestamp, 1h)
| render timechart
```

---

## 🛠️ Adding Custom Tracing

### Method 1: Decorator (Recommended)

```python
from feedbackforge.telemetry import trace_operation

@trace_operation("my_operation")
def my_function():
    # Your code here
    return result
```

### Method 2: Manual Span

```python
from feedbackforge.telemetry import tracer

if tracer:
    with tracer.start_as_current_span("my_operation") as span:
        # Add custom attributes
        span.set_attribute("customer_id", "ENT001")
        span.set_attribute("query_type", "weekly_summary")

        try:
            result = do_work()
            span.set_attribute("success", True)
            return result
        except Exception as e:
            span.set_attribute("success", False)
            span.record_exception(e)
            raise
```

### Method 3: Add Metrics

```python
from feedbackforge.telemetry import meter

if meter:
    # Counter
    my_counter = meter.create_counter(
        name="my_app.events",
        description="Number of events processed",
        unit="1"
    )
    my_counter.add(1, {"event_type": "user_action"})

    # Histogram
    my_histogram = meter.create_histogram(
        name="my_app.latency",
        description="Operation latency",
        unit="ms"
    )
    my_histogram.record(duration_ms)
```

---

## 🔧 Configuration Options

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `APPLICATIONINSIGHTS_CONNECTION_STRING` | (none) | **Required** - App Insights connection string |
| `OTEL_SERVICE_NAME` | `feedbackforge` | Service name in traces |
| `DISABLE_TELEMETRY` | `false` | Set to `"true"` to disable all telemetry |

### Disabling Telemetry

```bash
# Disable for development/testing
export DISABLE_TELEMETRY=true
python -m feedbackforge serve

# Output:
# 📊 Telemetry disabled via DISABLE_TELEMETRY environment variable
```

### Graceful Degradation

If Application Insights is not configured:
- ✅ Application continues to work normally
- ✅ No telemetry exported
- ✅ No performance impact

```bash
# Without APPLICATIONINSIGHTS_CONNECTION_STRING
python -m feedbackforge serve

# Output:
# 📊 Application Insights not configured. Set APPLICATIONINSIGHTS_CONNECTION_STRING to enable telemetry.
```

---

## 📊 Sample Queries (Kusto/KQL)

### Request Performance by Endpoint

```kusto
requests
| where timestamp > ago(1h)
| summarize
    count=count(),
    avg_duration=avg(duration),
    p95_duration=percentile(duration, 95),
    failure_rate=countif(success == false) * 100.0 / count()
  by name
| order by avg_duration desc
```

### Custom Metrics - Sessions Created Per Hour

```kusto
customMetrics
| where name == "feedbackforge.sessions.created"
| where timestamp > ago(24h)
| summarize sessions=sum(value) by bin(timestamp, 1h)
| render timechart
```

### Failed Requests with Details

```kusto
requests
| where success == false
| where timestamp > ago(1h)
| join kind=inner (
    exceptions
    | where timestamp > ago(1h)
  ) on operation_Id
| project
    timestamp,
    name,
    resultCode,
    duration,
    type,
    outerMessage
| order by timestamp desc
```

### Dependency Duration Analysis

```kusto
dependencies
| where timestamp > ago(1h)
| summarize
    count=count(),
    avg_duration=avg(duration),
    p95=percentile(duration, 95)
  by name, type
| order by avg_duration desc
```

### Agent Workflow Traces

```kusto
traces
| where message contains "agent" or message contains "workflow"
| where timestamp > ago(1h)
| project timestamp, severityLevel, message
| order by timestamp desc
```

---

## 🎯 Best Practices

### 1. **Use Meaningful Span Names**

```python
# Good
@trace_operation("cosmos.query_feedback_by_customer")

# Bad
@trace_operation("query")
```

### 2. **Add Contextual Attributes**

```python
with tracer.start_as_current_span("process_feedback") as span:
    span.set_attribute("customer_id", customer_id)
    span.set_attribute("feedback_type", feedback_type)
    span.set_attribute("item_count", len(items))
```

### 3. **Track Business Metrics**

```python
# Track important business events
if custom_metrics:
    custom_metrics["feedback_processed"].add(
        len(items),
        {"sentiment": "negative", "priority": "high"}
    )
```

### 4. **Don't Over-Instrument**

- ✅ Instrument API boundaries
- ✅ Instrument database/external calls
- ✅ Instrument critical business logic
- ❌ Don't instrument every function
- ❌ Don't add excessive attributes

### 5. **Use Sampling for High Volume**

For production with high traffic, configure sampling:

```python
# In telemetry.py
from opentelemetry.sdk.trace.sampling import ParentBasedTraceIdRatio

# Sample 10% of traces
sampler = ParentBasedTraceIdRatio(0.1)
trace_provider = TracerProvider(resource=resource, sampler=sampler)
```

---

## 💰 Cost Management

### Pricing Factors

1. **Data Ingestion**: ~$2.88 per GB
2. **Data Retention**: 90 days free, $0.12/GB/month after
3. **Web Tests**: Separate pricing

### Cost Optimization Tips

1. **Use Sampling** (recommended for production)
   ```python
   sampler = ParentBasedTraceIdRatio(0.1)  # 10% sampling
   ```

2. **Adjust Log Levels**
   ```python
   logging.getLogger("opentelemetry").setLevel(logging.WARNING)
   ```

3. **Set Data Retention**
   - Azure Portal → Application Insights → Usage and estimated costs
   - Set retention to 30 or 90 days

4. **Monitor Your Usage**
   - Azure Portal → Application Insights → Usage and estimated costs
   - Set up budget alerts

### Typical Usage Estimate

**For FeedbackForge (light usage):**
- Requests: ~10,000/month
- Data ingestion: ~100 MB/month
- **Estimated cost**: ~$0.30/month (within free tier)

**For Production (moderate usage):**
- Requests: ~1M/month
- Data ingestion: ~5 GB/month
- **Estimated cost**: ~$15-20/month

---

## 🐛 Troubleshooting

### Issue: "Telemetry not appearing in Application Insights"

**Check:**
1. Connection string is correct
2. Network connectivity to Azure
3. Wait 2-3 minutes for data propagation
4. Check Azure Portal → Application Insights → Live Metrics

**Debug:**
```bash
# Enable debug logging
export OTEL_LOG_LEVEL=debug
python -m feedbackforge serve
```

### Issue: "Import error for azure-monitor-opentelemetry-exporter"

**Solution:**
```bash
pip install --upgrade azure-monitor-opentelemetry-exporter
```

### Issue: "High costs"

**Solution:**
1. Enable sampling (see Cost Management above)
2. Reduce trace verbosity
3. Check for trace storms (infinite loops creating spans)

---

## 📚 Additional Resources

### OpenTelemetry
- [OpenTelemetry Python Docs](https://opentelemetry.io/docs/instrumentation/python/)
- [OpenTelemetry Specification](https://opentelemetry.io/docs/reference/specification/)

### Azure Application Insights
- [Application Insights Overview](https://learn.microsoft.com/azure/azure-monitor/app/app-insights-overview)
- [KQL Query Language](https://learn.microsoft.com/azure/data-explorer/kusto/query/)
- [Distributed Tracing](https://learn.microsoft.com/azure/azure-monitor/app/distributed-tracing)

### Azure Monitor
- [Azure Monitor Pricing](https://azure.microsoft.com/pricing/details/monitor/)
- [Log Analytics Workspace](https://learn.microsoft.com/azure/azure-monitor/logs/log-analytics-workspace-overview)

---

## 📝 Summary

### ✅ What's Enabled

- [x] OpenTelemetry tracing with Azure App Insights
- [x] Automatic FastAPI instrumentation
- [x] Automatic Redis instrumentation
- [x] Automatic HTTP client instrumentation
- [x] Custom business metrics
- [x] Exception tracking
- [x] Performance monitoring
- [x] Distributed tracing

### 🎯 Quick Start

```bash
# 1. Create Application Insights
az monitor app-insights component create --app feedbackforge-insights -g feedbackforge-rg

# 2. Get connection string
az monitor app-insights component show --app feedbackforge-insights -g feedbackforge-rg --query connectionString

# 3. Add to .env
APPLICATIONINSIGHTS_CONNECTION_STRING=<your-connection-string>

# 4. Start server
python -m feedbackforge serve

# 5. View in Azure Portal
# Navigate to Application Insights → Live Metrics
```

---

**Implementation Date**: 2026-02-27
**Status**: ✅ Complete and Working
**Telemetry Backend**: Azure Application Insights via OpenTelemetry
