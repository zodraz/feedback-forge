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

from azure.ai.evaluation import GroundednessEvaluator, RelevanceEvaluator, CoherenceEvaluator, FluencyEvaluator, AzureAIProject
from azure.identity import DefaultAzureCredential

from feedbackforge.dashboard_agent import create_dashboard_agent


# Azure AI Project configuration
azure_ai_project = AzureAIProject(
    subscription_id=os.environ["AZURE_SUBSCRIPTION_ID"],
    resource_group_name=os.environ["AZURE_RESOURCE_GROUP"],
    project_name=os.environ["AZURE_AI_PROJECT_NAME"],
)

# Model configuration for evaluators
model_config = {
    "azure_endpoint": os.environ.get("AZURE_OPENAI_ENDPOINT"),
    "api_key": os.environ.get("AZURE_OPENAI_API_KEY"),
    "azure_deployment": os.environ.get("AZURE_OPENAI_EVALUATION_DEPLOYMENT", "gpt-4"),
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


async def main():
    """Run cloud evaluation."""

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
        print(f"[{i}/{len(test_cases)}] Processing: {test_case['id']}")

        result = await target_function(query)

        # Add context and ground truth from test case
        result["context"] = json.dumps(test_case.get("golden_answer", {}))
        result["ground_truth"] = json.dumps(test_case.get("golden_answer", {}))

        data.append(result)

    print(f"\nGenerated {len(data)} evaluation entries\n")

    # Save data to JSONL file for evaluation
    data_file = "evaluations/evaluation_data.jsonl"
    print(f"Saving evaluation data to {data_file}...")
    with open(data_file, "w") as f:
        for entry in data:
            f.write(json.dumps(entry) + "\n")

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
