#!/usr/bin/env python3
"""
Test document preparation for Azure Search indexing.
Simulates the exact process without actually sending to Azure.
"""

import sys
import json
from pathlib import Path
from datetime import timezone
from dataclasses import asdict

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from feedbackforge.data_store import feedback_store

def prepare_document(item_dict):
    """Simulate the document preparation from rag_search.py"""

    # Convert datetime to ISO string with timezone (from rag_setup.py)
    if item_dict.get('timestamp'):
        ts = item_dict['timestamp']
        if isinstance(ts, str):
            if not ts.endswith('Z') and '+' not in ts and ts.count(':') == 2:
                ts += 'Z'
            item_dict['timestamp'] = ts
        else:
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
            item_dict['timestamp'] = ts.isoformat()

    # Helper function to ensure single value (from rag_search.py)
    def ensure_single_value(value, default=None):
        if isinstance(value, list):
            return value[0] if value else default
        return value if value is not None else default

    # Collection fields validation
    topics = item_dict.get("topics", [])
    if topics is None:
        topics = []
    elif not isinstance(topics, list):
        topics = [topics]
    topics = [str(t) for t in topics if t is not None]

    competitor_mentions = item_dict.get("competitor_mentions", [])
    if competitor_mentions is None:
        competitor_mentions = []
    elif not isinstance(competitor_mentions, list):
        competitor_mentions = [competitor_mentions]
    competitor_mentions = [str(c) for c in competitor_mentions if c is not None]

    # Ensure ALL string fields are not lists
    doc_id = ensure_single_value(item_dict.get("id"))
    text = ensure_single_value(item_dict.get("text"))
    sentiment = ensure_single_value(item_dict.get("sentiment"))
    customer_segment = ensure_single_value(item_dict.get("customer_segment"))
    customer_id = ensure_single_value(item_dict.get("customer_id"))
    customer_name = ensure_single_value(item_dict.get("customer_name"))
    product_version = ensure_single_value(item_dict.get("product_version"))
    platform = ensure_single_value(item_dict.get("platform"))

    # Numeric fields
    rating = ensure_single_value(item_dict.get("rating"))
    if rating is not None:
        rating = int(rating)

    sentiment_score = ensure_single_value(item_dict.get("sentiment_score"), 0.0)
    if sentiment_score is not None:
        sentiment_score = float(sentiment_score)

    # Boolean field
    is_urgent = ensure_single_value(item_dict.get("is_urgent"), False)
    if not isinstance(is_urgent, bool):
        is_urgent = bool(is_urgent)

    # Timestamp field
    timestamp = ensure_single_value(item_dict.get("timestamp"))
    if timestamp is not None and not isinstance(timestamp, str):
        timestamp = str(timestamp)

    doc = {
        "id": doc_id,
        "text": text,
        "sentiment": sentiment,
        "sentiment_score": sentiment_score,
        "topics": topics,
        "customer_segment": customer_segment,
        "customer_id": customer_id,
        "customer_name": customer_name,
        "rating": rating,
        "timestamp": timestamp,
        "product_version": product_version,
        "platform": platform,
        "is_urgent": is_urgent,
        "competitor_mentions": competitor_mentions,
        "text_vector": [0.1] * 1536,  # Fake embedding
    }

    return doc

def validate_document(doc):
    """Validate the document structure"""
    errors = []

    for key, value in doc.items():
        if key in ['topics', 'competitor_mentions', 'text_vector']:
            # These should be lists
            if not isinstance(value, list):
                errors.append(f"❌ {key}: should be list, got {type(value).__name__}")
        elif key in ['rating', 'sentiment_score']:
            # These should be numbers
            if value is not None and not isinstance(value, (int, float)):
                errors.append(f"❌ {key}: should be numeric, got {type(value).__name__}")
        elif key == 'is_urgent':
            # This should be boolean
            if not isinstance(value, bool):
                errors.append(f"❌ {key}: should be bool, got {type(value).__name__}")
        else:
            # All other fields should be strings or None
            if value is not None and isinstance(value, list):
                errors.append(f"❌ {key}: should NOT be list, got {value}")

    return errors

def main():
    print("=" * 70)
    print("Document Preparation Test")
    print("=" * 70)

    feedback_items = feedback_store.feedback[:3]

    for idx, item in enumerate(feedback_items):
        print(f"\n--- Testing Item {idx + 1}: {item.id} ---")

        # Convert to dict
        item_dict = asdict(item)

        # Prepare document
        try:
            doc = prepare_document(item_dict)

            # Validate
            errors = validate_document(doc)

            if errors:
                print("❌ VALIDATION FAILED:")
                for error in errors:
                    print(f"  {error}")
            else:
                print("✅ Document validation PASSED")
                print(f"  id: {doc['id']}")
                print(f"  timestamp: {doc['timestamp']}")
                print(f"  topics: {doc['topics']}")
                print(f"  rating: {doc['rating']} (type: {type(doc['rating']).__name__})")
                print(f"  is_urgent: {doc['is_urgent']} (type: {type(doc['is_urgent']).__name__})")

                # Try to serialize to JSON (this is what Azure Search does)
                try:
                    json_str = json.dumps(doc)
                    print(f"  ✅ JSON serialization successful ({len(json_str)} bytes)")
                except Exception as e:
                    print(f"  ❌ JSON serialization failed: {e}")

        except Exception as e:
            print(f"❌ Document preparation failed: {e}")
            import traceback
            traceback.print_exc()

    print("\n" + "=" * 70)
    print("Test Complete")
    print("=" * 70)

if __name__ == "__main__":
    main()
