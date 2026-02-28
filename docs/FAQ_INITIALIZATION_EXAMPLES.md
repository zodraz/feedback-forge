# FAQ Generator - Initialization Examples

## How to Pass Data / Initialize RAG Client

There are **3 ways** to initialize the FAQ Generator:

---

## Method 1: Auto-Initialize from Environment (Easiest)

The FAQ Generator will automatically initialize from your `.env` configuration:

```python
from feedbackforge.faq_generator import FAQGenerator

# Just create it - reads from .env automatically
generator = FAQGenerator()

# Now use it
themes = generator.find_common_themes()
faqs = generator.generate_faq_entries(themes)
```

**Requirements:**
- `.env` must have:
  ```bash
  AZURE_SEARCH_ENDPOINT=https://your-search.search.windows.net
  AZURE_SEARCH_KEY=your-key
  AZURE_SEARCH_INDEX_NAME=feedback-index
  ```

**When it works:**
- ✅ Most common use case
- ✅ Works with CLI: `python -m feedbackforge.cli_faq`
- ✅ Simple and clean

---

## Method 2: Initialize Global RAG Client First

Initialize the global RAG client before creating FAQ Generator:

```python
from feedbackforge.rag_search import init_rag_search
from feedbackforge.faq_generator import FAQGenerator

# Initialize the global RAG client
rag_client = init_rag_search()

if not rag_client:
    print("❌ RAG not configured!")
    exit(1)

# Now create FAQ generator (will use global)
generator = FAQGenerator()

# Use it
result = generator.find_common_themes(timeframe_days=30)
```

**When to use:**
- ✅ When you want to check if RAG is available first
- ✅ When sharing RAG client across multiple components
- ✅ Better error handling

---

## Method 3: Pass RAG Client Directly (Most Control)

Create and pass the RAG client explicitly:

```python
from feedbackforge.rag_search import FeedbackRAGSearch
from feedbackforge.faq_generator import FAQGenerator

# Create RAG client with explicit config
rag_client = FeedbackRAGSearch(
    search_endpoint="https://your-search.search.windows.net",
    index_name="feedback-index",
    api_key="your-api-key"  # or None to use DefaultAzureCredential
)

# Pass it to FAQ generator
generator = FAQGenerator(rag_client=rag_client)

# Use it
themes = generator.find_common_themes()
```

**When to use:**
- ✅ Custom configuration (different endpoint, index, etc.)
- ✅ Multiple RAG clients (dev/staging/prod)
- ✅ Unit testing with mock RAG client
- ✅ Fine-grained control

---

## Complete Examples

### Example 1: Simple Script

```python
#!/usr/bin/env python3
"""Simple FAQ generation script."""

from feedbackforge.faq_generator import generate_faq

# Just call it - auto-initializes from .env
result = generate_faq(
    timeframe_days=30,
    min_occurrences=3,
    max_faqs=15
)

print(f"Generated {len(result['faqs'])} FAQs")
for faq in result['faqs']:
    print(f"Q: {faq['question']}")
    print(f"A: {faq['answer']}\n")
```

**Run:**
```bash
python simple_faq.py
```

---

### Example 2: With Error Handling

```python
from feedbackforge.rag_search import init_rag_search
from feedbackforge.faq_generator import FAQGenerator

# Initialize and check
rag_client = init_rag_search()

if not rag_client:
    print("❌ Azure AI Search not configured!")
    print("   Please set AZURE_SEARCH_ENDPOINT in .env")
    print("   Run: python -m feedbackforge.rag_setup")
    exit(1)

print("✅ RAG client initialized")

# Create generator
generator = FAQGenerator()

try:
    # Find themes
    themes = generator.find_common_themes(
        timeframe_days=30,
        min_occurrences=3,
        max_themes=15
    )

    print(f"Found {len(themes)} common themes")

    # Generate FAQs
    faqs = generator.generate_faq_entries(themes)

    print(f"Generated {len(faqs)} FAQ entries")

    # Export
    generator.export_to_html(faqs, "faq.html")
    print("✅ Exported to faq.html")

except ValueError as e:
    print(f"❌ Error: {e}")
except Exception as e:
    print(f"❌ Unexpected error: {e}")
```

---

### Example 3: Custom Configuration

```python
from feedbackforge.rag_search import FeedbackRAGSearch
from feedbackforge.faq_generator import FAQGenerator

# Development RAG client
dev_rag = FeedbackRAGSearch(
    search_endpoint="https://dev-search.search.windows.net",
    index_name="feedback-dev",
    api_key="dev-key"
)

# Production RAG client
prod_rag = FeedbackRAGSearch(
    search_endpoint="https://prod-search.search.windows.net",
    index_name="feedback-prod",
    api_key=None  # Use DefaultAzureCredential
)

# Create generators for each environment
dev_generator = FAQGenerator(rag_client=dev_rag)
prod_generator = FAQGenerator(rag_client=prod_rag)

# Generate FAQs from dev
dev_faqs = dev_generator.find_common_themes(timeframe_days=7)

# Generate FAQs from prod
prod_faqs = prod_generator.find_common_themes(timeframe_days=30)
```

---

### Example 4: Using in Flask/FastAPI

```python
from fastapi import FastAPI
from feedbackforge.rag_search import init_rag_search
from feedbackforge.faq_generator import FAQGenerator

app = FastAPI()

# Initialize once at startup
@app.on_event("startup")
async def startup_event():
    global faq_generator

    rag_client = init_rag_search()
    if not rag_client:
        print("⚠️ Warning: RAG not configured, FAQ endpoint will fail")

    faq_generator = FAQGenerator(rag_client=rag_client)

@app.get("/api/faq")
async def get_faq(days: int = 30, min_mentions: int = 3):
    """Generate FAQs on demand."""

    if not faq_generator.rag_client:
        return {"error": "RAG not configured"}

    themes = faq_generator.find_common_themes(
        timeframe_days=days,
        min_occurrences=min_mentions
    )

    faqs = faq_generator.generate_faq_entries(themes)

    return {
        "count": len(faqs),
        "faqs": faqs
    }
```

---

### Example 5: Testing with Mock

```python
import pytest
from unittest.mock import Mock
from feedbackforge.faq_generator import FAQGenerator

def test_faq_generator():
    """Test FAQ generator with mock RAG client."""

    # Create mock RAG client
    mock_rag = Mock()
    mock_rag.hybrid_search.return_value = [
        {
            'id': 'fb001',
            'text': 'How do I export data?',
            'customer_name': 'John',
            'platform': 'Web',
            'rating': 4,
            'search_score': 0.95,
            'text_vector': [0.1] * 1536  # Mock embedding
        },
        {
            'id': 'fb002',
            'text': 'Can I download my info?',
            'customer_name': 'Jane',
            'platform': 'iOS',
            'rating': 3,
            'search_score': 0.90,
            'text_vector': [0.1] * 1536  # Similar embedding
        }
    ]

    # Create generator with mock
    generator = FAQGenerator(rag_client=mock_rag)

    # Test
    themes = generator.find_common_themes(timeframe_days=30)

    # Assertions
    assert len(themes) > 0
    assert mock_rag.hybrid_search.called
```

---

## Environment Variables Reference

Your `.env` file should have:

```bash
# Required for RAG
AZURE_SEARCH_ENDPOINT=https://your-search.search.windows.net
AZURE_SEARCH_KEY=your-admin-key-here
AZURE_SEARCH_INDEX_NAME=feedback-index  # Optional, default: feedback-index

# Required for embeddings
AZURE_OPENAI_ENDPOINT=https://your-openai.openai.azure.com/
AZURE_OPENAI_KEY=your-openai-key
AZURE_OPENAI_EMBEDDING_MODEL=text-embedding-3-small
```

---

## Troubleshooting

### Issue: "RAG client required for FAQ generation"

**Cause:** RAG client is not initialized

**Solution 1:** Check `.env` configuration
```bash
# Verify vars are set
echo $AZURE_SEARCH_ENDPOINT
echo $AZURE_SEARCH_KEY
```

**Solution 2:** Initialize explicitly
```python
from feedbackforge.rag_search import init_rag_search

rag = init_rag_search()
if not rag:
    print("Check your .env file!")
```

**Solution 3:** Pass client directly
```python
from feedbackforge.rag_search import FeedbackRAGSearch

rag = FeedbackRAGSearch(
    search_endpoint="https://...",
    api_key="..."
)

generator = FAQGenerator(rag_client=rag)
```

---

### Issue: "Index not found"

**Cause:** Azure AI Search index doesn't exist

**Solution:** Run setup first
```bash
python -m feedbackforge.rag_setup
```

---

### Issue: ImportError

**Cause:** Missing dependencies

**Solution:** Install packages
```bash
pip install -e .
```

---

## Quick Reference

| Use Case | Method | Code |
|----------|--------|------|
| **CLI** | Auto | `python -m feedbackforge.cli_faq` |
| **Simple script** | Auto | `FAQGenerator()` |
| **With error handling** | Global | `init_rag_search()` then `FAQGenerator()` |
| **Custom config** | Direct | `FAQGenerator(rag_client=custom_rag)` |
| **Testing** | Mock | `FAQGenerator(rag_client=mock)` |

---

## Best Practices

### ✅ DO:
- Initialize RAG client once at app startup
- Reuse the same RAG client instance
- Check if RAG is available before using
- Use environment variables for config
- Handle errors gracefully

### ❌ DON'T:
- Create new RAG client for each FAQ generation
- Hardcode credentials in code
- Ignore initialization errors
- Skip error handling

---

## Summary

**Easiest way:**
```python
from feedbackforge.faq_generator import generate_faq

result = generate_faq()  # Auto-initializes from .env
```

**Most control:**
```python
from feedbackforge.rag_search import FeedbackRAGSearch
from feedbackforge.faq_generator import FAQGenerator

rag = FeedbackRAGSearch(endpoint="...", api_key="...")
gen = FAQGenerator(rag_client=rag)
```

**Production-ready:**
```python
from feedbackforge.rag_search import init_rag_search
from feedbackforge.faq_generator import FAQGenerator

# At startup
rag = init_rag_search()
if not rag:
    raise RuntimeError("RAG required")

# Later
generator = FAQGenerator(rag_client=rag)
```

---

Last Updated: 2026-02-27
