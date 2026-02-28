"""
FAQ Generator Examples
======================

Demonstrates different ways to initialize and use the FAQ Generator.
"""

import os
from datetime import datetime


def example_1_simple():
    """
    Example 1: Simplest usage - auto-initialize from .env

    Prerequisites:
    - .env file with AZURE_SEARCH_ENDPOINT, AZURE_SEARCH_KEY
    - Azure AI Search index created (run: python -m feedbackforge.rag_setup)
    """
    print("=" * 70)
    print("Example 1: Simple Usage (Auto-Initialize)")
    print("=" * 70)

    from feedbackforge.faq_generator import generate_faq

    # Just call it - auto-initializes from environment
    result = generate_faq(
        timeframe_days=30,
        min_occurrences=3,
        max_faqs=10,
        answer_style="helpful",
        output_formats=["markdown", "html"]
    )

    print(f"✅ Generated {len(result['faqs'])} FAQs")
    print(f"   Exported to: {result['exports']}")
    print()


def example_2_with_error_handling():
    """
    Example 2: With proper error handling

    Use this pattern in production code.
    """
    print("=" * 70)
    print("Example 2: With Error Handling")
    print("=" * 70)

    from feedbackforge.rag_search import init_rag_search
    from feedbackforge.faq_generator import FAQGenerator

    # Initialize RAG client first
    rag_client = init_rag_search()

    if not rag_client:
        print("❌ Azure AI Search not configured!")
        print("   Please set environment variables:")
        print("   - AZURE_SEARCH_ENDPOINT")
        print("   - AZURE_SEARCH_KEY")
        return

    print("✅ RAG client initialized")

    # Create generator
    generator = FAQGenerator(rag_client=rag_client)

    try:
        # Find themes
        themes = generator.find_common_themes(
            timeframe_days=30,
            min_occurrences=3,
            max_themes=10
        )

        print(f"✅ Found {len(themes)} common themes")

        # Generate FAQs
        faqs = generator.generate_faq_entries(themes, answer_style="friendly")

        print(f"✅ Generated {len(faqs)} FAQ entries")

        # Export
        generator.export_to_markdown(faqs, "my_faq.md")
        generator.export_to_html(faqs, "my_faq.html")

        print("✅ Exported to my_faq.md and my_faq.html")

    except ValueError as e:
        print(f"❌ Configuration error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

    print()


def example_3_custom_config():
    """
    Example 3: Custom RAG client configuration

    Use this when you need non-standard configuration.
    """
    print("=" * 70)
    print("Example 3: Custom Configuration")
    print("=" * 70)

    from feedbackforge.rag_search import FeedbackRAGSearch
    from feedbackforge.faq_generator import FAQGenerator

    # Create RAG client with custom settings
    custom_rag = FeedbackRAGSearch(
        search_endpoint=os.getenv("AZURE_SEARCH_ENDPOINT"),
        index_name="feedback-custom",  # Custom index name
        api_key=os.getenv("AZURE_SEARCH_KEY")
    )

    # Pass to generator
    generator = FAQGenerator(rag_client=custom_rag)

    print("✅ Using custom RAG configuration")
    print(f"   Endpoint: {custom_rag.search_endpoint}")
    print(f"   Index: {custom_rag.index_name}")

    # Use it
    themes = generator.find_common_themes(timeframe_days=7)
    print(f"✅ Found {len(themes)} themes from last 7 days")
    print()


def example_4_multiple_environments():
    """
    Example 4: Different configurations for dev/staging/prod
    """
    print("=" * 70)
    print("Example 4: Multiple Environments")
    print("=" * 70)

    from feedbackforge.rag_search import FeedbackRAGSearch
    from feedbackforge.faq_generator import FAQGenerator

    # Development environment
    dev_rag = FeedbackRAGSearch(
        search_endpoint="https://dev-search.search.windows.net",
        index_name="feedback-dev",
        api_key=os.getenv("DEV_SEARCH_KEY")
    )

    # Production environment
    prod_rag = FeedbackRAGSearch(
        search_endpoint="https://prod-search.search.windows.net",
        index_name="feedback-prod",
        api_key=None  # Use DefaultAzureCredential in prod
    )

    # Create generators
    dev_gen = FAQGenerator(rag_client=dev_rag)
    prod_gen = FAQGenerator(rag_client=prod_rag)

    print("✅ Initialized dev and prod generators")

    # Generate FAQs from dev (short timeframe for testing)
    dev_themes = dev_gen.find_common_themes(timeframe_days=7, max_themes=5)
    print(f"   Dev: {len(dev_themes)} themes")

    # Generate FAQs from prod (longer timeframe)
    prod_themes = prod_gen.find_common_themes(timeframe_days=30, max_themes=15)
    print(f"   Prod: {len(prod_themes)} themes")
    print()


def example_5_scheduled_generation():
    """
    Example 5: Daily FAQ generation (for cron jobs)
    """
    print("=" * 70)
    print("Example 5: Scheduled FAQ Generation")
    print("=" * 70)

    from feedbackforge.faq_generator import generate_faq

    # Generate daily FAQs
    timestamp = datetime.now().strftime("%Y-%m-%d")

    result = generate_faq(
        timeframe_days=7,  # Last week
        min_occurrences=2,  # Lower threshold for daily
        max_faqs=20,
        answer_style="helpful",
        output_formats=["markdown", "html"]
    )

    # Rename files with date
    import os
    for old_file in result['exports']:
        base, ext = os.path.splitext(old_file)
        new_file = f"faq_daily_{timestamp}{ext}"
        if os.path.exists(old_file):
            os.rename(old_file, new_file)
            print(f"✅ Generated: {new_file}")

    print(f"✅ Daily FAQ generation complete: {len(result['faqs'])} FAQs")
    print()


def example_6_api_endpoint():
    """
    Example 6: FAQ generation as API endpoint
    """
    print("=" * 70)
    print("Example 6: API Endpoint (FastAPI)")
    print("=" * 70)

    print("Example code:")
    print("""
from fastapi import FastAPI, HTTPException
from feedbackforge.rag_search import init_rag_search
from feedbackforge.faq_generator import FAQGenerator

app = FastAPI()

# Initialize at startup
@app.on_event("startup")
async def startup_event():
    global faq_generator

    rag_client = init_rag_search()
    if not rag_client:
        print("⚠️ Warning: RAG not configured")

    faq_generator = FAQGenerator(rag_client=rag_client)

@app.get("/api/faq")
async def get_faq(days: int = 30, min_mentions: int = 3, max_count: int = 15):
    '''Generate FAQs on demand.'''

    if not faq_generator.rag_client:
        raise HTTPException(500, "RAG not configured")

    themes = faq_generator.find_common_themes(
        timeframe_days=days,
        min_occurrences=min_mentions,
        max_themes=max_count
    )

    faqs = faq_generator.generate_faq_entries(themes)

    return {
        "count": len(faqs),
        "generated_at": datetime.now().isoformat(),
        "faqs": faqs
    }
""")
    print()


def main():
    """Run all examples."""
    print("\n")
    print("╔══════════════════════════════════════════════════════════════════╗")
    print("║         FAQ Generator - Initialization Examples                 ║")
    print("╚══════════════════════════════════════════════════════════════════╝")
    print()

    examples = [
        ("Simple Usage", example_1_simple),
        ("With Error Handling", example_2_with_error_handling),
        ("Custom Configuration", example_3_custom_config),
        ("Multiple Environments", example_4_multiple_environments),
        ("Scheduled Generation", example_5_scheduled_generation),
        ("API Endpoint", example_6_api_endpoint),
    ]

    for i, (name, func) in enumerate(examples, 1):
        print(f"\n[{i}/{len(examples)}] {name}")
        print("-" * 70)

        try:
            func()
        except Exception as e:
            print(f"❌ Example failed: {e}")
            print("   (This might be expected if RAG is not configured)")

        print()

    print("=" * 70)
    print("Examples complete!")
    print()
    print("To run individual examples:")
    print("  python examples/faq_examples.py")
    print()


if __name__ == "__main__":
    main()
