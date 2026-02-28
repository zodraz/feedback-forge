# FeedbackForge RAG with Azure AI Search

## Overview

FeedbackForge now supports **Retrieval Augmented Generation (RAG)** using Azure AI Search. This enables:

- 🔍 **Semantic Search**: Natural language queries over feedback data
- 🎯 **Vector Search**: Similarity-based retrieval using embeddings
- 🚀 **Hybrid Search**: Combines keyword, vector, and semantic ranking for best results
- 📊 **Intelligent Analytics**: Better trend detection and anomaly identification

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    User Query                           │
│          "What are the iOS crash issues?"               │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│              RAG Search Layer                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │   Semantic   │  │   Vector     │  │   Hybrid     │  │
│  │   Search     │  │   Search     │  │   Search     │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│            Azure AI Search Index                        │
│  • Feedback Text (searchable)                          │
│  • Vector Embeddings (1536 dims)                       │
│  • Metadata (sentiment, platform, etc.)                │
│  • Facets & Filters                                    │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│         Cosmos DB / In-Memory Store                     │
│           (Source of Truth)                             │
└─────────────────────────────────────────────────────────┘
```

---

## Quick Start

### 1. Prerequisites

#### Azure Resources Needed:
- ✅ **Azure AI Search** resource
- ✅ **Azure OpenAI** with embedding model deployed
- ✅ (Optional) Existing Cosmos DB or In-Memory data store

#### Create Azure AI Search:
```bash
# Using Azure CLI
az search service create \
  --name feedbackforge-search \
  --resource-group feedbackforge-rg \
  --sku basic \
  --location swedencentral

# Get admin key
az search admin-key show \
  --service-name feedbackforge-search \
  --resource-group feedbackforge-rg
```

### 2. Configure Environment Variables

Add to your `.env` file:

```bash
# Azure AI Search (Required for RAG)
AZURE_SEARCH_ENDPOINT=https://feedbackforge-search.search.windows.net
AZURE_SEARCH_KEY=your-admin-key-here
AZURE_SEARCH_INDEX_NAME=feedback-index  # Optional, default: feedback-index

# Azure OpenAI Embeddings (Required for RAG)
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_KEY=your-openai-key
AZURE_OPENAI_EMBEDDING_MODEL=text-embedding-3-small  # Or text-embedding-ada-002
```

### 3. Set Up Index and Load Data

Run the setup script to create the index and load your feedback data:

```bash
# Activate your virtual environment
source .venv/bin/activate  # or: .venv\Scripts\activate on Windows

# Run setup
python -m feedbackforge.rag_setup
```

This will:
1. ✅ Create the Azure AI Search index with vector search
2. ✅ Generate embeddings for all feedback items
3. ✅ Index the data with semantic capabilities
4. ✅ Test the search functionality

**⏱ Time**: Expect ~1-2 minutes per 100 feedback items (due to embedding generation)

---

## Usage Examples

### Basic Semantic Search

```python
from feedbackforge.rag_tools import rag_search_feedback

# Search for iOS issues
results = rag_search_feedback(
    query="iOS app crashes and freezes",
    search_type="semantic",
    top=10
)

for result in results:
    print(f"Customer: {result['customer_name']}")
    print(f"Feedback: {result['text']}")
    print(f"Relevance: {result.get('reranker_score', 0):.4f}")
    print("---")
```

### Vector Similarity Search

```python
# Find feedback similar to a specific complaint
results = rag_search_feedback(
    query="The app keeps crashing when I try to export data",
    search_type="vector",
    top=5
)
```

### Hybrid Search (Recommended)

```python
# Best of both worlds - combines keyword, vector, and semantic
results = rag_search_feedback(
    query="customers complaining about billing issues",
    search_type="hybrid",  # Default
    top=10,
    filters="sentiment eq 'negative' and rating le 2"  # OData filters
)
```

### Advanced Filtering

```python
from datetime import datetime, timedelta

# Search with time-based filters
week_ago = datetime.now() - timedelta(days=7)
results = rag_search_feedback(
    query="performance problems",
    filters=f"timestamp ge {week_ago.isoformat()} and platform eq 'iOS'",
    top=20
)
```

---

## RAG-Enhanced Tools

The package includes RAG-enhanced versions of existing tools:

### 1. Enhanced Weekly Summary

```python
from feedbackforge.rag_tools import rag_get_weekly_summary

summary = rag_get_weekly_summary()

# Returns enhanced summary with:
# - Overall statistics
# - Top positive themes (RAG-detected)
# - Critical issues (RAG-ranked by relevance)
# - Urgent items
```

### 2. Intelligent Issue Analysis

```python
from feedbackforge.rag_tools import rag_get_issue_details

analysis = rag_get_issue_details("iOS crash")

# Returns:
# - Semantically similar feedback
# - Platform/version distribution
# - Affected customer count
# - Relevance-ranked samples
```

### 3. Competitor Intelligence

```python
from feedbackforge.rag_tools import rag_get_competitor_insights

insights = rag_get_competitor_insights()

# Returns:
# - Competitor mentions with context
# - Churn risk customers
# - Sentiment analysis
```

### 4. Anomaly Detection

```python
from feedbackforge.rag_tools import rag_detect_anomalies

anomalies = rag_detect_anomalies()

# Uses semantic patterns to detect:
# - Performance spikes
# - Security concerns
# - Payment issues
# - Auth problems
```

### 5. Find Similar Feedback

```python
from feedbackforge.rag_tools import rag_find_similar_feedback

similar = rag_find_similar_feedback(
    feedback_text="App crashes when exporting large files",
    top=5
)

# Returns semantically similar feedback with similarity scores
```

### 6. Question Answering

```python
from feedbackforge.rag_tools import rag_answer_question

answer = rag_answer_question(
    question="What are users saying about the new UI redesign?",
    context_window=10
)

# Returns relevant feedback context for LLM-based answering
```

---

## Integration with Agent

### Update Agent to Use RAG

```python
from feedbackforge.rag_tools import (
    rag_get_weekly_summary,
    rag_get_issue_details,
    rag_get_competitor_insights,
    rag_detect_anomalies,
    rag_search_feedback
)

# Register as agent tools
@agent.tool
def search_feedback(query: str, top: int = 10):
    """Search feedback using natural language with RAG."""
    return rag_search_feedback(query, top=top)

@agent.tool
def get_weekly_summary():
    """Get AI-enhanced weekly summary."""
    return rag_get_weekly_summary()

# And so on...
```

---

## Search Types Comparison

| Feature | Semantic | Vector | Hybrid |
|---------|----------|--------|--------|
| **Speed** | Fast | Fast | Medium |
| **Keyword Match** | ✅ Yes | ❌ No | ✅ Yes |
| **Semantic Understanding** | ✅ Good | ✅ Excellent | ✅ Excellent |
| **Synonym Handling** | ✅ Yes | ✅ Yes | ✅ Yes |
| **Concept Matching** | ⚠️ Limited | ✅ Excellent | ✅ Excellent |
| **Filters** | ✅ Full | ✅ Full | ✅ Full |
| **Best For** | Keyword queries | Similarity | Most use cases |

**Recommendation**: Use **Hybrid Search** for best results in production.

---

## Filter Syntax (OData)

Azure AI Search uses OData filter expressions:

```python
# Simple equality
filters="sentiment eq 'negative'"

# Multiple conditions
filters="sentiment eq 'negative' and rating le 2"

# Date ranges
filters="timestamp ge 2026-02-01T00:00:00Z"

# String contains (use search.in)
filters="platform eq 'iOS' or platform eq 'Android'"

# Complex example
filters="(sentiment eq 'negative' and rating le 2) and timestamp ge 2026-02-20T00:00:00Z"
```

### Available Filter Fields:
- `sentiment` (string: 'positive', 'negative', 'neutral')
- `sentiment_score` (double: -1.0 to 1.0)
- `customer_segment` (string: 'Enterprise', 'SMB', 'Individual')
- `rating` (int32: 1-5)
- `timestamp` (DateTimeOffset)
- `platform` (string: 'iOS', 'Android', 'Web', 'Desktop')
- `product_version` (string)
- `is_urgent` (boolean)
- `customer_id` (string)

---

## Faceted Search

Get aggregated counts for different dimensions:

```python
from feedbackforge.rag_search import rag_search_client

facets = rag_search_client.get_facets([
    "sentiment",
    "platform",
    "product_version",
    "customer_segment"
])

# Returns:
# {
#   "sentiment": [{"value": "negative", "count": 145}, ...],
#   "platform": [{"value": "iOS", "count": 87}, ...],
#   ...
# }
```

---

## Maintenance

### Re-indexing Data

When feedback data changes significantly:

```bash
# Full re-index
python -m feedbackforge.rag_setup
```

### Incremental Updates

```python
from feedbackforge.rag_search import rag_search_client
from feedbackforge.rag_tools import get_embeddings

# Index new feedback items
new_feedback = [...]  # Your new items

# Convert to dicts with embeddings
documents = []
for item in new_feedback:
    embedding = get_embeddings(item['text'])
    doc = {**item, 'text_vector': embedding}
    documents.append(doc)

# Upload
rag_search_client.search_client.upload_documents(documents)
```

### Delete Index

```python
from feedbackforge.rag_search import rag_search_client

rag_search_client.index_client.delete_index("feedback-index")
```

---

## Performance Optimization

### 1. Batch Embedding Generation

```python
# Generate embeddings in batches for better performance
from openai import AzureOpenAI

client = AzureOpenAI(...)

texts = [item['text'] for item in feedback_items]

# OpenAI supports up to 16 texts per request for embeddings
embeddings = client.embeddings.create(
    input=texts[:16],
    model="text-embedding-3-small"
)
```

### 2. Caching

```python
# Cache embeddings to avoid regeneration
import pickle

# Save
with open('embeddings_cache.pkl', 'wb') as f:
    pickle.dump(embeddings_dict, f)

# Load
with open('embeddings_cache.pkl', 'rb') as f:
    embeddings_dict = pickle.load(f)
```

### 3. Index Size

- **Basic tier**: Up to 2GB, 1 million documents
- **Standard tier**: Up to 100GB+, millions of documents
- **Storage tier**: Up to 2TB

---

## Cost Estimation

### Azure AI Search:
- **Basic tier**: ~$75/month (suitable for development/small production)
- **Standard S1**: ~$250/month (production)

### Azure OpenAI Embeddings:
- **text-embedding-3-small**: $0.02 per 1M tokens
- Example: 1000 feedback items (~100 words each) = ~$0.002

### Total for 10,000 feedback items:
- **One-time indexing**: ~$0.20 (embeddings)
- **Monthly**: $75+ (search service)

---

## Troubleshooting

### Issue: "Index not found"
```bash
# Create index first
python -m feedbackforge.rag_setup
```

### Issue: "Embedding generation fails"
```bash
# Check Azure OpenAI configuration
echo $AZURE_OPENAI_ENDPOINT
echo $AZURE_OPENAI_KEY

# Test connection
curl -H "api-key: $AZURE_OPENAI_KEY" \
  "$AZURE_OPENAI_ENDPOINT/openai/deployments/text-embedding-3-small?api-version=2024-02-01"
```

### Issue: "Slow search performance"
- Use filters to reduce result set
- Reduce `top` parameter
- Consider upgrading to Standard tier
- Use caching for repeated queries

### Issue: "OData filter syntax error"
- Check field names match exactly
- Use single quotes for string values
- Date format: `YYYY-MM-DDTHH:MM:SSZ`
- Escape special characters

---

## Best Practices

1. ✅ **Use Hybrid Search** for most queries (best accuracy)
2. ✅ **Apply filters** to narrow results before search
3. ✅ **Cache embeddings** to avoid regeneration
4. ✅ **Batch operations** when indexing large datasets
5. ✅ **Monitor costs** in Azure Portal
6. ✅ **Test queries** with different search types
7. ✅ **Use facets** for analytics and filtering UIs
8. ✅ **Keep index updated** with incremental updates

---

## Next Steps

1. **Set up Azure AI Search** resource
2. **Configure embeddings** in Azure OpenAI
3. **Run setup script** to create index
4. **Test searches** with your data
5. **Integrate with agent** tools
6. **Monitor performance** and costs

---

## Resources

- [Azure AI Search Documentation](https://learn.microsoft.com/en-us/azure/search/)
- [Vector Search Overview](https://learn.microsoft.com/en-us/azure/search/vector-search-overview)
- [OData Filter Syntax](https://learn.microsoft.com/en-us/azure/search/search-query-odata-filter)
- [Azure OpenAI Embeddings](https://learn.microsoft.com/en-us/azure/ai-services/openai/concepts/models#embeddings-models)

---

**Last Updated**: 2026-02-27
**Version**: 1.0.0
