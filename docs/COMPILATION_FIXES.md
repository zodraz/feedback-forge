# Compilation Fixes for RAG Module

## Issues Found and Fixed

### 1. `HnswAlgorithmConfiguration` - Fixed ✅

**Problem:**
```python
# ❌ This doesn't compile - parameters should be HnswParameters object, not dict
HnswAlgorithmConfiguration(
    name="feedback-hnsw",
    parameters={
        "m": 4,
        "efConstruction": 400,
        "efSearch": 500,
        "metric": "cosine"
    }
)
```

**Solution:**
```python
# ✅ Correct - use HnswParameters object with snake_case
from azure.search.documents.indexes.models import HnswParameters

HnswAlgorithmConfiguration(
    name="feedback-hnsw",
    parameters=HnswParameters(
        m=4,
        ef_construction=400,  # Note: snake_case, not camelCase
        ef_search=500,         # Note: snake_case
        metric="cosine"
    )
)
```

**Changes:**
- Import `HnswParameters`
- Create `HnswParameters` object instead of dict
- Use snake_case parameter names: `ef_construction`, `ef_search`

---

### 2. `vector_queries` - Fixed ✅

**Problem:**
```python
# ❌ This doesn't compile - vector_queries should use VectorizedQuery, not dict
results = search_client.search(
    search_text=query,
    vector_queries=[{
        "kind": "vector",
        "vector": query_vector,
        "fields": "text_vector",
        "k": top
    }]
)
```

**Solution:**
```python
# ✅ Correct - use VectorizedQuery objects
from azure.search.documents.models import VectorizedQuery

results = search_client.search(
    search_text=query,
    vector_queries=[
        VectorizedQuery(
            vector=query_vector,
            k=top,
            fields="text_vector"
        )
    ]
)
```

**Changes:**
- Import `VectorizedQuery`
- Create `VectorizedQuery` object instead of dict
- Remove `"kind": "vector"` (not needed in object)

---

## Files Modified

### `/home/abel/git/feedback-forge/src/feedbackforge/rag_search.py`

**Line ~14: Added imports**
```python
from azure.search.documents.indexes.models import (
    # ... existing imports ...
    HnswParameters,  # ← Added
)
from azure.search.documents.models import VectorizedQuery  # ← Added
```

**Line ~120: Fixed HnswAlgorithmConfiguration**
```python
HnswAlgorithmConfiguration(
    name="feedback-hnsw",
    parameters=HnswParameters(  # ← Changed from dict
        m=4,
        ef_construction=400,    # ← Changed from efConstruction
        ef_search=500,          # ← Changed from efSearch
        metric="cosine"
    )
)
```

**Line ~290: Fixed vector_search method**
```python
vector_queries=[
    VectorizedQuery(  # ← Changed from dict
        vector=query_vector,
        k=top,
        fields="text_vector"
    )
]
```

**Line ~345: Fixed hybrid_search method**
```python
vector_queries=[
    VectorizedQuery(  # ← Changed from dict
        vector=query_vector,
        k=top * 2,
        fields="text_vector"
    )
]
```

---

## Verification

All fixes have been tested and verified:

```bash
# Test imports
✅ python3 -c "from feedbackforge.rag_search import FeedbackRAGSearch"
✅ python3 -c "from feedbackforge.rag_setup import setup_rag_index"
✅ python3 -c "from feedbackforge.rag_tools import get_embeddings"
✅ python3 -c "from feedbackforge.faq_generator import FAQGenerator"

# Test object creation
✅ HnswParameters(m=4, ef_construction=400, ef_search=500, metric="cosine")
✅ HnswAlgorithmConfiguration(name="test", parameters=params)
✅ VectorizedQuery(vector=[0.1]*1536, k=10, fields="text_vector")
```

---

## Azure Search SDK Version

These fixes are for **azure-search-documents >= 11.4.0**

The API changed from accepting dictionaries to requiring proper typed objects:
- `HnswParameters` for HNSW configuration
- `VectorizedQuery` for vector search queries

---

## Common Mistakes to Avoid

### ❌ Don't use camelCase
```python
# Wrong
parameters=HnswParameters(
    efConstruction=400,  # ❌ Wrong - should be ef_construction
    efSearch=500         # ❌ Wrong - should be ef_search
)
```

### ❌ Don't use dictionaries
```python
# Wrong
vector_queries=[{"vector": vec, "k": 10}]  # ❌ Wrong - use VectorizedQuery
```

### ❌ Don't use "kind" field
```python
# Wrong
VectorizedQuery(
    kind="vector",  # ❌ Not needed, remove this
    vector=vec
)
```

---

### 3. `get_facets()` - Fixed ✅

**Problem:**
```python
# ❌ This doesn't work - hasattr check causes issues
facets = {}
if hasattr(results, 'get_facets'):
    facets = results.get_facets()

# ❌ This also doesn't work - facets is not a direct property
facets = results.facets if hasattr(results, 'facets') else {}
```

**Solution:**
```python
# ✅ Correct - call get_facets() directly and handle None return
facets_result = results.get_facets()
facets = facets_result if facets_result is not None else {}
```

**Changes:**
- Call `get_facets()` method directly (it returns `Optional[Dict]`)
- Handle `None` return value explicitly
- Remove `hasattr` check which was causing issues

---

### 4. `rag_setup.py` - Missing Import - Fixed ✅

**Problem:**
```python
# ❌ Using get_embeddings without importing it
def index_feedback_data(rag_client: FeedbackRAGSearch):
    rag_client.index_feedback(
        feedback_items=feedback_dicts,
        get_embeddings_func=lambda text: get_embeddings(text)  # ❌ Not imported!
    )
```

**Solution:**
```python
# ✅ Added import at top of file
from .rag_tools import get_embeddings

def index_feedback_data(rag_client: FeedbackRAGSearch):
    rag_client.index_feedback(
        feedback_items=feedback_dicts,
        get_embeddings_func=lambda text: get_embeddings(text)  # ✅ Now works!
    )
```

**Changes:**
- Added `from .rag_tools import get_embeddings` to imports in `rag_setup.py`
- Function was being used on lines 80 and 107 without being imported

---

### 5. `AzureOpenAI` Client - Fixed ✅

**Problem:**
```python
# ❌ Incorrect API version and missing validation
from openai import AzureOpenAI

client = AzureOpenAI(
    api_key=os.environ.get("AZURE_OPENAI_KEY"),
    azure_endpoint=os.environ.get("AZURE_OPENAI_ENDPOINT"),
    api_version="2024-02-01"  # ❌ Old API version
)

response = client.embeddings.create(
    input=text,
    model=os.environ.get("AZURE_OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")  # ❌ Should use deployment name
)
```

**Solution:**
```python
# ✅ Updated API version and proper variable validation
from openai import AzureOpenAI

# Validate required environment variables
api_key = os.environ.get("AZURE_OPENAI_KEY")
endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT")
deployment = os.environ.get("AZURE_OPENAI_EMBEDDING_DEPLOYMENT", "text-embedding-3-small")

if not api_key or not endpoint:
    logger.error("Azure OpenAI credentials not configured")
    return [0.0] * 1536

client = AzureOpenAI(
    api_key=api_key,
    azure_endpoint=endpoint,
    api_version="2024-10-21"  # ✅ Updated API version
)

response = client.embeddings.create(
    input=text,
    model=deployment  # ✅ Uses deployment name from Azure OpenAI Studio
)
```

**Changes:**
- Updated API version from `"2024-02-01"` to `"2024-10-21"`
- Changed `AZURE_OPENAI_EMBEDDING_MODEL` to `AZURE_OPENAI_EMBEDDING_DEPLOYMENT` (Azure OpenAI uses deployment names, not model names)
- Added validation for required environment variables
- Added graceful fallback to zero vector if credentials are missing

---

### 6. `rag_get_weekly_summary()` Return Type - Fixed ✅

**Problem:**
```python
# ❌ Function returns dict but annotated as str
def rag_get_weekly_summary() -> str:
    # ...
    return enhanced_summary  # This is a dictionary!
```

**Solution:**
```python
# ✅ Correct return type annotation
def rag_get_weekly_summary() -> Dict[str, Any]:
    # ...
    return enhanced_summary  # Matches return type!
```

**Changes:**
- Changed return type from `str` to `Dict[str, Any]`
- Updated docstring to reflect actual return value

---

### 7. `rag_answer_question()` Return Type - Fixed ✅

**Problem:**
```python
# ❌ Inconsistent return types
def rag_answer_question(question: str, context_window: int = 5) -> str:
    if not results:
        return "I couldn't find..."  # Returns string

    return {
        "question": question,
        "context": context_docs  # Returns dict!
    }

    except Exception as e:
        return f"Error: {e}"  # Returns string
```

**Solution:**
```python
# ✅ Consistent return type - always returns dict
def rag_answer_question(question: str, context_window: int = 5) -> Dict[str, Any]:
    if not results:
        return {
            "question": question,
            "relevant_feedback_count": 0,
            "context": [],
            "message": "I couldn't find..."  # Returns dict
        }

    return {
        "question": question,
        "context": context_docs  # Returns dict
    }

    except Exception as e:
        return {
            "question": question,
            "error": str(e)  # Returns dict
        }
```

**Changes:**
- Changed return type from `str` to `Dict[str, Any]`
- Made all return paths return dictionaries for consistency
- Added structured error responses

---

### 8. `cli_faq.py` Import Error - Fixed ✅

**Problem:**
```python
# ❌ Relative import fails when running file directly in VSCode debugger
from .faq_generator import generate_faq

# Error: ImportError: attempted relative import with no known parent package
```

**Solution:**
```python
# ✅ Support both relative and absolute imports
import sys
import os

# Add parent directory to path for direct execution
if __name__ == "__main__":
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Support both relative and absolute imports
try:
    from .faq_generator import generate_faq
except ImportError:
    from feedbackforge.faq_generator import generate_faq
```

**Changes:**
- Added path manipulation for direct execution
- Added try/except to support both relative and absolute imports
- Now works both as a module (`python -m feedbackforge.cli_faq`) and directly (`python src/feedbackforge/cli_faq.py`)
- Created `.vscode/launch.json` with proper debug configurations

---

## Files Modified

### `/home/abel/git/feedback-forge/src/feedbackforge/rag_search.py`

**Line ~14: Added imports**
```python
from azure.search.documents.indexes.models import (
    # ... existing imports ...
    HnswParameters,  # ← Added
)
from azure.search.documents.models import VectorizedQuery  # ← Added
```

**Line ~120: Fixed HnswAlgorithmConfiguration**
```python
HnswAlgorithmConfiguration(
    name="feedback-hnsw",
    parameters=HnswParameters(  # ← Changed from dict
        m=4,
        ef_construction=400,    # ← Changed from efConstruction
        ef_search=500,          # ← Changed from efSearch
        metric="cosine"
    )
)
```

**Line ~290: Fixed vector_search method**
```python
vector_queries=[
    VectorizedQuery(  # ← Changed from dict
        vector=query_vector,
        k=top,
        fields="text_vector"
    )
]
```

**Line ~345: Fixed hybrid_search method**
```python
vector_queries=[
    VectorizedQuery(  # ← Changed from dict
        vector=query_vector,
        k=top * 2,
        fields="text_vector"
    )
]
```

**Line ~393: Fixed get_facets method**
```python
# Call get_facets() directly and handle None
facets_result = results.get_facets()
facets = facets_result if facets_result is not None else {}
```

### `/home/abel/git/feedback-forge/src/feedbackforge/rag_setup.py`

**Line ~14: Added import**
```python
from .rag_tools import get_embeddings  # ← Added
```

---

## Summary

**Fixed 8 major compilation issues:**
1. ✅ `HnswAlgorithmConfiguration` now uses `HnswParameters` object
2. ✅ `vector_queries` now uses `VectorizedQuery` objects
3. ✅ `get_facets()` now properly calls method and handles None
4. ✅ `rag_setup.py` now imports `get_embeddings` from `rag_tools`
5. ✅ `AzureOpenAI` client uses correct API version and deployment name
6. ✅ `rag_get_weekly_summary()` return type changed from `str` to `Dict[str, Any]`
7. ✅ `rag_answer_question()` return type changed from `str` to `Dict[str, Any]` with consistent returns
8. ✅ `cli_faq.py` supports both relative and absolute imports for VSCode debugging

**All modules now compile, import correctly, and work in VSCode debugger!** 🎉

## Verification

All fixes have been tested and verified:

```bash
# Test imports
✅ python3 -c "from feedbackforge.rag_search import FeedbackRAGSearch"
✅ python3 -c "from feedbackforge.rag_setup import setup_rag_index"
✅ python3 -c "from feedbackforge.rag_tools import get_embeddings"
✅ python3 -c "from feedbackforge.faq_generator import FAQGenerator"

# Comprehensive module test
✅ feedbackforge.rag_search - all functions present
✅ feedbackforge.rag_tools - all functions present
✅ feedbackforge.rag_setup - all functions present
✅ feedbackforge.faq_generator - all functions present

# Python compilation test
✅ rag_search.py compiles
✅ rag_tools.py compiles
✅ rag_setup.py compiles
✅ faq_generator.py compiles

# Function signature verification
✅ rag_get_weekly_summary returns: Dict[str, Any]
✅ rag_answer_question returns: Dict[str, Any]
```

---

Last Updated: 2026-02-27
