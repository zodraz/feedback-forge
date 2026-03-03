# RAG Quick Start - 5 Minutes

## Prerequisites
- Azure AI Search resource
- Azure OpenAI with embedding model deployed

## 1. Install Dependencies

```bash
pip install -e .
```

## 2. Configure Environment

Add to `.env`:
```bash
AZURE_SEARCH_ENDPOINT=https://your-search.search.windows.net
AZURE_SEARCH_API_KEY=your-admin-key
AZURE_OPENAI_ENDPOINT=https://your-openai.openai.azure.com/
AZURE_OPENAI_KEY=your-key
AZURE_OPENAI_EMBEDDING_MODEL=text-embedding-3-small
```

## 3. Create Index & Load Data

```bash
python -m feedbackforge.rag_setup
```

## 4. Use RAG in Your Code

```python
from feedbackforge.rag_tools import rag_search_feedback

# Search feedback
results = rag_search_feedback(
    query="iOS crashes",
    search_type="hybrid",
    top=10
)

for r in results:
    print(f"{r['customer_name']}: {r['text']}")
```

## That's It! 🎉

**See [RAG_GUIDE.md](./RAG_GUIDE.md) for complete documentation.**

## Quick Examples

### Search with Filters
```python
# Negative feedback from last week
from datetime import datetime, timedelta
week_ago = datetime.now() - timedelta(days=7)

results = rag_search_feedback(
    query="app problems",
    filters=f"timestamp ge {week_ago.isoformat()} and sentiment eq 'negative'"
)
```

### Find Similar Feedback
```python
from feedbackforge.rag_tools import rag_find_similar_feedback

similar = rag_find_similar_feedback(
    "App crashes when exporting files",
    top=5
)
```

### Get Enhanced Analytics
```python
from feedbackforge.rag_tools import (
    rag_get_weekly_summary,
    rag_get_issue_details,
    rag_detect_anomalies
)

summary = rag_get_weekly_summary()
issues = rag_get_issue_details("iOS crash")
anomalies = rag_detect_anomalies()
```

## Search Types

| Type | When to Use |
|------|-------------|
| `"hybrid"` | ✅ **Best for most queries** (default) |
| `"semantic"` | Fast keyword + semantic ranking |
| `"vector"` | Pure similarity (no keywords) |

## Cost

- **Azure AI Search Basic**: ~$75/month
- **Embeddings**: ~$0.02 per 1000 items
- **Total for 10k items**: ~$75.20/month

## Troubleshooting

```bash
# Test connection
python -c "from feedbackforge.rag_search import create_rag_search_client; print(create_rag_search_client())"

# Re-create index
python -m feedbackforge.rag_setup
```

---

**Full Guide**: [RAG_GUIDE.md](./RAG_GUIDE.md)
