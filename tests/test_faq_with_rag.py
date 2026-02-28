"""
Test script to verify FAQ Generator uses Azure AI Search
"""

import logging
from feedbackforge.rag_search import rag_search_client
from feedbackforge.faq_generator import generate_faq

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_rag_integration():
    """Test that FAQ generator uses Azure AI Search."""

    print("=" * 70)
    print("Testing FAQ Generator with Azure AI Search RAG")
    print("=" * 70)
    print()

    # Check if RAG is configured
    print("1. Checking RAG configuration...")
    if not rag_search_client:
        print("❌ FAILED: RAG client not configured")
        print("   Set AZURE_SEARCH_ENDPOINT and AZURE_SEARCH_KEY in .env")
        print("   Then run: python -m feedbackforge.rag_setup")
        return False

    print("✅ RAG client configured")
    print(f"   Endpoint: {rag_search_client.search_endpoint}")
    print(f"   Index: {rag_search_client.index_name}")
    print()

    # Test FAQ generation
    print("2. Generating FAQs with RAG...")
    print("   (This will use Azure AI Search hybrid search + vector clustering)")
    print()

    try:
        result = generate_faq(
            timeframe_days=30,
            min_occurrences=2,
            max_faqs=5,
            answer_style="helpful",
            output_formats=["markdown"]
        )

        if not result['faqs']:
            print("⚠️ No FAQs generated (might need more feedback data)")
            print("   Try: python -m feedbackforge.rag_setup  (to index feedback)")
            return False

        print(f"✅ Generated {len(result['faqs'])} FAQs using Azure AI Search")
        print(f"   From {result['theme_count']} themes")
        print()

        # Show first FAQ as example
        if result['faqs']:
            faq = result['faqs'][0]
            print("3. Example FAQ Entry:")
            print(f"   Q: {faq['question']}")
            print(f"   A: {faq['answer'][:100]}...")
            print(f"   Frequency: {faq['frequency']} mentions")
            print(f"   Platforms: {', '.join(faq['platforms'])}")
            print()

        print("✅ SUCCESS: FAQ Generator is using Azure AI Search RAG!")
        print()
        print("=" * 70)
        return True

    except ValueError as e:
        if "RAG client required" in str(e):
            print("❌ FAILED: RAG not properly configured")
            print(f"   Error: {e}")
            return False
        raise
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False


if __name__ == "__main__":
    success = test_rag_integration()
    exit(0 if success else 1)
