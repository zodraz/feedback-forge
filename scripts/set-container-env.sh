#!/bin/bash
# Set environment variables for Azure Container App
# This script reads from .env and configures the container app

set -e

# Configuration - UPDATE THESE VALUES
RESOURCE_GROUP="feedbackforge-rg"  # Replace with your resource group name
CONTAINER_APP_NAME="feedbackforge-backend"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}================================${NC}"
echo -e "${YELLOW}Azure Container App Environment Variable Setup${NC}"
echo -e "${YELLOW}================================${NC}"
echo ""
echo -e "${YELLOW}Resource Group:${NC} $RESOURCE_GROUP"
echo -e "${YELLOW}Container App:${NC} $CONTAINER_APP_NAME"
echo ""

# Check if user wants to proceed
read -p "Are these settings correct? (y/n): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${RED}Aborted. Please update RESOURCE_GROUP and CONTAINER_APP_NAME in the script.${NC}"
    exit 1
fi

# Check if Azure CLI is installed and logged in
if ! command -v az &> /dev/null; then
    echo -e "${RED}Error: Azure CLI is not installed${NC}"
    exit 1
fi

if ! az account show &> /dev/null; then
    echo -e "${RED}Error: Not logged in to Azure. Run 'az login' first${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Azure CLI authenticated${NC}"
echo ""

# Build environment variables from .env
# Note: Only setting non-empty variables
echo -e "${YELLOW}Reading environment variables from .env file...${NC}"

ENV_VARS=""

# Function to add env var if not empty
add_env_var() {
    local key=$1
    local value=$2
    if [ -n "$value" ]; then
        if [ -n "$ENV_VARS" ]; then
            ENV_VARS="$ENV_VARS $key=$value"
        else
            ENV_VARS="$key=$value"
        fi
        echo -e "${GREEN}  ✓ ${NC}$key"
    else
        echo -e "${YELLOW}  ⊘ ${NC}$key (empty, skipping)"
    fi
}

# Read .env file and extract variables
# Azure AI
AZURE_AI_PROJECT_ENDPOINT=$(grep -E "^AZURE_AI_PROJECT_ENDPOINT=" .env | cut -d '=' -f2- | tr -d '"')
AZURE_AI_MODEL_DEPLOYMENT_NAME=$(grep -E "^AZURE_AI_MODEL_DEPLOYMENT_NAME=" .env | cut -d '=' -f2- | tr -d '"')
BING_CONNECTION_ID=$(grep -E "^BING_CONNECTION_ID=" .env | cut -d '=' -f2- | tr -d '"')

# Azure Search
AZURE_SEARCH_ENDPOINT=$(grep -E "^AZURE_SEARCH_ENDPOINT=" .env | cut -d '=' -f2- | tr -d '"')
AZURE_SEARCH_API_KEY=$(grep -E "^AZURE_SEARCH_API_KEY=" .env | cut -d '=' -f2- | tr -d '"')
AZURE_SEARCH_INDEX_NAME=$(grep -E "^AZURE_SEARCH_INDEX_NAME=" .env | cut -d '=' -f2- | tr -d '"')

# Azure OpenAI
AZURE_OPENAI_ENDPOINT=$(grep -E "^AZURE_OPENAI_ENDPOINT=" .env | cut -d '=' -f2- | tr -d '"')
AZURE_OPENAI_CHAT_DEPLOYMENT_NAME=$(grep -E "^AZURE_OPENAI_CHAT_DEPLOYMENT_NAME=" .env | cut -d '=' -f2- | tr -d '"')
AZURE_OPENAI_KEY=$(grep -E "^AZURE_OPENAI_KEY=" .env | cut -d '=' -f2- | tr -d '"')
AZURE_OPENAI_RESPONSES_DEPLOYMENT_NAME=$(grep -E "^AZURE_OPENAI_RESPONSES_DEPLOYMENT_NAME=" .env | cut -d '=' -f2- | tr -d '"')
AZURE_OPENAI_EMBEDDING_MODEL=$(grep -E "^AZURE_OPENAI_EMBEDDING_MODEL=" .env | cut -d '=' -f2- | tr -d '"')

# API Gateway
AZURE_API_GATEWAY_ENDPOINT=$(grep -E "^AZURE_API_GATEWAY_ENDPOINT=" .env | cut -d '=' -f2- | tr -d '"')
AZURE_API_GATEWAY_KEY=$(grep -E "^AZURE_API_GATEWAY_KEY=" .env | cut -d '=' -f2- | tr -d '"')
AZURE_AI_MODEL_DEPLOYMENT_VERSION=$(grep -E "^AZURE_AI_MODEL_DEPLOYMENT_VERSION=" .env | cut -d '=' -f2- | tr -d '"')

# OpenAI (optional)
OPENAI_API_KEY=$(grep -E "^OPENAI_API_KEY=" .env | cut -d '=' -f2- | tr -d '"')
OPENAI_CHAT_MODEL_ID=$(grep -E "^OPENAI_CHAT_MODEL_ID=" .env | cut -d '=' -f2- | tr -d '"')
OPENAI_RESPONSES_MODEL_ID=$(grep -E "^OPENAI_RESPONSES_MODEL_ID=" .env | cut -d '=' -f2- | tr -d '"')

# Application Insights
APPLICATIONINSIGHTS_CONNECTION_STRING=$(grep -E "^APPLICATIONINSIGHTS_CONNECTION_STRING=" .env | cut -d '=' -f2- | tr -d '"')
OTEL_SERVICE_NAME=$(grep -E "^OTEL_SERVICE_NAME=" .env | cut -d '=' -f2- | tr -d '"')
DISABLE_TELEMETRY=$(grep -E "^DISABLE_TELEMETRY=" .env | cut -d '=' -f2- | tr -d '"')

# Cosmos DB
COSMOS_DB_ENDPOINT=$(grep -E "^COSMOS_DB_ENDPOINT=" .env | cut -d '=' -f2- | tr -d '"')
COSMOS_DB_AUTH_METHOD=$(grep -E "^COSMOS_DB_AUTH_METHOD=" .env | cut -d '=' -f2- | tr -d '"')
COSMOS_DB_KEY=$(grep -E "^COSMOS_DB_KEY=" .env | cut -d '=' -f2- | tr -d '"')
COSMOS_DB_DATABASE=$(grep -E "^COSMOS_DB_DATABASE=" .env | cut -d '=' -f2- | tr -d '"')
COSMOS_DB_CONTAINER=$(grep -E "^COSMOS_DB_CONTAINER=" .env | cut -d '=' -f2- | tr -d '"')

# Redis
REDIS_URL=$(grep -E "^REDIS_URL=" .env | cut -d '=' -f2- | tr -d '"')

# Session
SESSION_TTL=$(grep -E "^SESSION_TTL=" .env | cut -d '=' -f2- | tr -d '"')

# Add all variables
echo ""
echo -e "${YELLOW}Variables to be set:${NC}"

# Critical variables for the current error
add_env_var "AZURE_OPENAI_ENDPOINT" "$AZURE_OPENAI_ENDPOINT"
add_env_var "AZURE_OPENAI_KEY" "$AZURE_OPENAI_KEY"
add_env_var "AZURE_AI_MODEL_DEPLOYMENT_NAME" "$AZURE_AI_MODEL_DEPLOYMENT_NAME"

# Other Azure AI variables
add_env_var "AZURE_AI_PROJECT_ENDPOINT" "$AZURE_AI_PROJECT_ENDPOINT"
add_env_var "AZURE_OPENAI_CHAT_DEPLOYMENT_NAME" "$AZURE_OPENAI_CHAT_DEPLOYMENT_NAME"
add_env_var "AZURE_OPENAI_RESPONSES_DEPLOYMENT_NAME" "$AZURE_OPENAI_RESPONSES_DEPLOYMENT_NAME"
add_env_var "AZURE_OPENAI_EMBEDDING_MODEL" "$AZURE_OPENAI_EMBEDDING_MODEL"
add_env_var "AZURE_AI_MODEL_DEPLOYMENT_VERSION" "$AZURE_AI_MODEL_DEPLOYMENT_VERSION"
add_env_var "BING_CONNECTION_ID" "$BING_CONNECTION_ID"

# Azure Search
add_env_var "AZURE_SEARCH_ENDPOINT" "$AZURE_SEARCH_ENDPOINT"
add_env_var "AZURE_SEARCH_API_KEY" "$AZURE_SEARCH_API_KEY"
add_env_var "AZURE_SEARCH_INDEX_NAME" "$AZURE_SEARCH_INDEX_NAME"

# API Gateway
add_env_var "AZURE_API_GATEWAY_ENDPOINT" "$AZURE_API_GATEWAY_ENDPOINT"
add_env_var "AZURE_API_GATEWAY_KEY" "$AZURE_API_GATEWAY_KEY"

# OpenAI (optional)
add_env_var "OPENAI_API_KEY" "$OPENAI_API_KEY"
add_env_var "OPENAI_CHAT_MODEL_ID" "$OPENAI_CHAT_MODEL_ID"
add_env_var "OPENAI_RESPONSES_MODEL_ID" "$OPENAI_RESPONSES_MODEL_ID"

# Telemetry
add_env_var "APPLICATIONINSIGHTS_CONNECTION_STRING" "$APPLICATIONINSIGHTS_CONNECTION_STRING"
add_env_var "OTEL_SERVICE_NAME" "$OTEL_SERVICE_NAME"
add_env_var "DISABLE_TELEMETRY" "$DISABLE_TELEMETRY"

# Cosmos DB
add_env_var "COSMOS_DB_ENDPOINT" "$COSMOS_DB_ENDPOINT"
add_env_var "COSMOS_DB_AUTH_METHOD" "$COSMOS_DB_AUTH_METHOD"
add_env_var "COSMOS_DB_KEY" "$COSMOS_DB_KEY"
add_env_var "COSMOS_DB_DATABASE" "$COSMOS_DB_DATABASE"
add_env_var "COSMOS_DB_CONTAINER" "$COSMOS_DB_CONTAINER"

# Redis
add_env_var "REDIS_URL" "$REDIS_URL"

# Session
add_env_var "SESSION_TTL" "$SESSION_TTL"

echo ""
echo -e "${YELLOW}================================${NC}"
echo -e "${YELLOW}Updating Azure Container App...${NC}"
echo -e "${YELLOW}================================${NC}"
echo ""

# Update the container app with environment variables
if az containerapp update \
    --name "$CONTAINER_APP_NAME" \
    --resource-group "$RESOURCE_GROUP" \
    --set-env-vars $ENV_VARS \
    --output none; then
    echo ""
    echo -e "${GREEN}✓ Successfully updated environment variables!${NC}"
    echo ""
    echo -e "${YELLOW}Next steps:${NC}"
    echo "1. The container app will automatically restart with new environment variables"
    echo "2. Monitor logs: az containerapp logs show -n $CONTAINER_APP_NAME -g $RESOURCE_GROUP --follow"
    echo "3. Check status: az containerapp show -n $CONTAINER_APP_NAME -g $RESOURCE_GROUP --query properties.runningStatus"
    echo ""
else
    echo ""
    echo -e "${RED}✗ Failed to update environment variables${NC}"
    echo -e "${YELLOW}Troubleshooting:${NC}"
    echo "1. Verify resource group: az group show -n $RESOURCE_GROUP"
    echo "2. Verify container app exists: az containerapp show -n $CONTAINER_APP_NAME -g $RESOURCE_GROUP"
    echo "3. Check Azure CLI version: az --version"
    exit 1
fi
