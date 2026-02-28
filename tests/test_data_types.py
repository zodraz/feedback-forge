#!/usr/bin/env python3
"""
Test script to validate data types before indexing to Azure Search.
This helps debug the "StartArray" error by checking data structure.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from feedbackforge.data_store import feedback_store
from dataclasses import asdict

def check_data_types():
    """Check the types of all fields in feedback data."""
    print("=" * 70)
    print("Feedback Data Type Validation")
    print("=" * 70)

    feedback_items = feedback_store.feedback
    print(f"\nTotal items: {len(feedback_items)}")

    if not feedback_items:
        print("❌ No feedback items found!")
        return

    # Check first few items
    for idx, item in enumerate(feedback_items[:3]):
        print(f"\n--- Item {idx + 1}: {item.id} ---")
        item_dict = asdict(item)

        for key, value in item_dict.items():
            value_type = type(value).__name__

            # Flag problematic types
            is_list = isinstance(value, list)

            if key in ['topics', 'competitor_mentions']:
                # Should be lists
                if not is_list:
                    print(f"  ⚠️  {key}: {value_type} = {value} (SHOULD BE LIST!)")
                else:
                    print(f"  ✅ {key}: list[{len(value)}] = {value}")
            else:
                # Should NOT be lists
                if is_list:
                    print(f"  ❌ {key}: {value_type} = {value} (SHOULD NOT BE LIST!)")
                else:
                    # Show first 50 chars for strings
                    display_value = str(value)[:50] + "..." if len(str(value)) > 50 else value
                    print(f"  ✅ {key}: {value_type} = {display_value}")

    print("\n" + "=" * 70)
    print("Type Validation Complete")
    print("=" * 70)
    print("\nLegend:")
    print("  ✅ = Correct type")
    print("  ❌ = WRONG! Primitive field has array value")
    print("  ⚠️  = WRONG! Collection field doesn't have array value")
    print("\n")

if __name__ == "__main__":
    check_data_types()
