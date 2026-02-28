# OpenTelemetry Quick Start

## 5-Minute Setup

### 1. Create Application Insights (Azure CLI)

```bash
az monitor app-insights component create \
  --app feedbackforge-insights \
  --location eastus \
  --resource-group feedbackforge-rg
```

### 2. Get Connection String

```bash
az monitor app-insights component show \
  --app feedbackforge-insights \
  --resource-group feedbackforge-rg \
  --query connectionString -o tsv
```

### 3. Add to `.env`

```bash
APPLICATIONINSIGHTS_CONNECTION_STRING=InstrumentationKey=...;IngestionEndpoint=...;LiveEndpoint=...
```

### 4. Restart Server

```bash
python -m feedbackforge serve
```

### 5. View Telemetry

Go to Azure Portal → Application Insights → Live Metrics

---

## What You Get

✅ **Request Tracing**: Every API call traced end-to-end
✅ **Performance Metrics**: Response times, throughput, errors
✅ **Dependencies**: Database queries, Redis operations, HTTP calls
✅ **Custom Metrics**: Business KPIs (sessions, agent executions)
✅ **Exception Tracking**: Full stack traces in Azure Portal
✅ **Application Map**: Visual dependency graph

---

## Cost

**Development/Testing**: FREE (within 5GB/month)
**Production (light)**: ~$5-10/month
**Production (heavy)**: ~$50-100/month

Enable sampling for high-volume production:
```python
# Reduce to 10% of traces
sampler = ParentBasedTraceIdRatio(0.1)
```

---

## Disable Telemetry

```bash
export DISABLE_TELEMETRY=true
```

Or don't set `APPLICATIONINSIGHTS_CONNECTION_STRING` - the app works fine without it!

---

## Full Documentation

See [TELEMETRY_GUIDE.md](./TELEMETRY_GUIDE.md) for complete setup, queries, and best practices.
