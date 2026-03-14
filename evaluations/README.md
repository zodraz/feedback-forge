# Azure AI Foundry Cloud Evaluation

Following the official Microsoft documentation:
https://learn.microsoft.com/en-us/azure/foundry/how-to/develop/cloud-evaluation?tabs=python

## Setup

### Install dependencies

```bash
pip install -r evaluations/requirements.txt
```

### Set environment variables

```bash
# Required for agent
export AZURE_AI_PROJECT_ENDPOINT="your-endpoint"
export AZURE_OPENAI_RESPONSES_DEPLOYMENT_NAME="your-deployment"

# Required for cloud evaluation
export AZURE_SUBSCRIPTION_ID="your-subscription-id"
export AZURE_RESOURCE_GROUP="your-resource-group"
export AZURE_AI_PROJECT_NAME="your-project-name"

# Required for evaluators (GPT-4)
export AZURE_OPENAI_ENDPOINT="https://your-resource.openai.azure.com"
export AZURE_OPENAI_API_KEY="your-api-key"
export AZURE_OPENAI_EVALUATION_DEPLOYMENT="gpt-4"
```

## Run Evaluation

```bash
python -m evaluations.run_evaluation
```

## What it does

1. Loads test cases from `datasets/test_cases.json`
2. Runs your FeedbackForge agent on each test case
3. Submits results to Azure AI Foundry for cloud evaluation
4. Uses GPT-4 evaluators: Groundedness, Relevance, Coherence, Fluency
5. Returns evaluation scores and metrics

## Evaluators

- **GroundednessEvaluator**: Measures if the response is grounded in the provided context
- **RelevanceEvaluator**: Measures if the response addresses the query
- **CoherenceEvaluator**: Measures logical consistency
- **FluencyEvaluator**: Measures language quality

All evaluators run in Azure AI Foundry using GPT-4.
