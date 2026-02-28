#!/usr/bin/env python3
"""
Reset Azure AI Search Index

This script deletes and recreates the search index with the correct schema.
Use this if you're getting schema mismatch errors like "StartArray" errors.
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def main():
    # Check environment variables
    search_endpoint = os.environ.get("AZURE_SEARCH_ENDPOINT")
    search_key = os.environ.get("AZURE_SEARCH_KEY")
    index_name = os.environ.get("AZURE_SEARCH_INDEX_NAME", "feedback-index")

    if not search_endpoint:
        print("❌ AZURE_SEARCH_ENDPOINT not set")
        print("   Set it in your environment or .env file")
        return 1

    print("=" * 70)
    print("Azure AI Search Index Reset")
    print("=" * 70)
    print(f"\nEndpoint: {search_endpoint}")
    print(f"Index: {index_name}")

    # Import after checking env vars
    from feedbackforge.rag_search import FeedbackRAGSearch

    try:
        # Create client
        rag_client = FeedbackRAGSearch(
            search_endpoint=search_endpoint,
            index_name=index_name,
            api_key=search_key
        )

        print(f"\n🔍 Checking if index '{index_name}' exists...")

        # Try to get the index
        try:
            existing_index = rag_client.index_client.get_index(index_name)
            print(f"✅ Index exists")
            print(f"\n⚠️  WARNING: This will DELETE the existing index and all data!")
            response = input(f"\nAre you sure you want to delete and recreate '{index_name}'? (yes/no): ")

            if response.lower() != 'yes':
                print("❌ Cancelled")
                return 0

            print(f"\n🗑️  Deleting index '{index_name}'...")
            rag_client.index_client.delete_index(index_name)
            print("✅ Index deleted")

        except Exception as e:
            print(f"ℹ️  Index doesn't exist yet (will create new one)")

        # Create fresh index
        print(f"\n🔧 Creating index '{index_name}' with correct schema...")
        rag_client.create_index(embedding_dimensions=1536)
        print(f"✅ Index '{index_name}' created successfully!")

        print("\n" + "=" * 70)
        print("✅ Index Reset Complete!")
        print("=" * 70)
        print("\nNext steps:")
        print("1. Run: python -m feedbackforge faq")
        print("   (This will auto-index the data)")
        print("\nOR")
        print("\n1. Manually index data:")
        print("   from feedbackforge.rag_setup import RAGSetup")
        print("   setup = RAGSetup()")
        print("   setup.ensure_data_indexed(force=True)")

        return 0

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
