"""
Example: Fetch GitHub Issues and Ingest into FeedbackForge
===========================================================

This script demonstrates how to programmatically use the MCP server
to fetch GitHub issues and ingest them into FeedbackForge.

Usage:
    python examples/fetch_github_feedback.py owner/repo

Example:
    python examples/fetch_github_feedback.py microsoft/vscode
    python examples/fetch_github_feedback.py anthropics/anthropic-sdk-python
"""

import asyncio
import json
import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from feedbackforge.mcp_server import fetch_github_issues, ingest_feedback_to_store


async def fetch_and_ingest(repo: str, state: str = "open", labels: str | None = None, limit: int = 50):
    """
    Fetch GitHub issues and ingest them into FeedbackForge data store.

    Args:
        repo: Repository in format 'owner/repo'
        state: Issue state ('open', 'closed', 'all')
        labels: Comma-separated labels to filter
        limit: Maximum number of issues to fetch
    """
    print(f"\n{'='*60}")
    print(f"Fetching GitHub Issues from {repo}")
    print(f"{'='*60}\n")

    # Step 1: Fetch issues from GitHub
    args = {
        "repo": repo,
        "state": state,
        "limit": limit
    }

    if labels:
        args["labels"] = labels

    print(f"📡 Fetching {limit} {state} issues...")
    if labels:
        print(f"🏷️  Filtering by labels: {labels}")

    try:
        result = await fetch_github_issues(args)
        result_text = result[0].text
        data = json.loads(result_text)

        if "error" in data:
            print(f"❌ Error: {data['error']}")
            if "hint" in data:
                print(f"💡 Hint: {data['hint']}")
            return

        print(f"✅ Fetched {data['fetched_count']} issues from GitHub\n")

        # Show sample
        if data["feedback_items"]:
            sample = data["feedback_items"][0]
            print("Sample feedback item:")
            print(f"  ID: {sample['id']}")
            print(f"  Text: {sample['text'][:100]}...")
            print(f"  Sentiment: {sample['sentiment']}")
            print(f"  Topics: {', '.join(sample['topics'])}")
            print(f"  Urgent: {sample['is_urgent']}\n")

        # Step 2: Ingest into FeedbackForge
        print("💾 Ingesting feedback items into FeedbackForge data store...")

        ingest_result = await ingest_feedback_to_store({
            "feedback_items": data["feedback_items"],
            "source": "github"
        })

        ingest_data = json.loads(ingest_result[0].text)

        if ingest_data.get("success"):
            print(f"✅ Successfully ingested {ingest_data['ingested_count']}/{ingest_data['total_items']} items")

            if ingest_data.get("errors"):
                print(f"⚠️  {len(ingest_data['errors'])} errors occurred during ingestion")

            print(f"\n{'='*60}")
            print("Next steps:")
            print("  1. Start chat mode: python -m feedbackforge chat")
            print("  2. Query: 'Show me feedback from GitHub'")
            print("  3. Query: 'What are the top issues from the GitHub data?'")
            print(f"{'='*60}\n")
        else:
            print(f"❌ Ingestion failed: {ingest_data.get('error')}")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python fetch_github_feedback.py REPO [STATE] [LABELS] [LIMIT]")
        print("\nExamples:")
        print("  python fetch_github_feedback.py microsoft/vscode")
        print("  python fetch_github_feedback.py microsoft/vscode open bug 25")
        print("  python fetch_github_feedback.py anthropics/anthropic-sdk-python all")
        sys.exit(1)

    repo = sys.argv[1]
    state = sys.argv[2] if len(sys.argv) > 2 else "open"
    labels = sys.argv[3] if len(sys.argv) > 3 else None
    limit = int(sys.argv[4]) if len(sys.argv) > 4 else 50

    # Check for GitHub token
    if not os.environ.get("GITHUB_TOKEN"):
        print("⚠️  Warning: GITHUB_TOKEN not set. You'll have lower rate limits (60 req/hour)")
        print("   Set it with: export GITHUB_TOKEN=your_token\n")

    await fetch_and_ingest(repo, state, labels, limit)


if __name__ == "__main__":
    asyncio.run(main())
