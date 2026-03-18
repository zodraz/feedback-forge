#!/usr/bin/env python3
"""
Azure AI Foundry Cloud Evaluation
Following: https://learn.microsoft.com/en-us/azure/foundry/how-to/develop/cloud-evaluation?tabs=python
"""

import asyncio
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from azure.ai.evaluation import GroundednessEvaluator, RelevanceEvaluator, CoherenceEvaluator, FluencyEvaluator, AzureAIProject
from azure.identity import DefaultAzureCredential

from feedbackforge.dashboard_agent import create_dashboard_agent

# Load environment variables from .env file
load_dotenv()


def validate_environment():
    """Validate that required environment variables are set."""
    required_vars = [
        "AZURE_SUBSCRIPTION_ID",
        "AZURE_RESOURCE_GROUP",
        "AZURE_AI_PROJECT_NAME",
        "AZURE_OPENAI_ENDPOINT",
        "AZURE_OPENAI_API_KEY",
    ]

    missing_vars = [var for var in required_vars if not os.environ.get(var)]

    if missing_vars:
        print("\n❌ ERROR: Missing required environment variables:\n")
        for var in missing_vars:
            print(f"   - {var}")
        print("\nPlease set these environment variables before running evaluations.")
        print("\nOption 1: Create a .env file in the project root:")
        print("  AZURE_SUBSCRIPTION_ID=your-subscription-id")
        print("  AZURE_RESOURCE_GROUP=your-resource-group")
        print("  AZURE_AI_PROJECT_NAME=your-project-name")
        print("  AZURE_OPENAI_ENDPOINT=https://your-endpoint.openai.azure.com/")
        print("  AZURE_OPENAI_API_KEY=your-api-key")
        print("  AZURE_OPENAI_EVALUATION_DEPLOYMENT=gpt-4o  # or gpt-4o-mini")
        print("\nOption 2: Export environment variables:")
        print("  export AZURE_SUBSCRIPTION_ID=your-subscription-id")
        print("  export AZURE_RESOURCE_GROUP=your-resource-group")
        print("  # ... etc")
        sys.exit(1)


# Validate environment before proceeding
validate_environment()

# Azure AI Project configuration
azure_ai_project = AzureAIProject(
    subscription_id=os.environ["AZURE_SUBSCRIPTION_ID"],
    resource_group_name=os.environ["AZURE_RESOURCE_GROUP"],
    project_name=os.environ["AZURE_AI_PROJECT_NAME"],
)

# Model configuration for evaluators
# Note: gpt-4o models require max_completion_tokens instead of max_tokens
# Using the latest API version and type="azure_openai" for compatibility
model_config = {
    "type": "azure_openai",
    "azure_endpoint": os.environ.get("AZURE_OPENAI_ENDPOINT"),
    "api_key": os.environ.get("AZURE_OPENAI_API_KEY"),
    "azure_deployment": os.environ.get("AZURE_OPENAI_EVALUATION_DEPLOYMENT", "gpt-4o"),
    "api_version": "2024-08-01-preview",  # Latest API version for gpt-4o support
}


async def target_function(query: str) -> dict:
    """Target function that calls the FeedbackForge agent."""
    agent = create_dashboard_agent()
    response = await agent.run(query)
    response_text = str(response.text) if hasattr(response, "text") else str(response)

    return {
        "query": query,
        "response": response_text,
    }


async def main(local_only: bool = False):
    """Run evaluation.

    Args:
        local_only: If True, skip cloud evaluation and only generate responses locally
    """

    # Load test cases
    dataset_path = "evaluations/datasets/test_cases.json"
    print(f"Loading test cases from {dataset_path}...")

    with open(dataset_path, "r") as f:
        test_cases = json.load(f)

    print(f"Loaded {len(test_cases)} test cases\n")

    # Run agent on test cases to generate evaluation data
    print("Running agent on test cases...")
    data = []

    for i, test_case in enumerate(test_cases, 1):
        query = test_case["query"]
        response_id = test_case.get("response_id", f"response_{i}")
        print(f"[{i}/{len(test_cases)}] Processing: {response_id}")

        import time
        start_time = time.time()
        result = await target_function(query)
        latency = time.time() - start_time

        # Update test case with generated response and metrics
        test_case["response"] = result["response"]
        test_case["latency"] = latency
        test_case["response_length"] = len(result["response"])

        data.append(test_case)

    print(f"\nGenerated {len(data)} evaluation entries\n")

    # Save data to JSONL file for evaluation
    data_file = "evaluations/evaluation_data.jsonl"
    print(f"Saving evaluation data to {data_file}...")
    with open(data_file, "w") as f:
        for entry in data:
            f.write(json.dumps(entry) + "\n")

    # Also save as JSON for easy viewing
    output_file = "evaluations/evaluation_results.json"
    with open(output_file, "w") as f:
        json.dump(data, f, indent=2)
    print(f"Saved evaluation data to {output_file}")

    if local_only:
        print("\n" + "="*80)
        print("LOCAL EVALUATION COMPLETE")
        print("="*80)
        print(f"\nGenerated {len(data)} responses with metrics:")
        print(f"  - Average latency: {sum(d['latency'] for d in data) / len(data):.2f}s")
        print(f"  - Average response length: {sum(d['response_length'] for d in data) / len(data):.0f} chars")
        print(f"\nResults saved to:")
        print(f"  - {output_file}")
        print(f"  - {data_file}")
        print("\n💡 To run cloud evaluation with Azure AI, fix RBAC permissions and run without --local flag")
        print("="*80)
        return data

    # Initialize evaluators
    print("Initializing evaluators...")
    credential = DefaultAzureCredential()

    groundedness_eval = GroundednessEvaluator(model_config, credential=credential)
    relevance_eval = RelevanceEvaluator(model_config, credential=credential)
    coherence_eval = CoherenceEvaluator(model_config, credential=credential)
    fluency_eval = FluencyEvaluator(model_config, credential=credential)

    # Run evaluation
    print("Running cloud evaluation...\n")

    from azure.ai.evaluation import evaluate

    result = evaluate(
        data=data_file,
        evaluators={
            "groundedness": groundedness_eval,
            "relevance": relevance_eval,
            "coherence": coherence_eval,
            "fluency": fluency_eval,
        },
        azure_ai_project=azure_ai_project,
    )

    # Print results
    print("\n" + "="*80)
    print("EVALUATION RESULTS")
    print("="*80)
    print(json.dumps(result, indent=2))
    print("="*80)


if __name__ == "__main__":
    asyncio.run(main())
